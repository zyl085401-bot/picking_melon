#!/usr/bin/env python3
#同时监听来自两个摄像头（一个在机械臂上，一个在基座上）、机器人关节和 TF 坐标变换的数据
import os
import cv2
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CameraInfo, JointState
from tf2_ros import Buffer, TransformListener
from builtin_interfaces.msg import Time
import json
import numpy as np
from datetime import datetime
from scipy.spatial.transform import Rotation as R  # <--- (修改) 导入 Scipy

class CalibDataSaver(Node):
    def __init__(self):
        super().__init__('calib_data_saver')
        self.bridge = CvBridge()

        # === Subscribers ===
        # Hand camera (for preview)
        self.hand_rgb_sub = self.create_subscription(Image, '/camera/camera_hand/color/image_raw', self.hand_rgb_cb, 10)
        self.hand_depth_sub = self.create_subscription(Image, '/camera/camera_hand/aligned_depth_to_color/image_raw', self.hand_depth_cb, 10)
        self.hand_info_sub = self.create_subscription(CameraInfo, '/camera/camera_hand/aligned_depth_to_color/camera_info', self.hand_info_cb, 10)

        # Joint states
        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.joint_cb, 10)

        # TF
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # === Buffers ===
        self.hand_rgb_msg = None
        self.hand_depth_msg = None
        self.hand_info = None
        self.joint_state = None

        # 保存路径
        self.save_dir = os.path.join(os.getcwd(), "calib_data")
        os.makedirs(self.save_dir, exist_ok=True)

        # 等待初始数据
        self.get_logger().info('Waiting for initial data...')
        while not self._data_ready():
            rclpy.spin_once(self, timeout_sec=0.1)
        self.get_logger().info("✅ CalibDataSaver 启动成功")
        self.get_logger().info("📌 正在预览手部相机图像")
        self.get_logger().info("📌 按下 's' 保存一帧完整数据，按下 'q' 退出")

        # OpenCV 显示窗口
        cv2.namedWindow("RGB Preview (Hand Camera)", cv2.WINDOW_AUTOSIZE)

    def _data_ready(self):
        """检查是否所有需要的数据都已经准备就绪"""
        return all([self.hand_rgb_msg, self.hand_depth_msg, self.hand_info,
                    self.joint_state])

    # === Callbacks ===
    def hand_rgb_cb(self, msg):
        self.hand_rgb_msg = msg

    def hand_depth_cb(self, msg):
        self.hand_depth_msg = msg

    def hand_info_cb(self, msg):
        self.hand_info = msg


    def joint_cb(self, msg):
        self.joint_state = msg

    # === 显示和保存主循环 ===
    def display_and_save(self):
        # 显示手部相机图像（预览）
        if self.hand_rgb_msg is not None:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(self.hand_rgb_msg, "bgr8")
                cv2.imshow("RGB Preview (Hand Camera)", cv_image)
            except Exception as e:
                self.get_logger().error(f"转换手部相机图像失败: {e}")

        # 检查按键
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            self.save_data()
        elif key == ord('q'):
            return False  # 退出信号
        return True

    # === 保存数据 ===
    def save_data(self):
        # 检查所有数据是否就绪
        required = [
            self.hand_rgb_msg, self.hand_depth_msg, self.hand_info,
            self.joint_state
        ]
        if not all(required):
            missing = ["hand_rgb", "hand_depth", "hand_info", "joint_state"]
            missing_items = [m for m, v in zip(missing, required) if v is None]
            self.get_logger().warn(f"数据不完整，无法保存！缺失: {missing_items}")
            return

 
        # --- 1. 获取ROS时间戳 (来自手部相机) ---
        stamp: Time = self.hand_rgb_msg.header.stamp
        # --- 2. 将ROS时间戳的 .sec 部分 (Unix时间戳) 转换为 datetime 对象 ---
        dt_object = datetime.fromtimestamp(stamp.sec)
        # --- 3. 格式化为 "YYYYMMDD_HHMMSS" 字符串 ---
        timestamp_str = dt_object.strftime("%Y%m%d_%H%M%S")
        # --- 4. 使用新的字符串作为文件夹名 ---
        save_path = os.path.join(self.save_dir, timestamp_str)
        os.makedirs(save_path, exist_ok=True)

        try:
            # --- 保存手部相机 ---
            hand_rgb_cv = self.bridge.imgmsg_to_cv2(self.hand_rgb_msg, "bgr8")
            hand_depth_cv = self.bridge.imgmsg_to_cv2(self.hand_depth_msg, "passthrough")
            cv2.imwrite(os.path.join(save_path, "hand_rgb.png"), hand_rgb_cv)
            cv2.imwrite(os.path.join(save_path, "hand_depth.png"), hand_depth_cv.astype(np.uint16))

            with open(os.path.join(save_path, "hand_camera_info.json"), "w") as f:
                json.dump(self.msg_to_dict(self.hand_info), f, indent=2)

            # --- 保存关节角 ---
            joint_data = {
                "name": list(self.joint_state.name),
                "position": list(self.joint_state.position),
                "velocity": list(self.joint_state.velocity),
                "effort": list(self.joint_state.effort),
            }

            # --- 保存 TF (包含 RPY) --- (使用 Scipy 修改)
            tf_data = {}
            try:
                # 1. 查询 'base_link' -> 'shears'
                t1 = self.tf_buffer.lookup_transform("base_link", "shears", rclpy.time.Time())
                t1_dict = self.tf_to_dict(t1) # {translation: [...], rotation: [x,y,z,w]}
                
                # 2. 计算 t1 的 RPY (角度)
                q1 = t1_dict["rotation"] # [x, y, z, w]
                r1 = R.from_quat(q1)
                # 'xyz' 对应 roll, pitch, yaw。 degrees=True 直接输出角度
                rpy1_degrees = r1.as_euler('xyz', degrees=True) 
                t1_dict["rpy_degrees"] = list(rpy1_degrees) # 转为 list 方便 JSON 序列化
                
                # 3. 查询 'base_link' -> 'camera_hand_link'
                t2 = self.tf_buffer.lookup_transform("base_link", "camera_hand_link", rclpy.time.Time())
                t2_dict = self.tf_to_dict(t2) # {translation: [...], rotation: [x,y,z,w]}

                # 4. 计算 t2 的 RPY (角度)
                q2 = t2_dict["rotation"]
                r2 = R.from_quat(q2)
                rpy2_degrees = r2.as_euler('xyz', degrees=True)
                t2_dict["rpy_degrees"] = list(rpy2_degrees) # 转为 list 方便 JSON 序列化

                # 5. 存入 tf_data
                tf_data["base_link_to_shears"] = t1_dict
                tf_data["base_link_to_camera_hand_link"] = t2_dict

            except Exception as e:
                self.get_logger().warn(f"TF 查询失败: {e}")

            # --- 保存 meta.json ---
            meta = {
                "timestamp_ros": f"{stamp.sec}_{stamp.nanosec}", # 原始高精度时间戳
                "timestamp_human": timestamp_str,                # 您需要的新格式
                "joints": joint_data,
                "tf": tf_data  # tf_data 现在自动包含了 rpy_degrees
            }
            with open(os.path.join(save_path, "meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

            self.get_logger().info(f"✅ 数据已保存到: {save_path}")

        except Exception as e:
            self.get_logger().error(f"保存数据时出错: {e}")

    # === 辅助函数 ===
    def msg_to_dict(self, msg):
        # (此函数无变化)
        return {
            "header": {
                "frame_id": msg.header.frame_id,
                "stamp": {"sec": msg.header.stamp.sec, "nanosec": msg.header.stamp.nanosec}
            },
            "height": msg.height,
            "width": msg.width,
            "k": list(msg.k),
            "d": list(msg.d),
            "r": list(msg.r),
            "p": list(msg.p),
            "distortion_model": msg.distortion_model
        }

    def tf_to_dict(self, tf_msg):
        # (此函数无变化)
        t = tf_msg.transform.translation
        r = tf_msg.transform.rotation
        return {
            "translation": [t.x, t.y, t.z],
            "rotation": [r.x, r.y, r.z, r.w]
        }


def main():
    rclpy.init()
    node = CalibDataSaver()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)  # 快速响应
            if not node.display_and_save():  # 显示 + 按键处理
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()
        print("👋 程序已退出")


if __name__ == "__main__":
    main()