
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class PlanTrajectoryForWaypoints(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, waypoints=None, trajectories=None):
        self.action_info = {
            'waypoints': waypoints,
            'trajectories': trajectories,
            "ID": "PlanTrajectoryForWaypoints"
        }
        # 构造action node
        super().__init__(self.action_info)
