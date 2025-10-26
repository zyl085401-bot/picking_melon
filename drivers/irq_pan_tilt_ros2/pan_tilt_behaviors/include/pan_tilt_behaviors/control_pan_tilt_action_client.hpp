#ifndef PAN_TILT_BEHAVIORS__CONTROL_PAN_TILT_ACTION_CLIENT_HPP
#define PAN_TILT_BEHAVIORS__CONTROL_PAN_TILT_ACTION_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <papjia_behavior_tree/action_client_behavior_base.hpp>
#include <pan_tilt_msgs/action/control_pan_tilt.hpp>

using ControlPanTilt = pan_tilt_msgs::action::ControlPanTilt;

namespace papjia::behaviors {
    class ControlPanTiltActionClient  final : public papjia::behavior_tree::ActionClientBehaviorBase<ControlPanTilt>
    {
    public:
        ControlPanTiltActionClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
        static BT::PortsList providedPorts();
    private:
        tl::expected<ControlPanTilt::Goal, std::string> createGoal();
        tl::expected<bool, std::string> processResult(const std::shared_ptr<ControlPanTilt::Result> result);
    };
}

#endif
