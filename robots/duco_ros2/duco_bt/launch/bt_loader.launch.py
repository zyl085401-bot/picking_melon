from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="papjia_behavior_tree",
                executable="papjia_bt_loader",
                output="screen",
                parameters=[
                    {
                        "plugins": [
                            "papjia/generic_behaviors",
                            "papjia/basic_behaviors",
                            "papjia/duco_bt",
                        ],
                        "service_execute_tree": "/papjia/bt/execute",
                    }
                ],
            ),
        ]
    )