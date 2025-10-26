import os
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
from builtin_interfaces.msg import Duration
from sensor_msgs.msg import JointState
import yaml
import threading
import copy
import xml.etree.ElementTree as ET
import uuid
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from arm_move import get_plan_and_execute_waypoints_sequence, Waypoint


class RobotUtils(Node):
    def __init__(self):
        super().__init__("robot_utils")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 创建一个锁，用于互斥访问共享资源
        self.lock = threading.Lock()

        # 初始化存储关节状态的字典
        self.joint_state = {}

        # 订阅 joint_states 话题
        self.joint_state_subscription = self.create_subscription(
            JointState, "/joint_states", self.joint_state_callback, 3  # 消息类型  # 话题名  # 回调函数  # 队列大小
        )
        self.joint_state_subscription  # 防止警告未使用
        self.joint_state
        self.arm_is_moving = False

        # 初始化任务执行器
        self.task_executor = PapjiaSkillExecutor()

        # 创建多线程执行器并添加节点
        self.spin_executor = MultiThreadedExecutor()
        self.spin_executor.add_node(self)
        # self.spin_executor.add_node(self.task_executor)
        self.spin_thread = threading.Thread(target=self.spin)
        self.spin_thread.start()
        
        # TODO 临时，后面这玩意要去掉
        from papjia_skill.action_models import ActionModels
        action_model_config_filepath = os.getenv('ACTION_MODEL_CONFIG_FILEPATH', '/workspace/src/papjia_skill/config/action_model.yaml')
        ActionModels(action_model_config_filepath)

    def spin(self):
        self.spin_executor.spin()

    def joint_state_callback(self, msg):
        # 获取锁，确保线程安全
        with self.lock:
            # 更新关节状态字典
            self.joint_state = {name: position for name, position in zip(msg.name, msg.position)}

    def plan_and_execute_arm_waypoints(self, waypoints: list[Waypoint]):
        print(waypoints)
        sequence = get_plan_and_execute_waypoints_sequence(waypoints)
        self.exec_tree(sequence, "plan_and_execute_waypoints" + str(uuid.uuid4()))
    
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
        try:
            self.arm_is_moving = True
            tree = BehaviorTree(tree_name)
            tree.add_child(seq)
            root = BehaviorRoot()
            root.add_child(tree)
            result = self.task_executor.execute_tree(tree_string=root.to_str(), tree_name=tree_name, keys=keys)
            self.arm_is_moving = False
            return result
        except Exception as e:
            self.get_logger().error(f"执行行为树失败: {str(e)}")
            self.arm_is_moving = False
            return None
    
    def get_move_status(self):
        return self.arm_is_moving

    def get_joint_state(self):
        # 获取锁，确保线程安全
        with self.lock:
            res = copy.deepcopy(self.joint_state)
            return res

    def parse_groups(self, file_path):
        # 解析 XML 文件
        tree = ET.parse(file_path)
        root = tree.getroot()
        groups = {}
        # 遍历所有 group 元素
        for group in root.findall("group"):
            group_name = group.get("name")  # 获取 group 的名称
            # 获取 group 内的 links 和 joints
            links = [link.get("name") for link in group.findall("link")]
            joints = [joint.get("name") for joint in group.findall("joint")]
            groups[group_name] = {"links": links, "joints": joints}
        return groups

    def query_transform(self, target_frame, source_frame):
        try:
            # 当前时间
            timeout = Duration(sec=1)

            # 手动轮询检查是否可以转换
            while True:
                self.get_logger().info("Checking for transform...")
                if self.tf_buffer.can_transform(target_frame, source_frame, self.get_clock().now(), timeout=rclpy.time.Duration(seconds=timeout.sec)):
                    break
                self.get_logger().info("Waiting for transform...")

            # 查询变换
            transform = self.tf_buffer.lookup_transform(target_frame, source_frame, self.get_clock().now(), timeout=rclpy.time.Duration(seconds=timeout.sec))

            # 提取平移和旋转信息
            translation = transform.transform.translation
            rotation = transform.transform.rotation

            # 打印变换信息
            self.get_logger().info(f"Transform from {source_frame} to {target_frame}:")
            self.get_logger().info(f"  Translation: x={translation.x}, y={translation.y}, z={translation.z}")
            self.get_logger().info(f"  Rotation (quaternion): x={rotation.x}, y={rotation.y}, z={rotation.z}, w={rotation.w}")
            return [translation.x, translation.y, translation.z, rotation.x, rotation.y, rotation.z, rotation.w]
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().error(f"Failed to lookup transform: {str(e)}")
        return None

    def query_frames(self):
        try:
            # 获取所有 frame 的信息（YAML 格式）
            frame_tree_yaml = self.tf_buffer.all_frames_as_yaml()

            # 解析 YAML 数据
            frame_data = yaml.safe_load(frame_tree_yaml)

            # 提取每个 frame 的 parent 和 child 信息
            parsed_frames = self.parse_frame_data(frame_data)

            # 打印解析后的信息
            for frame, info in parsed_frames.items():
                parent = info["parent"]
                children = info["children"]
                self.get_logger().info(f"Frame: {frame}, Parent: {parent}, Children: {children}")

            return parsed_frames

        except Exception as e:
            self.get_logger().error(f"Failed to query frames: {str(e)}")

        return None

    def parse_frame_data(self, frame_data):
        """
        从 YAML 数据中提取每个 frame 的 parent 和 children 信息。
        """
        parsed_frames = {}

        for child_frame, details in frame_data.items():
            # 获取 parent frame
            parent_frame = details.get("parent", None)

            # 初始化 frame 的信息
            if child_frame not in parsed_frames:
                parsed_frames[child_frame] = {"parent": None, "children": []}
            if parent_frame and parent_frame not in parsed_frames:
                parsed_frames[parent_frame] = {"parent": None, "children": []}

            # 设置 parent-child 关系
            parsed_frames[child_frame]["parent"] = parent_frame
            if parent_frame:
                parsed_frames[parent_frame]["children"].append(child_frame)

        return parsed_frames


def main(args=None):
    rclpy.init(args=args)
    node = RobotUtils()

    # 等待 TF 数据缓存完成
    transform = node.query_transform(target_frame="base_link", source_frame="arm_left_grasp")

    if transform:
        node.get_logger().info("Transform successfully retrieved.")

    frames = node.query_frames()
    if frames:
        node.get_logger().info("Frames successfully queried.")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
