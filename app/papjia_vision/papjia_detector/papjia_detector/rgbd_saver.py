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

        # 参数
        self.declare_parameter('rgb_topic', '/camera/camera/color/image_raw')
        self.declare_parameter('depth_topic', '/camera/camera/aligned_depth_to_color/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera/aligned_depth_to_color/camera_info')
        self.declare_parameter('save_path', '/workspace/rgbd_data/rgbd_hand_data')
        self.declare_parameter('save_key', 's')

        self.rgb_topic = self.get_parameter('rgb_topic').get_parameter_value().string_value
        self.depth_topic = self.get_parameter('depth_topic').get_parameter_value().string_value
        self.camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        self.save_path = self.get_parameter('save_path').get_parameter_value().string_value
        self.save_key = self.get_parameter('save_key').get_parameter_value().string_value

        os.makedirs(os.path.join(self.save_path, 'rgb'), exist_ok=True)
        os.makedirs(os.path.join(self.save_path, 'depth'), exist_ok=True)
        os.makedirs(os.path.join(self.save_path, 'camera_info'), exist_ok=True)

        self.bridge = CvBridge()

        self.latest_rgb = None
        self.latest_depth = None
        self.latest_camera_info = None
        self.rgb_lock = threading.Lock()
        self.depth_lock = threading.Lock()
        self.camera_info_lock = threading.Lock()

        self.rgb_sub = self.create_subscription(Image, self.rgb_topic, self.rgb_callback, 10)
        self.depth_sub = self.create_subscription(Image, self.depth_topic, self.depth_callback, 10)
        self.camera_info_sub = self.create_subscription(CameraInfo, self.camera_info_topic, self.camera_info_callback, 10)

        # 用 timer 替代 keyboard 监听线程
        self.timer = self.create_timer(0.1, self.display_and_listen)

        self.get_logger().info('RGBD Saver initialized')
        self.get_logger().info(f'Press "{self.save_key}" in the image window to save images and camera info')

    def camera_info_to_dict(self, camera_info):
        return {
            'header': {
                'frame_id': camera_info.header.frame_id,
                'stamp': {
                    'sec': camera_info.header.stamp.sec,
                    'nanosec': camera_info.header.stamp.nanosec
                }
            },
            'height': camera_info.height,
            'width': camera_info.width,
            'distortion_model': camera_info.distortion_model,
            'D': camera_info.d.tolist(),
            'K': np.array(camera_info.k).reshape(3, 3).tolist(),
            'R': np.array(camera_info.r).reshape(3, 3).tolist(),
            'P': np.array(camera_info.p).reshape(3, 4).tolist(),
            'binning_x': camera_info.binning_x,
            'binning_y': camera_info.binning_y,
            'roi': {
                'x_offset': camera_info.roi.x_offset,
                'y_offset': camera_info.roi.y_offset,
                'height': camera_info.roi.height,
                'width': camera_info.roi.width,
                'do_rectify': camera_info.roi.do_rectify
            }
        }

    def rgb_callback(self, msg):
        try:
            with self.rgb_lock:
                self.latest_rgb = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f'Error converting RGB image: {str(e)}')

    def depth_callback(self, msg):
        try:
            with self.depth_lock:
                self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception as e:
            self.get_logger().error(f'Error converting depth image: {str(e)}')

    def camera_info_callback(self, msg):
        with self.camera_info_lock:
            self.latest_camera_info = msg

    def save_images_and_info(self):
        if self.latest_rgb is None or self.latest_depth is None or self.latest_camera_info is None:
            self.get_logger().warn('Not all data available to save')
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        try:
            with self.rgb_lock:
                rgb_path = os.path.join(self.save_path, 'rgb', f'rgb_{timestamp}.png')
                cv2.imwrite(rgb_path, self.latest_rgb)

            with self.depth_lock:
                depth_path = os.path.join(self.save_path, 'depth', f'depth_{timestamp}.png')
                cv2.imwrite(depth_path, self.latest_depth.astype(np.uint16))

            with self.camera_info_lock:
                info_dict = self.camera_info_to_dict(self.latest_camera_info)
                info_path = os.path.join(self.save_path, 'camera_info', f'camera_info_{timestamp}.yaml')
                with open(info_path, 'w') as f:
                    yaml.dump(info_dict, f)

            self.get_logger().info(f'Data saved: {timestamp}')
        except Exception as e:
            self.get_logger().error(f'Error saving data: {str(e)}')

    def display_and_listen(self):
        if self.latest_rgb is not None:
            with self.rgb_lock:
                cv2.imshow("RGB Image (press 's' to save)", self.latest_rgb)
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
