#include "papjia_vision_behaviors/tags_detect_service_client.hpp"
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/camera_info.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>

namespace papjia
{
    namespace behaviors
    {
        DetectTagsServiceClient::DetectTagsServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                                         const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<DetectTags>(name, config, shared_resources)
        {
        }

        BT::PortsList DetectTagsServiceClient::providedPorts()
        {
            return BT::PortsList({BT::InputPort<std::string>("service_name"),
                                  BT::InputPort<sensor_msgs::msg::CameraInfo>("camera_info"),
                                  BT::InputPort<sensor_msgs::msg::Image>("image"),
                                  BT::OutputPort<geometry_msgs::msg::PoseStamped>("pose"),
                                  BT::OutputPort<bool>("success")});
        }

        tl::expected<std::string, std::string> DetectTagsServiceClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<DetectTags::Request, std::string> DetectTagsServiceClient::createRequest()
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

            const auto maybe_camera_info = getInput<sensor_msgs::msg::CameraInfo>("camera_info");
            sensor_msgs::msg::CameraInfo camera_info;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_camera_info))
            {
                return tl::make_unexpected("No image input port [image] provided");
            }
            else
            {
                camera_info = maybe_camera_info.value();
            }

            return papjia_vision_interface::build<DetectTags::Request>().camera_info(camera_info).image(image);
        }

        tl::expected<bool, std::string> DetectTagsServiceClient::processResponse(const DetectTags::Response &response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("tags detect service call failed");
            }
            setOutput<geometry_msgs::msg::PoseStamped>("pose", response.pose);
            setOutput<bool>("success", response.success);

            return true;
        }
    }
}