
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class GetPoseStampedMsg(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, frame_id=None, position=None, quaternion=None, pose_stamped=None):
        self.action_info = {
            'frame_id': frame_id,
            'position': position,
            'quaternion': quaternion,
            'pose_stamped': pose_stamped,
            "ID": "GetPoseStampedMsg"
        }
        # 构造action node
        super().__init__(self.action_info)
