"""
@Descripttion: 直线行走控制和沿线行走控制
@version: 1.0
@Author: 崔译文
@Date: 2024-03-10 14:27:06
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:45:00
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    config_dir = os.path.join(get_package_share_directory("papjia_melon_config"), "config")

    # 移动控制节点参数配置
    move_cfg_file = os.path.join(config_dir, "move.yaml")
    # 移动控制节点配置
    move_node = Node(
        package="papjia_move",
        name="move_service_node",
        executable="move_service",
        output="screen",
        parameters=[move_cfg_file],
    )

    # 沿线行走节点参数配置
    tracing_cfg_file = os.path.join(config_dir, "tracing_gps.yaml")
    # 沿线行走节点配置
    tracing_node = Node(
        package="papjia_line_tracing",
        name="papjia_line_tracing_node",
        executable="papjia_line_tracing_gps_node",
        output="screen",
        parameters=[tracing_cfg_file],
        arguments=["--ros-args", "--log-level", "INFO"],
    )

    # 添加节点到启动描述
    ld.add_action(move_node)
    ld.add_action(tracing_node)

    return ld
