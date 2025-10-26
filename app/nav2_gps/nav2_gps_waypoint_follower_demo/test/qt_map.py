#!/usr/bin/env python3
import sys
import yaml
import math
import os
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLabel, QFileDialog, QTextEdit, 
                             QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
# Import the missing CancelResponse
from action_msgs.srv import CancelGoal
from action_msgs.msg import GoalStatus

# Import the action interface (you'll need to replace this with your actual interface)
from tutorial_interfaces.action import GpsPath

class Point:
    """表示GPS航点，包含经纬度、偏航角和类别（A/B）"""
    def __init__(self, latitude, longitude, yaw, category="", index=0):
        self.lat = latitude
        self.lon = longitude
        self.yaw = yaw
        self.category = category
        self.index = index

    def distance(self, other):
        """计算两点间的欧几里得距离"""
        return math.sqrt((self.lat - other.lat) ** 2 + (self.lon - other.lon) ** 2)

    def __repr__(self):
        return f"{self.category}{self.index}({self.lat}, {self.lon}, {self.yaw})"

class MapCanvas(FigureCanvas):
    """地图显示和交互canvas"""
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        # 初始化
        self.points = []
        self.selected_point = None
        self.click_coords = None
        
        # 连接事件
        self.mpl_connect('button_press_event', self.on_click)
        
        # 默认显示空图
        self.axes.set_xlabel('Longitude')
        self.axes.set_ylabel('Latitude')
        self.axes.grid(True)
        self.fig.tight_layout()
        
    def plot_points(self, points):
        """绘制所有点和连线（包含新的连接规则）"""
        from collections import defaultdict

        self.points = points
        self.axes.clear()
        
        # 绘制A点和B点
        a_points = [p for p in points if p.category == 'A']
        b_points = [p for p in points if p.category == 'B']
        
        # 绘制点
        if a_points:
            a_lons = [p.lon for p in a_points]
            a_lats = [p.lat for p in a_points]
            self.axes.scatter(a_lons, a_lats, color='red', label='A Points')
            
            # 标记A点的索引
            for p in a_points:
                self.axes.text(p.lon, p.lat, f"A{p.index}", fontsize=8, ha='right')
            
        if b_points:
            b_lons = [p.lon for p in b_points]
            b_lats = [p.lat for p in b_points]
            self.axes.scatter(b_lons, b_lats, color='green', label='B Points')
            
            # 标记B点的索引
            for p in b_points:
                self.axes.text(p.lon, p.lat, f"B{p.index}", fontsize=8, ha='right')
        
        # 生成邻接表
        adj_list = defaultdict(list)
        
        # A点连接逻辑
        if a_points:
            boundary_points = self.find_boundary_points(a_points)
            
            for p in a_points:
                # 计算与其他A点的距离
                distances = []
                for other in a_points:
                    if other != p:
                        # 修复：distance方法调用错误，应该是p.distance(other)
                        dist = p.distance(other)
                        distances.append((dist, other))
                distances.sort(key=lambda x: x[0])
                
                if p in boundary_points:  # 边界点连接1个
                    if distances:
                        nearest = distances[0][1]
                        adj_list[p].append(nearest)
                        adj_list[nearest].append(p)
                else:  # 非边界点连接2个
                    for d in distances[:2]:
                        neighbor = d[1]
                        adj_list[p].append(neighbor)
                        adj_list[neighbor].append(p)
        
        # B点连接逻辑（连接到最近A点）
        for p in b_points:
            if a_points:
                # 修复：distance方法调用错误，应该是p.distance(a)
                nearest_a = min(a_points, key=lambda a: p.distance(a))
                adj_list[p].append(nearest_a)
                adj_list[nearest_a].append(p)
        
        # 绘制所有连线
        drawn = set()
        for point in adj_list:
            for neighbor in adj_list[point]:
                # 避免重复绘制
                if (point, neighbor) not in drawn and (neighbor, point) not in drawn:
                    # 确定连线颜色
                    line_color = 'red' if point.category == 'A' and neighbor.category == 'A' else 'green'
                    self.axes.plot(
                        [point.lon, neighbor.lon],
                        [point.lat, neighbor.lat],
                        color=line_color, 
                        alpha=0.7,
                        linestyle='--' if line_color == 'green' else '-'
                    )
                    drawn.add((point, neighbor))
        
        # 高亮选中点
        if self.selected_point:
            self.axes.scatter([self.selected_point[0]], [self.selected_point[1]], 
                            color='blue', s=100, marker='x', label='Selected')
        
        # 设置图表属性
        self.axes.set_xlabel('Longitude')
        self.axes.set_ylabel('Latitude')
        self.axes.grid(True)
        if a_points or b_points:
            self.axes.legend()
        self.fig.tight_layout()
        self.draw()
        
    def find_boundary_points(self, a_points):
        """ 找到最左、最右、最上、最下的 A 点 """
        if not a_points:
            return set()
            
        min_lat = min(a_points, key=lambda p: p.lat).lat
        max_lat = max(a_points, key=lambda p: p.lat).lat
        min_lon = min(a_points, key=lambda p: p.lon).lon
        max_lon = max(a_points, key=lambda p: p.lon).lon

        boundary_points = set()
        for p in a_points:
            if p.lat in (min_lat, max_lat) or p.lon in (min_lon, max_lon):
                boundary_points.add(p)
        return boundary_points

    
    def on_click(self, event):
        """处理点击事件"""
        if event.inaxes != self.axes:
            return
        
        # 记录点击坐标
        self.selected_point = (event.xdata, event.ydata)
        
        # 重绘地图以显示选中的点
        self.plot_points(self.points)
        
        # 更新点击坐标
        self.click_coords = (event.xdata, event.ydata)
        
        # 发送坐标已更新的信号
        if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'update_coord_label'):
            self.parent().update_coord_label()
    
    def get_selected_point(self):
        """返回选中的坐标点"""
        if self.click_coords:
            return self.click_coords
        return None
    
    def clear_selection(self):
        """清除选中状态"""
        self.selected_point = None
        self.click_coords = None
        self.plot_points(self.points)

