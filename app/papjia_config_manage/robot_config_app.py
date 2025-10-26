import rclpy
import json
import tkinter as tk
import numpy as np
import transformations as tfs
import copy
import time
from tkinter import messagebox, filedialog
from robot_utils import RobotUtils


class RobotConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Transform Query")

        self.dropdown_width = 30
        self.transform_width = 100
        self.group_state_width = 90

        # 初始化RobotUtils
        self.robot_utils = RobotUtils()
        self.frames = ["base_link", "arm_left_grasp", "arm_right_grasp_inner", "glass_tube", "op_glass_tube", "shake"]
        self.pose_modes = ["0-基于参考系的位姿", "1-基于末端当前位姿"]
        self.move_methods = ["0-PTP", "1-LIN", "2-OMPL"]
        self.move_spaces = ["0-关节空间", "1-笛卡尔空间"]
        self.arm_configs = {}
        self.task_configs = {}
        self.group_file_path = "/home/yw/workspace/ws_szyj/src/papjia_szyj/papjia_szyj_moveit_config/config/robot.srdf"
        self.joint_groups = self.robot_utils.parse_groups(self.group_file_path)
        self.joint_group_names = list(self.joint_groups.keys())

        ### 创建一个 Frame 用于水平排列下拉框
        frame_tf = tk.Frame(root, borderwidth=2, relief="solid", padx=10, pady=10)
        frame_tf.grid(row=0, column=0, sticky="nsew")
        # 创建 Target 下拉框前的提示文字
        self.target_label = tk.Label(frame_tf, text="Target:")
        self.target_label.grid(row=0, column=0, sticky="nsew")
        # 创建 Target 下拉框
        self.target_var = tk.StringVar(root)
        self.target_var.set(self.frames[0])  # 默认选项
        self.target_dropdown = tk.OptionMenu(frame_tf, self.target_var, *self.frames)
        self.target_dropdown.config(width=self.dropdown_width)
        self.target_dropdown.grid(row=0, column=1, sticky="nsew")
        # 创建 Target 下拉框前的提示文字
        self.source_label = tk.Label(frame_tf, text="Source:")
        self.source_label.grid(row=1, column=0, sticky="nsew")
        self.source_var = tk.StringVar(root)
        self.source_var.set(self.frames[0])  # 默认选项
        self.source_dropdown = tk.OptionMenu(frame_tf, self.source_var, *self.frames)
        self.source_dropdown.config(width=self.dropdown_width)
        self.source_dropdown.grid(row=1, column=1, sticky="nsew")
        # 添加查询按钮
        self.query_frames_button = tk.Button(frame_tf, text="查询Frames", command=self.query_frames)
        self.query_frames_button.grid(row=0, column=2, sticky="nsew")
        # 添加查询按钮
        self.query_transform_button = tk.Button(frame_tf, text="查询位姿", command=self.query_transform)
        self.query_transform_button.grid(row=1, column=2, sticky="nsew")
        # 添加显示变换信息的标签
        self.transform_label = tk.Label(frame_tf, text="None")
        self.transform_label.config(width=self.transform_width)
        self.transform_label.grid(row=1, column=3, sticky="nsew")

        ### 创建一个 Frame 末端相对位姿下拉框
        frame_arm_dropdown = tk.Frame(root)
        frame_arm_dropdown.grid(row=2, column=0, sticky="nsew")
        # 创建 End Effector 下拉框前的提示文字
        self.ik_frame_label = tk.Label(frame_arm_dropdown, text="End Effector:")
        self.ik_frame_label.pack(side=tk.LEFT, padx=5)
        # 创建 End Effector 下拉框
        self.ik_frame_var = tk.StringVar(root)
        self.ik_frame_var.set(self.frames[0])  # 默认选项
        self.ik_frame_dropdown = tk.OptionMenu(frame_arm_dropdown, self.ik_frame_var, *self.frames)
        self.ik_frame_dropdown.config(width=self.dropdown_width)
        self.ik_frame_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建下拉框前的提示文字
        self.goal_frame_label = tk.Label(frame_arm_dropdown, text="Ref Frame:")
        self.goal_frame_label.pack(side=tk.LEFT, padx=5)
        self.goal_frame_var = tk.StringVar(root)
        self.goal_frame_var.set(self.frames[0])  # 默认选项
        self.goal_frame_dropdown = tk.OptionMenu(frame_arm_dropdown, self.goal_frame_var, *self.frames)
        self.goal_frame_dropdown.config(width=self.dropdown_width)
        self.goal_frame_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 添加查询按钮
        self.query_frames_button = tk.Button(frame_arm_dropdown, text="查询Frames", command=self.query_frames2)
        self.query_frames_button.pack(side=tk.LEFT, padx=20, fill=tk.BOTH, expand=True)

        ### 创建一个 Frame 用于末端位姿查询
        frame_arm_transform = tk.Frame(root)
        frame_arm_transform.grid(row=3, column=0, sticky="nsew")
        # 添加查询按钮
        self.query_arm_transform_button = tk.Button(frame_arm_transform, text="查询位姿", command=self.query_transform2)
        self.query_arm_transform_button.pack(side=tk.LEFT, padx=5)
        # 添加显示变换信息的标签
        self.arm_transform_label = tk.Label(frame_arm_transform, text="None")
        self.arm_transform_label.config(width=self.transform_width)
        self.arm_transform_label.pack(side=tk.LEFT, padx=5)

        ### 创建一个 Frame 用于手臂查询
        frame_arm = tk.Frame(root)
        frame_arm.grid(row=4, column=0, sticky="nsew")
        # 创建 Joint Group 下拉框前的提示文字
        self.joint_group_label = tk.Label(frame_arm, text="Group:")
        self.joint_group_label.pack(side=tk.LEFT, padx=5)
        # 创建 Joint Group 下拉框
        self.joint_group_var = tk.StringVar(root)
        self.joint_group_var.set(self.joint_group_names[0])  # 默认选项
        self.joint_group_dropdown = tk.OptionMenu(frame_arm, self.joint_group_var, *self.joint_group_names)
        self.joint_group_dropdown.config(width=15)
        self.joint_group_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 添加查询按钮
        self.query_joint_group_button = tk.Button(frame_arm, text="查询当前状态", command=self.query_group)
        self.query_joint_group_button.pack(side=tk.LEFT, padx=5)
        # 添加显示变换信息的标签
        self.joint_group_label = tk.Label(frame_arm, text="None")
        self.joint_group_label.config(width=self.group_state_width)
        self.joint_group_label.pack(side=tk.LEFT, padx=5)

        ### 创建一个 Frame 用于手臂控制
        frame_arm_offset = tk.Frame(root)
        frame_arm_offset.grid(row=5, column=0, sticky="nsew")
        # 创建一个下拉框用于选择姿态模式
        self.pose_mode_label = tk.Label(frame_arm_offset, text="模式:")
        self.pose_mode_label.pack(side=tk.LEFT, padx=5)
        self.pose_mode_var = tk.StringVar(root)
        self.pose_mode_var.set(self.pose_modes[0])  # 默认选项
        self.pose_mode_dropdown = tk.OptionMenu(frame_arm_offset, self.pose_mode_var, *self.pose_modes)
        self.pose_mode_dropdown.config(width=12)
        self.pose_mode_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建一个下拉框用于选择移动方法
        self.move_method_label = tk.Label(frame_arm_offset, text="方法:")
        self.move_method_label.pack(side=tk.LEFT, padx=5)
        self.move_method_var = tk.StringVar(root)
        self.move_method_var.set(self.move_methods[0])  # 默认选项
        self.move_method_dropdown = tk.OptionMenu(frame_arm_offset, self.move_method_var, *self.move_methods)
        self.move_method_dropdown.config(width=5)
        self.move_method_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建 Offset 文本框/数字框
        self.arm_offset_x_label = tk.Label(frame_arm_offset, text="X:")
        self.arm_offset_x_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_x_entry.insert(0, "0.0")
        self.arm_offset_x_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_x_entry.pack(side=tk.LEFT, padx=5)
        self.arm_offset_y_label = tk.Label(frame_arm_offset, text="Y:")
        self.arm_offset_y_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_y_entry.insert(0, "0.0")
        self.arm_offset_y_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_y_entry.pack(side=tk.LEFT, padx=5)
        self.arm_offset_z_label = tk.Label(frame_arm_offset, text="Z:")
        self.arm_offset_z_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_z_entry.insert(0, "0.0")
        self.arm_offset_z_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_z_entry.pack(side=tk.LEFT, padx=5)
        self.arm_offset_roll_label = tk.Label(frame_arm_offset, text="Roll:")
        self.arm_offset_roll_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_roll_entry.insert(0, "0.0")
        self.arm_offset_roll_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_roll_entry.pack(side=tk.LEFT, padx=5)
        self.arm_offset_pitch_label = tk.Label(frame_arm_offset, text="Pitch:")
        self.arm_offset_pitch_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_pitch_entry.insert(0, "0.0")
        self.arm_offset_pitch_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_pitch_entry.pack(side=tk.LEFT, padx=5)
        self.arm_offset_yaw_label = tk.Label(frame_arm_offset, text="Yaw:")
        self.arm_offset_yaw_entry = tk.Entry(frame_arm_offset, width=6)
        self.arm_offset_yaw_entry.insert(0, "0.0")
        self.arm_offset_yaw_label.pack(side=tk.LEFT, padx=5)
        self.arm_offset_yaw_entry.pack(side=tk.LEFT, padx=5)

        ### 创建一个 Frame 用于手臂配置保存/手臂移动
        frame_arm_config = tk.Frame(root)
        frame_arm_config.grid(row=6, column=0, sticky="nsew")
        # 创建一个文本框输入配置的名称
        self.config_name_label = tk.Label(frame_arm_config, text="配置名称:")
        self.config_name_label.pack(side=tk.LEFT, padx=5)
        self.config_name_entry = tk.Entry(frame_arm_config, width=40)
        self.config_name_entry.pack(side=tk.LEFT, padx=5)
        # 创建一个文本框描述配置的特性
        self.config_description_label = tk.Label(frame_arm_config, text="描述:")
        self.config_description_label.pack(side=tk.LEFT, padx=5)
        self.config_description_entry = tk.Entry(frame_arm_config, width=40)
        self.config_description_entry.pack(side=tk.LEFT, padx=5)
        # 创建一个按钮用于执行位姿调整
        self.execute_pose_adjustment_button = tk.Button(frame_arm_config, text="移动", command=self.execute_pose_adjustment)
        self.execute_pose_adjustment_button.pack(side=tk.LEFT, padx=5)
        # 创建一个按钮用于保存配置
        self.save_config_button = tk.Button(frame_arm_config, text="保存配置", command=self.save_config)
        self.save_config_button.pack(side=tk.LEFT, padx=5)

        ### 创建一个 Frame 用于显示手臂配置
        frame_arm_config_list = tk.Frame(root)
        frame_arm_config_list.grid(row=7, column=0, sticky="nsew")
        # 创建一个下拉框用于选择配置
        self.config_select_label = tk.Label(frame_arm_config_list, text="目标配置:")
        self.config_select_label.pack(side=tk.LEFT, padx=5)
        self.config_select_var = tk.StringVar(root)
        self.config_select_var.set("")  # 默认选项
        self.config_select_dropdown = tk.OptionMenu(frame_arm_config_list, self.config_select_var, None)
        self.config_select_dropdown.config(width=15)
        self.config_select_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 绑定回调函数
        self.config_select_var.trace_add("write", self.on_select_config)
        # # 创建一个下拉列表控制移动空间
        # self.space_select_label = tk.Label(frame_arm_config_list, text="运动空间:")
        # self.space_select_label.pack(side=tk.LEFT, padx=5)
        # self.space_select_var = tk.StringVar(root)
        # self.space_select_var.set(self.move_spaces[0])  # 默认选项
        # self.space_select_dropdown = tk.OptionMenu(frame_arm_config_list, self.space_select_var, *self.move_spaces)
        # self.space_select_dropdown.config(width=15)
        # self.space_select_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建一个下拉框用于选择移动方法
        self.select_method_label = tk.Label(frame_arm_config_list, text="方法:")
        self.select_method_label.pack(side=tk.LEFT, padx=5)
        self.select_method_var = tk.StringVar(root)
        self.select_method_var.set(self.move_methods[0])  # 默认选项
        self.select_method_dropdown = tk.OptionMenu(frame_arm_config_list, self.select_method_var, *self.move_methods)
        self.select_method_dropdown.config(width=5)
        self.select_method_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建一个按钮用于移动机械臂
        self.execute_config_button = tk.Button(frame_arm_config_list, text="删除配置", command=self.delete_config)
        self.execute_config_button.pack(side=tk.LEFT, padx=5)

        ### 创建一个 Frame 用于任务配置
        frame_task = tk.Frame(root, borderwidth=2, relief="solid", padx=10, pady=10)
        frame_task.grid(row=8, column=0, sticky="nsew")
        # 创建一个控件从文件导入任务配置
        self.import_task_button = tk.Button(frame_task, text="导入任务配置", command=self.load_task_config_from_file)
        self.import_task_button.grid(row=0, column=0, sticky="nsew")
        # 创建一个显示框显示文件路径
        self.file_path_label = tk.Label(frame_task, text="None")
        self.file_path_label.config(width=100)
        self.file_path_label.grid(row=0, column=1, sticky="nsew")
        # 创建一个控件从文件导入所有点位配置
        self.import_all_poses_button = tk.Button(frame_task, text="导入所有点位", command=self.load_all_poses_from_file)
        self.import_all_poses_button.grid(row=1, column=0, sticky="nsew")
        # 创建一个显示框显示文件路径
        self.poses_file_path_label = tk.Label(frame_task, text="None")
        self.poses_file_path_label.config(width=100)
        self.poses_file_path_label.grid(row=1, column=1, sticky="nsew")
        # 创建一个下拉框显示任务配置
        self.task_config_list_label = tk.Label(frame_task, text="任务:")
        self.task_config_list_label.grid(row=2, column=0, sticky="nsew")
        self.task_config_list_var = tk.StringVar(root)
        self.task_config_list_var.set("")  # 默认选项
        self.task_config_list_dropdown = tk.OptionMenu(frame_task, self.task_config_list_var, None)
        self.task_config_list_dropdown.config(width=15)
        self.task_config_list_dropdown.grid(row=2, column=1, sticky="nsew")
        # 下拉框需要一个回调函数做对应的处理
        self.task_config_list_var.trace_add("write", self.on_select_task_config)
        # 创建一个按钮用于执行任务
        self.execute_task_button = tk.Button(frame_task, text="执行任务", command=self.execute_task)
        self.execute_task_button.grid(row=2, column=2, sticky="nsew")
        ## 创建一个下拉框显示任务对应的点位配置
        self.task_pose_config_list_label = tk.Label(frame_task, text="点位:")
        self.task_pose_config_list_label.grid(row=3, column=0, sticky="nsew")
        self.task_pose_config_list_var = tk.StringVar(root)
        self.task_pose_config_list_var.set("")  # 默认选项
        self.task_pose_config_list_dropdown = tk.OptionMenu(frame_task, self.task_pose_config_list_var, None)
        self.task_pose_config_list_dropdown.config(width=15)
        self.task_pose_config_list_dropdown.grid(row=3, column=1, sticky="nsew")
        # 下拉框需要一个回调函数做对应的处理
        self.task_pose_config_list_var.trace_add("write", self.on_select_task_pose_config)
        # 添加一个删除点位的按钮
        self.remove_task_pose_button = tk.Button(frame_task, text="删除点位", command=self.remove_task_pose)
        self.remove_task_pose_button.grid(row=3, column=2, sticky="nsew")

        ### 创建一个 Frame 用于添加任务配置
        frame_task_add = tk.Frame(root, borderwidth=2, relief="solid", padx=10, pady=10)
        frame_task_add.grid(row=9, column=0, sticky="nsew")
        # 创建一个文本框输入配置的名称       
        self.task_name_label = tk.Label(frame_task_add, text="任务名称:")
        self.task_name_label.pack(side=tk.LEFT, padx=5)
        self.task_name_entry = tk.Entry(frame_task_add, width=40)
        self.task_name_entry.pack(side=tk.LEFT, padx=5)
        # 创建下拉列表能够选择点位配置（self.configs.keys()）
        self.task_config_label = tk.Label(frame_task_add, text="可添加点位:")
        self.task_config_label.pack(side=tk.LEFT, padx=5)
        self.task_config_var = tk.StringVar(root)
        self.task_config_dropdown = tk.OptionMenu(frame_task_add, self.task_config_var, None)
        self.task_config_dropdown.config(width=self.dropdown_width)
        self.task_config_dropdown.pack(side=tk.LEFT, padx=1, fill=tk.BOTH, expand=True)
        # 创建一个按钮用于添加当前配置到任务
        self.add_to_task_button = tk.Button(frame_task_add, text="添加", command=self.add_to_task)
        self.add_to_task_button.pack(side=tk.LEFT, padx=5)
        # 创建一个按钮用于保存配置
        self.save_task_button = tk.Button(frame_task_add, text="导出", command=self.save_task)
        self.save_task_button.pack(side=tk.LEFT, padx=5)
    
    def remove_task_pose(self):
        pass
    
    def on_select_task_config(self, *args):
        task_name = self.task_config_list_var.get()
        configs = self.task_configs.get(task_name, [])
        self.task_pose_config_list_dropdown["menu"].delete(0, tk.END)
        for config_name in configs:
            self.task_pose_config_list_dropdown["menu"].add_command(label=config_name, command=tk._setit(self.task_pose_config_list_var, config_name))

    def on_select_task_pose_config(self, *args):
        config_name = self.task_pose_config_list_var.get()
        self.update_config_vision_by_name(config_name)

    def on_select_config(self, *args):
        config_name = self.config_select_var.get()
        self.update_config_vision_by_name(config_name)

    def execute_task(self):
        task_name = self.task_config_list_var.get()
        configs = self.task_configs.get(task_name, [])
        for config_name in configs:
            self.execute_config_by_name(config_name)
            # time.sleep(3)
            input("check")

    def add_to_task(self):
        task_name = self.task_name_entry.get()
        config_name = self.task_config_var.get()
        if task_name and config_name:
            if task_name not in self.task_configs:
                self.task_configs[task_name] = []
            self.task_configs[task_name].append(config_name)
            self.task_config_list_dropdown["menu"].delete(0, tk.END)
            for task_name in self.task_configs.keys():
                self.task_config_list_dropdown["menu"].add_command(label=task_name, command=tk._setit(self.task_config_list_var, task_name))
            print("loaded task names: ", self.task_configs.keys())
            # 弹框说明成功添加
            messagebox.showinfo("添加成功", f"{config_name} 已成功添加到任务 {task_name}")
        else:
            messagebox.showwarning("警告", "任务名或配置名不能为空")

    def save_task(self):
        # 弹出文件保存对话框，让用户选择保存路径
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not file_path:  # 用户取消操作
            return

        try:
            with open(file_path, "w") as file:
                json.dump(self.task_configs, file, indent=4, ensure_ascii=False)
            messagebox.showinfo("保存成功", f"配置已保存到文件：{file_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存配置时发生错误：{e}")
            
    def load_task_config_from_file(self):
        try:
            file_path = filedialog.askopenfilename(title="选择文件", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if not file_path:
                return
            with open(file_path, "r") as file:
                configs = json.load(file)
                for name, conifg in configs.items():
                    self.task_configs[name] = conifg
                self.file_path_label.config(text=file_path)
                self.task_config_list_dropdown["menu"].delete(0, tk.END)
                for task_name in self.task_configs.keys():
                    self.task_config_list_dropdown["menu"].add_command(label=task_name, command=tk._setit(self.task_config_list_var, task_name))
            print("loaded task names: ", self.task_configs.keys())
        except json.JSONDecodeError as e:
            print(f"JSON 解码错误: {e}")
        except FileNotFoundError:
            print("文件未找到，请检查路径！")
    
    def load_all_poses_from_file(self):
        try:
            file_path = filedialog.askopenfilename(title="选择文件", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            self.load_config_by_path(file_path)
            self.poses_file_path_label.config(text=file_path)
            config_names = list(self.arm_configs.keys())
            config_names.sort()
            self.config_select_dropdown["menu"].delete(0, tk.END)
            self.task_config_dropdown["menu"].delete(0, tk.END)
            for name in config_names:
                self.config_select_dropdown["menu"].add_command(label=name, command=tk._setit(self.config_select_var, name))
                self.task_config_dropdown["menu"].add_command(label=name, command=tk._setit(self.task_config_var, name))            

        except FileNotFoundError:
            print("文件未找到，请检查路径！")

    def load_config_by_path(self, file_path):
        try:
            with open(file_path, "r") as file:
                configs = json.load(file)
                for name, config in configs.items():
                    self.arm_configs[name] = config
            print("loaded config names: ", self.arm_configs.keys())
        except json.JSONDecodeError as e:
            print(f"JSON 解码错误: {e}")
        except FileNotFoundError:
            print("文件未找到，请检查路径！")

    def save_config(self):
        # 弹出文件保存对话框，让用户选择保存路径
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not file_path:  # 用户取消操作
            return

        try:
            # 将 arm_configs 保存为 JSON 文件
            with open(file_path, "w") as file:
                json.dump(self.arm_configs, file, indent=4, ensure_ascii=False)
            messagebox.showinfo("保存成功", f"配置已保存到文件：{file_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存配置时发生错误：{e}")

    def update_config_vision_by_name(self, config_name):
        config = self.arm_configs[config_name]
        if "planner" in config:
            for planner in self.move_methods:
                if planner[2:] == config["planner"].upper():
                    self.select_method_var.set(planner)
                    self.move_method_var.set(planner)
        # 修改文本框的值
        self.config_name_entry.delete(0, tk.END)
        self.config_name_entry.insert(0, config_name)
        if "description" in config:
            self.config_description_entry.delete(0, tk.END)
            self.config_description_entry.insert(0, config["description"])
        if "ik_frame" in config:
            self.ik_frame_var.set(config["ik_frame"])
        if "frame_id" in config:
            self.goal_frame_var.set(config["frame_id"])
        if "group" in config:
            self.joint_group_var.set(config["group"])
        if "pose" in config:
            self.pose_mode_var.set(self.pose_modes[0])
            x, y, z, qx, qy, qz, qw = config["pose"]
            roll, pitch, yaw = tfs.euler_from_quaternion([qw, qx, qy, qz])
            self.arm_offset_x_entry.delete(0, tk.END)
            self.arm_offset_x_entry.insert(0, str(x))
            self.arm_offset_y_entry.delete(0, tk.END)
            self.arm_offset_y_entry.insert(0, str(y))
            self.arm_offset_z_entry.delete(0, tk.END)
            self.arm_offset_z_entry.insert(0, str(z))
            self.arm_offset_roll_entry.delete(0, tk.END)
            self.arm_offset_roll_entry.insert(0, str(roll))
            self.arm_offset_pitch_entry.delete(0, tk.END)
            self.arm_offset_pitch_entry.insert(0, str(pitch))
            self.arm_offset_yaw_entry.delete(0, tk.END)
            self.arm_offset_yaw_entry.insert(0, str(yaw))

    def delete_config(self):
        config_name = self.config_select_var.get()
        del self.arm_configs[config_name]

    def execute_config_by_name(self, config_name):
        config = self.arm_configs[config_name]
        if "type" in config and config["type"] == "ref_pose":
            self.robot_utils.move_based_ref_pose(
                config["group"],
                config["ik_frame"],
                config["frame_id"],
                config["pose"],
                config["planner"],
                config_name,
            )
        else:
            planner = self.select_method_var.get()
            planner = planner[2:].lower()
            self.robot_utils.move_based_joint_state(
                config["group"],
                config_name,
                planner,
            )

    def execute_pose_adjustment(self):
        dx = float(self.arm_offset_x_entry.get())
        dy = float(self.arm_offset_y_entry.get())
        dz = float(self.arm_offset_z_entry.get())
        droll = float(self.arm_offset_roll_entry.get())
        dpitch = float(self.arm_offset_pitch_entry.get())
        dyaw = float(self.arm_offset_yaw_entry.get())
        pose_mode = self.pose_mode_var.get()
        end_effector = self.ik_frame_var.get()
        ref_frame = self.goal_frame_var.get()
        group_name = self.joint_group_var.get()
        pose_name = self.config_name_entry.get()
        pose_description = self.config_description_entry.get()
        move_method = self.move_method_var.get()
        move_method = move_method[2:].lower()
        if pose_name in self.arm_configs.keys():
            # 弹框询问是否继续
            if messagebox.askyesno("Confirm", "已存在配置名，继续吗？"):
                pass
            else:
                return
        config = {}
        config["group"] = group_name
        config["joint_names"] = self.joint_groups[group_name]["joints"]
        config["preWaypoint"] = ""
        config["type"] = "cartesian"
        config["ik_frame"] = end_effector
        config["frame_id"] = ref_frame
        config["planner"] = move_method
        config["description"] = pose_description
        res = False
        if pose_mode[0] == "0":
            q = tfs.quaternion_from_euler(droll, dpitch, dyaw)
            pose = [dx, dy, dz, q[1], q[2], q[3], q[0]]
            print("pose", pose)
            config["pose"] = pose
            res = self.robot_utils.move_based_ref_pose(group_name, end_effector, ref_frame, pose, move_method, pose_name)
        elif pose_mode[0] == "1":
            current_pose = self.robot_utils.query_transform(ref_frame, end_effector)
            x, y, z, qx, qy, qz, qw = current_pose[0:7]
            roll, pitch, yaw = tfs.euler_from_quaternion([qw, qx, qy, qz])
            q = tfs.quaternion_from_euler(droll + roll, dpitch + pitch, dyaw + yaw)
            pose = [x + dx, y + dy, z + dz, q[1], q[2], q[3], q[0]]
            config["pose"] = pose
            res = self.robot_utils.move_based_ref_pose(group_name, end_effector, ref_frame, pose, move_method, pose_name)
        else:
            print("Unknown pose mode.")
        if res:
            config["joint_values"] = self.query_group_by_name(group_name)
            if pose_name not in self.arm_configs.keys():
                self.config_select_dropdown["menu"].insert_command(
                    0,
                    label=pose_name,
                    command=lambda value=pose_name: self.config_select_var.set(value),  # 插入到最前面的位置
                )
            self.arm_configs[pose_name] = config
        else:
            messagebox.showerror("Error", "Failed to move the robot.")

    def query_frames(self):
        frames = self.robot_utils.query_frames()
        for frame in frames:
            if frame not in self.frames:
                self.frames.append(frame)
        # 访问 OptionMenu 的底层菜单，并删除现有的菜单项
        menu = self.target_dropdown["menu"]
        menu.delete(0, "end")
        # 添加新的菜单项
        for frame in self.frames:
            menu.add_command(label=frame, command=tk._setit(self.target_var, frame))
        # 更新当前选中的值（可选）
        self.target_var.set(self.frames[0])  # 设置为新的默认选项
        menu = self.source_dropdown["menu"]
        menu.delete(0, "end")
        for frame in self.frames:
            menu.add_command(label=frame, command=tk._setit(self.source_var, frame))
        self.source_var.set(self.frames[0])

    def query_frames2(self):
        frames = self.robot_utils.query_frames()
        for frame in frames:
            if frame not in self.frames:
                self.frames.append(frame)
                print(f"Found new frame: {frame}")
        # 访问 OptionMenu 的底层菜单，并删除现有的菜单项
        menu = self.ik_frame_dropdown["menu"]
        menu.delete(0, "end")
        # 添加新的菜单项
        for frame in self.frames:
            menu.add_command(label=frame, command=tk._setit(self.ik_frame_var, frame))
        # 更新当前选中的值（可选）
        self.ik_frame_var.set(self.frames[0])  # 设置为新的默认选项
        menu = self.goal_frame_dropdown["menu"]
        menu.delete(0, "end")
        for frame in self.frames:
            menu.add_command(label=frame, command=tk._setit(self.goal_frame_var, frame))
        self.goal_frame_var.set(self.frames[0])

    def query_transform(self):
        target_frame = self.target_var.get()
        source_frame = self.source_var.get()
        transform_info = self.robot_utils.query_transform(target_frame, source_frame)
        if transform_info is not None:
            pos = ", ".join([f"{x:.3f}" for x in transform_info[0:3]])
            rot = ", ".join([f"{x:.3f}" for x in transform_info[3:7]])
            x, y, z, w = transform_info[3:7]
            roll, pitch, yaw = tfs.euler_from_quaternion([w, x, y, z])
            roll = np.rad2deg(roll)
            pitch = np.rad2deg(pitch)
            yaw = np.rad2deg(yaw)
            formatted_str = f"位置(xyz): ({pos}) - 方向(xyzw): ({rot}) - 方向(rpy/deg): ({roll:.3f}, {pitch:.3f}, {yaw:.3f})"
        if transform_info:
            self.transform_label.config(text=formatted_str)
        else:
            messagebox.showerror("Error", "Failed to get transform.")

    def query_transform2(self):
        target_frame = self.goal_frame_var.get()
        source_frame = self.ik_frame_var.get()
        transform_info = self.robot_utils.query_transform(target_frame, source_frame)
        if transform_info is not None:
            pos = ", ".join([f"{x:.3f}" for x in transform_info[0:3]])
            rot = ", ".join([f"{x:.3f}" for x in transform_info[3:7]])
            x, y, z, w = transform_info[3:7]
            roll, pitch, yaw = tfs.euler_from_quaternion([w, x, y, z])
            roll = np.rad2deg(roll)
            pitch = np.rad2deg(pitch)
            yaw = np.rad2deg(yaw)
            formatted_str = f"位置(xyz): ({pos}) - 方向(xyzw): ({rot}) - 方向(rpy/deg): ({roll:.3f}, {pitch:.3f}, {yaw:.3f})"
        if transform_info:
            self.arm_transform_label.config(text=formatted_str)
        else:
            messagebox.showerror("Error", "Failed to get transform.")

    def query_group(self):
        joint_states = self.robot_utils.get_joint_state()
        group_name = self.joint_group_var.get()
        positions = []
        for joint_name in self.joint_groups[group_name]["joints"]:
            positions.append(joint_states[joint_name])
        rad_str = ", ".join([f"{x:.3f}" for x in positions])
        deg_str = ", ".join([f"{np.rad2deg(x):.1f}" for x in positions])
        formated_str = f"Rad: ({rad_str})  Deg: ({deg_str})"
        self.joint_group_label.config(text=formated_str)

    def query_group_by_name(self, group_name):
        joint_states = self.robot_utils.get_joint_state()
        positions = []
        for joint_name in self.joint_groups[group_name]["joints"]:
            positions.append(joint_states[joint_name])
        return positions

    def run(self):
        self.root.mainloop()


def main():
    # 初始化 ROS2
    rclpy.init()

    # 创建 Tkinter 窗口
    root = tk.Tk()

    # 创建 RobotConfigApp 并运行
    app = RobotConfigApp(root)
    app.run()

    # 关闭 ROS2
    rclpy.shutdown()


if __name__ == "__main__":
    main()
