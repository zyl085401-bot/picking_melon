
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class ImageSaveToFile(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, image=None, file_name=None):
        self.action_info = {
            'image': image,
            'file_name': file_name,
            "ID": "ImageSaveToFile"
        }
        # 构造action node
        super().__init__(self.action_info)
