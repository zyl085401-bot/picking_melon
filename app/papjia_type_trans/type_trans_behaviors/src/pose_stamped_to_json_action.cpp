#include <nlohmann/json.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include "type_trans_behaviors/pose_stamped_to_json_action.hpp"

namespace papjia::behaviors
{
    PoseStampedToJsonAction::PoseStampedToJsonAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList PoseStampedToJsonAction::providedPorts()
    {
        return BT::PortsList({
            BT::InputPort<geometry_msgs::msg::PoseStamped>("pose"),
            BT::OutputPort<std::string>("json_result")
        });
    }

    BT::NodeStatus PoseStampedToJsonAction::tick()
    {
        nlohmann::json json_data;

        geometry_msgs::msg::PoseStamped pose;
        auto maybe_pose = getInput<geometry_msgs::msg::PoseStamped>("pose");
        if (!maybe_pose)
        {
            RCLCPP_ERROR(rclcpp::get_logger("PoseStampedToJsonAction"), "Failed to get pose input");
            return BT::NodeStatus::FAILURE;
        }
        pose = maybe_pose.value();

        // 构建JSON数据
        json_data["header"] = {
            {"stamp", {
                {"sec", pose.header.stamp.sec},
                {"nanosec", pose.header.stamp.nanosec}
            }},
            {"frame_id", pose.header.frame_id}
        };

        json_data["pose"] = {
            {"position", {
                {"x", pose.pose.position.x},
                {"y", pose.pose.position.y},
                {"z", pose.pose.position.z}
            }},
            {"orientation", {
                {"x", pose.pose.orientation.x},
                {"y", pose.pose.orientation.y},
                {"z", pose.pose.orientation.z},
                {"w", pose.pose.orientation.w}
            }}
        };

        std::string json_str = json_data.dump();
        setOutput("json_result", json_str);

        RCLCPP_INFO(rclcpp::get_logger("PoseStampedToJsonAction"), "Converted pose to JSON: %s", json_str.c_str());

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors 