from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="papjia_visualization",
                executable="papjia_visualization_service",
                name="papjia_visualization_node",
                output="screen",
                parameters=[
                    {"service_topic": "visualization_service"},
                    {"marker_topic": "visualization/markers"},
                ],
            ),
        ]
    )
