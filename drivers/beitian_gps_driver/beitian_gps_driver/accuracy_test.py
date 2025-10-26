#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import matplotlib.pyplot as plt
import math
import numpy

# 地球上经度和纬度差值转换为米的因子
LATITUDE_FACTOR = 111194.926644558737
LONGITUDE_FACTOR = 111194.926644558737

class GPSPlotterNode(Node):
    def __init__(self):
        super().__init__('gps_accuracy_test')
        self.subscription = self.create_subscription(
            NavSatFix,
            'gps/fix',
            self.gps_callback,
            10)
        self.subscription
        self.origin_set = False
        self.origin_latitude = 0.0
        self.origin_longitude = 0.0
        self.latitude_diff_m = []
        self.longitude_diff_m = []
        self.distance_m = []
        self.distance_mean = 0.0
        self.distance_std = 0.0
        
        # 设置subplot
        self.fig, self.ax = plt.subplots(3, 1)

    def gps_callback(self, msg):
        if not self.origin_set:
            # 设置原点
            self.origin_latitude = msg.latitude
            self.origin_longitude = msg.longitude
            self.origin_set = True
        
        # 计算相对于原点的经纬度差值
        delta_latitude = msg.latitude - self.origin_latitude
        delta_longitude = msg.longitude - self.origin_longitude
        
        # 将经纬度差值转换为米
        delta_latitude_m = delta_latitude * LATITUDE_FACTOR
        delta_longitude_m = delta_longitude * LONGITUDE_FACTOR * math.cos(math.radians(self.origin_latitude))

        distance = math.sqrt(delta_latitude_m**2 + delta_longitude_m**2)
        
        # 将数据保存到历史列表中
        self.latitude_diff_m.append(delta_latitude_m)
        self.longitude_diff_m.append(delta_longitude_m)
        self.distance_m.append(distance)
        self.distance_mean = numpy.mean(self.distance_m)
        self.distance_std = numpy.std(self.distance_m)
        self.get_logger().info(f'Mean: {self.distance_mean:.2f}, Std: {self.distance_std:.2f}')
        
        # 绘制图形
        self.ax[0].cla()
        self.ax[0].plot(self.latitude_diff_m)
        self.ax[0].set_title('Latitude Difference (m)')
        
        self.ax[1].cla()
        self.ax[1].plot(self.longitude_diff_m)
        self.ax[1].set_title('Longitude Difference (m)')

        self.ax[2].cla()
        self.ax[2].plot(self.distance_m)
        self.ax[2].set_title('Distance from Origin (m)')
        
        plt.tight_layout()
        plt.pause(0.001)
        
def main(args=None):
    rclpy.init(args=args)
    gps_plotter_node = GPSPlotterNode()
    rclpy.spin(gps_plotter_node)
    gps_plotter_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
