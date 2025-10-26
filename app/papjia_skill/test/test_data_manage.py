import time
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.data_manage.data_manipulation import DataManipulation


def main(args=None):
    rclpy.init(args=args)

    models = ActionModels(
        "/workspace/src/papjia_skill/config/action_model.yaml"
    )  # 需要显式加载原子动作模型以检查字段

    dm = DataManipulation(db_srv_topic="/data_manage/database_manage_service")
    try:
        # 测试信息查询
        print("测试信息查询 ...", flush=True)
        res = dm.get_slots_by_type(slot_type="药液试管库")
        print(res, flush=True)
        # 测试信息比较
        print("测试信息比较 ...", flush=True)
        rows = 4
        cols = 5
        idx = 5
        slot_type = "药液试管库"
        slot_name_prefix = "药液试管槽"
        slots = []
        for i in range(rows):
            for j in range(cols):
                slot = {"name": f"{slot_name_prefix}_{i+1}_{j+1}", "status": "无"}
                slots.append(slot)
        res = dm.compare_slots_by_type(slot_type=slot_type, slots=slots)
        print("比较结果：", res, flush=True)
        slots[idx]["status"] = "有_未使用"
        res = dm.compare_slots_by_type(slot_type=slot_type, slots=slots)
        print("比较结果（数据更改后）：", res, flush=True)
        # 测试更新
        print("测试信息更新 ...", flush=True)
        slot_name = f"药液试管槽_{int(idx / cols) + 1}_{int(idx % cols) + 1}"
        record = {"status": "有_未使用"}
        dm.update_slot_by_name(name=slot_name, record=record)
        res = dm.compare_slots_by_type(slot_type=slot_type, slots=slots)
        print("比较结果（数据库更新后）：", res, flush=True)
        # 测试视觉更新
        print("测试信息视觉更新 ...", flush=True)
        res = dm.update_slots_by_vision(slot_type=slot_type)
        print(res, flush=True)
        res = dm.compare_slots_by_type(slot_type=slot_type, slots=slots)
        print("比较结果（视觉更新数据库后）：", res, flush=True)
    except Exception as e:
        print(f"An error occurred: {e}", flush=True)


if __name__ == "__main__":
    main()
