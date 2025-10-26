/*
 * @Descripttion: 多线程执行器
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-02 10:48:13
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 11:00:16
 */
#include <rclcpp/rclcpp.hpp>
#include <papjia_pose/obj_pose.hpp>

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    // Create MultiThreadedExecutor
    auto executor = std::make_shared<rclcpp::executors::MultiThreadedExecutor>(rclcpp::ExecutorOptions(), 5); // 多线程
    rclcpp::NodeOptions options;

    // Create a node
    auto node = std::make_shared<ObjPoseService>(options);

    // Add your callback to the executor
    executor->add_node(node);

    // RCLCPP_INFO(node->get_logger(), "%ld", executor->get_number_of_threads());

    executor->spin();

    rclcpp::shutdown();
    return 0;
}