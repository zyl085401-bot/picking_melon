/**
 * 游戏手柄控制底盘、升降、手抓、云台
 */
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <std_msgs/msg/string.hpp>

class JoyControl : public rclcpp::Node
{
public:
    /**
     * @brief: 类构建函数，获取ROS参数，创建订阅者和发布者
     * @return {*}
     */
    JoyControl() : Node("joy_control")
    {
        this->declare_parameter("use_stamp_vel", true);
        this->declare_parameter("AXIS_FORWARD_BACKWARD", 5);
        this->declare_parameter("AXIS_LEFT_RIGHT", 4);
        this->declare_parameter("KEY_TURN_LEFT", 3);
        this->declare_parameter("KEY_TURN_RIGHT", 1);
        this->declare_parameter("KEY_SPEED_UP", 6);

        this->declare_parameter("KEY_PANTILT_ON", 4);
        this->declare_parameter("KEY_PAN_LEFT", 0);
        this->declare_parameter("KEY_PAN_RIGHT", 2);
        this->declare_parameter("KEY_TILT_UP", 3);
        this->declare_parameter("KEY_TILT_DOWN", 1);
        this->declare_parameter("AXIS_EV_UP_DOWN", 5);

        this->declare_parameter("KEY_STOP_PRESS", 7);
        this->declare_parameter("KEY_STOP_RELEASE", 5);
        this->declare_parameter("KEY_PAW_OPEN", 8);
        this->declare_parameter("KEY_PAW_CLOSE", 9);

        this->declare_parameter("low_vel_x", 0.3);
        this->declare_parameter("high_vel_x", 0.5);
        this->declare_parameter("low_vel_y", 0.3);
        this->declare_parameter("high_vel_y", 0.5);
        this->declare_parameter("low_vel_yaw", 0.3);
        this->declare_parameter("high_vel_yaw", 0.8);
        this->declare_parameter("pantilt_increment", 5.0);
        this->declare_parameter("ev_increment_", 0.03);

        this->get_parameter("AXIS_FORWARD_BACKWARD", AXIS_FORWARD_BACKWARD);
        this->get_parameter("AXIS_LEFT_RIGHT", AXIS_LEFT_RIGHT);
        this->get_parameter("KEY_TURN_LEFT", KEY_TURN_LEFT);
        this->get_parameter("KEY_TURN_RIGHT", KEY_TURN_RIGHT);
        this->get_parameter("KEY_SPEED_UP", KEY_SPEED_UP);

        this->get_parameter("KEY_PANTILT_ON", KEY_PANTILT_ON);
        this->get_parameter("KEY_PAN_LEFT", KEY_PAN_LEFT);
        this->get_parameter("KEY_PAN_RIGHT", KEY_PAN_RIGHT);
        this->get_parameter("KEY_TILT_UP", KEY_TILT_UP);
        this->get_parameter("KEY_TILT_DOWN", KEY_TILT_DOWN);
        this->get_parameter("AXIS_EV_UP_DOWN", AXIS_EV_UP_DOWN);

        this->get_parameter("KEY_STOP_PRESS", KEY_STOP_PRESS);
        this->get_parameter("KEY_STOP_RELEASE", KEY_STOP_RELEASE);
        this->get_parameter("KEY_PAW_OPEN", KEY_PAW_OPEN);
        this->get_parameter("KEY_PAW_CLOSE", KEY_PAW_CLOSE);

        this->get_parameter("low_vel_x", low_vel_x_);
        this->get_parameter("high_vel_x", high_vel_x_);
        this->get_parameter("low_vel_y", low_vel_y_);
        this->get_parameter("high_vel_y", high_vel_y_);
        this->get_parameter("low_vel_yaw", low_vel_yaw_);
        this->get_parameter("high_vel_yaw", high_vel_yaw_);
        this->get_parameter("pantilt_increment", pantilt_increment_);
        this->get_parameter("ev_increment_", ev_increment_);
        this->get_parameter("use_stamp_vel", use_stamp_vel_);
        if (use_stamp_vel_)
        {
            vel_stamp_pub_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/cmd_vel_joy", 1);       // 发布底盘速度
        }
        else
        {
            vel_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel_joy", 1);       // 发布底盘速度
        }
        cmd_pub_ = this->create_publisher<std_msgs::msg::String>("/motor_manager_cmd", 2); // 驱动命令
        Nstop = 0;
        // 订阅手柄信息
        joy_sub_ = create_subscription<sensor_msgs::msg::Joy>("/joy", 1, std::bind(&JoyControl::joySubCallback, this, std::placeholders::_1));
    }

private:
    int AXIS_FORWARD_BACKWARD;
    int AXIS_LEFT_RIGHT;
    int KEY_TURN_LEFT;
    int KEY_TURN_RIGHT;
    int KEY_SPEED_UP;

