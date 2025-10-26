'''
ros2 launch duco_bringup duco.launch.py
ros2 launch duco_gcr5_moveit_config move_group.launch.py capabilities:=move_group/ExecuteTaskSolutionCapability
ros2 launch papjia_arm_task_constructor arm_task_service.launch.py
ros2 launch papjia_waypoint path_build.launch.py
ros2 launch papjia_foshan_demo_config behavior_loader.launch.py
ros2 launch papjia_ev ev.launch.py
ros2 launch papjia_switch switch.launch.py
'''

from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
   
    this_package_name = "papjia_melon_config"

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/camera.launch.py']),
    )

    arm_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/arm.launch.py']),
    )

    device_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/device.launch.py']),
    )

    car_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/car.launch.py']),
    )

    vision_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/vision.launch.py']),
    )

    bt_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(this_package_name), '/launch/bt.launch.py']),
    )

    return LaunchDescription([
            camera_launch,
            arm_launch,
            device_launch,
            car_launch,
            vision_launch,
            bt_launch
    ])