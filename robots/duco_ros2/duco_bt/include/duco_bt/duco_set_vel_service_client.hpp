#ifndef DUCO_BT__DUCO_SET_VEL_SERVICE_CLIENT_HPP
#define DUCO_BT__DUCO_SET_VEL_SERVICE_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <duco_msgs/srv/set_vel.hpp>

using SetVel = duco_msgs::srv::SetVel;

namespace papjia::behaviors {
    class DucoSetVelServiceClient  final : public papjia::behavior_tree::ServiceClientBehaviorBase<SetVel>
    {
    public:
        DucoSetVelServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
        static BT::PortsList providedPorts();
    private:
        tl::expected<std::string, std::string> getServiceName() override;
        tl::expected<SetVel::Request, std::string> createRequest() override;
        tl::expected<bool, std::string> processResponse(const SetVel::Response &response) override;
    };
}

#endif
