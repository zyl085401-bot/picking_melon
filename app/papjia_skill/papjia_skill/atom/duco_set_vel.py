
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class DucoSetVel(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, vel=None, wait_for_server_timeout=30, result_timeout=30, success=None):
        self.action_info = {
            'service_name': service_name,
            'vel': vel,
            'wait_for_server_timeout': wait_for_server_timeout,
            'result_timeout': result_timeout,
            'success': success,
            "ID": "DucoSetVel"
        }
        # 构造action node
        super().__init__(self.action_info)
