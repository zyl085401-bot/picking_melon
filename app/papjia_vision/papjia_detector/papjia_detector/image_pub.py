"""
@Descripttion:
@version:
@Author: 崔译文
@Date: 2024-01-11 16:40:25
@LastEditors: 崔译文
@LastEditTime: 2024-04-03 10:10:47
"""

import rclpy
from std_msgs.msg import Header
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from papjia_vision_interface.srv import UpdateImageSource
import cv2
import numpy as np
from cv_bridge import CvBridge
import threading
import yaml


class ImagePublisherNode(Node):
    """将图像文件发布到特定topic，并可选择发布点云

    Args:
        Node (_type_): ROS节点
    """

    def __init__(self):
        super().__init__("image_publisher_node")
        # 创建互斥锁
        self._lock = threading.Lock()

        # 创建回调组
        self.callback_group = ReentrantCallbackGroup()

        # 声明ROS参数
        self.declare_parameters(
            namespace="",
            parameters=[
                ("rgb_file", ""),
                ("rgb_topic", ""),
                ("depth_file", ""),
                ("depth_topic", ""),
                ("camera_frame", ""),
                ("update_service_topic", ""),
                ("flag_publish_cloud", False),
                ("cloud_topic", "/camera/camera_hand/points"),
                ("flag_publish_camera_info", False),
                ("camera_info_file", ""),
            ],
        )
        # 获取参数
        self.rgb_path = self.get_parameter("rgb_file").get_parameter_value().string_value
        self.rgb_topic = self.get_parameter("rgb_topic").get_parameter_value().string_value
        self.depth_path = self.get_parameter("depth_file").get_parameter_value().string_value
        self.depth_topic = self.get_parameter("depth_topic").get_parameter_value().string_value
        self.camera_frame = self.get_parameter("camera_frame").get_parameter_value().string_value
        self.update_service_topic = self.get_parameter("update_service_topic").get_parameter_value().string_value
        self.flag_publish_cloud = self.get_parameter("flag_publish_cloud").get_parameter_value().bool_value
        self.cloud_topic = self.get_parameter("cloud_topic").get_parameter_value().string_value
        self.flag_publish_camera_info = self.get_parameter("flag_publish_camera_info").get_parameter_value().bool_value
        self.camera_info_file = self.get_parameter("camera_info_file").get_parameter_value().string_value

        # 创建发布器
        self.pub_rgb = self.create_publisher(Image, self.rgb_topic, 1)
        self.pub_depth = self.create_publisher(Image, self.depth_topic, 1)
        if self.flag_publish_cloud:
            self.pub_cloud = self.create_publisher(PointCloud2, self.cloud_topic, 1)
            self.get_logger().info(f"点云将发布到话题: {self.cloud_topic}")
        if self.flag_publish_camera_info:
            self.pub_camera_info = self.create_publisher(CameraInfo, "/camera/camera_hand/aligned_depth_to_color/camera_info", 1)

        # 创建服务
        self.update_service = self.create_service(
            UpdateImageSource,
            self.update_service_topic,
            self.update_image_source_callback,
            callback_group=self.callback_group,
        )

        self.bridge = CvBridge()
        # 加载相机参数
        self.camera_matrix = None
        self.dist_coeffs = None
        self.load_camera_info()

        # 读取图片
        self.load_images()

        # 创建定时器，使用互斥回调组
        self.timer = self.create_timer(0.2, self.publish_image, callback_group=self.callback_group)

    def load_camera_info(self):
        """加载相机参数"""
        try:
            if not self.camera_info_file:
                self.get_logger().warn("未指定相机参数文件")
                return False

            with open(self.camera_info_file, "r") as f:
                camera_info = yaml.safe_load(f)

            # 获取相机内参矩阵
            self.camera_matrix = np.array(camera_info["K"]).reshape(3, 3)
            # 获取畸变系数
            self.dist_coeffs = np.array(camera_info["D"])

            # 创建相机信息消息
            self.camera_info_msg = CameraInfo()
            self.camera_info_msg.header.frame_id = self.camera_frame
            self.camera_info_msg.height = camera_info["height"]
            self.camera_info_msg.width = camera_info["width"]
            self.camera_info_msg.k = self.camera_matrix.flatten().tolist()
            self.camera_info_msg.d = self.dist_coeffs.tolist()
            self.camera_info_msg.p = np.array(camera_info["P"]).flatten().tolist()
            self.camera_info_msg.r = np.array(camera_info["R"]).flatten().tolist()
            self.camera_info_msg.distortion_model = camera_info["distortion_model"]

            # 设置ROI信息
            roi = camera_info["roi"]
            self.camera_info_msg.roi.x_offset = roi["x_offset"]
            self.camera_info_msg.roi.y_offset = roi["y_offset"]
            self.camera_info_msg.roi.height = roi["height"]
            self.camera_info_msg.roi.width = roi["width"]
            self.camera_info_msg.roi.do_rectify = roi["do_rectify"]

            # 设置binning信息
            self.camera_info_msg.binning_x = camera_info["binning_x"]
            self.camera_info_msg.binning_y = camera_info["binning_y"]

            self.get_logger().info(
                f"成功加载相机参数: 分辨率 {self.camera_info_msg.width}x{self.camera_info_msg.height}"
            )
            self.get_logger().info(f"相机内参矩阵: \n{self.camera_matrix}")
            self.get_logger().info(f"畸变系数: {self.dist_coeffs}")
            return True
        except Exception as e:
            self.get_logger().error(f"加载相机参数时发生错误: {str(e)}")
            return False

    def depth_to_pointcloud(self, depth_img, rgb_img):
        """将深度图像转换为点云

        Args:
            depth_img: 深度图像
            rgb_img: RGB图像

        Returns:
            PointCloud2: 点云消息
        """
        if self.camera_matrix is None:
            self.get_logger().error("相机参数未加载，无法生成点云")
            return None

        # 获取图像尺寸
        height, width = depth_img.shape

        # 生成像素坐标网格
        x, y = np.meshgrid(np.arange(width), np.arange(height))

        # 计算归一化坐标
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]

        # 创建有效深度掩码
        # 过滤掉深度值为0或过大的点（通常表示无效测量）
        valid_mask = (depth_img > 0) & (depth_img < 10000)  # 假设深度单位是毫米，最大有效距离为10米

        # 计算3D坐标
        Z = depth_img.astype(np.float32) / 1000.0  # 转换为米
        X = (x - cx) * Z / fx
        Y = (y - cy) * Z / fy

        # 只保留有效点
        valid_points = np.stack([X, Y, Z], axis=-1)[valid_mask]

        # 处理颜色数据
        # 将BGR转换为RGB，并打包成uint32格式
        rgb = rgb_img[valid_mask]
        rgb_packed = np.zeros(len(rgb), dtype=np.uint32)
        rgb_packed = (
            (rgb[:, 2].astype(np.uint32) << 16) | (rgb[:, 1].astype(np.uint32) << 8) | (rgb[:, 0].astype(np.uint32))
        )

        # 创建结构化数组
        dtype = np.dtype([("x", np.float32), ("y", np.float32), ("z", np.float32), ("rgb", np.uint32)])

        # 将点云数据组织成结构化数组
        cloud_array = np.zeros(len(valid_points), dtype=dtype)
        cloud_array["x"] = valid_points[:, 0]
        cloud_array["y"] = valid_points[:, 1]
        cloud_array["z"] = valid_points[:, 2]
        cloud_array["rgb"] = rgb_packed

        # 创建点云消息
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = self.camera_frame

        # 定义点云字段
        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="rgb", offset=12, datatype=PointField.UINT32, count=1),
        ]

        # 记录有效点的数量
        self.get_logger().debug(f"生成点云: 总点数 {height*width}, 有效点数 {len(valid_points)}")

        # 创建点云消息
        cloud_msg = point_cloud2.create_cloud(header, fields, cloud_array)
        return cloud_msg

    def load_images(self):
        """加载图像文件"""
        try:
            self.rgb = cv2.imread(self.rgb_path)
            if self.rgb is None:
                self.get_logger().error(f"无法加载RGB图像: {self.rgb_path}")
                return False

            self.depth = cv2.imread(self.depth_path, -1)
            if self.depth is None:
                self.get_logger().error(f"无法加载深度图像: {self.depth_path}")
                return False

            # 将OpenCV图像转换为ROS Image消息
            self.msg_rgb = self.bridge.cv2_to_imgmsg(self.rgb, "bgr8")
            self.msg_depth = self.bridge.cv2_to_imgmsg(self.depth, "mono16")
            return True
        except Exception as e:
            self.get_logger().error(f"加载图像时发生错误: {str(e)}")
            return False

    def update_image_source_callback(self, request, response):
        """处理更新图像源的请求

        Args:
            request: 包含新的图像源配置的请求
            response: 服务响应对象

        Returns:
            response: 包含操作结果的响应
        """
        try:
            with self._lock:
                # 停止timer
                if self.timer.is_canceled():
                    self.get_logger().warn("image_pub timer already stop")
                else:
                    self.get_logger().info("stop image_pub timer ...")
                    self.timer.cancel()
                    self.get_logger().info("stop image_pub timer finished")

                # 更新话题名称
                if request.color_topic:
                    self.destroy_publisher(self.pub_rgb)
                    self.rgb_topic = request.color_topic
                    self.pub_rgb = self.create_publisher(Image, self.rgb_topic, 1)
                    self.get_logger().info(f"已更新RGB话题为: {self.rgb_topic}")

                if request.depth_topic:
                    self.destroy_publisher(self.pub_depth)
                    self.depth_topic = request.depth_topic
                    self.pub_depth = self.create_publisher(Image, self.depth_topic, 1)
                    self.get_logger().info(f"已更新深度话题为: {self.depth_topic}")

                # 更新点云话题
                if hasattr(request, "cloud_topic") and request.cloud_topic:
                    if hasattr(self, "pub_cloud"):
                        self.destroy_publisher(self.pub_cloud)
                    self.cloud_topic = request.cloud_topic
                    if self.flag_publish_cloud:
                        self.pub_cloud = self.create_publisher(PointCloud2, self.cloud_topic, 1)
                        self.get_logger().info(f"已更新点云话题为: {self.cloud_topic}")

                # 更新文件路径
                if request.color_path:
                    self.rgb_path = request.color_path
                    self.get_logger().info(f"已更新RGB文件路径为: {self.rgb_path}")

                if request.depth_path:
                    self.depth_path = request.depth_path
                    self.get_logger().info(f"已更新深度文件路径为: {self.depth_path}")

                # 更新相机坐标系
                if request.camera_frame:
                    self.camera_frame = request.camera_frame
                    self.get_logger().info(f"已更新相机坐标系为: {self.camera_frame}")

                # 重新加载图片
                if not self.load_images():
                    response.success = False
                    response.message = "重新加载图像失败"
                    return response

                # 重新启动timer
                if self.timer.is_canceled():
                    self.timer.reset()
                    self.get_logger().info("start image_pub timer")
                else:
                    self.get_logger().warn("image_pub timer already start")

                response.success = True
                response.message = "成功更新图像源配置"

        except Exception as e:
            response.success = False
            response.message = f"更新图像源配置时发生错误: {str(e)}"
            self.get_logger().error(response.message)

        return response

    def publish_image(self):
        """发布图像消息和点云"""
        with self._lock:
            if not hasattr(self, "msg_rgb") or not hasattr(self, "msg_depth"):
                return

            current_time = self.get_clock().now().to_msg()

            # 发布RGB图像
            self.msg_rgb.header.frame_id = self.camera_frame
            self.msg_rgb.header.stamp = current_time
            self.pub_rgb.publish(self.msg_rgb)
            self.get_logger().debug("已发布RGB图像")

            # 发布深度图像
            self.msg_depth.header.frame_id = self.camera_frame
            self.msg_depth.header.stamp = current_time
            self.pub_depth.publish(self.msg_depth)
            self.get_logger().debug("已发布深度图像")

            # 发布相机信息
            if self.flag_publish_camera_info and hasattr(self, "camera_info_msg"):
                self.camera_info_msg.header.stamp = current_time
                self.pub_camera_info.publish(self.camera_info_msg)
                self.get_logger().debug("已发布相机信息")

            # 发布点云
            if self.flag_publish_cloud and self.camera_matrix is not None:
                cloud_msg = self.depth_to_pointcloud(self.depth, self.rgb)
                if cloud_msg is not None:
                    self.pub_cloud.publish(cloud_msg)
                    self.get_logger().debug("已发布点云数据")


def main(args=None):
    rclpy.init(args=args)

    # 创建节点
    image_publisher_node = ImagePublisherNode()

    # 创建多线程执行器
    executor = MultiThreadedExecutor(num_threads=2)  # 使用2个线程

    try:
        # 使用多线程执行器运行节点
        rclpy.spin(image_publisher_node, executor)
    except KeyboardInterrupt:
        pass
    finally:
        # 清理
        image_publisher_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
