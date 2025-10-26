
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetGraspWaypoints(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, filtered_object=None, pick_roll=None, pick_pitch=None, pick_yaw=None, group=None, frame_id=None, ik_frame=None, planner=None, max_velocity_scaling_factor=None, max_acceleration_scaling_factor=None, pre_grasp_waypoint=None, grasp_waypoint=None):
        self.action_info = {
            'filtered_object': filtered_object,
            'pick_roll': pick_roll,
            'pick_pitch': pick_pitch,
            'pick_yaw': pick_yaw,
            'group': group,
            'frame_id': frame_id,
            'ik_frame': ik_frame,
            'planner': planner,
            'max_velocity_scaling_factor': max_velocity_scaling_factor,
            'max_acceleration_scaling_factor': max_acceleration_scaling_factor,
            'pre_grasp_waypoint': pre_grasp_waypoint,
            'grasp_waypoint': grasp_waypoint,
            "ID": "GetGraspWaypoints"
        }
        # 构造action node
        super().__init__(self.action_info)
