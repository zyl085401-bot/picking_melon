import matplotlib.pyplot as plt
import numpy as np
import re

def parse_angles(log_text):
    actual_angles = []
    target_angles = []
    timestamps = []
    actual_pattern = r"actual joint angles: ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)°"
    target_pattern = r"target joint angles: ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)° ([-\d.]+)°"
    timestamp_pattern = r"\[(\d+\.\d+)\]"
    
    lines = log_text.split('\n')
    for i in range(len(lines)):
        line = lines[i]
        if "actual joint angles" in line:
            actual_match = re.search(actual_pattern, line)
            time_match = re.search(timestamp_pattern, line)
            
            # Look for corresponding target angles in the next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                target_match = re.search(target_pattern, next_line)
                
                if actual_match and target_match and time_match:
                    actual_angles.append([float(x) for x in actual_match.groups()])
                    target_angles.append([float(x) for x in target_match.groups()])
                    timestamps.append(float(time_match.group(1)))
    
    return np.array(timestamps), np.array(actual_angles), np.array(target_angles)

# Read log from file
with open('trajectory_log.txt', 'r') as f:
    log_text = f.read()

# Create figure
fig, axs = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('Robot Joint Angles Trajectory')

# Joint names
joint_names = ['Joint 1', 'Joint 2', 'Joint 3', 'Joint 4', 'Joint 5', 'Joint 6']

# Parse data
timestamps, actual_angles, target_angles = parse_angles(log_text)
# Convert to relative time (starting from 0)
rel_time = timestamps - timestamps[0]

# Plot each joint angle
for i in range(6):
    row = i // 2
    col = i % 2
    
    # Plot actual angles
    axs[row, col].plot(rel_time, actual_angles[:, i], 'b-', label='Actual')
    # Plot target angles
    axs[row, col].plot(rel_time, target_angles[:, i], 'r--', label='Target')
    
    axs[row, col].set_title(f'{joint_names[i]}')
    axs[row, col].set_xlabel('Time (s)')
    axs[row, col].set_ylabel('Angle (deg)')
    axs[row, col].grid(True)
    axs[row, col].legend()

plt.tight_layout()
plt.show()