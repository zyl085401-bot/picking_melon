#include "papjia_vision_behaviors/camera_info_get_from_topic_action.hpp"

static const rclcpp::Logger LOGGER = rclcpp::get_logger("behaviros_camera_info_get_from_topic");

namespace papjia::behaviors
{

    CameraInfoGetFromTopicAction::CameraInfoGetFromTopicAction(const std::string &name, const BT::NodeConfig &config,
                                                     const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
        : papjia::behavior_tree::AsyncBehaviorBase(name, config, shared_resources)
    {
        RCLCPP_INFO_STREAM(LOGGER, "Init");
    }

    BT::PortsList CameraInfoGetFromTopicAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("topic_name"),
                              BT::OutputPort<sensor_msgs::msg::CameraInfo>("camera_info")});
    }

    tl::expected<bool, std::string> CameraInfoGetFromTopicAction::doWork()
    {
        auto topic_name = getInput<std::string>("topic_name");
        auto node = this->shared_resources_->node_;

        rclcpp::CallbackGroup::SharedPtr cb_group_not_executed = node->create_callback_group(
            rclcpp::CallbackGroupType::MutuallyExclusive, false);
        auto subscription_options = rclcpp::SubscriptionOptions();
        subscription_options.callback_group = cb_group_not_executed;
        rclcpp::QoS qos(rclcpp::KeepLast(10));
        auto not_executed_callback =
            [this]([[maybe_unused]] sensor_msgs::msg::CameraInfo::ConstSharedPtr msg) -> void
        {
            RCLCPP_INFO_STREAM(LOGGER, "I never heard message");
        };
        rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr sub = node->create_subscription<sensor_msgs::msg::CameraInfo>(topic_name.value(), qos, not_executed_callback, subscription_options);

        sensor_msgs::msg::CameraInfo msg;
        rclcpp::MessageInfo msg_info;

        float timeout = 3.0;
        float hz = 50.0;
        rclcpp::Rate rate(hz);
        while (rclcpp::ok() && timeout > 0.0)
        {
            rate.sleep();
            if (sub->take(msg, msg_info))
            {

                setOutput("camera_info", msg);
                RCLCPP_INFO(node->get_logger(), "Catch camera info %d x %d", msg.width, msg.height);
                return true;
            }
            timeout -= 1.0 / hz;
        }
        return tl::make_unexpected(std::string("No CameraInfo found from: ") + topic_name.error());
    }
}
