#ifndef PAPJIA_MELON_BEHAVIORS__CONTROL_GRIPPER_CLIENT_HPP
#define PAPJIA_MELON_BEHAVIORS__CONTROL_GRIPPER_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_melon_interface/srv/control_gripper.hpp>

using ControlGripper = papjia_melon_interface::srv::ControlGripper;

namespace papjia
{
    namespace behaviors
    {
        class ControlGripperClient final : public papjia::behavior_tree::ServiceClientBehaviorBase<ControlGripper>
        {
        public:
            ControlGripperClient(const std::string &name, const BT::NodeConfiguration &config,
                                   const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
            static BT::PortsList providedPorts();

        private:
            tl::expected<std::string, std::string> getServiceName() override;

            tl::expected<ControlGripper::Request, std::string> createRequest() override;

            tl::expected<bool, std::string> processResponse(const ControlGripper::Response &response) override;
        };
    }
}

#endif