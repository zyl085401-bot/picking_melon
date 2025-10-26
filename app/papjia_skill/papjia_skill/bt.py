import xml.etree.ElementTree as ET
from xml.dom import minidom
import re 

class BTNode(object):
    def __init__(self, tag=''):
        self._inputs = {}
        self._outputs = {}
        self._tag = tag
        self._childs = []

    @property
    def inputs(self):
        return self._inputs
    
    @property
    def outputs(self):
        return self._outputs
    
    @property
    def tag(self):
        return self._tag
    
    def add_child(self, node):
        self._childs.append(node)
    
    def set_inputs(self, key, value):
        self.inputs[key] = value
    
    def set_outputs(self, key, value):
        self.outputs[key] = value
    
    def get_outputs(self, key):
        if key not in self._outputs:
            raise KeyError("Output key '{}' does not exist.".format(key))
        return self._outputs[key]
    
    def to_xml(self) -> ET.Element:
        params = {**self._inputs, **self._outputs}
        ele = ET.Element(self._tag, params)
        for child in self._childs:
            ele.append(child.to_xml())
        return ele
    
    def __repr__(self):
        parsed = minidom.parseString(ET.tostring(self.to_xml(), encoding='utf-8'))
        return parsed.toprettyxml(indent="    ")  # 使用4个空格缩进
    
    def to_str(self):
        return self.__repr__()


class BehaviorRoot(BTNode):
    def __init__(self):
        super().__init__('root')
        self.set_inputs('BTCPP_format', '4')


class BehaviorTree(BTNode):
    def __init__(self, tree_name):
        super().__init__('BehaviorTree')
        self.set_inputs('ID', tree_name)


class Sequence(BTNode):
    def __init__(self, sequence_name):
        super().__init__('Sequence')
        self.set_inputs('name', sequence_name)


class SubTree(BTNode):
    def __init__(self, subtree_name):
        super().__init__('SubTree')
        self.set_inputs('ID', subtree_name)


class InitMTCTask(BTNode):
    def __init__(self, task_name):
        super().__init__('InitMTCTask')
        self.set_inputs('task_name', task_name)
        self.set_outputs('task', '{task}')


class CreatePlanner(BTNode):
    def __init__(self, planner_type, max_velocity_scaling_factor, max_acceleration_scaling_factor):
        super().__init__('CreatePlanner')
        self.set_inputs('planner_type', planner_type)
        self.set_inputs('max_velocity_scaling_factor', str(max_velocity_scaling_factor))
        self.set_inputs('max_acceleration_scaling_factor', str(max_acceleration_scaling_factor))
        self.set_outputs('planner', '{planner}')


class SetupCurrentState(BTNode):
    def __init__(self):
        super().__init__('SetupCurrentState')
        self.set_inputs('task', '{task}')


class GetQuatFromXYZ(BTNode):
    def __init__(self, x, y, z):
        super().__init__('GetQuatFromXYZ')
        self.set_inputs('x', str(x))
        self.set_inputs('y', str(y))
        self.set_inputs('z', str(z))
        self.set_outputs('quaternion', '{quat}')


class GetJointStateConfig(BTNode):
    def __init__(self, service_name, state_name):
        super().__init__('GetJointStateConfig')
        self.set_inputs('service_name', service_name)
        self.set_inputs('state_name', state_name)
        self.set_outputs('joint_state', '{joint_state}')


class SetupMoveToJointState(BTNode):
    def __init__(self, task, planner, planning_group, stage_name, joint_state):
        super().__init__('SetupMoveToJointState')
        self.set_inputs('task', task)
        self.set_inputs('planner', planner)
        self.set_inputs('planning_group', planning_group)
        self.set_inputs('stage_name', stage_name)
        self.set_inputs('joint_state', joint_state)


class GetPoseStampedMsg(BTNode):
    def __init__(self, frame_id, pose_name, position=None, quaternion=None):
        super().__init__('GetPoseStampedMsg')
        self.set_inputs('frame_id', frame_id)
        self.set_outputs('pose_stamped', '{' + pose_name + '}')
        
        # TODO 检查输入的正确性
        if position is not None:
            if type(position) is list:
                self.set_inputs('position', ','.join([str(i) for i in position]))
            else:
                self.set_inputs('position', str(position))
        
        if quaternion is not None:
            if type(quaternion) is list:
                self.set_inputs('quaternion', ','.join([str(i) for i in quaternion]))
            else:
                self.set_inputs('quaternion', str(quaternion))
        

class SetupMoveToPose(BTNode):
    def __init__(self):
        super().__init__('SetupMoveToPose')


class PlanMTCTask(BTNode):
    def __init__(self, task):
        super().__init__('PlanMTCTask')
        self.set_inputs('task', task)
        
        
class ExecuteMTCTask(BTNode):
    def __init__(self, task):
        super().__init__('ExecuteMTCTask')
        self.set_inputs('task', task)


if __name__ == "__main__":
    action_InitMTCTask = InitMTCTask('GoToPick')
    print(action_InitMTCTask)
    action_CreatePlanner = CreatePlanner('lin', 0.1, 0.1)
    print(action_CreatePlanner)
    action_SetupCurrentState = SetupCurrentState()
    print(action_SetupCurrentState)
    
    action_GetQuatFromXYZ = GetQuatFromXYZ(0.1, 0.1, 0.1)
    print(action_GetQuatFromXYZ)
    
    action_GetPoseStampedMsg = GetPoseStampedMsg('base_link', 'pick_pose')
    action_GetPoseStampedMsg.set_inputs('position', '{pos}')
    action_GetPoseStampedMsg.set_inputs('quaternion', '{quat}')
    print(action_GetPoseStampedMsg)
    
    action_GetPoseStampedMsg = GetPoseStampedMsg('base_link', 'pick_pose', [0.25, -0.34, 0], '{quat}')
    print(action_GetPoseStampedMsg)
    
    action_SetupMoveToPose = SetupMoveToPose()
    action_SetupMoveToPose.set_inputs('task', '{task}')
    action_SetupMoveToPose.set_inputs('planner', '{planner}')
    action_SetupMoveToPose.set_inputs('planning_group', 'arm')
    action_SetupMoveToPose.set_inputs('stage_name', 'move_to_pose')
    action_SetupMoveToPose.set_inputs('ik_frame', 'eef')
    action_SetupMoveToPose.set_inputs('pose', '{pose}')
    print(action_SetupMoveToPose)
    
    action_PlanMTCTask = PlanMTCTask()
    action_PlanMTCTask.set_inputs('task', '{task}')
    print(action_PlanMTCTask)
    
    action_ExecuteMTCTask = ExecuteMTCTask()
    action_ExecuteMTCTask.set_inputs('task', '{task}')
    print(action_ExecuteMTCTask)
    
    sequence = Sequence()
    sequence.add_child(action_InitMTCTask)
    sequence.add_child(action_CreatePlanner)
    sequence.add_child(action_SetupCurrentState)
    sequence.add_child(action_GetQuatFromXYZ)
    sequence.add_child(action_GetPoseStampedMsg)
    sequence.add_child(action_SetupMoveToPose)
    sequence.add_child(action_PlanMTCTask)
    sequence.add_child(action_ExecuteMTCTask)
    print(sequence)
    print("---")
    
    tree = BehaviorTree("TestTreeMove")
    tree.add_child(sequence)
    print(tree)
    print("---")
    
    root = BehaviorRoot()
    root.add_child(tree)
    print(root)