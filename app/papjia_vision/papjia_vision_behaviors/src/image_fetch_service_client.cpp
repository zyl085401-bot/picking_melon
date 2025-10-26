#include <nlohmann/json.hpp>
#include <sensor_msgs/msg/image.hpp>
#include "papjia_vision_behaviors/image_fetch_service_client.hpp"

using json = nlohmann::json;

namespace papjia
{
    namespace behaviors
    {
        FetchImageServiceClient::FetchImageServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                                         const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<FetchImage>(name, config, shared_resources)
        {
        }

        BT::PortsList FetchImageServiceClient::providedPorts()
        {
            return BT::PortsList({
                BT::InputPort<std::string>("service_name"),
                BT::InputPort<std::string>("ip"),
                BT::InputPort<std::string>("device_name"),
                BT::OutputPort<bool>("success"),
                BT::OutputPort<sensor_msgs::msg::Image>("image"),
            });
        }

        tl::expected<std::string, std::string> FetchImageServiceClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<FetchImage::Request, std::string> FetchImageServiceClient::createRequest()
        {

            std::string ip;
            auto maybe_ip = getInput<std::string>("ip");
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_ip))
            {
                RCLCPP_INFO(rclcpp::get_logger("FetchImageServiceClient"), "[ip] input port not provided, disable categories filtering");
            }
            else
            {
                ip = maybe_ip.value();
            }

            std::string device_name;
            auto maybe_device_name = getInput<std::string>("device_name");
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_device_name))
            {
                RCLCPP_INFO(rclcpp::get_logger("FetchImageServiceClient"), "[device_name] input port not provided, disable categories filtering");
            }
            else
            {
                device_name = maybe_device_name.value();
            }

            return papjia_vision_interface::build<FetchImage::Request>().ip(ip).device_name(device_name);
        }

        tl::expected<bool, std::string> FetchImageServiceClient::processResponse(const FetchImage::Response &response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("object detect service call failed");
            }

            setOutput<bool>("success", response.success);
            setOutput<sensor_msgs::msg::Image>("image", response.image);

            return true;
        }
    }
}