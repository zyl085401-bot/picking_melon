from flask import Flask, request, jsonify
from flask_cors import CORS


class StorageManager:
    # 存储库配置 名称 -> 行 X 列
    STORAGE_CONFIG = {
        "药液试管库": {"rows": 4, "cols": 5},
        "玻璃试管库": {"rows": 4, "cols": 5},
        "1ml移液枪库": {"rows": 8, "cols": 12},
        "10ml移液枪库": {"rows": 4, "cols": 6},
        "烧瓶库": {"rows": 6, "cols": 8},
    }

    # 槽位状态
    SLOT_STATUS = ["无", "有_未使用", "有_已使用", "有_使用中"]

    # 存储库对应的槽位类型
    STORAGE_TO_SLOT = {
        "药液试管库": "药液试管槽",
        "玻璃试管库": "玻璃试管槽",
        "1ml移液枪库": "1ml枪头槽",
        "10ml移液枪库": "10ml枪头槽",
        "烧瓶库": "烧瓶槽",
    }

    def __init__(self):
        self.all_slots = {}  # 所有槽位信息
        self.initialize_slots()  # 初始化槽位

    def initialize_slots(self):
        # 初始化所有槽位
        for storage_name, config in self.STORAGE_CONFIG.items():
            slot_type = self.STORAGE_TO_SLOT[storage_name]
            for i in range(config["rows"]):
                for j in range(config["cols"]):
                    slot_name = f"{slot_type}_{i+1}_{j+1}"
                    slot_info = {
                        "name": slot_name,  # 槽位名称
                        "status": "无",  # 槽位状态，初始为“无”
                        "category": slot_type,  # 槽位类型
                        "storage": storage_name,  # 所属存储库名称
                        "position": {"row": i + 1, "col": j + 1},  # 槽位在存储库中的位置（行和列）
                    }
                    self.all_slots[slot_name] = slot_info

    def get_all_slots(self):
        # 获取所有槽位信息
        # 返回值是一个字典，键为存储库名称，值为该存储库的所有槽位信息列表
        res = {}
        for storage_name in self.STORAGE_CONFIG.keys():
            res[storage_name] = self.get_storage_slots(storage_name=storage_name)
        return res

    def get_storage_slots(self, storage_name):
        # 获取指定存储库的槽位信息
        # 返回值是一个字典，键为槽位名称，值为一个字典
        return {k: v for k, v in self.all_slots.items() if v["storage"] == storage_name}

    def get_storage_slots_via_vision(self, storage_name):
        # 获取指定存储库的槽位信息（通过视觉）
        # 返回值是一个字典，键为槽位名称，值为一个字典
        return {k: v for k, v in self.all_slots.items() if v["storage"] == storage_name}

    def get_slot(self, slot_name):
        # 获取指定槽位的信息
        # 返回值是一个字典，包含槽位的详细信息
        return self.all_slots.get(slot_name, {})

    def check_storage_slots(self, storage_name, slots):
        # 校验指定存储库的槽位状态
        # 参数 slots 是一个列表，包含需要校验的槽位信息，每个槽位信息是一个字典
        # 返回值是一个字典，键为槽位名称，值为一个字典，包含校验结果
        res = {}  # 存储校验结果
        slots_stored = self.get_storage_slots_via_vision(storage_name=storage_name)  # 获取存储库的槽位信息（通过视觉）
        for slot in slots:
            slot_name = slot.get("name", None)  # 获取槽位名称
            slot_status = slot.get("status", None)  # 获取槽位状态
            if slot_name and slot_status:
                status_stored = slots_stored.get(slot_name, {}).get("status", "None")  # 获取存储的槽位状态
                if slot_status != status_stored:
                    res[slot_name] = {"status": [slot_status, status_stored]}  # 如果状态不一致，记录校验结果
        return res  # 返回校验结果

    def update_storage_slots(self, storage_name, slots):
        # 更新指定存储库的槽位状态
        # 参数 slots 是一个列表，包含需要更新的槽位信息，每个槽位信息是一个字典
        # 返回值是一个元组，第一个元素是布尔值，表示更新是否成功，第二个元素是一个字典，键为槽位名称，值为布尔值，表示该槽位是否更新成功
        res = {}  # 存储更新结果
        status = True
        slots_stored = self.get_storage_slots(storage_name=storage_name)  # 获取存储库的槽位信息
        for slot in slots:
            slot_name = slot.get("name", "")  # 获取槽位名称
            slot_status = slot.get("status", "")  # 获取槽位状态
            if slot_name and slot_status:
                slot_stored = slots_stored.get(slot_name, {})  # 获取存储的槽位信息
                for k, v in slot.items():
                    slot_stored[k] = v  # 更新槽位信息
                res[slot_name] = True  # 更新成功
            else:
                res[slot_name] = False  # 更新失败
                status = False
        return status, res  # 返回更新结果


# ------------------ Flask App ------------------ #

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app)
manager = StorageManager()


@app.route("/api/slot/get_all", methods=["GET"])
def api_get_all_slot():
    # 获取指定槽位的信息
    slots = manager.get_all_slots()
    if slots:
        return jsonify({"status": "success", "data": slots})
    return jsonify({"status": "error", "message": f"不存在任何槽"}), 404


@app.route("/api/slot/<slot_name>/get", methods=["GET"])
def api_get_slot(slot_name):
    # 获取指定槽位的信息
    slot = manager.get_slot(slot_name)
    if slot:
        return jsonify({"status": "success", "data": slot})
    return jsonify({"status": "error", "message": f"槽 {slot_name} 不存在"}), 404


@app.route("/api/storage/<storage_name>/get", methods=["GET"])
def api_get_storage_slots(storage_name):
    # 获取指定存储库的所有槽位信息
    if storage_name not in StorageManager.STORAGE_CONFIG:
        return jsonify({"status": "error", "message": f"库 {storage_name} 不存在"}), 404
    return jsonify({"status": "success", "data": manager.get_storage_slots(storage_name)})


@app.route("/api/storage/<storage_name>/check", methods=["PUT"])
def api_check_storage_slots(storage_name):
    # 校验指定存储库的槽位状态
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "未提供校验数据"}), 400

    result = manager.check_storage_slots(storage_name, data["slots"])
    if result:
        return jsonify({"status": "error", "message": "校验失败", "data": result}), 400
    else:
        return jsonify({"status": "success", "message": "校验成功", "data": {}})


@app.route("/api/storage/<storage_name>/update", methods=["PUT"])
def api_update_storage_slots(storage_name):
    # 更新指定存储库的槽位状态
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "未提供更新数据"}), 400

    status, result = manager.update_storage_slots(storage_name, data["slots"])
    if status:
        return jsonify({"status": "success", "message": "更新成功", "data": result})
    else:
        return jsonify({"status": "error", "message": "更新失败", "data": result}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
