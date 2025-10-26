import json
import rclpy
from papjia_skill.btree import BehaviorTree, BehaviorRoot, Sequence
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.visualization import Visualization
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter
from papjia_skill.utils import swap_quotes, add_escape_character

# 初始化动作模型，加载配置文件
ActionModels("/workspace/src/papjia_melon/papjia_melon_config/config/action_model.yaml")


class TestVisualize:
    def __init__(self, service_name):
        # 服务名称
        self.service_name = service_name
        # 技能执行器
        self.executor = PapjiaSkillExecutor()

    def gen_seq_visualize_path(
        self,
        seq_name="visualize_path_seq",
        start=None,
        end=None,
    ):
        # 创建一个顺序节点（Sequence），用于行为树
        seq = Sequence(seq_name)
        # 构造可视化请求的数据结构，包含type、action和data
        data = {
            "type": "path",  # 可视化类型：路径
            "action": "add",  # 动作：添加
            "data": {
                "start": start,  # 路径起点
                "end": end,  # 路径终点
                "color": [1.0, 0.0, 0.0, 1.0],  # 颜色（红色，带透明度）
                "scale": [0.05, 0.05, 0.05],  # 尺寸
                "id": 0,  # marker id
                "frame_id": "map",  # 坐标系
                "ns": "path",  # 命名空间
            },
        }
        # 序列化为json字符串
        json_data = json.dumps(data)
        # 添加转义字符，以便BT服务器能够正确解析json_data为字符串
        json_data = add_escape_character(json_data)
        # 添加去除转义字符的节点，保证最终传递给服务端的是标准json
        seq.add_child(
            RemoveEscapeCharacter(
                json_input=json_data,
                json_result="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        # 添加可视化节点，实际调用服务
        seq.add_child(
            Visualization(
                service_name=self.service_name,
                data="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        return seq

    def gen_seq_visualize_cubes(
        self,
        seq_name="visualize_cubes_seq",
        cubes=None,
    ):
        # 创建一个顺序节点（Sequence），用于行为树
        seq = Sequence(seq_name)
        # 构造可视化请求的数据结构，包含type、action和data
        data = {
            "type": "cubes",  # 可视化类型：立方体
            "action": "add",  # 动作：添加
            "data": {
                "cubes": cubes,  # 立方体数组
                "frame_id": "base_link",  # 坐标系
                "ns": "cubes",  # 命名空间
            },
        }
        # 序列化为json字符串
        json_data = json.dumps(data)
        # 添加转义字符，以便BT服务器能够正确解析json_data为字符串
        json_data = add_escape_character(json_data)
        # 添加去除转义字符的节点，保证最终传递给服务端的是标准json
        seq.add_child(
            RemoveEscapeCharacter(
                json_input=json_data,
                json_result="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        # 添加可视化节点，实际调用服务
        seq.add_child(
            Visualization(
                service_name=self.service_name,
                data="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        return seq

    def visualize(self, print_tree=False, swap_quote=False, keys=[], seq=None):
        # 创建主行为树
        tree = BehaviorTree("main_tree")
        tree.add_child(seq)
        # 创建根节点
        root = BehaviorRoot()
        root.add_child(tree)
        # 转为字符串（行为树描述）
        str_root = root.to_str()
        # 可选：单双引号互换
        if swap_quote:
            str_root = swap_quotes(str_root)
        # 可选：打印行为树结构
        if print_tree:
            print(str_root, flush=True)
        # 执行行为树
        return self.executor.execute_tree(str_root, "main_tree", keys)


if __name__ == "__main__":
    # 初始化ROS2
    rclpy.init()
    # 创建测试对象
    visualizition = TestVisualize(
        service_name="visualization_service",
    )

    # 生成路径行为序列
    path_seq = visualizition.gen_seq_visualize_path(
        start=[0.2968398982193321, 0.4441358298063278, 0.0],
        end=[0.2917471758555621, 2.4753754371777177, 0.0],
    )
    # 执行测试，可视化路径
    visualizition.visualize(
        print_tree=True,
        seq=path_seq,
    )

    # 定义测试用的立方体数据
    test_cubes = [
        {
            "pose": [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],  # 位置和欧拉角
            "size": [0.2, 0.2, 0.2],  # 尺寸
            "color": [1.0, 0.0, 0.0, 1.0],  # 红色
            "id": 0,
        },
        {
            "pose": [1.5, 1.0, 0.0, 0.0, 0.0, 1.57],  # 位置和欧拉角（旋转90度）
            "size": [0.3, 0.3, 0.3],  # 尺寸
            "color": [0.0, 1.0, 0.0, 1.0],  # 绿色
            "id": 1,
        },
        {
            "pose": [1.0, 1.5, 0.0, 0.0, 0.0, 0.0],  # 位置和欧拉角
            "size": [0.25, 0.25, 0.25],  # 尺寸
            "color": [0.0, 0.0, 1.0, 0.8],  # 蓝色，带透明度
            "id": 2,
        },
    ]

    # 生成立方体行为序列
    cubes_seq = visualizition.gen_seq_visualize_cubes(
        cubes=test_cubes,
    )
    # 执行测试，可视化立方体
    visualizition.visualize(
        print_tree=True,
        seq=cubes_seq,
    )
