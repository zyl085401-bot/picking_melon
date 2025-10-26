"""
Descripttion: 发布图像depth&rgb
version: 1.0
Author: 崔译文
Date: 2023-12-19 15:30:44
@LastEditors: 崔译文
@LastEditTime: 2024-05-12 17:03:12
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import LogInfo


def generate_launch_description():
    ld = LaunchDescription()

    # 添加启动日志
    ld.add_action(LogInfo(msg="Starting RGBD publisher node..."))

    # 参数配置
    rgb_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "resource/images/rgb_20250610_161028_802108.png"
    )
    depth_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "resource/images/depth_20250610_161028_802108.png"
    )
    camera_info_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "resource/images/camera_info_20250610_161028_802108.yaml"
    )

    # 检查文件是否存在
    if not os.path.exists(rgb_file):
        ld.add_action(LogInfo(msg=f"Warning: RGB file not found: {rgb_file}"))
    if not os.path.exists(depth_file):
        ld.add_action(LogInfo(msg=f"Warning: Depth file not found: {depth_file}"))

    # 节点配置
    node = Node(
        package="papjia_detector",
        name="papjia_image_pub_node",
        executable="papjia_image_pub_node",
        output="screen",
        arguments=["--ros-args", "--log-level", "papjia_image_pub_node:=INFO", "--log-level", "rcl:=INFO"],
        parameters=[
            {
                "rgb_file": rgb_file,
                "rgb_topic": "/camera/camera_hand/color/image_raw",
                "depth_file": depth_file,
                "depth_topic": "/camera/camera_hand/aligned_depth_to_color/image_raw",
                "camera_info_file": camera_info_file,
                "flag_publish_cloud": True,
                "cloud_topic": "/camera/camera_hand/aligned_depth_to_color/points",
                "flag_publish_camera_info": True,
                "camera_frame": "camera_hand_color_optical_frame",
                "update_service_topic": "/papjia_image_pub_node/update_image_source",
                "camera_info_topic": "/camera/camera_hand/color/camera_info",
            }
        ],
    )

    # 添加TF节点日志
    ld.add_action(LogInfo(msg="Starting static transform publisher..."))

    tf_node_camera = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "-1.5709",
            "--pitch",
            "0",
            "--yaw",
            "-1.5709",
            "--frame-id",
            "camera_hand_link",
            "--child-frame-id",
            "camera_hand_color_optical_frame",
        ],
        output="screen",
    )

    tf_base_to_hand = Node(
        package="tf2_ros",
        name="tf_base_to_hand_static_publisher", # <-- 给一个与之前不重复的新名字
        executable="static_transform_publisher",
        arguments=[
            # --- VVVV  请根据您希望相机固定的“虚拟位置”修改这些值 VVVV ---
            "--x", "0.455",  # 示例值：在 base_link 前方 0.5 米
            "--y", "0.221",  # 示例值：在 base_link 中心
            "--z", "1.455",  # 示例值：在 base_link 上方 0.5 米
            "--roll", "0.012",
            "--pitch", "-0.171",
            "--yaw", "0.016",
            "--frame-id",
            "base_link", # <-- 父坐标系是固定的 base_link
            "--child-frame-id",
            "camera_hand_link", # <-- 子坐标系是 hand
        ],
        output="screen",
    )



    ld.add_action(node)
    ld.add_action(tf_node_camera)
    ld.add_action(tf_base_to_hand)
    ld.add_action(LogInfo(msg="Launch file configuration completed."))

    return ld
