# papjia_vision/papjia_detector/papjia_detector/rgbd_saver.py 对应的启动launch文件
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 声明参数
    rgb_topic = DeclareLaunchArgument(
        'rgb_topic',
        default_value='/camera/camera_hand/color/image_raw',
        description='RGB图像话题'
    )

    depth_topic = DeclareLaunchArgument(
        'depth_topic',
        default_value='/camera/camera_hand/aligned_depth_to_color/image_raw',
        description='深度图像话题'
    )

    camera_info_topic = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera/camera_hand/color/camera_info',
        description='相机信息话题'
    )

    enable_rgb = DeclareLaunchArgument(
        'enable_rgb',
        default_value='true',
        description='是否启用RGB图像保存'
    )

    enable_depth = DeclareLaunchArgument(
        'enable_depth',
        default_value='true',
        description='是否启用深度图像保存'
    )

    enable_camera_info = DeclareLaunchArgument(
        'enable_camera_info',
        default_value='true',
        description='是否启用相机信息保存'
    )

    save_path = DeclareLaunchArgument(
        'save_path',
        default_value='/workspace/rgbd_data',
        description='数据保存路径'
    )

    save_key = DeclareLaunchArgument(
        'save_key',
        default_value='s',
        description='保存触发按键'
    )

    # 创建节点
    rgbd_saver_node = Node(
        package='papjia_detector',
        executable='rgbd_saver',
        name='rgbd_saver',
        output='screen',
        parameters=[{
            'rgb_topic': LaunchConfiguration('rgb_topic'),
            'depth_topic': LaunchConfiguration('depth_topic'),
            'camera_info_topic': LaunchConfiguration('camera_info_topic'),
            'enable_rgb': LaunchConfiguration('enable_rgb'),
            'enable_depth': LaunchConfiguration('enable_depth'),
            'enable_camera_info': LaunchConfiguration('enable_camera_info'),
            'save_path': LaunchConfiguration('save_path'),
            'save_key': LaunchConfiguration('save_key')
        }]
    )

    # 创建启动描述
    ld = LaunchDescription()

    # 添加参数
    ld.add_action(rgb_topic)
    ld.add_action(depth_topic)
    ld.add_action(camera_info_topic)
    ld.add_action(enable_rgb)
    ld.add_action(enable_depth)
    ld.add_action(enable_camera_info)
    ld.add_action(save_path)
    ld.add_action(save_key)

    # 添加节点
    ld.add_action(rgbd_saver_node)

    return ld


