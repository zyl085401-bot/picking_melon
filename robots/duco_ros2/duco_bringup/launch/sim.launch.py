import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros.descriptions
from launch.conditions import IfCondition

from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    
    package_name = "duco_bringup"
    moveit_package_name = "duco_gcr5_moveit_config"
    
    duco_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(package_name), '/launch/duco.launch.py']),
        launch_arguments = {
            'controllers_file': 'duco_controllers_sim.yaml',
            'use_mock_hardware': 'true',
            'robot_controller': 'joint_trajectory_controller',
            'rviz': 'true'
        }.items(),
    )
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(moveit_package_name), '/launch/move_group.launch.py']),
        launch_arguments = {
            'capabilities': 'move_group/ExecuteTaskSolutionCapability'
        }.items(),
    )

    return LaunchDescription([
        duco_launch,
        move_group_launch
    ])
