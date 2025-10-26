import json

from papjia_melon_config.actions.arm_move import get_plan_and_execute_waypoints_sequence, JointWaypoint, CartWaypoint, get_waypoint_from_config

from papjia_skill.action_models import ActionModels

ActionModels("/workspace/src/papjia_melon/papjia_melon_config/config/action_model.yaml")

waypoint_file_path = "/workspace/src/papjia_melon/papjia_melon_config/config/waypoint_configs.json"
with open(waypoint_file_path, "r") as f:
    all_waypoint_configs = json.load(f)
waypoint_configs = all_waypoint_configs['test_tube']

w1 = JointWaypoint(
    waypoint_name="w1",
    joint_names=waypoint_configs['home']['joint_names'],
    joint_values=waypoint_configs['home']['joint_values'],
    group=waypoint_configs['home']['group'],
    planner=waypoint_configs['home']['planner'],
    max_velocity_scaling_factor=0.5, 
    max_acceleration_scaling_factor=0.5,
)

w2 = CartWaypoint(
    waypoint_name="w2",
    position=waypoint_configs['观测点1']['pose'][:3],
    orientation=waypoint_configs['观测点1']['pose'][3:],
    group=waypoint_configs['观测点1']['group'],
    frame_id=waypoint_configs['观测点1']['frame_id'],
    ik_frame=waypoint_configs['观测点1']['ik_frame'],
    planner=waypoint_configs['观测点1']['planner'],
    max_velocity_scaling_factor=0.5,
    max_acceleration_scaling_factor=0.5,
)

waypoint_names = ['home', '观测点1', '观测点2', '观测点3', '观测点4', '观测点5', '放到框内-准备', '放到框内-就绪', '放到框内-撤退'] 
waypoints = []
for waypoint_name in waypoint_names:
    waypoints.append(get_waypoint_from_config(waypoint_name, waypoint_configs[waypoint_name]))

sequence = get_plan_and_execute_waypoints_sequence(waypoints)

print(sequence)