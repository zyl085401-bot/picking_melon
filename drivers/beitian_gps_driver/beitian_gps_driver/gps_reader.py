import io
import pynmea2
import serial
import threading
import time
# import transforms3d as tfs
import rclpy
import math
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import NavSatFix, Imu
from geometry_msgs.msg import PoseStamped, Quaternion
from beitian_gps_driver.utm import latlon_to_utm
from tutorial_interfaces.msg import Heading
# from tf_transformations import quaternion_from_euler
from transforms3d.euler import euler2quat


class GPSReaderNode(Node):
    def __init__(self):
        # 调用父类的构造函数
        super().__init__("serial_reader")

        # 声明端口参数
        self.declare_parameter("port", "/dev/ttyUSB0")
        # 声明波特率参数
        self.declare_parameter("baudrate", 115200)
        # 声明GPS坐标系名称
        self.declare_parameter("gps_frame", "gps_link")
        # 声明默认纬度参数
        self.declare_parameter("default_latitude", 23.140001)
        # 声明默认经度参数
        self.declare_parameter("default_longitude", 113.29)
        # 声明默认航向参数
        self.declare_parameter("default_course", 0.0)

        # 获取端口参数值
        self.port = self.get_parameter("port").get_parameter_value().string_value
        # 获取波特率参数值
        self.baudrate = self.get_parameter("baudrate").get_parameter_value().integer_value
        # 获取GPS坐标系名称
        self.gps_frame = self.get_parameter("gps_frame").get_parameter_value().string_value
        # 获取默认纬度参数值
        self.default_latitude = self.get_parameter("default_latitude").get_parameter_value().double_value
        # 获取默认经度参数值
        self.default_longitude = self.get_parameter("default_longitude").get_parameter_value().double_value
        # 获取默认航向参数值
        self.default_course = self.get_parameter("default_course").get_parameter_value().double_value

        # 创建GPS位置信息发布器
        self.gps_pub = self.create_publisher(NavSatFix, "gps/fix", 1)
        # 创建位置信息发布器
        self.pose_pub = self.create_publisher(PoseStamped, "gps/pose", 1)
        # 创建NMEA消息发布器
        self.raw_pub = self.create_publisher(String, "gps/raw_data", 1)
        # 创建GPS航向消息发布器
        self.gps_orientation_pub = self.create_publisher(Heading, "gps/orientation", 1)
        self.gps_imu_pub = self.create_publisher(Imu, "gps/imu", 3)
        # 初始化UTM坐标系
        self.init_utm = latlon_to_utm(self.default_latitude, self.default_longitude)

        self.get_logger().info(f"port: {self.port}")
        self.get_logger().info(f"baudrate: {self.baudrate}")
        self.get_logger().info(f"default_longitude: {self.default_longitude}")
        self.get_logger().info(f"default_latitude: {self.default_latitude}")
        self.get_logger().info(f"default_course: {self.default_course}")
        self.get_logger().info(f"gps_frame: {self.gps_frame}")
        self.get_logger().info(f"init utm: {self.init_utm}")

        try:
            # 初始化串口通信
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1.2)
            # self.ser.flush()
            # 包装串口对象以支持文本读写
            self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser), errors="ignore")
            # 创建线程读取串口数据
            self.thread = threading.Thread(target=self.read_serial_data)
            # 设置线程为守护线程
            self.thread.daemon = True  # This makes sure the thread will exit when the main program exits
            # 启动线程
            self.thread.start()
        except Exception as e:
            # 记录打开串口失败的错误信息
            self.get_logger().error(f"Failed to open serial port: {e}")

    def read_serial_data(self):
        while rclpy.ok():
            try:
                line = self.sio.readline()
                stamp = self.get_clock().now().to_msg()

                # print("line: ",line)

                if line.startswith("$GNTHS") or line.startswith("$GBTHS") :
                    print("=== THS ===", flush=True)
                    try:
                        # 移除起始符和校验和部分
                        data = line.strip().split('*')[0][7:]
                        fields = data.split(',')

                        heading = float(fields[0])  # 航向角
                        status = fields[1]          # 状态指示符

                        if status == 'A':
                            # 数据有效，处理航向信息
                            print(f"航向角: {heading}°")
                            # heading_msg = Heading()
                            # heading_msg.header.frame_id = self.gps_frame
                            # heading_msg.header.stamp = stamp
                            # heading_msg.heading_deg = heading

                            # # 2. 发布消息
                            # self.gps_orientation_pub.publish(heading_msg)

                            # 初始化IMU消息的固定参数
                            imu_msg = Imu()
                            imu_msg.header.frame_id = self.gps_frame
                            
                            # 假设角速度和线性加速度未知（设为0）
                            imu_msg.angular_velocity.x = 0.0
                            imu_msg.angular_velocity.y = 0.0
                            imu_msg.angular_velocity.z = 0.0
                            imu_msg.linear_acceleration.x = 0.0
                            imu_msg.linear_acceleration.y = 0.0
                            imu_msg.linear_acceleration.z = 0.0

                            heading = (360 - heading) % 360
                            # heading = 90
                            yaw = heading * math.pi / 180.0

                            self.get_logger().info(f"THS航向角 deg: {heading}, rad: {yaw}")

                            # 将航向角转换为四元数（绕Z轴旋转）
                            q = euler2quat(0.0, 0.0, yaw)
                            
                            # 填充IMU消息的方向
                            imu_msg.orientation = Quaternion(x=q[1], y=q[2], z=q[3], w=q[0])
                            imu_msg.header.stamp = self.get_clock().now().to_msg()

                            self.gps_imu_pub.publish(imu_msg)
                        else:
                            print("航向数据无效")
                    except (IndexError, ValueError) as e:
                        print(f"解析 THS 句型时出错: {e}")
                if line.startswith("$GNGGA"):
                    msg = pynmea2.parse(line)
                    if isinstance(msg, pynmea2.types.talker.GGA):
                        print("=== GGA ===", flush=True)
                        print(type(msg), flush=True)
                        print(f"纬度: {msg.latitude}° {msg.lat_dir}", flush=True)
                        print(f"经度: {msg.longitude}° {msg.lon_dir}", flush=True)
                        gps_msg = NavSatFix()
                        gps_msg.header.frame_id = self.gps_frame
                        gps_msg.header.stamp = stamp
                        gps_msg.position_covariance = [0.0] * 9
                        gps_msg.position_covariance_type = 2
                        gps_msg.latitude = msg.latitude
                        gps_msg.longitude = msg.longitude
                        gps_msg.altitude = 0.0
                        self.gps_pub.publish(gps_msg)

                    # current_utm = latlon_to_utm(msg.latitude, msg.longitude)
                    # pose_msg = PoseStamped()
                    # pose_msg.header.frame_id = "map"
                    # pose_msg.header.stamp = stamp
                    # pose_msg.pose.position.x = current_utm[0] - self.init_utm[0]
                    # pose_msg.pose.position.y = current_utm[1] - self.init_utm[1]
                    # pose_msg.pose.position.z = 0.0
                    # self.pose_pub.publish(pose_msg)

                    # raw_msg = String()  
                    # raw_msg.data = line
                    # self.raw_pub.publish(raw_msg)
                    # else:
                    #     self.get_logger().warn("Gps data is not available.")
            except serial.SerialException as e:
                self.get_logger().error(f"Device error: {e}")
            except pynmea2.ParseError as e:
                self.get_logger().warning(f"Parse error: {e}")
                pass


def main(args=None):
    rclpy.init(args=args)
    node = GPSReaderNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
