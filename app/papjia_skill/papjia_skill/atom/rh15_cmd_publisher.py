
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class Rh15CmdPublisher(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, config_path=None, task_id=None, point_id=None, wait_time=None, success=None):
        self.action_info = {
            'config_path': config_path,
            'task_id': task_id,
            'point_id': point_id,
            'wait_time': wait_time,
            'success': success,
            "ID": "Rh15CmdPublisher"
        }
        # 构造action node
        super().__init__(self.action_info)
