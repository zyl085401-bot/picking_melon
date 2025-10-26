#include <pan_tilt_behaviors/control_pan_tilt_action_client.hpp>

namespace papjia::behaviors {

    ControlPanTiltActionClient::ControlPanTiltActionClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) : papjia::behavior_tree::ActionClientBehaviorBase<ControlPanTilt>(name, config, shared_resources) {}

    BT::PortsList ControlPanTiltActionClient::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("action_name"),
                          BT::InputPort<float>("yaw"),
                          BT::InputPort<float>("pitch"),
                          BT::InputPort<float>("duration"),
                          BT::InputPort<uint16_t>("speed"),
                          BT::InputPort<float>("timeout"),
                          BT::InputPort<double>("goal_result_timeout"),
                          BT::InputPort<double>("wait_for_server_timeout"),
                          BT::InputPort<double>("goal_response_timeout"),
                          BT::InputPort<double>("cancel_response_timeout"),
                          BT::OutputPort<bool>("success"),
                          BT::OutputPort<std::string>("message"),
                          BT::OutputPort<float>("result_yaw"),
                          BT::OutputPort<float>("result_pitch")});
    }

    tl::expected<ControlPanTilt::Goal, std::string> ControlPanTiltActionClient::createGoal()
    {
        const auto maybe_yaw = getInput<float>("yaw");
        float yaw;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_yaw))
        {
            return tl::make_unexpected("input port yaw is not set");
        }
        else
        {
            yaw = maybe_yaw.value();
        }
        const auto maybe_pitch = getInput<float>("pitch");
        float pitch;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_pitch))
        {
            return tl::make_unexpected("input port pitch is not set");
        }
        else
        {
            pitch = maybe_pitch.value();
        }
        const auto maybe_duration = getInput<float>("duration");
        float duration;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_duration))
        {
            return tl::make_unexpected("input port duration is not set");
        }
        else
        {
            duration = maybe_duration.value();
        }
        const auto maybe_speed = getInput<uint16_t>("speed");
        uint16_t speed;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_speed))
        {
            return tl::make_unexpected("input port speed is not set");
        }
        else
        {
            speed = maybe_speed.value();
        }
        const auto maybe_timeout = getInput<float>("timeout");
        float timeout;
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_timeout))
        {
            return tl::make_unexpected("input port timeout is not set");
        }
        else
        {
            timeout = maybe_timeout.value();
        }
        return pan_tilt_msgs::build<ControlPanTilt::Goal>().yaw(yaw).pitch(pitch).duration(duration).speed(speed).timeout(timeout);
    }

    tl::expected<bool, std::string> ControlPanTiltActionClient::processResult(const std::shared_ptr<ControlPanTilt::Result> result)
    {
        if (!result) return tl::make_unexpected("Result is null");
        setOutput<bool>("success", result->success);
        setOutput<std::string>("message", result->message);
        setOutput<float>("result_yaw", result->result_yaw);
        setOutput<float>("result_pitch", result->result_pitch);
        return true;
    }

}
