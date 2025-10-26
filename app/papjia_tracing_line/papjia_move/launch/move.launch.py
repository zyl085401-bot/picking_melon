"""
@Descripttion: 直线行走控制
@version: 1.0
@Author: 崔译文
@Date: 2024-03-10 14:27:06
@LastEditors: 崔译文
@LastEditTime: 2024-03-14 17:26:57
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    # 参数配置
    cfg_file = os.path.join(get_package_share_directory("papjia_move"), "config", "move.yaml")
    # 节点配置
    node = Node(
        package="papjia_move",
        name="move_service_node",
        executable="move_service",
        output="screen",
        parameters=[cfg_file],
    )

    ld.add_action(node)
    return ld
