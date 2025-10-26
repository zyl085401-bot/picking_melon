#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import os
from datetime import datetime
import yaml
import threading

class RGBDSaver(Node):
    def __init__(self):
        super().__init__('rgbd_saver')

        # ====== 参数声明 ======
        # hand 相机
        self.declare_parameter('rgb_topic_hand', '/camera/camera_hand/color/image_raw')
        self.declare_parameter('depth_topic_hand', '/camera/camera_hand/aligned_depth_to_color/image_raw')
        self.declare_parameter('camera_info_topic_hand', '/camera/camera_hand/aligned_depth_to_color/camera_info')
        self.declare_parameter('save_path_hand', '/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data/image/hand')

        # base 相机
        self.declare_parameter('rgb_topic_base', '/camera/camera_base/color/image_raw')
        self.declare_parameter('depth_topic_base', '/camera/camera_base/aligned_depth_to_color/image_raw')
        self.declare_parameter('camera_info_topic_base', '/camera/camera_base/aligned_depth_to_color/camera_info')
        self.declare_parameter('save_path_base', '/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data/image/base')

        # 保存按键
        self.declare_parameter('save_key', 's')

        # ====== 参数获取 ======
        self._initialize_parameters()

        # 创建保存目录
        for p in [self.save_path_hand, self.save_path_base]:
            os.makedirs(os.path.join(p, 'rgb'), exist_ok=True)
            os.makedirs(os.path.join(p, 'depth'), exist_ok=True)
            os.makedirs(os.path.join(p, 'camera_info'), exist_ok=True)

        # ====== 内部变量 ======
        self.bridge = CvBridge()
        self._initialize_variables_and_subscriptions()

        # 等待直到初始数据被接收
        self.get_logger().info('Waiting for initial data...')
        while rclpy.ok() and not self._data_ready():
            rclpy.spin_once(self, timeout_sec=0.1)
        self.get_logger().info('Initial data received.')

        self.timer = self.create_timer(0.1, self.display_and_listen)

    def _initialize_parameters(self):
        """初始化参数"""
        # hand
        self.rgb_topic_hand = self.get_parameter('rgb_topic_hand').get_parameter_value().string_value
        self.depth_topic_hand = self.get_parameter('depth_topic_hand').get_parameter_value().string_value
        self.camera_info_topic_hand = self.get_parameter('camera_info_topic_hand').get_parameter_value().string_value
        self.save_path_hand = self.get_parameter('save_path_hand').get_parameter_value().string_value

        # base
        self.rgb_topic_base = self.get_parameter('rgb_topic_base').get_parameter_value().string_value
        self.depth_topic_base = self.get_parameter('depth_topic_base').get_parameter_value().string_value
        self.camera_info_topic_base = self.get_parameter('camera_info_topic_base').get_parameter_value().string_value
        self.save_path_base = self.get_parameter('save_path_base').get_parameter_value().string_value

        self.save_key = self.get_parameter('save_key').get_parameter_value().string_value

    def _initialize_variables_and_subscriptions(self):
        """初始化内部变量和订阅者"""
        # hand
        self.latest_rgb_hand = None
        self.latest_depth_hand = None
        self.latest_info_hand = None
        self.rgb_lock_hand = threading.Lock()
        self.depth_lock_hand = threading.Lock()
        self.info_lock_hand = threading.Lock()

        # base
        self.latest_rgb_base = None
        self.latest_depth_base = None
        self.latest_info_base = None
        self.rgb_lock_base = threading.Lock()
        self.depth_lock_base = threading.Lock()
        self.info_lock_base = threading.Lock()

        # 订阅者
        self.rgb_sub_hand = self.create_subscription(Image, self.rgb_topic_hand, self.rgb_callback_hand, 10)
        self.depth_sub_hand = self.create_subscription(Image, self.depth_topic_hand, self.depth_callback_hand, 10)
        self.info_sub_hand = self.create_subscription(CameraInfo, self.camera_info_topic_hand, self.info_callback_hand, 10)

        self.rgb_sub_base = self.create_subscription(Image, self.rgb_topic_base, self.rgb_callback_base, 10)
        self.depth_sub_base = self.create_subscription(Image, self.depth_topic_base, self.depth_callback_base, 10)
        self.info_sub_base = self.create_subscription(CameraInfo, self.camera_info_topic_base, self.info_callback_base, 10)

    def _data_ready(self):
        """检查是否所有数据都已准备好"""
        return (self.latest_rgb_hand is not None and self.latest_depth_hand is not None and
            self.latest_rgb_base is not None and self.latest_depth_base is not None)

    def camera_info_to_dict(self, camera_info):
        ...

    def rgb_callback_hand(self, msg):
        try:
            with self.rgb_lock_hand:
                self.latest_rgb_hand = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                self.get_logger().debug("Received new RGB image from hand camera.")
        except Exception as e:
            self.get_logger().error(f'Error converting RGB hand: {str(e)}')

    def depth_callback_hand(self, msg):
        try:
            with self.depth_lock_hand:
                self.latest_depth_hand = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
                self.get_logger().debug("Received new Depth image from hand camera.")
        except Exception as e:
            self.get_logger().error(f'Error converting depth hand: {str(e)}')

    def info_callback_hand(self, msg):
        with self.info_lock_hand:
            self.latest_info_hand = msg
            self.get_logger().debug("Received new Camera Info from hand camera.")

    def rgb_callback_base(self, msg):
        try:
            with self.rgb_lock_base:
                self.latest_rgb_base = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                self.get_logger().debug("Received new RGB image from base camera.")
        except Exception as e:
            self.get_logger().error(f'Error converting RGB base: {str(e)}')

    def depth_callback_base(self, msg):
        try:
            with self.depth_lock_base:
                self.latest_depth_base = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
                self.get_logger().debug("Received new Depth image from base camera.")
        except Exception as e:
            self.get_logger().error(f'Error converting depth base: {str(e)}')

    def info_callback_base(self, msg):
        with self.info_lock_base:
            self.latest_info_base = msg
            self.get_logger().debug("Received new Camera Info from base camera.")

    def save_images_and_info(self):
        if not self._data_ready():
            self.get_logger().warn('Not all data available for BOTH cameras.')
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

        try:
            # hand 相机
            with self.rgb_lock_hand:
                cv2.imwrite(os.path.join(self.save_path_hand, 'rgb', f'rgb_{timestamp}.png'), self.latest_rgb_hand)
            with self.depth_lock_hand:
                cv2.imwrite(os.path.join(self.save_path_hand, 'depth', f'depth_{timestamp}.png'), self.latest_depth_hand.astype(np.uint16))
            with self.info_lock_hand:
                info_dict = self.camera_info_to_dict(self.latest_info_hand)
                with open(os.path.join(self.save_path_hand, 'camera_info', f'camera_info_{timestamp}.yaml'), 'w') as f:
                    yaml.dump(info_dict, f)

            # base 相机
            with self.rgb_lock_base:
                cv2.imwrite(os.path.join(self.save_path_base, 'rgb', f'rgb_{timestamp}.png'), self.latest_rgb_base)
            with self.depth_lock_base:
                cv2.imwrite(os.path.join(self.save_path_base, 'depth', f'depth_{timestamp}.png'), self.latest_depth_base.astype(np.uint16))
            with self.info_lock_base:
                info_dict = self.camera_info_to_dict(self.latest_info_base)
                with open(os.path.join(self.save_path_base, 'camera_info', f'camera_info_{timestamp}.yaml'), 'w') as f:
                    yaml.dump(info_dict, f)

            self.get_logger().info(f'Data saved for BOTH cameras: {timestamp}')
        except Exception as e:
            self.get_logger().error(f'Error saving data: {str(e)}')

    def display_and_listen(self):
        if self.latest_rgb_hand is not None:
            with self.rgb_lock_hand:
                cv2.imshow("RGB Hand (press 's' to save both cameras)", self.latest_rgb_hand)

        if self.latest_rgb_base is not None:
            with self.rgb_lock_base:
                cv2.imshow("RGB Base", self.latest_rgb_base)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(self.save_key):
            self.save_images_and_info()

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = RGBDSaver()
        rclpy.spin(node)
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()


















    