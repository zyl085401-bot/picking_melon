#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import numpy as np

class CharucoPosePublisher(Node):
    def __init__(self):
        super().__init__('charuco_pose_publisher')
        self.get_logger().info("Charuco Pose Publisher Node Started")

        # 订阅图像话题
        self.subscription = self.create_subscription(
            Image, '/camera/camera_base/color/image_raw', self.image_callback, 10)

        # 发布位姿话题
        self.pose_pub = self.create_publisher(PoseStamped, '/camera/camera_base/color/charuco/pose', 10)

        self.bridge = CvBridge()

        # === Charuco 棋盘配置 ===
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.board = cv2.aruco.CharucoBoard_create(
            squaresX=7, squaresY=5, squareLength=0.025, markerLength=0.018,
            dictionary=self.aruco_dict)


        # 相机内参（必须用你的标定结果替换）
        self.camera_matrix = np.array([[909.9423828125, 0.0, 648.8924560546875],
                                       [0.0, 909.9952392578125, 359.1855163574219],
                                       [0.0, 0.0, 1.0]], dtype=np.float32)
        self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)

    def image_callback(self, msg):
        # 1. 转换图像
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # 2. 检测 ArUco 标记
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict)

        if ids is None or len(ids) == 0:
            self.get_logger().warn("未检测到任何 ArUco 标记，跳过本帧")
            return

        # 3. 插值 Charuco 角点
        retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            markerCorners=corners, markerIds=ids, image=gray, board=self.board)

        if retval is None or retval < 4:
            self.get_logger().warn(f"检测到的 Charuco 角点不足: {retval}, 无法估计位姿")
            return

        # 4. 位姿估计
        retval, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
            charuco_corners, charuco_ids, self.board,
            self.camera_matrix, self.dist_coeffs,
            rvec=None,      # 必须显式传入
            tvec=None       # 必须显式传入
        )

        if retval is None or retval <= 0:
            self.get_logger().warn("Charuco 位姿估计失败 (retval <= 0)")
            return

        # 5. 发布位姿
        self.publish_pose(rvec, tvec)
        self.get_logger().info(
            f"发布 Charuco 位姿: tvec=({tvec[0][0]:.3f}, {tvec[1][0]:.3f}, {tvec[2][0]:.3f})"
        )

    def publish_pose(self, rvec, tvec):
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = "camera_base_link"

        # 平移
        pose_msg.pose.position.x = float(tvec[0])
        pose_msg.pose.position.y = float(tvec[1])
        pose_msg.pose.position.z = float(tvec[2])

        # 旋转：Rodrigues 向量转旋转矩阵再转四元数
        R, _ = cv2.Rodrigues(rvec)
        quat = self.rotation_matrix_to_quaternion(R)
        pose_msg.pose.orientation.x = quat[0]
        pose_msg.pose.orientation.y = quat[1]
        pose_msg.pose.orientation.z = quat[2]
        pose_msg.pose.orientation.w = quat[3]

        self.pose_pub.publish(pose_msg)
        self.get_logger().info(f"Published Charuco Pose: tvec={tvec.ravel()}")

    @staticmethod
    def rotation_matrix_to_quaternion(R):
        """将旋转矩阵转为四元数 (x, y, z, w)"""
        q = np.empty((4, ), dtype=np.float64)
        t = np.trace(R)
        if t > 0.0:
            t = np.sqrt(t + 1.0)
            q[3] = 0.5 * t
            t = 0.5 / t
            q[0] = (R[2, 1] - R[1, 2]) * t
            q[1] = (R[0, 2] - R[2, 0]) * t
            q[2] = (R[1, 0] - R[0, 1]) * t
        else:
            i = 0
            if R[1, 1] > R[0, 0]:
                i = 1
            if R[2, 2] > R[i, i]:
                i = 2
            j = (i + 1) % 3
            k = (i + 2) % 3
            t = np.sqrt(R[i, i] - R[j, j] - R[k, k] + 1.0)
            q[i] = 0.5 * t
            t = 0.5 / t
            q[3] = (R[k, j] - R[j, k]) * t
            q[j] = (R[j, i] + R[i, j]) * t
            q[k] = (R[k, i] + R[i, k]) * t
        return q

def main():
    rclpy.init()
    node = CharucoPosePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
