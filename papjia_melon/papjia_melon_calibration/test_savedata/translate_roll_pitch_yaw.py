from scipy.spatial.transform import Rotation as R

# 四元数 (x, y, z, w)
quat = [-0.003390249112241469,
        -0.12095625121750221,
        -0.19538737562503292,
        0.9732326879779202]

# 创建旋转对象
r = R.from_quat(quat)

# 转换成欧拉角 (roll, pitch, yaw)，单位：弧度
rpy = r.as_euler('xyz', degrees=False)

print(f"Roll (rad):  {rpy[0]}")
print(f"Pitch (rad): {rpy[1]}")
print(f"Yaw (rad):   {rpy[2]}")
