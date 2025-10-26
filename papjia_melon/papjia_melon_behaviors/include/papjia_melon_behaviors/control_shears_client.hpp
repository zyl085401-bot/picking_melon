#ifndef PAPJIA_MELON_BEHAVIORS__CONTROL_SHEARS_CLIENT_HPP
#define PAPJIA_MELON_BEHAVIORS__CONTROL_SHEARS_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_melon_interface/srv/control_shears.hpp>

using ControlShears = papjia_melon_interface::srv::ControlShears;

namespace papjia
{
    namespace behaviors
    {
        class ControlShearsClient final : public papjia::behavior_tree::ServiceClientBehaviorBase<ControlShears>
        {
        public:
            ControlShearsClient(const std::string &name, const BT::NodeConfiguration &config,
                                   const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
            static BT::PortsList providedPorts();

        private:
            tl::expected<std::string, std::string> getServiceName() override;

            tl::expected<ControlShears::Request, std::string> createRequest() override;

            tl::expected<bool, std::string> processResponse(const ControlShears::Response &response) override;
        };
    }
}

#endif