
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class StorageDishPickPlace(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, action_name=None, method=None, action=None, goal_result_timeout=120, wait_for_server_timeout=30, goal_response_timeout=5, cancel_response_timeout=5, success=None, message=None):
        self.action_info = {
            'action_name': action_name,
            'method': method,
            'action': action,
            'goal_result_timeout': goal_result_timeout,
            'wait_for_server_timeout': wait_for_server_timeout,
            'goal_response_timeout': goal_response_timeout,
            'cancel_response_timeout': cancel_response_timeout,
            'success': success,
            'message': message,
            "ID": "StorageDishPickPlace"
        }
        # 构造action node
        super().__init__(self.action_info)
