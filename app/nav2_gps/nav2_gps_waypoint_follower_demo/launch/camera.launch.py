# 1. 加载车的urdf，启动robot_state_publisher，发布tf
# 2. 启动车点控制器 yhs_can_control，提供cmd_vel控制接口，提供里程计接口
# 3. 启动imu驱动
# 4. 启动gps驱动
# 5. 启动realsense相机驱动，启动点云转激光
# 6. 启动定位
# 7. 启动rviz和启动mapviz
# 8. 启动导航

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml

def generate_launch_description():

    # 5. 启动realsense相机驱动
    rs_435i_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare('realsense2_camera'), '/launch/rs_launch.py']),
        launch_arguments = {
           'depth_module.profile': '1280x720x15',
           'rgb_camera.profile':  '1280x720x15',
           'align_depth.enable': 'true',
           'reconnect_timeout': '3.0',
           'pointcloud.enable': 'true',
       }.items()
    )
    
    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
        remappings=[('cloud_in', '/camera/camera/depth/color/points')],
        # remappings=[('scan', '/scan')],
        parameters=[{
            'target_frame': 'camera_link',
            'transform_tolerance': 0.01,
            'min_height': 0.0,
            'max_height': 1.0,
            'angle_min': -0.5236,
            'angle_max': 0.5236,
            'angle_increment': 0.0087,  # M_PI/360.0
            'scan_time': 0.3333,
            'range_min': 0.5,
            'range_max': 5.0,
            'use_inf': True,
            'inf_epsilon': 1.0
        }],
        name='pointcloud_to_laserscan')

    nodes = [
        rs_435i_driver,
        pointcloud_to_laserscan_node
    ]
    
    return LaunchDescription(nodes)