#include "papjia_melon_behaviors/control_shears_client.hpp"

namespace papjia
{
    namespace behaviors
    {
        ControlShearsClient::ControlShearsClient(const std::string &name, const BT::NodeConfiguration &config,
                                                       const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<ControlShears>(name, config, shared_resources)
        {
        }

        BT::PortsList ControlShearsClient::providedPorts()
        {
            return BT::PortsList({
                BT::InputPort<std::string>("service_name"),
                BT::InputPort<std::string>("cmd"),
            });
        }

        tl::expected<std::string, std::string> ControlShearsClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<ControlShears::Request, std::string> ControlShearsClient::createRequest()
        {
            const auto cmd = getInput<std::string>("cmd");
            if (const auto error = papjia::behavior_tree::maybe_error(cmd))
            {
                return tl::make_unexpected("Failed to get [cmd] from input data port: " + error.value());
            }
            return papjia_melon_interface::build<ControlShears::Request>().cmd(cmd.value());
        }

        tl::expected<bool, std::string> ControlShearsClient::processResponse(const ControlShears::Response& response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("control shears service call failed");
            }
            return true;
        }
    }
}