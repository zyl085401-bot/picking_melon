import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

package_name = 'papjia_melon_device'


def generate_launch_description():
    ld = LaunchDescription()
    # 参数配置
    config = os.path.join(
        get_package_share_directory(package_name), "config", "device.yaml"
    )
    
    # 节点配置
    node = Node(
        package=package_name,
        name="papjia_melon_device",
        executable="papjia_melon_device",
        output="screen",
        parameters=[config],
    )

    ld.add_action(node)
    return ld
