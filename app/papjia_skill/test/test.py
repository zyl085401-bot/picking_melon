import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.atom.test_parallel import TestParallel
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels


def create_tree():
    action1 = TestParallel(timeout=3, id="test1", result="")
    action2 = TestParallel(timeout=5, id="test2", result="")
    para1 = Parallel("TestParallel")
    para1.add_child(action1)
    para1.add_child(action2)
    tree1 = BehaviorTree("TestParallel")
    tree1.add_child(para1)
    root = BehaviorRoot()
    root.add_child(tree1)
    return "TestParallel", root.to_str()


def main(args=None):
    rclpy.init(args=args)
    executor = PapjiaSkillExecutor()

    models = ActionModels("/workspace/src/papjia_skill/config/action_model.yaml") # 需要显式加载原子动作模型以检查字段
    tree_id, tree_str = create_tree()

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
