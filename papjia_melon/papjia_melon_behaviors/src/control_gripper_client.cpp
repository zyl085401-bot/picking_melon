#include "papjia_melon_behaviors/control_gripper_client.hpp"

namespace papjia
{
    namespace behaviors
    {
        ControlGripperClient::ControlGripperClient(const std::string &name, const BT::NodeConfiguration &config,
                                                       const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<ControlGripper>(name, config, shared_resources)
        {
        }

        BT::PortsList ControlGripperClient::providedPorts()
        {
            return BT::PortsList({
                BT::InputPort<std::string>("service_name"),
                BT::InputPort<std::string>("cmd"),
            });
        }

        tl::expected<std::string, std::string> ControlGripperClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<ControlGripper::Request, std::string> ControlGripperClient::createRequest()
        {
            const auto cmd = getInput<std::string>("cmd");
            if (const auto error = papjia::behavior_tree::maybe_error(cmd))
            {
                return tl::make_unexpected("Failed to get [cmd] from input data port: " + error.value());
            }
            return papjia_melon_interface::build<ControlGripper::Request>().cmd(cmd.value());
        }

        tl::expected<bool, std::string> ControlGripperClient::processResponse(const ControlGripper::Response& response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("control gripper service call failed");
            }
            return true;
        }
    }
}