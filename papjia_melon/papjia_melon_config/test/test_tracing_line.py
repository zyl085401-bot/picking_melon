import rclpy
import yaml
import threading
import sys
import os
import time
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from robot_localization.srv import FromLL
from geometry_msgs.msg import PoseStamped
from nav2_gps_waypoint_follower_demo.utils.gps_utils import latLonYaw2Geopose
from tf2_ros import Buffer, TransformListener
from tf2_geometry_msgs import do_transform_pose
from papjia_move_msgs.srv import StraightMove


class TracingLineTest(Node):
    def __init__(self, wps_file_path):
        super().__init__("tracing_line_test")
        self._init_waypoints(wps_file_path)
        self._init_services()
        self._init_tf()

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

    def _init_tf(self):
        """TF系统初始化"""
        self.get_logger().info("初始化TF监听器...")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.get_logger().debug("TF系统初始化完成")

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

    def transform_pose(self, pose, target_frame="base_link", source_frame="map"):
        """增强版坐标变换"""
        try:
            self.get_logger().debug(f"尝试坐标变换：{source_frame}->{target_frame}")

            transform = self.tf_buffer.lookup_transform(
                target_frame=target_frame,
                source_frame=source_frame,
                time=rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=2.0),
            )

            transformed_pose = do_transform_pose(pose, transform)
            self.get_logger().info(f"坐标变换成功：{source_frame}->{target_frame}")
            self.get_logger().debug(f"变换结果：{transformed_pose}")
            return transformed_pose

        except Exception as e:
            self.get_logger().error(f"坐标变换失败：{str(e)}")
            return None

    def tracing_gps_dist(self, line_name, dist, speed):
        """增强版路径跟踪"""
        self.get_logger().info(f"开始执行路径跟踪：{line_name}")
        try:
            # 路径点获取
            if not (wps := self.points.get("waypoints", {}).get(line_name, [])):
                raise ValueError(f"未找到路径配置：{line_name}")

            self.get_logger().debug(f"获取到 {len(wps)} 个路径点")

            # 起点处理
            start_wp = wps[0]
            if not (start_pose := self.gps2pose(start_wp["latitude"], start_wp["longitude"], start_wp["yaw"])):
                raise RuntimeError("直线段起点坐标转换失败")

            self.get_logger().info(f"直线段起点坐标：{start_pose.pose.position}")

            # 终点处理
            end_wp = wps[-1]
            if not (end_pose := self.gps2pose(end_wp["latitude"], end_wp["longitude"], end_wp["yaw"])):
                raise RuntimeError("直线段终点坐标转换失败")

            self.get_logger().info(f"直线段终点坐标：{end_pose.pose.position}")

            # 构建请求
            req = StraightMove.Request(
                distance=dist,
                speed=speed,
                use_integral=True,
                follow_line=True,
                line_frame=start_pose.header.frame_id,
                line_start=[
                    start_pose.pose.position.x,
                    start_pose.pose.position.y,
                    0.0,
                ],
                line_end=[end_pose.pose.position.x, end_pose.pose.position.y, 0.0],
            )

            if speed < 0:
                req.line_start, req.line_end = req.line_end, req.line_start

            # 发送请求
            self.get_logger().info("发送移动请求...")
            future = self.tracing_client.call_async(req)
            self.get_logger().info("---等待移动服务完成...")
            rclpy.spin_until_future_complete(self, future, timeout_sec=120.0)
            self.get_logger().info("---移动服务完成")

            if future.exception():
                raise RuntimeError(f"服务异常：{future.exception()}")

            result = future.result()
            if result is None or not result.success:
                self.get_logger().error("移动服务返回失败状态")
                return None

            self.get_logger().info(f"路径跟踪({dist}|{speed})成功完成")
            return result

        except ValueError as e:
            self.get_logger().error(f"配置错误：{str(e)}")
            return None
        except RuntimeError as e:
            self.get_logger().error(f"执行错误：{str(e)}")
            return None
        except Exception as e:
            self.get_logger().error(f"未知错误：{str(e)}", exc_info=True)
            return None


def main():
    rclpy.init()

    try:
        # 配置加载（保留原有逻辑）
        default_path = os.path.join(
            get_package_share_directory("papjia_melon_config"),
            "config",
            "gps_waypoints_gazebo.yaml",
        )
        config_path = sys.argv[1] if len(sys.argv) > 1 else default_path

        # 节点初始化
        node = TracingLineTest(config_path)

        # 关键修改：使用独立线程运行执行器
        executor = MultiThreadedExecutor()
        executor.add_node(node)
        executor_thread = threading.Thread(
            target=executor.spin,
            daemon=True,  # 设置为守护线程防止卡住退出
            name="ros_executor_move",
        )
        executor_thread.start()
        node.get_logger().info("ROS执行器线程已启动")

        # 任务执行逻辑
        def execute():
            try:
                forward = True
                max_loop = 100
                loop_count = 0
                while loop_count < max_loop and rclpy.ok():
                    node.get_logger().info(f"第{loop_count}次执行")

                    # 同步调用服务
                    result = node.tracing_gps_dist("测试", 6.0, 0.3 if forward else -0.3)
                    node.get_logger().info(f"任务结果：{result}")

                    forward = not forward
                    loop_count += 1
                    time.sleep(3.0)

                node.get_logger().info("任务线程结束")
                executor.shutdown()
            except Exception as e:
                node.get_logger().critical(f"任务线程异常：{str(e)}")
                executor.shutdown()
            finally:
                node.destroy_node()
                rclpy.try_shutdown()

        # 启动任务线程
        task_thread = threading.Thread(target=execute, name="task_thread")
        task_thread.start()
        task_thread.join()  # 等待任务线程结束

    except Exception as e:
        print(f"致命错误：{str(e)}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
