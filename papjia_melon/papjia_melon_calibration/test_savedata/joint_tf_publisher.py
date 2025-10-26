#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from geometry_msgs.msg import TransformStamped
import tf2_ros

class JointTFPublisher(Node):
    def __init__(self):
        super().__init__('joint_tf_publisher')

        # === 1. 发布 /joint_states ===
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        # === 2. 发布 TF ===
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # === 3. 定义你的数据 ===
        # 关节数据
        self.joint_names = [
            "arm_joint1", "arm_joint2", "arm_joint4",
            "arm_joint5", "arm_joint3", "arm_joint6"
        ]
        self.positions = [
            1.1339056491851807,
            0.041907865554094315,
            -2.454071521759033,
            -1.0973964929580688,
            2.2912445068359375,
            -3.06060791015625
        ]
        self.velocities = [
            0.0011984225129708648,
            -0.0003235740587115288,
            0.00037151097785681486,
            0.0005392901366576552,
            -0.0006351639167405665,
            0.003032008884474635
        ]
        self.efforts = [
            0.11058473587036133,
            -0.016392547637224197,
            0.03225596994161606,
            0.0582943893969059,
            -0.012819086201488972,
            0.24756740033626556
        ]

        # TF 数据
        self.tf_data = {
            'shears': {
                'parent': 'base_link',
                'child': 'shears',
                'translation': [1.1269209001875942, -0.01667994353818464, 1.4351873236146955],
                'rotation': [0.013864404793007655, -0.05348986040324885, 0.02045594578533744, 0.998262574373999]
            },
            'camera_hand_link': {
                'parent': 'base_link',
                'child': 'camera_hand_link',
                'translation': [1.0566122847318475, 0.020736346429414243, 1.2979572303492701],
                'rotation': [0.020363254520771347, -0.0412057119604429, 0.011956790881517246, 0.9988715945100105]
            }
        }

        # 每 100ms 发布一次（10Hz）
        self.timer = self.create_timer(0.1, self.publish_data)

        self.get_logger().info("Joint and TF publisher is running.")

    def publish_data(self):
        # 发布 JointState
        joint_msg = JointState()
        joint_msg.header = Header()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = self.joint_names
        joint_msg.position = self.positions
        joint_msg.velocity = self.velocities
        joint_msg.effort = self.efforts
        self.joint_pub.publish(joint_msg)

        # 发布所有 TF
        for name, data in self.tf_data.items():
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = data['parent']
            t.child_frame_id = data['child']
            t.transform.translation.x = data['translation'][0]
            t.transform.translation.y = data['translation'][1]
            t.transform.translation.z = data['translation'][2]
            t.transform.rotation.x = data['rotation'][0]
            t.transform.rotation.y = data['rotation'][1]
            t.transform.rotation.z = data['rotation'][2]
            t.transform.rotation.w = data['rotation'][3]
            self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = JointTFPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()