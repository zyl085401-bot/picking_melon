
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class CompareJsonInfo(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, json_a=None, json_b=None, keys=None, status=None, result=None):
        self.action_info = {
            'service_name': service_name,
            'json_a': json_a,
            'json_b': json_b,
            'keys': keys,
            'status': status,
            'result': result,
            "ID": "CompareJsonInfo"
        }
        # 构造action node
        super().__init__(self.action_info)
