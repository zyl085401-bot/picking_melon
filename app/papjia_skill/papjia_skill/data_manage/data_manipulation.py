import json
import rclpy
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.utils import swap_quotes, add_escape_character
from papjia_skill.atom.image_get_from_topic import ImageGetFromTopic
from papjia_skill.atom.crop_image_msg import CropImageMsg
from papjia_skill.atom.mask_detect import MaskDetect
from papjia_skill.atom.object2d_to_json import Object2dToJson
from papjia_skill.atom.remapping_info import RemappingInfo
from papjia_skill.atom.insert_db_object import InsertDBObject
from papjia_skill.atom.update_db_object import UpdateDBObject
from papjia_skill.atom.query_db_object import QueryDBObject
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter


class DataManipulation:
    """
    一个处理与槽管理相关的数据操作的类。

    属性:
        db_srv_topic (str): 数据库管理服务的主题。
        executor (PapjiaSkillExecutor): 用于运行行为树的执行器。
        slot_types (dict): 一个将槽类型映射到其各自槽名称的字典。
    """

    def __init__(
        self,
        db_srv_topic="/data_manage/database_manage_service",
        vision_srv_topic="/papjia_vision/service_image_segment",
    ):
        self.db_srv_topic = db_srv_topic
        self.vision_srv_topic = vision_srv_topic
        self.executor = PapjiaSkillExecutor()
        self.slot_types = {
            "药液试管库": "药液试管槽",
            "玻璃试管库": "玻璃试管槽",
            "1ml移液枪库": "1ml枪头槽",
            "10ml移液枪库": "10ml枪头槽",
            "烧瓶库": "烧瓶槽",
        }
        self.rects = {
            "药液试管库": [713, 662, 1360, 1190],
            "玻璃试管库": [713, 662, 1360, 1190],
            "1ml移液枪库": [713, 662, 1360, 1190],
            "10ml移液枪库": [713, 662, 1360, 1190],
            "烧瓶库": [713, 662, 1360, 1190],
        }
        self.methods = {
            "药液试管库": ["药液试管槽映射"],
            "玻璃试管库": ["玻璃试管槽映射"],
            "1ml移液枪库": ["1ml枪头槽映射"],
            "10ml移液枪库": ["10ml枪头槽映射"],
            "烧瓶库": ["烧瓶槽映射"],
        }
        self.cameras = {
            "药液试管库": "/camera1/rgb/image_raw",
            "玻璃试管库": "/camera1/rgb/image_raw",
            "1ml移液枪库": "/camera1/rgb/image_raw",
            "10ml移液枪库": "/camera1/rgb/image_raw",
            "烧瓶库": "/camera2/rgb/image_raw",
        }
        self.categories = {
            "药液试管库": ["test_tube"],
            "玻璃试管库": ["玻璃试管"],
            "1ml移液枪库": ["1ml枪头"],
            "10ml移液枪库": ["10ml枪头"],
            "烧瓶库": ["烧瓶"],
        }

    def exec_tree(self, seq, tree_name, keys=[]):
        """
        执行一个包含给定序列和树名称的行为树。

        参数:
            seq (Sequence): 要添加为行为树子节点的序列。
            tree_name (str): 行为树的名称。
            keys (list, optional): 需要从执行后的黑板导出的数据的变量名列表，默认为空。

        返回:
            Result: 执行行为树的结果，一般为字典。
        """
        tree = BehaviorTree(tree_name)
        tree.add_child(seq)
        root = BehaviorRoot()
        root.add_child(tree)
        tree_str = swap_quotes(root.to_str())
        print(tree_str, flush=True)
        result = self.executor.execute_tree(tree_string=tree_str, tree_name=tree_name, keys=keys)
        result = result.result # TODO 光拿结果不够，还要再判断一下执行是否成功
        return result

    def get_slot_by_name(self, slot_name=None, tree_name="GetSlot"):
        """
        根据槽名称获取槽信息。

        参数:
            slot_name (str): 槽的名称。
            tree_name (str): 行为树的名称。

        返回:
            dict: 槽的信息，如果未找到则返回 None。
        """
        query = {"name": slot_name}
        to_json = RemoveEscapeCharacter(
            json_input=add_escape_character(json.dumps(query, ensure_ascii=False)),
            json_result="{json_query}",
        )
        query_op = QueryDBObject(
            service_name=self.db_srv_topic,
            collection_name="槽位",
            query="{json_query}",
            result="{query_result}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(to_json)
        seq.add_child(query_op)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["query_result"])
        records = json.loads(json.loads(result).get("query_result", {})).get("SUCCESS", [])
        if records:
            return records[0]
        return None

    def get_slots_by_type(self, slot_type=None, tree_name="GetSlots"):
        """
        根据槽类型获取槽信息。

        参数:
            slot_type (str): 槽的类型。
            tree_name (str): 行为树的名称。

        返回:
            list: 按名称排序的槽信息列表。
        """
        query = {"category": self.slot_types[slot_type]}
        to_json = RemoveEscapeCharacter(
            json_input=add_escape_character(json.dumps(query, ensure_ascii=False)),
            json_result="{json_query}",
        )
        query_op = QueryDBObject(
            service_name=self.db_srv_topic,
            collection_name="槽位",
            query="{json_query}",
            result="{query_result}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(to_json)
        seq.add_child(query_op)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["query_result"])
        records = json.loads(json.loads(result).get("query_result", {})).get("SUCCESS", [])
        res = {}
        for record in records:
            res[record.get("name", "无效键值")] = record
        return res

    def update_slot_by_name(self, name, record, tree_name="UpdateSlot"):
        """
        更新指定名称的槽记录。

        参数:
            name (str): 槽的名称。
            record (dict): 要更新的槽记录。
            tree_name (str): 行为树的名称。

        返回:
            int: 更新的记录数量。
        """
        query = {"name": name}
        query_to_json = RemoveEscapeCharacter(
            json_input=add_escape_character(json.dumps(query, ensure_ascii=False)),
            json_result="{json_query}",
        )
        record_to_json = RemoveEscapeCharacter(
            json_input=add_escape_character(json.dumps(record, ensure_ascii=False)),
            json_result="{json_record}",
        )
        update_op = UpdateDBObject(
            service_name=self.db_srv_topic,
            collection_name="槽位",
            query="{json_query}",
            record="{json_record}",
            result="{update_result}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(query_to_json)
        seq.add_child(record_to_json)
        seq.add_child(update_op)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["update_result"])
        cnt = json.loads(json.loads(result).get("update_result", {})).get("SUCCESS", 0)
        return cnt

    def get_slots_by_vision(self, slot_type, tree_name="DetectByVision"):
        get_image = ImageGetFromTopic(
            topic_name=self.cameras[slot_type],
            image="{image_msg}",
        )
        crop_image = CropImageMsg(
            image_input="{image_msg}",
            x1=self.rects[slot_type][0],
            y1=self.rects[slot_type][1],
            x2=self.rects[slot_type][2],
            y2=self.rects[slot_type][3],
            image_output="{image_msg}",
        )
        rect_detect = MaskDetect(
            service_name=self.vision_srv_topic,
            image="{image_msg}",
            max_num=30,
            min_score=0.5,
            allowed_categories=self.categories[slot_type],
            allowed_roi=[],
            objs_num="{objs_num}",
            objects="{objs2d}",
        )
        to_json = Object2dToJson(
            objects="{objs2d}",
            json_result="{objs_json}",
        )
        remapping = RemappingInfo(
            service_name=self.db_srv_topic,
            methods=self.methods[slot_type],
            records_input="{objs_json}",
            records_output="{objs_remapped}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(get_image)
        seq.add_child(crop_image)
        seq.add_child(rect_detect)
        seq.add_child(to_json)
        seq.add_child(remapping)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["objs_remapped"])
        records = json.loads(json.loads(result).get("objs_remapped", []))
        res = {}
        for record in records:
            res[record.get("name", "无效键值")] = record
        return res

    def update_slots_by_vision(self, slot_type, tree_name="InsertByVision"):
        get_image = ImageGetFromTopic(
            topic_name=self.cameras[slot_type],
            image="{image_msg}",
        )
        crop_image = CropImageMsg(
            image_input="{image_msg}",
            x1=self.rects[slot_type][0],
            y1=self.rects[slot_type][1],
            x2=self.rects[slot_type][2],
            y2=self.rects[slot_type][3],
            image_output="{image_msg}",
        )
        rect_detect = MaskDetect(
            service_name=self.vision_srv_topic,
            image="{image_msg}",
            max_num=30,
            min_score=0.5,
            allowed_categories=self.categories[slot_type],
            allowed_roi=[],
            objs_num="{objs_num}",
            objects="{objs2d}",
        )
        to_json = Object2dToJson(
            objects="{objs2d}",
            json_result="{objs_json}",
        )
        remapping = RemappingInfo(
            service_name=self.db_srv_topic,
            methods=self.methods[slot_type],
            records_input="{objs_json}",
            records_output="{objs_remapped}",
        )
        insert = InsertDBObject(
            service_name=self.db_srv_topic,
            collection_name="槽位",
            allowed_update="true",
            records="{objs_remapped}",
            result="{insert_result}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(get_image)
        seq.add_child(crop_image)
        seq.add_child(rect_detect)
        seq.add_child(to_json)
        seq.add_child(remapping)
        seq.add_child(insert)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["insert_result"])
        res = json.loads(json.loads(result).get("insert_result", []))
        return res

    def compare_slots_by_type(self, slot_type, slots):
        """
        比较给定槽类型的槽信息与提供的槽信息。

        参数:
            slot_type (str): 槽的类型。
            slots (list): 要比较的槽信息列表。

        返回:
            dict: 包含比较状态和差异信息的字典。
        """
        slots_a = sorted(slots, key=lambda x: x.get("name", ""))
        slots_b = self.get_slots_by_type(slot_type=slot_type)
        status = "SUCCESS"
        differences = []
        if not (isinstance(slots_a, list) and isinstance(slots_b, list)):
            status = "NOT_LIST"

        elif len(slots_a) != len(slots_b):
            status = "NOT_SIZE_EQUAL"
        else:
            for idx, (item1, item2) in enumerate(zip(slots_a, slots_b)):
                if not isinstance(item1, dict):
                    raise KeyError(f"item_a {idx} is not dict")
                if not isinstance(item2, dict):
                    raise KeyError(f"item_b {idx} is not dict")
                diff = {}
                for key in item1.keys():
                    value1 = item1.get(key)
                    value2 = item2.get(key)
                    if value1 != value2:  # 如果两个字典中该键的值不同
                        diff[key] = {"value1": value1, "value2": value2}

                if diff:
                    differences.append({"index": idx, "differences": diff})
        if len(differences) != 0:
            status = "HAS_DIFF"
        return {"status": status, "differences": differences}

    def update_object_by_code(self, record, tree_name="InsertCode"):
        records = [record]
        records_to_json = RemoveEscapeCharacter(
            json_input=add_escape_character(json.dumps(records, ensure_ascii=False)),
            json_result="{json_records}",
        )
        insert = InsertDBObject(
            service_name=self.db_srv_topic,
            collection_name="物料",
            allowed_update="true",
            records="{json_records}",
            result="{insert_result}",
        )
        seq = Sequence(f"Seq{tree_name}")
        seq.add_child(records_to_json)
        seq.add_child(insert)
        result = self.exec_tree(seq=seq, tree_name=tree_name, keys=["insert_result"])
        res = json.loads(json.loads(result).get("insert_result", [{"FAILED": 0}]))
        return res[0]

    def get_all_slots(self):
        """
        获取所有槽类型的槽信息。

        返回:
            dict: 一个包含所有槽类型及其对应槽信息的字典。
        """
        res = {}
        for slot_type in self.slot_types.keys():
            records = self.get_slots_by_type(slot_type)
            res[slot_type] = records
        return res
