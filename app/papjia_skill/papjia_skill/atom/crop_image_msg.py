
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class CropImageMsg(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, image_input=None, x1=None, y1=None, x2=None, y2=None, image_output=None):
        self.action_info = {
            'image_input': image_input,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'image_output': image_output,
            "ID": "CropImageMsg"
        }
        # 构造action node
        super().__init__(self.action_info)
