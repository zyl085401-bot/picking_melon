#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
from sensor_msgs.msg import JointState
from geometry_msgs.msg import TransformStamped
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import time
import math


class CombinedDataSaver(Node):
    def __init__(self):
        super().__init__("combined_data_saver")

        # ======================================
        # 📁 用户配置：统一保存目录
        # ======================================
        self.save_dir = Path("/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data")
        self.save_dir.mkdir(parents=True, exist_ok=True)  # 自动创建

        # ======================================
        # 🧭 TF 配置
        # ======================================
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # ======================================
        # 🤖 关节角配置
        # ======================================
        self.arm_joint_names = [f'arm_joint{i}' for i in range(1, 7)]
        self.latest_joint_state = None
        self.joint_received = False

        from rclpy.qos import qos_profile_sensor_data
        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_callback,
            qos_profile_sensor_data
        )

        self.get_logger().info("✅ 初始化完成，等待数据...")

        # 延迟 2 秒后采集一次
        self.timer = self.create_timer(2.0, self.save_combined_data)
        self.timer_done = False

    def joint_callback(self, msg):
        self.latest_joint_state = msg
        self.joint_received = True

    def quaternion_to_rpy(self, x, y, z, w):
        """四元数转 RPY（弧度和角度）"""
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (w * y - z * x)
        pitch = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(1.0, sinp) * math.pi / 2

        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return {
            "roll_radian": roll,
            "pitch_radian": pitch,
            "yaw_radian": yaw,
            "roll_degree": round(np.degrees(roll).item(), 6),
            "pitch_degree": round(np.degrees(pitch).item(), 6),
            "yaw_degree": round(np.degrees(yaw).item(), 6),
        }

    def transform_to_matrix(self, trans):
        """构建 4x4 齐次变换矩阵"""
        from scipy.spatial.transform import Rotation as R
        t = trans.transform.translation
        q = trans.transform.rotation
        rotation = R.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
        matrix = np.eye(4)
        matrix[0:3, 0:3] = rotation
        matrix[0:3, 3] = [t.x, t.y, t.z]
        return matrix.tolist()

    def save_combined_data(self):
        if self.timer_done:
            return
        self.timer_done = True

        # 全局时间戳（同步用）
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # 构建最终 JSON 数据
        combined_data = {
            "capture_timestamp": {
                "system": system_time,
                "sync_id": timestamp_str  # 用于外部关联
            },
            "tf_shears_to_base_link": None,
            "arm_joint_angles": None
        }

        # ========================
        # 1️⃣ 获取 TF 数据
        # ========================
        try:
            trans: TransformStamped = self.tf_buffer.lookup_transform(
                "base_link", "shears", rclpy.time.Time()
            )

            quat = trans.transform.rotation
            rpy_data = self.quaternion_to_rpy(quat.x, quat.y, quat.z, quat.w)
            matrix_4x4 = self.transform_to_matrix(trans)

            combined_data["tf_shears_to_base_link"] = {
                "source_frame": trans.child_frame_id,
                "target_frame": trans.header.frame_id,
                "ros_timestamp": {
                    "sec": trans.header.stamp.sec,
                    "nanosec": trans.header.stamp.nanosec
                },
                "translation": {
                    "x": round(trans.transform.translation.x, 6),
                    "y": round(trans.transform.translation.y, 6),
                    "z": round(trans.transform.translation.z, 6)
                },
                "rotation_quaternion": {
                    "x": round(quat.x, 6),
                    "y": round(quat.y, 6),
                    "z": round(quat.z, 6),
                    "w": round(quat.w, 6)
                },
                "rotation_rpy": rpy_data,
                "transformation_matrix_4x4": [[round(m, 6) for m in row] for row in matrix_4x4]
            }

            self.get_logger().info("✅ TF 数据已获取")

        except Exception as e:
            self.get_logger().warn(f"⚠️ TF 数据获取失败: {e}")
            combined_data["tf_shears_to_base_link"] = {"error": str(e)}

        # ========================
        # 2️⃣ 获取关节角数据
        # ========================
        try:
            timeout = 3.0
            start_time = time.time()
            while rclpy.ok() and not self.joint_received:
                rclpy.spin_once(self, timeout_sec=0.1)
                if (time.time() - start_time) > timeout:
                    raise TimeoutError("未收到 /joint_states")

            if not self.joint_received:
                raise RuntimeError("joint_state 未更新")

            msg = self.latest_joint_state
            name_to_pos = dict(zip(msg.name, msg.position))
            joint_angles = {}
            for j in self.arm_joint_names:
                angle = name_to_pos.get(j, float('nan'))
                joint_angles[j] = round(angle, 6) if not math.isnan(angle) else None

            combined_data["arm_joint_angles"] = joint_angles
            self.get_logger().info("✅ 关节角数据已获取")

        except Exception as e:
            self.get_logger().warn(f"⚠️ 关节角数据获取失败: {e}")
            combined_data["arm_joint_angles"] = {"error": str(e)}

        # ========================
        # 3️⃣ 获取 base_link 到 camera_hand_link 的 TF 数据
        # ========================
        try:
            trans_camera: TransformStamped = self.tf_buffer.lookup_transform(
                "base_link", "camera_hand_link", rclpy.time.Time()
            )

            quat_camera = trans_camera.transform.rotation
            rpy_data_camera = self.quaternion_to_rpy(quat_camera.x, quat_camera.y, quat_camera.z, quat_camera.w)
            matrix_4x4_camera = self.transform_to_matrix(trans_camera)

            combined_data["tf_camera_hand_to_base_link"] = {
                "source_frame": trans_camera.child_frame_id,
                "target_frame": trans_camera.header.frame_id,
                "ros_timestamp": {
                    "sec": trans_camera.header.stamp.sec,
                    "nanosec": trans_camera.header.stamp.nanosec
                },
                "translation": {
                    "x": round(trans_camera.transform.translation.x, 6),
                    "y": round(trans_camera.transform.translation.y, 6),
                    "z": round(trans_camera.transform.translation.z, 6)
                },
                "rotation_quaternion": {
                    "x": round(quat_camera.x, 6),
                    "y": round(quat_camera.y, 6),
                    "z": round(quat_camera.z, 6),
                    "w": round(quat_camera.w, 6)
                },
                "rotation_rpy": rpy_data_camera,
                "transformation_matrix_4x4": [[round(m, 6) for m in row] for row in matrix_4x4_camera]
            }

            self.get_logger().info("✅ camera_hand_link 到 base_link 的 TF 数据已获取")

        except Exception as e:
            self.get_logger().warn(f"⚠️ camera_hand_link 到 base_link 的 TF 数据获取失败: {e}")
            combined_data["tf_camera_hand_to_base_link"] = {"error": str(e)}


        # ========================
        # 💾 保存为单个 JSON 文件
        # ========================
        filename = f"calibration_data_{timestamp_str}.json"
        file_path = self.save_dir / filename

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=4, ensure_ascii=False)
            self.get_logger().info(f"📁 所有数据已保存到: {file_path}")
        except Exception as e:
            self.get_logger().error(f"❌ 文件保存失败: {e}")

        # 结束
        self.get_logger().info("🏁 数据采集与保存完成，节点退出。")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = CombinedDataSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()