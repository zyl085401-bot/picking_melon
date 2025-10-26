/*
 * @Descripttion: 物体位姿估计（依据点云）
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-15 15:08:34
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 10:56:16
 */
#ifndef __POSE_ESTIMATOR_HPP__
#define __POSE_ESTIMATOR_HPP__

#include <vector>
#include <algorithm>
#include <exception>
#include <iostream>
#include <Eigen/Core>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/conditional_removal.h>
#include <pcl/filters/passthrough.h>
#include <pcl/common/pca.h>
#include <pcl/common/common.h>
#include <pcl/common/transforms.h>
#include <pcl/segmentation/extract_clusters.h>
#include <pcl/segmentation/sac_segmentation.h>
#include "types.h"

/**
 * @brief: 点云大小比较
 * @return {*}
 */
bool comparePointIndicesSize(const pcl::PointIndices &a,
                             const pcl::PointIndices &b)
{
    return a.indices.size() > b.indices.size();
}

/**
 * @brief: 位姿评估器
 * @return {*}
 */
class PoseEstimator
{
public:
    PoseEstimator(const std::vector<double> &workspace,
                  double leaf_size)
    {
        workspace_ = workspace; // 工作空间3D
        leaf_size_ = leaf_size; // 下采样参数
    };

    /**
     * @brief: 设置物体的大小范围
     * @return {*}
     */
    void set_obj_size(const std::vector<double> &obj_size_min,
                      const std::vector<double> &obj_size_max)
    {
        obj_size_max_ = obj_size_max;
        obj_size_min_ = obj_size_min;
        std::cout << "物体大小 ";
        for (auto x : obj_size_min_)
            std::cout << x << " ";
        std::cout << "-> ";
        for (auto x : obj_size_max_)
            std::cout << x << " ";
        std::cout << std::endl;
    };

    /**
     * @brief: 设置物体点云的最小/最大点数
     * @return {*}
     */
    void set_obj_point_num(size_t point_num_min,
                           size_t point_num_max)
    {
        point_num_max_ = point_num_max;
        point_num_min_ = point_num_min;
        std::cout << "点云范围 [" << point_num_min_ << ", " << point_num_max_ << "]" << std::endl;
    };

    /**
     * @brief: 设置聚类分割的距离阈值
     * @param {double} tolerance 距离阈值
     * @return {*}
     */
    void set_cluster_tolerance(double tolerance)
    {
        cluster_tolerance_ = tolerance;
    };

    /**
     * @brief: 降采样
     * @return {*}
     */
    void downsample(const PointCloudT::Ptr &cloud,
                    PointCloudT::Ptr &cloud_downsample,
                    float leaf_size)
    {
        pcl::VoxelGrid<PointT> vg;
        vg.setInputCloud(cloud);
        vg.setLeafSize(leaf_size, leaf_size, leaf_size);
        vg.filter(*cloud_downsample);
        std::cout << "下采样 " << cloud->size() << " -> " << cloud_downsample->size() << std::endl;
    };

    /**
     * @brief: 降采样 - 带异常处理和自动调整
     * @return {*}
     */
    void downsample(const PointCloudT::Ptr &cloud,
                    PointCloudT::Ptr &cloud_downsample)
    {
        if (cloud->empty()) {
            *cloud_downsample = *cloud;
            return;
        }

        // 计算点云的范围
        PointT min_point, max_point;
        pcl::getMinMax3D(*cloud, min_point, max_point);
        
        // 计算点云的范围大小
        double range_x = max_point.x - min_point.x;
        double range_y = max_point.y - min_point.y;
        double range_z = max_point.z - min_point.z;
        double max_range = std::max({range_x, range_y, range_z});
        
        // 动态调整leaf_size以避免整数溢出
        // PCL使用32位整数索引，最大值为2^31-1
        double adjusted_leaf_size = leaf_size_;
        const double max_voxels = 1000000; // 安全阈值
        
        if (max_range / adjusted_leaf_size > max_voxels) {
            adjusted_leaf_size = max_range / max_voxels;
            std::cout << "自动调整leaf_size从 " << leaf_size_ << " 到 " << adjusted_leaf_size 
                      << " (点云范围: " << max_range << ")" << std::endl;
        }
        
        try {
            pcl::VoxelGrid<PointT> vg;
            vg.setInputCloud(cloud);
            vg.setLeafSize(adjusted_leaf_size, adjusted_leaf_size, adjusted_leaf_size);
            vg.filter(*cloud_downsample);
            std::cout << "下采样 " << cloud->size() << " -> " << cloud_downsample->size() 
                      << " (leaf_size: " << adjusted_leaf_size << ")" << std::endl;
        } catch (const std::exception& e) {
            std::cout << "VoxelGrid降采样失败: " << e.what() << std::endl;
            // 如果仍然失败，使用更大的leaf_size
            double fallback_leaf_size = std::max(adjusted_leaf_size * 2.0, 0.05);
            std::cout << "使用备用leaf_size: " << fallback_leaf_size << std::endl;
            
            pcl::VoxelGrid<PointT> vg;
            vg.setInputCloud(cloud);
            vg.setLeafSize(fallback_leaf_size, fallback_leaf_size, fallback_leaf_size);
            vg.filter(*cloud_downsample);
            std::cout << "备用下采样 " << cloud->size() << " -> " << cloud_downsample->size() << std::endl;
        }
    };

