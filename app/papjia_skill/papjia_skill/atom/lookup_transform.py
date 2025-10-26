
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class LookupTransform(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, parent_frame=None, child_frame=None, pose=None):
        self.action_info = {
            'parent_frame': parent_frame,
            'child_frame': child_frame,
            'pose': pose,
            "ID": "LookupTransform"
        }
        # 构造action node
        super().__init__(self.action_info)
