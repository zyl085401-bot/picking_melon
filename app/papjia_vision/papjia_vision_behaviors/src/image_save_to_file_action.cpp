#include "papjia_vision_behaviors/image_save_to_file_action.hpp"

static const rclcpp::Logger LOGGER = rclcpp::get_logger("behaviros_image_save_to_file");

namespace papjia::behaviors
{

    ImageSaveToFileAction::ImageSaveToFileAction(const std::string &name, const BT::NodeConfig &config,
                                                 const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
        : papjia::behavior_tree::AsyncBehaviorBase(name, config, shared_resources)
    {
        RCLCPP_INFO_STREAM(LOGGER, "Init");
    }

    BT::PortsList ImageSaveToFileAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<sensor_msgs::msg::Image>("image"),
                              BT::InputPort<std::string>("file_name")});
    }

    tl::expected<bool, std::string> ImageSaveToFileAction::doWork()
    {
        auto image_result = getInput<sensor_msgs::msg::Image>("image");
        if (!image_result)
        {
            return tl::make_unexpected(image_result.error());
        }

        auto file_name = getInput<std::string>("file_name");
        if (!file_name)
        {
            return tl::make_unexpected(file_name.error());
        }

        auto save_result = saveImage(image_result.value(), file_name.value());
        if (!save_result)
        {
            return tl::make_unexpected(save_result.error());
        }

        return true;
    }

    tl::expected<bool, std::string> ImageSaveToFileAction::saveImage(const sensor_msgs::msg::Image &image, const std::string &file_path)
    {
        try
        {
            cv::Mat cv_image = cv_bridge::toCvCopy(image, image.encoding)->image;
            if (cv::imwrite(file_path, cv_image))
            {
                RCLCPP_INFO(LOGGER, "Image saved to %s", file_path.c_str());
            }
            else
            {
                return tl::make_unexpected("Failed to save image to file.");
            }
        }
        catch (cv_bridge::Exception &e)
        {
            return tl::make_unexpected(std::string("cv_bridge exception: ") + e.what());
        }
        return true;
    }

}