    int KEY_PANTILT_ON;
    int KEY_PAN_LEFT;
    int KEY_PAN_RIGHT;
    int KEY_TILT_UP;
    int KEY_TILT_DOWN;
    int AXIS_EV_UP_DOWN;

    int KEY_STOP_PRESS;
    int KEY_STOP_RELEASE;
    int KEY_PAW_OPEN;
    int KEY_PAW_CLOSE;

    double low_vel_x_;
    double high_vel_x_;
    double low_vel_yaw_;
    double high_vel_yaw_;
    double low_vel_y_;
    double high_vel_y_;
    double pantilt_increment_;
    double ev_increment_;
    bool   use_stamp_vel_;

    int Nstop;

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr vel_pub_;
    rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr vel_stamp_pub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr cmd_pub_;
    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;

    /**
     * @brief: 将手柄信息转换为底盘速度
     * @param {SharedPtr} msg 手柄信息
     * @param {Twist} &cmd_vel 底盘速度
     * @return {*}
     */
    void toBaseSpeed(const sensor_msgs::msg::Joy::SharedPtr msg, geometry_msgs::msg::Twist &cmd_vel)
    {
        bool speedup = false;
        if (msg->buttons[KEY_SPEED_UP] == 1)
            speedup = true; // 高速度

        if (msg->buttons[KEY_TURN_LEFT] == 1)
        {
            if (speedup)
                cmd_vel.angular.z += high_vel_yaw_;
            else
                cmd_vel.angular.z += low_vel_yaw_;
        }
        if (msg->buttons[KEY_TURN_RIGHT] == 1)
        {
            if (speedup)
                cmd_vel.angular.z -= high_vel_yaw_;
            else
                cmd_vel.angular.z -= low_vel_yaw_;
        }

        int temp = judgeKey(msg->axes[AXIS_FORWARD_BACKWARD]);
        if (temp == 1)
        {
            if (speedup)
                cmd_vel.linear.x += high_vel_x_;
            else
                cmd_vel.linear.x += low_vel_x_;
        }
        else if (temp == -1)
        {
            if (speedup)
                cmd_vel.linear.x -= high_vel_x_;
            else
                cmd_vel.linear.x -= low_vel_x_;
        }

        temp = judgeKey(msg->axes[AXIS_LEFT_RIGHT]);
        if (temp == 1)
        {
            if (speedup)
                cmd_vel.linear.y += high_vel_y_;
            else
                cmd_vel.linear.y += low_vel_y_;
        }
        else if (temp == -1)
        {
            if (speedup)
                cmd_vel.linear.y -= high_vel_y_;
            else
                cmd_vel.linear.y -= low_vel_y_;
        }
    }

    /**
     * @brief: 将手柄信息转换为tile/pan运动命令
     * @param {SharedPtr} msg 手柄信息
     * @param {String} &cmd 运动命令
     * @return {*}
     */
    void toPanTiltCmd(const sensor_msgs::msg::Joy::SharedPtr msg, std_msgs::msg::String &cmd)

