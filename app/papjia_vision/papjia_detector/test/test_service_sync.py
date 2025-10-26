"""
Descripttion: 同步方式测试service是否正常工作
version: 1.0
Author: 崔译文
Date: 2023-12-20 11:19:43
@LastEditors: 崔译文
@LastEditTime: 2024-05-21 08:43:30
"""

import os
import cv2
import time
import rclpy
import numpy as np
import argparse
from rclpy.node import Node
from cv_bridge import CvBridge
from papjia_vision_interface.srv import SegImage
from papjia_logger.logger import logger
from threading import Thread
from ament_index_python.packages import get_package_share_directory


class ClientExample(Node):
    """一个一部service的client

    Args:
        Node (rclpy.node.Node): ros2的Node类
    """

    def __init__(self, image_path=None):
        super().__init__("client_sync")
        # 创建service的client
        self.cli = self.create_client(SegImage, "/papjia_vision/service_image_segment")
        # 等待service启动
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("service not available, waiting again...")
        # 创建service的request数据结构
        self.req = SegImage.Request()
        # cv bridge，用于sensor_msgs/Image和opencv图像间数据转换
        self.bridge = CvBridge()

        # 读取文件
        if image_path is None:
            # 如果没有提供图像路径，使用默认图像
            self.img = cv2.imread(
                os.path.join(
                    get_package_share_directory("papjia_detector"),
                    "resource/images",
                    "sample_glass_tube.jpg",
                )
            )
        else:
            # 使用提供的图像路径
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            self.img = cv2.imread(image_path)
            if self.img is None:
                raise ValueError(f"Failed to read image: {image_path}")

        # 转成sensor_msgs/Image
        msg = self.bridge.cv2_to_imgmsg(self.img, encoding="bgr8")
        self.req.image = msg
        self.req.max_num = 20
        self.req.min_score = 0.3

    def send_request(self):
        # 同步调用service
        return self.cli.call(self.req)


def test_service_sync(image_path=None):
    rclpy.init(args=None)

    try:
        client = ClientExample(image_path)

        spin_thread = Thread(target=rclpy.spin, args=(client,))
        spin_thread.start()
        n = 5
        while n > 0:
            start = time.perf_counter()
            res = client.send_request()  # 异步调用service
            end = time.perf_counter()
            logger.info("time usage %f", end - start)
            logger.info("sync objs num %d", res.objs_num)
            n -= 1
            if n == 0:
                alpha = 0.5
                beta = 1.0 - alpha
                # 掩码图像
                h, w = client.img.shape[0:2]
                print(w, h)
                img2 = np.zeros((h, w, 3), np.uint8)
                img_blending = client.img.copy()
                if res.with_mask:
                    # 转换为Opencv格式图像
                    mask = client.bridge.imgmsg_to_cv2(res.mask)
                    img2[mask > 0, :] = [0, 0, 150]
                    img_blending = cv2.addWeighted(
                        src1=client.img, alpha=alpha, src2=img2, beta=beta, gamma=0.0
                    )
                for i in range(res.objs_num):
                    rect = res.objects.objects[i].rect
                    # 添加rect
                    cv2.rectangle(
                        img_blending,
                        (rect.x1, rect.y1),
                        (rect.x2, rect.y2),
                        (100, 200, 0),
                        2,
                        lineType=cv2.LINE_AA,
                    )
                    print(res.objects.objects[i].category, res.objects.objects[i].rect)
                    # 添加类别
                    cv2.putText(
                        img_blending,
                        res.objects.objects[i].category,
                        (rect.x1, max(rect.y1 - 5, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 200, 200),
                        1,
                    )
                cv2.imshow("mask", img_blending)
                cv2.waitKey(1000 * 10)
                cv2.destroyAllWindows()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        client.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test image segmentation service")
    parser.add_argument("--image", type=str, help="Path to the input image")
    args = parser.parse_args()

    test_service_sync(args.image)
