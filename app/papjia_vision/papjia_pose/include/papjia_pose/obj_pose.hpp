/*
 * @Descripttion: 根据点云计算物体位姿
 * @version:
 * @Author: 崔译文
 * @Date: 2024-01-02 10:51:17
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 10:38:46
 */
#ifndef __OBJ_POSE__
#define __OBJ_POSE__

#include <string>
#include <mutex>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/time_synchronizer.h>
#include <papjia_vision_interface/srv/detect_objs.hpp>
#include <papjia_vision_interface/srv/seg_image.hpp>
#include <papjia_pose/visibility_control.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include "types.h"
#include "dcamera.hpp"
#include "pose_estimator.hpp"

struct CombinedData // 图像消息
{
    sensor_msgs::msg::Image::ConstSharedPtr rgb;   // 彩色图像消息
    sensor_msgs::msg::Image::ConstSharedPtr depth; // 深度图像消息
};

struct ImageSegmentationCfg // 图像分割配置
{
    size_t inst_num_max;   // 实例的最大数量
    size_t point_num_min;  // mask对应的最大点数
    size_t point_num_max;  // mask对应的最少点数
    size_t rect_area_min;  // rect区域的最小值
    size_t rect_area_max;  // rect区域的最大值
    double inst_score_min; // 最小评分
};

/**
 * @brief: 位姿计算 - ROS服务
 * @return {*}
 */
class ObjPoseService : public rclcpp::Node
{
private:
    bool flag_seg_by_cluster_; // 是否在实例图像上进一步聚类
    std::string target_frame_; // 目标TF frame
    std::shared_ptr<tf2_ros::TransformListener> transform_listener_;
    std::unique_ptr<tf2_ros::Buffer> tf_buffer_;

    std::string topic_image_rgb_;                                                    // 彩色图像topic
    std::string topic_image_depth_;                                                  // 深度图片topic
    bool flag_sync_image_;                                                           // 深度&彩色图像是否同步
    bool flag_pub_cloud_transformed_;                                                // 是否发布点云
    bool flag_use_pca_pose_;                                                         // 是否使用PCA姿态
    std::vector<CombinedData> datas_;                                                // 深度&彩色同步数据
    std::vector<sensor_msgs::msg::Image::ConstSharedPtr> rgbs_;                      // 分离的彩色图像
    std::vector<sensor_msgs::msg::Image::ConstSharedPtr> depths_;                    // 分离的深度图像
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_rgb_;         // 订阅图像
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_depth_;       // 订阅图像
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_cloud_;          // 发布点云
    rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr pub_markers_; // 发布marker
    message_filters::Subscriber<sensor_msgs::msg::Image> sub_image_rgb_temp_;
    message_filters::Subscriber<sensor_msgs::msg::Image> sub_image_depth_temp_;
    std::shared_ptr<message_filters::TimeSynchronizer<sensor_msgs::msg::Image, sensor_msgs::msg::Image>> sync_sub_; // 消息同步

    std::string service_object_detect_;                                             // 物体检测（位姿）topic
    rclcpp::Service<papjia_vision_interface::srv::DetectObjs>::SharedPtr server_object_detect_; // 物体检测（位姿）服务

    std::string service_image_seg_;                                          // 物体检测（mask）topic
    rclcpp::Client<papjia_vision_interface::srv::SegImage>::SharedPtr client_image_seg_; // 物体检测（mask）服务
    rclcpp::CallbackGroup::SharedPtr client_cb_group_;                       // 允许callback中callback

    std::string path_vision_cfg_;                   // 视觉功能配置文件
    ImageSegmentationCfg img_seg_cfg_;              // 图像分割（mask）配置
    std::shared_ptr<DCameraModel> dcamera_model_;   // 深度相机模型
    std::shared_ptr<PoseEstimator> pose_estimator_; // 姿态估计器

    std::mutex rgbs_mutex_;
    std::mutex depths_mutex_;
    std::mutex datas_mutex_;

public:
    COMPOSITION_PUBLIC
    explicit ObjPoseService(const rclcpp::NodeOptions &options);
    ~ObjPoseService();


    void saveDataWithTimestamp(const std::string& base_path, 
                                           const cv::Mat& color_image, 
                                           const cv::Mat& depth_image, 
                                           const std::vector<pcl::PointCloud<pcl::PointXYZ>::Ptr>& clouds);

    std::string getTimestampedFilename(const std::string& prefix, const std::string& extension);
    /**
     * @brief: 加载视觉配置
     * @param {string} &path 配置文件路径
     * @return {*}
     */
    void load_vision_config(const std::string &path);

    /**
     * @brief: 发布位姿估计结果（Markers）
     * @param {int} type Marker类型
     * @param {vector<papjia_vision_interface::msg::Object>} &objs 物体位姿以及大小
     * @return {*}
     */
    void pub_rviz_markers(int type, const std::vector<papjia_vision_interface::msg::Object> &objs);

    /**
     * @brief: 位姿估计Service
     * @param {SharedPtr} request 请求
     * @param {SharedPtr} response 结果
     * @return {*}
     */
    bool callback_object_detect(const papjia_vision_interface::srv::DetectObjs::Request::SharedPtr request, papjia_vision_interface::srv::DetectObjs::Response::SharedPtr response);

    /**
     * @brief: 彩色图像callback
     * @param {ConstSharedPtr} &msg 彩色图像消息
     * @return {*}
     */
    void callback_image_rgb(const sensor_msgs::msg::Image::ConstSharedPtr &msg);

    /**
     * @brief: 深度图像callback
     * @param {ConstSharedPtr} &msg 深度图像消息
     * @return {*}
     */
    void callback_image_depth(const sensor_msgs::msg::Image::ConstSharedPtr &msg);

    /**
     * @brief: 同步的深度和彩色图像callback
     * @param {ConstSharedPtr} &msg1 深度图像消息
     * @param {ConstSharedPtr} &msg2 彩色图像消息
     * @return {*}
     */
    void image_callback(const sensor_msgs::msg::Image::ConstSharedPtr &msg1, const sensor_msgs::msg::Image::ConstSharedPtr &msg2);
};

#endif