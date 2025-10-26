
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetJointWaypoint(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, waypoint_name=None, joint_names=None, joint_values=None, group=None, planner=None, max_velocity_scaling_factor=None, max_acceleration_scaling_factor=None, waypoint=None):
        self.action_info = {
            'waypoint_name': waypoint_name,
            'joint_names': joint_names,
            'joint_values': joint_values,
            'group': group,
            'planner': planner,
            'max_velocity_scaling_factor': max_velocity_scaling_factor,
            'max_acceleration_scaling_factor': max_acceleration_scaling_factor,
            'waypoint': waypoint,
            "ID": "GetJointWaypoint"
        }
        # 构造action node
        super().__init__(self.action_info)
