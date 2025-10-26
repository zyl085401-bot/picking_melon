from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir
from launch_ros.substitutions import FindPackageShare
import os

def generate_launch_description():
    config = os.path.join(
        FindPackageShare('beitian_gps_driver').find('beitian_gps_driver'),
        'config',
        'beitian_gps_config.yaml'
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=config,
            description='Path to the config file'
        ),
        
        Node(
            package='beitian_gps_driver',
            executable='serial_reader',
            name='serial_reader',
            parameters=[LaunchConfiguration('config')],
            output='log',
        ),
    ])
