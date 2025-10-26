
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetCartWaypoint(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, waypoint_name=None, position=None, orientation=None, group=None, frame_id=None, ik_frame=None, planner=None, max_velocity_scaling_factor=None, max_acceleration_scaling_factor=None, waypoint=None):
        self.action_info = {
            'waypoint_name': waypoint_name,
            'position': position,
            'orientation': orientation,
            'group': group,
            'frame_id': frame_id,
            'ik_frame': ik_frame,
            'planner': planner,
            'max_velocity_scaling_factor': max_velocity_scaling_factor,
            'max_acceleration_scaling_factor': max_acceleration_scaling_factor,
            'waypoint': waypoint,
            "ID": "GetCartWaypoint"
        }
        # 构造action node
        super().__init__(self.action_info)
