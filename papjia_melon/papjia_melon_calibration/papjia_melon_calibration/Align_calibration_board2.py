#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster, Buffer, TransformListener
import transforms3d
import numpy as np
import transforms3d.euler

class CameraBaseSolver(Node):
    def __init__(self):
        super().__init__("camera_base_solver")
        print("c程序开始")
        # 发布底盘相机相对于 base_link 的 TF
        self.tf_broadcaster = TransformBroadcaster(self)

        # 订阅棋盘 Pose
        self.create_subscription(PoseStamped, "/camera/camera_hand/color/charuco/pose", self.camera_hand_color_optical_frame_bo, 10)
        self.create_subscription(PoseStamped, "/camera/camera_base/color/charuco/pose", self.camera_base_color_optical_frame_bo, 10)

        # TF 缓冲区（获取 base_link -> ee_link）
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 已知手眼标定结果：arm_link_6 -> camera_hand_link  camera 坐标系 到 gripper 
        # ⚠️ 这里填你的手眼标定结果
        self.T_arm_link_6_ch = {
            "trans": np.array([0.037639, 0.006959, 0.198392]),  # 示例，手掌相机在末端正前方 10cm
            "quat": np.array([-0.6987285, 0.60427557, -0.2377273, 0.21476333])
        }
        print("计算得到T_arm_link_6_ch")

        # ✅ 定义 optical_frame → camera_link 的变换（绕 X 旋转 -90°）
        self.T_optical_to_link = {
            "trans": np.array([0.0, 0.0, 0.0]),
            "quat": transforms3d.euler.euler2quat(-np.pi/2, 0, -np.pi/2, axes='sxyz')
        }

        self.hand_pose = None
        self.base_pose = None

        self.create_timer(0.1, self.broadcast_tf)

    def camera_hand_color_optical_frame_bo(self, msg):
        self.hand_pose = msg

    def camera_base_color_optical_frame_bo(self, msg):
        self.base_pose = msg

    def pose_to_T(self, pose):
        return {
            "trans": np.array([pose.position.x, pose.position.y, pose.position.z]),
            "quat": np.array([pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w])
        }

    # def invert_T(self, T):
    #     q_inv = transforms3d.quaternions.qinverse(T["quat"])
    #     t_inv = -transforms3d.quaternions.qrotate(q_inv, T["trans"])
    #     return {"trans": t_inv, "quat": q_inv}
    
    def invert_T(self, T):
        q_inv = transforms3d.quaternions.qinverse(T["quat"])
        t_inv = -transforms3d.quaternions.rotate_vector(T["trans"], q_inv)
        return {"trans": t_inv, "quat": q_inv}

    def multiply_T(self, A, B):
        q = transforms3d.quaternions.qmult(A["quat"], B["quat"])
        # 使用 rotate_vector 替代 qrotate
        t = transforms3d.quaternions.rotate_vector(B["trans"], A["quat"]) + A["trans"]
        return {"trans": t, "quat": q}

    def broadcast_tf(self):
        if self.hand_pose is None or self.base_pose is None:
            print("hand_pose is None or self.base_pose is None")
            return

        try:
            # (1) 获取 base_link -> arm_link_6
            tf_ee = self.tf_buffer.lookup_transform("base_link", "arm_link_6", rclpy.time.Time())
            T_base_arm_link_6 = {
                "trans": np.array([tf_ee.transform.translation.x,
                                tf_ee.transform.translation.y,
                                tf_ee.transform.translation.z]),
                "quat": np.array([tf_ee.transform.rotation.x,
                                tf_ee.transform.rotation.y,
                                tf_ee.transform.rotation.z,
                                tf_ee.transform.rotation.w])
            }
            print("获取 base_link -> arm_link_6")

            # (2) base_link -> camera_hand
            T_base_ch = self.multiply_T(T_base_arm_link_6, self.T_arm_link_6_ch)
            print("获取 base_link -> camera_hand_link")

            # (3) 从相机观测计算
            T_ch_optical_bo  = self.pose_to_T(self.hand_pose.pose)  # camera_hand_optical → board
            # T_ch_bo = self.multiply_T(T_ch_optical_bo, self.T_optical_to_link)  # ✅ 转换到 link 坐标系
            T_ch_to_optical = self.invert_T(self.T_optical_to_link)
            T_ch_bo = self.multiply_T(T_ch_to_optical,T_ch_optical_bo)
            print("获取 camera_hand_link -> board")

            T_cb_optical_bo = self.pose_to_T(self.base_pose.pose)   # optical → board
            # T_cb_link_bo = self.multiply_T(T_cb_optical_bo, self.T_optical_to_link)  # ✅ 转换到 link 坐标系
            T_cb_to_optical = self.invert_T(self.T_optical_to_link)
            T_cb_bo = self.multiply_T(T_cb_to_optical, T_cb_optical_bo)
            print("获取 camera_base_link -> board")

            # (4) 计算 camera_base_link → camera_hand_link
            T_bo_ch = self.invert_T(T_ch_bo)
            T_cb_ch = self.multiply_T(T_cb_bo, T_bo_ch)
            print("获取 camera_base_link -> camera_hand_link")

            # 🔔 输出结果
            self.get_logger().info(f"T_cb_ch (camera_base_link → camera_hand_link):")
            self.get_logger().info(f"  Translation: {T_cb_ch['trans']}")
            self.get_logger().info(f"  Quaternion:  {T_cb_ch['quat']}")

            # (5) 计算 base_link → camera_base_link
            T_ch_cb = self.invert_T(T_cb_ch)
            T_base_cb = self.multiply_T(T_base_ch, T_ch_cb)
            print("获取 base_link -> camera_base_link")

            # (6) 发布 TF
            tf_msg = TransformStamped()
            tf_msg.header.stamp = self.get_clock().now().to_msg()
            tf_msg.header.frame_id = "base_link"
            tf_msg.child_frame_id = "camera_base_link"  # 假设 camera_base_link 是 base 相机的 link 坐标系
            tf_msg.transform.translation.x = T_base_cb["trans"][0]
            tf_msg.transform.translation.y = T_base_cb["trans"][1]
            tf_msg.transform.translation.z = T_base_cb["trans"][2]
            tf_msg.transform.rotation.x = T_base_cb["quat"][0]
            tf_msg.transform.rotation.y = T_base_cb["quat"][1]
            tf_msg.transform.rotation.z = T_base_cb["quat"][2]
            tf_msg.transform.rotation.w = T_base_cb["quat"][3]

            self.tf_broadcaster.sendTransform(tf_msg)
            self.get_logger().info("Published base_link → camera_base_link")

            # (7) 验证：棋盘在 base_link 下的坐标
            T_board_from_hand = self.multiply_T(T_base_ch, T_ch_bo)   # base_link -> board
            T_board_from_base = self.multiply_T(T_base_cb, T_cb_bo)   # base_link -> board

            self.get_logger().info("棋盘在 base_link 下的位置（两相机估计对比）:")
            self.get_logger().info(f"  From hand_camera: {T_board_from_hand['trans']}")
            self.get_logger().info(f"  From base_camera: {T_board_from_base['trans']}")


        except Exception as e:
            self.get_logger().warn(f"TF not ready: {e}")

def main():
    rclpy.init()
    node = CameraBaseSolver()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()

