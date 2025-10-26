#ifndef OBJECT_MANAGE_BEHAVIORS__OBJECT_TO_JSON_HPP
#define OBJECT_MANAGE_BEHAVIORS__OBJECT_TO_JSON_HPP

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia
{
    namespace behaviors
    {
        class ObjectsToJsonAction final : public BT::SyncActionNode
        {
        public:
            ObjectsToJsonAction(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts();
            BT::NodeStatus tick() override;
        };
    };
}

#endif