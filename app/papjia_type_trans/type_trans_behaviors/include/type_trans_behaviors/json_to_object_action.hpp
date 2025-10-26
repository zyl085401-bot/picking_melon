#ifndef OBJECT_MANAGE_BEHAVIORS__JSON_TO_OBJECT_HPP
#define OBJECT_MANAGE_BEHAVIORS__JSON_TO_OBJECT_HPP

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia
{
    namespace behaviors
    {
        class JsonToObjectAction final : public BT::SyncActionNode
        {
        public:
            JsonToObjectAction(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts();
            BT::NodeStatus tick() override;
        };
    };
}

#endif