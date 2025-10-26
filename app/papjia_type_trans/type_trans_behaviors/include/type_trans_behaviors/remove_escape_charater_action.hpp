#ifndef OBJECT_MANAGE_BEHAVIORS__Remove_Escape_Character_HPP
#define OBJECT_MANAGE_BEHAVIORS__Remove_Escape_Character_HPP

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia
{
    namespace behaviors
    {
        class RemoveEscapeCharacterAction final : public BT::SyncActionNode
        {
        public:
            RemoveEscapeCharacterAction(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts();
            BT::NodeStatus tick() override;
        };
    };
}

#endif