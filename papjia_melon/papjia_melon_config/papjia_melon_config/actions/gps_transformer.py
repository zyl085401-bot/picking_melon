import rclpy
import yaml
import math
from rclpy.node import Node
from robot_localization.srv import FromLL
from geometry_msgs.msg import PoseStamped
from nav2_gps_waypoint_follower_demo.utils.gps_utils import latLonYaw2Geopose
from papjia_move_msgs.srv import StraightMove


class GPStransformer(Node):
    def __init__(self, wps_file_path):
        super().__init__("tracing_line_test")
        self._init_waypoints(wps_file_path)
        self._init_services()

    def _init_waypoints(self, path):
        """增强路径点加载逻辑"""
        try:
            with open(path, "r") as f:
                self.points = yaml.safe_load(f)
                self.get_logger().info(f"成功加载路径点文件：{path}")
                self.get_logger().debug(f"路径点内容：{self.points}")
        except FileNotFoundError:
            self.get_logger().fatal(f"路径点文件不存在：{path}")
            raise
        except yaml.YAMLError as e:
            self.get_logger().fatal(f"YAML解析失败：{str(e)}")
            raise
        except Exception as e:
            self.get_logger().fatal(f"未知加载错误：{str(e)}")
            raise

    def _init_services(self):
        """服务初始化增强"""
        self.get_logger().info("初始化服务客户端...")

        # FromLL 定位服务
        self.localizer = self.create_client(FromLL, "/fromLL")
        self._wait_for_service(self.localizer, "FromLL", timeout=5.0)

        # 移动服务
        self.tracing_client = self.create_client(StraightMove, "/papjia/move/line_tracing")
        self._wait_for_service(self.tracing_client, "StraightMove", timeout=5.0)

    def _wait_for_service(self, client, name, timeout=5.0):
        """带超时的服务等待"""
        self.get_logger().info(f"等待 {name} 服务...")
        try:
            if not client.wait_for_service(timeout_sec=timeout):
                raise TimeoutError(f"{name} 服务未在 {timeout} 秒内就绪")
            self.get_logger().info(f"{name} 服务已就绪")
        except TimeoutError as e:
            self.get_logger().error(str(e))
            raise
        except Exception as e:
            self.get_logger().error(f"服务等待异常：{str(e)}")
            raise

    def gps2pose(self, latitude, longitude, yaw):
        """增强版坐标转换方法"""
        try:
            # 输入验证
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                raise ValueError(f"非法坐标值：lat={latitude}, lon={longitude}")

            self.get_logger().debug(f"开始GPS坐标转换：lat={latitude}, lon={longitude}, yaw={yaw}")

            # 构造请求
            wp = latLonYaw2Geopose(latitude, longitude, yaw)
            req = FromLL.Request()
            req.ll_point.longitude = wp.position.longitude
            req.ll_point.latitude = wp.position.latitude
            req.ll_point.altitude = wp.position.altitude

            # 服务调用
            future = self.localizer.call_async(req)
            rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

            if future.exception():
                raise RuntimeError(f"服务异常：{future.exception()}")

            # 处理响应
            resp = future.result()
            if not resp:
                raise RuntimeError("收到空响应")

            pose = PoseStamped()
            pose.header.frame_id = "map"
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position = resp.map_point

            self.get_logger().info(f"坐标转换成功：x={resp.map_point.x:.3f}, y={resp.map_point.y:.3f}")
            return pose

        except ValueError as e:
            self.get_logger().error(f"输入验证失败：{str(e)}")
            return None
        except TimeoutError as e:
            self.get_logger().error(f"服务超时：{str(e)}")
            return None
        except RuntimeError as e:
            self.get_logger().error(f"服务错误：{str(e)}")
            return None
        except Exception as e:
            self.get_logger().error(f"未知错误：{str(e)}", exc_info=True)
            return None

    def get_gps_line(self, line_name):
        # 路径点获取
        if not (wps := self.points.get("waypoints", {}).get(line_name, [])):
            raise ValueError(f"未找到路径配置：{line_name}")

        self.get_logger().debug(f"获取到 {len(wps)} 个路径点")

        # 起点处理
        start_wp = wps[0]
        if not (start_pose := self.gps2pose(start_wp["latitude"], start_wp["longitude"], start_wp["yaw"])):
            raise RuntimeError("直线段起点坐标转换失败")

        # 终点处理
        end_wp = wps[-1]
        if not (end_pose := self.gps2pose(end_wp["latitude"], end_wp["longitude"], end_wp["yaw"])):
            raise RuntimeError("直线段终点坐标转换失败")

        line_start = [start_pose.pose.position.x, start_pose.pose.position.y, 0.0]
        line_end = [end_pose.pose.position.x, end_pose.pose.position.y, 0.0]
        return line_start, line_end
