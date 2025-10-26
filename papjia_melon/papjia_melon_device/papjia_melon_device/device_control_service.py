import rclpy
from rclpy.node import Node

from papjia_melon_device.gripper_control import Gripper
from papjia_melon_device.shears_control import Shears

from papjia_melon_interface.srv import ControlGripper, ControlShears



class PapjiaMelonDevice(Node):

    def __init__(self):
        super().__init__('papjia_melon_device')
        
        # 参数设置
        self.declare_parameter("service_gripper_control", "/papjia/melon/device/gripper/control")
        self.declare_parameter("service_shears_control", "/papjia/melon/device/shears/control")
        self.declare_parameter("serial_gripper", "/dev/ACM1")
        self.declare_parameter("serial_shears", "/dev/ACM0")
        
        service_gripper_control = self.get_parameter("service_gripper_control").get_parameter_value().string_value
        service_shears_control = self.get_parameter("service_shears_control").get_parameter_value().string_value
        serial_gripper = self.get_parameter("serial_gripper").get_parameter_value().string_value
        serial_shears = self.get_parameter("serial_shears").get_parameter_value().string_value
        
        # 初始化设备
        self.gripper = Gripper(serial_gripper)
        self.shears = Shears(serial_shears)
        
        # 设置service
        self.gripper_control_service = self.create_service(ControlGripper, service_gripper_control, self.gripper_control_callback)
        self.shears_control_service = self.create_service(ControlShears, service_shears_control, self.shears_control_callback)
        self.get_logger().info("papjia_melon_device initialized")

    def gripper_control_callback(self, request: ControlGripper.Request, response: ControlGripper.Response):
        self.get_logger().info(f"receive new gripper control cmd: {request.cmd}")
        if request.cmd == "open":
            self.gripper.open()
        elif request.cmd == "close":
            self.gripper.close()
        else:
            self.get_logger().warn("cmd is invalid")
            response.success = False
            return response

        response.success = True
        return response
    
    def shears_control_callback(self, request: ControlShears.Request, response: ControlShears.Response):
        self.get_logger().info(f"receive new shears control cmd: {request.cmd}")
        if request.cmd == "open":
            self.shears.open()
        elif request.cmd == "close":
            self.shears.close()
        else:
            self.get_logger().warn("cmd is invalid")
            response.success = False
            return response

        response.success = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PapjiaMelonDevice()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
