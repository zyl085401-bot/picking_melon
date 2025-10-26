import numpy as np
import transforms3d as tf

# 已知变换参数
base_to_optical_translation = [0.6583268120125829, 0.05601538408472418, 0.9252996780174284]
base_to_optical_rotation_rpy = [-0.9802224801606779, 0.0039127458013440185, -1.6154407104405057]  # in radians

# camera_base_link到camera_base_color_optical_frame的变换 (假设为标准变换)
optical_to_base_link_translation = [0, 0, 0]
optical_to_base_link_rotation_rpy = [np.pi/2, 0, np.pi/2]  # +90° roll, +90° yaw

def transform_matrix(translation, rotation_rpy):
    """
    创建一个变换矩阵。
    :param translation: 平移向量 [x, y, z]
    :param rotation_rpy: 旋转角 [roll, pitch, yaw] (弧度)
    :return: 变换矩阵
    """
    matrix = np.eye(4)
    matrix[:3, :3] = tf.euler.euler2mat(rotation_rpy[0], rotation_rpy[1], rotation_rpy[2])
    matrix[:3, 3] = translation
    return matrix

# 计算 base_link 到 camera_base_color_optical_frame 的变换矩阵
base_to_optical_matrix = transform_matrix(base_to_optical_translation, base_to_optical_rotation_rpy)

# 计算 camera_base_color_optical_frame 到 camera_base_link 的变换矩阵
optical_to_base_link_matrix = transform_matrix(optical_to_base_link_translation, optical_to_base_link_rotation_rpy)

# 计算 base_link 到 camera_base_link 的变换
base_to_base_link_matrix = np.dot(base_to_optical_matrix, optical_to_base_link_matrix)

# 提取结果中的平移和旋转部分
final_translation = base_to_base_link_matrix[:3, 3]
final_rotation_matrix = base_to_base_link_matrix[:3, :3]
final_rotation_rpy = tf.euler.mat2euler(final_rotation_matrix)

print("Final Translation (base_link to camera_base_link):", final_translation)
print("Final Rotation RPY (base_link to camera_base_link):", np.degrees(final_rotation_rpy))