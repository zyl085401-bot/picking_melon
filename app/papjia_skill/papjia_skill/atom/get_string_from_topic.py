
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetStringFromTopic(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, topic_name=None, timeout=None, hz=None, result=None):
        self.action_info = {
            'topic_name': topic_name,
            'timeout': timeout,
            'hz': hz,
            'result': result,
            "ID": "GetStringFromTopic"
        }
        # 构造action node
        super().__init__(self.action_info)
