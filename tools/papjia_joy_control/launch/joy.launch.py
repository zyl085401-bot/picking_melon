"""
@Descripttion: 游戏手柄控制底盘、升降、手抓、云台
@version: 1.0
@Author: 崔译文
@Date: 2024-03-04 15:04:35
@LastEditors: 崔译文
@LastEditTime: 2024-03-04 16:33:33
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    joy_config = os.path.join(get_package_share_directory("papjia_joy_control"), "config", "joy-params.yaml")

    joy_node = Node(
        package="joy",
        name="joy_node",
        executable="joy_node",
        emulate_tty=True,
        output="screen",
        parameters=[joy_config],
    )

    joy_control_config = os.path.join(get_package_share_directory("papjia_joy_control"), "config", "xiaomi.yaml")

    joy_control_node = Node(
        package="papjia_joy_control",
        name="papjia_joy_control_node",
        executable="papjia_joy_control_node",
        emulate_tty=True,
        output="screen",
        parameters=[joy_control_config, {"use_stamp_vel": False}],
    )

    ld.add_action(joy_node)
    ld.add_action(joy_control_node)
    return ld
