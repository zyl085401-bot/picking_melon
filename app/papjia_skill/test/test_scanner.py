import time
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.get_string_from_topic import GetStringFromTopic
from papjia_common_msgs.msg import StringStamped


def tree_test_scanner(tree_name="TestScanner"):
    scanner = GetStringFromTopic(
        topic_name="/scanner1/barcode_data",
        timeout=10.0,
        hz=10.0,
    )
    seq = Sequence("SeqScanner")
    seq.add_child(scanner)
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def main(args=None):
    rclpy.init(args=args)
    executor = PapjiaSkillExecutor()

    models = ActionModels(
        "/workspace/src/papjia_skill/config/action_model.yaml"
    )  # 需要显式加载原子动作模型以检查字段
    tree_id, tree_str = tree_test_scanner()

    try:
        publisher = executor.create_publisher(
            StringStamped,
            "/scanner1/barcode_data",
            10,
        )
        time.sleep(5.0)

        def publish_data():
            time.sleep(5.0)
            msg = StringStamped()
            msg.header.stamp = executor.get_clock().now().to_msg()
            msg.value = "20250319202530"
            publisher.publish(msg)
            executor.get_logger().info("Published data to /scanner1/barcode_data")

        thread = threading.Thread(target=publish_data)
        thread.start()

        executor.execute_tree(tree_string=tree_str, tree_name=tree_id)

        thread.join()

    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
