#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from sensor_msgs.msg import Imu
import numpy as np
import math
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class ImuSubscriber(Node):
    def __init__(self):
        super().__init__("imu_subscriber")
        self.subscription = self.create_subscription(
            Imu,
            "/imu",  # Modify based on your actual IMU topic name
            self.imu_callback,
            10,
        )

        # Data queue for safe data transfer between threads
        self.data_queue = queue.Queue()

        # Store time and orientation data
        self.timestamps = []
        self.roll_angles = []
        self.pitch_angles = []
        self.yaw_angles = []

        # Store raw IMU data
        self.latest_raw_data = {
            "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
            "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0},
        }

        self.start_time = None
        self.running = True

        self.get_logger().info("IMU subscriber started, ready to visualize orientation and raw data...")

    def imu_callback(self, msg):
        # Get quaternion
        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        qw = msg.orientation.w

        # Convert quaternion to Euler angles (roll, pitch, yaw)
        euler = self.quaternion_to_euler(qx, qy, qz, qw)
        roll = euler[0]
        pitch = euler[1]
        yaw = euler[2]

        # Record current time and orientation angles
        if self.start_time is None:
            self.start_time = self.get_clock().now().nanoseconds / 1e9
            current_time = 0
        else:
            current_time = self.get_clock().now().nanoseconds / 1e9 - self.start_time

        # Store raw IMU data
        self.latest_raw_data["angular_velocity"] = {
            "x": msg.angular_velocity.x,
            "y": msg.angular_velocity.y,
            "z": msg.angular_velocity.z,
        }

        self.latest_raw_data["linear_acceleration"] = {
            "x": msg.linear_acceleration.x,
            "y": msg.linear_acceleration.y,
            "z": msg.linear_acceleration.z,
        }

        self.latest_raw_data["orientation"] = {"x": qx, "y": qy, "z": qz, "w": qw}

        # Put new data in the queue
        self.data_queue.put(
            (
                current_time,
                math.degrees(roll),
                math.degrees(pitch),
                math.degrees(yaw),
                self.latest_raw_data,
            )
        )

        self.get_logger().debug(
            f"Time: {current_time:.2f}s, Roll: {math.degrees(roll):.2f}°, "
            f"Pitch: {math.degrees(pitch):.2f}°, Yaw: {math.degrees(yaw):.2f}°"
        )

    def quaternion_to_euler(self, x, y, z, w):
        """Convert quaternion to Euler angles (roll, pitch, yaw)"""
        # Check if quaternion is valid
        if x == 0 and y == 0 and z == 0 and w == 0:
            return (0, 0, 0)

        # Normalize quaternion
        norm = math.sqrt(x * x + y * y + z * z + w * w)
        x /= norm
        y /= norm
        z /= norm
        w /= norm

        # Convert to Euler angles
        # roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)

        # yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return (roll, pitch, yaw)


