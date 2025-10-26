import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node

from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource



def generate_launch_description():
    # Get the package directory
    package_name='nav2_gps_waypoint_follower_demo'
    package_dir = get_package_share_directory('nav2_gps_waypoint_follower_demo')
    launch_dir = os.path.join(package_dir, 'launch')
    world = os.path.join(package_dir, 'worlds', 'sonoma_raceway.world')

    # Start Gazebo server
    start_gazebo_server_cmd = ExecuteProcess(
        cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world],
        cwd=[launch_dir], output='screen')

    # Start Gazebo client
    start_gazebo_client_cmd = ExecuteProcess(
        cmd=['gzclient'],
        cwd=[launch_dir], output='screen')
    
    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(package_name), "urdf", "car.urdf.xacro"]
            ),
            " ",
            "use_mock_hardware:=false",
            " ",
            "sim_gazebo_classic:=True",
            " ",
            " ",
        ]
    )

    robot_description = {
        "robot_description": robot_description_content, 
        'use_sim_time': True
    }

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {'use_sim_time': True}],
        remappings=[('/cmd_vel_out','/diff_driver_controller/cmd_vel_unstamped')]
    )

    # Spawn the robot in Gazebo
    spawn_entity_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'tracked_robot', '-x', '0.0', '-y', '0.0', '-z', '0.0', '-Y', '1.57'],
        output='screen')
    
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_driver_controller"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
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

    # Launch Gazebo
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_gazebo_client_cmd)

    # ld.add_action(camera_tf_node)

    ld.add_action(robot_state_publisher_node)

    # Spawn the robot
    ld.add_action(spawn_entity_cmd)

    ld.add_action(diff_drive_spawner)

    ld.add_action(joint_broad_spawner)

    ld.add_action(twist_mux)

    return ld