class ROS2Thread(QThread):
    """用于ROS2操作的线程"""
    action_feedback = pyqtSignal(str)
    action_result = pyqtSignal(str)
    action_status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.node = None
        self.action_client = None
        self.goal_handle = None
        self.callback_group = None
        self.is_running = True
        self.callback_group = ReentrantCallbackGroup()
        
    def run(self):
        """线程执行函数"""
        rclpy.init()
        self.callback_group = ReentrantCallbackGroup()
        self.node = Node('qt_map_client')
        
        # 创建Action客户端
        self.action_client = ActionClient(
            self.node, 
            GpsPath, 
            '/navigate_to_goal',
            callback_group=self.callback_group
        )
        
        # 等待Action服务可用
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            self.action_status.emit("Action服务在5秒内未启动，请检查ROS2环境")
        else:
            self.action_status.emit("已连接到Action服务")
        
        # 运行ROS2消息循环
        executor = MultiThreadedExecutor()
        executor.add_node(self.node)
        
        try:
            while rclpy.ok() and self.is_running:
                executor.spin_once(timeout_sec=0.1)
        except Exception as e:
            self.action_status.emit(f"ROS2错误: {str(e)}")
        finally:
            self.node.destroy_node()
            rclpy.shutdown()
    
    def send_goal(self, lat, lon, yaw, command):
        """发送导航目标"""
        if not self.action_client:
            self.action_status.emit("Action客户端未初始化")
            return
        
        goal_msg = GpsPath.Goal()
        goal_msg.goal_latitude = lat
        goal_msg.goal_longitude = lon 
        goal_msg.goal_yaw = yaw
        goal_msg.command = command
        
        self.action_status.emit(f"发送{command}命令: 经度={lon}, 纬度={lat}, 偏航={yaw}")
        
        # 发送目标并设置回调
        self.goal_handle = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self.goal_handle.add_done_callback(self.goal_response_callback)
    
    def feedback_callback(self, feedback_msg):
        """处理Action反馈"""
        feedback = feedback_msg.feedback
        self.action_feedback.emit(f"反馈: {feedback}")
    
    def goal_response_callback(self, future):
        """处理目标响应"""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.action_status.emit("目标被拒绝")
            return
        
        self.action_status.emit("目标被接受")
        
        # 获取结果
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self, future):
        """处理Action结果"""
        result = future.result().result
        self.action_result.emit(f"结果: {result}")
    
    def cancel_goal(self):
        """取消当前目标"""
        if self.goal_handle and self.goal_handle.done() and self.goal_handle.result().accepted:
            self.action_status.emit("正在取消目标...")
            # 修复：使用正确的CancelGoal枚举
            cancel_future = self.goal_handle.result().cancel_goal_async()
            cancel_future.add_done_callback(self.cancel_done_callback)
        else:
            self.action_status.emit("没有可取消的目标")
    
    def cancel_done_callback(self, future):
        """处理取消结果"""
        cancel_response = future.result()
        # 修复：使用正确的枚举值比较
        if cancel_response.return_code == GoalStatus.STATUS_CANCELED:
            self.action_status.emit("目标已成功取消")
        else:
            self.action_status.emit("取消目标失败")
    
    def stop(self):
        """停止线程"""
        self.is_running = False
        self.wait()

