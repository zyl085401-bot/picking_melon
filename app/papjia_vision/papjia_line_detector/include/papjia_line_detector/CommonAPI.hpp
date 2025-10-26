/*
 * @Descripttion: 视觉公共文件，实现一些公用接口
 * @version: 2.0
 * @Author: 崔译文
 * @Date: 2023-12-21 15:36:12
 * @LastEditors: 崔译文
 * @LastEditTime: 2023-12-29 09:30:11
 */
#ifndef __COMMONAPI__
#define __COMMONAPI__

#include <math.h>
#include <opencv2/opencv.hpp>

namespace COMMONAPI
{
    /**
     * @brief: 边缘检测，凡是高于高阈值的都保留,凡是小于低阈值都丢弃,从高于高阈值的像素出发,凡是大于低阈值而且相互连接的,都保留
     * @param {Mat} &src 源图像
     * @param {Mat} &dst 目标图像，存储边缘信息
     * @param {int} minVal 低阈值
     * @param {int} maxVal 高阈值
     * @return {null} 无返回值，结果存储在dst参数中
     */
    void EdgeDetect(cv::Mat &src, cv::Mat &dst, int minVal, int maxVal)
    {
        cv::Mat gray;
        cvtColor(src, gray, cv::COLOR_RGB2GRAY); // 转换为灰度图像
        cv::blur(gray, gray, cv::Size(3, 3));    // 高斯模糊
        cv::Canny(gray, dst, minVal, maxVal);    // 边缘检测
    }

    /**
     * @brief: 计算点到直线的距离
     * @param {Point2d} point1 直线上的一点
     * @param {Point2d} point2 直线上的一点
     * @param {Point2d} point 平面上一点
     * @return {distance} 点到直线的距离
     */
    double point2LineDistance(cv::Point2d point1, cv::Point2d point2, cv::Point2d point)
    {
        double x1 = point1.x;
        double y1 = point1.y;
        double x2 = point2.x;
        double y2 = point2.y;
        double x0 = point.x;
        double y0 = point.y;
        double distance;
        distance = fabs(((y1 - y2) * x0 - (x1 - x2) * y0 + (x1 * y2 - x2 * y1)) / sqrt(pow(y1 - y2, 2) + pow(x1 - x2, 2))); // 点到直线公式

        return distance;
    }

    /**
     * @brief: 将直线l1和l2合并为直线l
     * @param {Vec4i} &l1 直线
     * @param {Vec4i} &l2 直线
     * @param {Vec4i} &l 直线
     * @return {bool} 是否合并成功
     */
    bool mergeLine(cv::Vec4i &l1, cv::Vec4i &l2, cv::Vec4i &l, int distance = 10)
    {
        cv::Point2d p1(l1[0], l1[1]), p2(l[2], l[3]), p3(l2[0], l2[1]), p4(l2[2], l2[3]);
        double d1 = point2LineDistance(p1, p2, p3);
        double d2 = point2LineDistance(p1, p2, p4);
        if (std::max(d1, d2) < distance) // 计算两线段间的最短距离是否满足合并要求
        {
            if (abs(p1.x - p2.x) > abs(p1.y - p2.y))
            {
                if (p1.x < l[0])
                {
                    l[0] = p1.x;
                    l[1] = p1.y;
                }
                else if (p1.x > l[2])
                {
                    l[2] = p1.x;
                    l[3] = p1.y;
                }
                if (p2.x < l[0])
                {
                    l[0] = p2.x;
                    l[1] = p2.y;
                }
                else if (p2.x > l[2])
                {
                    l[2] = p2.x;
                    l[3] = p2.y;
                }
                if (p3.x < l[0])
                {
                    l[0] = p3.x;
                    l[1] = p3.y;
                }
                else if (p3.x > l[2])
                {
                    l[2] = p3.x;
                    l[3] = p3.y;
                }
                if (p4.x < l[0])
                {
                    l[0] = p4.x;
                    l[1] = p4.y;
                }
                else if (p4.x > l[2])
                {
                    l[2] = p4.x;
                    l[3] = p4.y;
                }
            }
            else
            {
                if (p1.y < l[0])
                {
                    l[0] = p1.x;
                    l[1] = p1.y;
                }
                else if (p1.y > l[2])
                {
                    l[2] = p1.x;
                    l[3] = p1.y;
                }
                if (p2.y < l[0])
                {
                    l[0] = p2.x;
                    l[1] = p2.y;
                }
                else if (p2.y > l[2])
                {
                    l[2] = p2.x;
                    l[3] = p2.y;
                }
                if (p3.y < l[0])
                {
                    l[0] = p3.x;
                    l[1] = p3.y;
                }
                else if (p3.y > l[2])
                {
                    l[2] = p3.x;
                    l[3] = p3.y;
                }
                if (p4.y < l[0])
                {
                    l[0] = p4.x;
                    l[1] = p4.y;
                }
                else if (p4.y > l[2])
                {
                    l[2] = p4.x;
                    l[3] = p4.y;
                }
            }
            return true;
        }
        return false;
    }

    /**
     * @brief: 合并直线集合
     * @param {vector<Vec4i>} &srcLines 需要合并的直线
     * @param {vector<Vec4i>} &dstLines 存储合并的结果
     * @return {null} 合并的结果存储在dstLines中
     */
    void mergeLines(std::vector<cv::Vec4i> &srcLines, std::vector<cv::Vec4i> &dstLines)
    {
        if (srcLines.size() > 0)
        {
            dstLines.push_back(cv::Vec4i(srcLines[0][0], srcLines[0][1], srcLines[0][2], srcLines[0][3])); // 先存入第一个直线
        }
        for (size_t i = 1; i < srcLines.size() - 1; ++i)
        {
            bool flagMerge = false;
            for (size_t k = 0; k < dstLines.size(); ++k)
            {
                flagMerge = mergeLine(dstLines[k], srcLines[i], dstLines[k]); // 合并srcLines[i]到dstLines[k]
                if (flagMerge)
                {
                    break;
                }
            }
            if (!flagMerge)
            {
                dstLines.push_back(cv::Vec4i(srcLines[i][0], srcLines[i][1], srcLines[i][2], srcLines[i][3])); // 压入新直线
            }
        }
    }
} // namespace COMMONAPI

#endif