    /**
     * @brief: 包围盒过滤
     * @return {*}
     */
    void filter_by_conditions(const PointCloudT::Ptr &cloud,
                              PointCloudT::Ptr &cloud_filtered,
                              std::vector<float> &limits)
    {
        if (limits.size() < 6)
        {
            std::cout << "条件不足 !" << std::endl;
        }
        pcl::ConditionAnd<PointT>::Ptr range_cond(new pcl::ConditionAnd<PointT>());
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "x", pcl::ComparisonOps::GT, limits[0])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "x", pcl::ComparisonOps::LT, limits[1])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "y", pcl::ComparisonOps::GT, limits[2])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "y", pcl::ComparisonOps::LT, limits[3])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "z", pcl::ComparisonOps::GT, limits[4])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "z", pcl::ComparisonOps::LT, limits[5])));
        // build the filter
        pcl::ConditionalRemoval<PointT> condrem;
        condrem.setCondition(range_cond);
        condrem.setInputCloud(cloud);
        condrem.setKeepOrganized(false);
        // apply filter
        condrem.filter(*cloud_filtered);
        std::cout << "点云范围过滤 " << cloud->size() << " -> " << cloud_filtered->size() << std::endl;
    };

    /**
     * @brief: 包围盒过滤
     * @return {*}
     */
    void filter_by_conditions(const PointCloudT::Ptr &cloud,
                              PointCloudT::Ptr &cloud_filtered)
    {
        if (workspace_.size() < 6)
        {
            std::cout << "条件不足 !" << std::endl;
        }
        pcl::ConditionAnd<PointT>::Ptr range_cond(new pcl::ConditionAnd<PointT>());
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "x", pcl::ComparisonOps::GT, workspace_[0])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "x", pcl::ComparisonOps::LT, workspace_[1])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "y", pcl::ComparisonOps::GT, workspace_[2])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "y", pcl::ComparisonOps::LT, workspace_[3])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "z", pcl::ComparisonOps::GT, workspace_[4])));
        range_cond->addComparison(
            pcl::FieldComparison<PointT>::ConstPtr(new pcl::FieldComparison<PointT>(
                "z", pcl::ComparisonOps::LT, workspace_[5])));
        // build the filter
        pcl::ConditionalRemoval<PointT> condrem;
        condrem.setCondition(range_cond);
        condrem.setInputCloud(cloud);
        condrem.setKeepOrganized(false);
        // apply filter
        condrem.filter(*cloud_filtered);
        std::cout << "点云范围过滤 " << cloud->size() << " -> " << cloud_filtered->size() << std::endl;
    };

    /**
     * @brief: 点云范围是否在工作空间内
     * @return {bool} false为在空间之外
     */
    bool is_valid_range(const PointT &min_point, const PointT &max_point)
    {
        if (workspace_.size() != 6)
        {
            std::cout << "范围条件不足 !" << std::endl;
            return true;
        }
        if (min_point.x < workspace_[0] || min_point.y < workspace_[1] || min_point.z < workspace_[2] || max_point.x > workspace_[3] || max_point.y > workspace_[4] || max_point.z > workspace_[5])
        {
            std::cout << "超出范围 " << min_point << " " << max_point << std::endl;
            return false;
        }
        return true;
    }

    /**
     * @brief: 物体大小是否在为设置范围内
     * @return {bool} false为在设置外
     */
    bool is_valid_size(const PointT &min_point, const PointT &max_point)
    {
        if (obj_size_min_.size() != 3 || obj_size_max_.size() != 3)
        {
            std::cout << "大小条件不足 !" << std::endl;
            return true;
        }
        double x, y, z;
        x = max_point.x - min_point.x;
        y = max_point.y - min_point.y;
        z = max_point.z - min_point.z;
        if (x < obj_size_min_[0] || y < obj_size_min_[1] || z < obj_size_min_[2])
        {
            std::cout << "物体太小 size(" << x << ", " << y << ", " << z << ")" << std::endl;
            return false;
        }
        if (x > obj_size_max_[0] || y > obj_size_max_[1] || z > obj_size_max_[2])
        {
            std::cout << "物体太大 size(" << x << ", " << y << ", " << z << ")" << std::endl;
            return false;
        }
        return true;
    }

    /**
     * @brief: 单轴范围过滤
     * @return {*}
     */
    void filter_by_pass(const PointCloudT::Ptr &cloud,
                        PointCloudT::Ptr &cloud_filtered,
                        std::string field,
                        double min,
                        double max)
    {
        // Create the filtering object
        pcl::PassThrough<PointT> pass;
        pass.setInputCloud(cloud);
        pass.setFilterFieldName(field);
        pass.setFilterLimits(min, max);
        // pass.setFilterLimitsNegative(true);
        pass.filter(*cloud_filtered);
        std::cout << "点云过滤(" << field << ") " << cloud->size() << " -> " << cloud_filtered->size() << std::endl;
    };

    /**
     * @brief: PCA姿态计算
     * @return {*}
     */
    void pca_transform(const PointCloudT::Ptr &cloud,
                       PointCloudT::Ptr &cloud_transformed,
                       Eigen::Matrix4d &pca_transform)
    {
        pcl::PCA<PointT> pca; // PCA算法

        pcl::PointCloud<PointT> objProj;
        pca.setInputCloud(cloud);                                                          // 设置输入点云
        pca.project(*cloud, *cloud_transformed);                                           // 投影点云
        Eigen::Matrix3f EigenSpaceObj = pca.getEigenVectors();                             // 获取特征向量
        Eigen::Vector3f PcaTransObj(pca.getMean()(0), pca.getMean()(1), pca.getMean()(2)); // 获取平均值

        Eigen::Matrix3f EigenSpaceObjT = EigenSpaceObj.transpose();      // 获取特征向量的转置矩阵
        Eigen::Vector3f PcaTransObj_inv = -EigenSpaceObjT * PcaTransObj; // 获取平均值的逆矩阵
        pca_transform << EigenSpaceObjT(0, 0), EigenSpaceObjT(0, 1),
            EigenSpaceObjT(0, 2), PcaTransObj_inv(0), EigenSpaceObjT(1, 0),
            EigenSpaceObjT(1, 1), EigenSpaceObjT(1, 2), PcaTransObj_inv(1),
            EigenSpaceObjT(2, 0), EigenSpaceObjT(2, 1), EigenSpaceObjT(2, 2),
            PcaTransObj_inv(2), 0, 0, 0, 1;
    };

    /**
     * @brief: PCA姿态计算，包含坐标轴调整
     * @return {*}
     */
    void pca_transform_z(const PointCloudT::Ptr &cloud,
                         PointCloudT::Ptr &cloud_transformed,
                         Eigen::Matrix4d &pca_transform,
                         Eigen::Vector4d &pca_centroid,
                         Eigen::Quaterniond &pca_quat)
    {
        pcl::compute3DCentroid(*cloud, pca_centroid);
        Eigen::Matrix3d covariance_matrix;
        pcl::computeCovarianceMatrixNormalized(*cloud, pca_centroid, covariance_matrix);

        Eigen::SelfAdjointEigenSolver<Eigen::Matrix3d> eigen_solver(covariance_matrix, Eigen::ComputeEigenvectors);
        Eigen::Matrix3d eigenVectorsPCA = eigen_solver.eigenvectors();
        eigenVectorsPCA.col(0) = eigenVectorsPCA.col(2); // 校正主方向间垂直
        if (eigenVectorsPCA(2, 0) < 0)
        {
            eigenVectorsPCA.col(0) *= -1;
        }
        eigenVectorsPCA.col(2) = eigenVectorsPCA.col(0).cross(eigenVectorsPCA.col(1));
        if (eigenVectorsPCA(2, 2) < 0)
        {
            eigenVectorsPCA.col(1) *= -1;
            eigenVectorsPCA.col(2) = eigenVectorsPCA.col(0).cross(eigenVectorsPCA.col(1));
        }

        pca_quat = Eigen::Quaterniond(eigenVectorsPCA);

        pca_transform.block<3, 3>(0, 0) = eigenVectorsPCA.transpose();                                      // R.
        pca_transform.block<3, 1>(0, 3) = -1.0f * (eigenVectorsPCA.transpose()) * (pca_centroid.head<3>()); //  -R*t
        pcl::transformPointCloud(*cloud, *cloud_transformed, pca_transform);
    };

    /**
     * @brief: PCA姿态估计，模型匹配
     * @return {*}
     */
    void pca_registration(const PointCloudT::Ptr &cloud_input,
                          const PointCloudT::Ptr &cloud_model,
                          PointCloudT::Ptr &cloud_projected,
                          Eigen::Matrix4d &transform)
    {
        Eigen::Matrix4d transform1, transform2;
        pca_transform(cloud_input, cloud_projected, transform1);
        pca_transform(cloud_model, cloud_projected, transform2);
        transform = transform2 * transform1;
        pcl::transformPointCloud(*cloud_input, *cloud_projected, transform); // 变换点云
    };

    /**
     * @brief: 点云簇聚类分割
     * @return {*}
     */
    void seg_by_cluster_extraction(PointCloudT::Ptr &cloud,
                                   std::vector<PointCloudT::Ptr> &clusters,
                                   double tolerance,
                                   size_t min_cluster_size,
                                   size_t max_cluster_size)
    {
        pcl::search::KdTree<PointT>::Ptr tree(
            new pcl::search::KdTree<PointT>);
        tree->setInputCloud(cloud);

        std::vector<pcl::PointIndices> cluster_indices;
        pcl::EuclideanClusterExtraction<PointT> ec;
        ec.setClusterTolerance(tolerance);
        ec.setMinClusterSize(min_cluster_size);
        ec.setMaxClusterSize(max_cluster_size);
        ec.setSearchMethod(tree);
        ec.setInputCloud(cloud);
        // 聚类抽取结果保存在一个数组中，数组中每个元素代表抽取的一个组件点云的下标
        ec.extract(cluster_indices);

        if (cluster_indices.size() <= 0)
        {
            std::cout << " 没有合适的点云簇!" << std::endl;
            return;
        }
        // 排序
        sort(cluster_indices.begin(), cluster_indices.end(), comparePointIndicesSize);
        for (size_t i = 0; i < cluster_indices.size(); ++i)
        {
            PointCloudT::Ptr cluster(new PointCloudT);
            pcl::copyPointCloud(*cloud, cluster_indices[i].indices, *cluster);
            std::cout << "抽取点云簇 " << cluster->size() << " 点" << std::endl;
            clusters.push_back(cluster);
        }
    };

    /**
     * @brief: 点云簇聚类分割
     * @return {*}
     */
    void seg_by_cluster_extraction(PointCloudT::Ptr &cloud,
                                   std::vector<PointCloudT::Ptr> &clusters)
    {
        pcl::search::KdTree<PointT>::Ptr tree(
            new pcl::search::KdTree<PointT>);
        tree->setInputCloud(cloud);

        std::vector<pcl::PointIndices> cluster_indices;
        pcl::EuclideanClusterExtraction<PointT> ec;
        ec.setClusterTolerance(cluster_tolerance_);
        ec.setMinClusterSize(point_num_min_);
        ec.setMaxClusterSize(point_num_max_);
        ec.setSearchMethod(tree);
        ec.setInputCloud(cloud);
        // 聚类抽取结果保存在一个数组中，数组中每个元素代表抽取的一个组件点云的下标
        ec.extract(cluster_indices);

        if (cluster_indices.size() <= 0)
        {
            std::cout << " 没有合适的点云簇!" << std::endl;
            return;
        }
        // 排序
        sort(cluster_indices.begin(), cluster_indices.end(), comparePointIndicesSize);
        for (size_t i = 0; i < cluster_indices.size(); ++i)
        {
            PointCloudT::Ptr cluster(new PointCloudT);
            pcl::copyPointCloud(*cloud, cluster_indices[i].indices, *cluster);
            // std::cout << "抽取点云簇 " << cluster->size() << " 点" << std::endl;
            clusters.push_back(cluster);
        }
    };

private:
    std::vector<double> workspace_;    // 工作空间3D
    std::vector<double> obj_size_min_; // 物体最小大小
    std::vector<double> obj_size_max_; // 物体最大大小
    size_t point_num_max_;             // 最大点云
    size_t point_num_min_;             // 最小点云
    double leaf_size_;                 // 叶子大小，降采样参数
    double cluster_tolerance_;         // 距离聚类参数，距离阈值，大于此值属于不同点云
};

#endif