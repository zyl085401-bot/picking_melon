
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class JsonToObject(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, json_object=None, result_object=None):
        self.action_info = {
            'json_object': json_object,
            'result_object': result_object,
            "ID": "JsonToObject"
        }
        # 构造action node
        super().__init__(self.action_info)
