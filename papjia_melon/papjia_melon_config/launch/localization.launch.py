# 实际环境下的定位启动文件
# 功能：
# 1. 启动实际环境下的机器人定位（EKF + GPS）
# 2. 启动可视化工具（RViz 和 Mapviz）
# 3. 启动速度混控器

# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # 获取功能包路径
    bringup_dir = get_package_share_directory('papjia_melon_config')
    gps_wpf_dir = get_package_share_directory(
        "nav2_gps_waypoint_follower_demo")
    launch_dir = os.path.join(gps_wpf_dir, 'launch')

    # 声明可视化工具启动参数
    use_rviz = LaunchConfiguration('use_rviz')      # 是否启动 RViz
    use_mapviz = LaunchConfiguration('use_mapviz')  # 是否启动 Mapviz

    # 配置 RViz 启动参数
    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Whether to start RVIZ')

    # 配置 Mapviz 启动参数
    declare_use_mapviz_cmd = DeclareLaunchArgument(
        'use_mapviz',
        default_value='False',
        description='Whether to start mapviz')

    # 启动实际环境下的机器人定位
    # 使用 EKF 融合 IMU 和 GPS 数据，与仿真版本使用不同的启动文件
    robot_localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'dual_ekf_navsat.launch.py'))
    )

    # 启动 RViz 可视化工具
    # 用于显示机器人状态、传感器数据和路径规划
    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", 'rviz_launch.py')),
        condition=IfCondition(use_rviz)
    )

    # 启动 Mapviz 可视化工具
    # 用于显示 GPS 轨迹和地图数据
    mapviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'mapviz.launch.py')),
        condition=IfCondition(use_mapviz)
    )

    # 启动速度混控器
    # 用于处理多个速度输入源（如导航、遥控等）
    twist_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'twist_mux.launch.py'))
    )

    # 创建启动描述
    ld = LaunchDescription()

    # 添加定位功能
    ld.add_action(robot_localization_cmd)

    # 添加可视化工具
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(rviz_cmd)
    ld.add_action(declare_use_mapviz_cmd)
    ld.add_action(mapviz_cmd)
    ld.add_action(twist_cmd)

    return ld
