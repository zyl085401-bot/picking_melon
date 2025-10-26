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
                            "papjia/vision_behaviors",
                        ],
                        "service_execute_tree": "/papjia/bt/execute",
                    }
                ],
            ),
            Node(package="examples_rclcpp_minimal_action_server", executable="action_server_not_composable", output="screen"),
        ]
    )
