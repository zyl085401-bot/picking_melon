import copy
import launch.actions
import os
import sys
import cv2
import numpy as np
import csv
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from .DucoCobot import DucoCobot
from .gen_py.robot.ttypes import TaskState
import time
from .transformations import *

from geometry_msgs.msg import PoseStamped
import yaml
from .handeye_calibration import HandeyeCalibrator

import threading


class CalibrationDataCollector(Node):
    def __init__(self, pose_list):
        super().__init__('papjia_calibration_data_collector')
        
        # 参数设置
        self.declare_parameter("topic_rgb", "/camera/camera_hand/color/image_raw")
        self.declare_parameter("topic_charuco_rgb", "/camera/camera_hand/color/charuco")
        self.declare_parameter("topic_charuco_pose", "/camera/camera_hand/color/charuco/pose")
        self.declare_parameter("save_path", "/workspace/data/0610")
        self.declare_parameter("cali_type", "eye_in_hand")
        
        # 获取参数
        topic_rgb = self.get_parameter("topic_rgb").get_parameter_value().string_value
        topic_charuco_rgb = self.get_parameter("topic_charuco_rgb").get_parameter_value().string_value
        topic_charuco_pose = self.get_parameter("topic_charuco_pose").get_parameter_value().string_value
        save_path = self.get_parameter("save_path").get_parameter_value().string_value
        self.cali_type = self.get_parameter("cali_type").get_parameter_value().string_value
        
        # 程序运行时创建新的文件夹，用于保存数据
        current_time = time.time()
        timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(current_time))
        self.data_save_dir = os.path.join(save_path, timestamp_str)
        os.makedirs(self.data_save_dir)
        self.pose_save_filepath = os.path.join(self.data_save_dir, 'pose.csv')
        self.cali_result_save_filepath = os.path.join(self.data_save_dir, 'cali_result_{0}.csv'.format(self.cali_type))
        
        # 标定算子
        self.calibrator = HandeyeCalibrator()

        # 定义机器人位置
        self.home_position = [1.541968, 0.295302, 1.51564, -0.308715, -1.54095, -3.0919]
        self.vel = 3
        self.acc = self.vel * 3
        
        # 初始化机器人
        self.duco_robot = DucoCobot('192.168.1.10', 7003)
        self.duco_robot.open()
        self.move_home()
        
        # 订阅相机图像，marker板识别结果
        self.cv_bridge = CvBridge()
        self.rgb_image: None | Image = None
        self.charuco_rgb_image: None | Image = None
        self.lock = threading.Lock()
        self.charuco_detect_result: PoseStamped | None = None
        self.rgb_subscription = self.create_subscription(Image, topic_rgb, self.rgb_image_callback, 10)
        self.charuco_rgb_subscription = self.create_subscription(Image, topic_charuco_rgb, self.charuco_rgb_image_callback, 10)
        self.charuco_pose_subscription = self.create_subscription(PoseStamped, topic_charuco_pose, self.charuco_detect_result_callback, 10)

        # cv2.namedWindow("RT_Frame")
        # cv2.namedWindow("Save_Image")
        # cv2.namedWindow("Charuco_Image")
        
        self.pose_list = pose_list
        data_collect_thread = threading.Thread(target=self.collect_data)
        data_collect_thread.start()

    def move_home(self):
        """运动到Home位置

        Returns:
            bool: 运动成功与否
        """
        loginfo = "运动到home位置: {0}".format(self.home_position)
        self.get_logger().info(loginfo)

        res = self.duco_robot.movej2(joints_list=self.home_position, v=self.vel, a=self.acc, r=0, block=True)
        loginfo = "运动结束，任务状态: {0}".format(res)
        self.get_logger().info(loginfo)
        if res == TaskState.ST_Finished:
            return True
        else:
            return False

    def movej(self, joint_positions):
        """发送关节命令，执行关节运动
        """
        loginfo = "运动到: {0}".format(joint_positions)
        self.get_logger().info(loginfo)

        res = self.duco_robot.movej2(joints_list=joint_positions, v=self.vel, a=self.acc, r=0, block=True)
        loginfo = "运动结束，任务状态: {0}".format(res)
        self.get_logger().info(loginfo)
        if res == TaskState.ST_Finished:
            return True
        else:
            return False

    def movel(self, pose, isQuat=True):
        """直线运动

        Args:
            pose (_type_): _description_
            convertToEuler (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
        """
        if isQuat:
            assert len(pose) == 7
            euler = list(euler_from_quaternion(pose[3:]))
            pose = pose[:3] + list(euler)
        
        loginfo = "直线运动到: {0}".format(pose)
        self.get_logger().info(loginfo)

        res = self.duco_robot.movel(
            p=pose, v=self.vel, a=self.acc, r=0,
            q_near=self.duco_robot.cal_ikine(pose, q_near=self.duco_robot.get_actual_joints_position(),
                                             tool=[0]*6, wobj=[0]*6,),
            tool="default", wobj="default",  block=True)
        loginfo = "运动结束，任务状态: {0}".format(res)
        self.get_logger().info(loginfo)

        if res == TaskState.ST_Finished:
            return True
        else:
            return False
    
    def get_current_robot_pose(self):
        cur_pose = self.duco_robot.get_tcp_pose()
        cur_pose_quat = quaternion_from_euler(cur_pose[3], cur_pose[4], cur_pose[5])
        cur_pose = cur_pose[:3] + list(cur_pose_quat)
        return cur_pose
    
    def get_current_joint_position(self):
        return self.duco_robot.get_actual_joints_position()
    
    def rgb_image_callback(self, msg):
        try:
            # 将ROS图像消息转换为OpenCV图像
            with self.lock:
                cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
                self.rgb_image = msg
        except Exception as e:
            self.get_logger().error("Error converting ROS image to OpenCV image: %s" % str(e))
            return
        # 显示图像
        # cv2.imshow("RT_Frame", cv_image)
        # cv2.waitKey(1)

    def charuco_rgb_image_callback(self, msg):
        self.charuco_rgb_image = msg
    
    def charuco_detect_result_callback(self, msg):
        self.charuco_detect_result = msg

    def save_data(self, i):
        # 检查数据的时效性
        current_time = self.get_clock().now().to_msg().sec
        if abs(self.rgb_image.header.stamp.sec - current_time) > 2:
            self.get_logger().error("rgb image timestamp is old")
            sys.exit()
        if abs(self.charuco_detect_result.header.stamp.sec - current_time) > 2:
            self.get_logger().error("charuco_detect_result timestamp is old")
            sys.exit()
        
        rgb_image = copy.deepcopy(self.rgb_image)
        charuco_pose = [
            self.charuco_detect_result.pose.position.x,
            self.charuco_detect_result.pose.position.y,
            self.charuco_detect_result.pose.position.z,
            self.charuco_detect_result.pose.orientation.x,
            self.charuco_detect_result.pose.orientation.y,
            self.charuco_detect_result.pose.orientation.z,
            self.charuco_detect_result.pose.orientation.w,
        ]
        robot_pose = self.get_current_robot_pose()
        print("charuco_pose: ", charuco_pose)
        print("robot pose: ", robot_pose)
        
        charuco_rgb_image = copy.deepcopy(self.charuco_rgb_image)
        charuco_rgb_image = self.cv_bridge.imgmsg_to_cv2(charuco_rgb_image, desired_encoding="bgr8")
        # cv2.imshow("Charuco_Image", charuco_rgb_image)
        
        rgb_image_filename =  os.path.join(self.data_save_dir, "{0}_rgb.png".format(i))
        rgb_image = self.cv_bridge.imgmsg_to_cv2(rgb_image, desired_encoding="bgr8")
        # cv2.imshow("Save_Image", rgb_image)
        cv2.imwrite(rgb_image_filename, rgb_image)

        return robot_pose, charuco_pose

    def calibration(self, robot_poses, charuco_poses, cali_type):
        result = None
        print(cali_type == 'eye_in_hand')
        print(cali_type == 'eye_to_hand')
        if cali_type not in ["eye_to_hand", "eye_in_hand"]:
            raise Exception("不支持的标定类型：{0}".format(cali_type))
        result = self.calibrator.calibration(robot_poses, charuco_poses, cali_type)
        msg_info = "\ncalibration result:\n"
        msg_info += "\ttype: {0}".format(cali_type)
        msg_info += "\tpose: {0}".format(result)
        self.get_logger().info(msg_info)
        return result
    
    def collect_data(self):
        # 控制机器人运动到指定的关节位置
        self.get_logger().info("开始采集数据：")
        time.sleep(3)
        robot_poses = []
        charuco_poses = []
        for i, pose in enumerate(self.pose_list):
            self.get_logger().info("**** 准备运动到第{0}个点: {1}".format(i+1, pose))
            self.movel(pose)
            self.get_logger().info("到达，稳定3秒")
            time.sleep(5)
            self.get_logger().info("写入数据")
            robot_pose, charuco_pose = self.save_data(i)
            robot_poses.append(robot_pose)
            charuco_poses.append(charuco_pose)
            if i >= 3:
                result = self.calibration(robot_poses, charuco_poses, self.cali_type)
        self.get_logger().info("采集结束，数据保存在: {0}".format(self.data_save_dir))
        
        # 保存两组pose
        with open(self.pose_save_filepath, "a", newline='') as f:
            writer = csv.writer(f)
            for i in range(len(robot_poses)):
                writer.writerow(robot_poses[i])
                writer.writerow(charuco_poses[i])
                writer.writerow("---")
                print(robot_poses[i])
                print(charuco_poses[i])
                print("---")

        # 计算并保存标定结果
        result = self.calibration(robot_poses, charuco_poses, self.cali_type)
        with open(self.cali_result_save_filepath, "+w") as f:
            writer = csv.writer(f)
            writer.writerow(result)
        
        self.get_logger().info("采集结束")


