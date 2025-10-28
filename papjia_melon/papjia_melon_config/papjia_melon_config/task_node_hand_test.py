import os
import json
import rclpy
import math
import time
import numpy as np
from copy import deepcopy
from ament_index_python.packages import get_package_share_directory
from papjia_melon_config.actions.actions import (
    StraightMove,
    open_gripper,
    close_gripper,
    close_shears,
    open_shears,
    move_to_pose,
)
from papjia_melon_config.actions.arm_move import (
    get_plan_and_execute_waypoints_sequence,
    get_waypoint_from_config,
)
from papjia_skill.btree import BehaviorTree, BehaviorRoot, Sequence
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.action_models import ActionModels
from papjia_melon_config.actions.gps_transformer import GPStransformer
from papjia_melon_config.actions.object_detector import ObjectDetector
from papjia_skill.utils import swap_quotes, add_escape_character
from papjia_skill.atom.lookup_transform import LookupTransform
from papjia_skill.atom.pose_stamped_to_json import PoseStampedToJson
from papjia_skill.atom.pause_until_signal import PauseUntilSignal
from papjia_skill.atom.papjia_delay_async import PapjiaDelayAsync
from papjia_melon_calibration.transformations import pose_to_matrix, matrix_to_pose
from papjia_melon_config.logger import logger
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter
from papjia_skill.atom.visualization import Visualization
from papjia_skill.atom.duco_set_vel import DucoSetVel

ActionModels("/workspace/src/papjia_melon/papjia_melon_config/config/action_model.yaml")


