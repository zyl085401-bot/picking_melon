/*
 * @Descripttion: 直线检测服务
 * @version: 2.0
 * @Author: 崔译文
 * @Date: 2023-12-21 15:40:10
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-02 10:46:16
 */
#ifndef __LINE_DETECTOR_HPP__
#define __LINE_DETECTOR_HPP__

#include <string>
#include <vector>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <papjia_vision_interface/srv/detect_line.hpp>
#include <papjia_line_detector/visibility_control.h>

/**
 * @brief: LineDetectorService类，提供直线检测服务
 * @return {*}
 */
class LineDetectorService : public rclcpp::Node
{
public:
    COMPOSITION_PUBLIC
    explicit LineDetectorService(const rclcpp::NodeOptions &options);

private:
    std::string service_seg_line_;                          // 直线分割服务的topic
    std::string topic_image_line_;                                // 检测结果的图像要发布到的topic
    std::string topic_image_;                                     // 原始图像的topic
    bool flag_pub_image_line_;                                    // 是否发布检测结果（图像形式）
    bool flag_use_rect_;                                          // 是否使用rect参数
    std::vector<int64_t> rect_;                                   // 区域选定参数
    std::vector<sensor_msgs::msg::Image::ConstSharedPtr> images_; // 摄像头的图像
    rclcpp::CallbackGroup::SharedPtr callback_group_organization_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_image_line_; // 检测结果（图像形式）的Publisher
    rclcpp::Service<papjia_vision_interface::srv::DetectLine>::SharedPtr server_seg_line_;   // 服务Server
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_;         // 订阅图像

    /**
     * @brief: 服务处理函数
     * @return {bool} 是否成功
     */
    bool detect_line_callback(const papjia_vision_interface::srv::DetectLine::Request::SharedPtr request,
                              const papjia_vision_interface::srv::DetectLine::Response::SharedPtr response);
    /**
     * @brief: 订阅图像
     * @param {ConstSharedPtr} &msg 图像的消息，指针类型
     * @return {void}
     */
    void image_callback(const sensor_msgs::msg::Image::ConstSharedPtr &msg);
};

#endif