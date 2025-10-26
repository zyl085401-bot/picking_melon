
 #!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
import json
from pathlib import Path
from datetime import datetime
import numpy as np


class TFListener(Node):
    def __init__(self):
        super().__init__("tf_data_saver")
        # ✅ 设置保存目录（可修改）
        self.save_directory = Path("/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data/shears_tf").expanduser()

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        # 延迟 1.5 秒，确保 TF 树建立
        self.timer = self.create_timer(1.5, self.lookup_and_save_full_transform)

    def quaternion_to_rpy(self, x, y, z, w):
        """将四元数转换为 RPY（弧度和角度）"""
        import math
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        pitch = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(1.0, sinp) * math.pi / 2

        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return {
            "roll_radian": roll,
            "pitch_radian": pitch,
            "yaw_radian": yaw,
            "roll_degree": np.degrees(roll).item(),
            "pitch_degree": np.degrees(pitch).item(),
            "yaw_degree": np.degrees(yaw).item(),
        }

    def transform_to_matrix(self, trans):
        """构建 4x4 齐次变换矩阵"""
        from scipy.spatial.transform import Rotation as R
        t = trans.transform.translation
        q = trans.transform.rotation

        # 平移向量
        translation = np.array([t.x, t.y, t.z])
        # 旋转矩阵（由四元数）
        rotation = R.from_quat([q.x, q.y, q.z, q.w]).as_matrix()

        # 构建齐次变换矩阵
        matrix = np.eye(4)
        matrix[0:3, 0:3] = rotation
        matrix[0:3, 3] = translation

        return matrix.tolist()  # 转为 Python list，便于 JSON 序列化

    def lookup_and_save_full_transform(self):
        try:
            # 查询 shears -> base_link 的变换
            trans: TransformStamped = self.tf_buffer.lookup_transform(
                "base_link",   # 目标坐标系
                "camera_base_link",      # 源坐标系
                rclpy.time.Time()  # 最新可用
            )

            # 计算 RPY
            quat = trans.transform.rotation
            rpy_data = self.quaternion_to_rpy(quat.x, quat.y, quat.z, quat.w)

            # 构建变换矩阵
            matrix_4x4 = self.transform_to_matrix(trans)

            # 构建完整数据
            transform_data = {
                "source_frame": trans.child_frame_id,  # shears
                "target_frame": trans.header.frame_id,  # base_link
                "ros_timestamp": {
                    "sec": trans.header.stamp.sec,
                    "nanosec": trans.header.stamp.nanosec
                },
                "system_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "translation": {
                    "x": trans.transform.translation.x,
                    "y": trans.transform.translation.y,
                    "z": trans.transform.translation.z
                },
                "rotation_quaternion": {
                    "x": quat.x,
                    "y": quat.y,
                    "z": quat.z,
                    "w": quat.w
                },
                "rotation_rpy": {
                    "roll_radian": rpy_data["roll_radian"],
                    "pitch_radian": rpy_data["pitch_radian"],
                    "yaw_radian": rpy_data["yaw_radian"],
                    "roll_degree": rpy_data["roll_degree"],
                    "pitch_degree": rpy_data["pitch_degree"],
                    "yaw_degree": rpy_data["yaw_degree"]
                },
                "transformation_matrix_4x4": matrix_4x4
            }

            # 创建保存目录
            self.save_directory.mkdir(parents=True, exist_ok=True)

            # 生成文件名：tf_20250827_164512.json
            timestamp_str = datetime.now().strftime("tf_%Y%m%d_%H%M%S.json")
            output_path = self.save_directory / timestamp_str

            # 保存为 JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(transform_data, f, indent=4, ensure_ascii=False)

            self.get_logger().info(f"✅ 完整 TF 数据已保存到: {output_path}")

        except Exception as e:
            self.get_logger().error(f"❌ 获取或保存变换失败: {e}")

        # 完成后退出
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = TFListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()