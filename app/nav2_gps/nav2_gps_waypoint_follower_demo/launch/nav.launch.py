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

    bringup_dir = get_package_share_directory('nav2_bringup')
    gps_wpf_dir = get_package_share_directory(
        "nav2_gps_waypoint_follower_demo")
    params_dir = os.path.join(gps_wpf_dir, "config")
    nav2_params = os.path.join(params_dir, "nav2_no_map_params.yaml")
    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )

    # 8. 启动导航
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "False",
            "params_file": configured_params,
            "autostart": "true",
        }.items(),
    )


    nodes = [
        nav2
    ]
    
    return LaunchDescription(nodes)