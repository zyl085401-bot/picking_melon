
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class MaskDetect(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, image=None, max_num=None, min_score=None, allowed_roi=None, allowed_categories=None, objs_num=None, with_mask=None, mask=None, objects=None):
        self.action_info = {
            'service_name': service_name,
            'image': image,
            'max_num': max_num,
            'min_score': min_score,
            'allowed_roi': allowed_roi,
            'allowed_categories': allowed_categories,
            'objs_num': objs_num,
            'with_mask': with_mask,
            'mask': mask,
            'objects': objects,
            "ID": "MaskDetect"
        }
        # 构造action node
        super().__init__(self.action_info)
