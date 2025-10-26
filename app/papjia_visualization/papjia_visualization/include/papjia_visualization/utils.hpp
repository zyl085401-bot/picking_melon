#ifndef PAPJIA_VISUALIZATION__UTILS_HPP
#define PAPJIA_VISUALIZATION__UTILS_HPP

#include <vector>
#include <stdexcept>
#include <string>
#include <cmath>
#include <geometry_msgs/msg/point.hpp>
#include <geometry_msgs/msg/quaternion.hpp>

void euler_to_quaternion(double roll, double pitch, double yaw,
                         double &qx, double &qy, double &qz, double &qw)
{
    double cy = std::cos(yaw * 0.5);
    double sy = std::sin(yaw * 0.5);
    double cp = std::cos(pitch * 0.5);
    double sp = std::sin(pitch * 0.5);
    double cr = std::cos(roll * 0.5);
    double sr = std::sin(roll * 0.5);

    qw = cr * cp * cy + sr * sp * sy;
    qx = sr * cp * cy - cr * sp * sy;
    qy = cr * sp * cy + sr * cp * sy;
    qz = cr * cp * sy - sr * sp * cy;
}

void parse_pose(const std::vector<double> &point_array,
                geometry_msgs::msg::Point &position,
                geometry_msgs::msg::Quaternion &orientation)
{
    if (point_array.size() < 3)
    {
        throw std::invalid_argument("数组至少需要3个元素");
    }

    position.x = point_array[0];
    position.y = point_array[1];
    position.z = point_array[2];

    // 默认姿态
    orientation.x = 0.0;
    orientation.y = 0.0;
    orientation.z = 0.0;
    orientation.w = 1.0;

    // 处理长度为6的情况：欧拉角
    if (point_array.size() == 6)
    {
        double qx, qy, qz, qw;
        euler_to_quaternion(
            point_array[3],
            point_array[4],
            point_array[5],
            qx, qy, qz, qw);
        orientation.x = qx;
        orientation.y = qy;
        orientation.z = qz;
        orientation.w = qw;
    }

    // 处理长度为7的情况：四元数
    else if (point_array.size() >= 7)
    {
        orientation.x = point_array[3];
        orientation.y = point_array[4];
        orientation.z = point_array[5];
        orientation.w = point_array[6];
    }
}

#endif