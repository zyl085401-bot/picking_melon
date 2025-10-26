
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class PumpOut(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, action_name=None, volume=None, goal_result_timeout=120, wait_for_server_timeout=30, goal_response_timeout=5, cancel_response_timeout=5, pumped_volume=None):
        self.action_info = {
            'action_name': action_name,
            'volume': volume,
            'goal_result_timeout': goal_result_timeout,
            'wait_for_server_timeout': wait_for_server_timeout,
            'goal_response_timeout': goal_response_timeout,
            'cancel_response_timeout': cancel_response_timeout,
            'pumped_volume': pumped_volume,
            "ID": "PumpOut"
        }
        # 构造action node
        super().__init__(self.action_info)
