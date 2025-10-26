from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    socat_path = "socat"
    read_device = "/tmp/ttyUSB_READ"
    write_device = "/tmp/ttyUSB_WRITE"
    write_interval = 1.0
    default_latitude = 23.14
    default_longitude = 113.29

    virtual_serial_node = Node(
        package="beitian_gps_driver",
        executable="virtual_serial",
        name="virtual_serial_node",
        parameters=[{"read_alias": read_device, "write_alias": write_device, "socat_path": socat_path}],
        output="screen",
    )

    write_gps_node = Node(
        package="beitian_gps_driver",
        executable="gps_writer",
        name="write_gps_node",
        parameters=[{"device": write_device, "latitude": default_latitude, "longitude": default_longitude, "interval": write_interval}],
        output="screen",
    )

    return LaunchDescription([virtual_serial_node, write_gps_node])
