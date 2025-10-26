from transformations import *
import numpy as np

link6_to_camera_color = [-0.02789510, 0.00139138, 0.2081727, -0.0002320, 0.002490197, 0.0190897, 0.999814]
camera_link_to_color = [-0.00043854, 0.014769, 9.6446e-05, -0.49403, 0.50499, -0.49354, 0.50729]

camera_link_to_color_mat = pose_to_matrix(camera_link_to_color)
camera_color_to_link6_mat = np.linalg.inv(pose_to_matrix(link6_to_camera_color))

camera_link_to_link6_mat = np.dot(camera_link_to_color_mat, camera_color_to_link6_mat)
link6_to_camera_link = matrix_to_pose(np.linalg.inv(camera_link_to_link6_mat))

print(link6_to_camera_link)

print(euler_from_matrix(np.linalg.inv(camera_link_to_link6_mat)))