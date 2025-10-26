#include <algorithm>
#include <string>
#include <memory>

#include "nav2_core/exceptions.hpp"
#include "nav2_util/node_utils.hpp"
#include "nav2_util/geometry_utils.hpp"
#include "nav2_obstacle_stop_controller/obstacle_stop_controller.hpp"

using std::hypot;
using std::min;
using std::max;
using std::abs;
using nav2_util::declare_parameter_if_not_declared;
using nav2_util::geometry_utils::euclidean_distance;

namespace nav2_obstacle_stop_controller
{

/**
 * Find element in iterator with the minimum calculated value
 */
template<typename Iter, typename Getter>
Iter min_by(Iter begin, Iter end, Getter getCompareVal)
{
  if (begin == end) {
    return end;
  }
  auto lowest = getCompareVal(*begin);
  Iter lowest_it = begin;
  for (Iter it = ++begin; it != end; ++it) {
    auto comp = getCompareVal(*it);
    if (comp < lowest) {
      lowest = comp;
      lowest_it = it;
    }
  }
  return lowest_it;
}

void ObstacleStopController::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name, std::shared_ptr<tf2_ros::Buffer> tf,
  const std::shared_ptr<nav2_costmap_2d::Costmap2DROS> local_costmap)
{
  node_ = parent;

  auto node = node_.lock();

  local_costmap_ = local_costmap;
  tf_ = tf;
  plugin_name_ = name;
  logger_ = node->get_logger();
  clock_ = node->get_clock();

  declare_parameter_if_not_declared(
    node, plugin_name_ + ".desired_linear_vel", rclcpp::ParameterValue(
      0.2));
  declare_parameter_if_not_declared(
    node, plugin_name_ + ".lookahead_dist",
    rclcpp::ParameterValue(0.4));
  declare_parameter_if_not_declared(
    node, plugin_name_ + ".max_angular_vel", rclcpp::ParameterValue(
      1.0));
  declare_parameter_if_not_declared(
    node, plugin_name_ + ".transform_tolerance", rclcpp::ParameterValue(
      0.1));
  declare_parameter_if_not_declared(
    node, plugin_name_ + ".stop_threshold", rclcpp::ParameterValue(
      0.5));
  declare_parameter_if_not_declared(
    node, plugin_name_ + ".acceleration_limit", rclcpp::ParameterValue(
      0.5));


  node->get_parameter(plugin_name_ + ".desired_linear_vel", desired_linear_vel_);
  node->get_parameter(plugin_name_ + ".lookahead_dist", lookahead_dist_);
  node->get_parameter(plugin_name_ + ".max_angular_vel", max_angular_vel_);
  double transform_tolerance;
  node->get_parameter(plugin_name_ + ".transform_tolerance", transform_tolerance);
  transform_tolerance_ = rclcpp::Duration::from_seconds(transform_tolerance);
  node->get_parameter(plugin_name_ + ".stop_threshold", stop_threshold_);
  node->get_parameter(plugin_name_ + ".acceleration_limit", acceleration_limit_);
  
  global_pub_ = node->create_publisher<nav_msgs::msg::Path>("received_global_plan", 1);
  velocity_subscription_ = node->create_subscription<geometry_msgs::msg::Twist>(
  "cmd_vel", 10,
  std::bind(&ObstacleStopController::velocityCallback, this, std::placeholders::_1));
}

void ObstacleStopController::cleanup()
{
  RCLCPP_INFO(
    logger_,
    "Cleaning up controller: %s of type obstacle_stop_controller::ObstacleStopController",
    plugin_name_.c_str());
  global_pub_.reset();
}

void ObstacleStopController::activate()
{
  RCLCPP_INFO(
    logger_,
    "Activating controller: %s of type obstacle_stop_controller::ObstacleStopController\"  %s",
    plugin_name_.c_str(),plugin_name_.c_str());
  global_pub_->on_activate();
}

void ObstacleStopController::deactivate()
{
  RCLCPP_INFO(
    logger_,
    "Dectivating controller: %s of type obstacle_stop_controller::ObstacleStopController\"  %s",
    plugin_name_.c_str(),plugin_name_.c_str());
  global_pub_->on_deactivate();
}

void ObstacleStopController::setSpeedLimit(const double& speed_limit, const bool& percentage)
{
  (void) speed_limit;
  (void) percentage;
}

void ObstacleStopController::velocityCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
{
  current_velocity_ = *msg;
  current_linear_vel_ = msg->linear.x;
}

