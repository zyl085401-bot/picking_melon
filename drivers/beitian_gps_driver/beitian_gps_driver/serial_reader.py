import rclpy
from rclpy.node import Node
import io
import pynmea2
import serial
import threading
import time

from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import Pose2D

class SerialReaderNode(Node):
    def __init__(self):
        super().__init__('serial_reader')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('defualt_latitude', 23.14)
        self.declare_parameter('defualt_longitude', 113.29)
        
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.default_latitude = self.get_parameter('defualt_latitude').get_parameter_value().double_value
        self.default_longitude = self.get_parameter('defualt_longitude').get_parameter_value().double_value

        self.NavsatFix_pub = self.create_publisher(NavSatFix, 'gps/fix', 10)
        self.Pose_pub = self.create_publisher(Pose2D, 'gps/pose', 10)
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=5.0)
            self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser), errors='ignore')
            self.thread = threading.Thread(target=self.read_serial_data)
            self.thread.daemon = True  # This makes sure the thread will exit when the main program exits
            self.thread.start()
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port: {e}')

    def read_serial_data(self):
        while rclpy.ok():
            try:
                line = self.sio.readline()
                msg = pynmea2.parse(line)

                if isinstance(msg, pynmea2.types.talker.RMC):
                    # self.get_logger().info(repr(msg))
                    gps_raw = NavSatFix()
                    gps_raw.header.stamp = self.get_clock().now().to_msg()
                    gps_raw.header.frame_id = 'gps'
                    gps_raw.altitude = 0.0
                    gps_raw.position_covariance = [0.0] * 9
                    gps_raw.position_covariance_type = 2

                    pose = Pose2D()
                    pose.x = 0.0
                    pose.y = 0.0

                    if 1 or msg.is_valid:
                        gps_raw.latitude = msg.latitude
                        gps_raw.longitude = msg.longitude
                        
                        pose.theta = float(msg.true_course)
                    else:
                        self.get_logger().warn('Gps data is not available. Use default data.(%f, %f)' % (self.default_latitude, self.default_longitude))
                        gps_raw.latitude = self.default_latitude
                        gps_raw.longitude = self.default_longitude
                        pose.theta = 0.0

                    self.NavsatFix_pub.publish(gps_raw)
                    self.Pose_pub.publish(pose)
                time.sleep(0.05)

            except serial.SerialException as e:
                self.get_logger().error(f'Device error: {e}')
            except pynmea2.ParseError as e:
                # self.get_logger().warning(f'Parse error: {e}')
                pass

def main(args=None):
    rclpy.init(args=args)
    node = SerialReaderNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
