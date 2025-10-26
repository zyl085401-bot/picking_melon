
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class StraightMove(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, service_name=None, result_timeout=30, distance=None, speed=None, use_integral=None, follow_line=None, line_frame=None, line_start=None, line_end=None, success=None):
        self.action_info = {
            'service_name': service_name,
            'result_timeout': result_timeout,
            'distance': distance,
            'speed': speed,
            'use_integral': use_integral,
            'follow_line': follow_line,
            'line_frame': line_frame,
            'line_start': line_start,
            'line_end': line_end,
            'success': success,
            "ID": "StraightMove"
        }
        # 构造action node
        super().__init__(self.action_info)
