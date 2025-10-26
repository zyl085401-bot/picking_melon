#ifndef PAPJIA_VISUALIZATION__PARSE_JSON_HPP
#define PAPJIA_VISUALIZATION__PARSE_JSON_HPP

#include <string>
#include <vector>
#include <map>
#include <nlohmann/json.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <papjia_visualization/utils.hpp>
#include <rclcpp/clock.hpp>
#include <papjia_visualization/utils.hpp>

namespace papjia_visualization
{
    void parse_path(const nlohmann::json &data, std::vector<visualization_msgs::msg::Marker> &markers)
    {
        std::vector<double> start_pose;
        if (data.contains("start") && data["start"].is_array())
        {
            start_pose = data["start"].get<std::vector<double>>();
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("parse_path"), "start is not provided");
            return;
        }
        std::vector<double> end_pose;
        if (data.contains("end") && data["end"].is_array())
        {
            end_pose = data["end"].get<std::vector<double>>();
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("parse_path"), "end is not provided");
            return;
        }
        std::string ns = "line";
        if (data.contains("ns") && data["ns"].is_string())
        {
            ns = data["ns"].get<std::string>();
        }
        std::string frame_id = "map";
        if (data.contains("frame_id") && data["frame_id"].is_string())
        {
            frame_id = data["frame_id"].get<std::string>();
        }
        int64_t id = 0;
        if (data.contains("id") && data["id"].is_number_integer())
        {
            id = data["id"].get<int64_t>();
        }
        std::vector<double> rgba = {1.0, 0.0, 0.0, 1.0};
        if (data.contains("color") && data["color"].is_array())
        {
            rgba = data["color"].get<std::vector<double>>();
        }
        std::vector<double> scale = {0.05, 0.05, 0.05};
        if (data.contains("scale") && data["scale"].is_array())
        {
            scale = data["scale"].get<std::vector<double>>();
        }

        // 解析起点和终点
        geometry_msgs::msg::Point start_pos, end_pos;
        geometry_msgs::msg::Quaternion start_quat, end_quat;

        parse_pose(start_pose, start_pos, start_quat);
        parse_pose(end_pose, end_pos, end_quat);

        std_msgs::msg::Header header;
        header.frame_id = frame_id;
        header.stamp = rclcpp::Clock().now();

        visualization_msgs::msg::Marker line_marker;
        line_marker.header = header;
        line_marker.ns = ns;
        line_marker.id = id;
        line_marker.type = visualization_msgs::msg::Marker::LINE_STRIP;
        line_marker.action = visualization_msgs::msg::Marker::ADD;
        line_marker.scale.x = scale[0]; // 线宽
        line_marker.color.r = rgba[0];
        line_marker.color.g = rgba[1];
        line_marker.color.b = rgba[2];
        line_marker.color.a = rgba[3];
        line_marker.points.push_back(start_pos);
        line_marker.points.push_back(end_pos);

        markers.push_back(line_marker);

        visualization_msgs::msg::Marker points_marker;
        points_marker.header = header;
        points_marker.ns = ns;
        points_marker.id = id + 1;
        points_marker.type = visualization_msgs::msg::Marker::POINTS;
        points_marker.action = visualization_msgs::msg::Marker::ADD;
        points_marker.scale.x = 0.1;
        points_marker.scale.y = 0.1;
        points_marker.color.g = 1.0;
        points_marker.color.a = 1.0;
        points_marker.points.push_back(start_pos);
        points_marker.points.push_back(end_pos);

        markers.push_back(points_marker);
    }
} // namespace papjia_visualization

#endif