import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point, Quaternion
import math
import tf2_ros
from tf2_geometry_msgs import do_transform_pose


class ImuArrowPublisher(Node):
    def __init__(self):
        super().__init__('imu_arrow_publisher')
        self.use_sim_time = True
        self.target_frame = 'map'

        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, self.use_sim_time)])

        # 创建IMU消息的订阅者
        self.imu_subscriber = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )

        # 创建Marker消息的发布者
        self.marker_publisher = self.create_publisher(Marker, 'visualization_marker', 10)

        # 初始化tf2监听器
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 创建Marker
        self.marker = Marker()
        self.marker.header.frame_id = self.target_frame
        self.marker.type = Marker.ARROW
        self.marker.scale.x = 0.3  # 箭头粗细
        self.marker.scale.y = 0.03  # 箭头宽度
        self.marker.scale.z = 0.03  # 箭头高度
        self.marker.color.a = 0.6  # 不透明
        self.marker.color.r = 1.0  # 红色
        self.marker.color.g = 0.0
        self.marker.color.b = 0.0

    def imu_callback(self, msg):
        # 提取四元数并计算对应的欧拉角
        orientation = msg.orientation
        # 将四元数转换为欧拉角
        yaw = self.quaternion_to_yaw(orientation)
        self.get_logger().info(f'imu yaw: {yaw * 180.0 / math.pi}')

        # 获取base_link到odom的变换
        try:
            transform = self.tf_buffer.lookup_transform(self.target_frame, 'base_link', rclpy.time.Time())
            base_position = transform.transform.translation

            # 更新Marker的位置为base_link的位置
            self.marker.pose.position = Point(x=base_position.x, y=base_position.y, z=base_position.z)

        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            self.get_logger().error(f'TF error: {e}')
        
        # 计算箭头朝向的角度
        self.marker.pose.orientation = orientation

        # 发布Marker
        self.marker.header.stamp = self.get_clock().now().to_msg()  # 更新时间戳
        self.marker_publisher.publish(self.marker)

    def quaternion_to_yaw(self, orientation):
        # 将四元数转换为欧拉角（yaw）
        siny = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
        return math.atan2(siny, cosy)

    def yaw_to_quaternion(self, yaw):
        # 将yaw角转换为四元数
        half_yaw = yaw * 0.5
        q = Quaternion()
        q.w = math.cos(half_yaw)
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(half_yaw)
        return q


def main(args=None):
    rclpy.init(args=args)
    imu_arrow_publisher = ImuArrowPublisher()
    rclpy.spin(imu_arrow_publisher)
    imu_arrow_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
