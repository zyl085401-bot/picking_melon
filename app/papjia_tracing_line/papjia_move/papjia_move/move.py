"""
@Descripttion: 直线盲走/寻迹控制
@version: 1.0
@Author: 崔译文
@Date: 2024-03-14 09:36:21
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 11:41:55
"""

import threading
import copy
import math
import rclpy
import time
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose, Twist, TwistStamped
from papjia_move_msgs.srv import TracingLineTrigger, StraightMove


def cal_distance(p1, p2):
    """计算两点间距离

    Args:
        p1 (位置类): 位置
        p2 (位置类): 位置

    Returns:
        _type_: _description_
    """
    return math.sqrt(math.pow((p2.x - p1.x), 2) + math.pow((p2.y - p1.y), 2))


class MoveService(Node):
    def __init__(self):
        """初始化服务"""
        super().__init__("move_service_node")
        # 声明ROS参数
        self.declare_parameters(
            namespace="",
            parameters=[
                ("topic_tracing_move", ""),
                ("topic_tracing_trigger", ""),
                ("topic_straight_move", ""),
                ("topic_cmd_vel", "cmd_vel"),
                ("topic_odom", ""),
                ("enable_tracing", False),
                ("enable_move", True),
                ("default_speed", 0.1),
                ("use_stamp_twist", True),
                ("cmd_vel", "/cmd_vel"),
            ],
        )

        self.mutex = threading.Lock()
        self.current_pose = Pose()
        self.start_pose = Pose()
        
        self.enable_tracing = self.get_parameter("enable_tracing").get_parameter_value().bool_value
        self.enable_move = self.get_parameter("enable_move").get_parameter_value().bool_value
        self.default_speed = self.get_parameter("default_speed").get_parameter_value().double_value
        self.use_stamp_twist = self.get_parameter("use_stamp_twist").get_parameter_value().bool_value
        self.topic_cmd_vel = self.get_parameter("topic_cmd_vel").get_parameter_value().string_value
        self.get_logger().info(f"enable_tracing: {self.enable_tracing}, enable_move: {self.enable_move}, use_stamp_twist: {self.use_stamp_twist}")
        self.get_logger().info(f"default_speed: {self.default_speed}")

        if not self.enable_tracing and not self.enable_move:
            raise ValueError("At least one of enable_tracing or enable_move must be True")
        if self.use_stamp_twist:
            self.pub_vel = self.create_publisher(TwistStamped, self.topic_cmd_vel, 3)
        else:
            self.pub_vel = self.create_publisher(Twist, self.topic_cmd_vel, 3)
        
        self.callback_group = ReentrantCallbackGroup()
        
        # 寻线模式
        if self.enable_tracing:
            self.topic_tracing_move = self.get_parameter("topic_tracing_move").get_parameter_value().string_value
            self.topic_tracing_trigger = (
                self.get_parameter("topic_tracing_trigger").get_parameter_value().string_value
            )
            self.server_tracing_move = self.create_service(
                StraightMove,
                self.topic_tracing_move,
                self.tracing_move_callback,
                callback_group=self.callback_group,
            )
            self.client_tracing_trigger = self.create_client(
                TracingLineTrigger, self.topic_tracing_trigger, callback_group=self.callback_group
            )
            self.get_logger().info(f"topic_tracing_move: {self.topic_tracing_move}")
        
        # 直行模式
        if self.enable_move:
            self.topic_straight_move = (
                self.get_parameter("topic_straight_move").get_parameter_value().string_value
            )
            self.server_straight_move = self.create_service(
                StraightMove,
                self.topic_straight_move,
                self.straight_move_callback,
                callback_group=self.callback_group,
            )
        
        # 订阅里程计
        self.topic_odom = self.get_parameter("topic_odom").get_parameter_value().string_value
        self.sub_odom = self.create_subscription(Odometry, self.topic_odom, self.odom_callback, 2)
        

    def odom_callback(self, msg):
        """订阅odom数据

        Args:
            msg (Odometry): odom数据
        """
        self.mutex.acquire()
        self.current_pose = copy.deepcopy(msg.pose.pose)
        self.mutex.release()

    def get_current_pose(self):
        """获取当前位姿

        Returns:
            Pose: 机器人当前位姿
        """
        self.mutex.acquire()
        pose = copy.deepcopy(self.current_pose)
        self.mutex.release()
        return pose

    def cmp_dist_and_speed(self, req):
        """计算速度和需要行走的距离

        Args:
            req (StraightMove.Request): 服务的请求参数

        Returns:
            list: 距离和速度
        """
        dist = abs(req.distance)
        speed = req.speed
        if dist == 0:
            return [0, 0]
        elif speed == 0:
            speed = dist / req.distance * self.default_speed
        else:
            speed *= dist / req.distance
        return [dist, speed]

    def publish_speed(self, speed):
        """根据use_stamp_twist设定不同的速度消息发布

        Args:
            speed (list): [线速度, 角速度]
        """
        if self.use_stamp_twist:
            twist = TwistStamped()
            twist.twist.linear.x = speed[0]
            twist.twist.angular.z = speed[1]
            self.pub_vel.publish(twist)
        else:
            twist = Twist()
            twist.linear.x = speed[0]
            twist.angular.z = speed[1]
            self.pub_vel.publish(twist)

    def straight_move_callback(self, request, response):
        """直走服务

        Args:
            request (StraightMove.Request): 请求参数
            response (StraightMove.Response): 需要返回的参数

        Returns:
            StraightMove.Response: 需要返回的参数
        """
        self.start_pose = self.get_current_pose()
        self.get_logger().info(
            "start position(%.3lf, %.3lf)" % (self.start_pose.position.x, self.start_pose.position.y)
        )
        dist, speed = self.cmp_dist_and_speed(request)
        if dist == 0:
            response.success = False
            return response
        while True:
            current_pose = self.get_current_pose()
            d = cal_distance(self.start_pose.position, current_pose.position)
            self.get_logger().info("moved dist %.3lf, goal %.3lf" % (d, dist), skip_first=True, throttle_duration_sec=3.0)
            if d > dist - 0.005:
                self.get_logger().info(
                    "stop position(%.3lf, %.3lf)" % (current_pose.position.x, current_pose.position.y)
                )
                break
            self.publish_speed([speed, 0.0])
            time.sleep(0.1)
        self.publish_speed([0.0, 0.0])
        response.success = True
        return response

    def tracing_move_callback(self, request, response):
        """寻迹直走服务

        Args:
            request (StraightMove.Request): 请求参数
            response (StraightMove.Response): 需要返回的参数

        Returns:
            StraightMove.Response: 需要返回的参数
        """
        self.start_pose = self.get_current_pose()
        self.get_logger().info(
            "start position(%.3lf, %.3lf)" % (self.start_pose.position.x, self.start_pose.position.y)
        )
        use_integral = request.use_integral
        dist, speed = self.cmp_dist_and_speed(request)
        if dist == 0:
            response.success = False
            return response
        req = TracingLineTrigger.Request()
        req.trigger = "start"
        req.speed = speed
        req.line_frame = request.line_frame
        req.line_start.x = request.line_start[0]
        req.line_start.y = request.line_start[1]
        req.line_start.theta = request.line_start[2]
        req.line_end.x = request.line_end[0]
        req.line_end.y = request.line_end[1]
        req.line_end.theta = request.line_end[2]
        self.client_tracing_trigger.call(req)
        d = 0.0
        self.mutex.acquire()
        current_pose = copy.deepcopy(self.current_pose)
        self.mutex.release()
        prev_pose = copy.deepcopy(current_pose)
        while True:
            self.mutex.acquire()
            current_pose = copy.deepcopy(self.current_pose)
            self.mutex.release()
            if use_integral:
                d += cal_distance(prev_pose.position, current_pose.position)
                prev_pose = copy.deepcopy(current_pose)
            else:
                d = cal_distance(self.start_pose.position, current_pose.position)
            self.get_logger().info("moved dist %.3lf" % d)
            if d > dist - 0.005:
                self.get_logger().info(
                    "stop position(%.3lf, %.3lf)" % (current_pose.position.x, current_pose.position.y)
                )
                break
            time.sleep(0.1)
        req.trigger = "stop"
        self.client_tracing_trigger.call(req)
        response.success = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = MoveService()
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
