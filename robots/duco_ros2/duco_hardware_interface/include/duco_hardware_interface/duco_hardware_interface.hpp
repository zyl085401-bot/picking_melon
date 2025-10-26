#ifndef DUCO_HARDWARE_INTERFACE__DUCO_HARDWARE_INTERFACE_HPP_
#define DUCO_HARDWARE_INTERFACE__DUCO_HARDWARE_INTERFACE_HPP_

#include <string>
#include <vector>
#include <mutex>
#include <cmath>

// ros2_control hardware_interface
#include "duco_hardware_interface/visibility_control.h"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

// ROS
#include "rclcpp/rclcpp.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

// Duco API
#include "duco_driver/DucoCobot.h"

namespace duco_hardware_interface
{
    /*
     * 0.0: 没有轨迹需要转发，控制器处于空闲状态，可以接收新的轨迹。
     * 1.0: 控制器已接收并接受了新的轨迹。当状态为1.0时，控制器将向硬件接口写入一个轨迹点。
     * 2.0: 硬件接口将读取控制器写入的轨迹点。状态将在1.0和2.0之间切换，直到硬件接口读取完所有轨迹点。
     * 3.0: 硬件接口已读取所有轨迹点，现在将所有点写入物理机器人控制器。
     * 4.0: 机器人正在执行轨迹运动。
     * 5.0: 机器人完成轨迹执行。
     */
    const double TRANSFER_STATE_IDLE = 0.0;
    const double TRANSFER_STATE_WAITING_FOR_POINT = 1.0;
    const double TRANSFER_STATE_TRANSFERRING = 2.0;
    const double TRANSFER_STATE_TRANSFER_DONE = 3.0;
    const double TRANSFER_STATE_IN_MOTION = 4.0;
    const double TRANSFER_STATE_DONE = 5.0;

    struct TaskStateInfo
    {
        const char *message;
        bool is_error;
    };

    static const std::map<int, TaskStateInfo> task_state_map = {
        {0, {"task idle", false}},
        {1, {"task running", false}},
        {2, {"task paused", true}},
        {3, {"task stopped", true}},
        {4, {"task completed", false}},
        {5, {"task interrupt", true}},
        {6, {"task error", true}},
        {7, {"task illegal", true}},
        {8, {"task parameter mismatch", true}}};

    class DucoHardwareInterface : public hardware_interface::SystemInterface
    {
    public:
        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::CallbackReturn on_init(
            const hardware_interface::HardwareInfo &info) override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::CallbackReturn on_configure(
            const rclcpp_lifecycle::State &previous_state) override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::CallbackReturn on_activate(
            const rclcpp_lifecycle::State &previous_state) override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::CallbackReturn on_deactivate(
            const rclcpp_lifecycle::State &previous_state) override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::return_type read(
            const rclcpp::Time &time, const rclcpp::Duration &period) override;

        TEMPLATES__ROS2_CONTROL__VISIBILITY_PUBLIC
        hardware_interface::return_type write(
            const rclcpp::Time &time, const rclcpp::Duration &period) override;

    private:
        std::string robot_ip_;
        std::shared_ptr<DucoRPC::DucoCobot> duco_cobot_;

        bool onActive();
        bool onDeactive();
        void readJointState();
        void check_passthrough_trajectory_controller();

        // Joint state interface values
        std::vector<double> duco_joint_positions_;
        std::vector<double> duco_joint_velocities_;
        std::vector<double> duco_joint_efforts_;

        // Passthrough trajectory controller interface values
        double passthrough_trajectory_transfer_state_;
        double passthrough_trajectory_abort_;
        double vel_;
        std::vector<double> passthrough_point_positions_;
        std::vector<std::vector<double>> passthrough_trajectory_positions_;
        int32_t trackJointMotionID_;

        const std::string PASSTHROUGH_GPIO = "trajectory_passthrough";
    };

} // namespace duco_hardware_interface

#endif // DUCO_HARDWARE_INTERFACE__DUCO_HARDWARE_INTERFACE_HPP_
