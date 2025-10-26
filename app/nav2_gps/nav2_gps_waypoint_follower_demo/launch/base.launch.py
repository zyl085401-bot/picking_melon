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

    # 1.加载车的urdf，启动robot_state_publisher，发布tf
    urdf_file_name = "car.urdf"
    urdf = os.path.join(get_package_share_directory('nav2_gps_waypoint_follower_demo'), 'urdf', urdf_file_name)
    with open(urdf,'r') as infp:
        robot_description = infp.read()
    
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[{'robot_description': robot_description}],
        arguments=[urdf]
    )

    # 2.启动车点控制器 yhs_can_control，提供cmd_vel控制接口，提供里程计接口
    car_can_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare('yhs_can_control'), '/launch/yhs_can_control.launch.py'])
    )

    # 3.启动imu驱动
    imu_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare('hipnuc_imu'), '/launch/imu_location.launch.py'])
    )
    
    nodes = [
        robot_state_pub_node,
        car_can_control,
        imu_driver
    ]
    
    return LaunchDescription(nodes)