    {
        std::string incre = std::to_string(pantilt_increment_);

        if (msg->buttons[KEY_PAN_LEFT] == 1)
            cmd.data = "add pan " + incre;
        else if (msg->buttons[KEY_PAN_RIGHT] == 1)
            cmd.data = "add pan -" + incre;
        if (msg->buttons[KEY_TILT_UP] == 1)
            cmd.data = "add tilt " + incre;
        else if (msg->buttons[KEY_TILT_DOWN] == 1)
            cmd.data = "add tilt -" + incre;
    }

    /**
     * @brief: 手柄信息转换为手抓运动
     * @param {SharedPtr} msg 手柄信息
     * @param {String} &cmd 运动命令
     * @return {*}
     */
    void toPawCmd(const sensor_msgs::msg::Joy::SharedPtr msg, std_msgs::msg::String &cmd)
    {
        if (msg->buttons[KEY_PAW_OPEN] == 1)
        {
            cmd.data = "open paw";
        }
        else if (msg->buttons[KEY_PAW_CLOSE] == 1)
        {
            cmd.data = "close paw";
        }
    }

    /**
     * @brief: 发布速度消息
     * @param {Twist} twist 速度信息
     * @return {*}
     */
    void publishVelCmd(const geometry_msgs::msg::Twist &twist)
    {
        if (use_stamp_vel_)
        {
            geometry_msgs::msg::TwistStamped cmd_vel;
            cmd_vel.twist = twist;
            vel_stamp_pub_->publish(cmd_vel);
        }
        else
        {
            vel_pub_->publish(twist);
        }
    }

    /**
     * @brief: 手柄信息回调函数，内部处理手柄转运动信息
     * @param {SharedPtr} msg 手柄信息
     * @return {*}
     */
    void joySubCallback(const sensor_msgs::msg::Joy::SharedPtr msg)
    {
        std_msgs::msg::String cmd;
        // 急停开关
        if (msg->buttons[KEY_STOP_RELEASE] == 1 || msg->buttons[KEY_STOP_PRESS] == 1)
        {
            cmd.data = "stop " + std::to_string(msg->buttons[KEY_STOP_PRESS]);
            cmd_pub_->publish(cmd);
            return;
        }
        // 手抓闭合
        if (msg->buttons[KEY_PAW_OPEN] == 1 || msg->buttons[KEY_PAW_CLOSE] == 1)
        {
            if (msg->buttons[KEY_PAW_OPEN] == 1)
                cmd.data = "open paw";
            else
                cmd.data = "close paw";
            cmd_pub_->publish(cmd);
        }
        // 升降移动
        else if (msg->axes[AXIS_EV_UP_DOWN] == 1 || msg->axes[AXIS_EV_UP_DOWN] == -1)
        {
            cmd.data = "add ev " + std::to_string(msg->axes[AXIS_EV_UP_DOWN] * ev_increment_);
            cmd_pub_->publish(cmd);
        }
        // 云台移动
        else if (msg->buttons[KEY_PANTILT_ON] == 1)
        {
            toPanTiltCmd(msg, cmd);
            if (cmd.data != "")
                cmd_pub_->publish(cmd);
        }
        else // 底盘移动
        {
            geometry_msgs::msg::Twist twist;
            toBaseSpeed(msg, twist);
            if (twist.linear.x == 0 && twist.angular.z == 0)
            {
                if (Nstop < 5)
                {
                    ++Nstop;
                    publishVelCmd(twist);
                }
            }
            else
            {
                Nstop = 0;
                publishVelCmd(twist);
            }
        }
    }

    /**
     * @brief: 速度方向化
     * @param {double} &vel 速度
     * @return {*}
     */
    int judgeKey(const double &vel)
    {
        if (vel >= 0.01)
            return 1;
        else if (vel <= -0.01)
            return -1;
        else
            return 0;
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<JoyControl>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
