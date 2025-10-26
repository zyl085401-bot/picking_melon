"""
@Descripttion: 摄像头模型, 用于计算2d->3d
@version: 1.0
@Author: 崔译文
@Date: 2024-03-11 10:14:13
@LastEditors: 崔译文
@LastEditTime: 2024-04-09 10:57:43
"""

import numpy as np
import yaml
import math
import transforms3d as tfs


def pose_to_matrix(position, rpy):
    """将位姿（位姿和旋转角）转化为对应的齐次矩阵

    Args:
        position (list): 位置
        rpy (list): 欧拉角

    Returns:
        np.ndarray: 齐次矩阵
    """
    translation = np.array(position)
    rotation = tfs.euler.euler2mat(rpy[0], rpy[1], rpy[2])
    # 构建转换矩阵
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return matrix


class CameraModel:
    def __init__(self, config_file=None, pose_left2right=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]):
        """相机模型的初始化，主要读入配置信息

        Args:
            config_file (string): 配置文件路径
        """
        if config_file:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
                self.update(config=config)
        self.pose_left2right = pose_left2right

    def update(self, config):
        self.image_width = config["image_width"]
        self.image_height = config["image_height"]
        self.camera_name = config["camera_name"]
        # 相机内参
        self.camera_matrix = np.array(config["camera_matrix"]["data"]).reshape(
            (config["camera_matrix"]["rows"], config["camera_matrix"]["cols"])
        )
        # 畸变系数
        self.distortion_coefficients = np.array(config["distortion_coefficients"]["data"]).reshape(
            (config["distortion_coefficients"]["rows"], config["distortion_coefficients"]["cols"])
        )
        # 校正矩阵
        self.rectification_matrix = np.array(config["rectification_matrix"]["data"]).reshape(
            (config["rectification_matrix"]["rows"], config["rectification_matrix"]["cols"])
        )
        # 投影矩阵
        self.projection_matrix = np.array(config["projection_matrix"]["data"]).reshape(
            (config["projection_matrix"]["rows"], config["projection_matrix"]["cols"])
        )
        # 相机模型
        self.distortion_model = config["distortion_model"]
        # 相机位姿
        self.camera_pose = config["camera_pose"]
        # 位姿矩阵
        self.pose_matrix = np.dot(
            pose_to_matrix(self.camera_pose[0:3], self.camera_pose[3:6]),
            pose_to_matrix(self.pose_left2right[0:3], self.pose_left2right[3:6]),
        )

        # 世界平面方程（基于相机）
        self.oxy = self.plane_oxy()

    def pixel_to_camera(self, pixel_coords):
        """将特殊平面的在相机中的像素坐标转化为相机坐标系下的3D坐标

        Args:
            pixel_coords (list): 像素坐标

        Returns:
            list: 3D点对应的齐次坐标
        """
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        u, v = pixel_coords
        x = (u - cx) * (1 / fx)
        y = (v - cy) * (1 / fy)
        z = 1.0
        a = self.oxy[0] * x + self.oxy[1] * y + self.oxy[2]
        if a == 0:
            print("!!! Error in pixel_to_camera !!!")
        else:
            z = -self.oxy[3] / a
            x *= z
            y *= z
        return [x, y, z, 1]

    def camera_to_world(self, point):
        """将一个点的相机坐标下的位置坐标转化为世界坐标系下的坐标

        Args:
            point (np.ndarray): 相机坐标系下的3D坐标

        Returns:
            np.ndarray: 世界坐标系下的3D坐标
        """
        position = np.dot(self.pose_matrix, point)
        return position

    def pixel_to_world(self, pixel_coords):
        """将特殊平面的在相机中的像素坐标转化为世界坐标系下的3D坐标

        Args:
            pixel_coords (list): 像素坐标

        Returns:
            np.ndarray: 世界坐标系下的坐标
        """
        point = self.pixel_to_camera(pixel_coords)
        position = self.camera_to_world(point)
        return position

    def plane_oxy(self):
        """世界坐标系oxy平面在相机坐标系下的平面方程

        Returns:
            list: 平面oxy的平面方程参数
        """
        M = np.linalg.inv(self.pose_matrix)
        a, b, c = M[0:3, 2]
        d = -(a * M[0, 3] + b * M[1, 3] + c * M[2, 3])
        return [a, b, c, d]
