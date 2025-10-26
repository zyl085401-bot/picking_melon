
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class FetchImage(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, ip=None, device_name=None, success=None, image=None):
        self.action_info = {
            'service_name': service_name,
            'ip': ip,
            'device_name': device_name,
            'success': success,
            'image': image,
            "ID": "FetchImage"
        }
        # 构造action node
        super().__init__(self.action_info)
