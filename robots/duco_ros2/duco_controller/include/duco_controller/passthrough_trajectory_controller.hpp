#pragma once

#include <stdint.h>

#include <functional>
#include <limits>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include <controller_interface/controller_interface.hpp>
#include <realtime_tools/realtime_buffer.hpp>
#include <realtime_tools/realtime_server_goal_handle.hpp>
#include <rclcpp_action/server.hpp>
#include <rclcpp_action/create_server.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/server_goal_handle.hpp>
#include <rclcpp/time.hpp>
#include <rclcpp/duration.hpp>
#include <rclcpp/clock.hpp>

#include "trajectory_msgs/msg/joint_trajectory.hpp"
#include "control_msgs/action/follow_joint_trajectory.hpp"

#include "duco_msgs/srv/set_vel.hpp"

#include "duco_controller/passthrough_trajectory_controller_parameters.hpp"

namespace duco_controller
{
    /*
     * 0.0: No trajectory to forward, the controller is idling and ready to receive a new trajectory.
     * 1.0: The controller has received and accepted a new trajectory. When the state is 1.0, the controller will write a
     * point to the hardware interface.
     * 2.0: The hardware interface will read the point written from the controller. The state will switch between 1.0
     * and 2.0 until all points have been read by the hardware interface.
     * 3.0: The hardware interface has read all the points, and will now write all the points to the physical robot
     * controller.
     * 4.0: The robot is moving through the trajectory.
     * 5.0: The robot finished executing the trajectory.
     */
    const double TRANSFER_STATE_IDLE = 0.0;
    const double TRANSFER_STATE_WAITING_FOR_POINT = 1.0;
    const double TRANSFER_STATE_TRANSFERRING = 2.0;
    const double TRANSFER_STATE_TRANSFER_DONE = 3.0;
    const double TRANSFER_STATE_IN_MOTION = 4.0;
    const double TRANSFER_STATE_DONE = 5.0;

    class PassthroughTrajectoryController : public controller_interface::ControllerInterface
    {
    public:
        PassthroughTrajectoryController() = default;
        ~PassthroughTrajectoryController() override = default;

        controller_interface::InterfaceConfiguration state_interface_configuration() const override;
        controller_interface::InterfaceConfiguration command_interface_configuration() const override;

        controller_interface::CallbackReturn on_init() override;
        controller_interface::CallbackReturn on_configure(const rclcpp_lifecycle::State &previous_state) override;
        controller_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State &previous_state) override;
        controller_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State &previous_state) override;

        controller_interface::return_type update(const rclcpp::Time &time, const rclcpp::Duration &period) override;

    private:
        using FollowJTrajAction = control_msgs::action::FollowJointTrajectory;
        using RealtimeGoalHandle = realtime_tools::RealtimeServerGoalHandle<FollowJTrajAction>;
        using RealtimeGoalHandlePtr = std::shared_ptr<RealtimeGoalHandle>;
        using RealtimeGoalHandleBuffer = realtime_tools::RealtimeBuffer<RealtimeGoalHandlePtr>;

        void start_action_server();
        void end_goal();
        bool check_goal_tolerance();
        bool check_goal(std::shared_ptr<const control_msgs::action::FollowJointTrajectory::Goal> goal);

        // 定义参数监听器
        std::shared_ptr<passthrough_trajectory_controller::ParamListener> passthrough_param_listener_;
        passthrough_trajectory_controller::Params passthrough_params_;

        // 定义发送轨迹动作服务器
        rclcpp_action::Server<FollowJTrajAction>::SharedPtr send_trajectory_action_server_;
        rclcpp_action::GoalResponse goal_received_callback(
            const rclcpp_action::GoalUUID &uuid, std::shared_ptr<const FollowJTrajAction::Goal> goal);
        rclcpp_action::CancelResponse goal_cancelled_callback(
            const std::shared_ptr<rclcpp_action::ServerGoalHandle<FollowJTrajAction>> goal_handle);
        void goal_accepted_callback(
            std::shared_ptr<rclcpp_action::ServerGoalHandle<FollowJTrajAction>> goal_handle);

        // 定义速度服务
        rclcpp::Service<duco_msgs::srv::SetVel>::SharedPtr set_vel_service_;
        bool set_vel_service_callback(
            const std::shared_ptr<duco_msgs::srv::SetVel::Request> request,
            std::shared_ptr<duco_msgs::srv::SetVel::Response> response);


        realtime_tools::RealtimeBuffer<std::vector<std::string>> joint_names_;
        std::vector<std::string> state_interface_types_;

        std::vector<std::string> joint_state_interface_names_;
        std::vector<std::reference_wrapper<hardware_interface::LoanedStateInterface>> joint_position_state_interface_;

        std::unordered_map<std::string, size_t> create_joint_mapping(const std::vector<std::string> &joint_names) const;
        RealtimeGoalHandleBuffer rt_active_goal_;
        rclcpp::TimerBase::SharedPtr goal_handle_timer_;
        realtime_tools::RealtimeBuffer<std::unordered_map<std::string, size_t>> joint_trajectory_mapping_;
        rclcpp::Duration action_monitor_period_ = rclcpp::Duration::from_seconds(0.05);

        trajectory_msgs::msg::JointTrajectory active_joint_traj_;
        realtime_tools::RealtimeBuffer<std::vector<control_msgs::msg::JointTolerance>> goal_tolerance_;

        std::atomic<size_t> current_index_;
        std::atomic<bool> trajectory_active_;
        std::atomic<size_t> number_of_joints_;

        std::optional<std::reference_wrapper<hardware_interface::LoanedStateInterface>> scaling_state_interface_;
        std::optional<std::reference_wrapper<hardware_interface::LoanedCommandInterface>> abort_command_interface_;
        std::optional<std::reference_wrapper<hardware_interface::LoanedCommandInterface>> transfer_command_interface_;
        std::optional<std::reference_wrapper<hardware_interface::LoanedCommandInterface>> vel_;
    };

} // namespace duco_controller