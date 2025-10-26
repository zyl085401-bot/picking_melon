"""
@Descripttion: 手眼标定
@version: 1.0
@Author: 崔译文
@Date: 2024-03-18 14:41:48
@LastEditors: 崔译文
@LastEditTime: 2024-03-21 17:48:06
"""

import cv2
import numpy as np 
from .transformations import quaternion_matrix, quaternion_from_matrix

class HandeyeCalibrator:
    def __init__(self):
        self.AVAILABLE_ALGORITHMS = {
            "Tsai-Lenz": cv2.CALIB_HAND_EYE_TSAI,
            "Park": cv2.CALIB_HAND_EYE_PARK,
            "Horaud": cv2.CALIB_HAND_EYE_HORAUD,
            "Andreff": cv2.CALIB_HAND_EYE_ANDREFF,
            "Daniilidis": cv2.CALIB_HAND_EYE_DANIILIDIS,
        }
    
    def calibration(self, robot_poses: list[list], target_poses: list[list], cali_type: str, method: str = "Horaud"):
        R_gripper2base = []
        t_gripper2base = []
        R_target2cam = []
        t_target2cam = []
        
        assert len(robot_poses) == len(target_poses)
        for i in range(len(robot_poses)):
            pose = robot_poses[i]
            assert len(pose) == 7
            t_gripper2base.append(np.array(pose[0:3]).reshape(-1, 1))
            R_gripper2base.append(quaternion_matrix(pose[3:])[:3, :3])
            
            pose = target_poses[i]
            assert len(pose) == 7
            t_target2cam.append(np.array(pose[0:3]).reshape(-1, 1))
            R_target2cam.append(quaternion_matrix(pose[3:])[:3, :3])
        
        R, t = self.calibration_cv2(R_gripper2base, t_gripper2base, R_target2cam, t_target2cam, cali_type, method=method)
        temp = np.zeros((4,4))
        temp[:3, :3] = R
        temp[3, 3] = 1
        quat = quaternion_from_matrix(temp) # quat = [x, y, z, w]
        tran = t.flatten()
        pose = [ tran[0], tran[1], tran[2], quat[0], quat[1], quat[2], quat[3]]
        return pose
    
    def calibration_cv2(self, R_gripper2base, t_gripper2base, R_target2cam, t_target2cam, cali_type="eye_to_hand", method="Horaud"):
        R = None
        t = None
        if cali_type == "eye_in_hand":  # 摄像头固定在手臂末端，标定板固定在base坐标系
            R, t = cv2.calibrateHandEye(
                R_gripper2base=R_gripper2base,
                t_gripper2base=t_gripper2base,
                R_target2cam=R_target2cam,
                t_target2cam=t_target2cam,
                method=self.AVAILABLE_ALGORITHMS[method],
            )
        elif cali_type == "eye_to_hand":  # 摄像头固定在base坐标系，标定板固定在手臂末端
            R_base2gripper, t_base2gripper = [], []
            for R, t in zip(R_gripper2base, t_gripper2base):
                R_b2g = R.T
                t_b2g = -R_b2g @ t
                R_base2gripper.append(R_b2g)
                t_base2gripper.append(t_b2g)
            R, t = cv2.calibrateHandEye(
                R_gripper2base=R_base2gripper,
                t_gripper2base=t_base2gripper,
                R_target2cam=R_target2cam,
                t_target2cam=t_target2cam,
                method=self.AVAILABLE_ALGORITHMS[method],
            )
        return R, t
