import launch
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    serial_reader = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [get_package_share_directory('beitian_gps_driver'), '/launch/serial_reader_launch.py']
        )
    )

    dual_ekf_navsat = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [get_package_share_directory('beitian_gps_driver'), '/launch/dual_ekf_navsat.launch.py']
        )
    )

    mapviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [get_package_share_directory('beitian_gps_driver'), '/launch/mapviz.launch.py']
        )
    )

    delayed_mapviz = TimerAction(
        period=2.5,
        actions=[mapviz],
    )

    return LaunchDescription([
        serial_reader,
        dual_ekf_navsat,
        delayed_mapviz
    ])
