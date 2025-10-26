"""
Descripttion: 直线检测的lanuch文件
version: 2.0
Author: 崔译文
Date: 2023-12-25 14:30:44
@LastEditors: 崔译文
@LastEditTime: 2024-01-03 11:47:17
"""
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    """Generate launch description with multiple components."""
    container = ComposableNodeContainer(
        name="my_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="papjia_line_detector",
                plugin="LineDetectorService",
                name="line_seg_node",
                parameters=[
                    {
                        "service_seg_line": "/papjia_detector/line_seg_service",
                        "topic_image_line": "/papjia_detector/line_seg_result",
                        "topic_image": "/hk_camera/rgb",
                        "flag_pub_image_line": True,
                        "flag_use_rect": False,
                        "rect": [100, 100, 200, 210],
                    }
                ],
            ),
            ComposableNode(
                package="hk_camera",
                plugin="HKCameraPlugin",  # 对应Plugin名称，一般为类名
                name="hk_camera_node",
                parameters=[
                    {
                        "topic_image_rgb": "/hk_camera/rgb",
                        "frame_id": "hk_camera",
                        "frame_rate": 10,
                    }
                ],
            ),
        ],
        output="screen",
        emulate_tty=True,
    )

    return launch.LaunchDescription([container])
