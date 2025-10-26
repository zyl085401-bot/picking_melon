import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
import numpy as np
import open3d as o3d
import os
import time
import threading
import queue


class PointCloudSaver(Node):
    def __init__(self):
        super().__init__("pointcloud_saver")
        # 声明参数
        self.declare_parameter("point_cloud_topic", "/camera/depth_registered/points")
        self.declare_parameter("save_command", "s")
        self.declare_parameter("output_dir", "/workspace/rgbd_data/point_cloud")

        # 获取参数
        self.point_cloud_topic = self.get_parameter("point_cloud_topic").get_parameter_value().string_value
        self.save_command = self.get_parameter("save_command").get_parameter_value().string_value
        self.output_dir = self.get_parameter("output_dir").get_parameter_value().string_value

        # 创建保存目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 订阅点云话题
        self.subscription = self.create_subscription(PointCloud2, self.point_cloud_topic, self.callback, 10)
        self.subscription  # 防止未使用变量警告

        # 创建命令队列和线程
        self.command_queue = queue.Queue()
        self.command_thread = threading.Thread(target=self._command_listener)
        self.command_thread.daemon = True
        self.command_thread.start()

        # 存储最新的点云数据
        self.latest_point_cloud = None
        self.point_cloud_lock = threading.Lock()

        self.get_logger().info(f"节点已启动，等待点云数据...")
        self.get_logger().info(f"输入 '{self.save_command}' 命令保存点云")

    def _command_listener(self):
        """监听用户输入命令的线程"""
        while rclpy.ok():
            try:
                command = input().strip()
                if command == self.save_command:
                    self._save_point_cloud()
                else:
                    self.get_logger().info(f"未知命令: {command}")
                    self.get_logger().info(f"请输入 '{self.save_command}' 保存点云")
            except Exception as e:
                self.get_logger().error(f"命令处理错误: {str(e)}")

    def callback(self, msg):
        """点云数据回调函数"""
        try:
            with self.point_cloud_lock:
                self.latest_point_cloud = msg
        except Exception as e:
            self.get_logger().error(f"处理点云数据失败: {str(e)}")

    def _save_point_cloud(self):
        """保存点云数据"""
        try:
            with self.point_cloud_lock:
                if self.latest_point_cloud is None:
                    self.get_logger().warn("没有可用的点云数据")
                    return

                msg = self.latest_point_cloud
                use_color = False
                for field in msg.fields:
                    if field.name == "rgb":
                        use_color = True
                        print("Found RGB field with offset:", field.offset)

                # 将PointCloud2消息转换为NumPy数组
                points = point_cloud2.read_points_numpy(msg)
                print("Points shape:", points.shape)
                print("Points dtype:", points.dtype)

                xyz = points[:, :3]  # 提取XYZ坐标

                # 创建Open3D点云对象
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(xyz)

                # 提取颜色信息
                if use_color:
                    try:
                        # RGB数据在第4个float32位置
                        rgb_float = points[:, 3]

                        # 将float32转换为bytes以提取RGB值
                        rgb_bytes = rgb_float.view(np.uint32)

                        # 提取RGB通道 (RGB按照R<<16, G<<8, B格式打包)
                        r = (rgb_bytes & 0x00FF0000) >> 16
                        g = (rgb_bytes & 0x0000FF00) >> 8
                        b = rgb_bytes & 0x000000FF

                        # 组合RGB通道并归一化到[0,1]范围
                        rgb_array = np.column_stack([r, g, b]).astype(np.float64) / 255.0

                        pcd.colors = o3d.utility.Vector3dVector(rgb_array)
                        print("Successfully extracted colors")
                        print("Color shape:", rgb_array.shape)
                        print("Color range:", np.min(rgb_array), "-", np.max(rgb_array))

                        pcd.colors = o3d.utility.Vector3dVector(rgb_array)

                    except Exception as e:
                        print(f"Failed to extract colors: {e}")
                        print("Points array structure:", points.shape, points.dtype)

                # 生成文件名
                timestamp = int(time.time())
                filename = os.path.join(self.output_dir, f"cloud_{timestamp}.ply")

                # 保存为PLY文件
                o3d.io.write_point_cloud(filename, pcd)
                self.get_logger().info(f"点云已保存至: {filename}")

        except Exception as e:
            self.get_logger().error(f"保存点云失败: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudSaver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
