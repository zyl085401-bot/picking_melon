#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from std_msgs.msg import Header
from cv_bridge import CvBridge
import cv2
import numpy as np
import os
import yaml
import glob
from datetime import datetime
import threading
import time
import sensor_msgs.msg as sensor_msgs
from sensor_msgs_py import point_cloud2


class RGBD2Cloud(Node):
    def __init__(self):
        super().__init__("rgbd2cloud")

        # 声明参数
        self.declare_parameter("data_path", "/workspace/rgbd_data")
        self.declare_parameter("publish_rate", 1.0)  # Hz

        # 获取参数
        self.data_path = self.get_parameter("data_path").get_parameter_value().string_value
        self.publish_rate = self.get_parameter("publish_rate").get_parameter_value().double_value

        # 创建发布器
        self.point_cloud_pub = self.create_publisher(PointCloud2, "/rgbd_cloud", 10)

        # 初始化CV bridge
        self.bridge = CvBridge()

        # 创建定时器
        self.timer = self.create_timer(1.0 / self.publish_rate, self.timer_callback)

        # 获取所有时间戳
        self.timestamps = self._get_timestamps()
        self.current_index = 0

        self.get_logger().info("RGBD2Cloud initialized")
        self.get_logger().info(f"Found {len(self.timestamps)} sets of data")

    def _get_timestamps(self):
        """获取所有可用的时间戳"""
        timestamps = set()

        # 从rgb文件名中获取时间戳
        rgb_files = glob.glob(os.path.join(self.data_path, "rgb", "*.png"))
        for f in rgb_files:
            timestamp = os.path.basename(f).replace("rgb_", "").replace(".png", "")
            if os.path.exists(os.path.join(self.data_path, "depth", f"depth_{timestamp}.png")) and os.path.exists(
                os.path.join(self.data_path, "camera_info", f"camera_info_{timestamp}.yaml")
            ):
                timestamps.add(timestamp)

        return sorted(list(timestamps))

    def _load_camera_info(self, timestamp):
        """加载相机信息"""
        info_path = os.path.join(self.data_path, "camera_info", f"camera_info_{timestamp}.yaml")
        with open(info_path, "r") as f:
            data = yaml.safe_load(f)

        camera_info = CameraInfo()
        camera_info.height = data["height"]
        camera_info.width = data["width"]
        camera_info.d = data["D"]

        # 将嵌套列表展平为一维数组
        camera_info.k = [item for sublist in data["K"] for item in sublist]
        camera_info.r = [item for sublist in data["R"] for item in sublist]
        camera_info.p = [item for sublist in data["P"] for item in sublist]
        camera_info.distortion_model = data["distortion_model"]

        return camera_info

    def _create_point_cloud(self, rgb_img, depth_img, camera_info):
        """从RGB和深度图像创建点云"""
        # 获取相机内参
        # 相机内参矩阵K是一个3x3矩阵，按行优先存储
        # [fx  0  cx]
        # [0  fy  cy]
        # [0   0   1]
        self.get_logger().info(f"Camera matrix K: {camera_info.k}")

        # 检查相机内参矩阵的大小
        if len(camera_info.k) != 9:
            self.get_logger().error(f"Invalid camera matrix size: {len(camera_info.k)}. Expected 9 elements.")
            raise ValueError("Invalid camera matrix size")

        fx = camera_info.k[0]  # 第一行第一列
        fy = camera_info.k[4]  # 第二行第二列
        cx = camera_info.k[2]  # 第一行第三列
        cy = camera_info.k[5]  # 第二行第三列

        self.get_logger().info(f"Camera parameters: fx={fx}, fy={fy}, cx={cx}, cy={cy}")

        # 创建点云数据
        height, width = depth_img.shape

        # 使用numpy进行向量化计算以提高性能
        v, u = np.indices((height, width))
        z = depth_img.astype(np.float32) / 1000.0  # 转换为米
        valid_mask = z > 0

        # 计算3D坐标
        x = np.multiply(u - cx, z) / fx
        y = np.multiply(v - cy, z) / fy

        # 获取有效点的RGB颜色并合并为一个float32值
        if len(rgb_img.shape) == 3:  # 确保是彩色图像
            r = rgb_img[:, :, 2][valid_mask].astype(np.uint32)  # BGR格式
            g = rgb_img[:, :, 1][valid_mask].astype(np.uint32)
            b = rgb_img[:, :, 0][valid_mask].astype(np.uint32)

            # 将RGB打包为float32格式 (与ROS2标准点云格式一致)
            rgb_packed = np.left_shift(r, 16) | np.left_shift(g, 8) | b
            rgb_packed = rgb_packed.view(np.float32)
        else:
            # 如果不是彩色图像，使用灰度值
            self.get_logger().warn("RGB image is not in color format")
            rgb_packed = np.zeros(valid_mask.sum(), dtype=np.float32)

        # 获取有效的3D坐标
        x = x[valid_mask]
        y = y[valid_mask]
        z = z[valid_mask]

        # 创建点云数据
        points = np.column_stack([x, y, z, rgb_packed])

        # 创建PointCloud2消息
        fields = [
            point_cloud2.PointField(name="x", offset=0, datatype=point_cloud2.PointField.FLOAT32, count=1),
            point_cloud2.PointField(name="y", offset=4, datatype=point_cloud2.PointField.FLOAT32, count=1),
            point_cloud2.PointField(name="z", offset=8, datatype=point_cloud2.PointField.FLOAT32, count=1),
            point_cloud2.PointField(name="rgb", offset=12, datatype=point_cloud2.PointField.FLOAT32, count=1),
        ]

        # 创建Header
        header = Header()
        header.frame_id = "camera_color_optical_frame"
        header.stamp = self.get_clock().now().to_msg()

        pc2_msg = point_cloud2.create_cloud(header=header, fields=fields, points=points)

        return pc2_msg

    def timer_callback(self):
        """定时器回调函数，用于发布点云"""
        if not self.timestamps:
            self.get_logger().warn("No data available")
            return

        try:
            # 获取当前时间戳
            timestamp = self.timestamps[self.current_index]

            # 加载RGB图像
            rgb_path = os.path.join(self.data_path, "rgb", f"rgb_{timestamp}.png")
            rgb_img = cv2.imread(rgb_path)
            if rgb_img is None:
                raise Exception(f"Failed to load RGB image: {rgb_path}")

            # 加载深度图像
            depth_path = os.path.join(self.data_path, "depth", f"depth_{timestamp}.png")
            depth_img = cv2.imread(depth_path, cv2.IMREAD_ANYDEPTH)
            if depth_img is None:
                raise Exception(f"Failed to load depth image: {depth_path}")

            # 加载相机信息
            camera_info = self._load_camera_info(timestamp)

            # 创建并发布点云
            pc2_msg = self._create_point_cloud(rgb_img, depth_img, camera_info)
            self.point_cloud_pub.publish(pc2_msg)

            self.get_logger().info(f"Published point cloud for timestamp: {timestamp}")

            # 更新索引
            self.current_index = (self.current_index + 1) % len(self.timestamps)

        except Exception as e:
            self.get_logger().error(f"Error publishing point cloud: {str(e)}")
            import traceback

            self.get_logger().error(traceback.format_exc())


def main(args=None):
    rclpy.init(args=args)
    node = RGBD2Cloud()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
