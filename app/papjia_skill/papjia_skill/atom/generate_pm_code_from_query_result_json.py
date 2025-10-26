
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GeneratePMCodeFromQueryResultJson(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, query_result=None, task_name=None, pm_code=None):
        self.action_info = {
            'query_result': query_result,
            'task_name': task_name,
            'pm_code': pm_code,
            "ID": "GeneratePMCodeFromQueryResultJson"
        }
        # 构造action node
        super().__init__(self.action_info)
