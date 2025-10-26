#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener, TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from transforms3d.euler import euler2quat
from tutorial_interfaces.msg import Heading

class TfCorrectionNode(Node):
    def __init__(self):
        super().__init__('tf_correction_node')
        # 创建 TF2 Buffer 和 Listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        # 创建 TransformBroadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        # 订阅 GPS 航向角话题
        self.latest_yaw = None
        self.heading_sub = self.create_subscription(
            Heading,
            '/gps/orientation',
            self.heading_callback,
            10
        )
        self.get_logger().info('TfCorrectionNode 已启动，等待 GPS 航向角与 TF 数据')

    def heading_callback(self, msg: Heading):
        # 缓存最新 yaw，并发布修正后的 TF
        self.latest_yaw = msg.heading_deg * 3.141592653589793 / 180.0
        self.stamp = msg.header.stamp
        self.publish_corrected_tf()

    def publish_corrected_tf(self):
        if self.latest_yaw is None:
            return

        try:
            # 查询最新的 map->base_link 变换
            trans = self.tf_buffer.lookup_transform(
                'map', 'base_link', rclpy.time.Time()
            )
        except Exception as e:
            self.get_logger().warn(f'Lookup failed: {e}')
            return

        # 构造新的 TransformStamped
        corrected = TransformStamped()
        corrected.header.stamp = self.stamp
        corrected.header.frame_id = 'map'
        corrected.child_frame_id = 'base_link'
        # 保留原平移
        corrected.transform.translation = trans.transform.translation
        # 替换为 GPS 四元数朝向
        qx, qy, qz, qw = euler2quat(0.0, 0.0, self.latest_yaw)
        corrected.transform.rotation.x = qw
        corrected.transform.rotation.y = qx
        corrected.transform.rotation.z = qy
        corrected.transform.rotation.w = qz
        # 发布新的 TF
        self.tf_broadcaster.sendTransform(corrected)

def main(args=None):
    rclpy.init(args=args)
    node = TfCorrectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
