import os
import time
from datetime import datetime
import rclpy
from rclpy.node import Node


def decimal_to_dms(decimal_degrees):
    """
    将十进制度数转换为度分格式 (DDDMM.MMM)。
    """
    degrees = int(decimal_degrees)
    minutes = (decimal_degrees - degrees) * 60
    return f"{degrees:02d}{minutes:06.3f}"

def generate_gprmc(latitude, longitude):
    """
    生成一条模拟的 GPRMC 数据。
    """
    now = datetime.utcnow()
    time_str = now.strftime("%H%M%S.00")  # UTC时间
    date_str = now.strftime("%d%m%y")  # 日期
    speed = "000.5"  # 节为单位的速度
    course = "054.7"  # 航向

    # 格式化纬度和经度
    latitude_str = decimal_to_dms(latitude)
    longitude_str = decimal_to_dms(longitude)

    # 构造 GPRMC 数据
    gprmc = f"GPRMC,{time_str},A,{latitude_str},N,{longitude_str},E,{speed},{course},{date_str},003.1,W,A,V"
    
    # 计算校验和
    checksum = calculate_checksum(gprmc)
    
    # 返回完整的 NMEA 句子
    return f"${gprmc}*{checksum:02X}"


def calculate_checksum(sentence):
    """
    计算 NMEA 句子的校验和。
    """
    checksum = 0
    for char in sentence:
        checksum ^= ord(char)
    return checksum


class GPRMCWriterNode(Node):
    """
    一个 ROS 2 节点，周期性地向 /dev/ttyUSB0 写入 GPRMC 数据。
    """

    def __init__(self):
        super().__init__("gprmc_writer")

        # 声明参数
        self.declare_parameter("latitude", 23.2475)  # 默认纬度
        self.declare_parameter("longitude", 113.5659)  # 默认经度
        self.declare_parameter("device", "/dev/ttyUSB0")  # 默认设备路径
        self.declare_parameter("interval", 1.0)  # 默认写入间隔（秒）

        # 获取参数
        self.device = self.get_parameter("device").get_parameter_value().string_value
        self.latitude = self.get_parameter("latitude").get_parameter_value().double_value
        self.longitude = self.get_parameter("longitude").get_parameter_value().double_value
        self.interval = self.get_parameter("interval").get_parameter_value().double_value

        # 等待设备准备好
        self.wait_for_device()

        try:
            # 打开设备文件
            self.tty = open(self.device, "w")
        except PermissionError:
            self.get_logger().error(f"无法访问 {self.device}，请检查权限或使用 sudo 运行。")
            raise

        self.get_logger().info(f"成功打开设备 {self.device}，开始周期性写入 GPRMC 数据。")
        self.get_logger().info(f"使用纬度 {self.latitude} 和经度 {self.longitude}。")

        # 创建定时器，周期性写入数据
        self.timer = self.create_timer(self.interval, self.write_gprmc)

    def wait_for_device(self):
        """等待设备准备好（设备路径存在）"""
        while not os.path.exists(self.device):
            self.get_logger().info(f"等待设备 {self.device} 准备好...")
            time.sleep(1)  # 每秒检查一次
        self.get_logger().info(f"设备 {self.device} 已准备好!")

    def write_gprmc(self):
        """
        向设备写入 GPRMC 数据。
        """
        try:
            gprmc_data = generate_gprmc(self.latitude, self.longitude)
            self.tty.write(gprmc_data + "\n")
            self.tty.flush()  # 确保数据立即写入
            self.get_logger().info(f"写入: {gprmc_data}")
        except Exception as e:
            self.get_logger().error(f"写入时发生错误: {e}")

    def destroy_node(self):
        """
        清理资源，关闭文件。
        """
        self.get_logger().info("清理资源，关闭设备文件。")
        if hasattr(self, "tty") and self.tty:
            self.tty.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = GPRMCWriterNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if "node" in locals():
            node.destroy_node()
        rclpy.shutdown()
