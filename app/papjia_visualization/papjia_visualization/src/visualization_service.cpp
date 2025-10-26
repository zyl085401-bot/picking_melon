#include <rclcpp/rclcpp.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <geometry_msgs/msg/point.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <papjia_visualization_interface/srv/visualization.hpp>
#include <cmath>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>
#include <papjia_visualization/parse_json.hpp>

namespace papjia_visualization
{
    class VisualizationService : public rclcpp::Node
    {
    public:
        VisualizationService()
            : Node("visualization_service")
        {
            // 声明服务topic
            this->declare_parameter<std::string>("service_topic", "visualization_service");
            // 声明marker话题
            this->declare_parameter<std::string>("marker_topic", "/visualization/markers");
            // 获取服务topic
            this->get_parameter("service_topic", service_topic_);
            // 获取marker话题
            this->get_parameter("marker_topic", markers_topic_);
            // 创建服务
            service_ = this->create_service<papjia_visualization_interface::srv::Visualization>(
                service_topic_,
                std::bind(
                    &VisualizationService::visualize_callback,
                    this,
                    std::placeholders::_1,
                    std::placeholders::_2));

            // 创建发布者
            marker_pub_ = this->create_publisher<visualization_msgs::msg::MarkerArray>(markers_topic_, 10);
            RCLCPP_INFO(this->get_logger(), "可视化服务已启动");
        }

        void visualize_callback(
            const std::shared_ptr<papjia_visualization_interface::srv::Visualization::Request> request,
            const std::shared_ptr<papjia_visualization_interface::srv::Visualization::Response> response)
        {
            try
            {
                RCLCPP_INFO(this->get_logger(), "收到可视化请求");
                // 解析请求，解析json字符串
                nlohmann::json data = nlohmann::json::parse(request->data);
                std::string type, action;
                if (!data.contains("type") || !data["type"].is_string())
                {
                    throw std::runtime_error("Missing type field");
                }
                type = data["type"].get<std::string>();
                if (!data.contains("action") || !data["action"].is_string())
                {
                    throw std::runtime_error("Missing action field");
                }
                action = data["action"].get<std::string>();
                RCLCPP_INFO(this->get_logger(), "type: %s, action: %s", type.c_str(), action.c_str());

                visualization_msgs::msg::MarkerArray marker_array_;

                if (type == "path")
                {
                    parse_path(data["data"], marker_array_.markers);
                }

                marker_pub_->publish(marker_array_);
                // 响应
                response->success = true;
                response->message = "可视化成功";
            }
            catch (const std::exception &e)
            {
                RCLCPP_ERROR(this->get_logger(), "可视化失败: %s", e.what());
                response->success = false;
                response->message = std::string(e.what());
            }
        }

    private:
        std::string service_topic_;
        std::string markers_topic_;
        rclcpp::Service<papjia_visualization_interface::srv::Visualization>::SharedPtr service_;
        rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
    };
} // namespace papjia_visualization

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<papjia_visualization::VisualizationService>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}