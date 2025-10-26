/*
 * @Descripttion: 深度相机模型
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-12 15:15:40
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 10:18:59
 */
#ifndef __DCAMERA_MODEL__
#define __DCAMERA_MODEL__

#include <string>
#include <vector>
#include <opencv2/opencv.hpp>
#include "types.h"

/**
 * @brief: 深度相机
 * @return {*}
 */
class DCameraModel
{
public:
    /**
     * @brief: 构造函数
     * @return {*}
     */
    DCameraModel(const std::string &distortion_model,
                 const std::vector<double> &D,
                 const std::vector<double> &K,
                 const std::vector<double> &P,
                 double metric)
    {
        distortion_model_ = distortion_model; // 畸变魔星
        D_ = D;                               // 畸变参数
        K_ = K;                               // 内参
        P_ = P;                               // 投影矩阵
        fx_ = K_[0], fy_ = K_[4], cx_ = K_[2], cy_ = K_[5];
        metric_ = metric;
        std::cout << "cx: " << cx_ << " cy: " << cy_ << " fx: " << fx_ << " fy:" << fy_ << std::endl;
        std::cout << "metric: " << metric_ << std::endl;
    };

    /**
     * @brief: 深度图转无结构点云
     * @param {Mat} &depth 深度图
     * @param {Ptr} &cloud 点云
     * @return {*}
     */
    void depth_to_pointcloud(const cv::Mat &depth, PointCloudT::Ptr &cloud)
    {
        int w = depth.cols;
        int h = depth.rows;
        for (int v = 0; v < h; v++)
        {
            const uint16_t *row = depth.ptr<uint16_t>(v);
            for (int u = 0; u < w; u++)
            {
                if (!std::isnan(row[u])) // 深度是否有效
                {
                    double z = metric_ * row[u];
                    double x = (u - cx_) * z / fx_;
                    double y = (v - cy_) * z / fy_;
                    PointT p((float)x, (float)y, (float)z); // 构造3D点
                    cloud->push_back(p);
                }
            }
        }
    };

    /**
     * @brief: 依据深度和掩码生成多个点云
     * @return {*}
     */
    void depth_to_pointclouds(const cv::Mat &depth,
                              const std::vector<std::vector<int>> &rects,
                              std::vector<PointCloudT::Ptr> &clouds)
    {
        for (size_t i = 0; i < rects.size(); ++i)
        {
            PointCloudT::Ptr cloud(new PointCloudT); // 构造点云
            int x1 = rects[i][0], y1 = rects[i][1], x2 = rects[i][2], y2 = rects[i][3];
            for (int v = y1; v < y2; ++v)
            {
                const uint16_t *rd = depth.ptr<uint16_t>(v);
                for (int u = x1; u < x2; ++u)
                {
                    if (!std::isnan(rd[u])) // 深度是否有效
                    {
                        double z = metric_ * rd[u];
                        double x = (u - cx_) * z / fx_;
                        double y = (v - cy_) * z / fy_;
                        PointT p((float)x, (float)y, (float)z);
                        cloud->push_back(p); // 加入对应点云
                    }
                }
            }
            clouds.push_back(cloud);
        }
        for (auto cloud : clouds)
        {
            std::cout << "Pointcloud size: " << cloud->size() << std::endl;
        }
    };

    /**
     * @brief: 依据深度和掩码生成多个点云
     * @return {*}
     */
    void depth_to_pointclouds(const cv::Mat &depth,
                              const cv::Mat &mask,
                              std::vector<PointCloudT::Ptr> &clouds,
                              int inst_max_num = 0)
    {
        if (inst_max_num > 0) // 掩码（实例）个数
        {
            for (int i = 0; i < inst_max_num; ++i)
            {
                PointCloudT::Ptr cloud(new PointCloudT); // 构造点云
                clouds.push_back(cloud);
            }
            int w = mask.cols;
            int h = mask.rows;
            std::cout << "image width: " << w << " image height: " << h << std::endl;
            for (int v = 0; v < h; ++v)
            {
                const uchar *rm = mask.ptr<uchar>(v);
                const uint16_t *rd = depth.ptr<uint16_t>(v);
                for (int u = 0; u < w; ++u)
                {
                    int k = rm[u]; // 掩码
                    if (k > 0)
                    {
                        k -= 1;                 // 掩码转下标
                        if (!std::isnan(rd[u])) // 有效深度值
                        {
                            double z = metric_ * rd[u];
                            double x = (u - cx_) * z / fx_;
                            double y = (v - cy_) * z / fy_;
                            PointT p((float)x, (float)y, (float)z);
                            clouds[k]->push_back(p); // 加入对应点云
                        }
                    }
                }
            }
            for (auto cloud : clouds)
            {
                std::cout << "Pointcloud size: " << cloud->size() << std::endl;
            }
        }
    };

private:
    std::string distortion_model_;
    std::vector<double> D_;    // 畸变参数
    std::vector<double> K_;    // 相机内参
    std::vector<double> P_;    // 相机投影参数
    double cx_, cy_, fx_, fy_; // 目前只使用这几个相机内参
    double metric_;
};

#endif