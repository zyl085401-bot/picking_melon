#pragma once

#include <rclcpp/rclcpp.hpp>
#include <behaviortree_cpp/action_node.h>
#include <papjia_behavior_tree/custom_types.hpp>
#include <papjia_vision_interface/msg/object.hpp>
#include <papjia_mtc_bt/waypoint.hpp>
#include <deque>
#include <tf2/LinearMath/Quaternion.h>

namespace papjia
{
    namespace behaviors
    {
        class FilterObject : public BT::SyncActionNode
        {
        public:
            FilterObject(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts()
            {
                return BT::PortsList({BT::InputPort<std::vector<papjia_vision_interface::msg::Object>>("objects"),
                                      BT::OutputPort<papjia_vision_interface::msg::Object>("filtered_object")});
            }
            BT::NodeStatus tick() override;
        };

        class GetGraspWaypoints : public BT::SyncActionNode
        {
        public:
            GetGraspWaypoints(const std::string &name, const BT::NodeConfig &config);
            static BT::PortsList providedPorts()
            {
                return BT::PortsList({
                    BT::InputPort<papjia_vision_interface::msg::Object>("filtered_object"),
                    BT::InputPort<double>("pick_roll"),
                    BT::InputPort<double>("pick_pitch"),
                    BT::InputPort<double>("pick_yaw"),
                    BT::InputPort<std::string>("group"),
                    BT::InputPort<std::string>("frame_id"),
                    BT::InputPort<std::string>("ik_frame"),
                    BT::InputPort<std::string>("planner"),
                    BT::InputPort<double>("max_velocity_scaling_factor"),
                    BT::InputPort<double>("max_acceleration_scaling_factor"),
                    BT::OutputPort<std::shared_ptr<papjia_waypoint::Waypoint>>("pre_grasp_waypoint"),
                    BT::OutputPort<std::shared_ptr<papjia_waypoint::Waypoint>>("grasp_waypoint")
                });
            }
            BT::NodeStatus tick() override;
        };
        
    }
}