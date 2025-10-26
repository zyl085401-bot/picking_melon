#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
import math
from typing import Optional

class CameraFrustumVisualizer(Node):
    def __init__(
        self,
        camera_tf: str,
        marker_topic: str,
        # 可以通过内参或视野角度两种方式初始化
        h_fov: Optional[float] = None,
        v_fov: Optional[float] = None,
        # 内参参数
        focal_length: Optional[float] = None,    # 焦距(米), 物理焦距
        sensor_width: Optional[float] = None,     # 传感器宽度(米)
        sensor_height: Optional[float] = None,    # 传感器高度(米)
        # 内参矩阵(K矩阵)参数
        fx: Optional[float] = None,       # x轴焦距(像素)
        fy: Optional[float] = None,       # y轴焦距(像素)
        width: Optional[int] = None,       # 图像宽度(像素)
        height: Optional[int] = None,      # 图像高度(像素)
        # 其他参数
        distance: float = 3.0,            # 可视距离
        color: tuple = (0.0, 1.0, 0.0, 0.8),  # RGBA颜色 (0-1.0)
        fill_sides: bool = True,           # 是否填充锥体侧面
        fill_color: tuple = (0.2, 0.8, 0.2, 0.4)  # 填充颜色 (0-1.0)
        ):
        """
        相机视野可视化器 - 支持通过内参计算视野和侧面填充
        
        参数选项:
        1. 直接提供视野角度(h_fov, v_fov)
        2. 提供物理内参(focal_length, sensor_width, sensor_height)
        3. 提供像素内参(fx, fy, width, height)
        
        Args:
            camera_tf: 相机TF帧名称 (如: 'camera_optical_frame')
            marker_topic: Marker发布的topic名称
            h_fov: 水平视野角(弧度)
            v_fov: 垂直视野角(弧度)
            focal_length: 相机焦距(米), 物理焦距
            sensor_width: 传感器宽度(米)
            sensor_height: 传感器高度(米)
            fx: x轴焦距(像素)
            fy: y轴焦距(像素)
            width: 图像宽度(像素)
            height: 图像高度(像素)
            distance: 视野锥体长度(米)
            color: RGBA颜色元组, 取值范围0-1.0 (线框颜色)
            fill_sides: 是否填充锥体侧面
            fill_color: RGBA填充颜色元组, 取值范围0-1.0
        """
        super().__init__('camera_frustum_visualizer')
        
        # 参数存储
        self.camera_tf = camera_tf
        self.distance = distance
        self.color = color
        self.fill_sides = fill_sides
        self.fill_color = fill_color
        
        # 计算视野角度
        if h_fov is not None and v_fov is not None:
            # 方式1: 直接提供视野角度
            self.h_fov = h_fov
            self.v_fov = v_fov
            self.get_logger().info(f"使用直接提供的视野角度: h_fov={math.degrees(h_fov):.2f}°, v_fov={math.degrees(v_fov):.2f}°")
            
        elif focal_length is not None and sensor_width is not None and sensor_height is not None:
            # 方式2: 通过物理内参计算
            self.h_fov = 2 * math.atan(sensor_width / (2 * focal_length))
            self.v_fov = 2 * math.atan(sensor_height / (2 * focal_length))
            self.get_logger().info(
                f"通过物理内参计算的视野: h_fov={math.degrees(self.h_fov):.2f}°, v_fov={math.degrees(self.v_fov):.2f}° "
                f"(焦距={focal_length:.6f}m, 传感器尺寸={sensor_width:.4f}x{sensor_height:.4f}m)"
            )
            
        elif fx is not None and fy is not None and width is not None and height is not None:
            # 方式3: 通过像素内参计算
            # 计算传感器尺寸(假设像素为正方形)
            # 从像素焦距转换到物理焦距需要传感器尺寸，但可直接计算视野角度
            self.h_fov = 2 * math.atan(width / (2 * fx))
            self.v_fov = 2 * math.atan(height / (2 * fy))
            self.get_logger().info(
                f"通过像素内参计算的视野: h_fov={math.degrees(self.h_fov):.2f}°, v_fov={math.degrees(self.v_fov):.2f}° "
                f"(fx={fx:.2f}px, fy={fy:.2f}px, 图像分辨率={width}x{height}px)"
            )
            
        else:
            raise ValueError("必须提供有效的视野参数组合: 1)h_fov+v_fov, 2)focal_length+sensor_width+sensor_height, 3)fx+fy+width+height")
        
        # 创建Marker发布器
        self.marker_pub = self.create_publisher(Marker, marker_topic, 10)
        
        # 创建定时器定期更新视野
        self.timer = self.create_timer(0.1, self.publish_frustum)  # 10Hz更新
        
        self.get_logger().info(f"相机视野可视化器已初始化. TF: {camera_tf}, Topic: {marker_topic}")
        if self.fill_sides:
            self.get_logger().info(f"开启锥体侧面填充")
    
    def calculate_frustum_points(self) -> list:
        """计算视野锥体的顶点坐标"""
        half_h = math.tan(self.h_fov / 2) * self.distance
        half_v = math.tan(self.v_fov / 2) * self.distance
        
        # 在相机坐标系下的点（Z轴向前，X向右，Y向下）
        return [
            # 相机中心 (0, 0, 0)
            Point(x=0.0, y=0.0, z=0.0),
            
            # 成像平面右上角 (X+, Y-, Z+)
            Point(x=half_h, y=-half_v, z=self.distance),
            
            # 成像平面右下角 (X+, Y+, Z+)
            Point(x=half_h, y=half_v, z=self.distance),
            
            # 成像平面左下角 (X-, Y+, Z+)
            Point(x=-half_h, y=half_v, z=self.distance),
            
            # 成像平面左上角 (X-, Y-, Z+)
            Point(x=-half_h, y=-half_v, z=self.distance)
        ]
    
    def publish_frustum(self):
        """创建并发布Marker消息"""
        # 计算视野点
        points = self.calculate_frustum_points()
        
        # 1. 首先发布线框Marker
        self.publish_frame_marker(points)
        
        # 2. 如果需要，发布侧面填充Marker
        if self.fill_sides:
            self.publish_side_fill_marker(points)
    
    def publish_frame_marker(self, points):
        """发布线框Marker"""
        marker = Marker()
        
        # 设置基础属性
        marker.header.frame_id = self.camera_tf
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "camera_frustum"
        marker.id = 0
        marker.type = Marker.LINE_LIST
        marker.action = Marker.ADD
        
        # 设置尺寸和颜色
        marker.scale.x = 0.01  # 线宽
        marker.color.r = self.color[0]
        marker.color.g = self.color[1]
        marker.color.b = self.color[2]
        marker.color.a = self.color[3]
        
        # 设置位姿
        marker.pose.orientation.w = 1.0
        
        # 添加线段：相机中心 -> 四个角
        marker.points.append(points[0])  # 中心
        marker.points.append(points[1])  # 右上
        
        marker.points.append(points[0])  # 中心
        marker.points.append(points[2])  # 右下
        
        marker.points.append(points[0])  # 中心
        marker.points.append(points[3])  # 左下
        
        marker.points.append(points[0])  # 中心
        marker.points.append(points[4])  # 左上
        
        # 添加线段：成像平面矩形
        marker.points.append(points[1])  # 右上
        marker.points.append(points[2])  # 右下
        
        marker.points.append(points[2])  # 右下
        marker.points.append(points[3])  # 左下
        
        marker.points.append(points[3])  # 左下
        marker.points.append(points[4])  # 左上
        
        marker.points.append(points[4])  # 左上
        marker.points.append(points[1])  # 右上
        
        # 发布Marker
        self.marker_pub.publish(marker)
    
    def publish_side_fill_marker(self, points):
        """发布锥体侧面填充Marker"""
        marker = Marker()
        
        # 设置基础属性
        marker.header.frame_id = self.camera_tf
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "camera_frustum"
        marker.id = 1
        marker.type = Marker.TRIANGLE_LIST
        marker.action = Marker.ADD
        
        # 设置尺寸和颜色
        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0
        marker.color.r = self.fill_color[0]
        marker.color.g = self.fill_color[1]
        marker.color.b = self.fill_color[2]
        marker.color.a = self.fill_color[3]
        
        # 设置位姿
        marker.pose.orientation.w = 1.0
        
        # 填充四个侧面，每个侧面用两个三角形填充
        # 注：三角形顺序保证从外部可见（避免背面消隐）
        
        # 1. 右侧面 (从相机角度看右侧面)
        # 三角形1：相机中心(0) -> 右上角(1) -> 右下角(2)
        marker.points.append(points[0])
        marker.points.append(points[1])
        marker.points.append(points[2])
        
        # 2. 下侧面
        # 三角形2：相机中心(0) -> 右下角(2) -> 左下角(3)
        marker.points.append(points[0])
        marker.points.append(points[2])
        marker.points.append(points[3])
        
        # 3. 左侧面
        # 三角形3：相机中心(0) -> 左下角(3) -> 左上角(4)
        marker.points.append(points[0])
        marker.points.append(points[3])
        marker.points.append(points[4])
        
        # 4. 上侧面
        # 三角形4：相机中心(0) -> 左上角(4) -> 右上角(1)
        marker.points.append(points[0])
        marker.points.append(points[4])
        marker.points.append(points[1])
        
        # 发布填充Marker
        self.marker_pub.publish(marker)

# 示例用法
def main(args=None):
    rclpy.init(args=args)
    
    try:
        # 示例3: 使用像素内参并开启侧面填充
        visualizer = CameraFrustumVisualizer(
            camera_tf="camera_hand_color_optical_frame",
            marker_topic="/camera_hand_color_frustum",
            fx=911.3623046875,
            fy=911.5818481445312,
            width=1280,
            height=720,
            distance=3.0,
            color=(1.0, 0.0, 0.0, 1.0),  # 红色线框
            fill_sides=True,              # 开启侧面填充
            fill_color=(1.0, 0.0, 0.0, 0.3)  # 红色半透明填充
        )
        
        rclpy.spin(visualizer)
        
    except ValueError as e:
        print(f"参数错误: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        if 'visualizer' in locals():
            visualizer.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()