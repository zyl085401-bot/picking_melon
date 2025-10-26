import numpy as np
from scipy.spatial.transform import Rotation as R

# -----------------------------
# 输入：你从 tf2_echo 得到的结果
# -----------------------------
# base_link -> camera_base_color_optical_frame
t_color_optical = np.array([0.658, 0.056, 0.925])        # translation
rpy_color_optical = np.array([-0.980, 0.004, -1.615])     # roll, pitch, yaw (radian)

# 构造旋转（注意：ROS 使用 intrinsic ZYX 顺序，等价于外在 XYZ）
# 所以我们用 'xyz' 表示外在旋转顺序（即先 roll 绕 X，再 pitch 绕 Y，最后 yaw 绕 Z）
R_color_optical = R.from_euler('xyz', rpy_color_optical)

# -----------------------------
# 已知：camera_base_link -> camera_base_color_optical_frame
# 这是标准 optical frame correction
# -----------------------------
t_cam_to_opt = np.array([0.0, 0.0, 0.0])
rpy_cam_to_opt = np.array([-np.pi/2, 0.0, -np.pi/2])  # [-1.5708, 0, -1.5708]
R_cam_to_opt = R.from_euler('xyz', rpy_cam_to_opt)

# 求逆：color_optical_frame -> camera_base_link
R_opt_to_cam = R_cam_to_opt.inv()
t_opt_to_cam = np.zeros(3)  # 因为原平移为0

# -----------------------------
# 计算：base_link -> camera_base_link
# T_total = T_color * T_opt_to_cam
# -----------------------------
R_result = R_color_optical * R_opt_to_cam
t_result = R_color_optical.apply(t_opt_to_cam) + t_color_optical
# 因为 t_opt_to_cam = 0，所以 t_result = t_color_optical

# 输出结果
rpy_result = R_result.as_euler('xyz')  # 输出 RPY，单位：弧度

print("=== T(base_link → camera_base_link) ===")
print("Translation [x, y, z]:", np.round(t_result, 6))
print("Rotation RPY [roll, pitch, yaw] (rad):", np.round(rpy_result, 6))
print("Rotation RPY [roll, pitch, yaw] (deg):", np.round(np.rad2deg(rpy_result), 6))