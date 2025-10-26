#ifndef TYPE_TRANS_BEHAVIORS_POSE_STAMPED_TO_JSON_ACTION_HPP_
#define TYPE_TRANS_BEHAVIORS_POSE_STAMPED_TO_JSON_ACTION_HPP_

#include <behaviortree_cpp/action_node.h>
#include <rclcpp/rclcpp.hpp>

namespace papjia::behaviors
{

class PoseStampedToJsonAction : public BT::SyncActionNode
{
public:
    PoseStampedToJsonAction(const std::string &name, const BT::NodeConfig &config);

    static BT::PortsList providedPorts();

    BT::NodeStatus tick() override;
};

} // namespace papjia::behaviors

#endif // TYPE_TRANS_BEHAVIORS_POSE_STAMPED_TO_JSON_ACTION_HPP_ 