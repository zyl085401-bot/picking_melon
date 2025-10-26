
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class InsertDBObject(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, collection_name=None, records=None, allowed_update=None, result=None):
        self.action_info = {
            'service_name': service_name,
            'collection_name': collection_name,
            'records': records,
            'allowed_update': allowed_update,
            'result': result,
            "ID": "InsertDBObject"
        }
        # 构造action node
        super().__init__(self.action_info)
