
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class CompareStringEqual(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, str1=None, str2=None):
        self.action_info = {
            'str1': str1,
            'str2': str2,
            "ID": "CompareStringEqual"
        }
        # 构造action node
        super().__init__(self.action_info)
