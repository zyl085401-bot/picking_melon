from papjia_skill.atom.control_gripper import ControlGripper
from papjia_skill.atom.control_shears import ControlShears
from papjia_skill.atom.object_detect import ObjectDetect
from papjia_skill.atom.json_to_object import JsonToObject
from papjia_skill.atom.filter_object import FilterObject
from papjia_skill.atom.get_grasp_waypoints import GetGraspWaypoints
from papjia_skill.atom.add_waypoint_to_vector import AddWaypointToVector
from papjia_skill.atom.plan_trajectory_for_waypoints import PlanTrajectoryForWaypoints
from papjia_skill.atom.execute_trajectory import ExecuteTrajectory
from papjia_skill.atom.straight_move import StraightMove
from papjia_skill.btree import Sequence
from papjia_skill.action_models import ActionModels

ActionModels("/workspace/src/papjia_melon/papjia_melon_config/config/action_model.yaml")

service_control_gripper = "/papjia/melon/device/gripper/control"
service_control_shears = "/papjia/melon/device/shears/control"
service_object_detect = "/papjia/melon/device/object/detect"
service_straight_move = "/papjia/move/straight_move"

def open_gripper():
    return ControlGripper(service_control_gripper, "open")

def close_gripper():
    return ControlGripper(service_control_gripper, "close")

def open_shears():
    return ControlShears(service_control_shears, "open")

def close_shears():
    return ControlShears(service_control_shears, "close")

def detect_objects(max_num=10, min_score=0.5):
    return ObjectDetect(service_object_detect, max_num, min_score)

def straight_move(distance=0.0, speed=0.0, use_integral=False):
    return StraightMove(service_straight_move, distance, speed, use_integral)


def move_to_pose(
    planner="lin",
    max_velocity_scaling_factor=0.5,
    max_acceleration_scaling_factor=0.5,
    pick_roll=0.0,
    pick_pitch=0.0,
    pick_yaw=0.0,
    group="arm",
    ik_frame="gripper",
    frame_id="base_link",
    filtered_object="filtered_object",
):
    # to_do 【往上、往前补偿】
    get_grasp_waypoints = GetGraspWaypoints(
        filtered_object=f"{{{filtered_object}}}",
        pick_roll=pick_roll,
        pick_pitch=pick_pitch,
        pick_yaw=pick_yaw,
        group=group,
        frame_id=frame_id,
        ik_frame=ik_frame,
        planner=planner,
        max_velocity_scaling_factor=max_velocity_scaling_factor,
        max_acceleration_scaling_factor=max_acceleration_scaling_factor,
        pre_grasp_waypoint="{pre_grasp_waypoint}",
        grasp_waypoint="{grasp_waypoint}",
    )

    add_pre_grasp_waypoint = AddWaypointToVector(waypoint_in="{pre_grasp_waypoint}", vector_out="{waypoints}")
    add_grasp_waypoint = AddWaypointToVector(
        waypoint_in="{grasp_waypoint}", vector_in="{waypoints}", vector_out="{waypoints}"
    )
    plan_trajectory_for_waypoints = PlanTrajectoryForWaypoints(waypoints="{waypoints}", trajectories="{trajectories}")
    execute_trajectory = ExecuteTrajectory(trajectories="{trajectories}")

    sequence = Sequence("move_to_pose")
    sequence.add_child(get_grasp_waypoints)
    sequence.add_child(add_pre_grasp_waypoint)
    sequence.add_child(add_grasp_waypoint)
    sequence.add_child(plan_trajectory_for_waypoints)
    sequence.add_child(execute_trajectory)
    return sequence


def detect_and_grasp_object(
        max_num=10, 
        min_score=0.5, 
        planner="lin", 
        max_velocity_scaling_factor=0.5, 
        max_acceleration_scaling_factor=0.5,
        pick_roll=0.0, 
        pick_pitch=0.0, 
        pick_yaw=0.0,
        group="arm",
        ik_frame="arm_gripper", 
        frame_id="arm_base_link",
    ):
    detect_objects = ObjectDetect(service_object_detect, max_num, min_score, objects="{objects}")
    filter_objects = FilterObject(objects="{objects}", filtered_object="{filtered_object}")
    get_grasp_waypoints = GetGraspWaypoints(
        filtered_object="{filtered_object}", 
        pick_roll=pick_roll,
        pick_pitch=pick_pitch,
        pick_yaw=pick_yaw,
        group=group,
        frame_id=frame_id,
        ik_frame=ik_frame,
        planner=planner,
        max_velocity_scaling_factor=max_velocity_scaling_factor,
        max_acceleration_scaling_factor=max_acceleration_scaling_factor,
        pre_grasp_waypoint="{pre_grasp_waypoint}", 
        grasp_waypoint="{grasp_waypoint}"
    )


    add_pre_grasp_waypoint = AddWaypointToVector(
        waypoint_in="{pre_grasp_waypoint}",
        vector_out="{waypoints}"
    )
    add_grasp_waypoint = AddWaypointToVector(
        waypoint_in="{grasp_waypoint}",
        vector_in="{waypoints}",
        vector_out="{waypoints}"
    )
    plan_trajectory_for_waypoints = PlanTrajectoryForWaypoints(
        waypoints="{waypoints}",
        trajectories="{trajectories}"
    )
    execute_trajectory = ExecuteTrajectory(
        trajectories="{trajectories}"
    )

    sequence = Sequence("detect_objects_and_filter")
    sequence.add_child(detect_objects)
    sequence.add_child(filter_objects)
    sequence.add_child(get_grasp_waypoints)
    sequence.add_child(add_pre_grasp_waypoint)
    sequence.add_child(add_grasp_waypoint)
    sequence.add_child(plan_trajectory_for_waypoints)
    sequence.add_child(execute_trajectory)
    return sequence
