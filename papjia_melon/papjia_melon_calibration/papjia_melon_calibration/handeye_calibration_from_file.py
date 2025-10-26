"""
Descripttion: 手眼标定 - 从文件读取数据
version: 1.0
Author: 崔译文
Date: 2024-01-02 10:50:45
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:15:39
"""

import csv
import numpy as np
from typing import List, Tuple, Set
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster
from .transformations import pose_to_matrix, matrix_to_pose, euler_from_quaternion, quaternion_from_euler
from .handeye_calibration import HandeyeCalibrator
import os
import yaml
import time


class CalibrationFromCSV(Node):
    """手眼标定数据收集器

    从CSV文件读取机器人位姿和标定板位姿数据，执行手眼标定计算。
    """

    def __init__(self):
        """初始化节点和参数"""
        super().__init__("papjia_calibration_data_collector")

        # 创建回调组
        self.callback_group = ReentrantCallbackGroup()

        # 创建静态TF广播器
        self.tf_broadcaster = StaticTransformBroadcaster(self)

        # 存储所有TF消息
        self.tf_messages = []

        # 声明参数
        self._declare_parameters()

        # 获取参数值
        self._load_parameters()

        # 执行标定
        self._run_calibration()

    def _declare_parameters(self) -> None:
        """声明ROS参数

        参数说明:
            save_path: 标定数据CSV文件路径
            cali_type: 标定类型（eye_in_hand 或 eye_to_hand）
            skip_indices: 要跳过的数据组索引（从0开始）
        """
        self.declare_parameters(
            namespace="",
            parameters=[
                ("save_path", "/workspace/data/0610/2025-06-10_15-11-10/pose.csv"),
                ("cali_type", "eye_in_hand"),
                ("skip_indices", []),
                ("optical2camera", [0.0, 0.0, 0.0, -np.pi / 2, 0.0, -np.pi / 2]),
            ],
        )

    def _load_parameters(self) -> None:
        """加载参数值"""
        self.pose_csv_path = self.get_parameter("save_path").get_parameter_value().string_value
        self.cali_type = self.get_parameter("cali_type").get_parameter_value().string_value
        self.skip_indices = self.get_parameter("skip_indices").get_parameter_value().integer_array_value
        optical2camera_array = self.get_parameter("optical2camera").get_parameter_value().double_array_value

        # 分别获取平移和欧拉角
        translation = optical2camera_array[0:3]  # [x, y, z]
        euler_angles = optical2camera_array[3:6]  # [roll, pitch, yaw]

        # 将欧拉角转换为四元数
        quaternion = quaternion_from_euler(euler_angles[0], euler_angles[1], euler_angles[2])

        # 组合平移和四元数
        self.optical2camera = np.concatenate([translation, quaternion])

        if self.skip_indices:
            self.get_logger().info(f"将跳过以下组的数据: {sorted(self.skip_indices)}")

        # 验证标定类型
        if self.cali_type not in ["eye_in_hand", "eye_to_hand"]:
            self.get_logger().error(f"不支持的标定类型: {self.cali_type}")
            raise ValueError(f"标定类型必须是 'eye_in_hand' 或 'eye_to_hand'")

    def _run_calibration(self) -> None:
        """执行标定流程"""
        try:
            # 读取数据
            robot_poses, charuco_poses = self._read_pose_csv(self.pose_csv_path, self.skip_indices)

            if not robot_poses or not charuco_poses:
                self.get_logger().error("没有有效的标定数据")
                return

            self.get_logger().info(f"使用 {len(robot_poses)} 组数据进行标定")

            # 发布所有静态TF
            if self.tf_messages:
                self.tf_broadcaster.sendTransform(self.tf_messages)
                self.get_logger().info(f"已发布 {len(self.tf_messages)} 个静态TF")

            # 执行标定
            calibrator = HandeyeCalibrator()

            methods = ["Tsai-Lenz", "Park", "Horaud", "Andreff", "Daniilidis"]
            for method in methods:
                self.get_logger().info(f"使用 {method} 方法进行标定")

                optical2hand_pose = calibrator.calibration(robot_poses, charuco_poses, self.cali_type, method=method)

                # 将结果转换为相机坐标系
                camera2hand_pose = self._convert_to_camera_frame(optical2hand_pose, self.optical2camera)

                # 打印结果
                self._print_calibration_result(camera2hand_pose)

        except Exception as e:
            self.get_logger().error(f"标定过程出错: {str(e)}")
            raise

    def _convert_to_camera_frame(self, optical2hand: np.ndarray, optical2camera: List[float]) -> np.ndarray:
        """将结果转换为相机坐标系

        Args:
            result_pose: 标定结果位姿数组 [x, y, z, qx, qy, qz, qw]
            optical2camera: 光学坐标系到相机坐标系的变换参数
        """
        optical2camera_matrix = pose_to_matrix(optical2camera)
        optical2hand_matrix = pose_to_matrix(optical2hand)
        camera2optical_matrix = np.linalg.inv(optical2camera_matrix)
        camera2hand_matrix = np.dot(optical2hand_matrix, camera2optical_matrix)
        return matrix_to_pose(camera2hand_matrix)

    def _print_calibration_result(self, result_pose: np.ndarray) -> None:
        """打印标定结果

        Args:
            result_pose: 标定结果位姿数组 [x, y, z, qx, qy, qz, qw]
        """
        self.get_logger().info("标定结果:")
        self.get_logger().info(f"  平移: [{result_pose[0]:.6f}, {result_pose[1]:.6f}, {result_pose[2]:.6f}]")
        self.get_logger().info(
            f"  四元数: [{result_pose[3]:.6f}, {result_pose[4]:.6f}, {result_pose[5]:.6f}, {result_pose[6]:.6f}]"
        )
        self.get_logger().info(f"  欧拉角: {euler_from_quaternion(result_pose[3:7])}")

    def _read_pose_csv(self, file_path: str, skip_groups: Set[int]) -> Tuple[List[List[float]], List[List[float]]]:
        """读取CSV文件中的位姿数据

        Args:
            file_path: CSV文件路径
            skip_groups: 要跳过的数据组索引集合

        Returns:
            Tuple[List[List[float]], List[List[float]]]: 机器人位姿列表和标定板位姿列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 数据格式错误
        """
        robot_poses: List[List[float]] = []
        charuco_poses: List[List[float]] = []

        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                valid_lines = self._validate_csv_lines(reader)

                # 按组处理数据
                for group_idx, i in enumerate(range(0, len(valid_lines), 2)):
                    if i + 1 >= len(valid_lines):
                        self.get_logger().warn("姿态行数为奇数，最后一行被跳过")
                        break

                    if group_idx in skip_groups:
                        self.get_logger().debug(f"跳过组 {group_idx} (行 {i + 1}, {i + 2})")
                        continue

                    robot_pose = valid_lines[i]
                    robot_poses.append(robot_pose)
                    # 发布机器人位姿TF
                    self._publish_robot_tf(robot_pose, group_idx)

                    charuco_poses.append(valid_lines[i + 1])

        except FileNotFoundError:
            self.get_logger().error(f"找不到文件: {file_path}")
            raise
        except Exception as e:
            self.get_logger().error(f"读取文件时出错: {str(e)}")
            raise

        return robot_poses, charuco_poses

    def _validate_csv_lines(self, reader: csv.reader) -> List[List[float]]:
        """验证并转换CSV行数据

        Args:
            reader: CSV读取器

        Returns:
            List[List[float]]: 有效的浮点数行列表

        Raises:
            ValueError: 数据格式错误
        """
        valid_lines: List[List[float]] = []

        for idx, row in enumerate(reader, 1):
            try:
                # 跳过空行和无效行
                if not row or any(cell.strip() in {"-", "---", ""} for cell in row):
                    self.get_logger().debug(f"跳过无效行 {idx}: {row}")
                    continue

                # 转换为浮点数
                float_row = [float(cell.strip()) for cell in row]

                # 验证数据长度
                if len(float_row) != 7:
                    self.get_logger().warn(f"行 {idx} 不是7个元素: {row}")
                    continue

                valid_lines.append(float_row)

            except ValueError as e:
                self.get_logger().warn(f"行 {idx} 包含非数字数据: {row}")
                continue

        if not valid_lines:
            raise ValueError("没有有效的标定数据")

        return valid_lines

    def _publish_robot_tf(self, robot_pose, index):
        """发布机器人位姿TF

        Args:
            robot_pose: 机器人位姿 [x, y, z, qx, qy, qz, qw]
            index: 位姿索引
        """
        # 创建TF消息
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "arm_base_link"
        t.child_frame_id = f"arm_link_6_{index}"

        # 设置平移
        t.transform.translation.x = float(robot_pose[0])
        t.transform.translation.y = float(robot_pose[1])
        t.transform.translation.z = float(robot_pose[2])

        # 直接使用四元数
        t.transform.rotation.x = float(robot_pose[3])
        t.transform.rotation.y = float(robot_pose[4])
        t.transform.rotation.z = float(robot_pose[5])
        t.transform.rotation.w = float(robot_pose[6])

        # 将TF消息添加到列表中
        self.tf_messages.append(t)
        self.get_logger().debug(f"已添加TF: {t.header.frame_id} -> {t.child_frame_id}")


def main(args=None):
    """主函数"""
    try:
        rclpy.init(args=args)
        collector = CalibrationFromCSV()
        rclpy.spin(collector)
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
    finally:
        if "collector" in locals():
            collector.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
