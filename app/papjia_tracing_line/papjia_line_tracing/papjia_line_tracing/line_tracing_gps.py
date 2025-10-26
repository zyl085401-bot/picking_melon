"""
@Descripttion: 寻迹控制
@version: 1.0
@Author: 崔译文
@Date: 2024-03-07 16:41:18
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 12:15:21
"""

import time
from datetime import datetime
import rclpy
import numpy as np
import transforms3d
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped, Pose2D, PoseStamped
from tf2_geometry_msgs import do_transform_pose
from tf2_ros import Buffer, TransformListener
from ament_index_python.packages import get_package_share_directory
from papjia_move_msgs.srv import TracingLineTrigger
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from .pid import PIDController
from .car import Car


def point_to_line_distance(point, line_point1, line_point2):
    """点到直线的距离

    Args:
        point (list): 点的坐标
        line_point1 (list): 直线上的点
        line_point2 (list): 直线上的点

    Returns:
        float: 距离
    """
    # 计算直线的单位方向向量
    direction_vector = line_point2 - line_point1
    direction_vector /= np.linalg.norm(direction_vector)
    # 计算点到直线的投影点
    projection_point = line_point1 + np.dot(point - line_point1, direction_vector) * direction_vector
    # 计算投影向量
    projection_vector = projection_point - point
    # 计算投影向量的模长
    distance = np.linalg.norm(projection_vector)
    # 判断点在直线左侧还是右侧
    if np.cross(direction_vector, projection_vector) > 0:  # 若叉乘结果为正，则在直线左侧
        distance *= -1
    return distance


