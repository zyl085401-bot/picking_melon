from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    read_device = "/dev/papjia_gps"
    
    return LaunchDescription(
        [
            Node(
                package="beitian_gps_driver",
                executable="gps_reader",
                name="gps_reader",
                parameters=[
                    {
                        "port": read_device,
                        "baudrate": 115200,
                        "gps_frame": "gps_link",
                        "default_latitude": 23.1786054285,
                        "default_longitude": 113.401730728,
                        "default_course": 0.0,
                    }
                ],
                output="screen",
            ),
        ]
    )
