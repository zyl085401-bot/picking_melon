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
        get_package_share_directory("papjia_melon_config"), "resource/images/test/3_base_rgb.png"
    )
    depth_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "resource/images/test/3_base_depth.png"
    )
    camera_info_file = os.path.join(
        get_package_share_directory("papjia_melon_config"), "resource/images/test/3_camera_base_info.yaml"
    )

    # 检查文件是否存在
    if not os.path.exists(rgb_file):
        ld.add_action(LogInfo(msg=f"Warning: RGB file not found: {rgb_file}"))
    if not os.path.exists(depth_file):
        ld.add_action(LogInfo(msg=f"Warning: Depth file not found: {depth_file}"))

    # 节点配置
    node = Node(
        package="papjia_detector",
        name="papjia_image_pub_base_node",
        executable="papjia_image_pub_base_node",
        output="screen",
        arguments=["--ros-args", "--log-level", "papjia_image_pub_base_node:=INFO", "--log-level", "rcl:=INFO"],
        parameters=[
            {
                "rgb_file": rgb_file,
                "rgb_topic": "/camera/camera_base/color/image_raw",
                "depth_file": depth_file,
                "depth_topic": "/camera/camera_base/aligned_depth_to_color/image_raw",
                "camera_info_file": camera_info_file,
                "flag_publish_cloud": True,
                "cloud_topic": "/camera/camera_base/aligned_depth_to_color/points",
                "flag_publish_camera_info": True,
                "camera_frame": "camera_base_color_optical_frame",
                "update_service_topic": "/papjia_image_pub_node/update_image_source",
            }
        ],
    )

    # 添加TF节点日志
    ld.add_action(LogInfo(msg="Starting static transform publisher..."))

    tf_camera_to_optical = Node(
        package="tf2_ros",
        name="tf_camera_base_optical_broadcaster",
        executable="static_transform_publisher",
        arguments=[
            "0", "0", "0",           # 平移为0
            "-1.5709", "0", "-1.5709",  # roll=-π/2, pitch=0, yaw=-π/2
            "camera_base_link",
            "camera_base_color_optical_frame"
        ],
    )

    # tf_camera_to_optical = Node(
    #     package="tf2_ros",
    #     name="tf_node_camera",
    #     executable="static_transform_publisher",
    #     arguments=[
    #         "--x",
    #         "0",
    #         "--y",
    #         "0",
    #         "--z",
    #         "0",
    #         "--roll",
    #         "-1.5708",
    #         "--pitch",
    #         "0",
    #         "--yaw",
    #         "-1.5708",
    #         "--frame-id",
    #         "camera_base_link",
    #         "--child-frame-id",
    #         "camera_base_color_optical_frame",
    #     ],
        # output="screen",
    # )



    ld.add_action(node)
    # ld.add_action(tf_base_to_camera)
    ld.add_action(tf_camera_to_optical)
    ld.add_action(LogInfo(msg="Launch file configuration completed."))

    return ld
