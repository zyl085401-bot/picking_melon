"""
@Descripttion: 组合节点 - 弃用
@version: 1.0
@Author: 崔译文
@Date: 2024-01-02 14:38:51
@LastEditors: 崔译文
@LastEditTime: 2024-01-19 10:57:45
"""
import os
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 参数配置
    camera_cfg_file = os.path.join(
        get_package_share_directory("papjia_pose"), "config", "camera.yaml"
    )
    """Generate launch description with multiple components."""
    container = ComposableNodeContainer(
        name="papjia_pose",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="papjia_pose",
                plugin="ObjPoseService",  # 对应Plugin名称，一般为类名
                name="obj_pose_node",
                parameters=[
                    {
                        "topic_image_rgb": "/hk_camera/rgb",
                        "topic_image_depth": "/camera1/depth/image_raw",
                        "path_camera_info": camera_cfg_file,
                        "flag_sync_image": False,
                        "service_object_detect": "/papjia_vision/service_object_detect",
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
