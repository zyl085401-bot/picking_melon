import json
import rclpy

from papjia_melon_config.actions.actions import *
from papjia_melon_config.actions.arm_move import get_plan_and_execute_waypoints_sequence, get_waypoint_from_config

from papjia_skill.btree import BehaviorTree, BehaviorRoot, Sequence
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.action_models import ActionModels
ActionModels("/workspace/src/papjia_melon/papjia_melon_config/config/action_model.yaml")


class MelonTask:
    def __init__(self):
        waypoint_file_path = "/workspace/src/papjia_melon/papjia_melon_config/config/waypoint_configs.json"
        with open(waypoint_file_path, "r") as f:
            self.all_waypoint_configs = json.load(f)
        self.waypoint_configs = self.all_waypoint_configs['melon']
        self.executor = PapjiaSkillExecutor()

    def gen_sequence_go_to_detect(self, waypoint_name: str):
        """
        生成前往观测点的机械臂运动序列
        """
        waypoint_detect = get_waypoint_from_config(waypoint_name, self.waypoint_configs[waypoint_name])
        sequence_go_to_detect = get_plan_and_execute_waypoints_sequence(
            [waypoint_detect]
        )
        return sequence_go_to_detect
    
    def gen_sequence_detect_and_grasp_object(self, pick_roll=0.0, pick_pitch=0.0, pick_yaw=0.0):
        """
        生成检测并抓取物体的机械臂运动序列
        """
        sequence_detect_and_grasp_object = detect_and_grasp_object(
            max_num=10, 
            min_score=0.5, 
            planner="lin", 
            max_velocity_scaling_factor=0.5, 
            max_acceleration_scaling_factor=0.5,
            pick_roll=pick_roll, 
            pick_pitch=pick_pitch, 
            pick_yaw=pick_yaw,
            group="arm",
            ik_frame="arm_gripper", 
            frame_id="arm_base_link",
        )
        return sequence_detect_and_grasp_object
    
    def gen_sequence_grasp_action(self):
        """
        生成夹爪夹取动作的行为
        """
        sequence_grasp_action = Sequence("grasp_action")
        # 闭合夹爪
        sequence_grasp_action.add_child(close_gripper())
        # 闭合剪刀
        sequence_grasp_action.add_child(close_shears())
        # 打开剪刀
        sequence_grasp_action.add_child(open_shears())
        return sequence_grasp_action

    def gen_sequence_put_object_in_box(self):
        """
        生成将物体放入框内的机械臂运动序列
        """
        # 运动到框内
        waypoint_names = ['ready', 'place_pre', '放到框内-就绪']
        waypoints = []
        for waypoint_name in waypoint_names:
            waypoints.append(get_waypoint_from_config(waypoint_name, self.waypoint_configs[waypoint_name]))
        sequence_put_object_in_box = get_plan_and_execute_waypoints_sequence(waypoints)
        
        # 打开夹爪
        sequence_put_object_in_box.add_child(open_gripper())

        # 撤退
        waypoint_names = ['place_pre', 'ready']
        waypoints = []
        for waypoint_name in waypoint_names:
            waypoints.append(get_waypoint_from_config(waypoint_name, self.waypoint_configs[waypoint_name]))
        sequence_put_object_in_box = get_plan_and_execute_waypoints_sequence(waypoints)
        return sequence_put_object_in_box

    def task_grasp_object(self):
        """
        生成任务
        """
        sequence_task = Sequence("task")

        sequence_task.add_child(self.gen_sequence_go_to_detect('观测点1'))
        sequence_task.add_child(self.gen_sequence_detect_and_grasp_object())
        sequence_task.add_child(self.gen_sequence_grasp_action())
        sequence_task.add_child(self.gen_sequence_put_object_in_box())

        tree = BehaviorTree("task_grasp_object")
        tree.add_child(sequence_task)
        root = BehaviorRoot()
        root.add_child(tree)
        execute_result = self.executor.execute_tree(root.to_str(), "task_grasp_object")
        return execute_result
    
    def test_pick_and_place(self):
        """
        测试夹取和放置
        """
        sequence_task = Sequence("task")
        
        waypoint_names = [
            'ready', 
            '观测点1', 
            '抓取点测试', 
            'ready', 
            'place_pre', 
            '放到框内-就绪',
            'place_pre',
            'ready'
        ]

        for waypoint_name in waypoint_names:
            waypoint = get_waypoint_from_config(waypoint_name, self.waypoint_configs[waypoint_name])
            sequence_task.add_child(get_plan_and_execute_waypoints_sequence([waypoint]))
        
        tree = BehaviorTree("test_pick_and_place")
        tree.add_child(sequence_task)
        root = BehaviorRoot()
        root.add_child(tree)
        execute_result = self.executor.execute_tree(root.to_str(), "test_pick_and_place")



if __name__ == "__main__":
    rclpy.init()
    task = MelonTask()
    # task.task_grasp_object()
    task.test_pick_and_place()