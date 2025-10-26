# 机械臂启动文件
# 功能：
# 1. 加载机械臂的 URDF 模型
# 2. 启动 ros2_control 控制器管理器
# 3. 启动机器人状态发布器
# 4. 启动 RViz 可视化工具
# 5. 启动关节状态广播器
# 6. 启动机械臂控制器
# 7. 启动 MoveIt 运动规划功能

import os

from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution, PythonExpression

from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    
    # 定义包名和机器人名称
    package_name = "papjia_melon_config"
    moveit_package_name = "papjia_melon_moveit_config"
    robot_name = "melon_grasper"
    controllers_file = "arm_controllers.yaml"          # 实际硬件控制器配置文件
    controllers_sim_file = "arm_controllers_sim.yaml"  # 仿真控制器配置文件
    robot_description_file = "robot.urdf.xacro"        # 机器人描述文件

    # 加载 MoveIt 配置
    moveit_config = MoveItConfigsBuilder(robot_name, package_name=moveit_package_name).to_moveit_configs()
    
    # 声明启动参数
    declared_arguments = []
    # 添加是否使用模拟硬件的参数
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_mock_hardware",
            default_value="false",
            description="Start robot with mock hardware mirroring command to its states.",
        )
    )
    use_mock_hardware = LaunchConfiguration("use_mock_hardware")
    
    # 生成机器人描述
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("papjia_melon_config"), "description", "robot.urdf.xacro"]
            ),
            " ",
            "use_mock_hardware:=",
            use_mock_hardware,
            " ",
            "robot_ip:=192.168.1.10",  # 机械臂控制器 IP 地址
            " ",
        ]
    )

    robot_description = {"robot_description": robot_description_content}

    # 根据是否使用模拟硬件选择对应的控制器配置文件
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare(package_name),
            "config",
            PythonExpression([
                "'", controllers_sim_file, "' if '", use_mock_hardware, "' == 'true' else '", controllers_file, "'"
            ])
        ]
    )
    # RViz 配置文件路径
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("papjia_melon_config"), "rviz", "rviz.rviz"]
    )

    # 启动 ros2_control 控制器管理器节点
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="both",
        parameters=[robot_description, robot_controllers],
    )
    # 启动机器人状态发布器节点
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    # 启动 RViz 可视化节点
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[moveit_config.to_dict()]
    )

    # 启动关节状态广播器
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    # 定义并启动机械臂控制器
    robot_controller_names = ["arm_controller"]
    robot_controller_spawners = []
    for controller in robot_controller_names:
        robot_controller_spawners += [
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[controller, "-c", "/controller_manager"],
            )
        ]

    # 设置节点启动顺序：等待 ros2_control_node 启动后，延迟 2 秒启动关节状态广播器
    delay_joint_state_broadcaster_spawner_after_ros2_control_node = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=control_node,
            on_start=[
                TimerAction(
                    period=2.0,
                    actions=[joint_state_broadcaster_spawner],
                ),
            ],
        )
    )

    # 设置节点启动顺序：等待关节状态广播器启动后，依次启动机械臂控制器
    delay_robot_controller_spawners_after_joint_state_broadcaster_spawner = []
    for i, controller in enumerate(robot_controller_spawners):
        delay_robot_controller_spawners_after_joint_state_broadcaster_spawner += [
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=robot_controller_spawners[i - 1]
                    if i > 0
                    else joint_state_broadcaster_spawner,
                    on_exit=[controller],
                )
            )
        ]
    
    # 启动 MoveIt 运动规划功能
    arm_move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("papjia_melon_moveit_config"), '/launch/move_group.launch.py']),
        launch_arguments = {
            'capabilities': 'move_group/ExecuteTaskSolutionCapability'
        }.items(),
    )
    
    # 组合所有节点
    nodes = [
        control_node,
        robot_state_pub_node,
        rviz_node,
        delay_joint_state_broadcaster_spawner_after_ros2_control_node,
        arm_move_group_launch,
    ] + delay_robot_controller_spawners_after_joint_state_broadcaster_spawner

    return LaunchDescription(declared_arguments + nodes)
