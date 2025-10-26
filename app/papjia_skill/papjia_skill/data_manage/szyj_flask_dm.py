import rclpy
from flask import Flask, request, jsonify
from flask_cors import CORS
from papjia_skill.action_models import ActionModels
from papjia_skill.data_manage.data_manipulation import DataManipulation


class StorageManager:
    # 定义库的配置
    STORAGE_CONFIG = {
        "药液试管库": {"rows": 5, "cols": 4},
        "玻璃试管库": {"rows": 5, "cols": 4},
        "1ml移液枪库": {"rows": 10, "cols": 10},
        "10ml移液枪库": {"rows": 10, "cols": 10},
        "烧瓶库": {"rows": 6, "cols": 8},
    }

    def __init__(self):
        self.dm = DataManipulation(
            db_srv_topic="/data_manage/database_manage_service",
            vision_srv_topic="/papjia_vision/service_image_segment",
        )

    def get_all_slots(self) -> dict:
        # 获取所有槽位信息
        return self.dm.get_all_slots()  # 返回所有槽位信息

    def get_storage_slots(self, storage_name: str) -> list:
        # 获取指定存储库的槽位信息
        return self.dm.get_slots_by_type(storage_name)  # 返回指定存储库的槽位信息

    def get_storage_slots_via_vision(self, storage_name: str) -> list:
        # 获取指定存储库的槽位信息（通过视觉）
        return self.dm.get_slots_by_vision(storage_name)  # 返回槽位信息

    def get_slot(self, slot_name: str) -> dict:
        # 获取指定槽位的信息
        return self.dm.get_slot_by_name(slot_name)  # 返回指定槽位的信息

    def check_storage_slots(self, storage_name: str, slots: list) -> dict:
        # 校验指定存储库的槽位状态
        res = {}  # 存储校验结果
        slots_stored = self.get_storage_slots_via_vision(storage_name=storage_name)  # 获取存储库的槽位信息（通过视觉）
        for slot in slots:
            slot_name = slot.get("name", None)  # 获取槽位名称
            slot_status = slot.get("status", None)  # 获取槽位状态
            if slot_name and slot_status:
                slot_stored = slots_stored.get(slot_name, {})
                status_stored = slots_stored.get(slot_name, {}).get("status", "无")  # 获取存储的槽位状态
                if slot_status != status_stored:
                    res[slot_name] = {"status": [slot_status, status_stored]}  # 如果状态不一致，记录校验结果
        return res  # 返回校验结果

    def update_storage_slots(self, storage_name: str, slots: list) -> tuple:
        # 更新指定存储库的槽位状态
        res = {}  # 存储更新结果
        status = True
        for slot in slots:
            slot_name = slot.get("name", "")  # 获取槽位名称
            if slot_name:
                cnt = self.dm.update_slot_by_name(slot_name, slot)
                if cnt > 0:
                    res[slot_name] = True  # 更新成功
                else:
                    res[slot_name] = False  # 更新失败
                    status = False
            else:
                raise ValueError("No valid name")
        return status, res  # 返回更新结果


def main(args=None):
    rclpy.init(args=None)

    models = ActionModels("/workspace/src/papjia_skill/config/action_model.yaml")  # 需要显式加载原子动作模型以检查字段

    # ------------------ Flask App ------------------ #
    app = Flask(__name__)
    app.json.ensure_ascii = False
    CORS(app)
    manager = StorageManager()

    @app.route("/api/slot/<slot_name>/get", methods=["GET"])
    def api_get_slot(slot_name):
        # 获取指定槽位的信息
        slot = manager.get_slot(slot_name)
        if slot:
            return jsonify({"status": "success", "data": slot})
        return jsonify({"status": "error", "message": f"槽 {slot_name} 不存在"}), 404

    @app.route("/api/slot/get_all", methods=["GET"])
    def api_get_all_slots():
        # 获取指定槽位的信息
        slots = manager.get_all_slots()
        if slots:
            return jsonify({"status": "success", "data": slots})
        return jsonify({"status": "error", "message": f"槽不存在"}), 404

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

    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
