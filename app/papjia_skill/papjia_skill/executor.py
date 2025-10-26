import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from papjia_behavior_interface.action import ExecuteTree


class PapjiaSkillExecutor(Node):
    def __init__(self, node_name="papjia_skill_executor"):
        super().__init__(node_name)
        self.action_client = ActionClient(self, ExecuteTree, "execute_tree")
        self.get_logger().info("PapjiaSkillExecutor 初始化完成.")

    def execute_tree(self, tree_string, tree_name, keys=[]):
        """执行行为树."""
        if not self.action_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error("Action server 未启动.")
            return

        goal_msg = ExecuteTree.Goal()
        goal_msg.tree_string = tree_string
        goal_msg.tree_type = ExecuteTree.Goal.STRING  # 树类型为字符串
        goal_msg.tree_name = tree_name
        goal_msg.keys = keys

        self.get_logger().info(f"发送行为树任务: {tree_name}")
        future = self.action_client.send_goal_async(goal_msg, self.feedback_callback)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("任务被拒绝.")
            return

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result
        self.get_logger().info(f"任务完成. 成功: {result.success}")
        return result

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        # self.get_logger().info(f"反馈 - 当前状态: {feedback.current_status}")


class PapjiaSkillAsyncExecutor(Node):
    def __init__(self, node_name="papjia_skill_executor"):
        super().__init__(node_name)
        self.action_client = ActionClient(self, ExecuteTree, "execute_tree")
        self.get_logger().info("PapjiaSkillAsyncExecutor 初始化完成.")

    async def execute_tree(self, tree_string, tree_name, keys=[]):
        """执行行为树."""
        self.get_logger().info("等待行为树服务...")
        if not self.action_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error("Action server 未启动.")
            # 返回一个失败的结果对象
            result = ExecuteTree.Result()
            result.success = False
            result.result = "Action server 未启动"
            return result

        goal_msg = ExecuteTree.Goal()
        goal_msg.tree_string = tree_string
        goal_msg.tree_type = ExecuteTree.Goal.STRING  # 树类型为字符串
        goal_msg.tree_name = tree_name
        goal_msg.keys = keys

        self.get_logger().info(f"发送行为树任务: {tree_name}")
        goal_handle = await self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback,
        )
        if not goal_handle.accepted:
            self.get_logger().error("任务被拒绝.")
            # 返回一个失败的结果对象
            result = ExecuteTree.Result()
            result.success = False
            result.result = "任务被拒绝"
            return result

        self.get_logger().info("任务已接收，等待完成...")
        res = await goal_handle.get_result_async()
        result = res.result
        status = res.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"任务完成. 结果: {result}")
        else:
            self.get_logger().error(f"任务异常. 状态: {status}")
            # 确保返回的结果对象有success属性
            if not hasattr(result, 'success'):
                result.success = False
        return result

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f"反馈 - 当前状态: {feedback.current_status}")