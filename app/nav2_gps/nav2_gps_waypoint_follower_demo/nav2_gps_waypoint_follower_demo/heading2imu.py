#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Heading
from sensor_msgs.msg import Imu
from transforms3d.euler import euler2quat
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

qos = QoSProfile(
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST)

class HeadingToImu(Node):
    def __init__(self):
        super().__init__('heading_to_imu')
        # 存储最新收到的 Heading
        self.latest_heading = None

        # 订阅 /gps/orientation
        self.create_subscription(
            Heading,
            '/gps/orientation',
            self.heading_callback,
            qos_profile=qos)

        # 订阅 /imu
        self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            qos_profile=qos)

        # 发布 /imu/heading
        self.pub = self.create_publisher(
            Imu,
            '/imu/heading',
            10)

        self.get_logger().info('HeadingToImu 节点已启动，等待消息...')

    def heading_callback(self, msg: Heading):
        # 每次收到航向角，存储起来
        self.latest_heading = msg
        self.get_logger().debug(f"Received Heading: {msg.heading_deg}°")

    def imu_callback(self, imu_msg: Imu):
        # 收到 IMU 时，如果已有 Heading，就一起合并并发布
        if self.latest_heading is None:
            self.get_logger().warn("尚未收到 Heading，跳过合并发布")
            return

        heading_msg = self.latest_heading
        # 合并并发布
        merged = Imu()
        # 用 Heading 的 header（时间戳和 frame_id）
        merged.header = heading_msg.header

        # 将绝对航向映射为四元数
        yaw_deg = (360.0 - heading_msg.heading_deg) % 360.0
        self.get_logger().info(f"yaw_deg: {yaw_deg}°")
        yaw_rad = yaw_deg * math.pi / 180.0
        q = euler2quat(0.0, 0.0, yaw_rad)
        merged.orientation.x = q[0]
        merged.orientation.y = q[1]
        merged.orientation.z = q[2]
        merged.orientation.w = q[3]
        merged.orientation_covariance = [-1.0] * 9

        # 拷贝原始 IMU 的其他字段
        merged.angular_velocity = imu_msg.angular_velocity
        merged.angular_velocity_covariance = imu_msg.angular_velocity_covariance
        merged.linear_acceleration = imu_msg.linear_acceleration
        merged.linear_acceleration_covariance = imu_msg.linear_acceleration_covariance

        # 发布合并后的 IMU
        self.pub.publish(merged)
        # self.get_logger().info("Published merged IMU on /imu/heading")

def main(args=None):
    rclpy.init(args=args)
    node = HeadingToImu()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
