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

    poses = [
        [
            0.873,
            0.000,
            1.432,
            0.000,
            -0.188,
            -0.000,
            0.982,
        ],  # 0.4 -> 0.5 0.873 + 0.5 = 1.373
        [
            0.637,
            0.765,
            1.503,
            0.065,
            -0.118,
            0.140,
            0.981,
        ],  # 0.4 -> 0.5 0.637 + 0.5 = 1.137
        [
            0.880,
            -0.664,
            1.557,
            -0.004,
            -0.205,
            -0.073,
            0.976,
        ],  # 0.3 -> 0.4 0.880 + 0.4 = 1.280
    ]

    pose = poses[0]
    scale = [0.05, 0.05, 0.4]
    color = [0.0, 1.0, 0.0, 0.6]

    # 定义测试用的立方体数据
    test_cubes = [
        {
            "pose": [
                pose[0] + 0.3,
                pose[1],
                1.9 - scale[2] / 2,
                0.0,
                0.0,
                0.0,
            ],  # 位置和欧拉角
            "scale": scale,  # 尺寸
            "color": color,  # 红色
            "id": 0,
        },
        {
            "pose": [
                pose[0] + 0.4,
                pose[1],
                1.9 - scale[2] / 2,
                0.0,
                0.0,
                0.0,
            ],  # 位置和欧拉角（旋转90度）
            "scale": scale,  # 尺寸
            "color": color,  # 绿色
            "id": 1,
        },
        {
            "pose": [
                pose[0] + 0.5,
                pose[1],
                1.9 - scale[2] / 2,
                0.0,
                0.0,
                0.0,
            ],  # 位置和欧拉角
            "scale": scale,  # 尺寸
            "color": color,  # 蓝色，带透明度
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
