"""
@Descripttion: 沿线行走launch文件
@version: 1.0
@Author: 崔译文
@Date: 2024-03-10 14:27:06
@LastEditors: 崔译文
@LastEditTime: 2024-05-21 10:11:20
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    # 参数配置
    cfg_file = os.path.join(get_package_share_directory("papjia_line_tracing"), "config", "tracing_sim.yaml")
    # 节点配置
    node = Node(
        package="papjia_line_tracing",
        name="papjia_line_tracing_node",
        executable="papjia_line_tracing_node",
        output="screen",
        parameters=[cfg_file],
        arguments=["--ros-args", "--log-level", "INFO"],
    )

    ld.add_action(node)
    return ld
