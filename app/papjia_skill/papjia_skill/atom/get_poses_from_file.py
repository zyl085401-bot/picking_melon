
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetPosesFromFile(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, filename=None, frame_id=None, poses=None):
        self.action_info = {
            'filename': filename,
            'frame_id': frame_id,
            'poses': poses,
            "ID": "GetPosesFromFile"
        }
        # 构造action node
        super().__init__(self.action_info)
