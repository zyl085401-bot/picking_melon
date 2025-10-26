import json
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.object_detect import ObjectDetect
from papjia_skill.atom.object_to_json import ObjectToJson


def sequence_object_pose(sequence_name="SeqObjectPose"):
    object_detect = ObjectDetect(
        service_name="/papjia_vision/service_object_detect",
        max_num=5,
        min_score=0.8,
        objects="{objs}",
    )
    object_to_json = ObjectToJson(
        objects="{objs}",
        json_result="{objs_json}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(object_detect)
    seq.add_child(object_to_json)
    return seq


def tree_test_pose(tree_name="TestObjectPose"):
    seq = sequence_object_pose()
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
        result = executor.execute_tree(tree_string=tree_str, tree_name=tree_id, keys=["objs_json"])
        objs_json = json.loads(result.result)
        print(objs_json, flush=True)
        objs = json.loads(objs_json["objs_json"])
        print(objs, flush=True)
        for obj in objs:
            print(obj, flush=True)
            for key, value in obj.items():
                print(key, value, flush=True)
    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
