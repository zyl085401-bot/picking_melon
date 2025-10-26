#ifndef OBJECT_MANAGE_BEHAVIORS__GET_OBJECT_FROM_DBJSON_HPP
#define OBJECT_MANAGE_BEHAVIORS__GET_OBJECT_FROM_DBJSON_HPP

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia
{
    namespace behaviors
    {
        class GetObjectFromDBJsonAction final : public BT::SyncActionNode
        {
        public:
            GetObjectFromDBJsonAction(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts();
            BT::NodeStatus tick() override;
        };
    };
}

#endif