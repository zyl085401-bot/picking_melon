import rclpy
from rclpy.node import Node
from papjia_move_msgs.srv import StraightMove  # 替换为实际的服务类型

class ServiceClient(Node):
    def __init__(self):
        super().__init__('move_service_client')
        self.client = self.create_client(StraightMove, '/papjia/move/line_tracing')  # 替换为实际服务名

        self.get_logger().info('正在连接服务...')
        
        # 等待服务可用
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('服务未就绪，等待中...')
        
        self.get_logger().info('服务已就绪')
        
    def send_request(self):
        # 创建请求对象
        request = StraightMove.Request()
        
        # 填充请求参数（根据实际需求修改数值）
        request.distance = 5.0          # float32
        request.use_integral = True     # bool
        request.follow_line = True     # bool
        request.line_frame = "map"      # string
        request.line_start = [0.0, 0.0, 1.57] # float64[2]
        # request.line_end = [0.0, 3.0, 1.57]   # float64[2]
        # request.speed = 0.2             # float32

        request.line_end = [0.0, -3.0, 1.57]   # float64[2]
        request.speed = -0.2             # float32
        
        # 发送异步请求
        future = self.client.call_async(request)
        future.add_done_callback(self.response_callback)
        
    def response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info(f"服务调用成功: {response.success}")
            else:
                self.get_logger().warn(f"服务执行失败")
        except Exception as e:
            self.get_logger().error(f"服务调用异常: {e}")

def main(args=None):
    rclpy.init(args=args)
    client_node = ServiceClient()
    client_node.send_request()
    
    try:
        rclpy.spin(client_node)
    except KeyboardInterrupt:
        client_node.get_logger().info("用户终止操作")
    finally:
        client_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()