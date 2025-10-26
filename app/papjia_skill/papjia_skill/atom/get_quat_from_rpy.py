
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetQuatFromRPY(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, roll=None, pitch=None, yaw=None, quaternion=None):
        self.action_info = {
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw,
            'quaternion': quaternion,
            "ID": "GetQuatFromRPY"
        }
        # 构造action node
        super().__init__(self.action_info)
