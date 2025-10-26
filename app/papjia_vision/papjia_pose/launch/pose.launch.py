"""
@Descripttion: 节点执行器 - 启用
@version: 1.0
@Author: 崔译文
@Date: 2024-01-02 14:38:51
@LastEditors: 崔译文
@LastEditTime: 2024-01-19 10:58:25
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 参数配置
    vision_cfg_file = os.path.join(get_package_share_directory("papjia_pose"), "config", "winding_pose.yaml")
    pose_node = Node(
        package="papjia_pose",
        executable="papjia_pose_node",  # 多线程节点
        name="papjia_pose_node",
        emulate_tty=True,
        output="screen",
        parameters=[
            {
                "topic_image_rgb": "/camera1/rgb/image_raw",
                "topic_image_depth": "/camera1/depth/image_raw",
                "flag_sync_image": False,
                "flag_pub_cloud_transformed": False,
                "flag_use_pca_pose": True,
                "service_object_detect": "/papjia_vision/service_object_detect",
                "service_image_seg": "/papjia_vision/service_image_segment",
                "path_vision_cfg": vision_cfg_file,
            },
        ],
        arguments=["--ros-args", "--log-level", "INFO"],
    )

    # 节点配置
    # 参数配置
    model_cfg_file = os.path.join(get_package_share_directory("papjia_pose"), "config", "winding_model.yaml")
    mask_node = Node(
        package="papjia_detector",
        name="papjia_detector_node",
        executable="papjia_mask_node",
        output="screen",
        parameters=[model_cfg_file],
    )

    launch_description = LaunchDescription([pose_node, mask_node])
    return launch_description
