import time
import serial
from rclpy.logging import get_logger


class Gripper():
    def __init__(self, port):
        self.comm = serial.Serial(port=port, baudrate=115200, parity='N', stopbits=1, bytesize=8)
        self.logger = get_logger('Gripper')
        if not self.comm.is_open:
            self.logger.error("open comm failed")
            raise Exception("open comm failed")
        self.logger.info(f"gripper controller ready, port name: {port}")

    def check_sum(self, s, length, data):
        sum = 0
        for i in range(length):
            sum = sum + data[s+i]
        return sum & 0xff

    def send_cmd(self, id, angle):
        angle = (int)(angle * 1000)
        cmd = [0x3E, 0xA3, 0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        cmd[2] = id & 0xff
        cmd[4] = self.check_sum(0, 4, cmd)
        cmd[5] = int(angle) & 0xff
        cmd[6] = (int(angle) >> 8) & 0xff
        cmd[7] = (int(angle) >> 16) & 0xff
        cmd[8] = (int(angle) >> 24) & 0xff
        cmd[9] = (int(angle) >> 32) & 0xff
        cmd[10] = (int(angle) >> 40) & 0xff
        cmd[11] = (int(angle) >> 48) & 0xff
        cmd[12] = (int(angle) >> 56) & 0xff
        cmd[13] = self.check_sum(5, 8, cmd)
        self.comm.write(cmd)

    def open(self):
        # self.send_cmd(1, -60)
        self.send_cmd(1, 10)
        time.sleep(0.5)
        self.logger.info("open gripper")
    
    def close(self):
        self.send_cmd(1, -95)
        time.sleep(0.5)
        self.logger.info("close gripper")



if __name__ == "__main__":
    gripper = Gripper("/dev/ttyACM1")
    # gripper.open()
    # time.sleep(1)

    # gripper.close()
    gripper.open()  