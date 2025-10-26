import numpy as np
import json
import yaml
from transformations import euler_from_matrix, matrix_to_pose

def dh_to_matrix(a, alpha, d, theta):
    """
    将给定的DH参数转换为齐次变换矩阵。
    
    参数:
    a: 关节沿x轴的位移
    alpha: 相邻关节之间的扭转角 (以弧度为单位)
    d: 关节沿z轴的位移
    theta: 关节角度 (以弧度为单位)
    
    返回值:
    4x4 齐次变换矩阵
    """
    # 计算齐次变换矩阵的每个元素
    T = np.array([
        [              np.cos(theta),              -np.sin(theta),              0,                a],
        [np.sin(theta)*np.cos(alpha), np.cos(theta)*np.cos(alpha), -np.sin(alpha), -d*np.sin(alpha)],
        [np.sin(theta)*np.sin(alpha), np.cos(theta)*np.sin(alpha),  np.cos(alpha),  d*np.cos(alpha)],
        [                          0,                           0,              0,                1]
    ])
    
    return T

def load_json(file_path):
    """
    从指定文件路径加载 JSON 数据。
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_json(data, file_path):
    """
    将数据保存为 JSON 格式到指定文件路径。
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def save_yaml(data, file_path):
    """
    将数据保存为 YAML 格式到指定文件路径。
    """
    with open(file_path, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def update_dh_params(original_dh, delta_dh):
    """
    更新原始 DH 参数。
    
    参数:
    - original_dh: 原始的 DH 参数，列表形式 [theta, d, a, alpha]
    - delta_dh: 标定后的修正值，列表形式 [delta_theta, delta_d, delta_a, delta_alpha]
    
    返回:
    - 更新后的 DH 参数
    """
    updated_dh = [orig + delta for orig, delta in zip(original_dh, delta_dh)]
    return updated_dh


# 1. 读取原始 DH 参数和标定结果
robot_dh_file = "device.json"
calibration_file = "KinematicCalibration.json"

robot_data = load_json(robot_dh_file)
calibration_data = load_json(calibration_file)

# 2. 提取 DH 参数和标定结果
original_dh_params = [link["dh"] for link in robot_data["link_list"]]
delta_dh_params = [calib["delta_dh"] for calib in calibration_data["links_kinematic_calibration"]]

# 3. 更新 DH 参数
updated_dh_params = []
for i in range(1, len(original_dh_params)):  # 从 link1 开始，因为 link0 没有 delta_dh
    updated_dh = update_dh_params(original_dh_params[i], delta_dh_params[i-1])
    updated_dh_params.append(updated_dh)

# 4. 将更新后的 DH 参数保存到原始数据结构中
for i in range(1, len(robot_data["link_list"])):  # 跳过 link0
    robot_data["link_list"][i]["dh"] = updated_dh_params[i-1]

# 5. 保存更新后的 DH 参数到新的 JSON 文件
updated_dh_file = "updated_dh_params.json"
save_json(robot_data, updated_dh_file)

print(f"Updated DH parameters have been saved to {updated_dh_file}")

# 6. 加载更新后的 DH 参数并计算齐次变换矩阵
robot_data = load_json("updated_dh_params.json")
dh_params = [link["dh"] for link in robot_data["link_list"]]
kin_cali = {}
for i in range(1, len(dh_params)):
    dh_param = dh_params[i]
    T = dh_to_matrix(dh_param[0], dh_param[1], dh_param[2], dh_param[3])
    position = matrix_to_pose(T)[:3]
    euler = euler_from_matrix(T)
    
    position_str = ' '.join([str(round(x,5)) for x in position])
    euler_str = ' '.join([str(round(x,7)) for x in euler])
    
    kin_cali[f"joint{i}"] = {
        "xyz": position_str,
        "rpy": euler_str
    }

# 7. 将数据保存为 YAML 格式
yaml_file = "kinematic_calibration.yaml"
save_yaml({"kin_cali": kin_cali}, yaml_file)

print(f"Kinematic calibration data has been saved to {yaml_file}")