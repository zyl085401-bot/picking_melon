/*
 * @Descripttion: 直线检测服务测试
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2023-12-25 15:36:21
 * @LastEditors: 崔译文
 * @LastEditTime: 2023-12-28 17:50:13
 */
#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <string>
#include <papjia_vision_interface/srv/detect_line.hpp>
#include <rclcpp/rclcpp.hpp>
#include <cv_bridge/cv_bridge.h>
#include <std_msgs/msg/header.hpp>

using namespace std::chrono_literals;

void load_image_from_file(std::string path, cv::Mat &img)
{
    img = cv::imread(path);
}

TEST(papjia_line_detector, line_seg_service)
{
    rclcpp::init(0, NULL);

    std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("line_seg_client");
    rclcpp::Client<papjia_vision_interface::srv::DetectLine>::SharedPtr client =
        node->create_client<papjia_vision_interface::srv::DetectLine>("/papjia_detector/line_seg_service");

    while (!client->wait_for_service(1s))
    {
        if (!rclcpp::ok())
        {
            RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
            ASSERT_TRUE(false);
        }
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "service not available, waiting again...");
    }

    cv::Mat img;
    load_image_from_file("/home/yw/ros2_ws/src/papjia_pickplace2/papjia_line_detector/resource/example.jpg", img);
    sensor_msgs::msg::Image::SharedPtr msg_ptr = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", img).toImageMsg();
    auto request = std::make_shared<papjia_vision_interface::srv::DetectLine::Request>();
    request->image = *msg_ptr;
    request->flag_has_image = true;

    while (!client->wait_for_service(1s))
    {
        if (!rclcpp::ok())
        {
            RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
            ASSERT_TRUE(false);
        }
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "service not available, waiting again...");
    }

    auto result = client->async_send_request(request);
    // Wait for the result.
    if (rclcpp::spin_until_future_complete(node, result) == rclcpp::FutureReturnCode::SUCCESS)
    {
        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Success");
    }
    else
    {
        RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Failed to call service add_two_ints");
        ASSERT_TRUE(false);
    }

    rclcpp::shutdown();
    ASSERT_TRUE(true);
}

int main(int argc, char **argv)
{
    testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}