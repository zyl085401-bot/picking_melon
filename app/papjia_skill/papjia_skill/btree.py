import xml.etree.ElementTree as ET
from xml.dom import minidom
from papjia_skill.action_models import ActionModels
from copy import deepcopy


class BTNode(object):
    def __init__(self, tag=""):
        self._inputs = {}
        self._outputs = {}
        self._tag = tag
        self._childs = []

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def tag(self):
        return self._tag

    def add_child(self, node):
        self._childs.append(node)

    def set_inputs(self, key, value):
        self.inputs[key] = value

    def set_outputs(self, key, value):
        self.outputs[key] = value

    def get_outputs(self, key):
        if key not in self._outputs:
            raise KeyError("Output key '{}' does not exist.".format(key))
        return self._outputs[key]

    def to_xml(self) -> ET.Element:
        params = {**self._inputs, **self._outputs}
        ele = ET.Element(self._tag, params)
        for child in self._childs:
            ele.append(child.to_xml())
        return ele

    def __repr__(self):
        parsed = minidom.parseString(ET.tostring(self.to_xml(), encoding="utf-8"))
        return parsed.toprettyxml(indent="    ")  # 使用4个空格缩进

    def to_str(self):
        return self.__repr__()


class BehaviorRoot(BTNode):
    def __init__(self):
        super().__init__("root")
        self.set_inputs("BTCPP_format", "4")


class BehaviorTree(BTNode):
    def __init__(self, tree_name):
        super().__init__("BehaviorTree")
        self.set_inputs("ID", tree_name)


class SubTree(BTNode):
    def __init__(self, subtree_name):
        super().__init__("SubTree")
        self.set_inputs("ID", subtree_name)


class Sequence(BTNode):
    def __init__(self, sequence_name):
        super().__init__("Sequence")
        self.set_inputs("name", sequence_name)


class Parallel(BTNode):
    def __init__(self, parallel_name):
        super().__init__("Parallel")
        self.set_inputs("name", parallel_name)


class ActionNode(BTNode):

    def __init__(self, action):
        super().__init__(action["ID"])
        self.action_info = deepcopy(action)
        self.action_id = self.action_info.pop("ID")

        if ActionModels.check_action(action_id=self.action_id, action=self.action_info):
            self.action_model = ActionModels.action_models.get(self.action_id)
            # 设置输入参数
            for port in self.action_model.inputs:
                if port.name in self.action_info:
                    if self.action_info[port.name] is None:
                        pass
                        # raise ValueError(f"输入端口 {port.name} 缺乏设置")
                    else:
                        self.set_inputs(port.name, str(self.action_info[port.name]))
            # 设置输出参数
            for port in self.action_model.outputs:
                if port.name in self.action_info and self.action_info[port.name] is not None and self.action_info[port.name] != "":
                    self.set_outputs(port.name, str(self.action_info[port.name]))
                else:
                    self.set_outputs(port.name, "{" + port.name + "}")
