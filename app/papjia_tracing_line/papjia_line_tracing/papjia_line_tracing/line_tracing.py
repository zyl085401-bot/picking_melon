"""
@Descripttion: 寻迹控制
@version: 1.0
@Author: 崔译文
@Date: 2024-03-07 16:41:18
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 12:15:21
"""

import os
import time
from datetime import datetime
import cv2
import threading
import copy
import rclpy
import numpy as np
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
from papjia_move_msgs.srv import TracingLineTrigger
from papjia_vision_interface.srv import SegImage
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from .pid import PIDController
from .fld import FastLineDetector
from .camera import CameraModel
from .car import Car


def filter_by_color(image, lower_hsv=np.array([10, 30, 100]), upper_hsv=np.array([60, 255, 255])):
    """根据设定的颜色进行过滤（非设定颜色设置为黑色）

    Args:
        image (图像数组): _description_
        lower_hsv (hsv颜色值, optional): _description_. Defaults to np.array([20, 100, 100]).
        upper_hsv (hsv颜色值, optional): _description_. Defaults to np.array([30, 255, 255]).

    Returns:
        图像数组: 过滤后的图像
    """
    # 将图像从BGR颜色空间转换为HSV颜色空间
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 使用inRange函数获取黄色区域的掩码
    hsv_mask = cv2.inRange(hsv_image, lower_hsv, upper_hsv)

    # 对原始图像应用掩码，将非黄色区域置为黑色
    result_image = cv2.bitwise_and(image, image, mask=hsv_mask)
    result_image[hsv_mask > 0] = [0, 255, 255]
    return result_image


