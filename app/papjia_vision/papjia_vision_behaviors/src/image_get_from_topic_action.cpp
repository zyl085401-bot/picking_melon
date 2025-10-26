#include "papjia_vision_behaviors/image_get_from_topic_action.hpp"

static const rclcpp::Logger LOGGER = rclcpp::get_logger("behaviros_image_get_from_topic");

namespace papjia::behaviors
{

    ImageGetFromTopicAction::ImageGetFromTopicAction(const std::string &name, const BT::NodeConfig &config,
                                                     const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
        : papjia::behavior_tree::AsyncBehaviorBase(name, config, shared_resources)
    {
        RCLCPP_INFO_STREAM(LOGGER, "Init");
    }

    BT::PortsList ImageGetFromTopicAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("topic_name"),
                              BT::OutputPort<sensor_msgs::msg::Image>("image")});
    }

    tl::expected<bool, std::string> ImageGetFromTopicAction::doWork()
    {
        auto topic_name = getInput<std::string>("topic_name");
        auto node = this->shared_resources_->node_;

        rclcpp::CallbackGroup::SharedPtr cb_group_not_executed = node->create_callback_group(
            rclcpp::CallbackGroupType::MutuallyExclusive, false);
        auto subscription_options = rclcpp::SubscriptionOptions();
        subscription_options.callback_group = cb_group_not_executed;
        rclcpp::QoS qos(rclcpp::KeepLast(10));
        auto not_executed_callback =
            [this]([[maybe_unused]] sensor_msgs::msg::Image::ConstSharedPtr msg) -> void
        {
            RCLCPP_INFO_STREAM(LOGGER, "I never heard message");
        };
        rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub = node->create_subscription<sensor_msgs::msg::Image>(topic_name.value(), qos, not_executed_callback, subscription_options);

        sensor_msgs::msg::Image msg;
        rclcpp::MessageInfo msg_info;

        float timeout = 3.0;
        float hz = 50.0;
        rclcpp::Rate rate(hz);
        while (rclcpp::ok() && timeout > 0.0)
        {
            rate.sleep();
            if (sub->take(msg, msg_info))
            {

                setOutput("image", msg);
                RCLCPP_INFO(node->get_logger(), "Catch image");
                return true;
            }
            timeout -= 1.0 / hz;
        }
        return tl::make_unexpected(std::string("No image found from: ") + topic_name.error());
    }
}
