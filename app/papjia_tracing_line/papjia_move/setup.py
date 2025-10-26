"""
@Descripttion: 
@version: 
@Author: 崔译文
@Date: 2024-03-14 09:35:53
@LastEditors: 崔译文
@LastEditTime: 2024-03-14 14:25:48
"""

import os
from glob import glob
from setuptools import find_packages, setup

package_name = "papjia_move"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="yw",
    maintainer_email="cuigw@mail.ustc.edu.cn",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["move_service = papjia_move.move:main"],
    },
)
