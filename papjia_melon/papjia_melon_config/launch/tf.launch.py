import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import LogInfo


def generate_launch_description():
    ld = LaunchDescription()

    tf_camera_hand_link_to_base_link = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "1.0566122847318475",
            "--y",
            "0.020736346429414243",
            "--z",
            "1.2979572303492701",
            "--qx",
            "0.020363254520771347",
            "--qy",
            "-0.0412057119604429",
            "--qz",
            "0.011956790881517246",
            "--qw",
            "0.9988715945100105",
            "--frame-id",
            "base_link",
            "--child-frame-id",
            "camera_hand_link",
        ],
        output="screen",
    )

    tf_camera_hand_color_optical_frame_to_camera_hand_link = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "-1.5709",
            "--pitch",
            "0",
            "--yaw",
            "-1.5709",
            "--frame-id",
            "camera_hand_link",
            "--child-frame-id",
            "camera_hand_color_optical_frame",
        ],
    )

    tf_camera_base_color_optical_frame_to_camera_base_link = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "-1.5709",
            "--pitch",
            "0",
            "--yaw",
            "-1.5709",
            "--frame-id",
            "camera_base_link",
            "--child-frame-id",
            "camera_base_color_optical_frame",
        ],
    )



    tf_board_link_to_camera_hand_color_optical_frame = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "-0.028719909168673095",
            "--y",
            "0.12008276782047228",
            "--z",
            "0.5038858521371771",
            "--qx",
            "0.9966852044736503",
            "--qy",
            "-0.011576330055154726",
            "--qz",
            "-0.06746760109600815",
            "--qw",
            "0.04396264969405324",
            "--frame-id",
            "camera_hand_color_optical_frame",
            "--child-frame-id",
            "board_link",
        ],
    )
############################################################
    tf_board_link_to_camera_base_color_optical_frame = Node(
        package="tf2_ros",
        name="tf_node_camera",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "-0.05192392686762353",
            "--y",
            "0.2604471174122433",
            "--z",
            "0.9185107299113705",
            "--qx",
            "0.9548185294957703",
            "--qy",
            "-0.0010835302753495015",
            "--qz",
            "-0.033719589863140075",
            "--qw",
            "0.2952683372004843",
            "--frame-id",
            "camera_base_color_optical_frame",
            "--child-frame-id",
            "board_link",
        ],
    )
############################################################
    # [0.955, -0.001, -0.034, -0.295]
    tf_camera_base_color_optical_frame_to_board = Node(
        package="tf2_ros",
        name="tf_node_base",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0.116",
            "--y",
            "-0.302",
            "--z",
            "0.900",
            "--qx",
            "0.955",
            "--qy",
            "-0.001",
            "--qz",
            "-0.034",
            "--qw",
            "-0.295",
            "--frame-id",
            "board_link",
            "--child-frame-id",
            "camera_base_color_optical_frame",
        ],
    )

    ld.add_action(tf_camera_hand_link_to_base_link)
    ld.add_action(tf_camera_hand_color_optical_frame_to_camera_hand_link)
    ld.add_action(tf_board_link_to_camera_hand_color_optical_frame)
    ld.add_action(tf_camera_base_color_optical_frame_to_board)
    # ld.add_action(tf_board_link_to_camera_base_color_optical_frame)
    # ld.add_action(tf_board_link_to_camera_base_color_optical_frame)
    ld.add_action(LogInfo(msg="Launch file configuration completed."))

    return ld
