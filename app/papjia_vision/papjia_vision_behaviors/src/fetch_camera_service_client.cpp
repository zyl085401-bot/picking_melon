#include <papjia_vision_behaviors/fetch_camera_service_client.hpp>

namespace papjia::behaviors {

    FetchCameraServiceClient::FetchCameraServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) : papjia::behavior_tree::ServiceClientBehaviorBase<FetchCamera>(name, config, shared_resources) {}

    BT::PortsList FetchCameraServiceClient::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("service_name"),
                          BT::InputPort<bool>("fetch_camera_info"),
                          BT::InputPort<bool>("fetch_color"),
                          BT::InputPort<bool>("fetch_depth"),
                          BT::InputPort<double>("wait_for_server_timeout"),
                          BT::InputPort<double>("result_timeout"),
                          BT::OutputPort<sensor_msgs::msg::Image>("color"),
                          BT::OutputPort<sensor_msgs::msg::Image>("depth"),
                          BT::OutputPort<sensor_msgs::msg::CameraInfo>("camera_info"),
                          BT::OutputPort<std::string>("message"),
                          BT::OutputPort<bool>("success")});
    }

    tl::expected<std::string, std::string> FetchCameraServiceClient::getServiceName()
    {
        const auto service_name = getInput<std::string>("service_name");
        if (const auto error = papjia::behavior_tree::maybe_error(service_name))
    {
            return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
    }
        return service_name.value();
    }

    tl::expected<FetchCamera::Request, std::string> FetchCameraServiceClient::createRequest()
    {
        const auto maybe_fetch_camera_info = getInput<bool>("fetch_camera_info");
        bool fetch_camera_info;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_fetch_camera_info))
        {
            return tl::make_unexpected("input port fetch_camera_info is not set");
        }
        else
        {
            fetch_camera_info = maybe_fetch_camera_info.value();
        }
        const auto maybe_fetch_color = getInput<bool>("fetch_color");
        bool fetch_color;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_fetch_color))
        {
            return tl::make_unexpected("input port fetch_color is not set");
        }
        else
        {
            fetch_color = maybe_fetch_color.value();
        }
        const auto maybe_fetch_depth = getInput<bool>("fetch_depth");
        bool fetch_depth;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_fetch_depth))
        {
            return tl::make_unexpected("input port fetch_depth is not set");
        }
        else
        {
            fetch_depth = maybe_fetch_depth.value();
        }
        return papjia_vision_interface::build<FetchCamera::Request>().fetch_camera_info(fetch_camera_info).fetch_color(fetch_color).fetch_depth(fetch_depth);
    }

    tl::expected<bool, std::string> FetchCameraServiceClient::processResponse(const FetchCamera::Response& response)
    {
        setOutput<sensor_msgs::msg::Image>("color", response.color);
        setOutput<sensor_msgs::msg::Image>("depth", response.depth);
        setOutput<sensor_msgs::msg::CameraInfo>("camera_info", response.camera_info);
        setOutput<std::string>("message", response.message);
        setOutput<bool>("success", response.success);
        return true;
    }

}