geometry_msgs::msg::TwistStamped ObstacleStopController::computeVelocityCommands(
  const geometry_msgs::msg::PoseStamped & pose,
  const geometry_msgs::msg::Twist & velocity,
  nav2_core::GoalChecker * goal_checker)
{
  (void)velocity;
  (void)goal_checker;

  auto transformed_plan = transformGlobalPlan(pose);

  // Find the first pose which is at a distance greater than the specified lookahed distance
  auto goal_pose_it = std::find_if(
    transformed_plan.poses.begin(), transformed_plan.poses.end(), [&](const auto & ps) {
      return hypot(ps.pose.position.x, ps.pose.position.y) >= lookahead_dist_;
    });

  // If the last pose is still within lookahed distance, take the last pose
  if (goal_pose_it == transformed_plan.poses.end()) {
    goal_pose_it = std::prev(transformed_plan.poses.end());
  }
  auto goal_pose = goal_pose_it->pose;

  double linear_vel, angular_vel;

  auto costmap = local_costmap_->getCostmap();
  bool obstacle_detected = false;
  unsigned int mx, my;

  double robot_x = pose.pose.position.x;
  double robot_y = pose.pose.position.y;

  tf2::Quaternion q(
    pose.pose.orientation.x,
    pose.pose.orientation.y,
    pose.pose.orientation.z,
    pose.pose.orientation.w);
  tf2::Matrix3x3 m(q);
  double roll, pitch, yaw;
  m.getRPY(roll, pitch, yaw);

  // 基于stop_threshold_计算前方的点
  double safe_distance = 0.1;
  for (double distance = safe_distance; distance <= stop_threshold_; distance += safe_distance) {
    double x = robot_x + distance * cos(yaw);
    double y = robot_y + distance * sin(yaw);

    if (costmap->worldToMap(x, y, mx, my)) {
      auto cost = costmap->getCost(mx, my);
      if (cost > nav2_costmap_2d::INSCRIBED_INFLATED_OBSTACLE) {
        obstacle_detected = true;
        RCLCPP_INFO(logger_, "Obstacle detected in front %fm away", distance);
        break;
      }
    }
  }
  if (goal_pose.position.x > 0) {
      auto curvature = 2.0 * goal_pose.position.y /
                       (goal_pose.position.x * goal_pose.position.x + goal_pose.position.y * goal_pose.position.y);
      linear_vel = desired_linear_vel_;
      angular_vel = desired_linear_vel_ * curvature;
  } else {
      double distance = std::hypot(goal_pose.position.x, goal_pose.position.y);
      linear_vel = 0.1 * distance;
      angular_vel = std::copysign(0.5 * max_angular_vel_, goal_pose.position.y);
  }

  auto now = rclcpp::Clock().now();
  if (last_time_.nanoseconds() == 0)
  {
    // Initialize last_time_ on the first run
    last_time_ = now;
  }

  if (obstacle_detected) {
    linear_vel = 0.0;
    // angular_vel = 0.0;
  } else {
    double max_linear_acceleration = acceleration_limit_ * (now - last_time_).seconds();
    if (linear_vel > current_linear_vel_) {
      current_linear_vel_ = std::min(linear_vel, current_linear_vel_ + max_linear_acceleration);
    } else {
      current_linear_vel_ = linear_vel; // Sudden stop or deceleration is allowed
    }
    linear_vel = current_linear_vel_;
  }

  last_time_ = now;

  // Create and publish a TwistStamped message with the desired velocity
  geometry_msgs::msg::TwistStamped cmd_vel;
  cmd_vel.header.frame_id = pose.header.frame_id;
  cmd_vel.header.stamp = clock_->now();
  cmd_vel.twist.linear.x = linear_vel;
  cmd_vel.twist.angular.z = std::max(
    -1.0 * abs(max_angular_vel_), std::min(
      angular_vel, abs(
        max_angular_vel_)));

  return cmd_vel;
}

void ObstacleStopController::setPlan(const nav_msgs::msg::Path & path)
{
  global_pub_->publish(path);
  global_plan_ = path;
}

