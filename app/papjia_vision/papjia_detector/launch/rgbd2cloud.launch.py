"""
Description: 从保存的RGBD数据生成并发布点云的launch文件
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 声明参数
    data_path = DeclareLaunchArgument(
        "data_path", default_value="/workspace/images/rgbd_data", description="RGBD数据保存路径"
    )

    publish_rate = DeclareLaunchArgument("publish_rate", default_value="1.0", description="点云发布频率(Hz)")

    # 创建节点
    rgbd2cloud_node = Node(
        package="papjia_detector",
        executable="rgbd2cloud",
        name="rgbd2cloud",
        output="screen",
        parameters=[
            {"data_path": LaunchConfiguration("data_path"), "publish_rate": LaunchConfiguration("publish_rate")}
        ],
    )

    # 创建启动描述
    ld = LaunchDescription()

    # 添加参数
    ld.add_action(data_path)
    ld.add_action(publish_rate)

    # 添加节点
    ld.add_action(rgbd2cloud_node)

    return ld
