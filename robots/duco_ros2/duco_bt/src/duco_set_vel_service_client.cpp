#include <duco_bt/duco_set_vel_service_client.hpp>

namespace papjia::behaviors {

    DucoSetVelServiceClient::DucoSetVelServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) : papjia::behavior_tree::ServiceClientBehaviorBase<SetVel>(name, config, shared_resources) {}

    BT::PortsList DucoSetVelServiceClient::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("service_name"),
                          BT::InputPort<double>("vel"),
                          BT::InputPort<double>("wait_for_server_timeout"),
                          BT::InputPort<double>("result_timeout"),
                          BT::OutputPort<bool>("success")});
    }

    tl::expected<std::string, std::string> DucoSetVelServiceClient::getServiceName()
    {
        const auto service_name = getInput<std::string>("service_name");
        if (const auto error = papjia::behavior_tree::maybe_error(service_name))
    {
            return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
    }
        return service_name.value();
    }

    tl::expected<SetVel::Request, std::string> DucoSetVelServiceClient::createRequest()
    {
        const auto maybe_vel = getInput<double>("vel");
        double vel;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_vel))
        {
            return tl::make_unexpected("input port vel is not set");
        }
        else
        {
            vel = maybe_vel.value();
        }
        return duco_msgs::build<SetVel::Request>().vel(vel);
    }

    tl::expected<bool, std::string> DucoSetVelServiceClient::processResponse(const SetVel::Response& response)
    {
        setOutput<bool>("success", response.success);
        return true;
    }

}
