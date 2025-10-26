import json
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.image_get_from_topic import ImageGetFromTopic
from papjia_skill.atom.crop_image_msg import CropImageMsg
from papjia_skill.atom.mask_detect import MaskDetect
from papjia_skill.atom.object2d_to_json import Object2dToJson
from papjia_skill.atom.remapping_info import RemappingInfo
from papjia_skill.atom.insert_db_object import InsertDBObject
from papjia_skill.atom.update_db_object import UpdateDBObject
from papjia_skill.atom.query_db_object import QueryDBObject
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter


def swap_quotes(input_str):
    # 使用占位符替换单引号
    temp_str = input_str.replace("'", "$PH")
    # 将双引号转换为单引号
    temp_str = temp_str.replace('"', "'")
    # 将占位符替换回双引号
    result_str = temp_str.replace("$PH", '"')
    return result_str


def sequence_image_seg(sequence_name="SeqImageSeg"):
    get_image = ImageGetFromTopic(
        topic_name="/camera1/rgb/image_raw", image="{image_msg}"
    )
    crop_image = CropImageMsg(
        image_input="{image_msg}",
        x1=713,
        y1=662,
        x2=1360,
        y2=1190,
        image_output="{image_msg}",
    )
    mask_detect = MaskDetect(
        service_name="/papjia_vision/service_image_segment",
        image="{image_msg}",
        max_num=30,
        min_score=0.5,
        allowed_categories=["test_tube"],
        allowed_roi=[],
        objs_num="{objs_num}",
        objects="{objs2d}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(get_image)
    seq.add_child(crop_image)
    seq.add_child(mask_detect)
    return seq


def sequence_objs2json(sequence_name="Seqobjs2json"):
    to_json = Object2dToJson(objects="{objs2d}", json_result="{objs_json}")
    seq = Sequence(sequence_name)
    seq.add_child(to_json)
    return seq


def sequence_remapping(sequence_name="SeqRemapping"):
    remapping = RemappingInfo(
        service_name="/data_manage/database_manage_service",
        methods=["药液试管槽映射"],
        records_input="{objs_json}",
        records_output="{objs_remapped}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(remapping)
    return seq


def sequence_insert(sequence_name="SeqInsert"):
    insert = InsertDBObject(
        service_name="/data_manage/database_manage_service",
        collection_name="槽位",
        allowed_update="true",
        records="{objs_remapped}",
        result="{result}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(insert)
    return seq


def sequence_update(sequence_name="SeqUpdate"):
    query = RemoveEscapeCharacter(
        json_input='\{"name":"药液试管槽_4_1"\}', json_result="{json_query}"
    )
    record = RemoveEscapeCharacter(
        json_input='\{"score": 0.3\}', json_result="{json_record}"
    )
    update = UpdateDBObject(
        service_name="/data_manage/database_manage_service",
        collection_name="槽位",
        query="{json_query}",
        record="{json_record}",
        result="{result}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(query)
    seq.add_child(record)
    seq.add_child(update)
    return seq

def sequence_query_name(sequence_name="SeqQuery"):
    query_single = RemoveEscapeCharacter(
        json_input='\{"name":"药液试管槽_4_1"\}', json_result="{json_query}"
    )
    query = QueryDBObject(
        service_name="/data_manage/database_manage_service",
        collection_name="槽位",
        query="{json_query}",
        result="{query_result}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(query_single)
    seq.add_child(query)
    return seq

def sequence_query_category(sequence_name="SeqQuery"):
    query_single = RemoveEscapeCharacter(
        json_input='\{"category":"药液试管槽"\}', json_result="{json_query}"
    )
    query = QueryDBObject(
        service_name="/data_manage/database_manage_service",
        collection_name="槽位",
        query="{json_query}",
        result="{query_result}",
    )
    seq = Sequence(sequence_name)
    seq.add_child(query_single)
    seq.add_child(query)
    return seq

def tree_test_db(tree_name="TestDataBase"):
    seq = Sequence("test")
    seq.add_child(sequence_image_seg())
    seq.add_child(sequence_objs2json())
    seq.add_child(sequence_remapping())
    seq.add_child(sequence_insert())
    seq.add_child(sequence_update())
    seq.add_child(sequence_query_name())
    seq.add_child(sequence_query_category())
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
    tree_id, tree_str = tree_test_db()

    tree_str = swap_quotes(tree_str)

    print(tree_str, flush=True)

    try:
        result = executor.execute_tree(tree_string=tree_str, tree_name=tree_id, keys=["query_result"])
        print(result, flush=True)
        records = json.loads(json.loads(result).get("query_result")).get("SUCCESS")
        print(records)
    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
