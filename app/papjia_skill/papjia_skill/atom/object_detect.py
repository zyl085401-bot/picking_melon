
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class ObjectDetect(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, max_num=None, min_score=None, objects=None):
        self.action_info = {
            'service_name': service_name,
            'max_num': max_num,
            'min_score': min_score,
            'objects': objects,
            "ID": "ObjectDetect"
        }
        # 构造action node
        super().__init__(self.action_info)
