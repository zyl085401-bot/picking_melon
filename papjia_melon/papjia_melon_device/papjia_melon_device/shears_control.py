import serial
import time
from rclpy.logging import get_logger

class FramerRTU():
    @classmethod
    def generate_crc16_table(cls) -> list[int]:
        #生产CRC查找表
        result = []
        for byte in range(256):
            crc = 0x0000
            for _ in range(8):
                if (byte ^ crc) & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
                byte >>= 1
            result.append(crc)
        return result
    crc16_table: list[int] = [0]

    @classmethod
    def check_CRC(cls, data: bytes, check: int) -> bool:
        return cls.compute_CRC(data) == check

    @classmethod
    def compute_CRC(cls, data: bytes) -> int:
        """
        modbus 的 CRC 值从 0xffff 开始
        """
        crc = 0xFFFF
        for data_byte in data:
            idx = cls.crc16_table[(crc ^ int(data_byte)) & 0xFF]
            crc = ((crc >> 8) & 0xFF) ^ idx
        swapped = ((crc << 8) & 0xFF00) | ((crc >> 8) & 0x00FF)
        return swapped


class Shears():
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200) #设置串口
        self.FramerRTU = FramerRTU()
        # 初始化旋转方向
        self.logger = get_logger('Shears')
        # self.SendCommand("01 06 03 F3 00 00")
        self.logger.info(f"Shears controller ready, port name: {port}")

    def set_vel(self, direction):
        # 设置旋转方向
        if direction == 1:
            self.SendCommand("01 10 03 E7 00 02 04 00 01 4C 08")# 0001 4C08对应10进制 85000
        elif direction == -1:        
            self.SendCommand("01 10 03 E7 00 02 04 FF FF B1 E0")# FFFF B1E0对应10进制 -20000
        commands = [
            '01 10 03 80 00 01 02 00 06', #控制字给0x06
            '01 10 03 80 00 01 02 00 07', #控制字给0x07
            '01 10 03 80 00 01 02 00 0F', #控制字给0x0F
            '01 10 03 80 00 01 02 00 1F', #控制字给0x1F
            ]
        for command in commands:
            self.SendCommand(command)
        # self.SendCommand('01 10 03 80 00 01 02 00 1F') #使电机运动
        self.logger.info(f"Set vel, direction: {direction}")

    def first_set(self):
        first_commands = [
            '01 06 03 80 00 07', #控制字给0x07,电机失能
            '01 06 00 B1 00 00', #运动模式设置为位置控制模式
            '01 10 03 F8 00 02 04 00 01 86 A0', # 设置目标速度100000step/s
            '01 10 00 26 00 02 04 65 76 61 73', # 保存当前所有参数
            ]
        for first_command in first_commands:
            self.SendCommand(first_command)

    def stop(self):
        self.SendCommand("01 10 04 48 00 02 04 00 00 00 00")
        self.logger.info(f"Stop")

    def SendCommand(self, command):
        FramerRTU.crc16_table = FramerRTU.generate_crc16_table()
        hex_data = bytes.fromhex(command)#十六进制字符串转换为字节串
        crc_value = self.FramerRTU.compute_CRC(hex_data)#计算CRC
        bytes_data = crc_value.to_bytes(2, byteorder='big')#整数转字节串
        hex_string = hex_data + bytes_data
        self.ser.write(hex_string)

        # 打印发送的16进制数据
        hex_string_with_spaces = ' '.join([hex_string.hex().upper()[i:i+2] for i in range(0, len(hex_string.hex().upper()), 2)])
        self.logger.debug(f"发送数据: {hex_string_with_spaces}")

        # 读取和打印返回的数据
        response = self.ser.read(8)
        response_with_spaces = ' '.join([response.hex().upper()[i:i+2] for i in range(0, len(response.hex().upper()), 2)])
        self.logger.debug(f"返回数据: {response_with_spaces}")
        time.sleep(0.01)  # 延时 0.01 秒

    def open(self):
        self.set_vel(1)
        time.sleep(2.5)
        self.logger.info("Open shears")
    
    def close(self):
        self.set_vel(-1)
        time.sleep(2.5)
        self.logger.info("Close shears")
    
    def __del__(self):
        self.ser.close()  # 确保被销毁时关闭串口


if __name__ == "__main__":
    scissors = Shears("/dev/ttyACM0")
    scissors.open()
    time.sleep(5)
    scissors.close()
    # scissors.open()
    # scissors.first_set()