"""
Descripttion: 同步方式测试service是否正常工作
version: 1.0
Author: 崔译文
Date: 2023-12-20 11:19:43
@LastEditors: 崔译文
@LastEditTime: 2024-05-21 08:43:30
"""
import cv2
import time
import rclpy
import numpy as np
import os
from rclpy.node import Node
from cv_bridge import CvBridge
from papjia_vision_interface.srv import SegImage
from papjia_logger.logger import logger
from threading import Thread


class ClientExample(Node):
    """一个异步service的client

    Args:
        Node (rclpy.node.Node): ros2的Node类
    """

    def __init__(self):
        super().__init__("client_async")
        # 创建service的client
        self.cli = self.create_client(
            SegImage, "/papjia_vision/service_image_segment"
        )
        # 等待service启动
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("service not available, waiting again...")
        # 创建service的request数据结构
        self.req = SegImage.Request()
        # cv bridge，用于sensor_msgs/Image和opencv图像间数据转换
        self.bridge = CvBridge()

    def set_image(self, image_path):
        # 读取文件
        self.img = cv2.imread(image_path)
        # 转成sensor_msgs/Image
        msg = self.bridge.cv2_to_imgmsg(self.img, encoding="bgr8")
        self.req.image = msg
        self.req.max_num = 20
        self.req.min_score = 0.1

    def send_request(self):
        # 同步调用service
        return self.cli.call(self.req)


def test_service_dir_sync(image_folder):
    rclpy.init(args=None)

    client = ClientExample()
    spin_thread = Thread(target=rclpy.spin, args=(client,))
    spin_thread.daemon = True
    spin_thread.start()

    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

    try:
        for image_file in os.listdir(image_folder):
            image_path = os.path.join(image_folder, image_file)
            if not os.path.isfile(image_path) or not image_file.lower().endswith(valid_extensions):
                continue

            client.set_image(image_path)

            start = time.perf_counter()
            res = client.send_request()  # 同步调用service
            end = time.perf_counter()
            logger.info("seg %s time usage %f", image_file, end - start)
            logger.info("sync objs num %d", res.objs_num)

            if res.objs_num == 0:
                cv2.imshow("mask", client.img)
                cv2.waitKey(1000 * 10)
                continue
            alpha = 0.5
            beta = 1.0 - alpha
            # 掩码图像
            h, w = client.img.shape[0:2]
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
                logger.info("rect area:%.2f", (rect.y2 - rect.y1) * (rect.x2 - rect.x1))
                # 添加rect
                cv2.rectangle(
                    img_blending,
                    (rect.x1, rect.y1),
                    (rect.x2, rect.y2),
                    (100, 200, 0),
                    1,
                    lineType=cv2.LINE_AA,
                )
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
    except KeyboardInterrupt:
        pass
    finally:
        client.destroy_node()
        rclpy.shutdown()


# 使用示例
test_service_dir_sync("/home/yw/projects/小功能/rect1")
# test_service_dir_sync("/home/yw/projects/detectron2_we/datasets/Lane/val")
