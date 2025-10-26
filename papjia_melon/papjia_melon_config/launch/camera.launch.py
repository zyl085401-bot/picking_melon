# 相机启动文件
# 功能：
# 1. 启动 RealSense 相机（基座相机和手部相机）
# 2. 配置相机参数（分辨率、点云等）
# 3. 可选启动 ChArUco 标定板检测功能
# 4. 支持相机重连和错误恢复 ？？？

import os

from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    # 声明启动参数
    declared_arguments = []
    # 添加是否启用标定板检测的参数
    declared_arguments.append(
        DeclareLaunchArgument(
            "detect_charucoboard",
            default_value="false",
            description="Whether to enable charucoboard detection or not",
        )
    )
    detect_charucoboard = LaunchConfiguration("detect_charucoboard")
    
    # 启动基座相机
    # 配置参数：
    # - camera_name: 相机名称
    # - serial_no: 相机序列号
    # - depth_module.profile: 深度相机分辨率（1280x720，15fps）
    # - rgb_camera.profile: RGB相机分辨率（1280x720，15fps）
    # - align_depth.enable: 启用深度对齐
    # - reconnect_timeout: 重连超时时间
    # - pointcloud.enable: 启用点云输出
    camera_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("realsense2_camera"), '/launch/rs_launch.py']),
        launch_arguments = {
            'camera_name': 'camera_base',
            'serial_no': "'216322075474'",
            'depth_module.profile': '1280x720x15',
            'rgb_camera.profile':  '1280x720x15',
            'align_depth.enable': 'true',
            'reconnect_timeout': '3.0',
            'pointcloud.enable': 'true',
        }.items(),
    )
    
    # 启动手部相机
    # 配置参数与基座相机相同，但使用不同的序列号
    camera_hand_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("realsense2_camera"), '/launch/rs_launch.py']),
        launch_arguments = {
            'camera_name': 'camera_hand',
            'serial_no': "'244222071821'",
            'depth_module.profile': '1280x720x15',
            'rgb_camera.profile':  '1280x720x15',
            'align_depth.enable': 'true',
            'reconnect_timeout': '3.0',
            'pointcloud.enable': 'true',
        }.items(),
    )
    
    # 加载 ChArUco 标定板检测的配置文件
    charuco_config = os.path.join(get_package_share_directory('papjia_melon_config'), 'config', 'charuco.yaml')
    
    # 基座相机的标定板检测节点
    # 根据 detect_charucoboard 参数决定是否启动
    camera_base_charuco_detector = Node(
        package='charuco_detector',
        executable='charuco_detector_node',
        name='camera_base_charuco_detector',
        output='screen',
        parameters=[charuco_config],
        condition=IfCondition(detect_charucoboard)
    )
    
    # 手部相机的标定板检测节点
    # 根据 detect_charucoboard 参数决定是否启动
    camera_hand_charuco_detector = Node(
        package='charuco_detector',
        executable='charuco_detector_node',
        name='camera_hand_charuco_detector',
        output='screen',
        parameters=[charuco_config],
        condition=IfCondition(detect_charucoboard)
    )
    
    # 组合需要启动的节点
    # 目前只启用手部相机和其标定板检测
    nodes = [
        camera_base_launch,  # 基座相机暂时注释
        camera_hand_launch    # 启用手部相机
    ]
    
    nodes += [
        camera_base_charuco_detector,  # 基座相机标定板检测暂时注释
        camera_hand_charuco_detector   # 启用手部相机标定板检测
    ]

    return LaunchDescription(declared_arguments + nodes)