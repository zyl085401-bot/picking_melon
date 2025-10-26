#ifndef OBJECT_MANAGE_BEHAVIORS__OBJECT2D_TO_JSON_HPP
#define OBJECT_MANAGE_BEHAVIORS__OBJECT2D_TO_JSON_HPP

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia
{
    namespace behaviors
    {
        class Objects2dToJsonAction final : public BT::SyncActionNode
        {
        public:
            Objects2dToJsonAction(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts();
            BT::NodeStatus tick() override;
        };
    };
}

#endif