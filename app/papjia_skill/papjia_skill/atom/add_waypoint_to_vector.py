
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class AddWaypointToVector(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, waypoint_in=None, vector_in=None, vector_out=None):
        self.action_info = {
            'waypoint_in': waypoint_in,
            'vector_in': vector_in,
            'vector_out': vector_out,
            "ID": "AddWaypointToVector"
        }
        # 构造action node
        super().__init__(self.action_info)
