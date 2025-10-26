#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage  # 注意：导入 TFMessage
import math
from tf2_ros import TransformBroadcaster
from rclpy.qos import QoSProfile, DurabilityPolicy  # 在文件顶部添加


class TFBroadcasterDemo(Node):
    def __init__(self):
        super().__init__('tf_broadcaster_demo')

        # 动态 tf 发布到 /tf
        self.tf_broadcaster = TransformBroadcaster(self)

        # ✅ 为 /tf_static 设置正确的 QoS
        static_qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.TRANSIENT_LOCAL  # 保证 late-joiner 能收到
        )
        self.tf_static_publisher = self.create_publisher(
            TFMessage,
            '/tf_static',
            static_qos
        )

        # 定时发布静态 tf（关键！）
        self.static_timer = self.create_timer(2.0, self.publish_static_tf)  # 每 2 秒发一次

        # 可选：首次发布（可删）
        # self.publish_static_tf()

        # 定时发布动态 tf
        self.timer = self.create_timer(0.1, self.broadcast_dynamic_tf)

        self.get_logger().info("TF 演示节点已启动，正在发布坐标变换...")

    def publish_static_tf(self):
        """发布静态坐标变换（可重复调用）"""
        transforms = []

        # base_link -> camera_base
        t1 = TransformStamped()
        t1.header.stamp = self.get_clock().now().to_msg()
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'camera_base'
        t1.transform.translation.x = 0.1
        t1.transform.translation.y = -0.2
        t1.transform.translation.z = 0.3
        t1.transform.rotation.w = 1.0

        # base_link -> camera_hand
        t2 = TransformStamped()
        t2.header.stamp = self.get_clock().now().to_msg()
        t2.header.frame_id = 'base_link'
        t2.child_frame_id = 'camera_hand'
        t2.transform.translation.x = 0.05
        t2.transform.translation.y = 0.0
        t2.transform.translation.z = -0.1
        t2.transform.rotation.w = 0.924
        t2.transform.rotation.x = 0.383
        t2.transform.rotation.y = 0.0
        t2.transform.rotation.z = 0.0

        transforms.append(t1)
        transforms.append(t2)

        # 手动构造 TFMessage 并发布
        tfm = TFMessage(transforms=transforms)
        self.tf_static_publisher.publish(tfm)

        # 可选：只在第一次打印
        # self.get_logger().info("已发布静态 TF: base_link → camera_base, camera_hand")
    def broadcast_dynamic_tf(self):
        """周期性发布动态坐标变换（使用 TransformBroadcaster）"""
        now = self.get_clock().now()
        transforms = []

        # world -> base_link
        base_t = TransformStamped()
        base_t.header.stamp = now.to_msg()
        base_t.header.frame_id = 'world'
        base_t.child_frame_id = 'base_link'
        base_t.transform.translation.x = 2.0 + math.sin(now.nanoseconds * 1e-9 * 0.5) * 0.5
        base_t.transform.translation.y = 1.0 + math.cos(now.nanoseconds * 1e-9 * 0.3) * 0.3
        base_t.transform.translation.z = 0.0
        angle_z = math.sin(now.nanoseconds * 1e-9 * 0.2) * 0.1
        base_t.transform.rotation.z = math.sin(angle_z * 0.5)
        base_t.transform.rotation.w = math.cos(angle_z * 0.5)

        # camera_base -> charuco_board_base
        charuco_base_t = TransformStamped()
        charuco_base_t.header.stamp = now.to_msg()
        charuco_base_t.header.frame_id = 'camera_base'
        charuco_base_t.child_frame_id = 'charuco_board_base'
        charuco_base_t.transform.translation.x = 0.4 + math.sin(now.nanoseconds * 1e-9) * 0.001
        charuco_base_t.transform.translation.y = 0.0
        charuco_base_t.transform.translation.z = 0.6
        charuco_base_t.transform.rotation.w = 0.707
        charuco_base_t.transform.rotation.x = 0.0
        charuco_base_t.transform.rotation.y = 0.707
        charuco_base_t.transform.rotation.z = 0.0

        # camera_hand -> charuco_board_hand
        charuco_hand_t = TransformStamped()
        charuco_hand_t.header.stamp = now.to_msg()
        charuco_hand_t.header.frame_id = 'camera_hand'
        charuco_hand_t.child_frame_id = 'charuco_board_hand'
        charuco_hand_t.transform.translation.x = 0.35
        charuco_hand_t.transform.translation.y = -0.1
        charuco_hand_t.transform.translation.z = 0.5
        charuco_hand_t.transform.rotation.w = 0.707
        charuco_hand_t.transform.rotation.x = 0.0
        charuco_hand_t.transform.rotation.y = 0.707
        charuco_hand_t.transform.rotation.z = 0.0

        transforms.append(base_t)
        transforms.append(charuco_base_t)
        transforms.append(charuco_hand_t)

        # 使用标准广播器发布到 /tf
        self.tf_broadcaster.sendTransform(transforms)

def main():
    rclpy.init()
    node = TFBroadcasterDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()