class MapInterface(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.last_yaw = 0.0  # 默认偏航角
        self.default_map_path = os.path.expanduser("/home/duz1/nav2_gps/src/nav2_gps_waypoint_follower_demo/map")  # 设置默认地图路径
        
        # 启动ROS2线程
        self.ros_thread = ROS2Thread()
        self.ros_thread.action_feedback.connect(self.update_feedback)
        self.ros_thread.action_result.connect(self.update_result)
        self.ros_thread.action_status.connect(self.update_status)
        self.ros_thread.start()
        
        # 程序启动时加载默认地图
        self.load_default_map()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('ROS2 地图导航界面')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧地图区域
        map_group = QGroupBox("地图显示")
        map_layout = QVBoxLayout()
        self.map_canvas = MapCanvas(self, width=8, height=6)  # 将self传递给MapCanvas
        map_layout.addWidget(self.map_canvas)
        
        # 地图控制区域
        map_control_layout = QHBoxLayout()
        self.load_map_btn = QPushButton("加载地图")
        self.load_map_btn.clicked.connect(self.load_map)
        self.clear_selection_btn = QPushButton("清除选择")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        map_control_layout.addWidget(self.load_map_btn)
        map_control_layout.addWidget(self.clear_selection_btn)
        map_layout.addLayout(map_control_layout)
        
        # 坐标显示区域
        coord_layout = QHBoxLayout()
        self.coord_label = QLabel("选中坐标: 无")
        coord_layout.addWidget(self.coord_label)
        map_layout.addLayout(coord_layout)
        
        map_group.setLayout(map_layout)
        main_layout.addWidget(map_group, 2)
        
        # 右侧控制区域
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Action控制区域
        action_group = QGroupBox("导航控制")
        action_layout = QVBoxLayout()
        
        # 导航按钮
        self.navigate_btn = QPushButton("导航到选中点")
        self.navigate_btn.clicked.connect(self.send_navigation_goal)
        action_layout.addWidget(self.navigate_btn)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消导航")
        self.cancel_btn.clicked.connect(self.cancel_navigation)
        action_layout.addWidget(self.cancel_btn)
        
        # 恢复按钮
        self.resume_btn = QPushButton("恢复导航")
        self.resume_btn.clicked.connect(self.resume_navigation)
        action_layout.addWidget(self.resume_btn)
        
        action_group.setLayout(action_layout)
        control_layout.addWidget(action_group)
        
        # 状态和反馈显示区域
        status_group = QGroupBox("状态和反馈")
        status_layout = QVBoxLayout()
        
        # 状态显示
        status_label = QLabel("状态:")
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_text)
        
        # 反馈显示
        feedback_label = QLabel("反馈:")
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        status_layout.addWidget(feedback_label)
        status_layout.addWidget(self.feedback_text)
        
        # 结果显示
        result_label = QLabel("结果:")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        status_layout.addWidget(result_label)
        status_layout.addWidget(self.result_text)
        
        status_group.setLayout(status_layout)
        control_layout.addWidget(status_group)
        
        main_layout.addWidget(control_widget, 1)
    
    def load_default_map(self):
        """加载默认路径下的地图文件"""
        try:
            if os.path.exists(self.default_map_path):
                yaml_files = [f for f in os.listdir(self.default_map_path) if f.endswith(('.yaml', '.yml'))]
                
                if yaml_files:
                    points = []
                    category = 'A'  # 默认分类
                    
                    for file_name in yaml_files:
                        file_path = os.path.join(self.default_map_path, file_name)
                        
                        # 根据文件名判断分类
                        if 'B_' in file_name:
                            category = 'B'
                        else:
                            category = 'A'
                        
                        with open(file_path, 'r', encoding='utf-8') as file:
                            data = yaml.safe_load(file)
                            
                            if 'waypoints' in data:
                                for i, p in enumerate(data['waypoints']):
                                    point = Point(
                                        p['latitude'], 
                                        p['longitude'], 
                                        p['yaw'], 
                                        category, 
                                        i
                                    )
                                    points.append(point)
                    
                    # 绘制地图
                    if points:
                        self.map_canvas.plot_points(points)
                        self.update_status(f"成功加载默认路径下的 {len(points)} 个点")
                    else:
                        self.update_status(f"未在默认路径 {self.default_map_path} 下找到有效的航点数据")
                else:
                    self.update_status(f"未在默认路径 {self.default_map_path} 下找到YAML文件")
            else:
                self.update_status(f"默认路径 {self.default_map_path} 不存在")
        except Exception as e:
            self.update_status(f"加载默认地图失败: {str(e)}")
    
    def load_map(self):
        """加载地图文件"""
        try:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setNameFilter("YAML Files (*.yaml *.yml)")
            
            if file_dialog.exec_():
                filenames = file_dialog.selectedFiles()
                
                if len(filenames) > 0:
                    points = []
                    category = 'A'  # 默认分类
                    
                    for index, file_path in enumerate(filenames):
                        # 根据文件名判断分类
                        if 'B_' in file_path:
                            category = 'B'
                        else:
                            category = 'A'
                        
                        with open(file_path, 'r', encoding='utf-8') as file:
                            data = yaml.safe_load(file)
                            
                            if 'waypoints' in data:
                                for i, p in enumerate(data['waypoints']):
                                    point = Point(
                                        p['latitude'], 
                                        p['longitude'], 
                                        p['yaw'], 
                                        category, 
                                        i
                                    )
                                    points.append(point)
                    
                    # 绘制地图
                    self.map_canvas.plot_points(points)
                    self.update_status(f"成功加载 {len(points)} 个点")
        except Exception as e:
            self.update_status(f"加载地图失败: {str(e)}")
    
    def clear_selection(self):
        """清除选中的坐标点"""
        self.map_canvas.clear_selection()
        self.coord_label.setText("选中坐标: 无")
    
    def update_coord_label(self):
        """更新坐标标签"""
        selected_point = self.map_canvas.get_selected_point()
        if selected_point:
            lon, lat = selected_point
            self.coord_label.setText(f"选中坐标: 经度={lon:.8f}, 纬度={lat:.8f}")
        else:
            self.coord_label.setText("选中坐标: 无")
    
    def send_navigation_goal(self):
        """发送导航目标"""
        selected_point = self.map_canvas.get_selected_point()
        if selected_point:
            lon, lat = selected_point
            self.ros_thread.send_goal(lat, lon, self.last_yaw, 'start')
            self.update_coord_label()
        else:
            self.update_status("未选中坐标点")
    
    def cancel_navigation(self):
        """取消导航"""
        self.ros_thread.send_goal(0.0, 0.0, 0.0, 'cancel')
    
    def resume_navigation(self):
        """恢复导航"""
        self.ros_thread.send_goal(0.0, 0.0, 0.0, 'resume')
    
    def update_feedback(self, text):
        """更新反馈信息"""
        self.feedback_text.append(text)
        self.feedback_text.verticalScrollBar().setValue(
            self.feedback_text.verticalScrollBar().maximum()
        )
    
    def update_result(self, text):
        """更新结果信息"""
        self.result_text.append(text)
        self.result_text.verticalScrollBar().setValue(
            self.result_text.verticalScrollBar().maximum()
        )
    
    def update_status(self, text):
        """更新状态信息"""
        self.status_text.append(text)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.ros_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapInterface()
    window.show()
    sys.exit(app.exec_())