import json
from papjia_skill.atom.object_detect import ObjectDetect
from papjia_skill.atom.object_to_json import ObjectToJson
from papjia_skill.atom.json_to_object import JsonToObject
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter
from papjia_skill.btree import Sequence
from papjia_skill.utils import add_escape_character, swap_quotes
from copy import deepcopy


class ObjectDetector(Sequence):
    def __init__(self, service_name=None, max_num=None, min_score=None):
        self.service_name = service_name if service_name else "/papjia/vision/local/object/detect"   #/papjia/vision/local/object/detect global
        self.max_num = max_num if max_num else 10
        self.min_score = min_score if min_score else 0.55
        print(f"service_name: {self.service_name}, max_num: {self.max_num}, min_score: {self.min_score}", flush=True)

    def gen_sequence_detect_json_objects(self, service_name=None, max_num=None, min_score=None, key="json_objects"):
        seq = Sequence("seq_detect_objects")
        detect_objects = ObjectDetect(
            service_name=service_name if service_name else self.service_name,
            max_num=max_num if max_num else self.max_num,
            min_score=min_score if min_score else self.min_score,
            objects="{objects}",
        )
        to_json = ObjectToJson(
            objects="{objects}",
            json_result=f"{{{key}}}",
        )
        seq.add_child(detect_objects)
        seq.add_child(to_json)
        return seq

    def gen_action_dict2object(self, obj_dict, key="result_object"):
        json_data = json.dumps(obj_dict)
        json_object = RemoveEscapeCharacter(json_input=add_escape_character(json_data), json_result="{json_object}")
        json2obj = JsonToObject(json_object="{json_object}", result_object=f"{{{key}}}")
        seq = Sequence("seq_dict2object")
        seq.add_child(json_object)
        seq.add_child(json2obj)
        return seq

    def select_nearest_object(self, object_list, base_position=[0.0, 0.0, 0.0]):
        """
        从物体列表中选择距离最近的物体
        """
        if not object_list:
            return (None, None)

        min_distance = float("inf")
        nearest_object = None
        nearest_index = None
        for index, obj in enumerate(object_list):
            obj_position = obj["pose"][:3]  # 只取xyz坐标
            distance = (
                (obj_position[0] - base_position[0]) ** 2
                + (obj_position[1] - base_position[1]) ** 2
                + (obj_position[2] - base_position[2]) ** 2
            ) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_object = deepcopy(obj)
                nearest_index = index
        return (nearest_object, nearest_index)

    def select_grasp_position(self, object):
        """
        根据物体的位置选择机械臂的抓取位置
        """
        if not object:
            return None

        # 获取物体位置
        object_position = object["pose"][:3]
        object_size = object["scale"]
        # 计算顶端位置
        top_position = [object_position[0], object_position[1], object_position[2] + object_size[2] / 2]
        # 计算抓取位置
        # to_do 【补偿运动 向前 +0.11】
        grasp_position = [top_position[0], top_position[1], top_position[2] + 0.03 - 0.16]
        print(
            f"物体位置: ({object_position[0]:.2f}, {object_position[1]:.2f}, {object_position[2]:.2f}) --> 抓取位置: ({grasp_position[0]:.2f}, {grasp_position[1]:.2f}, {grasp_position[2]:.2f})"
        )
        return grasp_position

    def is_valid_position(self, position, obs_name="观测点_中"):
        is_valid = False
        can_grasp = False
        need_move_dist = 0.0
        x, y, z = position[0:3]
        if x < 1.60 and abs(y) < 0.9 and z < 1.85:
            is_valid = True
            can_grasp = True
        # if obs_name == "观测点_中":
        #     best_obs_x = 1.28
        #     if abs(y) < 0.45 and x < 1.50:
        #         can_grasp = True
        #     elif abs(y) < 0.65 and x < 1.37:
        #         can_grasp = True
        #     elif abs(y) < 0.65 and x < 1.60:
        #         can_grasp = True
        #         is_valid = True
        #         need_move_dist = x - best_obs_x
        # elif obs_name == "观测点_左":
        #     best_obs_x = 1.04
        #     if y >= 0.50 and y <= 1.05 and x < 1.14:
        #         can_grasp = True
        #     elif y >= 0.50 and y <= 0.9 and x < 1.25:
        #         can_grasp = True
        #     elif y >= 0.50 and y <= 1.05 and x < 1.35:
        #         can_grasp = True
        #         is_valid = True
        #         need_move_dist = x - best_obs_x
        # elif obs_name == "观测点_右":
        #     best_obs_x = 1.18
        #     if y >= -0.7 and y <= -0.4 and x < 1.35:
        #         can_grasp = True
        #     elif y >= -0.8 and y <= -0.4 and x < 1.30:
        #         can_grasp = True
        #     elif y >= -0.9 and y <= -0.4 and x < 1.23:
        #         can_grasp = True
        #     elif y >= -0.95 and y <= -0.4 and x < 1.35:
        #         can_grasp = True
        #         is_valid = True
        #         need_move_dist = x - best_obs_x
        return (can_grasp, is_valid, need_move_dist)

    def filter_and_select_object(self, objects, obs_name="观测点_中"):
        can_grasp_objs = []
        valid_grasp_info = []
        min_move_dist = 1000.0
        for obj in objects:
            if obj["scale"][2] < 0.15:
                print(f"物体高度小于0.20米，跳过: {obj['scale']}")
                continue
            grasp_position = self.select_grasp_position(obj)
            can_grasp, is_valid, need_move_dist = self.is_valid_position(grasp_position, obs_name=obs_name)
            print(f"can_grasp: {can_grasp}, is_valid: {is_valid}, need_move_dist: {need_move_dist:.2f}")
            if can_grasp:
                can_grasp_obj = deepcopy(obj)
                can_grasp_obj["original_pose"] = obj["pose"][:]
                can_grasp_obj["original_scale"] = obj["scale"][:]
                can_grasp_obj["pose"][:3] = grasp_position
                can_grasp_objs.append(can_grasp_obj)
            elif is_valid:  # 不是可以抓取的位置，但是是有效的位置
                valid_grasp_info.append((can_grasp, is_valid, need_move_dist))
        for can_grasp, is_valid, need_move_dist in valid_grasp_info:
            if need_move_dist > 0.01 and need_move_dist < min_move_dist:
                min_move_dist = need_move_dist
        obj, index = self.select_nearest_object(can_grasp_objs)
        return obj, min_move_dist
        # return None, 1000.0
