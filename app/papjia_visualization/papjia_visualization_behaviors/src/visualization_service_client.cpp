#include <papjia_visualization_behaviors/visualization_service_client.hpp>

namespace papjia::behaviors {

    VisualizationServiceClient::VisualizationServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) : papjia::behavior_tree::ServiceClientBehaviorBase<Visualization>(name, config, shared_resources) {}

    BT::PortsList VisualizationServiceClient::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("service_name"),
                          BT::InputPort<std::string>("data"),
                          BT::InputPort<double>("wait_for_server_timeout"),
                          BT::InputPort<double>("result_timeout"),
                          BT::OutputPort<bool>("success"),
                          BT::OutputPort<std::string>("message")});
    }

    tl::expected<std::string, std::string> VisualizationServiceClient::getServiceName()
    {
        const auto service_name = getInput<std::string>("service_name");
        if (const auto error = papjia::behavior_tree::maybe_error(service_name))
    {
            return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
    }
        return service_name.value();
    }

    tl::expected<Visualization::Request, std::string> VisualizationServiceClient::createRequest()
    {
        const auto maybe_data = getInput<std::string>("data");
        std::string data;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_data))
        {
            return tl::make_unexpected("input port data is not set");
        }
        else
        {
            data = maybe_data.value();
        }
        return papjia_visualization_interface::build<Visualization::Request>().data(data);
    }

    tl::expected<bool, std::string> VisualizationServiceClient::processResponse(const Visualization::Response& response)
    {
        setOutput<bool>("success", response.success);
        setOutput<std::string>("message", response.message);
        return true;
    }

}
