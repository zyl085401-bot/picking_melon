#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Heading
from std_msgs.msg import Header
from rclpy.clock import Clock, ClockType

class HeadingPublisher(Node):
    def __init__(self):
        super().__init__('heading_publisher')
        # 声明并设置 use_sim_time 参数为 True
        # self.declare_parameter('use_sim_time', True)
        # 使用仿真时间的时钟
        self.clock = Clock(clock_type=ClockType.ROS_TIME)
        # 创建发布器
        self.publisher_ = self.create_publisher(Heading, '/gps/orientation', 10)
        # 设置定时器，每秒发布一次
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.heading_deg = 180.0  # 初始航向角

    def timer_callback(self):
        # 获取当前仿真时间
        current_time = self.clock.now().to_msg()
        # 创建 Heading 消息
        msg = Heading()
        msg.header = Header()
        msg.header.stamp = current_time
        msg.header.frame_id = 'gps_link'
        msg.heading_deg = self.heading_deg
        # 发布消息
        self.publisher_.publish(msg)
        self.get_logger().info(f'发布 Heading: {msg.heading_deg}°')
        # 更新航向角
        # self.heading_deg = (self.heading_deg + 10.0) % 360.0

def main(args=None):
    rclpy.init(args=args)
    node = HeadingPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
