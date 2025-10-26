# 行为树加载器启动文件
# 功能：
# 1. 加载行为树插件配置文件
# 2. 加载 MoveIt 配置
# 3. 启动行为树加载器节点，用于加载和执行自定义行为树节点

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # 加载行为树插件配置文件路径
    bt_plugins = os.path.join(
        get_package_share_directory('papjia_melon_config'),
        'config',
        'bt_plugins.yaml'  # 行为树插件配置文件，定义了自定义行为树节点的类型和参数
    )
    
    # 加载 MoveIt 配置，用于行为树节点与机械臂交互
    moveit_config = MoveItConfigsBuilder("melon_grasper", package_name="papjia_melon_moveit_config").to_moveit_configs()

    # 启动行为树加载器节点
    return LaunchDescription([
        Node(
            package='papjia_behavior_tree',  # 行为树功能包
            executable='papjia_bt_loader',   # 行为树加载器可执行文件
            output="screen",                 # 输出到屏幕，方便调试
            parameters=[
                bt_plugins,                  # 行为树插件配置
                moveit_config.to_dict()      # MoveIt 配置，用于机械臂控制
            ],
        )
    ])