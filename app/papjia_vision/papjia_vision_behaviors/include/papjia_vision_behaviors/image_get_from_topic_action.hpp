#ifndef PAPJIA_GENERIC_BEHAVIORS__GET_IMAGE_FROM_TOPIC
#define PAPJIA_GENERIC_BEHAVIORS__GET_IMAGE_FROM_TOPIC

#include <papjia_behavior_tree/async_behavior_base.hpp>
#include <behaviortree_cpp/action_node.h>
#include <papjia_behavior_tree/check_error.hpp>

#include <sensor_msgs/msg/image.hpp>
#include <rclcpp/rclcpp.hpp>

namespace papjia::behaviors
{
    class ImageGetFromTopicAction : public papjia::behavior_tree::AsyncBehaviorBase
    {
    public:
        ImageGetFromTopicAction(const std::string &name, const BT::NodeConfig &config,
                                const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);

        static BT::PortsList providedPorts();

    private: /*  */
        tl::expected<bool, std::string> doWork() override;

        std::shared_future<tl::expected<bool, std::string>> &getFuture() override
        {
            return future_;
        }
        std::shared_future<tl::expected<bool, std::string>> future_;
    };
}

#endif