"""
@Descripttion: 
@version: 
@Author: 崔译文
@Date: 2024-03-26 17:51:49
@LastEditors: 崔译文
@LastEditTime: 2024-05-08 15:13:45
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import os
import time

class ImageSubscriber(Node):
    def __init__(self):
        super().__init__("papjia_manual_record_camera")
        
        # 参数设置
        self.declare_parameter("topic_rgb", "/camera/rgb/image_raw")
        self.declare_parameter("save_path", "/home/lab/papjia_datas/papjia_manual_record_camera")
        
        # 获取参数
        topic_rgb = self.get_parameter("topic_rgb").get_parameter_value().string_value
        save_path = self.get_parameter("save_path").get_parameter_value().string_value
        
        # 订阅图像
        self.subscription = self.create_subscription(Image, topic_rgb, self.image_callback, 10)
        self.subscription  # 防止Python的垃圾回收机制清除订阅对象
        self.cv_bridge = CvBridge()
        self.cv_image = None
        self.lock = threading.Lock()
        
        # 每次运行本程序时重新建立文件夹
        current_time = time.time()
        timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(current_time))
        self.folder = os.path.join(save_path, timestamp_str)
        os.makedirs(self.folder)

    def image_callback(self, msg):
        try:
            # 将ROS图像消息转换为OpenCV图像
            with self.lock:
                self.cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error("Error converting ROS image to OpenCV image: %s" % str(e))
            return
        # 显示图像
        cv2.imshow("RT_Frame", self.cv_image)
        cv2.waitKey(1)

    def start_image_saving_thread(self):
        self.save_thread = threading.Thread(target=self.image_saving_thread)
        self.save_thread.start()

    def image_saving_thread(self):
        num = 0
        img = None
        while rclpy.ok():
            key = input("lock image ? ")
            if key == "n":
                continue
            if key == "q":
                break
            with self.lock:
                if self.cv_image is not None:
                    img = self.cv_image.copy()
            if img is not None:
                cv2.imshow("Locked Image", img)
                cv2.waitKey(10)
                key = input("save image ? ")
                if key == "n":
                    cv2.destroyWindow("Locked Image")
                    continue
                cv2.destroyWindow("Locked Image")
                fname = os.path.join(self.folder, "{0}.png".format(num))
                cv2.imwrite(fname, img)
                num += 1
                self.get_logger().info("saved {0}".format(fname))
            else:
                self.get_logger().info("no image")
        self.get_logger().info("Finished!")


def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    image_subscriber.start_image_saving_thread()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
