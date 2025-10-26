
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class DeleteDBObject(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, collection_name=None, query=None, result=None):
        self.action_info = {
            'service_name': service_name,
            'collection_name': collection_name,
            'query': query,
            'result': result,
            "ID": "DeleteDBObject"
        }
        # 构造action node
        super().__init__(self.action_info)
