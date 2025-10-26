
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GripperCommand(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, action_name=None, goal_position=None, force=None, velocity=None, goal_result_timeout=120, wait_for_server_timeout=30, goal_response_timeout=5, cancel_response_timeout=5, result_position=None, stalled=None, reached_goal=None):
        self.action_info = {
            'action_name': action_name,
            'goal_position': goal_position,
            'force': force,
            'velocity': velocity,
            'goal_result_timeout': goal_result_timeout,
            'wait_for_server_timeout': wait_for_server_timeout,
            'goal_response_timeout': goal_response_timeout,
            'cancel_response_timeout': cancel_response_timeout,
            'result_position': result_position,
            'stalled': stalled,
            'reached_goal': reached_goal,
            "ID": "GripperCommand"
        }
        # 构造action node
        super().__init__(self.action_info)
