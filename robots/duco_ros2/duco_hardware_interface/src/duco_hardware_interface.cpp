#include "duco_hardware_interface/duco_hardware_interface.hpp"

namespace duco_hardware_interface
{
  hardware_interface::CallbackReturn DucoHardwareInterface::on_init(
      const hardware_interface::HardwareInfo &info)
  {
    if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
    {
      return CallbackReturn::ERROR;
    }

    for (const hardware_interface::ComponentInfo &joint : info_.joints)
    {
      if (joint.state_interfaces.size() != 3)
      {
        RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                     "Joint '%s' has %zu state interface. 3 expected.",
                     joint.name.c_str(), joint.state_interfaces.size());
        return hardware_interface::CallbackReturn::ERROR;
      }

      // state_interfaces: HW_IF_POSITION
      if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
      {
        RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                     "Joint '%s' have %s state interface. '%s' expected.",
                     joint.name.c_str(),
                     joint.state_interfaces[0].name.c_str(),
                     hardware_interface::HW_IF_POSITION);
        return hardware_interface::CallbackReturn::ERROR;
      }

      // state_interfaces: HW_IF_VELOCITY
      if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY)
      {
        RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                     "Joint '%s' have %s state interface. '%s' expected.",
                     joint.name.c_str(),
                     joint.state_interfaces[1].name.c_str(),
                     hardware_interface::HW_IF_VELOCITY);
        return hardware_interface::CallbackReturn::ERROR;
      }
      // state_interfaces: HW_IF_EFFORT
      if (joint.state_interfaces[2].name != hardware_interface::HW_IF_EFFORT)
      {
        RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                     "Joint '%s' have %s state interface. '%s' expected.",
                     joint.name.c_str(),
                     joint.state_interfaces[2].name.c_str(),
                     hardware_interface::HW_IF_EFFORT);
        return hardware_interface::CallbackReturn::ERROR;
      }
    }

    // GPIOs配置检查
    if (info_.gpios.size() != 1)
    {
      RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                   "Duco cobot has %zu gpios found. 1 expected.", info_.gpios.size());
      return hardware_interface::CallbackReturn::ERROR;
    }
    for (const hardware_interface::ComponentInfo &gpio : info_.gpios)
    {
      // command_interfaces size
      if (gpio.command_interfaces.size() != 9)
      {
        RCLCPP_FATAL(rclcpp::get_logger("DucoHardwareInterface"),
                     "GPIO '%s' has %zu command interfaces found. 9 expected.", gpio.name.c_str(),
                     gpio.command_interfaces.size());
        return hardware_interface::CallbackReturn::ERROR;
      }
    }

    duco_joint_positions_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
    duco_joint_velocities_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());
    duco_joint_efforts_.resize(info_.joints.size(), std::numeric_limits<double>::quiet_NaN());

    passthrough_trajectory_transfer_state_ = 0.0;
    passthrough_trajectory_abort_ = 0.0;
    passthrough_point_positions_.resize(6, std::numeric_limits<double>::quiet_NaN());
    passthrough_trajectory_positions_.clear();
    trackJointMotionID_ = -1;
    vel_ = 0.5;

    return CallbackReturn::SUCCESS;
  }

  hardware_interface::CallbackReturn DucoHardwareInterface::on_configure(
      const rclcpp_lifecycle::State & /*previous_state*/)
  {
    // TODO(anyone): prepare the robot to be ready for read calls and write calls of some interfaces
    return CallbackReturn::SUCCESS;
  }

  std::vector<hardware_interface::StateInterface> DucoHardwareInterface::export_state_interfaces()
  {
    std::vector<hardware_interface::StateInterface> state_interfaces;
    for (size_t i = 0; i < info_.joints.size(); ++i)
    {
      state_interfaces.emplace_back(hardware_interface::StateInterface(
          info_.joints[i].name, hardware_interface::HW_IF_POSITION, &duco_joint_positions_[i]));
      state_interfaces.emplace_back(hardware_interface::StateInterface(
          info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &duco_joint_velocities_[i]));
      state_interfaces.emplace_back(hardware_interface::StateInterface(
          info_.joints[i].name, hardware_interface::HW_IF_EFFORT, &duco_joint_efforts_[i]));
    }
    return state_interfaces;
  }

  std::vector<hardware_interface::CommandInterface> DucoHardwareInterface::export_command_interfaces()
  {
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    for (size_t i = 0; i < 6; ++i)
    {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
          info_.gpios[0].name, "setpoint_positions_" + std::to_string(i), &passthrough_point_positions_[i]));
    }
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
        info_.gpios[0].name, "transfer_state", &passthrough_trajectory_transfer_state_));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
        info_.gpios[0].name, "abort", &passthrough_trajectory_abort_));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
        info_.gpios[0].name, "vel", &vel_));
    return command_interfaces;
  }

  hardware_interface::CallbackReturn DucoHardwareInterface::on_activate(
      const rclcpp_lifecycle::State & /*previous_state*/)
  {
    // prepare the robot to receive commands
    RCLCPP_INFO(rclcpp::get_logger("DucoHardwareInterface"), "Activating duco robot, please waiting...");
    onActive();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    readJointState();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    return CallbackReturn::SUCCESS;
  }

  hardware_interface::CallbackReturn DucoHardwareInterface::on_deactivate(
      const rclcpp_lifecycle::State & /*previous_state*/)
  {
    // prepare the robot to stop receiving commands
    onDeactive();
    return CallbackReturn::SUCCESS;
  }

  hardware_interface::return_type DucoHardwareInterface::read(
      const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
  {
    readJointState();
    return hardware_interface::return_type::OK;
  }

  hardware_interface::return_type DucoHardwareInterface::write(
      const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
  {
    check_passthrough_trajectory_controller();
    return hardware_interface::return_type::OK;
  }

  bool DucoHardwareInterface::onActive()
  {
    const std::string robot_ip = info_.hardware_parameters["robot_ip"];
    const int retry_interval_ms = 10000;  // 重试间隔改为10秒
    int retry_count = 0;
    
    while (true)
    {
      try
      {
        RCLCPP_INFO(rclcpp::get_logger("DucoHardwareInterface"), 
          "Attempting to connect to robot at %s:%d (attempt %d)...", 
          robot_ip.c_str(), 7003, retry_count + 1);
        
        duco_cobot_ = std::make_shared<DucoRPC::DucoCobot>(robot_ip, 7003);
        duco_cobot_->open();
        duco_cobot_->power_on(true);
        duco_cobot_->enable(true);
        
        // 测试连接是否真正可用
        std::vector<double> actual_joints_position;
        duco_cobot_->get_actual_joints_position(actual_joints_position);
        
        // 连接成功，执行初始化操作
        // fixed 新松轨迹池Bug，第一次上电使能跑轨迹池的时候，不会动
        duco_cobot_->trackClearQueue();
        std::vector<std::vector<double>> trajectory;
        trajectory.emplace_back(actual_joints_position);
        trajectory.emplace_back(actual_joints_position);
        trajectory.emplace_back(actual_joints_position);
        duco_cobot_->trackEnqueue(trajectory, true);
        duco_cobot_->trackJointMotion(0.1, 1.0, true);
        duco_cobot_->trackClearQueue();
        
        RCLCPP_INFO(rclcpp::get_logger("DucoHardwareInterface"), 
          "Successfully connected to robot");
        return true;
      }
      catch (const std::exception& e)
      {
        RCLCPP_WARN(rclcpp::get_logger("DucoHardwareInterface"), 
          "Connection attempt failed: %s", e.what());
        
        if (duco_cobot_)
        {
          try
          {
            duco_cobot_->close();
          }
          catch (...) {}
          duco_cobot_.reset();
        }
        
        retry_count++;
        RCLCPP_INFO(rclcpp::get_logger("DucoHardwareInterface"), 
          "Waiting %d seconds before next attempt...", retry_interval_ms/1000);
        std::this_thread::sleep_for(std::chrono::milliseconds(retry_interval_ms));
      }
    }
    return false;
  }

  bool DucoHardwareInterface::onDeactive()
  {
    // duco_cobot_->disable(true);
    // duco_cobot_->power_off(true);
    // duco_cobot_->close();
    // RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "Duco cobot disconnected.");
    return true;
  }

  void DucoHardwareInterface::readJointState()
  {
    std::vector<double> actual_joints_position, actual_joints_velocity, actual_joints_effort;
    duco_cobot_->get_actual_joints_position(actual_joints_position);
    duco_cobot_->get_actual_joints_speed(actual_joints_velocity);
    duco_cobot_->get_actual_joints_acceleration(actual_joints_effort);

    {
      for (std::size_t i = 0; i < duco_joint_positions_.size(); i++)
      {
        duco_joint_positions_[i] = actual_joints_position[i];
        duco_joint_velocities_[i] = actual_joints_velocity[i];
        duco_joint_efforts_[i] = actual_joints_effort[i];
      }
    }
  }

  void DucoHardwareInterface::check_passthrough_trajectory_controller()
  {
    // 收到轨迹停止请求，且当前不处于idel状态
    if (passthrough_trajectory_abort_ == 1.0 && passthrough_trajectory_transfer_state_ != TRANSFER_STATE_IDLE)
    {
      duco_cobot_->trackClearQueue();
      passthrough_trajectory_abort_ = 0.0;
      passthrough_trajectory_positions_.clear();
      trackJointMotionID_ = -1;
      RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "Trajectory aborted.");
    }
    // 轨迹已经准备好，等待发送
    else if (passthrough_trajectory_transfer_state_ == TRANSFER_STATE_TRANSFERRING)
    {
      passthrough_trajectory_abort_ = 0.0;
      passthrough_trajectory_positions_.emplace_back(passthrough_point_positions_);
      passthrough_trajectory_transfer_state_ = TRANSFER_STATE_WAITING_FOR_POINT;

      RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"),
                         "Received point " << passthrough_trajectory_positions_.size() << " : "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[0] * 180.0 / M_PI << "° "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[1] * 180.0 / M_PI << "° "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[2] * 180.0 / M_PI << "° "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[3] * 180.0 / M_PI << "° "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[4] * 180.0 / M_PI << "° "
                                           << std::fixed << std::setprecision(4) << passthrough_point_positions_[5] * 180.0 / M_PI << "°");
    }
    // 轨迹已经发送完毕，启动执行
    else if (passthrough_trajectory_transfer_state_ == 3.0)
    {

      // 打印轨迹点信息
      RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"),
                         "Sending trajectory with " << passthrough_trajectory_positions_.size() << " points");
      duco_cobot_->trackClearQueue();
      duco_cobot_->trackEnqueue(passthrough_trajectory_positions_, true);

      double acc = vel_ * 10.0;
      RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "trackEnqueue size: " << duco_cobot_->getQueueSize() << ", vel: " << vel_ << ", acc: " << acc);
      trackJointMotionID_ = duco_cobot_->trackJointMotion(vel_, acc, false);
      if (trackJointMotionID_ == -1) {
        passthrough_trajectory_abort_ = 1.0;
        passthrough_trajectory_transfer_state_ = 5.0;
        RCLCPP_ERROR_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "trackJointMotion failed");
        return;
      }

      passthrough_trajectory_positions_.clear();
      passthrough_trajectory_abort_ = 0.0;
      passthrough_trajectory_transfer_state_ = 4.0;
      RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "Start executing trajectory.");
    }
    // 轨迹正在执行中
    else if (passthrough_trajectory_transfer_state_ == 4.0)
    {
      // 检查轨迹是否执行完毕
      int32_t task_state = duco_cobot_->get_noneblock_taskstate(trackJointMotionID_);

      auto it = task_state_map.find(task_state);
      if (it != task_state_map.end()) {
        const auto& info = it->second;
        
        if (task_state == 0 || task_state == 1) {
          RCLCPP_INFO_STREAM_ONCE(rclcpp::get_logger("DucoHardwareInterface"), 
              "Trajectory " << info.message << ": " << task_state);
        }

        if (info.is_error) {
          duco_cobot_->trackClearQueue();
          duco_cobot_->stop(true);
          std::vector<std::string> last_error;
          duco_cobot_->get_last_error(last_error);
          passthrough_trajectory_abort_ = 1.0;
          passthrough_trajectory_transfer_state_ = 5.0;
          RCLCPP_ERROR_STREAM(rclcpp::get_logger("DucoHardwareInterface"), 
              "Trajectory failed, " << info.message << ": " << task_state << ", " << last_error[0]);
        }

        if (task_state == 4)
        {
          passthrough_trajectory_abort_ = 0.0;
          passthrough_trajectory_transfer_state_ = 5.0;
          RCLCPP_INFO_STREAM_ONCE(rclcpp::get_logger("DucoHardwareInterface"), 
              "Trajectory executing: " << task_state);
          RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), 
              "Trajectory done.");
        }
      }

      // 打印实时关节角度值
      // std::vector<double> actual_joints_position;
      // duco_cobot_->get_actual_joints_position(actual_joints_position);
      // RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "actual joint angles: " << std::fixed << std::setprecision(4)
      //   << actual_joints_position[0] * 180.0 / M_PI << "° "
      //   << actual_joints_position[1] * 180.0 / M_PI << "° "
      //   << actual_joints_position[2] * 180.0 / M_PI << "° "
      //   << actual_joints_position[3] * 180.0 / M_PI << "° "
      //   << actual_joints_position[4] * 180.0 / M_PI << "° "
      //   << actual_joints_position[5] * 180.0 / M_PI << "°");
      
      // std::vector<double> target_joints_position;
      // duco_cobot_->get_target_joints_position(target_joints_position);
      // RCLCPP_INFO_STREAM(rclcpp::get_logger("DucoHardwareInterface"), "target joint angles: " << std::fixed << std::setprecision(4)
      //   << target_joints_position[0] * 180.0 / M_PI << "° "
      //   << target_joints_position[1] * 180.0 / M_PI << "° "
      //   << target_joints_position[2] * 180.0 / M_PI << "° "
      //   << target_joints_position[3] * 180.0 / M_PI << "° "
      //   << target_joints_position[4] * 180.0 / M_PI << "° "
      //   << target_joints_position[5] * 180.0 / M_PI << "°");
    }
  }

} // namespace duco_hardware_interface

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(
    duco_hardware_interface::DucoHardwareInterface, hardware_interface::SystemInterface)