class ImuVisualizer:
    def __init__(self, root, imu_subscriber):
        self.root = root
        self.root.title("IMU Data Visualization")
        self.root.geometry("800x600")
        self.imu_subscriber = imu_subscriber

        # Create the main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create orientation angle display section
        angle_frame = ttk.LabelFrame(main_frame, text="Orientation Angles (degrees)")
        angle_frame.pack(fill=tk.X, pady=5)

        # Roll, Pitch, Yaw labels and values
        ttk.Label(angle_frame, text="Roll:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.roll_var = tk.StringVar(value="0.00")
        ttk.Label(angle_frame, textvariable=self.roll_var, width=10).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(angle_frame, text="Pitch:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.pitch_var = tk.StringVar(value="0.00")
        ttk.Label(angle_frame, textvariable=self.pitch_var, width=10).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(angle_frame, text="Yaw:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.yaw_var = tk.StringVar(value="0.00")
        ttk.Label(angle_frame, textvariable=self.yaw_var, width=10).grid(row=0, column=5, padx=5, pady=2)

        # Create raw data display section
        raw_data_frame = ttk.LabelFrame(main_frame, text="Raw IMU Data")
        raw_data_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Angular velocity section
        ang_vel_frame = ttk.LabelFrame(raw_data_frame, text="Angular Velocity (rad/s)")
        ang_vel_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ang_vel_frame, text="X:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.ang_vel_x_var = tk.StringVar(value="0.00")
        ttk.Label(ang_vel_frame, textvariable=self.ang_vel_x_var, width=10).grid(
            row=0, column=1, padx=5, pady=2
        )

        ttk.Label(ang_vel_frame, text="Y:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.ang_vel_y_var = tk.StringVar(value="0.00")
        ttk.Label(ang_vel_frame, textvariable=self.ang_vel_y_var, width=10).grid(
            row=0, column=3, padx=5, pady=2
        )

        ttk.Label(ang_vel_frame, text="Z:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.ang_vel_z_var = tk.StringVar(value="0.00")
        ttk.Label(ang_vel_frame, textvariable=self.ang_vel_z_var, width=10).grid(
            row=0, column=5, padx=5, pady=2
        )

        # Linear acceleration section
        lin_acc_frame = ttk.LabelFrame(raw_data_frame, text="Linear Acceleration (m/s²)")
        lin_acc_frame.pack(fill=tk.X, pady=5)

        ttk.Label(lin_acc_frame, text="X:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.lin_acc_x_var = tk.StringVar(value="0.00")
        ttk.Label(lin_acc_frame, textvariable=self.lin_acc_x_var, width=10).grid(
            row=0, column=1, padx=5, pady=2
        )

        ttk.Label(lin_acc_frame, text="Y:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.lin_acc_y_var = tk.StringVar(value="0.00")
        ttk.Label(lin_acc_frame, textvariable=self.lin_acc_y_var, width=10).grid(
            row=0, column=3, padx=5, pady=2
        )

        ttk.Label(lin_acc_frame, text="Z:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.lin_acc_z_var = tk.StringVar(value="0.00")
        ttk.Label(lin_acc_frame, textvariable=self.lin_acc_z_var, width=10).grid(
            row=0, column=5, padx=5, pady=2
        )

        # Quaternion section
        quat_frame = ttk.LabelFrame(raw_data_frame, text="Quaternion")
        quat_frame.pack(fill=tk.X, pady=5)

        ttk.Label(quat_frame, text="X:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.quat_x_var = tk.StringVar(value="0.00")
        ttk.Label(quat_frame, textvariable=self.quat_x_var, width=10).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(quat_frame, text="Y:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.quat_y_var = tk.StringVar(value="0.00")
        ttk.Label(quat_frame, textvariable=self.quat_y_var, width=10).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(quat_frame, text="Z:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.quat_z_var = tk.StringVar(value="0.00")
        ttk.Label(quat_frame, textvariable=self.quat_z_var, width=10).grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(quat_frame, text="W:").grid(row=0, column=6, padx=5, pady=2, sticky=tk.W)
        self.quat_w_var = tk.StringVar(value="0.00")
        ttk.Label(quat_frame, textvariable=self.quat_w_var, width=10).grid(row=0, column=7, padx=5, pady=2)

        # Plot section for orientation angles
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Angle (degrees)")
        self.ax.set_title("IMU Orientation Angles Over Time")
        self.ax.grid(True)

        (self.roll_line,) = self.ax.plot([], [], "r-", label="Roll")
        (self.pitch_line,) = self.ax.plot([], [], "g-", label="Pitch")
        (self.yaw_line,) = self.ax.plot([], [], "b-", label="Yaw")
        self.ax.legend()

        # Set initial axis limits
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-180, 180)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)

        # Schedule the update function
        self.root.after(100, self.update_display)

    def update_display(self):
        # Get all available data from the queue
        while not self.imu_subscriber.data_queue.empty():
            try:
                timestamp, roll, pitch, yaw, raw_data = self.imu_subscriber.data_queue.get_nowait()

                # Update orientation angle variables
                self.roll_var.set(f"{roll:.2f}")
                self.pitch_var.set(f"{pitch:.2f}")
                self.yaw_var.set(f"{yaw:.2f}")

                # Update raw data variables
                # Angular velocity
                self.ang_vel_x_var.set(f"{raw_data['angular_velocity']['x']:.4f}")
                self.ang_vel_y_var.set(f"{raw_data['angular_velocity']['y']:.4f}")
                self.ang_vel_z_var.set(f"{raw_data['angular_velocity']['z']:.4f}")

                # Linear acceleration
                self.lin_acc_x_var.set(f"{raw_data['linear_acceleration']['x']:.4f}")
                self.lin_acc_y_var.set(f"{raw_data['linear_acceleration']['y']:.4f}")
                self.lin_acc_z_var.set(f"{raw_data['linear_acceleration']['z']:.4f}")

                # Quaternion
                self.quat_x_var.set(f"{raw_data['orientation']['x']:.4f}")
                self.quat_y_var.set(f"{raw_data['orientation']['y']:.4f}")
                self.quat_z_var.set(f"{raw_data['orientation']['z']:.4f}")
                self.quat_w_var.set(f"{raw_data['orientation']['w']:.4f}")

                # Store data for plotting
                self.imu_subscriber.timestamps.append(timestamp)
                self.imu_subscriber.roll_angles.append(roll)
                self.imu_subscriber.pitch_angles.append(pitch)
                self.imu_subscriber.yaw_angles.append(yaw)

            except queue.Empty:
                break

        # Limit data points to keep the plot responsive
        max_points = 300
        if len(self.imu_subscriber.timestamps) > max_points:
            self.imu_subscriber.timestamps = self.imu_subscriber.timestamps[-max_points:]
            self.imu_subscriber.roll_angles = self.imu_subscriber.roll_angles[-max_points:]
            self.imu_subscriber.pitch_angles = self.imu_subscriber.pitch_angles[-max_points:]
            self.imu_subscriber.yaw_angles = self.imu_subscriber.yaw_angles[-max_points:]

        # Update the plot
        if self.imu_subscriber.timestamps:
            # Update line data
            self.roll_line.set_data(self.imu_subscriber.timestamps, self.imu_subscriber.roll_angles)
            self.pitch_line.set_data(self.imu_subscriber.timestamps, self.imu_subscriber.pitch_angles)
            self.yaw_line.set_data(self.imu_subscriber.timestamps, self.imu_subscriber.yaw_angles)

            # Update plot boundaries
            self.ax.set_xlim(
                min(self.imu_subscriber.timestamps),
                max(self.imu_subscriber.timestamps) + 0.1,
            )

            # Find min and max values across all angles
            all_angles = (
                self.imu_subscriber.roll_angles
                + self.imu_subscriber.pitch_angles
                + self.imu_subscriber.yaw_angles
            )

            if all_angles:
                ymin = min(all_angles) - 5
                ymax = max(all_angles) + 5
                self.ax.set_ylim(ymin, ymax)

            self.canvas.draw()

        # Schedule the next update
        self.root.after(100, self.update_display)


def ros_spin(node):
    """Run ROS2 node in a separate thread"""
    rclpy.spin(node)


def main(args=None):
    # Initialize ROS2
    rclpy.init(args=args)

    # Create IMU subscriber node
    imu_subscriber = ImuSubscriber()

    # Create ROS2 thread
    ros_thread = threading.Thread(target=ros_spin, args=(imu_subscriber,))
    ros_thread.daemon = True
    ros_thread.start()

    # Create Tkinter application
    root = tk.Tk()
    app = ImuVisualizer(root, imu_subscriber)

    try:
        # Run the Tkinter main loop
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        imu_subscriber.running = False
        imu_subscriber.destroy_node()
        rclpy.shutdown()
        print("Program exited")


if __name__ == "__main__":
    main()
