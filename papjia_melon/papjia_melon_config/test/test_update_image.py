#!/usr/bin/env python3
"""
Descripttion: 测试更新图像源服务和目标检测服务
version: 1.0
Author: 崔译文
Date: 2024-05-12
"""

import os
import rclpy
from time import sleep
from rclpy.node import Node
from papjia_vision_interface.srv import UpdateImageSource, DetectObjs
from ament_index_python.packages import get_package_share_directory


class VisionTestClient(Node):
    """视觉服务测试客户端"""

    def __init__(self):
        super().__init__("vision_test_client")
        # 创建更新图像源服务客户端
        self.update_client = self.create_client(UpdateImageSource, "/papjia_image_pub_node/update_image_source")
        while not self.update_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("等待更新图像源服务启动...")
        self.get_logger().info("更新图像源服务已就绪")

        # 创建目标检测服务客户端
        self.detect_client = self.create_client(DetectObjs, "/papjia/vision/local/object/detect")
        while not self.detect_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("等待目标检测服务启动...")
        self.get_logger().info("目标检测服务已就绪")

    def update_image_source(
        self, rgb_topic: str, depth_topic: str, camera_frame: str, color_path: str = "", depth_path: str = ""
    ) -> bool:
        """发送更新图像源请求

        Args:
            rgb_topic (str): RGB图像话题名称
            depth_topic (str): 深度图像话题名称
            camera_frame (str): 相机坐标系名称
            color_path (str, optional): 彩色图像路径. 默认为空字符串.
            depth_path (str, optional): 深度图像路径. 默认为空字符串.

        Returns:
            bool: 请求是否成功
        """
        request = UpdateImageSource.Request()
        request.color_topic = rgb_topic
        request.depth_topic = depth_topic
        request.camera_frame = camera_frame
        request.color_path = color_path
        request.depth_path = depth_path

        self.get_logger().info(
            f"发送更新图像源请求:\n"
            f"  RGB话题: {rgb_topic}\n"
            f"  深度话题: {depth_topic}\n"
            f"  坐标系: {camera_frame}\n"
            f"  彩色图像路径: {color_path}\n"
            f"  深度图像路径: {depth_path}"
        )

        future = self.update_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            response = future.result()
            self.get_logger().info(f"更新图像源服务响应: {response.message}")
            return response.success
        else:
            self.get_logger().error("更新图像源服务调用失败")
            return False

    def detect_objects(self, max_num: int = 10, min_score: float = 0.3) -> bool:
        """发送目标检测请求

        Args:
            max_num (int, optional): 最大检测目标数. 默认为10.
            min_score (float, optional): 最小置信度阈值. 默认为0.3.

        Returns:
            bool: 请求是否成功
        """
        request = DetectObjs.Request()
        request.max_num = max_num
        request.min_score = min_score

        self.get_logger().info(f"发送目标检测请求:\n" f"  最大目标数: {max_num}\n" f"  最小置信度: {min_score}")

        future = self.detect_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            response = future.result()
            if response.success:
                self.get_logger().info(f"检测到 {len(response.objects)} 个目标:")
                for i, obj in enumerate(response.objects):
                    self.get_logger().info(
                        f"  目标 {i+1}:\n"
                        f"    标签: {obj.category}\n"
                        f"    大小: {obj.scale}\n"
                        f"    位置: {obj.pose}"
                    )
            else:
                self.get_logger().warn("目标检测未成功")
            return response.success
        else:
            self.get_logger().error("目标检测服务调用失败")
            return False


def main(args=None):
    rclpy.init(args=args)

    # 创建客户端节点
    client = VisionTestClient()

    try:
        # 获取图像文件路径
        resource_dir = get_package_share_directory("papjia_melon_config")
        default_color_path = os.path.join(resource_dir, "resource/images/rgb_20250526_135948_989763.png")
        default_depth_path = os.path.join(resource_dir, "resource/images/depth_20250526_135948_989763.png")

        # 测试用例1：使用默认话题名称和图像路径
        success = client.update_image_source(
            rgb_topic="/camera/camera_hand/color/image_raw",
            depth_topic="/camera/camera_hand/aligned_depth_to_color/image_raw",
            camera_frame="camera_hand_color_optical_frame",
            color_path=default_color_path,
            depth_path=default_depth_path,
        )
        client.get_logger().info(f'测试用例1更新图像源结果: {"成功" if success else "失败"}')

        if success:
            # 等待图像更新完成
            client.get_logger().info("等待图像更新完成...")
            sleep(2.0)  # 等待2秒

            # 调用目标检测服务
            detect_success = client.detect_objects(max_num=10, min_score=0.3)
            client.get_logger().info(f'测试用例1目标检测结果: {"成功" if detect_success else "失败"}')

        # 测试用例2：使用新的话题名称和新的图像路径
        new_color_path = os.path.join(resource_dir, "resource/images/rgb_20250526_135258_004700.png")
        new_depth_path = os.path.join(resource_dir, "resource/images/depth_20250526_135258_004700.png")
        success = client.update_image_source(
            rgb_topic="/camera/camera_hand/color/image_raw",
            depth_topic="/camera/camera_hand/aligned_depth_to_color/image_raw",
            camera_frame="camera_hand_color_optical_frame",
            color_path=new_color_path,
            depth_path=new_depth_path,
        )
        client.get_logger().info(f'测试用例2更新图像源结果: {"成功" if success else "失败"}')

        if success:
            # 等待图像更新完成
            client.get_logger().info("等待图像更新完成...")
            sleep(2.0)  # 等待2秒

            # 调用目标检测服务
            detect_success = client.detect_objects(max_num=10, min_score=0.3)
            client.get_logger().info(f'测试用例2目标检测结果: {"成功" if detect_success else "失败"}')

    except Exception as e:
        client.get_logger().error(f"测试过程中发生错误: {str(e)}")
    finally:
        client.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
