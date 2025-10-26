# 车辆 Gazebo 仿真启动文件
# 功能：
# 1. 启动 Gazebo 仿真环境
# 2. 加载车辆模型到仿真环境中
# 3. 配置仿真参数和物理引擎

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
    # 获取导航功能包的路径
    gps_wpf_dir = get_package_share_directory(
        "nav2_gps_waypoint_follower_demo")
    launch_dir = os.path.join(gps_wpf_dir, 'launch')

    # 启动 Gazebo 仿真器
    # 通过 gazebo_robot.launch.py 加载车辆模型和仿真环境
    gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, 'gazebo_robot.launch.py'))
    )

    # 创建启动描述
    ld = LaunchDescription()

    # 添加 Gazebo 仿真器启动命令
    ld.add_action(gazebo_cmd)

    return ld