def angle_between_vectors(a, b):
    """计算两个向量之间的夹角（逆时针为正，顺时针为负）

    Args:
        a (numpy数组): 第一个向量
        b (numpy数组): 第二个向量

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
    if cross_product < 0:
        angle_rad *= -1  # 顺时针旋转为负角度

    return angle_rad


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
    direction_vector = np.array(line_point2) - np.array(line_point1)
    direction_vector /= np.linalg.norm(direction_vector)
    # 计算点到直线的投影点
    projection_point = line_point1 + np.dot(np.array(point) - np.array(line_point1), direction_vector) * direction_vector
    # 计算投影向量
    projection_vector = projection_point - np.array(point)
    # 计算投影向量的模长
    distance = np.linalg.norm(projection_vector)
    # 判断点在直线左侧还是右侧
    if np.cross(direction_vector, projection_vector) > 0:  # 若叉乘结果为正，则在直线左侧
        distance *= -1
    return distance


class LineTracking(Node):
    """循线行走ROS接口及实现

    Args:
        Node (ROS2节点): ROS2节点
    """

    def __init__(self):
        """
        1. 接收参数
        2. 订阅图像
        3. 订阅摄像头信息
        4. 创建速度发布器
        5. 创建PID控制器
        6. 创建循线行走服务
        """
        super().__init__("line_tracking_node")

        # 声明ROS参数
        self.declare_parameters(
            namespace="",
            parameters=[
                ("roi", [0]),
                ("centerline", [0]),
                ("max_angle_diff", 30.0),
                ("max_img_num", 1),
                ("wheel_separation", 0.5),
                ("car_speed", 0.2),
                ("topic_tracing_trigger", ""),
                ("pid", [0.0]),
                ("topic_image", "/camera/image_raw"),
                ("topic_camera_info", "/camera/camera_info"),
                ("pose_camera2base", [0.0]),
                ("pose_left2right", [0.0]),
                ("enable_adjust_speed", True),
                ("use_stamp_twist", True),
                ("save_folder", "/tmp"),
                ("save_image", False),
                ("show_image", False),
                ("update_hz", 10.0),
                ("use_maskrcnn", True),
            ],
        )

        self.forward_move = True

        self.roi = self.get_parameter("roi").get_parameter_value().integer_array_value
        self.centerline = self.get_parameter("centerline").get_parameter_value().integer_array_value
        self.max_img_num = self.get_parameter("max_img_num").get_parameter_value().integer_value

        self.callback_group = ReentrantCallbackGroup()
        self.client_lane_detect = self.create_client(SegImage, "/papjia_vision/service_image_segment", callback_group=self.callback_group)

        self.use_maskrcnn = self.get_parameter("use_maskrcnn").get_parameter_value().bool_value
        self.update_hz = self.get_parameter("update_hz").get_parameter_value().double_value
        self.timer = self.create_timer(1 / self.update_hz, self.line_tracking, callback_group=self.callback_group)
        self.timer.cancel()
        self.topic_tracing_trigger = self.get_parameter("topic_tracing_trigger").get_parameter_value().string_value
        self.srv_tracing = self.create_service(
            TracingLineTrigger,
            self.topic_tracing_trigger,
            self.callback_tracing_trigger,
        )

        self.img_msg = None
        self.mutex_image = threading.Lock()
        self.image_timeout = 0.1
        self.topic_image = self.get_parameter("topic_image").get_parameter_value().string_value
        self.topic_camera_info = self.get_parameter("topic_camera_info").get_parameter_value().string_value
        self.sub_image = self.create_subscription(Image, self.topic_image, self.callback_image, 3)
        self.sub_image  # 防止Python对订阅对象进行垃圾回收
        self.bridge = CvBridge()

        self.save_folder = self.get_parameter("save_folder").get_parameter_value().string_value
        self.save_image = self.get_parameter("save_image").get_parameter_value().bool_value
        self.show_image = self.get_parameter("show_image").get_parameter_value().bool_value
        if not self.use_maskrcnn:
            self.fld = FastLineDetector(length_threshold=30, canny_th1=100, canny_th2=150, canny_aperture_size=7)
        # camera model
        self.pose_left2right = self.get_parameter("pose_left2right").get_parameter_value().double_array_value
        self.pose_camera2base = self.get_parameter("pose_camera2base").get_parameter_value().double_array_value
        self.camera = None
        self.camera_cfg = {
            "new": False,
            "camera_name": self.topic_camera_info.rsplit("/", 1)[0],
            "camera_pose": self.pose_camera2base,
        }
        self.mutex_camera_cfg = threading.Lock()
        self.sub_camera_info = self.create_subscription(CameraInfo, self.topic_camera_info, self.callback_camera_info, 3)
        self.sub_camera_info

        self.wheel_separation = self.get_parameter("wheel_separation").get_parameter_value().double_value
        self.init_car_speed = self.get_parameter("car_speed").get_parameter_value().double_value
        self.car = Car(self.wheel_separation, self.init_car_speed)
        self.enable_adjust_speed = self.get_parameter("enable_adjust_speed").get_parameter_value().bool_value
        self.trigger_adjust_speed = False
        self.use_stamp_twist = self.get_parameter("use_stamp_twist").get_parameter_value().bool_value
        if self.use_stamp_twist:
            self.pub_vel = self.create_publisher(TwistStamped, "/cmd_vel", 3)
        else:
            self.pub_vel = self.create_publisher(Twist, "/cmd_vel", 3)

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
        self.mutex_camera_cfg.acquire()
        camera_cfg = copy.deepcopy(self.camera_cfg)
        self.camera_cfg["new"] = False
        self.mutex_camera_cfg.release()
        if camera_cfg["new"] is True:
            self.camera = CameraModel(pose_left2right=self.pose_left2right)
            self.camera.update(camera_cfg)
            self.get_logger().info("update camera model config")
        else:
            response.success = False
            self.get_logger().warn("No camera info !")
            return response
        if request.trigger == "start":
            self.car.reset(abs(request.speed))
            self.pid_controller.reset()
            self.forward_move = False if request.speed < 0 else True
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

    def callback_camera_info(self, msg):
        """订阅相机参数

        Args:
            msg (CameraInfo): 相机信息的消息
        """
        self.mutex_camera_cfg.acquire()
        self.camera_cfg["image_height"] = msg.height
        self.camera_cfg["image_width"] = msg.width
        self.camera_cfg["distortion_model"] = msg.distortion_model
        self.camera_cfg["distortion_coefficients"] = {
            "data": msg.d,
            "rows": 1,
            "cols": 5,
        }
        self.camera_cfg["camera_matrix"] = {"data": msg.k, "rows": 3, "cols": 3}
        self.camera_cfg["rectification_matrix"] = {"data": msg.r, "rows": 3, "cols": 3}
        self.camera_cfg["projection_matrix"] = {"data": msg.p, "rows": 3, "cols": 4}
        self.camera_cfg["new"] = True
        self.mutex_camera_cfg.release()

    def callback_image(self, msg):
        """订阅图像

        Args:
            msg (Image): 图像消息
        """
        self.get_logger().debug("callback_image")
        try:
            if self.mutex_image.acquire(timeout=self.image_timeout):
                self.img_msg = copy.deepcopy(msg)
                self.mutex_image.release()
            else:
                self.get_logger().error("Acquire image lock timeout! ")
        except Exception as e:
            self.get_logger().error("Error converting image: %s" % str(e))
            return

    def get_image(self, convert=True):
        """获取最新的图像（不重复获取同一张）

        Returns:
            图像数组: 图像
        """
        img = None
        if self.mutex_image.acquire():
            if self.img_msg is not None:  # 可能没有新图像
                if convert:
                    try:
                        img = self.bridge.imgmsg_to_cv2(self.img_msg, desired_encoding="bgr8")
                    except Exception as e:
                        self.get_logger().error("Error converting image: %s" % str(e))
                else:
                    img = copy.deepcopy(self.img_msg)
                self.img_msg = None
            self.mutex_image.release()
        else:
            self.get_logger().error("Acquire image lock timeout! ")
            time.sleep(self.image_timeout)
        return img

    def get_cross_angle(self, l1, l2):
        """获取两个直线的夹角（弧度）

        Args:
            l1 (直线[x1,y1,x2,y2]): 直线1
            l2 (直线[x1,y1,x2,y2]): 直线2

        Returns:
            float: 两直线夹角（弧度）
        """
        vec1 = np.array([l1[2] - l1[0], l1[3] - l1[1]])
        vec2 = np.array([l2[2] - l2[0], l2[3] - l2[1]])
        return angle_between_vectors(vec1, vec2)  # 弧度

    def line_properties(self, line):
        """计算直线的夹角(和self.centerline)以及线段端点在基坐标系下的3D坐标

        Args:
            line (直线[x1,y1,x2,y2]): 直线参数

        Returns:
            list: 夹角和坐标
        """
        angle = self.get_cross_angle(line, self.centerline)
        x1, y1, x2, y2 = line[:]
        p1 = self.camera.pixel_to_world([x1, y1])
        p2 = self.camera.pixel_to_world([x2, y2])
        if p1[0] * p1[0] + p1[1] * p1[1] > p2[0] * p2[0] + p2[1] * p2[1]:  # p2更远
            p1, p2 = p2, p1
        return [angle, p1[0:2], p2[0:2]]

    def detect_lines(self, img):
        """车道线检测

        Args:
            img (图像数组): 图像

        Returns:
            list: 车道线[左, 右]
        """
        self.get_logger().debug("begin detect lines")
        ## 直线检测
        roi_img = img[
            self.roi[1] : self.roi[3],
            self.roi[0] : self.roi[2],
        ]
        lines = self.fld.detect(roi_img, show=False, save=False)
        for line in lines:
            line[0] += self.roi[0]
            line[1] += self.roi[1]
            line[2] += self.roi[0]
            line[3] += self.roi[1]
        line_filtered = []
        for line in lines:
            x1, y1, x2, y2 = line[:]
            if abs(y2 - y1) / abs(self.roi[3] - self.roi[1]) > 0.5:  # 直线与roi垂直
                line_filtered.append([x1, y1, x2, y2])
        lines = sorted(line_filtered, key=lambda line: line[3], reverse=True)
        if self.show_image or self.save_image:
            cv2.rectangle(
                img,
                (self.roi[0], self.roi[1]),
                (self.roi[2], self.roi[3]),
                (0, 0, 255),
                2,
            )
            n = 0
            for line in lines:
                n += 1
                x0, y0, x1, y1 = [int(round(i)) for i in line]
                if n <= 2:
                    cv2.line(img, (x0, y0), (x1, y1), (0, 0, 255), 3, cv2.LINE_AA)
                else:
                    cv2.line(img, (x0, y0), (x1, y1), (0, 255, 0), 1, cv2.LINE_AA)
            if self.show_image:
                # 显示结果
                cv2.imshow("LSD", img)
                cv2.waitKey(10)
            if self.save_image:
                # 获取当前时间（包含毫秒级别）
                current_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
                cv2.imwrite(os.path.join(self.save_folder, f"{current_time}.png"), img)
        if len(lines) < 2:
            self.get_logger().warn("detect lines num: %d" % (len(lines)))
            return [None, None]
        self.get_logger().debug("finished detect lines")
        line1 = lines[0]
        line2 = lines[1]
        max_dist = point_to_line_distance(line1[0:2], line2[0:2], line2[2:4])
        if max_dist < 0:
            return [line2, line1]
        return [line1, line2]

    def adjust_speed(self, angle, dist):
        """基于PID调整速度

        Args:
            angle (double): 角度偏差（车道线和车行进方向）
            dist (double): 距离(车中心到车道线中线)

        Returns:
            _type_: _description_
        """
        error = angle + dist * 3
        end_time = time.time()
        time_step = end_time - self.start_time if end_time - self.start_time < 0.1 else 0.1
        self.start_time = end_time
        adjustment = self.pid_controller.update(error, time_step)
        # 根据调整量来调整两个轮子的速度
        if abs(adjustment) < 0.001:
            adjustment = 0
        self.get_logger().info("error (%.5f), time step %.2f, adjustment %.5f" % (error, time_step, adjustment))
        speed = self.car.update_speed(adjustment)
        self.get_logger().info("linear.x %.5f, angular.z %.5f, angle %.5f, dist %.5f" % (speed[0], speed[1] * 180 / np.pi, angle * 180 / np.pi, dist))
        if speed[1] > 2 * self.car.init_left_wheel_speed / self.car.wheel_separation:
            speed[1] = 2 * self.car.init_left_wheel_speed / self.car.wheel_separation
            self.get_logger().warn("linear.x %.5f, angular.z %.5f, angle %.5f, dist %.5f" % (speed[0], speed[1] * 180 / np.pi, angle * 180 / np.pi, dist))
        elif speed[1] < -2.0 * self.car.init_left_wheel_speed / self.car.wheel_separation:
            speed[1] = -2.0 * self.car.init_left_wheel_speed / self.car.wheel_separation
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

    def detect_lane(self, img_msg):
        req = SegImage.Request()
        req.image = img_msg
        req.max_num = 10
        req.min_score = 0.9
        res = self.client_lane_detect.call(req)
        if res.objs_num == 0:
            return [None, None]

        idx = 0
        max_num_points = 0
        for i in range(res.objs_num):
            if res.points_num[i] > max_num_points:
                max_num_points = res.points_num[i]
                idx = i + 1

        mask = self.bridge.imgmsg_to_cv2(res.mask)
        img_size = [img_msg.width, img_msg.height]
        mask_size = [mask.shape[1], mask.shape[0]]
        if img_size[0] != mask_size[0] or img_size[1] != mask_size[1]:
            mask = cv2.resize(mask, img_size[1])
        x1, y1, x2, y2 = self.roi[:]
        c1 = [x1, y1]
        for x in range(x1, x2, 1):
            if mask[y1, x] == idx:
                c1[0] = x
                break
        for x in range(x2, x1, -1):
            if mask[y1, x] == idx:
                c1[0] = (c1[0] + x) / 2
                break
        c2 = [x2, y2]
        for x in range(x1, x2, 1):
            if mask[y2, x] == idx:
                c2[0] = x
                break
        for x in range(x2, x1, -1):
            if mask[y2, x] == idx:
                c2[0] = (c2[0] + x) / 2
                break
        angle, p1, p2 = self.line_properties([c1[0], c1[1], c2[0], c2[1]])
        return [p1, p2]

    def line_tracking(self):
        self.get_logger().info("line_tracking ...")
        """循线程序"""
        img = self.get_image(self.use_maskrcnn != True)
        if img is None:
            self.get_logger().warn("Get image fail!")
            return
        p1 = None
        p2 = None
        if self.use_maskrcnn:
            p1, p2 = self.detect_lane(img_msg=img)
        else:
            # img = filter_by_color(img)
            left_line, right_line = self.detect_lines(img)
            if left_line is None:
                return
            ## 角度和位置偏向计算
            angle1, p11, p12 = self.line_properties(left_line)
            self.get_logger().debug("left_line %.1f %.1f %.1f %.1f" % (left_line[0], left_line[1], left_line[2], left_line[3]))
            self.get_logger().debug("left_line_properties %.2f %.2f %.2f %.2f %.2f" % (p11[0], p11[1], p12[0], p12[1], angle1))
            angle2, p21, p22 = self.line_properties(right_line)
            self.get_logger().debug("right_line %.1f %.1f %.1f %.1f" % (right_line[0], right_line[1], right_line[2], right_line[3]))
            self.get_logger().debug("right_line_properties %.2f %.2f %.2f %.2f %.2f" % (p21[0], p21[1], p22[0], p22[1], angle2))
            p1 = [(p11[0] + p21[0]) / 2, (p11[1] + p21[1]) / 2]
            p2 = [(p12[0] + p22[0]) / 2, (p12[1] + p22[1]) / 2]

        if p1 is None:
            self.get_logger().warn("find lane failed")
            return
        dist = point_to_line_distance([0.0, 0.0], p1, p2)
        dist = dist if self.forward_move else dist * -1.0
        angle = self.get_cross_angle([p1[0], p1[1], p2[0], p2[1]], [0.0, 0.0, 1.0, 0.0])
        self.get_logger().info("center_line %.2f %.2f %.2f %.2f %.2f %.2f" % (p1[0], p1[1], p2[0], p2[1], angle * 180 / np.pi, dist))
        if self.enable_adjust_speed and self.trigger_adjust_speed:
            ### pid调控
            speed = self.adjust_speed(angle=angle, dist=dist)
            # 发布速度
            self.publish_speed(speed)
        self.get_logger().info("line_tracking finished")


def main(args=None):
    rclpy.init(args=args)
    node = LineTracking()
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
