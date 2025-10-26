"""
Descripttion: 图像分割的lanuch文件
version: 2.0
Author: 崔译文
Date: 2023-12-19 15:30:44
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:14:36
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    # 参数配置
    params = [
        {"name": "model_type", "default": "yolo", "description": "模型类型"},
        {"name": "resource_dir", "default": os.path.join(get_package_share_directory("papjia_detector"), "resource"), "description": "资源文件夹"},
        {"name": "model_path", "default": "weights/tube.pt", "description": "模型权重文件"},
        {"name": "labels", "default": '["M1", "M2", M3]', "description": "类别名称"},
        {"name": "rect", "default": "[0, 0, 1280, 720]", "description": "[x1,y1,x2,y2]"},
        {"name": "device", "default": '"0"', "description": "设备ID"},
        {"name": "sample_image", "default": "images/sample_glass_tube.jpg", "description": "预分割图像"},
        {"name": "channels", "default": "rgb", "description": "图像通道顺序"},
        {"name": "service_topic", "default": "/papjia_vision/service_image_segment", "description": "服务名称"},
        {"name": "result_image_topic", "default": "/papjia_vision/service_image_segment/result_image", "description": "服务调佣结果"},
        {"name": "prepare_times", "default": "2", "description": "预分割次数"},
        {"name": "with_mask", "default": "False", "description": "是否是分割模型"},
        {"name": "rect_height_ratio", "default": "0.99", "description": "取部分rect"},
    ]

    # 创建参数声明列表
    declare_arguments = [DeclareLaunchArgument(param["name"], default_value=param["default"], description=param["description"]) for param in params]

    # 创建节点参数字典
    node_params = {param["name"]: LaunchConfiguration(param["name"]) for param in params}

    # 创建节点
    node = Node(package="papjia_detector", name="papjia_vision_ripeness_node", executable="papjia_mask_node", output="screen", parameters=[node_params])

    # 返回 LaunchDescription
    return LaunchDescription(declare_arguments + [node])
