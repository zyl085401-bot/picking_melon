import os
import stat
import subprocess
import time
import shutil
import rclpy
from rclpy.node import Node


class VirtualSerialPortNode(Node):
    def __init__(self):
        super().__init__("virtual_serial_port_node")

        # 声明参数
        self.declare_parameter("read_alias", "/dev/ttyUSB_READ")  # 默认映射的读端设备名称
        self.declare_parameter("write_alias", "/dev/ttyUSB_WRITE")  # 默认映射的写端设备名称
        self.declare_parameter("socat_path", "socat")  # 默认 socat 命令路径

        # 获取参数
        self.read_alias = self.get_parameter("read_alias").get_parameter_value().string_value
        self.write_alias = self.get_parameter("write_alias").get_parameter_value().string_value
        self.socat_path = self.get_parameter("socat_path").get_parameter_value().string_value

        self.socat_process = None
        self.cleanup()

        # 检查 socat 是否安装
        if not shutil.which(self.socat_path):
            self.get_logger().error("socat 未安装，请使用 'sudo apt install socat' 进行安装。")
            return

        self.create_virtual_serial_ports()

    def create_virtual_serial_ports(self):
        try:
            self.get_logger().info("启动 socat 创建虚拟串口对...")

            # 启动 socat 命令
            self.socat_process = subprocess.Popen(
                [self.socat_path, "-d", "-d", "pty,b115200", "pty,b115200"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Python 3.7+ 使用 text=True 而非 universal_newlines=True
            )

            time.sleep(1)  # 等待 socat 启动并输出设备信息

            # 实时读取 stderr 输出，提取虚拟串口设备
            dev1, dev2 = None, None
            while True:
                line = self.socat_process.stderr.readline()
                if not line:
                    break
                self.get_logger().debug(line.strip())
                if "PTY is" in line:
                    if dev1 is None:
                        dev1 = line.split()[-1]
                    elif dev2 is None:
                        dev2 = line.split()[-1]
                        break

            if not dev1 or not dev2:
                self.socat_process.terminate()
                raise RuntimeError("无法创建虚拟串口设备，请检查 socat 是否工作正常。")

            self.get_logger().info(f"创建了虚拟串口对: {dev1} 和 {dev2}")

            # 分别将虚拟串口端点映射为读端和写端
            self._create_symlink(dev1, self.read_alias)
            self._create_symlink(dev2, self.write_alias)

            self.get_logger().info(f"读端映射到 {self.read_alias} ({dev1})")
            self.get_logger().info(f"写端映射到 {self.write_alias} ({dev2})")
            self.get_logger().info("按 Ctrl+C 停止节点并关闭 socat。")

        except Exception as e:
            self.get_logger().error(f"创建虚拟串口对时发生错误: {e}")
            self.cleanup()

    def _create_symlink(self, source, alias):
        """创建符号链接，确保无冲突"""
        if os.path.exists(alias):
            self.get_logger().warning(f"{alias} 已存在，将会被覆盖。")
            os.remove(alias)
        os.symlink(source, alias)

    def cleanup(self):
        """清理资源，终止 socat 进程并删除符号链接。"""
        for alias in [self.read_alias, self.write_alias]:
            if os.path.lexists(alias):
                self.get_logger().warn(f"移除 {alias}")
                os.remove(alias)
        if self.socat_process:
            self.socat_process.terminate()
        self.get_logger().info("资源清理完成。")

    def destroy_node(self):
        """销毁节点时清理资源。"""
        self.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = VirtualSerialPortNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if "node" in locals():
            node.destroy_node()
        rclpy.shutdown()
