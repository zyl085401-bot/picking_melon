#include "duco_controller/passthrough_trajectory_controller.hpp"

namespace duco_controller
{

    controller_interface::CallbackReturn PassthroughTrajectoryController::on_init()
    {
        try
        {
            passthrough_param_listener_ = std::make_shared<passthrough_trajectory_controller::ParamListener>(get_node());
            passthrough_params_ = passthrough_param_listener_->get_params();
            current_index_ = 0;
            auto joint_names = passthrough_params_.joints;
            joint_names_.writeFromNonRT(joint_names);
            number_of_joints_ = joint_names.size();
            state_interface_types_ = passthrough_params_.state_interfaces;
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Exception thrown during init: %s", e.what());
            return controller_interface::CallbackReturn::ERROR;
        }
        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::CallbackReturn PassthroughTrajectoryController::on_configure(
        const rclcpp_lifecycle::State &previous_state)
    {
        start_action_server();
        trajectory_active_ = false;

        joint_state_interface_names_.clear();
        joint_state_interface_names_.reserve(number_of_joints_ * state_interface_types_.size());

        auto joint_names_internal = joint_names_.readFromRT();
        for (const auto &joint_name : *joint_names_internal)
        {
            for (const auto &interface_type : state_interface_types_)
            {
                joint_state_interface_names_.emplace_back(joint_name + "/" + interface_type);
            }
        }

        return ControllerInterface::on_configure(previous_state);
    }

    controller_interface::InterfaceConfiguration PassthroughTrajectoryController::state_interface_configuration() const
    {
        controller_interface::InterfaceConfiguration conf;
        conf.type = controller_interface::interface_configuration_type::INDIVIDUAL;

        std::copy(joint_state_interface_names_.cbegin(), joint_state_interface_names_.cend(), std::back_inserter(conf.names));
        return conf;
    }

    controller_interface::InterfaceConfiguration PassthroughTrajectoryController::command_interface_configuration() const
    {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;

        const std::string tf_prefix = passthrough_params_.tf_prefix;

        for (size_t i = 0; i < number_of_joints_; ++i)
        {
            config.names.emplace_back(tf_prefix + "trajectory_passthrough/setpoint_positions_" + std::to_string(i));
        }

        config.names.push_back(tf_prefix + "trajectory_passthrough/abort");
        config.names.emplace_back(tf_prefix + "trajectory_passthrough/transfer_state");
        config.names.emplace_back(tf_prefix + "trajectory_passthrough/vel");

        return config;
    }

    controller_interface::CallbackReturn PassthroughTrajectoryController::on_activate(const rclcpp_lifecycle::State &state)
    {
        joint_position_state_interface_.clear();

        for (auto &interface_name : joint_state_interface_names_)
        {
            auto interface_it = std::find_if(state_interfaces_.begin(), state_interfaces_.end(),
                                             [&](auto &interface)
                                             { return (interface.get_name() == interface_name); });
            if (interface_it != state_interfaces_.end())
            {
                if (interface_it->get_interface_name() == "position")
                {
                    joint_position_state_interface_.emplace_back(*interface_it);
                }
            }
        }

        {
            const std::string interface_name = passthrough_params_.tf_prefix + "trajectory_passthrough/"
                                                                               "abort";
            auto it = std::find_if(command_interfaces_.begin(), command_interfaces_.end(),
                                   [&](auto &interface)
                                   { return (interface.get_name() == interface_name); });
            if (it != command_interfaces_.end())
            {
                abort_command_interface_ = *it;
            }
            else
            {
                RCLCPP_ERROR(get_node()->get_logger(), "Did not find '%s' in command interfaces.", interface_name.c_str());
                return controller_interface::CallbackReturn::ERROR;
            }
        }

        {
            const std::string interface_name = passthrough_params_.tf_prefix + "trajectory_passthrough/transfer_state";
            auto it = std::find_if(command_interfaces_.begin(), command_interfaces_.end(),
                                   [&](auto &interface)
                                   { return (interface.get_name() == interface_name); });
            if (it != command_interfaces_.end())
            {
                transfer_command_interface_ = *it;
            }
            else
            {
                RCLCPP_ERROR(get_node()->get_logger(), "Did not find '%s' in command interfaces.", interface_name.c_str());
                return controller_interface::CallbackReturn::ERROR;
            }
        }

        {
            const std::string interface_name = passthrough_params_.tf_prefix + "trajectory_passthrough/vel";
            auto it = std::find_if(command_interfaces_.begin(), command_interfaces_.end(),
                                   [&](auto &interface)
                                   { return (interface.get_name() == interface_name); });
            if (it != command_interfaces_.end())
            {
                vel_ = *it;
            }
            else
            {
                RCLCPP_ERROR(get_node()->get_logger(), "Did not find '%s' in command interfaces.", interface_name.c_str());
                return controller_interface::CallbackReturn::ERROR;
            }
        }

        // 设置速度服务
        set_vel_service_ = get_node()->create_service<duco_msgs::srv::SetVel>(
            std::string(get_node()->get_name()) + "/set_vel", 
            std::bind(&PassthroughTrajectoryController::set_vel_service_callback, this, std::placeholders::_1, std::placeholders::_2));
        RCLCPP_INFO(get_node()->get_logger(), "set_vel service is ready");

        return ControllerInterface::on_activate(state);
    }

    controller_interface::CallbackReturn PassthroughTrajectoryController::on_deactivate(const rclcpp_lifecycle::State &)
    {
        try
        {
            abort_command_interface_->get().set_value(1.0);
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Could not write to abort command interface.");
            return controller_interface::CallbackReturn::ERROR;
        }
        if (trajectory_active_)
        {
            const auto active_goal = *rt_active_goal_.readFromRT();
            std::shared_ptr<control_msgs::action::FollowJointTrajectory::Result> result =
                std::make_shared<control_msgs::action::FollowJointTrajectory::Result>();
            result->set__error_string("Aborting current goal, since the controller is being deactivated.");
            active_goal->setAborted(result);
            rt_active_goal_.writeFromNonRT(RealtimeGoalHandlePtr());
            end_goal();
        }
        return CallbackReturn::SUCCESS;
    }

    controller_interface::return_type PassthroughTrajectoryController::update(const rclcpp::Time & /*time*/,
                                                                              const rclcpp::Duration & /*period*/)
    {
        const auto active_goal = *rt_active_goal_.readFromRT();

        const auto current_transfer_state = transfer_command_interface_->get().get_value();

        try
        {
            if (active_goal && trajectory_active_)
            {
                if (current_transfer_state != TRANSFER_STATE_IDLE)
                {
                    // Check if the trajectory has been aborted from the hardware interface. E.g. the robot was stopped on the teach
                    // pendant.
                    if (abort_command_interface_->get().get_value() == 1.0 && current_index_ > 0)
                    {
                        RCLCPP_INFO(get_node()->get_logger(), "Trajectory aborted by hardware, aborting action.");
                        std::shared_ptr<control_msgs::action::FollowJointTrajectory::Result> result =
                            std::make_shared<control_msgs::action::FollowJointTrajectory::Result>();
                        active_goal->setAborted(result);
                        end_goal();
                        return controller_interface::return_type::OK;
                    }
                }

                active_joint_traj_ = active_goal->gh_->get_goal()->trajectory;

                if (current_index_ == 0 && current_transfer_state == TRANSFER_STATE_IDLE)
                {
                    transfer_command_interface_->get().set_value(TRANSFER_STATE_WAITING_FOR_POINT);
                }
                auto joint_mapping = joint_trajectory_mapping_.readFromRT();

                // Write a new point to the command interface, if the previous point has been read by the hardware interface.
                if (current_transfer_state == TRANSFER_STATE_WAITING_FOR_POINT)
                {
                    if (current_index_ < active_joint_traj_.points.size())
                    {
                        // Write the positions for each joint of the robot
                        auto joint_names_internal = joint_names_.readFromRT();
                        // We've added the joint interfaces matching the order of the joint names so we can safely access
                        // them by the index.
                        for (size_t i = 0; i < number_of_joints_; i++)
                        {
                            command_interfaces_[i].set_value(
                                active_joint_traj_.points[current_index_].positions[joint_mapping->at(joint_names_internal->at(i))]);
                        }
                        // Tell hardware interface that this point is ready to be read.
                        transfer_command_interface_->get().set_value(TRANSFER_STATE_TRANSFERRING);
                        current_index_++;
                        // Check if all points have been written to the hardware interface.
                    }
                    else if (current_index_ == active_joint_traj_.points.size())
                    {
                        transfer_command_interface_->get().set_value(TRANSFER_STATE_TRANSFER_DONE);
                    }
                    else
                    {
                        RCLCPP_ERROR(get_node()->get_logger(), "Hardware waiting for trajectory point while none is present!");
                    }
                    // When the trajectory is finished, report the goal as successful to the client.
                }
                else if (current_transfer_state == TRANSFER_STATE_DONE)
                {
                    auto result = active_goal->preallocated_result_;
                    // Check if the actual position complies with the tolerances given.
                    if (!check_goal_tolerance())
                    {
                        result->error_code = control_msgs::action::FollowJointTrajectory::Result::GOAL_TOLERANCE_VIOLATED;
                        result->error_string = "Robot not within tolerances at end of trajectory.";
                        active_goal->setAborted(result);
                        end_goal();
                        RCLCPP_ERROR(get_node()->get_logger(), "Trajectory failed, goal tolerances not met.");
                    }
                    else
                    {
                        result->error_code = control_msgs::action::FollowJointTrajectory::Result::SUCCESSFUL;
                        result->error_string = "Trajectory succeeded";
                        active_goal->setSucceeded(result);
                        end_goal();
                        RCLCPP_INFO(get_node()->get_logger(), "%s", result->error_string.c_str());
                    }
                }
                else if (current_transfer_state == TRANSFER_STATE_IN_MOTION)
                {
                    // TODO: 运动过程中的处理逻辑：暂时不需要
                }
            }
            else if (current_transfer_state != TRANSFER_STATE_IDLE && current_transfer_state != TRANSFER_STATE_DONE)
            {
                // No goal is active, but we are not in IDLE, either. We have been canceled.
                abort_command_interface_->get().set_value(1.0);
            }
            else if (current_transfer_state == TRANSFER_STATE_DONE)
            {
                // We have been informed about the finished trajectory. Let's reset things.
                transfer_command_interface_->get().set_value(TRANSFER_STATE_IDLE);
                abort_command_interface_->get().set_value(0.0);
            }
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Exception thrown during update: %s", e.what());
            return controller_interface::return_type::ERROR;
        }

        return controller_interface::return_type::OK;
    }

    void PassthroughTrajectoryController::start_action_server(void)
    {
        send_trajectory_action_server_ = rclcpp_action::create_server<control_msgs::action::FollowJointTrajectory>(
            get_node(), std::string(get_node()->get_name()) + "/follow_joint_trajectory",
            std::bind(&PassthroughTrajectoryController::goal_received_callback, this, std::placeholders::_1,
                      std::placeholders::_2),
            std::bind(&PassthroughTrajectoryController::goal_cancelled_callback, this, std::placeholders::_1),
            std::bind(&PassthroughTrajectoryController::goal_accepted_callback, this, std::placeholders::_1));
        return;
    }

    rclcpp_action::GoalResponse PassthroughTrajectoryController::goal_received_callback(
        const rclcpp_action::GoalUUID & /*uuid*/,
        std::shared_ptr<const control_msgs::action::FollowJointTrajectory::Goal> goal)
    {
        RCLCPP_INFO(get_node()->get_logger(), "Received new trajectory.");

        if (trajectory_active_)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Can't accept new trajectory. A trajectory is already executing.");
            return rclcpp_action::GoalResponse::REJECT;
        }

        // Check that all parts of the trajectory are valid.
        if (!check_goal(goal))
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Trajectory rejected");
            return rclcpp_action::GoalResponse::REJECT;
        }

        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
    }

    bool PassthroughTrajectoryController::check_goal(
        std::shared_ptr<const control_msgs::action::FollowJointTrajectory::Goal> goal)
    {
        // 如果没有点，则返回false
        if (goal->trajectory.points.size() == 0)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "轨迹点数量必须至少有1个点");
            return false;
        }
        // 如果轨迹点数量小于3个,进行插补
        if (goal->trajectory.points.size() < 3)
        {
            RCLCPP_INFO(get_node()->get_logger(), "轨迹点数量少于3个,进行插补。当前点数: %zu",
                        goal->trajectory.points.size());

            // 创建新的轨迹点
            std::vector<trajectory_msgs::msg::JointTrajectoryPoint> new_points;

            // 如果只有1个点,在前后各插入一个相同的点
            if (goal->trajectory.points.size() == 1)
            {
                new_points.push_back(goal->trajectory.points[0]);
                new_points.push_back(goal->trajectory.points[0]);
                new_points.push_back(goal->trajectory.points[0]);
            }
            // 如果有2个点,在中间插入一个点
            else if (goal->trajectory.points.size() == 2)
            {
                new_points.push_back(goal->trajectory.points[0]);

                // 创建中间点
                trajectory_msgs::msg::JointTrajectoryPoint mid_point;
                mid_point.positions.resize(number_of_joints_);
                for (size_t j = 0; j < number_of_joints_; j++)
                {
                    mid_point.positions[j] = (goal->trajectory.points[0].positions[j] +
                                              goal->trajectory.points[1].positions[j]) /
                                             2.0;
                }

                new_points.push_back(mid_point);
                new_points.push_back(goal->trajectory.points[1]);
            }

            // 创建新的轨迹
            auto new_trajectory = goal->trajectory;
            new_trajectory.points = new_points;

            // 替换原轨迹
            const_cast<control_msgs::action::FollowJointTrajectory::Goal *>(goal.get())->trajectory = new_trajectory;

            RCLCPP_INFO(get_node()->get_logger(), "插补后的轨迹点数: %zu", goal->trajectory.points.size());
        }

        // 检查每个点的关节数是否正确
        for (uint32_t i = 0; i < goal->trajectory.points.size(); i++)
        {
            if (goal->trajectory.points[i].positions.size() != number_of_joints_)
            {
                std::string msg = "轨迹点关节数不正确。每个点必须包含所有关节位置 (" + std::to_string(number_of_joints_) + " 个关节)";
                RCLCPP_ERROR(get_node()->get_logger(), "%s", msg.c_str());
                msg = "第 " + std::to_string(i + 1) + " 个点包含 " + std::to_string(goal->trajectory.points[i].positions.size()) + " 个关节位置";
                RCLCPP_ERROR(get_node()->get_logger(), "%s", msg.c_str());
                return false;
            }
        }

        // 检查第一个点是否与当前关节位置相同
        for (size_t i = 0; i < number_of_joints_; i++) {
            if (std::abs(joint_position_state_interface_[i].get().get_value() - goal->trajectory.points[0].positions[i]) > 0.01) {
                RCLCPP_ERROR(get_node()->get_logger(), "当前关节位置与轨迹点位置不匹配: %f, %f", 
                    joint_position_state_interface_[i].get().get_value(), goal->trajectory.points[0].positions[i]);
                return false;
            }
        }
        
        return true;
    }

    rclcpp_action::CancelResponse PassthroughTrajectoryController::goal_cancelled_callback(
        const std::shared_ptr<rclcpp_action::ServerGoalHandle<control_msgs::action::FollowJointTrajectory>> goal_handle)
    {
        // Check that cancel request refers to currently active goal (if any)
        const auto active_goal = *rt_active_goal_.readFromNonRT();
        if (active_goal && active_goal->gh_ == goal_handle)
        {
            RCLCPP_INFO(get_node()->get_logger(), "Cancelling active trajectory requested.");

            // Mark the current goal as canceled
            auto result = std::make_shared<FollowJTrajAction::Result>();
            active_goal->setCanceled(result);
            rt_active_goal_.writeFromNonRT(RealtimeGoalHandlePtr());
            trajectory_active_ = false;
        }
        return rclcpp_action::CancelResponse::ACCEPT;
    }

    // Action goal was accepted, initialise values for a new trajectory.
    void PassthroughTrajectoryController::goal_accepted_callback(
        std::shared_ptr<rclcpp_action::ServerGoalHandle<control_msgs::action::FollowJointTrajectory>> goal_handle)
    {
        RCLCPP_INFO_STREAM(get_node()->get_logger(), "Accepted new trajectory with "
                                                         << goal_handle->get_goal()->trajectory.points.size() << " points.");
        current_index_ = 0;

        // TODO(fexner): Merge goal tolerances with default tolerances

        joint_trajectory_mapping_.writeFromNonRT(create_joint_mapping(goal_handle->get_goal()->trajectory.joint_names));

        // sort goal tolerances to match internal joint order
        std::vector<control_msgs::msg::JointTolerance> goal_tolerances;
        if (!goal_handle->get_goal()->goal_tolerance.empty())
        {
            auto joint_names_internal = joint_names_.readFromRT();
            std::stringstream ss;
            ss << "Using goal tolerances\n";
            for (auto &joint_name : *joint_names_internal)
            {
                auto found_it =
                    std::find_if(goal_handle->get_goal()->goal_tolerance.begin(), goal_handle->get_goal()->goal_tolerance.end(),
                                 [&joint_name](auto &tol)
                                 { return tol.name == joint_name; });
                if (found_it != goal_handle->get_goal()->goal_tolerance.end())
                {
                    goal_tolerances.push_back(*found_it);
                    ss << joint_name << " -- position: " << found_it->position << ", velocity: " << found_it->velocity
                       << ", acceleration: " << found_it->acceleration << std::endl;
                }
            }
            RCLCPP_INFO_STREAM(get_node()->get_logger(), ss.str());
        }
        goal_tolerance_.writeFromNonRT(goal_tolerances);

        // Action handling will be done from the timer callback to avoid those things in the realtime
        // thread. First, we delete the existing (if any) timer by resetting the pointer and then create a new
        // one.
        //
        RealtimeGoalHandlePtr rt_goal = std::make_shared<RealtimeGoalHandle>(goal_handle);
        rt_goal->execute();
        rt_active_goal_.writeFromNonRT(rt_goal);
        goal_handle_timer_.reset();
        goal_handle_timer_ = get_node()->create_wall_timer(action_monitor_period_.to_chrono<std::chrono::nanoseconds>(),
                                                           std::bind(&RealtimeGoalHandle::runNonRealtime, rt_goal));
        trajectory_active_ = true;
        return;
    }
    bool PassthroughTrajectoryController::check_goal_tolerance()
    {
        auto goal_tolerance = goal_tolerance_.readFromRT();
        auto joint_mapping = joint_trajectory_mapping_.readFromRT();
        auto joint_names_internal = joint_names_.readFromRT();
        if (goal_tolerance->empty())
        {
            return true;
        }

        for (size_t i = 0; i < number_of_joints_; ++i)
        {
            const std::string joint_name = joint_names_internal->at(i);
            const auto &joint_tol = goal_tolerance->at(i);
            const auto &setpoint = active_joint_traj_.points.back().positions[joint_mapping->at(joint_name)];
            const double joint_pos = joint_position_state_interface_[i].get().get_value();
            if (std::abs(joint_pos - setpoint) > joint_tol.position)
            {
                RCLCPP_ERROR(
                    get_node()->get_logger(), "Joint %s should be at position %f, but is at position %f, where tolerance is %f",
                    joint_position_state_interface_[i].get().get_name().c_str(), setpoint, joint_pos, joint_tol.position);
                return false;
            }
        }

        return true;
    }
    void PassthroughTrajectoryController::end_goal()
    {
        trajectory_active_ = false;
        try
        {
            transfer_command_interface_->get().set_value(TRANSFER_STATE_IDLE);
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(get_node()->get_logger(), "Could not write to transfer command interface.");
        }
    }

    std::unordered_map<std::string, size_t>
    PassthroughTrajectoryController::create_joint_mapping(const std::vector<std::string> &joint_names) const
    {
        std::unordered_map<std::string, size_t> joint_mapping;
        auto joint_names_internal = joint_names_.readFromNonRT();
        for (auto &joint_name : *joint_names_internal)
        {
            auto found_it = std::find(joint_names.begin(), joint_names.end(), joint_name);
            if (found_it != joint_names.end())
            {
                joint_mapping.insert({joint_name, found_it - joint_names.begin()});
            }
        }
        return joint_mapping;
    }

    bool PassthroughTrajectoryController::set_vel_service_callback(
        const std::shared_ptr<duco_msgs::srv::SetVel::Request> request,
        std::shared_ptr<duco_msgs::srv::SetVel::Response> response)
    {
        double vel = request->vel;
        // 检查速度值是否在有效范围内
        if (vel < 0.0 || vel > 3.14) {
            RCLCPP_WARN(
                get_node()->get_logger(), 
                "vel exceed the valid range 0.0~3.14, set vel to 0.1");
            vel = 0.1;
        }
        vel_->get().set_value(vel);
        RCLCPP_INFO(get_node()->get_logger(), "set vel to %f", vel);
        response->success = true;
        return true;
    }
} // namespace duco_controller
#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(duco_controller::PassthroughTrajectoryController, controller_interface::ControllerInterface)