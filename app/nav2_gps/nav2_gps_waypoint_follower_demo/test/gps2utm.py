#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from pyproj import Transformer
import matplotlib.pyplot as plt
import math

class GpsToLocalCoordinateNode(Node):
    def __init__(self):
        super().__init__('gps_to_local_coordinate_node')

        # 订阅 GPS 数据
        self.subscription = self.create_subscription(
            NavSatFix,
            '/gps/fix',
            self.gps_callback,
            10  # QoS
        )
        self.subscription  # 防止变量被垃圾回收

        # 创建 WGS84 (经纬度) 到 UTM 的转换器
        self.transformer = Transformer.from_crs("epsg:4326", "epsg:32649", always_xy=True)  

        # 存储第一个UTM坐标作为局部坐标系原点
        self.origin_x = None
        self.origin_y = None

        # 存储局部坐标轨迹
        self.local_x_data = []
        self.local_y_data = []

        # 设置Matplotlib图表
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'bo-', markersize=1)  # 轨迹线
        self.ax.set_xlabel('Local X')
        self.ax.set_ylabel('Local Y')
        self.ax.set_title('Real-time Local Coordinate Trajectory')
        self.ax.grid(True)

        # 初始化坐标轴范围
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)

        # 非阻塞显示图表
        plt.ion()
        plt.show()

    def gps_callback(self, msg):
        if msg.latitude == 0.0 and msg.longitude == 0.0:
            self.get_logger().warning("接收到无效的GPS数据")
            return

        # 将当前 GPS 转换为 UTM 坐标
        utm_x, utm_y = self.transformer.transform(msg.longitude, msg.latitude)
        self.get_logger().info(f"收到的UTM坐标: X={utm_x}, Y={utm_y}")

        # 如果还未设置原点，则将当前UTM坐标设为原点
        if self.origin_x is None and self.origin_y is None:
            self.origin_x, self.origin_y = utm_x, utm_y
            self.get_logger().info(f"设置原点: X={self.origin_x}, Y={self.origin_y}")
        else:
            # 计算相对于原点的局部坐标
            local_x = utm_x - self.origin_x
            local_y = utm_y - self.origin_y

            # 存储局部坐标并更新轨迹
            self.local_x_data.append(local_x)
            self.local_y_data.append(local_y)

            # 计算与原点的欧氏距离（单位：米）
            self.get_logger().info(f"局部坐标: X={local_x}, Y={local_y}")
            distance = math.sqrt(local_x**2 + local_y**2)
            self.get_logger().info(f"距离原点: {distance:.2f} 米")


    def update_plot(self):
        """更新Matplotlib图表中的轨迹线。"""
        self.line.set_data(self.local_x_data, self.local_y_data)

        # 动态调整坐标轴范围
        self.ax.relim()
        self.ax.autoscale_view()

        # 刷新图表
        plt.draw()
        plt.pause(0.1)

def main(args=None):
    rclpy.init(args=args)
    node = GpsToLocalCoordinateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()