def main():
    rclpy.init()

    # 设置要采集的pose
    pose_list = [
        [-0.14228804409503937, 0.863705575466156, 0.11804646253585815, 0.03905317187811211, 0.9985614619578895, 0.0335789319147275, -0.01491012375022812],
        [-0.4124646484851837, 0.8637003898620605, 0.11807068437337875, 0.08286932003318248, 0.9864177680687719, 0.026870896822671297, 0.139250197627],
        [-0.40032461285591125, 0.9641211032867432, 0.022890515625476837, 0.245412058239377, 0.9496102994053475, 0.004826795101502565, 0.19490998687354946],
        [-0.21065159142017365, 0.9495015144348145, -0.0006374541553668678, 0.34957594620731697, 0.9364063530478303, 0.02833127835851432, 0.011710613625841623],
        [-0.21303589642047882, 0.8633254766464233, -0.12211095541715622, -0.6043981032263916, -0.7943707635766036, -0.017816735228533616, 0.05797056785007597],
        [-0.07714412361383438, 0.920989453792572, 0.0172348003834486, -0.40204216024743317, -0.9080655992369573, 0.029863175027401087, 0.11352162632417517],
        [-0.0923958271741867, 0.9143767952919006, -0.04572778567671776, 0.07285809654237832, -0.9947876985203526, -0.030675173957123745, 0.06440626012665017],
        [-0.09442303329706192, 0.9239593148231506, -0.06402967870235443, 0.35060824021470843, -0.9314141214233124, -0.08319123622686543, 0.05119389145035069],
        [-0.168411523103714, 0.9773350358009338, 0.005679694004356861, 0.6283982393914979, -0.7758944180950543, -0.05499899880397946, -0.008866500389812484],
        [-0.29537802934646606, 0.9315305948257446, -0.02436451055109501, -0.5231577343529772, 0.849220511676653, -0.0014957344925443927, 0.0716119425279831],
        [-0.09264256060123444, 0.977601170539856, -0.05974526330828667, 0.4931103978429995, -0.8654214838343022, -0.08818101846262989, -0.01057822480601723],
        [-0.08966469764709473, 0.9664449691772461, -0.07712967693805695, 0.2788715529431163, -0.9568051718503457, -0.04238368896798142, 0.07041408232016147],
        [-0.2666124403476715, 0.950227677822113, 0.0007983400137163699, 0.08712891147673628, -0.9955359915583535, -0.031991203390188384, 0.01712323574715999],
        [-0.3738113343715668, 0.8935502767562866, -0.009381866082549095, 0.06509668411905226, -0.991965492626045, -0.03876546716187563, -0.1013120018141644],
        [-0.34605395793914795, 0.9017831087112427, 0.041608791798353195, 0.2139046764335665, 0.9688052485276919, 0.025078288816111457, 0.12260611426476335]
    ]

    collector = CalibrationDataCollector(pose_list)
    # print(collector.get_current_joint_position())
    # while True:
    #     robot_pose = collector.get_current_robot_pose()
    #     print(robot_pose)
    #     input("wait key")

    rclpy.spin(collector)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
