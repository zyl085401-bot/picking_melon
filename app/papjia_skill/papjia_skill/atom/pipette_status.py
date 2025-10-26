
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class PipetteStatus(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, wait_for_server_timeout=30, result_timeout=30, tip_status=None, running_status=None, liquid_volume=None, activate_status=None):
        self.action_info = {
            'service_name': service_name,
            'wait_for_server_timeout': wait_for_server_timeout,
            'result_timeout': result_timeout,
            'tip_status': tip_status,
            'running_status': running_status,
            'liquid_volume': liquid_volume,
            'activate_status': activate_status,
            "ID": "PipetteStatus"
        }
        # 构造action node
        super().__init__(self.action_info)
