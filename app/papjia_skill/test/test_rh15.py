import json
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.rh15_cmd_publisher import Rh15CmdPublisher


def sequence_rh15_cmd_publisher(sequence_name="SeqRh15CmdPublisher"):
    rh15_cmd_publisher = Rh15CmdPublisher(
        config_path="/workspace/install/glove_hand_bridge/share/glove_hand_bridge/config/task.json",
        task_id="task0",
        # point_id="p12",
        point_id="p0",
        wait_time=1.0,
        success="{success}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(rh15_cmd_publisher)
    return seq


def tree_test_pose(tree_name="TestRh15CmdPublisher"):
    seq = sequence_rh15_cmd_publisher()
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def main(args=None):
    rclpy.init(args=args)
    executor = PapjiaSkillExecutor()

    models = ActionModels("/workspace/install/papjia_skill/share/papjia_skill/config/action_model.yaml")  # 需要显式加载原子动作模型以检查字段
    tree_id, tree_str = tree_test_pose()

    print(tree_str, flush=True)

    try:
        result = executor.execute_tree(tree_string=tree_str, tree_name=tree_id, keys=["success"])
        success = json.loads(result.result)
        print(success, flush=True)
    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