nav_msgs::msg::Path
ObstacleStopController::transformGlobalPlan(
  const geometry_msgs::msg::PoseStamped & pose)
{
  // Original mplementation taken fron nav2_dwb_controller

  if (global_plan_.poses.empty()) {
    throw nav2_core::PlannerException("Received plan with zero length");
  }

  // let's get the pose of the robot in the frame of the plan
  geometry_msgs::msg::PoseStamped robot_pose;
  if (!transformPose(
      tf_, global_plan_.header.frame_id, pose,
      robot_pose, transform_tolerance_))
  {
    throw nav2_core::PlannerException("Unable to transform robot pose into global plan's frame");
  }

  // We'll discard points on the plan that are outside the local costmap
  nav2_costmap_2d::Costmap2D * costmap = local_costmap_->getCostmap();
  double dist_threshold = std::max(costmap->getSizeInCellsX(), costmap->getSizeInCellsY()) *
    costmap->getResolution() / 2.0;

  // First find the closest pose on the path to the robot
  auto transformation_begin =
    min_by(
    global_plan_.poses.begin(), global_plan_.poses.end(),
    [&robot_pose](const geometry_msgs::msg::PoseStamped & ps) {
      return euclidean_distance(robot_pose, ps);
    });

  // From the closest point, look for the first point that's further then dist_threshold from the
  // robot. These points are definitely outside of the costmap so we won't transform them.
  auto transformation_end = std::find_if(
    transformation_begin, end(global_plan_.poses),
    [&](const auto & global_plan_pose) {
      return euclidean_distance(robot_pose, global_plan_pose) > dist_threshold;
    });

  // Helper function for the transform below. Transforms a PoseStamped from global frame to local
  auto transformGlobalPoseToLocal = [&](const auto & global_plan_pose) {
      // We took a copy of the pose, let's lookup the transform at the current time
      geometry_msgs::msg::PoseStamped stamped_pose, transformed_pose;
      stamped_pose.header.frame_id = global_plan_.header.frame_id;
      stamped_pose.header.stamp = pose.header.stamp;
      stamped_pose.pose = global_plan_pose.pose;
      transformPose(
        tf_, local_costmap_->getBaseFrameID(),
        stamped_pose, transformed_pose, transform_tolerance_);
      return transformed_pose;
    };

  // Transform the near part of the global plan into the robot's frame of reference.
  nav_msgs::msg::Path transformed_plan;
  std::transform(
    transformation_begin, transformation_end,
    std::back_inserter(transformed_plan.poses),
    transformGlobalPoseToLocal);
  transformed_plan.header.frame_id = local_costmap_->getBaseFrameID();
  transformed_plan.header.stamp = pose.header.stamp;

  // Remove the portion of the global plan that we've already passed so we don't
  // process it on the next iteration (this is called path pruning)
  global_plan_.poses.erase(begin(global_plan_.poses), transformation_begin);
  global_pub_->publish(transformed_plan);

  if (transformed_plan.poses.empty()) {
    throw nav2_core::PlannerException("Resulting plan has 0 poses in it.");
  }

  return transformed_plan;
}

bool ObstacleStopController::transformPose(
  const std::shared_ptr<tf2_ros::Buffer> tf,
  const std::string frame,
  const geometry_msgs::msg::PoseStamped & in_pose,
  geometry_msgs::msg::PoseStamped & out_pose,
  const rclcpp::Duration & transform_tolerance
) const
{
  // Implementation taken as is fron nav_2d_utils in nav2_dwb_controller

  if (in_pose.header.frame_id == frame) {
    out_pose = in_pose;
    return true;
  }

  try {
    tf->transform(in_pose, out_pose, frame);
    return true;
  } catch (tf2::ExtrapolationException & ex) {
    auto transform = tf->lookupTransform(
      frame,
      in_pose.header.frame_id,
      tf2::TimePointZero
    );
    if (
      (rclcpp::Time(in_pose.header.stamp) - rclcpp::Time(transform.header.stamp)) >
      transform_tolerance)
    {
      RCLCPP_ERROR(
        rclcpp::get_logger("tf_help"),
        "Transform data too old when converting from %s to %s",
        in_pose.header.frame_id.c_str(),
        frame.c_str()
      );
      RCLCPP_ERROR(
        rclcpp::get_logger("tf_help"),
        "Data time: %ds %uns, Transform time: %ds %uns",
        in_pose.header.stamp.sec,
        in_pose.header.stamp.nanosec,
        transform.header.stamp.sec,
        transform.header.stamp.nanosec
      );
      return false;
    } else {
      tf2::doTransform(in_pose, out_pose, transform);
      return true;
    }
  } catch (tf2::TransformException & ex) {
    RCLCPP_ERROR(
      rclcpp::get_logger("tf_help"),
      "Exception in transformPose: %s",
      ex.what()
    );
    return false;
  }
  return false;
}

}  // namespace nav2_obstacle_stop_controller

// Register this controller as a nav2_core plugin
PLUGINLIB_EXPORT_CLASS(nav2_obstacle_stop_controller::ObstacleStopController, nav2_core::Controller)