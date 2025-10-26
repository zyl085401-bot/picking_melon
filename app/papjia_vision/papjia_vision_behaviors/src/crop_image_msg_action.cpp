#include <map>
#include "papjia_vision_behaviors/crop_image_msg_action.hpp"

static const rclcpp::Logger LOGGER = rclcpp::get_logger("behaviros_crop_image_msg");

namespace papjia::behaviors
{

    CropImageMsgAction::CropImageMsgAction(const std::string &name, const BT::NodeConfig &config,
                                           const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
        : papjia::behavior_tree::AsyncBehaviorBase(name, config, shared_resources)
    {
        RCLCPP_INFO_STREAM(LOGGER, "Init");
    }

    BT::PortsList CropImageMsgAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<sensor_msgs::msg::Image>("image_input"),
                              BT::InputPort<int>("x1"),
                              BT::InputPort<int>("y1"),
                              BT::InputPort<int>("x2"),
                              BT::InputPort<int>("y2"),
                              BT::OutputPort<sensor_msgs::msg::Image>("image_output")});
    }

    tl::expected<bool, std::string> CropImageMsgAction::doWork()
    {
        sensor_msgs::msg::Image image_input;
        auto maybe_image_input = getInput<sensor_msgs::msg::Image>("image_input");
        if (!maybe_image_input)
        {
            RCLCPP_INFO_STREAM(LOGGER, "No input port [image_input] found.");
            return tl::make_unexpected(maybe_image_input.error());
        }
        else
        {
            image_input = maybe_image_input.value();
        }

        int x1, y1, x2, y2;
        auto maybe_x1 = getInput<int>("x1");
        if (!maybe_x1)
        {
            RCLCPP_INFO_STREAM(LOGGER, "No input port [x1] found.");
            return tl::make_unexpected(maybe_x1.error());
        }
        else
        {
            x1 = maybe_x1.value();
        }

        auto maybe_y1 = getInput<int>("y1");
        if (!maybe_y1)
        {
            RCLCPP_INFO_STREAM(LOGGER, "No input port [y1] found.");
            return tl::make_unexpected(maybe_y1.error());
        }
        else
        {
            y1 = maybe_y1.value();
        }

        auto maybe_x2 = getInput<int>("x2");
        if (!maybe_x2)
        {
            RCLCPP_INFO_STREAM(LOGGER, "No input port [x2] found.");
            return tl::make_unexpected(maybe_x2.error());
        }
        else
        {
            x2 = maybe_x2.value();
        }

        auto maybe_y2 = getInput<int>("y2");
        if (!maybe_y2)
        {
            RCLCPP_INFO_STREAM(LOGGER, "No input port [y2] found.");
            return tl::make_unexpected(maybe_y2.error());
        }
        else
        {
            y2 = maybe_y2.value();
        }

        // 转化图像
        cv_bridge::CvImagePtr cv_ptr;
        cv::Mat cv_mat;
        std::map<std::string, std::string> image_encoding_map = {
            {"mono8", "8UC1"},   // Grayscale image
            {"mono16", "16UC1"}, // 16-bit grayscale image
            {"bgr8", "8UC3"},    // Color image with blue-green-red order
            {"rgb8", "8UC3"},    // Color image with red-green-blue order
            {"bgra8", "8UC4"},   // BGR color image with an alpha channel
            {"rgba8", "8UC4"}    // RGB color image with an alpha channel
        };
        cv_ptr = cv_bridge::toCvCopy(image_input, image_encoding_map[image_input.encoding]);
        cv_ptr->image.copyTo(cv_mat);

        // 裁剪图像
        cv::Rect2i rect(x1, y1, x2 - x1, y2 - y1);
        cv::Mat cropped_image = cv_mat(rect);

        auto image_output = cv_bridge::CvImage(image_input.header, image_input.encoding, cropped_image).toImageMsg();

        setOutput<sensor_msgs::msg::Image>("image_output", *image_output);

        return true;
    }

}