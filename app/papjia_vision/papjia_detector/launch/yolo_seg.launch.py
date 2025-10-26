"""
Descripttion: 图像分割的lanuch文件
version: 2.0
Author: 崔译文
Date: 2023-12-19 15:30:44
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:14:36
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    # 获取包路径
    pkg_share = get_package_share_directory("papjia_detector")

    # 配置文件路径
    config_file = os.path.join(pkg_share, "config", "yolo_seg.yaml")

    # 创建节点
    node = Node(
        package="papjia_detector",
        name="papjia_vision_seg_node",
        executable="papjia_mask_node",
        output="screen",
        parameters=[config_file],
    )

    # 返回 LaunchDescription
    return LaunchDescription([node])