class MelonTask:
    # 服务名称常量
    VISUALIZE_SERVICE = "/visualization_service"
    LINE_TRACING_SERVICE = "/papjia/move/line_tracing"
    STRAIGHT_MOVE_SERVICE = "/papjia/move/straight_move"
    PAUSE_UNTIL_SIGNAL_TOPIC = "pause_until_signal"

    def __init__(
        self,
        waypoint_file_path,
        gps_waypoint_file_path,
        use_tracing=False,
        use_arm=False,
        use_pause=False,
        use_device=True,
    ):
        self.waypoint_file_path = waypoint_file_path
        self.gps_waypoint_file_path = gps_waypoint_file_path
        with open(self.waypoint_file_path, "r") as f:
            self.all_waypoint_configs = json.load(f)
        self.waypoint_configs = self.all_waypoint_configs["melon"]
        self.object_detector = ObjectDetector()
        self.executor = PapjiaSkillExecutor()
        self.use_tracing = use_tracing
        self.use_arm = use_arm
        self.use_pause = use_pause
        self.use_device = use_device
        self.logger = logger
        self.camera_waypoint_names = [
            ("观测点_中", [0.0, 0.05, 0.0]),
            ("观测点_左", [0.0, 0.02, 0.0]),
            ("观测点_右", [0.0, -0.02, 0.0]),
        ]
        # 行走配置
        self.max_move_distance_once = 1.0  # 单次沿线运动最大距离
        self.min_distance_to_end = 0.3  # 机器人距离终点最小距离
        self.move_speed = 0.3  # 沿线运动速度
        self.melon_lines = [
            "丝瓜1",
            "丝瓜2",
            "丝瓜3",
            "丝瓜4",
            "苦瓜3",
            "苦瓜2",
            "苦瓜1",
        ]
        self.melon_lines = ["苦瓜4"]
        # self.keep_signal_ids = ["_抓取_", "_开始", "_结束", "_沿线", "等待GPS刷新"]
        self.keep_signal_ids = ["_抓取_", "等待GPS刷新", "_物体检测","arm_ready","move_to_object","put_object_in_box"]
        # self.keep_signal_ids = ["_抓取_", "等待GPS刷新", "_物体检测"]
        if self.use_tracing:
            self.gps_transformer = GPStransformer(self.gps_waypoint_file_path)
        else:
            self.line_length_sim = 3.0
            self.rob2start_line_sim = 0.0
            self.rob2end_line_sim = self.line_length_sim - self.rob2start_line_sim

    def gen_sequence_put_object_in_box(self):
        """
        生成将物体放入框内的机械臂运动序列
        """
        # 运动到框内
        seq = Sequence("seq_put_object_in_box")
        waypoint_names = ["ready", "放到框内_准备", "放到框内_就绪"]
        waypoints = []
        for waypoint_name in waypoint_names:
            waypoints.append(
                get_waypoint_from_config(
                    waypoint_name, self.waypoint_configs[waypoint_name]
                )
            )
        sequence_put_object_in_box = get_plan_and_execute_waypoints_sequence(waypoints)
        seq.add_child(sequence_put_object_in_box)

        if self.use_device:
            # 打开夹爪
            seq.add_child(open_gripper())
            seq.add_child(PapjiaDelayAsync(delay_duration=1.0))

        # 撤退
        waypoint_names = ["放到框内_准备", "ready"]
        waypoints = []
        for waypoint_name in waypoint_names:
            waypoints.append(
                get_waypoint_from_config(
                    waypoint_name, self.waypoint_configs[waypoint_name]
                )
            )
        sequence_return_ready_from_box = get_plan_and_execute_waypoints_sequence(
            waypoints
        )
        seq.add_child(sequence_return_ready_from_box)
        return seq

    def gen_sequence_gps_tracing(self, line_name, distance, speed=0.3):
        line_start, line_end = self.get_base_line(line_name)
        if speed < 0:
            line_end, line_start = line_start, line_end
        tracing = StraightMove(
            service_name=self.LINE_TRACING_SERVICE,
            result_timeout=60.0,
            distance=distance,
            speed=speed,
            use_integral=True,
            follow_line=True,
            line_frame="map",
            line_start=";".join([str(num) for num in line_start]),
            line_end=";".join([str(num) for num in line_end]),
        )
        seq = Sequence("seq_gps_tracing")
        seq.add_child(tracing)
        return seq

    def gen_seq_visualize_path(
        self,
        seq_name="visualize_path_seq",
        start=[0.039, -1.246, 0.0],
        end=[-0.608, 4.752, 0.0],
    ):
        # 创建一个顺序节点（Sequence），用于行为树
        seq = Sequence(
            seq_name,
        )
        # 构造可视化请求的数据结构，包含type、action和data
        data = {
            "type": "path",  # 可视化类型：路径
            "action": "add",  # 动作：添加
            "data": {
                "start": start,  # 路径起点
                "end": end,  # 路径终点
                "color": [1.0, 0.0, 0.0, 1.0],  # 颜色（红色，带透明度）
                "scale": [0.05, 0.05, 0.05],  # 尺寸
                "id": 0,  # marker id
                "frame_id": "map",  # 坐标系
                "ns": "path",  # 命名空间
            },
        }
        # 序列化为json字符串
        json_data = json.dumps(data)
        # 添加转义字符，以便BT服务器能够正确解析json_data为字符串
        json_data = add_escape_character(json_data)
        # 添加去除转义字符的节点，保证最终传递给服务端的是标准json
        seq.add_child(
            RemoveEscapeCharacter(
                json_input=json_data,
                json_result="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        # 添加可视化节点，实际调用服务
        seq.add_child(
            Visualization(
                service_name=self.VISUALIZE_SERVICE,
                data="{json_data}",  # 使用黑板变量传递json_data
            )
        )
        return seq

    def gen_seq_visualize_objs(self, seq_name="visualize_objs_seq", objs=[]):
        seq = Sequence(seq_name)
        cubes = []
        for obj in objs:
            cubes.append(
                {
                    "pose": obj["original_pose"],
                    "scale": obj["original_scale"],
                    "color": [1.0, 0.0, 0.0, 1.0],
                }
            )

        data = {
            "type": "cubes",
            "action": "add",
            "data": {
                "cubes": cubes,
                "frame_id": "base_footprint",
                "ns": "cubes",
            },
        }
        json_data = json.dumps(data)
        json_data = add_escape_character(json_data)
        seq.add_child(
            RemoveEscapeCharacter(json_input=json_data, json_result="{json_data}")
        )
        seq.add_child(
            Visualization(service_name=self.VISUALIZE_SERVICE, data="{json_data}")
        )
        return seq

    def exec_sequence(self, seq, keys=[], print_tree=False, swap_quote=False):
        tree = BehaviorTree("main_tree")
        tree.add_child(seq)
        root = BehaviorRoot()
        root.add_child(tree)
        str_root = root.to_str()
        if swap_quote:
            str_root = swap_quotes(str_root)
        if print_tree:
            print(str_root, flush=True)
        return self.executor.execute_tree(str_root, "main_tree", keys)

    def update_arm_vel(self, vel=1.0):
        seq = Sequence("seq_update_arm_vel")
        seq.add_child(DucoSetVel(vel=vel))
        res = self.exec_sequence(seq)
        return res.success

    def wait_signal(self, signal_id):
        """
        等待信号
        """
        self.logger.info(f"等待信号 {signal_id} ...")
        if not self.use_pause:
            self.logger.info(f"收到信号 {signal_id}")
            return
        flag_wait = False
        for keep_id in self.keep_signal_ids:
            if keep_id in signal_id:
                flag_wait = True
                break
        if not flag_wait:
            self.logger.info(f"信号 {signal_id} 直接通过")
            return
        while True:
            pause = PauseUntilSignal(self.PAUSE_UNTIL_SIGNAL_TOPIC, signal_id=signal_id)
            seq = Sequence("seq_wait_signal")
            seq.add_child(pause)
            res = self.exec_sequence(seq)
            if res.success:
                self.logger.info(f"收到信号 {signal_id}")
                break
            else:
                self.logger.error(f"错误的信号，信号id为 {signal_id}")
                time.sleep(1)

    def straight_move_distance(self, distance, speed=0.1):
        if not self.use_tracing:
            self.logger.info(f"不使用寻迹，直接跳过直线运动 {distance:.2f} 米")
            return True
        self.logger.info(f"准备直线运动 {distance:.2f} 米 [非巡线]")
        seq = Sequence("seq_straight_move_distance")
        seq.add_child(
            StraightMove(
                service_name=self.STRAIGHT_MOVE_SERVICE,
                result_timeout=60.0,
                distance=distance,
                speed=speed,
                use_integral=True,
                follow_line=False,
            )
        )
        res = self.exec_sequence(seq)
        return res.success

    def gps_tracing_distance(self, line_name, distance, speed=0.3):
        """
        沿着线运动
        """
        if not self.use_tracing:
            if speed > 0:
                self.rob2start_line_sim += distance
                self.rob2end_line_sim -= distance
            else:
                self.rob2start_line_sim -= distance
                self.rob2end_line_sim += distance
            self.logger.info(
                f"模拟运动 {distance:.2f} 米，现在距离起点 {self.rob2start_line_sim:.2f} 米， 距离终点 {self.rob2end_line_sim:.2f} 米"
            )
            return True
        seq = self.gen_sequence_gps_tracing(line_name, distance, speed)
        res = self.exec_sequence(seq)
        return res.success

    def get_tf_pose(self, parent_frame="map", child_frame="base_footprint"):
        """
        获取机器人位姿
        """
        trans = LookupTransform(
            parent_frame=parent_frame, child_frame=child_frame, pose="{pose}"
        )
        trans_json = PoseStampedToJson(pose="{pose}", json_result="{json_pose}")
        seq = Sequence("seq_get_tf_pose")
        seq.add_child(trans)
        seq.add_child(trans_json)
        res = self.exec_sequence(seq, keys=["json_pose"])
        pose = json.loads(json.loads(res.result).get("json_pose", "None"))
        return pose

    def get_robot2line_distance(
        self, line_name, to_start=True, parent_frame="map", child_frame="base_footprint"
    ):
        """
        获取机器人到线的距离
        """
        if not self.use_tracing:
            if to_start:
                return self.rob2start_line_sim
            else:
                return self.rob2end_line_sim
        pose = self.get_tf_pose(parent_frame, child_frame)
        position = [
            pose["pose"]["position"]["x"],
            pose["pose"]["position"]["y"],
            pose["pose"]["position"]["z"],
        ]
        line_start, line_end = self.get_base_line(line_name)
        # 计算机器人到路径点的距离
        if to_start:
            return math.sqrt(
                (position[0] - line_start[0]) ** 2 + (position[1] - line_start[1]) ** 2
            )
        else:
            return math.sqrt(
                (position[0] - line_end[0]) ** 2 + (position[1] - line_end[1]) ** 2
            )

    def get_base_line(self, line_name):
        """
        获取基站到线的距离，返回处理后的位姿数据
        """
        # 获取位姿数据
        pose_base2gps = self.get_tf_pose(
            parent_frame="gps_link", child_frame="base_footprint"
        )
        pose_gps2map = self.get_tf_pose(parent_frame="map", child_frame="gps_link")
        self.logger.info(
            f"pose_base2gps: {pose_base2gps['pose']['position']}, {pose_base2gps['pose']['orientation']}"
        )
        self.logger.info(
            f"pose_gps2map: {pose_gps2map['pose']['position']}, {pose_gps2map['pose']['orientation']}"
        )

        # 获取线的起点和终点
        line_start, line_end = self.gps_transformer.get_gps_line(line_name)
        self.logger.info(f"line_start_gps: {line_start}")
        self.logger.info(f"line_end_gps: {line_end}")

        matrix_base2gps = pose_to_matrix(
            [
                pose_base2gps["pose"]["position"]["x"],
                pose_base2gps["pose"]["position"]["y"],
                pose_base2gps["pose"]["position"]["z"],
                pose_base2gps["pose"]["orientation"]["x"],
                pose_base2gps["pose"]["orientation"]["y"],
                pose_base2gps["pose"]["orientation"]["z"],
                pose_base2gps["pose"]["orientation"]["w"],
            ]
        )
        matrix_gps2map_start = pose_to_matrix(
            [
                line_start[0],
                line_start[1],
                line_start[2],
                pose_gps2map["pose"]["orientation"]["x"],
                pose_gps2map["pose"]["orientation"]["y"],
                pose_gps2map["pose"]["orientation"]["z"],
                pose_gps2map["pose"]["orientation"]["w"],
            ]
        )
        matrix_gps2map_end = pose_to_matrix(
            [
                line_end[0],
                line_end[1],
                line_end[2],
                pose_gps2map["pose"]["orientation"]["x"],
                pose_gps2map["pose"]["orientation"]["y"],
                pose_gps2map["pose"]["orientation"]["z"],
                pose_gps2map["pose"]["orientation"]["w"],
            ]
        )
        matrix_line_start = np.dot(matrix_gps2map_start, matrix_base2gps)
        matrix_line_end = np.dot(matrix_gps2map_end, matrix_base2gps)
        pose_line_start = matrix_to_pose(matrix_line_start)
        pose_line_end = matrix_to_pose(matrix_line_end)
        self.logger.info(f"line_start_base: {pose_line_start}")
        self.logger.info(f"line_end_base: {pose_line_end}")
        return [pose_line_start[0], pose_line_start[1], 0.0], [
            pose_line_end[0],
            pose_line_end[1],
            0.0,
        ]

    def visualize_path(self, start=[0.039, -1.246, 0.0], end=[-0.608, 4.752, 0.0]):
        seq = self.gen_seq_visualize_path(start=start, end=end)
        res = self.exec_sequence(seq)
        return res.success

    def visualize_objs(self, objs=[]):
        seq = self.gen_seq_visualize_objs(objs=objs)
        res = self.exec_sequence(seq)
        return res.success

    def detect_objects(self, max_num=10, min_score=0.4):
        """
        检测物体并过滤物体
        """
        seq = self.object_detector.gen_sequence_detect_json_objects(
            min_score=min_score, key="json_objects"
        )
        res = self.exec_sequence(seq, keys=["json_objects"], print_tree=True)
        objects = json.loads(json.loads(res.result).get("json_objects", "[]"))
        return objects

    def move_to_object(
        self,
        object,
        pick_roll=0.0,
        pick_pitch=0.0,
        pick_yaw=0.0,
        planner="ptp",
        ik_frame="gripper",
        frame_id="base_footprint",
    ):
        """
        移动到物体
        """
        self.logger.info(f"准备移动到物体 {object}")
        seq_object = self.object_detector.gen_action_dict2object(
            object, key="filtered_object"
        )
        seq_move_arm = move_to_pose(
            planner=planner,
            pick_roll=pick_roll,
            pick_pitch=pick_pitch,
            pick_yaw=pick_yaw,
            ik_frame=ik_frame,
            frame_id=frame_id,
            filtered_object="filtered_object",
        )
        seq = Sequence("seq_object_and_grasp")
        seq.add_child(seq_object)
        seq.add_child(seq_move_arm)
        res = self.exec_sequence(seq)
        self.logger.info(f"Grasp pose before IK: roll={pick_roll}, pitch={pick_pitch}, yaw={pick_yaw}")
        return res.success

    def move_to_waypoint(self, waypoint_name):
        """
        移动到观测点
        """
        if not self.use_arm:
            self.logger.info(f"不使用手臂，直接跳过手臂移动 {waypoint_name}")
            return True
        self.logger.info(f"准备移动到 {waypoint_name}")
        waypoint = get_waypoint_from_config(
            waypoint_name, self.waypoint_configs[waypoint_name]
        )
        sequence_to_waypoint = get_plan_and_execute_waypoints_sequence([waypoint])
        res = self.exec_sequence(sequence_to_waypoint)
        return res.success

    def open_device(self):
        """
        打开设备
        """
        if not self.use_device:
            return True
        seq = Sequence("open_device")
        seq.add_child(open_shears())
        seq.add_child(open_gripper())
        res = self.exec_sequence(seq)
        return res.success

    def grasp_object(self):
        """
        夹取物体
        """
        if not self.use_device:
            return True
        sequence_grasp_action = Sequence("grasp_action")
        # 闭合夹爪
        sequence_grasp_action.add_child(close_gripper())
        # 闭合剪刀
        sequence_grasp_action.add_child(close_shears())
        # # 等待闭合完成
        sequence_grasp_action.add_child(PapjiaDelayAsync(delay_duration=3.5))
        # 打开剪刀
        sequence_grasp_action.add_child(open_shears())
        res = self.exec_sequence(sequence_grasp_action)
        return res.success

    def put_object_in_box(self):
        """
        将物体放入框内
        """
        seq = self.gen_sequence_put_object_in_box()
        res = self.exec_sequence(seq)
        return res.success

    def test_detect_and_grasp_and_put_object(
        self, with_vision=True, waypoint_name="观测点_中" ##
    ):
        """
        测试检测物体、夹取物体、放入框内
        """
        self.wait_signal(signal_id="arm_ready")
        if not self.move_to_waypoint(waypoint_name="ready"):
            self.logger.error("移动手臂到准备点位失败")
            return

        self.open_device()

        self.wait_signal(signal_id=waypoint_name)
        if not self.move_to_waypoint(waypoint_name=waypoint_name):
            self.logger.error("移动手臂到准备点位失败")
            return

        if with_vision:
            objects = self.detect_objects()
            if not objects:
                self.logger.warning("未检测到物体")
                return
            self.logger.info(f"检测到的物体 {objects}")

            object, need_move = self.object_detector.filter_and_select_object(
                objects, obs_name=waypoint_name
            )
            if not object:
                self.logger.warning("未找到可夹取的物体")
                return
            # if need_move:
            #     self.logger.warning(f"物体 {object['pose'][0:3]} 太远了，无法夹取")
            #     return
            self.visualize_objs(objs=[object])
        else:
            object = {}
            object["category"] = "melon"
            object["pose"] = [
                1.0,
                0.22,
                1.40,
                -0.012023540567983217,
                -0.12398568312323482,
                0.10915125076825744,
                0.9861891245133458,
            ]
            object["scale"] = [0.03, 0.03, 0.3]

        self.logger.info(f"需要移动到物体 {object}")
        self.wait_signal(signal_id="move_to_object")
        # to_do
        # pick_roll、pick_pitch、pick_yaw等参考
        # 补偿运动向上【pick_pitch=-0.252】
        # object["pose"][0] -= 0.1

        '''
        offsets = camera_waypoint_names[waypoint_name]
        object["pose"][0] += offsets[0]
        object["pose"][1] += offsets[1]
        object["pose"][2] += offsets[2]
        pick_yaw = math.atan2(object["pose"][1], object["pose"][0])
        self.move_to_object(
            object,
            pick_roll=0.0,
            pick_pitch=-0.252,
            pick_yaw=pick_yaw,
            planner="lin",
            frame_id="base_footprint",
            ik_frame="gripper",
        )
        '''

        if not self.move_to_object(
            object,
            pick_roll=-0.057, 
            pick_pitch=-0.252, #-0.252
            pick_yaw=0.055, 
            planner="lin",
            frame_id="base_footprint",
            ik_frame="gripper",
        ):
            self.logger.error("移动到物体失败")
            return

        self.logger.info("夹取物体")
        self.grasp_object()

        self.logger.info("放入框内")
        self.wait_signal(signal_id="put_object_in_box")
        self.put_object_in_box()

    def test_pose_for_grasp_object(
        self,
        waypoint_name="观测点_中",
        init_pose=[0.9, 0.0, 1.40, 0, 0, 0, 1.0],
        rangex=[0.3, 1.0],
        rangey=[-1.0, 1.0],
        z=1.65,
    ):
        """
        测试检测抓取能够达到的位姿
        """
        self.wait_signal(signal_id="arm_ready")
        if not self.move_to_waypoint(waypoint_name="ready"):
            self.logger.error("移动手臂到准备点位失败")
            return
        self.wait_signal(signal_id=waypoint_name)
        if not self.move_to_waypoint(waypoint_name=waypoint_name):
            self.logger.error(f"移动手臂到 {waypoint_name} 失败")
            return
        self.wait_signal(signal_id=f"{waypoint_name}_抓取位姿统计")
        all_success_poses = []
        object = {}
        object["category"] = "melon"
        object["pose"] = deepcopy(init_pose)
        object["scale"] = [0.04, 0.04, 0.4]
        stepx = 0.05
        stepy = 0.02
        total_points = len(np.arange(rangex[0], rangex[1], stepx)) * len(
            np.arange(rangey[0], rangey[1], stepy)
        )
        current_point = 0
        for x in np.arange(rangex[0], rangex[1], stepx):
            for y in np.arange(rangey[0], rangey[1], stepy):
                if not self.move_to_waypoint(waypoint_name=waypoint_name):
                    self.logger.error(f"移动到 {waypoint_name} 失败")
                    raise Exception(f"移动到 {waypoint_name} 失败")  # 此问题不应出现
                object["pose"] = deepcopy(init_pose)
                object["pose"][0] += x
                object["pose"][1] += y
                object["pose"][2] = z
                self.wait_signal(signal_id="move_to_object")
                pick_yaw = math.atan2(object["pose"][1], object["pose"][0])
                if not self.move_to_object(
                    object,
                    pick_roll=0.0,
                    pick_pitch=-0.252,
                    pick_yaw=pick_yaw,
                    planner="lin",
                    frame_id="base_footprint",
                    ik_frame="gripper",
                ):
                    self.logger.error("移动到物体失败")
                else:
                    self.logger.info("移动到物体成功")
                    if not self.move_to_waypoint(waypoint_name="ready"):
                        self.logger.error("返回 ready 失败")
                        raise Exception("返回 ready 失败")  # 此问题不应出现
                    all_success_poses.append(object["pose"])
                # 打印当前进度（百分比）
                current_point += 1
                progress = (current_point / total_points) * 100
                self.logger.info(f"当前进度: {progress:.5f}%")
                time.sleep(0.05)
        # 保存为json文件
        with open(f"data/{waypoint_name}_success.json", "w") as f:
            json.dump(all_success_poses, f)

    def test_gps_tracing(self, line_name="测试"):
        """
        测试沿着线运动
        """
        self.logger.info("开始测试沿线前进运动")
        dist2end = self.get_robot2line_distance(line_name, to_start=False)
        self.logger.info(f"机器人到线终点距离: {dist2end}")
        self.wait_signal(signal_id=f"{line_name}_前进")
        self.gps_tracing_distance(line_name, distance=dist2end, speed=0.3)
        time.sleep(1.5)  # 等待1.5秒, 等待GPS刷新
        dist2end = self.get_robot2line_distance(line_name, to_start=False)
        self.logger.info(f"机器人到线终点距离: {dist2end}")

        self.logger.info("开始测试沿线后退运动")
        dist2start = self.get_robot2line_distance(line_name, to_start=True)
        self.logger.info(f"机器人到线起点距离: {dist2start}")
        self.wait_signal(signal_id=f"{line_name}_后退")
        self.gps_tracing_distance(line_name, distance=dist2start, speed=-0.3)
        time.sleep(1.5)
        dist2start = self.get_robot2line_distance(line_name, to_start=True)
        self.logger.info(f"机器人到线起点距离: {dist2start}")

    def test_tracing_line_return(self, line_name):
        """
        测试沿线返回
        """
        while True:
            dist2start = self.get_robot2line_distance(line_name, to_start=True)
            self.logger.info(f"剩余返回距离: {dist2start}米")
            if dist2start < self.max_move_distance_once:
                self.logger.info(f"准备返回距离{dist2start}米")
                self.wait_signal(signal_id=f"{line_name}_沿线返回")
                self.gps_tracing_distance(
                    line_name, distance=dist2start, speed=-self.move_speed
                )
                time.sleep(2.0)
                dist2start = self.get_robot2line_distance(line_name, to_start=True)
                self.logger.info(f"返回结束，机器人到线起点距离: {dist2start}")
                break
            self.logger.info(f"准备返回距离: {self.max_move_distance_once}米")
            self.wait_signal(signal_id=f"{line_name}_沿线返回")
            self.gps_tracing_distance(
                line_name, distance=self.max_move_distance_once, speed=-self.move_speed
            )
            self.logger.info("继续返回")

    def test_single_line_task(self, line_name):
        """
        测试单行任务
        """
        if self.use_tracing:
            line_start, line_end = self.get_base_line(line_name)
            self.visualize_path(start=line_start[0:3], end=line_end[0:3])

        flag_tracing_move = False
        move_distance = self.max_move_distance_once

        while True:
            if self.use_tracing and flag_tracing_move:
                self.wait_signal(signal_id="导航准备")
                if not self.move_to_waypoint(waypoint_name="ready"):
                    self.logger.error("移动手臂到准备点位失败")
                if not self.move_to_waypoint(waypoint_name="导航准备"):
                    self.logger.error("移动手臂到导航准备点位失败")
                self.straight_move_distance(distance=0.05, speed=0.02)
                self.wait_signal(signal_id="等待GPS刷新")
                dist2end = self.get_robot2line_distance(line_name, to_start=False)
                if dist2end < self.min_distance_to_end:  # 返回
                    self.logger.warning(
                        f"机器人距离终点 {line_name} 位置小于 {self.min_distance_to_end:.2f} 米，准备返回"
                    )
                    self.test_tracing_line_return(line_name)
                    self.logger.info(f"返回 {line_name}起点 成功")
                    break
                # 前进
                move_distance = min(
                    move_distance, min(self.max_move_distance_once, dist2end)
                )
                self.logger.info(f"准备前进 {move_distance:.2f} 米")
                self.wait_signal(signal_id=f"{line_name}_沿线行走")
                self.gps_tracing_distance(
                    line_name, distance=move_distance, speed=self.move_speed
                )
                self.logger.info(f"前进 {move_distance:.2f} 米")
                flag_tracing_move = False
                self.wait_signal(signal_id="arm_ready")
                if not self.move_to_waypoint(waypoint_name="ready"):
                    self.logger.error("移动手臂到准备点位失败")
            if not self.use_arm:
                flag_tracing_move = True
                continue
            # 移动到观测位姿
            move_distance = self.max_move_distance_once
            for waypoint_name, offsets in self.camera_waypoint_names:
                self.move_to_waypoint(waypoint_name="ready")
                while True:  # 循环检测
                    self.wait_signal(signal_id=f"{line_name}_{waypoint_name}")
                    if not self.move_to_waypoint(waypoint_name=waypoint_name):
                        self.logger.error(f"移动到观测位姿 {waypoint_name} 失败")
                        raise Exception("移动到观测位姿失败")  # 此问题不应出现
                    self.logger.info(f"移动到观测位姿 {waypoint_name} 成功")
                    self.wait_signal(signal_id=f"{line_name}_物体检测")
                    objects = self.detect_objects()
                    if not objects:
                        # 没有物体，需要移动
                        flag_tracing_move = True
                        move_distance = min(move_distance, self.max_move_distance_once)
                        self.logger.warning(
                            f"{waypoint_name} 没有检测到物体，需要移动 {move_distance:.2f} 米"
                        )
                        break
                    for obj in objects:
                        self.logger.info(f"{obj['category']}: {obj['pose']}")
                    # self.wait_signal(signal_id=f"{line_name}_物体过滤")
                    object, need_move_dist = (
                        self.object_detector.filter_and_select_object(
                            objects, obs_name=waypoint_name
                        )
                    )
                    if not object:  # 没有找到可抓取的物体，需要移动
                        flag_tracing_move = True
                        move_distance = min(move_distance, need_move_dist)
                        self.logger.warning(
                            f"{waypoint_name} 没有找到可抓取物体，需要移动 {need_move_dist:.2f} 米，最少需要移动 {move_distance:.2f} 米"
                        )
                        break
                    self.logger.info(f"找到可抓取物体: {object['category']}")
                    self.logger.info(f" 物体抓取位姿: {object['pose']}")
                    self.visualize_objs(objs=[object])
                    self.wait_signal(signal_id=f"{line_name}_抓取_移动手臂")
                    object["pose"][0] += offsets[0]   ###################################这里改偏移量
                    object["pose"][1] += offsets[1]
                    object["pose"][2] += offsets[2]
                    pick_yaw = math.atan2(object["pose"][1], object["pose"][0])
                    if not self.move_to_object(
                        object,
                        pick_roll=0.0,
                        pick_pitch=-0.252,
                        pick_yaw=pick_yaw,
                        planner="lin",
                        frame_id="base_footprint",
                        ik_frame="gripper",
                    ):
                        self.logger.error("移动手臂夹取物体失败")
                        # raise Exception("移动手臂夹取物体失败")  # 此问题不应出现
                        break
                    # 抓取物体
                    self.logger.info("移动手臂成功，准备夹取物体")
                    self.wait_signal(signal_id=f"{line_name}_抓取_夹取")
                    self.grasp_object()
                    # 放入框内
                    self.logger.info("夹取物体成功")
                    self.wait_signal(signal_id=f"{line_name}_抓取_放瓜")
                    if not self.put_object_in_box():
                        self.logger.error("放入框内失败")
                        raise Exception("放入框内失败")  # 此问题不应出现
                    self.logger.info("放入框内成功")
                    flag_tracing_move = False

    def test_all_task(self):
        """
        测试所有任务
        """
        if self.use_arm:
            self.update_arm_vel(vel=1.5)
            self.wait_signal(signal_id="arm_ready")
            if not self.move_to_waypoint(waypoint_name="ready"):
                self.logger.error("移动手臂到准备点位失败")
                return
        for line_name in self.melon_lines:
            self.logger.info(f"开始执行 {line_name} 任务")
            # 测试单行任务
            self.wait_signal(signal_id=f"{line_name}_开始")
            self.test_single_line_task(line_name)
            # 等待信号
            self.wait_signal(signal_id=f"{line_name}_结束")



    def test_detect_arm(
            self, with_vision=True, waypoint_name="观测点_中"
        ):
            """
            测试检测物体、夹取物体、放入框内
            """
            self.wait_signal(signal_id="arm_ready")
            if not self.move_to_waypoint(waypoint_name="ready"):
                self.logger.error("移动手臂到准备点位失败")
                return

            self.open_device()

            # self.wait_signal(signal_id=waypoint_name)
            if not self.move_to_waypoint(waypoint_name=waypoint_name):
                self.logger.error("移动手臂到准备点位失败")
                return

            if with_vision:
                objects = self.detect_objects()
                if not objects:
                    self.logger.warning("未检测到物体")
                    return
                self.logger.info(f"检测到的物体 {objects}")

                object, need_move = self.object_detector.filter_and_select_object(
                    objects, obs_name=waypoint_name
                )
                if not object:
                    self.logger.warning("未找到可夹取的物体")
                    return
                # if need_move:
                #     self.logger.warning(f"物体 {object['pose'][0:3]} 太远了，无法夹取")
                #     return
                self.visualize_objs(objs=[object])
            else:
                object = {}
                object["category"] = "melon"
                object["pose"] = [
                    1.0,
                    0.22,
                    1.40,
                    -0.012023540567983217,
                    -0.12398568312323482,
                    0.10915125076825744,
                    0.9861891245133458,
                ]
                object["scale"] = [0.03, 0.03, 0.3]

            self.logger.info(f"需要移动到物体 {object}")
            ####################这里暂停一下可以保持机械臂观望姿态趁机采取图像#################################
            # self.wait_signal(signal_id="move_to_object")
            # to_do
            # pick_roll、pick_pitch、pick_yaw等参考
            # 补偿运动向上【pick_pitch=-0.252】
   
            # offsets = self.camera_waypoint_names[waypoint_name]
            # object["pose"][0] += offsets[0]
            # object["pose"][1] += offsets[1]
            # object["pose"][2] += offsets[2]

            # object["pose"][0] -= 0.2
            if not self.move_to_object(
                object,
                pick_roll=-0.057, #-0.057
                pick_pitch=-0.252, #-0.252
                pick_yaw=0.055, #0.055
                planner="lin",
                frame_id="base_footprint",
                ik_frame="gripper",
            ):
                self.logger.error("移动到物体失败")
                return
            ####################这里暂停一下可以保持机械臂抓取姿态趁机量取误差#################################
            self.logger.info("夹取物体")
            self.grasp_object()

            self.logger.info("放入框内")
            self.wait_signal(signal_id="put_object_in_box")
            self.put_object_in_box()


    def test_grasp_pose(
            self, with_vision=True, waypoint_name="观测点_中"
        ):
            """
            测试检测物体、夹取物体、放入框内
            """
            self.wait_signal(signal_id="arm_ready")
            if not self.move_to_waypoint(waypoint_name="ready"):
                self.logger.error("移动手臂到准备点位失败")
                return

            self.open_device()

            self.wait_signal(signal_id=waypoint_name)
            if not self.move_to_waypoint(waypoint_name=waypoint_name):
                self.logger.error("移动手臂到准备点位失败")
                return

            if with_vision:
                objects = self.detect_objects()
                if not objects:
                    self.logger.warning("未检测到物体")
                    return
                self.logger.info(f"检测到的物体 {objects}")

                object, need_move = self.object_detector.filter_and_select_object(
                    objects, obs_name=waypoint_name
                )
                if not object:
                    self.logger.warning("未找到可夹取的物体")
                    return
                # if need_move:
                #     self.logger.warning(f"物体 {object['pose'][0:3]} 太远了，无法夹取")
                #     return
                self.visualize_objs(objs=[object])
            else:
                object = {}
                object["category"] = "melon"
                object["pose"] = [
                    1.0,
                    0.22,
                    1.40,
                    -0.012023540567983217,
                    -0.12398568312323482,
                    0.10915125076825744,
                    0.9861891245133458,
                ]
                object["scale"] = [0.03, 0.03, 0.3]

            self.logger.info(f"需要移动到物体 {object}")
            ####################这里暂停一下可以保持机械臂观望姿态趁机采取图像#################################
            self.wait_signal(signal_id="move_to_object")
            # to_do
            # pick_roll、pick_pitch、pick_yaw等参考
            # 补偿运动向上【pick_pitch=-0.252】
   
            # offsets = self.camera_waypoint_names[waypoint_name]
            # object["pose"][0] += offsets[0]
            # object["pose"][1] += offsets[1]
            # object["pose"][2] += offsets[2]

            object["pose"][0] -= 0.1
            object["pose"][1] -= 0.5
            if not self.move_to_object(
                object,
                pick_roll=-0.057,
                pick_pitch=-0.252, #-0.252
                pick_yaw=0.055,
                planner="lin",
                frame_id="base_footprint",
                ik_frame="gripper",
            ):
                self.logger.error("移动到物体失败")
                return
            ####################这里暂停一下可以保持机械臂抓取姿态趁机量取误差#################################
            self.logger.info("夹取物体")
            self.grasp_object()








if __name__ == "__main__":
    rclpy.init()
    waypoint_file_path = (
        "/workspace/src/papjia_melon/papjia_melon_config/config/waypoint_configs.json"
    )
    gps_waypoint_file_path = "/workspace/src/papjia_melon/papjia_melon_config/config/gps_waypoints_modified.yaml"
    task = MelonTask(
        waypoint_file_path,
        gps_waypoint_file_path,
        use_tracing=False,
        use_arm=True,
        use_pause=True,
        use_device=False, #True
    )

    # task.detect_objects()
    task.test_detect_arm(with_vision=True)
    # task.test_pose_for_grasp_object()
    # task.move_to_waypoint(waypoint_name="ready")
    # 测试检测并抓取物体
    # task.test_detect_and_grasp_and_put_object(with_vision=True)
    # 测试所有任务
    # task.put_object_in_box()
  
    # task.test_all_task()
    # n = 10
    # while n > 0:
        # task.move_to_waypoint(waypoint_name="ready")
    #     task.move_to_waypoint(waypoint_name="观测点_左")
    #     task.move_to_waypoint(waypoint_name="ready")
    #     task.move_to_waypoint(waypoint_name="观测点_左")
    #     task.move_to_waypoint(waypoint_name="ready")
    #     task.put_object_in_box()
    #     n -= 1
    # task.move_to_waypoint(waypoint_name="ready")
    # task.move_to_waypoint(waypoint_name="观测点_右")
    # task.open_device()
    # task.grasp_object()

    # waypoint_names = [
    #     "观测点_中",
    #     "观测点_左",
    #     "观测点_右",
    # ]
    # poses = [
    #     [0.873, 0.000, 1.432, 0.000, -0.188, -0.000, 0.982],
    #     [0.637, 0.765, 1.503, 0.065, -0.118, 0.140, 0.981],
    #     [0.880, -0.664, 1.557, -0.004, -0.205, -0.073, 0.976],
    # ]
    # ranges = [
    #     [[0.4, 0.9], [-0.75, 0.75]],
    #     [[0.4, 0.70], [-0.5, 0.5]],
    #     [[0.4, 0.70], [-0.5, 0.5]],
    # ]
    # for name, pose, range in zip(waypoint_names, poses, ranges):
    #     task.test_pose_for_grasp_object(
    #         waypoint_name=name,
    #         init_pose=pose,
    #         rangex=range[0],
    #         rangey=range[1],
    #         z=1.75,  ## 绝不可高于这个值
    #     )

    rclpy.shutdown()