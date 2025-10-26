
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    yaml_path = '/workspace/src/papjia_melon/papjia_melon_calibration/config/handeye.yaml'
    return LaunchDescription([
        Node(
            package='papjia_melon_calibration',  # ⚠️ 你的 ROS 2 包名
            executable='handeye_calibration',  # ⚠️ 可执行文件名（setup.py中 entry_points 定义的）
            name='handeye_calibration',
            output='screen',
            parameters=[
                # {"save_path": "/workspace/src/papjia_melon/papjia_melon_calibration/pose.csv"},
                # {"cali_type": "eye_in_hand"},
                # {"skip_indices": [0,5]}  #这里设置要跳过的组编号（从1开始，符合人类习惯）
                [yaml_path]
            ]
        )
    ])
