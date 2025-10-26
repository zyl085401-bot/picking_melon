import launch
import launch.actions
import launch.substitutions
import launch_ros.actions
import os
from ament_index_python.packages import get_package_share_directory

gps_driver_dir = get_package_share_directory("beitian_gps_driver")
mapviz_config_file = os.path.join(gps_driver_dir, "config", "gps.mvc")


def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="swri_transform",
            arguments=["0", "0", "0", "0", "0", "0", "map", "origin"],
            output="log",
        ),
        launch_ros.actions.Node(
            package="swri_transform_util",
            executable="initialize_origin.py",
            name="initialize_origin",
            parameters=[
                {
                    "local_xy_origins": [
                        23.135,
                        113.288,
                        0.0,
                        0.0
                    ]
                },
            ],
            remappings=[
                ("fix" , "gps/fix"),
            ],
            output="log",
        ),
        launch_ros.actions.Node(
            package="mapviz",
            executable="mapviz",
            name="mapviz",
            parameters=[{"config": mapviz_config_file}],
            output="log",
        ),
    ])
