#include <nlohmann/json.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <papjia_vision_interface/msg/objects2d.hpp>
#include "papjia_vision_behaviors/mask_detect_service_client.hpp"

using json = nlohmann::json;

namespace papjia
{
    namespace behaviors
    {
        DetectMasksServiceClient::DetectMasksServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                                           const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<DetectMasks>(name, config, shared_resources)
        {
        }

        BT::PortsList DetectMasksServiceClient::providedPorts()
        {
            return BT::PortsList({
                BT::InputPort<std::string>("service_name"),
                BT::InputPort<sensor_msgs::msg::Image>("image"),
                BT::InputPort<std::uint64_t>("max_num"),
                BT::InputPort<double>("min_score"),
                BT::InputPort<std::string>("allowed_roi"),
                BT::InputPort<std::string>("allowed_categories"),
                BT::OutputPort<std::uint64_t>("objs_num"),
                BT::OutputPort<bool>("with_mask"),
                BT::OutputPort<sensor_msgs::msg::Image>("mask"),
                BT::OutputPort<papjia_vision_interface::msg::Objects2d>("objects"),
            });
        }

        tl::expected<std::string, std::string> DetectMasksServiceClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<DetectMasks::Request, std::string> DetectMasksServiceClient::createRequest()
        {
            const auto maybe_image = getInput<sensor_msgs::msg::Image>("image");
            sensor_msgs::msg::Image image;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_image))
            {
                return tl::make_unexpected("No image input port [image] provided");
            }
            else
            {
                image = maybe_image.value();
            }

            const auto maybe_max_num = getInput<std::uint64_t>("max_num");
            std::uint64_t max_num;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_max_num))
            {
                max_num = 20;
            }
            else
            {
                max_num = maybe_max_num.value();
            }

            const auto maybe_min_score = getInput<double>("min_score");
            double min_score;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_min_score))
            {
                min_score = 0.98;
            }
            else
            {
                min_score = maybe_min_score.value();
            }

            std::vector<std::string> allowed_categories;
            auto maybe_allowed_categories = getInput<std::string>("allowed_categories");
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_allowed_categories))
            {
                RCLCPP_INFO(rclcpp::get_logger("DetectMasksServiceClient"), "[allowed_categories] input port not provided, disable categories filtering");
            }
            else
            {
                // Parse the JSON string
                json parsed_array = json::parse(maybe_allowed_categories.value());
                allowed_categories = parsed_array.get<std::vector<std::string>>();
            }

            std::vector<uint64_t> allowed_roi;
            auto maybe_allowed_roi = getInput<std::string>("allowed_roi");
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_allowed_roi))
            {
                RCLCPP_INFO(rclcpp::get_logger("DetectMasksServiceClient"), "[allowed_roi] input port not provided, disable ROI filtering");
            }
            else
            {
                // Parse the JSON string
                json parsed_array = json::parse(maybe_allowed_roi.value());
                allowed_roi = parsed_array.get<std::vector<uint64_t>>();
            }

            return papjia_vision_interface::build<DetectMasks::Request>().image(image).max_num(max_num).min_score(min_score).allowed_roi(allowed_roi).allowed_categories(allowed_categories);
        }

        tl::expected<bool, std::string> DetectMasksServiceClient::processResponse(const DetectMasks::Response &response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("object detect service call failed");
            }

            setOutput<std::uint64_t>("objs_num", response.objs_num);
            setOutput<bool>("with_mask", response.with_mask);
            setOutput<sensor_msgs::msg::Image>("mask", response.mask);
            setOutput<papjia_vision_interface::msg::Objects2d>("objects", response.objects);            
            
            RCLCPP_INFO(rclcpp::get_logger("DetectMasksServiceClient"), "object detect found %ld objects", response.objs_num);

            return true;
        }
    }
}