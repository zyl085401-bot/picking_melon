import rclpy
from rclpy.node import Node
from papjia_behavior_interface.srv import ExecuteTree
import sys


class ExecuteTreeClient(Node):
    def __init__(self):
        super().__init__('execute_tree_client')

    def send_request(self, task_file, tree_name):
        client = self.create_client(ExecuteTree, '/papjia/bt/execute')

        # 等待服务可用
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待服务可用中...')

        # 创建服务请求
        request = ExecuteTree.Request()
        request.task_file = task_file
        request.tree_name = tree_name

        # 异步调用服务
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        # 检查服务响应
        if future.result() is not None:
            return future.result().success
        else:
            self.get_logger().error('服务调用失败')
            return None


def main():
    rclpy.init()

    # 检查传入的参数
    if len(sys.argv) != 3:
        print("Usage: ros2 run <package_name> <executable_name> <task_file> <tree_name>")
        return

    task_file = sys.argv[1]
    tree_name = sys.argv[2]

    # 创建客户端节点
    node = ExecuteTreeClient()
    success = node.send_request(task_file, tree_name)

    if success is not None:
        if success:
            node.get_logger().info(f"成功执行行为树: {tree_name}，来自文件: {task_file}")
        else:
            node.get_logger().info(f"执行行为树失败: {tree_name}，来自文件: {task_file}")

    # 销毁节点并关闭 ROS
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
