import copy
import os
import sys
import threading
import time
import csv

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.time import Time, Duration
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge

from .DucoCobot import DucoCobot
from .gen_py.robot.ttypes import TaskState
from .transformations import euler_from_quaternion, quaternion_from_euler
from .handeye_calibration import HandeyeCalibrator


MAX_LATENCY_S = 2.0
MSG_TIMEOUT_S = 1.0


class CalibrationDataCollector(Node):
    def __init__(self, pose_list):
        super().__init__('papjia_calibration_data_collector')

        # 参数
        self.declare_parameter("topic_rgb", "/camera/camera_hand/color/image_raw")
        self.declare_parameter("topic_charuco_rgb", "/camera/camera_hand/color/charuco")
        self.declare_parameter("topic_charuco_pose", "/camera/camera_hand/color/charuco/pose")
        self.declare_parameter("save_path", "/workspace/data/0610")
        self.declare_parameter("cali_type", "eye_in_hand")

        topic_rgb = self.get_parameter("topic_rgb").get_parameter_value().string_value
        topic_charuco_rgb = self.get_parameter("topic_charuco_rgb").get_parameter_value().string_value
        topic_charuco_pose = self.get_parameter("topic_charuco_pose").get_parameter_value().string_value
        save_path = self.get_parameter("save_path").get_parameter_value().string_value
        self.cali_type = self.get_parameter("cali_type").get_parameter_value().string_value

        # 保存路径
        timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        self.data_save_dir = os.path.join(save_path, timestamp_str)
        os.makedirs(self.data_save_dir, exist_ok=True)
        self.pose_save_filepath = os.path.join(self.data_save_dir, 'pose.csv')
        self.cali_result_save_filepath = os.path.join(self.data_save_dir, f'cali_result_{self.cali_type}.csv')

        # 标定
        self.calibrator = HandeyeCalibrator()

        # 机器人初始化
        self.home_position = [1.541968,0.295302,1.51564,-0.308715,-1.54095,-3.0919]
        self.vel = 3
        self.acc = self.vel * 3
        self.duco_robot = DucoCobot('192.168.1.10',7003)
        self.duco_robot.open()
        self.move_home()

        # 图像/姿态保存结构
        self.cv_bridge = CvBridge()
        self.lock = threading.Lock()
        self.rgb_image = None
        self.charuco_rgb_image = None
        self.charuco_detect_result = None

        # 订阅
        self.create_subscription(Image, topic_rgb, self.rgb_cb, 10)
        self.create_subscription(Image, topic_charuco_rgb, self.charuco_rgb_cb, 10)
        self.create_subscription(PoseStamped, topic_charuco_pose, self.charuco_pose_cb, 10)

        self.pose_list = pose_list
        threading.Thread(target=self.collect_data, daemon=True).start()

    def move_home(self):
        self.get_logger().info(f"移动到 home: {self.home_position}")
        res = self.duco_robot.movej2(joints_list=self.home_position, v=self.vel, a=self.acc, r=0, block=True)
        self.get_logger().info(f"运动状态: {res}")
        return res == TaskState.ST_Finished

    def movel(self, pose):
        pos = list(pose[:3]) + list(euler_from_quaternion(pose[3:]))
        self.get_logger().info(f"直线移动到: {pos}")
        ik = self.duco_robot.cal_ikine(pose, q_near=self.duco_robot.get_actual_joints_position(), tool=[0]*6, wobj=[0]*6)
        res = self.duco_robot.movel(p=pos, v=self.vel, a=self.acc, r=0, q_near=ik, tool="default", wobj="default", block=True)
        self.get_logger().info(f"运动结束，状态: {res}")
        return res == TaskState.ST_Finished

    def get_current_robot_pose(self):
        cur = self.duco_robot.get_tcp_pose()
        quat = quaternion_from_euler(cur[3], cur[4], cur[5])
        return cur[:3] + list(quat)

    def rgb_cb(self, msg: Image):
        with self.lock:
            self.rgb_image = msg

    def charuco_rgb_cb(self, msg: Image):
        with self.lock:
            self.charuco_rgb_image = msg

    def charuco_pose_cb(self, msg: PoseStamped):
        with self.lock:
            self.charuco_detect_result = msg

    def wait_for_fresh(self, attr_name):
        start = self.get_clock().now()
        while True:
            with self.lock:
                msg = getattr(self, attr_name)
            if msg:
                dt = self.get_clock().now() - Time.from_msg(msg.header.stamp)
                if dt < Duration(seconds=MAX_LATENCY_S):
                    return msg
            if self.get_clock().now() - start > Duration(seconds=MSG_TIMEOUT_S):
                self.get_logger().warn(f"等待 fresh {attr_name} 超时 {MSG_TIMEOUT_S}s")
                return None
            rclpy.spin_once(self, timeout_sec=0.05)

    def save_data(self, i):
        msgs = {
            'rgb_image': self.wait_for_fresh('rgb_image'),
            'charuco_rgb_image': self.wait_for_fresh('charuco_rgb_image'),
            'charuco_detect_result': self.wait_for_fresh('charuco_detect_result'),
        }
        if any(v is None for v in msgs.values()):
            self.get_logger().error(f"第 {i} 点数据不全，跳过")
            return None, None

        rgb = msgs['rgb_image']
        ch_pose_msg = msgs['charuco_detect_result']
        robot_pose = self.get_current_robot_pose()
        ch_pose = [
            ch_pose_msg.pose.position.x,
            ch_pose_msg.pose.position.y,
            ch_pose_msg.pose.position.z,
            ch_pose_msg.pose.orientation.x,
            ch_pose_msg.pose.orientation.y,
            ch_pose_msg.pose.orientation.z,
            ch_pose_msg.pose.orientation.w,
        ]

        # 保存图像
        cvb = self.cv_bridge
        rgb_cv = cvb.imgmsg_to_cv2(rgb, desired_encoding='bgr8')
        fn = os.path.join(self.data_save_dir, f"{i}_rgb.png")
        cv2.imwrite(fn, rgb_cv)

        self.get_logger().info(f"采样点 {i}: robot_pose={robot_pose}, charuco_pose={ch_pose}")
        return robot_pose, ch_pose

    def calibration(self, robot_poses, charuco_poses):
        return self.calibrator.calibration(robot_poses, charuco_poses, self.cali_type)

    def collect_data(self):
        self.get_logger().info("开始数据采集")
        rp, cp = [], []
        for i, p in enumerate(self.pose_list):
            self.get_logger().info(f"移动到第 {i} 点")
            self.movel(p); time.sleep(3)
            rp_curr, cp_curr = self.save_data(i)
            if rp_curr and cp_curr:
                rp.append(rp_curr); cp.append(cp_curr)
                if len(rp) >= 4:
                    self.get_logger().info("中间标定结果:")
                    self.get_logger().info(str(self.calibration(rp, cp)))
            else:
                self.get_logger().warn(f"第 {i} 点采集失败")

        self.get_logger().info("采集结束，保存所有数据")
        with open(self.pose_save_filepath, 'w', newline='') as f:
            w = csv.writer(f)
            for a, b in zip(rp, cp):
                w.writerow(a); w.writerow(b); w.writerow(['---'])

        res = self.calibration(rp, cp)
        with open(self.cali_result_save_filepath, 'w', newline='') as f:
            csv.writer(f).writerow(res)

        self.get_logger().info("标定完成")

def main():
    rclpy.init()
    pose_list = [...]  # 你的 pose 列表
    node = CalibrationDataCollector(pose_list)
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
