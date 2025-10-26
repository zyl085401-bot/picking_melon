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
    pose_base_cfg_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "config", "papjia_pose_base_config.yaml"
    )
    
    camera_base_pose_node = Node(
        package="papjia_pose",
        executable="papjia_pose_node",
        name="papjia_pose_node",
        namespace="camera_base",
        emulate_tty=True,
        output="screen",
        parameters=[
            {
                "topic_image_rgb": "/camera/camera_base/color/image_raw",
                "topic_image_depth": "/camera/camera_base/aligned_depth_to_color/image_raw",
                "flag_sync_image": False,
                "flag_pub_cloud_transformed": False,
                "flag_use_pca_pose": False,
                "service_object_detect": "/papjia/vision/global/object/detect",
                "service_image_seg": "/papjia/vision/global/segment",
                "path_vision_cfg": pose_base_cfg_file,
            },
        ],
        arguments=["--ros-args", "--log-level", "INFO"],
    )

    vision_config = os.path.join(
        get_package_share_directory("papjia_melon_config"), "config", "vision_base.yaml"
    )
    
    # 全局检测模型，检测bbox2
    vision_gloabl = Node(
        package="papjia_detector",
        executable="papjia_mask_node",
        name="vision_gloabl",
        output="screen",
        parameters=[vision_config],
    )
    
    launch_description = LaunchDescription([
        camera_base_pose_node,
        vision_gloabl
    ])
    return launch_description
