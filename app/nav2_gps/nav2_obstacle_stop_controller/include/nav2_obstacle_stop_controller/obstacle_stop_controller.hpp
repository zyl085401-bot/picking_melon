#ifndef NAV2_OBSTACLE_STOP_CONTROLLER__OBSTACLE_STOP_CONTROLLER_HPP_
#define NAV2_OBSTACLE_STOP_CONTROLLER__OBSTACLE_STOP_CONTROLLER_HPP_

#include <string>
#include <vector>
#include <memory>

#include "nav2_core/controller.hpp"
#include "rclcpp/rclcpp.hpp"
#include "pluginlib/class_loader.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "geometry_msgs/msg/twist.hpp"

namespace nav2_obstacle_stop_controller
{

class ObstacleStopController : public nav2_core::Controller
{
public:
  ObstacleStopController() = default;
  ~ObstacleStopController() override = default;

  void configure(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    std::string name, std::shared_ptr<tf2_ros::Buffer> tf,
    std::shared_ptr<nav2_costmap_2d::Costmap2DROS> local_costmap) override;


  void cleanup() override;
  void activate() override;
  void deactivate() override;
  void setSpeedLimit(const double & speed_limit, const bool & percentage) override;
  void velocityCallback(const geometry_msgs::msg::Twist::SharedPtr msg);

  geometry_msgs::msg::TwistStamped computeVelocityCommands(
    const geometry_msgs::msg::PoseStamped & pose,
    const geometry_msgs::msg::Twist & velocity,
    nav2_core::GoalChecker * goal_checker) override;

  void setPlan(const nav_msgs::msg::Path & path) override;

protected:
  nav_msgs::msg::Path transformGlobalPlan(const geometry_msgs::msg::PoseStamped & pose);

  void scanCallback(const sensor_msgs::msg::LaserScan::SharedPtr scan_msg);
  geometry_msgs::msg::Twist current_velocity_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr velocity_subscription_;

  bool transformPose(
    const std::shared_ptr<tf2_ros::Buffer> tf,
    const std::string frame,
    const geometry_msgs::msg::PoseStamped & in_pose,
    geometry_msgs::msg::PoseStamped & out_pose,
    const rclcpp::Duration & transform_tolerance
  ) const;

  rclcpp_lifecycle::LifecycleNode::WeakPtr node_;
  std::shared_ptr<tf2_ros::Buffer> tf_;
  std::string plugin_name_;
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> local_costmap_;
  rclcpp::Logger logger_ {rclcpp::get_logger("ObstacleStopController")};
  rclcpp::Clock::SharedPtr clock_;

  double desired_linear_vel_;
  double lookahead_dist_;
  double max_angular_vel_;
  double stop_threshold_;
  double acceleration_limit_;
  double current_linear_vel_;

  rclcpp::Time last_time_;  // 添加这行

  rclcpp::Duration transform_tolerance_ {0, 0};

  nav_msgs::msg::Path global_plan_;
  std::shared_ptr<rclcpp_lifecycle::LifecyclePublisher<nav_msgs::msg::Path>> global_pub_;
};

}  // namespace nav2_obstacle_stop_controller

#endif  // NAV2_OBSTACLE_STOP_CONTROLLER__OBSTACLE_STOP_CONTROLLER_HPP_
