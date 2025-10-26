#!/usr/bin/env python3

import threading
import time
import math
import yaml
import heapq
import rclpy
from pyproj import Proj
from collections import defaultdict
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from nav2_simple_commander.robot_navigator import BasicNavigator

from tutorial_interfaces.action import GpsPath  

from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler

from rclpy.action import ActionServer, CancelResponse, GoalResponse

# 定义路径点类
class Point:
    def __init__(self, latitude, longitude, yaw, category, index):
        self.lat = latitude
        self.lon = longitude
        self.yaw = yaw
        self.category = category
        self.index = index
        self.neighbors = []
    
    def distance(self, other):
        return math.hypot(self.lat - other.lat, self.lon - other.lon)
    
    def __repr__(self):
        return f"{self.category}{self.index}({self.lat}, {self.lon})"
    
    def __lt__(self, other):
        return (self.lat, self.lon) < (other.lat, other.lon)

# 图结构，用于路径规划
class Graph:
    def __init__(self, a_yaml_path, b_yaml_path):
        self.nodes = []
        self.adj_list = defaultdict(list)
        self._load_points(a_yaml_path, 'A')
        self._load_points(b_yaml_path, 'B')
        self._connect_points()
    
    def _load_points(self, file_path, category):
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            for i, wp in enumerate(data['waypoints']):
                self.nodes.append(Point(wp['latitude'], wp['longitude'], 
                                      wp['yaw'], category, i))
    
    def _connect_points(self):
        a_points = [p for p in self.nodes if p.category == 'A']
        b_points = [p for p in self.nodes if p.category == 'B']

        # 连接A类点：每个点连接最近的两个点
        for p in a_points:
            distances = [(other, p.distance(other)) for other in a_points if other != p]
            sorted_neighbors = sorted(distances, key=lambda x: x[1])[:2]
            for neighbor, _ in sorted_neighbors:
                self.adj_list[p].append(neighbor)
                self.adj_list[neighbor].append(p)

        # 将B类点连接到最近的A类点
        for p in b_points:
            nearest_a = min(a_points, key=lambda a: p.distance(a))
            self.adj_list[p].append(nearest_a)
            self.adj_list[nearest_a].append(p)
    
    def find_nearest_A(self, lat, lon):
        a_points = [p for p in self.nodes if p.category == 'A']
        return min(a_points, key=lambda p: math.hypot(p.lat - lat, p.lon - lon))
    
    def dijkstra(self, start, goal):
        heap = [(0.0, start, [])]
        visited = set()
        
        while heap:
            cost, current, path = heapq.heappop(heap)
            if current in visited:
                continue
            if current == goal:
                return path + [current]
            visited.add(current)
            for neighbor in self.adj_list[current]:
                if neighbor not in visited:
                    heapq.heappush(heap, (cost + current.distance(neighbor), 
                                        neighbor, path + [current]))
        return None

