"""
Descripttion: ROS2 python包配置文件
version: 2.0
Author: 崔译文
Date: 2023-12-18 09:00:50
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:39:04
"""

import os
from glob import glob
from setuptools import find_packages, setup

package_name = "papjia_detector"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.py")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*yaml")),
        ),
        (
            os.path.join("share", package_name, "resource/weights"),
            glob(os.path.join("resource/weights", "*.*")),
        ),
        (
            os.path.join("share", package_name, "resource/images"),
            glob(os.path.join("resource/images", "*.*")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="yw",
    maintainer_email="yw@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "papjia_mask_node = papjia_detector.papjia_mask_node:main",
            "papjia_image_pub_node = papjia_detector.image_pub:main",
            "papjia_image_pub_base_node = papjia_detector.image_pub_base:main",
            "rgbd_saver = papjia_detector.rgbd_saver:main",
            "cloud_saver = papjia_detector.cloud_saver:main",
            "rgbd2cloud = papjia_detector.rgbd2cloud:main",
        ],
    },
)