def angle_between_vectors(a, b):
    """计算两个向量之间的夹角（逆时针为正，顺时针为负）

    Args:
        a (numpy数组): 第一个向量【目标线段方向】
        b (numpy数组): 第二个向量【机器人base_link的x轴】

    Returns:
        float: 夹角（以弧度表示）
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    cos_theta = dot_product / (norm_a * norm_b)
    # 使用clip确保cos_theta在[-1, 1]之间，避免由于数值计算误差导致arccos报错
    angle_rad = np.arccos(np.clip(cos_theta, -1.0, 1.0))
    # 判断顺时针还是逆时针
    cross_product = np.cross(a, b)
    if cross_product < 0:  # 逆时针旋转为正角度
        angle_rad *= -1  #  b 在 a 的顺时针方向，返回负角度

    return angle_rad


def transform_pose2d(pose2d_map, tf_buffer, target_frame="base_link", source_frame="map"):
    """
    使用 transforms3d 库的坐标变换 (ROS 2 Humble)
    :param pose2d_map: 输入位姿 (map 坐标系)
    :param tf_buffer: tf2_ros.Buffer 实例
    :return: 转换后的 base_link 坐标系位姿 (失败返回 None)
    """
    # 创建 PoseStamped 用于 TF2 变换
    pose_stamped = PoseStamped()
    pose_stamped.header.frame_id = "map"
    pose_stamped.header.stamp = rclpy.time.Time().to_msg()
    pose_stamped.pose.position.x = pose2d_map.x
    pose_stamped.pose.position.y = pose2d_map.y
    pose_stamped.pose.position.z = 0.0

    # 使用 transforms3d 生成绕 Z 轴的四元数 (注意弧度单位)
    theta = pose2d_map.theta
    quat = transforms3d.euler.euler2quat(0, 0, theta, "sxyz")  # 静态轴旋转顺序: X-Y-Z
    # 调整四元数顺序为 ROS 格式 (x, y, z, w)
    pose_stamped.pose.orientation.x = quat[1]
    pose_stamped.pose.orientation.y = quat[2]
    pose_stamped.pose.orientation.z = quat[3]
    pose_stamped.pose.orientation.w = quat[0]

    try:
        transform = tf_buffer.lookup_transform(
            target_frame=target_frame,
            source_frame=source_frame,
            time=rclpy.time.Time(),
            timeout=rclpy.duration.Duration(seconds=1),
        )
    except Exception as e:
        rclpy.logging.get_logger("tf2").warn(f"TF2 错误: {str(e)}")
        return None

    # 应用变换
    pose_transformed = do_transform_pose(pose_stamped.pose, transform)

    # 转换为 Pose2D
    pose2d_base = Pose2D()
    pose2d_base.x = pose_transformed.position.x
    pose2d_base.y = pose_transformed.position.y

    # 使用 transforms3d 从四元数提取偏航角
    q_ros = [
        pose_transformed.orientation.w,  # transforms3d 需要 (w, x, y, z)
        pose_transformed.orientation.x,
        pose_transformed.orientation.y,
        pose_transformed.orientation.z,
    ]
    _, _, yaw = transforms3d.euler.quat2euler(q_ros, "sxyz")  # 与生成时顺序一致
    pose2d_base.theta = yaw

    return pose2d_base


class LineTracking(Node):
    """循线行走ROS接口及实现

    Args:
        Node (ROS2节点): ROS2节点
    """

    def __init__(self):
        super().__init__("line_tracking_node")

        # 声明ROS参数
        self.declare_parameters(
            namespace="",
            parameters=[
                ("max_angle_diff", 30.0),
                ("wheel_separation", 0.5),
                ("car_speed", 0.2),
                ("topic_tracing_trigger", ""),
                ("pid", [0.0]),
                ("enable_adjust_speed", True),
                ("use_stamp_twist", True),
                ("topic_cmd_vel", "/cmd_vel"),
                ("save_folder", "/tmp"),
                ("update_hz", 10.0),
                ("base_link", "base_link"),
                ("max_twist_z", 1.0),
            ],
        )

        self.forward_move = True
        self.line_start = None
        self.line_end = None
        self.line_frame = None
        self.base_link = self.get_parameter("base_link").get_parameter_value().string_value
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.callback_group = ReentrantCallbackGroup()
        self.update_hz = self.get_parameter("update_hz").get_parameter_value().double_value
        self.timer = self.create_timer(
            1 / self.update_hz, self.line_tracking, callback_group=self.callback_group
        )
        self.timer.cancel()
        self.topic_tracing_trigger = (
            self.get_parameter("topic_tracing_trigger").get_parameter_value().string_value
        )
        self.get_logger().info(f"topic_tracing_trigger: {self.topic_tracing_trigger}")
        self.srv_tracing = self.create_service(
            TracingLineTrigger,
            self.topic_tracing_trigger,
            self.callback_tracing_trigger,
        )

        self.wheel_separation = self.get_parameter("wheel_separation").get_parameter_value().double_value
        self.init_car_speed = self.get_parameter("car_speed").get_parameter_value().double_value
        self.max_twist_z = self.get_parameter("max_twist_z").get_parameter_value().double_value
        self.car = Car(self.wheel_separation, self.init_car_speed)
        self.enable_adjust_speed = self.get_parameter("enable_adjust_speed").get_parameter_value().bool_value
        self.trigger_adjust_speed = False
        self.use_stamp_twist = self.get_parameter("use_stamp_twist").get_parameter_value().bool_value
        self.topic_cmd_vel = self.get_parameter("topic_cmd_vel").get_parameter_value().string_value
        if self.use_stamp_twist:
            self.pub_vel = self.create_publisher(TwistStamped, self.topic_cmd_vel, 3)
        else:
            self.pub_vel = self.create_publisher(Twist, self.topic_cmd_vel, 3)

        self.pid = self.get_parameter("pid").get_parameter_value().double_array_value
        self.pid_controller = PIDController(self.pid[0], self.pid[1], self.pid[2], int(3 * self.update_hz))
        self.start_time = time.time()

    def callback_tracing_trigger(self, request, response):
        """循线行走开关，控制定时器线程是否运行

        Args:
            request (TracingLineTrigger.Request): 服务请求参数
            response (TracingLineTrigger.Response): 服务结果

        Returns:
            TracingLineTrigger.Response: 服务结果
        """
        if request.trigger == "start":
            self.car.reset(abs(request.speed))
            self.pid_controller.reset()
            self.forward_move = False if request.speed < 0 else True
            self.line_frame = request.line_frame
            self.line_start = request.line_start
            self.line_end = request.line_end
            self.start_time = time.time()
            if self.timer.is_canceled():
                self.timer.reset()
                self.trigger_adjust_speed = True
                self.get_logger().info("start tracing line timer")
                response.success = True
            else:
                self.get_logger().warn("tracing line timer already start")
        elif request.trigger == "stop":
            if self.timer.is_canceled():
                self.get_logger().warn("tracing line timer already stop")
            else:
                self.get_logger().info("stop tracing line timer ...")
                self.timer.cancel()
                self.trigger_adjust_speed = False
                time.sleep(0.01)
                response.success = True
                self.publish_speed([0.0, 0.0])
                self.get_logger().info("stop tracing line timer finished")
        return response

    def compute_distance_and_angle(self, point_start, point_end):
        """计算距离和角度

        Args:
            point_start (Point): 起始点
            point_end (Point): 终止点

        Returns:
            double: 距离
            double: 角度
        """

        dist = point_to_line_distance(
            np.array([0, 0]),
            np.array([point_start.x, point_start.y]),
            np.array([point_end.x, point_end.y]),
        )
        forward_vec = [1.0, 0]
        if self.forward_move is False:
            forward_vec = [-1.0, 0]

        angle = angle_between_vectors(
            np.array([point_end.x - point_start.x, point_end.y - point_start.y]),
            np.array(forward_vec),
        )
        self.get_logger().info(f"distance: {dist} and angle: {angle * 180 / np.pi}")
        return [dist, angle]

    def adjust_speed(self, angle, dist):
        """基于PID调整速度

        Args:
            angle (double): 角度偏差（车道线和车行进方向）
            dist (double): 距离(车中心到车道线中线)

        Returns:
            _type_: _description_
        """
        error = angle + dist
        end_time = time.time()
        time_step = end_time - self.start_time if end_time - self.start_time > 0.1 else 0.1
        self.start_time = end_time
        adjustment = self.pid_controller.update(error, time_step)
        # 根据调整量来调整两个轮子的速度
        if abs(adjustment) < 0.001:
            adjustment = 0
        self.get_logger().info(
            "error (%.5f), time step %.2f, adjustment %.5f" % (error, time_step, adjustment)
        )
        speed = self.car.update_speed(adjustment)
        speed[1] = max(min(speed[1], self.max_twist_z), -self.max_twist_z)
        self.get_logger().info(
            "linear.x %.5f, angular.z %.5f, angle %.5f, dist %.5f"
            % (speed[0], speed[1] * 180 / np.pi, angle * 180 / np.pi, dist)
        )
        return speed

    def publish_speed(self, speed):
        """根据use_stamp_twist设定不同的速度消息发布

        Args:
            speed (list): [线速度, 角速度]
        """
        if self.use_stamp_twist:
            twist = TwistStamped()
            twist.twist.linear.x = speed[0] if self.forward_move else speed[0] * -1.0
            twist.twist.angular.z = speed[1]
            self.pub_vel.publish(twist)
        else:
            twist = Twist()
            twist.linear.x = speed[0] if self.forward_move else speed[0] * -1.0
            twist.angular.z = speed[1]
            self.pub_vel.publish(twist)

    def line_tracking(self):
        point_start = transform_pose2d(self.line_start, self.tf_buffer, self.base_link, self.line_frame)
        point_end = transform_pose2d(self.line_end, self.tf_buffer, self.base_link, self.line_frame)
        self.get_logger().info(f"start: ({point_start.x:.2f}, {point_start.y:.2f}), end: ({point_end.x:.2f}, {point_end.y:.2f})")
        dist, angle = self.compute_distance_and_angle(point_start=point_start, point_end=point_end)
        if self.enable_adjust_speed and self.trigger_adjust_speed:
            ### pid调控
            speed = self.adjust_speed(angle=angle, dist=dist)
            # 发布速度
            self.publish_speed(speed)


def main(args=None):
    rclpy.init(args=args)
    node = LineTracking()
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