# Action Server 节点
class NavigationAction(Node):
    def __init__(self):
        super().__init__('navigation_action')
        self.navigator = BasicNavigator()
        self.graph = Graph(
            "/workspace/src/app/nav2_gps/nav2_gps_waypoint_follower_demo/test/A_gps_waypoints.yaml",
            "/workspace/src/app/nav2_gps/nav2_gps_waypoint_follower_demo/test/B_gps_waypoints.yaml"
        )
        # 初始化UTM投影（根据实际区域设置zone参数）
        self.utm_proj = Proj(proj='utm', zone=10, ellps='WGS84', preserve_units=False)

        self.current_pos = None
        self.pos_lock = threading.Lock()

        # 订阅GPS话题
        self.gps_sub = self.create_subscription(
            NavSatFix,
            '/gps/filtered',
            self.gps_callback,
            10
        )
        
        # 创建 action server
        self._action_server = ActionServer(
            self,
            GpsPath,
            'navigate_to_goal',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )
        self.get_logger().info("Navigation Action Server 已启动")

    def gps_callback(self, msg):
        with self.pos_lock:
            self.current_pos = (msg.latitude, msg.longitude)

    def goal_callback(self, goal_request):
        self.get_logger().info(f"收到目标请求，command: {goal_request.command}")
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("收到取消请求，正在取消导航任务")
        self.navigator.cancelTask()
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        cmd = (goal_handle.request.command or "").strip().lower()
        goal_lat = goal_handle.request.goal_latitude
        goal_lon = goal_handle.request.goal_longitude
        goal_yaw = goal_handle.request.goal_yaw

        # 处理 start
        if cmd == "start":
            self.get_logger().info("开始新的导航任务")
            with self.pos_lock:
                if not self.current_pos:
                    goal_handle.abort()
                    res = GpsPath.Result()
                    res.success = False
                    res.message = "尚未获取到当前位置"
                    return res
                cur_lat, cur_lon = self.current_pos
            start_pt = self.graph.find_nearest_A(cur_lat, cur_lon)
            goal_pt = Point(goal_lat, goal_lon, goal_yaw, 'B', -1)
            # 临时连边进行规划
            nearest_a = self.graph.find_nearest_A(goal_lat, goal_lon)
            self.graph.adj_list[goal_pt].append(nearest_a)
            self.graph.adj_list[nearest_a].append(goal_pt)
            path = self.graph.dijkstra(start_pt, goal_pt)
            # 清理
            self.graph.adj_list[goal_pt].remove(nearest_a)
            self.graph.adj_list[nearest_a].remove(goal_pt)
            if not path:
                goal_handle.abort()
                res = GpsPath.Result()
                res.success = False
                res.message = "路径规划失败"
                return res
            self.current_path = path
            self.get_logger().info(f"规划到 {len(path)} 个路径点")
        elif cmd == "cancel":
            self.get_logger().info("收到取消指令，取消导航任务")
            self.navigator.cancelTask()
            res = GpsPath.Result()
            res.success = False
            res.message = "任务已取消"
            goal_handle.succeed()
            return res
        else:
            # resume 或未知命令
            if not hasattr(self, 'current_path'):
                goal_handle.abort()
                res = GpsPath.Result()
                res.success = False
                res.message = "无可恢复任务"
                return res

        # 准备 PoseStamped 列表用于 followWaypoints
        with self.pos_lock:
            origin_lat, origin_lon = self.current_pos
        origin_x, origin_y = self.utm_proj(origin_lon, origin_lat)

        pose_list = []
        now = self.get_clock().now().to_msg()
        for pt in self.current_path:
            utm_x, utm_y = self.utm_proj(pt.lon, pt.lat)
            dx = utm_x - origin_x
            dy = utm_y - origin_y
            ps = PoseStamped()
            ps.header.frame_id = 'map'
            ps.header.stamp = now
            ps.pose.position.x = dx
            ps.pose.position.y = dy
            ps.pose.position.z = 0.0
            # 朝向假设 pt.yaw 已是弧度，参考 map x 轴
            qx, qy, qz, qw = quaternion_from_euler(0, 0, pt.yaw)
            ps.pose.orientation.x = qx
            ps.pose.orientation.y = qy
            ps.pose.orientation.z = qz
            ps.pose.orientation.w = qw
            pose_list.append(ps)

        # 切换到 Nav2 active
        # self.navigator.waitUntilNav2Active()
        accepted = self.navigator.followWaypoints(pose_list)
        if not accepted:
            goal_handle.abort()
            res = GpsPath.Result()
            res.success = False
            res.message = "Nav2 拒绝了路点请求"
            return res

        total = len(pose_list)
        # 轮询任务状态并发布反馈
        while not self.navigator.isTaskComplete():
            fb = self.navigator.getFeedback()
            if fb:
                idx = fb.current_waypoint
                feedback = GpsPath.Feedback()
                feedback.current_status = f"正在到达 {idx}/{total}"
                goal_handle.publish_feedback(feedback)
            time.sleep(0.1)

        # 全部完成
        reached = ", ".join(str(p) for p in self.current_path)
        res = GpsPath.Result()
        res.success = True
        res.message = "导航任务完成"
        res.reached_points = reached
        res.unreached_points = ""
        goal_handle.succeed()
        return res


def main(args=None):
    rclpy.init(args=args)
    action_server = NavigationAction()
    try:
        rclpy.spin(action_server)
    except KeyboardInterrupt:
        action_server.get_logger().info("Shutting down Navigation Action Server")
        action_server.navigator.lifecycleShutdown()
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
