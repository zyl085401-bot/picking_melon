"""
@Descripttion: tf发布 - base-camera
@version: 1.0
@Author: 崔译文
@Date: 2024-01-16 10:23:58
@LastEditors: 崔译文
@LastEditTime: 2024-01-19 10:59:35
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="robot_to_camera",
                output="screen",
                arguments=[
                    "0.662762",
                    "-0.0677867",
                    "1.22691",
                    "0.708",
                    "0.706",
                    "-0.018",
                    "0.003",
                    "base_link",
                    "camera_depth_optical_frame",
                ],
            ),
        ]
    )
