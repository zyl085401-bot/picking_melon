#include "papjia_melon_behaviors/action_nodes.hpp"

namespace papjia
{
    namespace behaviors
    {
        static const rclcpp::Logger logger = rclcpp::get_logger("papjia_melon_bt");

        double distance(double x1, double y1, double x2, double y2)
        {
            return std::sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
        }

        /****************************************************************************/
        /************************** FilterObject ***************************** */
        /****************************************************************************/
        FilterObject::FilterObject(const std::string &name, const BT::NodeConfiguration &config)
            : BT::SyncActionNode(name, config)
        {
        }

        BT::NodeStatus FilterObject::tick()
        {
            std::vector<papjia_vision_interface::msg::Object> objects;

            if (!getInput<std::vector<papjia_vision_interface::msg::Object>>("objects", objects))
            {
                RCLCPP_ERROR(logger, "Objects not set");
                return BT::NodeStatus::FAILURE;
            }

            papjia_vision_interface::msg::Object filtered_object;
            double min_distance = std::numeric_limits<double>::max();
            // 遍历所有识别到的物体
            for (const auto &object : objects)
            {
                // 计算物体到机器人基座的距离
                double dis_to_base = distance(object.pose.position.x, object.pose.position.y, 0, 0);
                RCLCPP_INFO_STREAM(logger, "物体到基座距离: " << dis_to_base);
                
                // 如果找到更近的物体,更新最近物体和最小距离
                if (dis_to_base < min_distance)
                {
                    filtered_object = object;
                    min_distance = dis_to_base;
                }
            }
            try
            {
                RCLCPP_INFO_STREAM(logger, "最近的物体, x: " << filtered_object.pose.position.x << ", y: " << filtered_object.pose.position.y << ", 距离: " << min_distance);
                setOutput("filtered_object", filtered_object);
                return BT::NodeStatus::SUCCESS;
            }
            catch(const std::exception& e)
            {
                RCLCPP_ERROR(logger, "No object found");
                return BT::NodeStatus::FAILURE;
            }
        }

        /****************************************************************************/
        /************************** GetGraspWaypoints ***************************** */
        /****************************************************************************/
        GetGraspWaypoints::GetGraspWaypoints(const std::string &name, const BT::NodeConfiguration &config)
            : BT::SyncActionNode(name, config)
        {
        }

        BT::NodeStatus GetGraspWaypoints::tick()
        {
            // 获取输入参数
            papjia_vision_interface::msg::Object filtered_object;
            double pick_roll, pick_pitch, pick_yaw;
            std::string group, frame_id, ik_frame, planner;
            double max_velocity_scaling_factor, max_acceleration_scaling_factor;

            if (!getInput<papjia_vision_interface::msg::Object>("filtered_object", filtered_object))
            {
                RCLCPP_ERROR(logger, "Filtered object not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<double>("pick_roll", pick_roll))
            {
                RCLCPP_ERROR(logger, "Pick roll not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<double>("pick_pitch", pick_pitch))
            {
                RCLCPP_ERROR(logger, "Pick pitch not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<double>("pick_yaw", pick_yaw))
            {
                RCLCPP_ERROR(logger, "Pick yaw not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<std::string>("group", group))
            {
                RCLCPP_ERROR(logger, "Group not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<std::string>("frame_id", frame_id))
            {
                RCLCPP_ERROR(logger, "Frame ID not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<std::string>("ik_frame", ik_frame))
            {
                RCLCPP_ERROR(logger, "IK frame not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<std::string>("planner", planner))
            {
                RCLCPP_ERROR(logger, "Planner not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<double>("max_velocity_scaling_factor", max_velocity_scaling_factor))
            {
                RCLCPP_ERROR(logger, "Max velocity scaling factor not set");
                return BT::NodeStatus::FAILURE;
            }
            if (!getInput<double>("max_acceleration_scaling_factor", max_acceleration_scaling_factor))
            {
                RCLCPP_ERROR(logger, "Max acceleration scaling factor not set");
                return BT::NodeStatus::FAILURE;
            }

            try
            {
                double pre_waypoint2object_distance = 0.1; // 预备抓取点距离物体10cm
                double offset_x = 0.0;
                double offset_y = 0.0;
                double offset_z = 0.0;
                if (std::abs(pick_yaw) > 0.01)
                {
                    // 根据yaw值计算offset_x, offset_y
                    offset_x = pre_waypoint2object_distance * std::cos(pick_yaw);
                    offset_y = pre_waypoint2object_distance * std::sin(pick_yaw);
                }
                else
                {
                    offset_x = pre_waypoint2object_distance;
                    offset_y = 0.0;
                }
                // 创建预备抓取点
                std::array<double, 3> pre_grasp_position = {
                    filtered_object.pose.position.x - offset_x,
                    filtered_object.pose.position.y - offset_y,
                    filtered_object.pose.position.z - offset_z
                };

                // 使用输入的欧拉角创建四元数
                tf2::Quaternion q;
                q.setRPY(pick_roll, pick_pitch, pick_yaw);
                std::array<double, 4> pre_grasp_orientation = {
                    q.x(), q.y(), q.z(), q.w()
                };

                auto pre_grasp_waypoint = std::make_shared<papjia_waypoint::CartWaypoint>(
                    "pre_grasp",
                    pre_grasp_position,
                    pre_grasp_orientation,
                    group,
                    frame_id,
                    ik_frame,
                    planner,
                    max_velocity_scaling_factor,
                    max_acceleration_scaling_factor
                );

                // 创建实际抓取点
                std::array<double, 3> grasp_position = {
                    filtered_object.pose.position.x,
                    filtered_object.pose.position.y,
                    filtered_object.pose.position.z
                };

                auto grasp_waypoint = std::make_shared<papjia_waypoint::CartWaypoint>(
                    "grasp",
                    grasp_position,
                    pre_grasp_orientation,  // 使用相同的方向
                    group,
                    frame_id,
                    ik_frame,
                    planner,
                    max_velocity_scaling_factor,
                    max_acceleration_scaling_factor
                );

                RCLCPP_INFO_STREAM(logger, "生成抓取点位 - 预备点: (" 
                    << pre_grasp_position[0] << ", "
                    << pre_grasp_position[1] << ", "
                    << pre_grasp_position[2] << ")");
                
                RCLCPP_INFO_STREAM(logger, "生成抓取点位 - 抓取点: (" 
                    << grasp_position[0] << ", "
                    << grasp_position[1] << ", "
                    << grasp_position[2] << ")");

                setOutput("pre_grasp_waypoint", std::static_pointer_cast<papjia_waypoint::Waypoint>(pre_grasp_waypoint));
                setOutput("grasp_waypoint", std::static_pointer_cast<papjia_waypoint::Waypoint>(grasp_waypoint));
                return BT::NodeStatus::SUCCESS;
            }
            catch(const std::exception& e)
            {
                RCLCPP_ERROR(logger, "Failed to generate grasp waypoints: %s", e.what());
                return BT::NodeStatus::FAILURE;
            }
        }
    }
}