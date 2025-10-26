/*
 * @Descripttion: 直线检测服务
 * @version: 2.0
 * @Author: 崔译文
 * @Date: 2023-12-21 15:40:10
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-10 10:19:18
 */
#include <opencv2/opencv.hpp>
#include <rclcpp/rclcpp.hpp>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/msg/image.hpp>
#include <papjia_vision_interface/srv/detect_line.hpp>
#include <papjia_line_detector/CommonAPI.hpp>
#include <papjia_line_detector/line_detector.hpp>

LineDetectorService::LineDetectorService(const rclcpp::NodeOptions &options) : Node("line_detector", options)
{
    RCLCPP_INFO(this->get_logger(), "Begin init node ...");
    this->declare_parameter<std::string>("service_seg_line", "");
    this->declare_parameter<std::string>("topic_image_line", "");
    this->declare_parameter<std::string>("topic_image", "");
    this->declare_parameter<std::vector<int64_t>>("rect", std::vector<int64_t>({0, 0, 0, 0}));
    this->declare_parameter<bool>("flag_pub_image_line", false);
    this->declare_parameter<bool>("flag_use_rect", false);

    this->get_parameter("service_seg_line", service_seg_line_);
    this->get_parameter("topic_image_line", topic_image_line_);
    this->get_parameter("topic_image", topic_image_);
    this->get_parameter("flag_pub_image_line", flag_pub_image_line_);
    this->get_parameter("flag_use_rect", flag_use_rect_);

    RCLCPP_INFO(this->get_logger(), "Get param service_seg_line %s", service_seg_line_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param topic_image_line %s", topic_image_line_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param topic_image %s", topic_image_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param flag_pub_image_line %d", flag_pub_image_line_);
    RCLCPP_INFO(this->get_logger(), "Get param flag_use_rect %d", flag_use_rect_);
    if (flag_use_rect_)
    {
        this->get_parameter("rect", rect_);
        RCLCPP_INFO(this->get_logger(), "Get param rect [%ld %ld %ld %ld]", rect_[0], rect_[1], rect_[2], rect_[3]);
    }

    callback_group_organization_ = this->create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
    server_seg_line_ = this->create_service<papjia_vision_interface::srv::DetectLine>(service_seg_line_,
                                                                          std::bind(&LineDetectorService::detect_line_callback, this, std::placeholders::_1, std::placeholders::_2),
                                                                          rmw_qos_profile_services_default,
                                                                          callback_group_organization_);
    RCLCPP_INFO(this->get_logger(), "Loaded service server %s", service_seg_line_.c_str());
    sub_image_ = this->create_subscription<sensor_msgs::msg::Image>(topic_image_, 5, std::bind(&LineDetectorService::image_callback, this, std::placeholders::_1));
    pub_image_line_ = this->create_publisher<sensor_msgs::msg::Image>(topic_image_line_, 5);
    RCLCPP_INFO(this->get_logger(), "Loaded publisher for topic %s", topic_image_line_.c_str());
    RCLCPP_INFO(this->get_logger(), "Finished init node");
}

void LineDetectorService::image_callback(const sensor_msgs::msg::Image::ConstSharedPtr &msg)
{
    images_.clear();
    images_.push_back(msg);
    RCLCPP_DEBUG(this->get_logger(), "Rev rgb image with time %d.{%03d}", msg->header.stamp.sec, int32_t(msg->header.stamp.nanosec / 1000000));
}

bool LineDetectorService::detect_line_callback(const papjia_vision_interface::srv::DetectLine::Request::SharedPtr request,
                                               const papjia_vision_interface::srv::DetectLine::Response::SharedPtr response)
{
    // 获取图像
    sensor_msgs::msg::Image::ConstSharedPtr image;
    if (request->flag_has_image)
    {
        image = std::make_shared<sensor_msgs::msg::Image>(request->image);
    }
    else if (images_.size() > 0)
    {
        image = images_.back();
        images_.clear();
    }
    else
    {
        return false;
    }
    RCLCPP_DEBUG(this->get_logger(), "Get cv image");
    // 转化图像
    cv_bridge::CvImagePtr cv_ptr;
    cv_ptr = cv_bridge::toCvCopy(image, "8UC3");
    cv::Mat img;
    cv_ptr->image.copyTo(img);
    // 获取感兴趣区域
    cv::Mat edge, rectImg;
    cv::Point2d tl;
    cv::Rect2d rect;
    if (flag_use_rect_)
    {
        tl.x = rect_[0];
        tl.y = rect_[1];
        rect.x = rect_[0];
        rect.y = rect_[1];
        rect.width = rect_[2];
        rect.height = rect_[3];
        rectImg = img(rect);
    }
    else
    {
        rectImg = img;
    }
    RCLCPP_DEBUG(this->get_logger(), "Get rect image");
    // 边缘检测
    COMMONAPI::EdgeDetect(rectImg, edge, 100, 200);
    // 直线检测
    std::vector<cv::Vec4i> lines, lines2;                   // 存储直线数据
    HoughLinesP(edge, lines, 1, CV_PI / 180.0, 60, 30, 10); // 源图需要是二值图像，HoughLines也是一样
    COMMONAPI::mergeLines(lines, lines2);                   // 合并直线
    RCLCPP_DEBUG(this->get_logger(), "Get lines");
    // 构造结果
    for (size_t i = 0; i < lines2.size(); ++i)
    {
        cv::Vec4i l = lines2[i];
        response->lines.push_back(l[0] + tl.x);
        response->lines.push_back(l[1] + tl.y);
        response->lines.push_back(l[2] + tl.x);
        response->lines.push_back(l[3] + tl.y);
    }
    response->size = lines2.size();
    response->success = true;
    RCLCPP_INFO(this->get_logger(), "Constructed line result");
    this->get_parameter("flag_pub_image_line", flag_pub_image_line_);
    if (flag_pub_image_line_)
    {
        cv::Mat gray, rgb;
        cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
        cv::cvtColor(gray, rgb, cv::COLOR_GRAY2BGR);
        if (flag_use_rect_)
        {
            rectangle(rgb, rect, cv::Scalar(186, 88, 255));
        }
        for (size_t i = 0; i < response->lines.size(); i += 4)
        {
            cv::Point p1(response->lines[i], response->lines[i + 1]);
            cv::Point p2(response->lines[i + 2], response->lines[i + 3]);
            line(rgb, p1, p2, cv::Scalar(186, 88, 255), 1, cv::LINE_AA);
        }
        sensor_msgs::msg::Image::SharedPtr msg_ptr = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", rgb).toImageMsg();
        pub_image_line_->publish(*msg_ptr);
        RCLCPP_INFO(this->get_logger(), "Published line result within image");
    }
    return true;
}

#include "rclcpp_components/register_node_macro.hpp"

// Register the component with class_loader.
// This acts as a sort of entry point, allowing the component to be discoverable when its library
// is being loaded into a running process.
RCLCPP_COMPONENTS_REGISTER_NODE(LineDetectorService)
