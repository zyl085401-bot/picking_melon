import os
import yaml
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PortModel:
    name: str
    type: str


@dataclass
class ActionModel:
    id: str
    package_name: str
    class_name: str
    description: str
    inputs: List[PortModel]
    outputs: List[PortModel]


class ActionModels:
    action_models: Dict[str, ActionModel]

    def __init__(self, action_config_file: str):
        ActionModels.action_models = {}
        if action_config_file:
            self.load_action_models(action_config_file)
        else:
            print("没有配置动作的文件", flush=True)

    def load_action_models(self, action_config_file: str):
        with open(action_config_file, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if "action_dirs" in data:
                for action_dir in data["action_dirs"]:
                    self.load_action_from_dir(action_dir)
            else:
                print("没有配置动作的文件夹", flush=True)

    def load_action_from_dir(self, action_dir: str):
        # 获取目录下的所有动作配置文件
        if not os.path.exists(action_dir):
            print(f"警告: 目录不存在: {action_dir}", flush=True)
            return
            
        action_files = os.listdir(action_dir)
        for action_file in action_files:
            if action_file.endswith(".xml"):
                action_details = self.parse_action_xml(
                    os.path.join(action_dir, action_file)
                )
                ActionModels.action_models[action_details["ID"]] = ActionModel(
                    id=action_details["ID"],
                    package_name=action_details["package_name"],
                    class_name=action_details["class_name"],
                    description=action_details["description"],
                    inputs=[
                        PortModel(name=input_info["name"], type=input_info["type"])
                        for input_info in action_details["inputs"]
                    ],
                    outputs=[
                        PortModel(name=output_info["name"], type=output_info["type"])
                        for output_info in action_details["outputs"]
                    ],
                )
                # print(f"加载动作 {action_details['ID']} 成功", flush=True)
            else:
                print(f"动作配置文件 {action_file} 不是yaml文件", flush=True)

    def parse_action_xml(self, action_file: str):
        # print(f"解析动作配置文件 {action_file}", flush=True)
        tree = ET.parse(action_file)
        root = tree.getroot()

        action = root.find("Action")
        action_details = {
            "ID": action.get("ID"),
            "package_name": action.find("package_name").text,
            "class_name": action.find("class_name").text,
            "description": action.find("description").text,
            "inputs": [],
            "outputs": [],
        }

        for input_elem in action.findall("input"):
            action_details["inputs"].append(
                {"name": input_elem.get("name"), "type": input_elem.get("type")}
            )

        for output_elem in action.findall("output"):
            action_details["outputs"].append(
                {"name": output_elem.get("name"), "type": output_elem.get("type")}
            )

        return action_details

    @staticmethod
    def gen_atom_action(atom_dir, force=False):
        # 如果目录不存在，创建它；如果存在，不做操作
        os.makedirs(atom_dir, exist_ok=True)

        def generate_filename(action_id):
            result = []
            for i, c in enumerate(action_id):
                if c.isupper():
                    if i > 0 and (
                        not action_id[i - 1].isupper()
                        or (i < len(action_id) - 1 and action_id[i + 1].islower())
                    ):
                        result.append("_")
                    result.append(c.lower())
                else:
                    result.append(c)
            return "".join(result)

        # 遍历所有的动作类型
        for action_id, action_model in ActionModels.action_models.items():
            file_path = os.path.join(atom_dir, f"{generate_filename(action_id)}.py")
            if not force and os.path.exists(file_path):
                # print(f"文件 {file_path} 已存在，跳过", flush=True)
                continue
            class_content = f"""
from papjia_skill.action_models import PortModel, ActionModel
from papjia_skill.btree import ActionNode

class {action_id}(ActionNode):
    # 设置初始化函数，参数分别是action_model中inputs和outputs的列表中的PortModel的name成员
    def __init__(self, {', '.join([port.name + ('=120' if port.name == 'goal_result_timeout' else '=30' if port.name in ['result_timeout', 'wait_for_server_timeout'] else '=5' if port.name in ['goal_response_timeout', 'cancel_response_timeout'] else '=None') for port in action_model.inputs + action_model.outputs])}):
        self.action_info = {{
{(chr(10)).join([f"            '{port.name}': {port.name}," for port in action_model.inputs + action_model.outputs])}
            "ID": "{action_id}"
        }}
        # 构造action node
        super().__init__(self.action_info)
"""
            # 将class_content写入对应文件
            with open(file_path, "w") as f:
                f.write(class_content)

    @staticmethod
    def to_json():
        res = {}
        for action_id, action_info in ActionModels.action_models.items():
            res[action_id] = {
                "description": action_info.description,
                "package_name": action_info.package_name,
                "class_name": action_info.class_name,
                "inputs": [
                    {"name": port_info.name, "type": port_info.type}
                    for port_info in action_info.inputs
                ],
                "outputs": [
                    {"name": port_info.name, "type": port_info.type}
                    for port_info in action_info.outputs
                ],
            }
        return json.dumps(res, ensure_ascii=False, indent=4)

    @staticmethod
    def check_action(action_id: str, action: Dict) -> bool:
        # 验证动作ID有效性
        if action_id not in ActionModels.action_models:
            raise ValueError(f"动作 {action_id} 不存在")

        action_model = ActionModels.action_models[action_id]
        is_valid = True

        # 使用集合操作优化端口检查
        def _check_ports(expected_ports, actual_keys):
            nonlocal is_valid
            expected_names = {port.name for port in expected_ports}
            actual_names = set(actual_keys)

            # 检查缺失端口
            for missing in expected_names - actual_names:
                raise ValueError(f"动作 {action_id} 缺少 {missing}")

            # 检查多余端口
            for extra in actual_names - expected_names:
                raise ValueError(f"动作 {action_id} 不存在 {extra}")

        # 检查输入输出端口
        _check_ports(action_model.inputs + action_model.outputs, action.keys())

        return is_valid


if __name__ == "__main__":
    action_model_config_filepath = os.getenv(
        "ACTION_MODEL_CONFIG_FILEPATH",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config/action_model.yaml",
        ),
    )
    models = ActionModels(action_model_config_filepath)
    # print(models.to_json(), flush=True)
    models.gen_atom_action(os.path.abspath("papjia_skill/atom"), force=True)

    # action = {
    #     "ID": "InsertDBObject",
    #     "inputs": {
    #         "service_name": "string",
    #         "records": "string",
    #         "allowed_update": False,
    #     },
    #     "outputs": {"result": "string"},
    # }
    # print(models.check_action(action), flush=True)
