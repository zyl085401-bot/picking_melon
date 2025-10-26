import uuid
from typing import List

from papjia_skill.atom.get_joint_waypoint import GetJointWaypoint
from papjia_skill.atom.get_cart_waypoint import GetCartWaypoint
from papjia_skill.atom.add_waypoint_to_vector import AddWaypointToVector
from papjia_skill.atom.plan_trajectory_for_waypoints import PlanTrajectoryForWaypoints
from papjia_skill.atom.execute_trajectory import ExecuteTrajectory

from papjia_skill.btree import Sequence, SubTree, BehaviorTree


class Waypoint:
    def __init__(self, 
                 waypoint_type: str,
                 waypoint_name: str,
                 group: str, 
                 planner: str, 
                 max_velocity_scaling_factor: float, 
                 max_acceleration_scaling_factor: float):
        self.waypoint_type = waypoint_type
        self.waypoint_name = waypoint_name
        self.group = group
        self.planner = planner
        self.max_velocity_scaling_factor = max_velocity_scaling_factor
        self.max_acceleration_scaling_factor = max_acceleration_scaling_factor
        
        self.joint_names = []
        self.joint_values = []

        self.frame_id = None
        self.ik_frame = None
        self.position = []
        self.orientation = []
    
    def convert_joint_names_to_str(self):
        return ",".join(self.joint_names)

    def convert_joint_values_to_str(self):
        return ";".join(str(value) for value in self.joint_values)
    
    def convert_position_to_str(self):
        return ",".join(str(value) for value in self.position)

    def convert_orientation_to_str(self):
        return ",".join(str(value) for value in self.orientation)

class JointWaypoint(Waypoint):
    def __init__(self, 
                 waypoint_name: str,
                 joint_names: List[str],
                 joint_values: List[float],
                 group: str,
                 planner: str,
                 max_velocity_scaling_factor: float,
                 max_acceleration_scaling_factor: float):
        super().__init__(waypoint_type="joint", 
                         waypoint_name=waypoint_name, 
                         group=group, 
                         planner=planner, 
                         max_velocity_scaling_factor=max_velocity_scaling_factor, 
                         max_acceleration_scaling_factor=max_acceleration_scaling_factor)
        assert len(joint_names) == len(joint_values)
        self.joint_names = joint_names
        self.joint_values = joint_values


class CartWaypoint(Waypoint):
    def __init__(self, 
                 waypoint_name: str,
                 position: List[float],
                 orientation: List[float],
                 group: str,
                 frame_id: str,
                 ik_frame: str,
                 planner: str,
                 max_velocity_scaling_factor: float,
                 max_acceleration_scaling_factor: float):
        super().__init__(waypoint_type="cart",
                         waypoint_name=waypoint_name,
                         group=group,
                         planner=planner,
                         max_velocity_scaling_factor=max_velocity_scaling_factor,
                         max_acceleration_scaling_factor=max_acceleration_scaling_factor)
        assert len(position) == 3
        assert len(orientation) == 4
        self.frame_id = frame_id
        self.ik_frame = ik_frame
        self.position = position
        self.orientation = orientation

def get_waypoint_from_config(waypoint_name: str, waypoint_config: dict, 
                                   max_velocity_scaling_factor=0.5, 
                                   max_acceleration_scaling_factor=0.5):
    print(waypoint_config)
    if waypoint_config['type'] == 'joint':
        return JointWaypoint(
            waypoint_name=waypoint_name,
            joint_names=waypoint_config['joint_names'],
            joint_values=waypoint_config['joint_values'],
            group=waypoint_config['group'],
            planner=waypoint_config['planner'],
            max_velocity_scaling_factor=max_velocity_scaling_factor,
            max_acceleration_scaling_factor=max_acceleration_scaling_factor
        )
    elif waypoint_config['type'] == 'cartesian':
        return CartWaypoint(
            waypoint_name=waypoint_name,
            position=waypoint_config['pose'][:3],
            orientation=waypoint_config['pose'][3:],
            group=waypoint_config['group'],
            frame_id=waypoint_config['frame_id'],
            ik_frame=waypoint_config['ik_frame'],
            planner=waypoint_config['planner'],
            max_velocity_scaling_factor=max_velocity_scaling_factor,
            max_acceleration_scaling_factor=max_acceleration_scaling_factor
        )
    else:
        print(waypoint_config)
        raise ValueError(f"Invalid waypoint type: {waypoint_config['type']}")

def get_plan_and_execute_waypoints_sequence(waypoints: List[Waypoint]):
    random_suffix = str(uuid.uuid4())
    sequence_name = 'plan_and_execute_waypoints_' + random_suffix
    sequence = Sequence(sequence_name)

    for i, waypoint in enumerate(waypoints):
        assert waypoint.waypoint_type in ['joint', 'cart']
        if waypoint.waypoint_type == 'joint':
            joint_waypoint = GetJointWaypoint(
                waypoint_name=waypoint.waypoint_name,
                joint_names=waypoint.convert_joint_names_to_str(),
                joint_values=waypoint.convert_joint_values_to_str(),
                group=waypoint.group,
                planner=waypoint.planner,
                max_velocity_scaling_factor=waypoint.max_velocity_scaling_factor,
                max_acceleration_scaling_factor=waypoint.max_acceleration_scaling_factor,
                waypoint="{waypoint_" + random_suffix + "}"
            )
            sequence.add_child(joint_waypoint)
        elif waypoint.waypoint_type == 'cart':
            cart_waypoint = GetCartWaypoint(
                waypoint_name=waypoint.waypoint_name,
                position=waypoint.convert_position_to_str(),
                orientation=waypoint.convert_orientation_to_str(),
                group=waypoint.group,
                frame_id=waypoint.frame_id,
                ik_frame=waypoint.ik_frame,
                planner=waypoint.planner,
                max_velocity_scaling_factor=waypoint.max_velocity_scaling_factor,
                max_acceleration_scaling_factor=waypoint.max_acceleration_scaling_factor,
                waypoint="{waypoint_" + random_suffix + "}"
            )
            sequence.add_child(cart_waypoint)
        
        if i == 0:
            add_waypoint_to_vector = AddWaypointToVector(
                waypoint_in="{waypoint_" + random_suffix + "}",
                vector_out="{waypoints_" + random_suffix + "}"
            )
        else:
            add_waypoint_to_vector = AddWaypointToVector(
                waypoint_in="{waypoint_" + random_suffix + "}",
                vector_in="{waypoints_" + random_suffix + "}",
                vector_out="{waypoints_" + random_suffix + "}"
            )
        sequence.add_child(add_waypoint_to_vector)
    
    plan_trajectory_for_waypoints = PlanTrajectoryForWaypoints(
        waypoints="{waypoints_" + random_suffix + "}",
        trajectories="{trajectories_" + random_suffix + "}"
    )
    sequence.add_child(plan_trajectory_for_waypoints)

    execute_trajectory = ExecuteTrajectory(
        trajectories="{trajectories_" + random_suffix + "}"
    )
    sequence.add_child(execute_trajectory)

    return sequence