#!/usr/bin/env python3
import matplotlib.pyplot as plt
import re
import numpy as np
import os
import matplotlib

# 直接使用英文标签，不尝试中文支持
use_chinese = False

# 获取日志文件的路径
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, "trajectory_log.txt")

# 初始化数据存储列表
points = []
joint_values = []

# 读取并解析日志文件
with open(log_file, 'r') as f:
    for line in f:
        if "Received point" in line:
            # 使用正则表达式提取关节角度值
            match = re.search(r'Received point (\d+) : ([-\d\.]+)° ([-\d\.]+)° ([-\d\.]+)° ([-\d\.]+)° ([-\d\.]+)° ([-\d\.]+)°', line)
            if match:
                point_num = int(match.group(1))
                joints = [float(match.group(i)) for i in range(2, 8)]
                points.append(point_num)
                joint_values.append(joints)

# 转换为numpy数组以便处理
joint_values = np.array(joint_values)

# 设置英文标签
joint_names = ['Joint 1', 'Joint 2', 'Joint 3', 'Joint 4', 'Joint 5', 'Joint 6']
x_label = 'Path Point'
y_label = 'Joint Angle (°)'
title_all = 'Joint Angle Trajectory'
title_joint2 = 'Joint 2 Angle Trajectory (Collision occurred at this joint)'
collision_area = 'Collision Area'
error_msg = "Error: [0x00A10004] Robot detected collision: Safety collision reaction triggered - Joint 2"
title_3d = 'Joint Angle Space Trajectory Visualization'
traj_label = 'Trajectory'
collision_point = 'Collision Point'

# 颜色和线型
colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown']
line_styles = ['-', '-', '-', '--', '-.', ':']
line_widths = [1.5, 1.5, 1.5, 2, 2, 2]

# 创建图1：所有关节轨迹概览
plt.figure(figsize=(12, 6))
for i in range(6):
    plt.plot(points, joint_values[:, i], label=joint_names[i], 
             color=colors[i], linestyle=line_styles[i], linewidth=line_widths[i])
plt.xlabel(x_label)
plt.ylabel(y_label)
plt.title(title_all)
plt.legend()
plt.grid(True)
plt.axvspan(50, 51, alpha=0.3, color='red')
plt.tight_layout()
plt.savefig(os.path.join(script_dir, "trajectory_overview.png"))
plt.show()

# 创建图2：每个关节的单独图表
plt.figure(figsize=(15, 10))
for i in range(6):
    plt.subplot(3, 2, i+1)  # 使用3x2的网格，索引从1到6
    plt.plot(points, joint_values[:, i], label=joint_names[i], 
             color=colors[i], linewidth=2)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f'{joint_names[i]} Trajectory')
    plt.legend()
    plt.grid(True)
    
    # 高亮显示碰撞区域，特别是关节2
    if i == 1:  # 关节2
        plt.axvspan(50, 51, alpha=0.3, color='red', label=collision_area)
        plt.title(title_joint2)
    else:
        plt.axvspan(50, 51, alpha=0.1, color='red')

# 添加错误信息注释
plt.figtext(0.5, 0.01, error_msg, ha="center", fontsize=10, bbox={"facecolor":"red", "alpha":0.2, "pad":5})

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig(os.path.join(script_dir, "trajectory_details.png"))
plt.show()

# 创建一个简单的3D关节位置变化图
try:
    from mpl_toolkits.mplot3d import Axes3D
    
    # 这里我们简单地使用前三个关节角度来创建一个3D图
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 用前三个关节角度创建3D轨迹
    ax.plot(joint_values[:, 0], joint_values[:, 1], joint_values[:, 2], 'b-', label=traj_label)
    ax.plot(joint_values[-1, 0], joint_values[-1, 1], joint_values[-1, 2], 'ro', label=collision_point)
    
    ax.set_xlabel(joint_names[0] + ' (°)')
    ax.set_ylabel(joint_names[1] + ' (°)')
    ax.set_zlabel(joint_names[2] + ' (°)')
    ax.set_title(title_3d)
    ax.legend()
    
    plt.savefig(os.path.join(script_dir, "trajectory_3d_visualization.png"))
    plt.show()
    
    # 额外添加一个不同角度的3D图
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 使用不同组合的关节角度
    ax.plot(joint_values[:, 3], joint_values[:, 4], joint_values[:, 5], 'g-', label=traj_label)
    ax.plot(joint_values[-1, 3], joint_values[-1, 4], joint_values[-1, 5], 'ro', label=collision_point)
    
    ax.set_xlabel(joint_names[3] + ' (°)')
    ax.set_ylabel(joint_names[4] + ' (°)')
    ax.set_zlabel(joint_names[5] + ' (°)')
    ax.set_title('Additional Joint Angle Space Visualization')
    ax.legend()
    
    plt.savefig(os.path.join(script_dir, "trajectory_3d_visualization_2.png"))
    plt.show()
except ImportError:
    print("3D plotting library not installed, skipping 3D visualization")
except Exception as e:
    print(f"Error in 3D visualization: {e}")

print("Visualization completed. Generated charts have been saved to the same directory.")

# 输出各关节的角度变化率分析
if len(joint_values) > 1:
    print("\nJoint angle change rate analysis:")
    for i in range(6):
        joint_angles = joint_values[:, i]
        joint_changes = np.diff(joint_angles)
        
        print(f"\n{joint_names[i]}:")
        print(f"  Maximum change rate: {np.max(np.abs(joint_changes)):.4f}°/step")
        print(f"  Average change rate: {np.mean(np.abs(joint_changes)):.4f}°/step")
        print(f"  Last position: {joint_angles[-1]:.4f}°")
        
        # 检查角度变化是否有明显异常
        threshold = np.mean(np.abs(joint_changes)) + 2 * np.std(np.abs(joint_changes))
        anomalies = np.where(np.abs(joint_changes) > threshold)[0]
        if len(anomalies) > 0:
            print(f"  Anomalous points: {anomalies + 1} -> {anomalies + 2}") 