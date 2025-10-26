from papjia_skill.bt import *
import xml.etree.ElementTree

from typing import List, Optional


class Waypoint:
    def __init__(self, 
                 waypoint_type: str,
                 group: str, 
                 frame_id: str,
                 ik_frame: str,
                 planner: str, 
                 max_velocity_scaling_factor: float, 
                 max_acceleration_scaling_factor: float, 
                 stage_name: str,):
        self.waypoint_type = waypoint_type
        self.group = group
        self.frame_id = frame_id
        self.ik_frame = ik_frame
        self.planner = planner
        self.max_velocity_scaling_factor = max_velocity_scaling_factor
        self.max_acceleration_scaling_factor = max_acceleration_scaling_factor
        self.stage_name = stage_name
    
    def create_planner_node(self, sequence: Sequence) -> CreatePlanner:
        action_CreatePlanner = CreatePlanner(self.planner, self.max_velocity_scaling_factor, self.max_acceleration_scaling_factor)
        action_CreatePlanner.set_outputs('planner', '{' + self.stage_name + '_planner}')
        sequence.add_child(action_CreatePlanner)
        return action_CreatePlanner
    
    def to_bt(self, sequence : Sequence, action_InitMTCTask : InitMTCTask):
        raise NotImplementedError("to_bt is not implemented for this class")


class JointWaypoint(Waypoint):
    def __init__(self, 
                 joint_state_name: str, 
                 **kwargs):
        super().__init__(waypoint_type="joint", frame_id=None, ik_frame=None, **kwargs)
        self.joint_state_name = joint_state_name
    
    def to_bt(self, sequence : Sequence, action_InitMTCTask : InitMTCTask):
        # 生成规划器
        action_CreatePlanner = self.create_planner_node(sequence)
        
        # 获取关节状态配置
        action_GetJointStateConfig = GetJointStateConfig('/handle_joint_state_config', self.joint_state_name)
        action_GetJointStateConfig.set_outputs('joint_state', '{' + self.joint_state_name + '}')
        sequence.add_child(action_GetJointStateConfig)
        
        # 设置移动到关节状态
        action_SetupMoveToJointState = SetupMoveToJointState(
            action_InitMTCTask.get_outputs('task'),
            action_CreatePlanner.get_outputs('planner'),
            self.group,
            self.stage_name,
            action_GetJointStateConfig.get_outputs('joint_state')
        )
        sequence.add_child(action_SetupMoveToJointState)


class CartWaypoint(Waypoint):
    def __init__(self, 
                 position: List[float], 
                 orientation: List[float], 
                 **kwargs):
        super().__init__(waypoint_type="cart", **kwargs)
        self.position = position
        self.orientation = orientation
    
    def to_bt(self, sequence : Sequence, action_InitMTCTask : InitMTCTask):
        # 生成规划器
        action_CreatePlanner = self.create_planner_node(sequence)
        
        # 生成pose
        pose_name = self.stage_name + '_pose'
        action_GetPoseStampedMsg = GetPoseStampedMsg(self.frame_id, pose_name, self.position, self.orientation)
        sequence.add_child(action_GetPoseStampedMsg)
        
        # 设置移动到姿态
        action_SetupMoveToPose = SetupMoveToPose()
        
        action_SetupMoveToPose.set_inputs('task', action_InitMTCTask.get_outputs('task'),)
        action_SetupMoveToPose.set_inputs('planner', action_CreatePlanner.get_outputs('planner'),)
        action_SetupMoveToPose.set_inputs('planning_group', self.group,)
        action_SetupMoveToPose.set_inputs('stage_name', self.stage_name,)
        action_SetupMoveToPose.set_inputs('ik_frame', self.ik_frame)
        action_SetupMoveToPose.set_inputs('pose', action_GetPoseStampedMsg.get_outputs('pose_stamped'))
        sequence.add_child(action_SetupMoveToPose)


def arm_move_primitive_bt(primitive_name, waypoints, vel=1.0, simulate=True):
    sequence = Sequence(primitive_name)
    
    action_InitMTCTask = InitMTCTask(primitive_name)
    sequence.add_child(action_InitMTCTask)
    
    action_SetupCurrentState = SetupCurrentState()
    sequence.add_child(action_SetupCurrentState)
    
    for waypoint in waypoints:
        waypoint.to_bt(sequence, action_InitMTCTask)
        
    action_PlanMTCTask = PlanMTCTask(action_InitMTCTask.get_outputs('task'))
    sequence.add_child(action_PlanMTCTask)
    
    action_ExecuteMTCTask = ExecuteMTCTask(action_InitMTCTask.get_outputs('task'))
    action_ExecuteMTCTask.set_inputs('vel', str(vel))
    action_ExecuteMTCTask.set_inputs('simulate', str(simulate))
    sequence.add_child(action_ExecuteMTCTask)
    return sequence