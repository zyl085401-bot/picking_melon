##launch file
import os

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    imu_config = os.path.join(
        get_package_share_directory('hipnuc_imu'),
        'config',
        'hipnuc_config.yaml',
    ),
    
    # ekf_config = os.path.join(
    #     get_package_share_directory('hipnuc_imu'),
    #     'config',
    #     'ekf_config.yaml'
    # )

    imu_node = Node(
        package='hipnuc_imu',
        executable='talker',
            name='IMU_publisher',
            output='log',
            parameters=[imu_config]
            )
    
    # ekf_location_node = Node(
    #     package='robot_localization',
    #     executable='ekf_node',
    #     name='ekf_filter_node',
    #     output='log',
    #     parameters=[ekf_config],
    #     remappings=[
    #         ('/odometry/filtered', '/odom')
    #     ]
    # )
    
    return LaunchDescription([
        imu_node,
        # ekf_location_node
    ])



