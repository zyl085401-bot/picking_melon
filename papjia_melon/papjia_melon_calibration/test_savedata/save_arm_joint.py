#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import json
import os
from datetime import datetime
import time

class ArmJointSnapshot(Node):
    def __init__(self):
        super().__init__('arm_joint_snapshot')
        self.arm_joint_names = [f'arm_joint{i}' for i in range(1, 7)]  # arm_joint1 ~ arm_joint6
        self.latest_joint_state = None
        self.joint_state_received = False

        # 订阅 /joint_states
        from rclpy.qos import qos_profile_sensor_data
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            qos_profile_sensor_data,  # 推荐用于传感器数据
        )
        self.get_logger().info("✅ 正在监听 /joint_states...")

    def joint_state_callback(self, msg):
        """接收到 joint_states 消息时的回调"""
        self.latest_joint_state = msg
        self.joint_state_received = True
        self.get_logger().debug("📩 收到 joint_states 消息")

    def record_once(self, save_dir='.', timeout=5.0):
        """
        记录一次手臂关节值（快照）

        参数:
        - save_dir: 保存目录
        - timeout: 等待数据的最大时间（秒）
        """
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
                self.get_logger().info(f"📁 创建目录: {save_dir}")
            except Exception as e:
                self.get_logger().error(f"❌ 无法创建目录 {save_dir}: {e}")
                return False

        self.joint_state_received = False
        self.latest_joint_state = None

        self.get_logger().info(f"⏳ 等待 /joint_states 数据（最多 {timeout} 秒）...")

        start_time = time.time()
        while rclpy.ok():
            # 非阻塞 spin，处理回调
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.joint_state_received and self.latest_joint_state is not None:
                break

            if (time.time() - start_time) > timeout:
                self.get_logger().error("❌ 超时：未收到 /joint_states 数据")
                return False

        # 提取 arm_joint1 ~ arm_joint6
        msg = self.latest_joint_state
        name_to_pos = dict(zip(msg.name, msg.position))
        arm_joint_positions = {}
        for joint_name in self.arm_joint_names:
            if joint_name in name_to_pos:
                arm_joint_positions[joint_name] = round(name_to_pos[joint_name], 6)
            else:
                arm_joint_positions[joint_name] = None
                self.get_logger().warn(f"⚠️ 未收到关节 {joint_name} 的数据")

        # 生成带时间戳的文件名
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"arm_joints_{timestamp_str}.json"
        file_path = os.path.join(save_dir, filename)

        # 构建日志
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            'joint_angles': arm_joint_positions
        }

        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=4, ensure_ascii=False)
            self.get_logger().info("✅ 成功记录一次关节快照")
            self.get_logger().info(f"💾 已保存到: {file_path}")
            return True
        except Exception as e:
            self.get_logger().error(f"❌ 保存失败: {e}")
            return False


# =================== 主函数 ===================
def main():
    rclpy.init()

    snapshot = ArmJointSnapshot()

    # -----------------------------
    # ✏️ 用户配置
    # -----------------------------
    save_directory = "/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data/arm_joints"  # 修改为你想保存的路径

    success = snapshot.record_once(save_dir=save_directory, timeout=5.0)

    if not success:
        snapshot.get_logger().error("🛑 记录失败，请检查：")
        snapshot.get_logger().error("   1. ROS2 是否已启动？")
        snapshot.get_logger().error("   2. 机械臂控制器是否在运行？")
        snapshot.get_logger().error("   3. 是否运行了：ros2 topic echo /joint_states 看是否有输出？")

    snapshot.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()