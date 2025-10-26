import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # Get the package directory
    package_name='nav2_gps_waypoint_follower_demo'


    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {'use_sim_time': False}],
        remappings=[('/cmd_vel_out','/cmd_vel')]
    )


    # camera_tf_node = Node(
    #         package='tf2_ros',
    #         executable='static_transform_publisher',
    #         name='static_transform_publisher',
    #         output='log',
    #         arguments=['0', '0', '0', '0', '0', '0', '1', 'camera_link', 'cloud'])
    
    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
        remappings=[('cloud_in', '/front_depth_camera/points')],
        # remappings=[('scan', '/scan')],
        parameters=[{
            'target_frame': 'cloud',
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
    
    # Create the launch description and populate
    ld = LaunchDescription()

    ld.add_action(twist_mux)

    return ld