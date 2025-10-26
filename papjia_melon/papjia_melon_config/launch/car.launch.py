# 启动车辆基础功能：
# 1. 启动车点控制器 yhs_can_control，提供 cmd_vel 控制接口和里程计接口
# 2. 启动 IMU 驱动，提供姿态数据
# 3. 启动 GPS 驱动，提供位置数据

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # 启动车点控制器 yhs_can_control，提供 cmd_vel 控制接口和里程计接口
    car_can_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("yhs_can_control"), "/launch/yhs_can_control.launch.py"]
        )
    )

    # 启动 IMU 驱动，提供姿态数据
    imu_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("hipnuc_imu"), "/launch/imu_location.launch.py"])
    )

    # 启动 GPS 驱动，提供位置数据
    gps_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("beitian_gps_driver"), "/launch/gps_reader.launch.py"]
        )
    )

    nodes = [
        car_can_control,
        imu_driver,
        gps_driver,
    ]

    return LaunchDescription(nodes)
