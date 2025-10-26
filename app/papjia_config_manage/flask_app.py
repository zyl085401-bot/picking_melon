from flask import Flask, jsonify, request
from flask_cors import CORS
# import roslibpy
# import roslibpy.actionlib
import rclpy
import os
import json
import threading
from robot_utils import RobotUtils
from arm_move import JointWaypoint, CartWaypoint
# client = roslibpy.Ros(host='10.13.18.151', port=9090)
# client.run()

rclpy.init()
app = Flask(__name__)

robot_utils = RobotUtils()

waypoint_config_filepath = os.getenv('WAYPOINT_CONFIG_FILEPATH', os.path.join(os.path.dirname(__file__), 'szyj_waypoint_configs.json'))
task_config_filepath = os.getenv('TASK_CONFIG_FILEPATH', os.path.join(os.path.dirname(__file__), 'szyj_task_configs.json'))
print(waypoint_config_filepath)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


@app.route("/", methods=['GET'])
def ping():
    return jsonify('pong'), 200
    
@app.route("/waypoints/get_all", methods=['GET'])
def get_all_waypoints():
    try:
        print(f"获取所有路径点信息：{waypoint_config_filepath}")
        with open(waypoint_config_filepath, 'r') as file:
            data = json.load(file)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_joint_states/<arm_group>", methods=['GET'])
def get_joint_states(arm_group: str):
    joint_states = robot_utils.get_joint_state()
    filter_joint_states = {k: v for k, v in joint_states.items() if arm_group in k}
    return jsonify(filter_joint_states), 200

@app.route("/waypoints/update/<object_type>", methods=['POST'])
def update_waypoint(object_type: str):
    try:
        waypoint = request.json
        print(waypoint)
        with open(waypoint_config_filepath, 'r') as file:
            data = json.load(file)
        
        if object_type not in data:
            return jsonify({"error": f"物体类型 {object_type} 不存在."}), 400
        
        object_waypoints = data[object_type]
        if waypoint['name'] not in object_waypoints:
            return jsonify({"error": f"路径点 {waypoint['name']} 不存在."}), 400
        
        if waypoint['type'] == 'joint':
            object_waypoints[waypoint['name']] = {
                "group": waypoint["armGroup"],
                "planner": waypoint["planner"],
                "preWaypoint": waypoint["preWaypoint"],
                "joint_names": waypoint["joint_names"],
                "joint_values": waypoint["joint_values"],
                "description": waypoint["description"],
                "type": waypoint["type"]
            }
        else:
            object_waypoints[waypoint['name']] = {
                "group": waypoint["armGroup"],
                "planner": waypoint["planner"],
                "preWaypoint": waypoint["preWaypoint"],
                "ik_frame": waypoint["ik_frame"],
                "frame_id": waypoint["frame_id"],
                "pose": waypoint["pose"],
                "joint_names": waypoint["joint_names"],
                "joint_values": waypoint["joint_values"],
                "description": waypoint["description"],
                "type": waypoint["type"]
            }
            
        with open(waypoint_config_filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return jsonify({"message": "Waypoints updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/waypoints/add/<object_type>", methods=['POST'])
def add_waypoint(object_type: str):
    try:
        waypoint = request.json
        with open(waypoint_config_filepath, 'r') as file:
            data = json.load(file)
        
        if object_type not in data:
            return jsonify({"error": f"物体类型 {object_type} 不存在."}), 400
        
        object_waypoints = data[object_type]
        if waypoint['name'] in object_waypoints:
            return jsonify({"error": f"Waypoint with name {waypoint['name']} already exists."}), 400
        
        if waypoint['type'] == 'joint':
            # 临时处理：根据手臂组生成关节名称
            waypoint['joint_names'] = [
                waypoint['armGroup'] + '_' + 'joint' + str(i) for i in range(1, 7)
            ]
            object_waypoints[waypoint['name']] = {
                "group": waypoint["armGroup"],
                "planner": waypoint["planner"],
                "preWaypoint": waypoint["preWaypoint"],
                "joint_names": waypoint["joint_names"],
                "joint_values": waypoint["joint_values"],
                "description": waypoint["description"],
                "type": waypoint["type"]
            }
        else:
            object_waypoints[waypoint['name']] = {
                "group": waypoint["armGroup"],
                "planner": waypoint["planner"],
                "preWaypoint": waypoint["preWaypoint"],
                "ik_frame": waypoint["ik_frame"],
                "frame_id": waypoint["frame_id"],
                "pose": waypoint["pose"],
                "description": waypoint["description"],
                "type": waypoint["type"]
            }
        with open(waypoint_config_filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            return jsonify({"message": "Waypoints added successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/waypoints/delete/<object>/<name>", methods=['DELETE'])
def delete_waypoint(object: str, name: str):
    try:
        with open(waypoint_config_filepath, 'r') as file:
            data = json.load(file)
        if object not in data:
            return jsonify({"error": f"物体类型 {object} 不存在."}), 400
        
        object_waypoints = data[object]
        if name not in object_waypoints:
            return jsonify({"error": f"路径点 {name} 不存在."}), 400
        del object_waypoints[name]
        
        with open(waypoint_config_filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return jsonify({"message": "Waypoints deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/waypoints/move", methods=['POST'])
def move_to_waypoint():
    waypoint_config = request.json
    waypoints = []
    if waypoint_config['type'] == 'joint':
        waypoint = JointWaypoint(
            waypoint_name=waypoint_config['name'],
            joint_names=waypoint_config['joint_names'],
            joint_values=waypoint_config['joint_values'],
            group=waypoint_config['armGroup'],
            planner=waypoint_config['planner'],
            max_velocity_scaling_factor=waypoint_config['speed'],
            max_acceleration_scaling_factor=waypoint_config['acceleration']
        )
        waypoints.append(waypoint)
    else:
        waypoint = CartWaypoint(
            waypoint_name=waypoint_config['name'],
            position=waypoint_config['pose'][:3],
            orientation=waypoint_config['pose'][3:],
            group=waypoint_config['armGroup'],
            frame_id=waypoint_config['frame_id'],
            ik_frame=waypoint_config['ik_frame'],
            planner=waypoint_config['planner'],
            max_velocity_scaling_factor=waypoint_config['speed'],
            max_acceleration_scaling_factor=waypoint_config['acceleration']
        )
        waypoints.append(waypoint)
    print(waypoints)
    move_thread = threading.Thread(target=robot_utils.plan_and_execute_arm_waypoints, args=(waypoints,))
    move_thread.start()
    return jsonify({"message": "Moving to the specified waypoint."})

@app.route("/waypoints/move/status", methods=['GET'])
def get_move_status():
    status = robot_utils.get_move_status()
    return jsonify({"status": status})

# 保存任务配置
@app.route("/task/save", methods=['POST'])
def save_task_config():
    try:
        config = request.json
        with open(task_config_filepath, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
        return jsonify({"message": "Task config saved successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取所有任务配置
@app.route("/task/list", methods=['GET'])
def get_all_task_configs():
    try:
        with open(task_config_filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取指定任务配置
@app.route("/task/<name>", methods=['GET'])
def get_task_config(name):
    try:
        with open(task_config_filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 输出所有任务名称，帮助调试
        available_tasks = list(data.keys())
        print(f"Available tasks: {available_tasks}")

        if name not in data:
            return jsonify({"error": f"Task config {name} not found. Available tasks: {available_tasks}"}), 404
        return jsonify(data[name]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False)
    rclpy.shutdown()