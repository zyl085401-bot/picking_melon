import time
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.compare_json_info import CompareJsonInfo
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter


def swap_quotes(input_str):
    # 使用占位符替换单引号
    temp_str = input_str.replace("'", "$PH")
    # 将双引号转换为单引号
    temp_str = temp_str.replace('"', "'")
    # 将占位符替换回双引号
    result_str = temp_str.replace("$PH", '"')
    return result_str


def tree_test_info_compare(tree_name="TestInfoCompare"):
    data1 = RemoveEscapeCharacter(
        json_input='[\{"name": "药液试管槽_1_1", "status": "无"\}, \{"name": "药液试管槽_1_2", "status": "无"\}, \{"name": "药液试管槽_1_3", "status": "无"\}]',
        json_result="{json_a}",
    )
    data2 = RemoveEscapeCharacter(
        json_input='[\{"name": "药液试管槽_1_1", "status": "有_未使用"\}, \{"name": "药液试管槽_1_2", "status": "无"\}, \{"name": "药液试管槽_1_3", "status": "有_未使用"\}]',
        json_result="{json_b}",
    )
    compare = CompareJsonInfo(
        service_name="/data_manage/compare_json_info",
        json_a="{json_a}",
        json_b="{json_b}",
        keys=["name", "status"],
    )
    seq = Sequence("SeqCompare")
    seq.add_child(data1)
    seq.add_child(data2)
    seq.add_child(compare)
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def main(args=None):
    rclpy.init(args=args)
    executor = PapjiaSkillExecutor()

    models = ActionModels("/workspace/src/papjia_skill/config/action_model.yaml")  # 需要显式加载原子动作模型以检查字段
    tree_id, tree_str = tree_test_info_compare()
    tree_str = swap_quotes(tree_str)

    try:
        executor.execute_tree(tree_string=tree_str, tree_name=tree_id)
    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
