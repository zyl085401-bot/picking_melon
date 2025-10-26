
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class SetVector3D(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, x=None, y=None, z=None, vector3d=None):
        self.action_info = {
            'x': x,
            'y': y,
            'z': z,
            'vector3d': vector3d,
            "ID": "SetVector3D"
        }
        # 构造action node
        super().__init__(self.action_info)
