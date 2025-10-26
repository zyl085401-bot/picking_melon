#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
import yaml
import os
from datetime import datetime

class CalibrationDataRecorder(Node):
    def __init__(self):
        super().__init__("calibration_data_recorder")

        # 👇 设置你想要的保存目录（可修改）
        self.save_directory = "/workspaces/src/papjia_melon/papjia_melon_calibration/papjia_melon_calibration/data"  # 你可以改成 "/path/to/your/dir" 或使用相对路径
        os.makedirs(self.save_directory, exist_ok=True)  # 自动创建目录

        self.hand_pose = None
        self.base_pose = None
        self.joint_state = None

        # 订阅
        self.create_subscription(
            PoseStamped,
            "/camera/camera_hand/color/charuco/pose",
            self.hand_cb,
            10
        )
        self.get_logger().info("订阅到 /camera/camera_hand/color/charuco/pose 话题数据")

        self.create_subscription(
            PoseStamped,
            "/camera/camera_base/color/charuco/pose",
            self.base_cb,
            10
        )
        self.get_logger().info("订阅到 /camera/camera_base/color/charuco/pose 话题数据")

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_cb,
            10
        )
        self.get_logger().info("订阅到 /joint_states 话题数据")

        # 每 2 秒尝试保存一次
        self.create_timer(2.0, self.save_once)

        # 生成文件名（带时间戳）
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.save_directory, f"calibration_data_{ts}.yaml")

        self.get_logger().info(f"将保存数据到: {self.filename}")

    def hand_cb(self, msg):
        self.hand_pose = msg

    def base_cb(self, msg):
        self.base_pose = msg

    def joint_cb(self, msg):
        self.joint_state = msg

    def save_once(self):
        """尝试保存一次数据，只要所有数据都收到就保存并退出"""
        if self.hand_pose is not None and self.base_pose is not None and self.joint_state is not None:
            data = {
                "camera_hand_pose": self.pose_to_dict(self.hand_pose),
                "camera_base_pose": self.pose_to_dict(self.base_pose),
                "joint_state": {
                    "name": list(self.joint_state.name),
                    "position": list(self.joint_state.position)
                }
            }
            try:
                with open(self.filename, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                self.get_logger().info(f"✅ 保存成功: {self.filename}")
            except Exception as e:
                self.get_logger().error(f"❌ 保存失败: {e}")

            # 保存后退出
            rclpy.shutdown()

    def pose_to_dict(self, pose_stamped):
        p = pose_stamped.pose.position
        q = pose_stamped.pose.orientation
        return {
            "position": [p.x, p.y, p.z],
            "orientation": [q.x, q.y, q.z, q.w]
        }


def main():
    rclpy.init()
    node = CalibrationDataRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()