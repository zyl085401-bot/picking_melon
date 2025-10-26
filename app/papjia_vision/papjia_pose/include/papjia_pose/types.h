/*
 * @Descripttion: 点云类型
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-15 11:03:25
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 10:57:14
 */
#ifndef __TYPES_H__
#define __TYPES_H__

#include <pcl/point_types.h>
#include <pcl/point_cloud.h>

typedef pcl::PointXYZ PointT;
typedef pcl::PointCloud<PointT> PointCloudT;

#endif