/*
 * @Descripttion: 位姿估计 - 虽有插件形式但不使用
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-02 10:50:45
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 11:01:10
 */
#include <nlohmann/json.hpp>

#include <fstream>
#include <chrono>
#include <yaml-cpp/yaml.h>
#include <cv_bridge/cv_bridge.h>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <pcl/common/transforms.h>
#include <pcl_conversions/pcl_conversions.h>
#include <papjia_vision_interface/srv/detect_objs.hpp>
#include <papjia_vision_interface/msg/object.hpp>
#include "papjia_pose/obj_pose.hpp"

#include <iostream>
#include <string>
#include <filesystem> // C++17 引入的文件系统库
#include <pcl/io/ply_io.h>


namespace fs = std::filesystem; ////////////

using namespace std::placeholders;
using namespace std::chrono_literals;

////////////////////////////////////////////////////////
// 获取当前时间的时间戳字符串
using json = nlohmann::json;


ObjPoseService::ObjPoseService(const rclcpp::NodeOptions &options) : Node("line_detector", options)
{
    RCLCPP_INFO(this->get_logger(), "Begin init node ...");

    // 声明ROS变量
    this->declare_parameter<std::string>("topic_image_rgb", "");
    this->declare_parameter<std::string>("topic_image_depth", "");
    this->declare_parameter<std::string>("path_vision_cfg", "");
    this->declare_parameter<std::string>("service_object_detect", "");
    this->declare_parameter<std::string>("service_image_seg", "");
    this->declare_parameter<bool>("flag_sync_image", false);
    this->declare_parameter<bool>("flag_pub_cloud_transformed", false);
    this->declare_parameter<bool>("flag_use_pca_pose", false);
    

    this->get_parameter("topic_image_rgb", topic_image_rgb_);
    this->get_parameter("topic_image_depth", topic_image_depth_);
    this->get_parameter("path_vision_cfg", path_vision_cfg_);
    this->get_parameter("service_object_detect", service_object_detect_);
    this->get_parameter("service_image_seg", service_image_seg_);
    this->get_parameter("flag_sync_image", flag_sync_image_);
    this->get_parameter("flag_pub_cloud_transformed", flag_pub_cloud_transformed_);
    this->get_parameter("flag_use_pca_pose", flag_use_pca_pose_);

    RCLCPP_INFO(this->get_logger(), "Get param topic_image_rgb %s", topic_image_rgb_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param topic_image_depth %s", topic_image_depth_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param path_vision_cfg %s", path_vision_cfg_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param service_object_detect %s", service_object_detect_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param service_image_seg %s", service_image_seg_.c_str());
    RCLCPP_INFO(this->get_logger(), "Get param flag_sync_image %d", flag_sync_image_);

    if (flag_sync_image_)
    {
        sub_image_depth_temp_.subscribe(this, topic_image_depth_);
        sub_image_rgb_temp_.subscribe(this, topic_image_rgb_);
        // 设置时间同步器，最后一个参数是回调函数
        sync_sub_ = std::make_shared<message_filters::TimeSynchronizer<sensor_msgs::msg::Image, sensor_msgs::msg::Image>>(sub_image_depth_temp_, sub_image_rgb_temp_, 3);
        sync_sub_->registerCallback(std::bind(&ObjPoseService::image_callback, this, _1, _2));
        RCLCPP_INFO(this->get_logger(), "Register sync(%s, %s)", topic_image_depth_.c_str(), topic_image_rgb_.c_str());
    }
    else
    {
        // 创建图像订阅器
        sub_image_rgb_ = create_subscription<sensor_msgs::msg::Image>(
            topic_image_rgb_, 1, std::bind(&ObjPoseService::callback_image_rgb, this, _1));
        RCLCPP_INFO(this->get_logger(), "Register callback(%s)", topic_image_rgb_.c_str());
        sub_image_depth_ = create_subscription<sensor_msgs::msg::Image>(
            topic_image_depth_, 1, std::bind(&ObjPoseService::callback_image_depth, this, _1));
        RCLCPP_INFO(this->get_logger(), "Register callback(%s)", topic_image_depth_.c_str());
    }

    // 加载视觉配置
    load_vision_config(path_vision_cfg_);

    // 创建服务
    server_object_detect_ = this->create_service<papjia_vision_interface::srv::DetectObjs>(service_object_detect_,
                                                                               std::bind(&ObjPoseService::callback_object_detect, this, _1, _2));
    client_cb_group_ = this->create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);
    client_image_seg_ = this->create_client<papjia_vision_interface::srv::SegImage>(service_image_seg_,
                                                                        rmw_qos_profile_services_default,
                                                                        client_cb_group_);
    // 点云发布器
    pub_cloud_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/papjia_pose/pointcloud", 3);
    // TF转换器
    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
    transform_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
    // Marker发布器
    pub_markers_ = this->create_publisher<visualization_msgs::msg::MarkerArray>("/papjia_pose/marker_array", 3);

    RCLCPP_INFO(this->get_logger(), "Finished init");
}

ObjPoseService::~ObjPoseService()
{
}

///////////////////////////////////////////////

std::string ObjPoseService::getTimestampedFilename(const std::string& prefix, const std::string& extension) {
    auto now = std::chrono::system_clock::now();
    auto in_time_t = std::chrono::system_clock::to_time_t(now);

    std::stringstream ss;
    ss << std::put_time(std::localtime(&in_time_t), "%Y%m%d_%H%M%S");

    std::string filename = prefix + "_" + ss.str();
    if (!extension.empty()) {
        filename += "." + extension;
    }

    RCLCPP_INFO(get_logger(), "生成文件名: %s", filename.c_str());
    return filename;
}


void ObjPoseService::saveDataWithTimestamp(const std::string& base_path, 
                                           const cv::Mat& color_image, 
                                           const cv::Mat& depth_image, 
                                           const std::vector<pcl::PointCloud<pcl::PointXYZ>::Ptr>& clouds) {
    if (!fs::exists(base_path)) {
        fs::create_directories(base_path);
    }

    // 文件名（不含路径）
    std::string color_filename = getTimestampedFilename("color_image", "png");
    std::string depth_filename = getTimestampedFilename("aligned_depth_image", "png");

    // 拼接完整路径
    std::string color_fullpath = (fs::path(base_path) / color_filename).string();
    std::string depth_fullpath = (fs::path(base_path) / depth_filename).string();

    if (!color_image.empty()) {
        cv::imwrite(color_fullpath, color_image);
        RCLCPP_INFO(get_logger(), "Saved color image to %s", color_fullpath.c_str());
    }

    if (!depth_image.empty()) {
        cv::imwrite(depth_fullpath, depth_image);
        RCLCPP_INFO(get_logger(), "Saved aligned depth image to %s", depth_fullpath.c_str());
    }

    for(size_t i = 0; i < clouds.size(); ++i) {
        if (clouds[i] && !clouds[i]->empty()) {
            std::string cloud_filename = getTimestampedFilename("cloud_" + std::to_string(i), "ply");
            std::string cloud_fullpath = (fs::path(base_path) / cloud_filename).string();
            pcl::io::savePLYFileBinary(cloud_fullpath, *clouds[i]);
            RCLCPP_INFO(get_logger(), "Saved point cloud to %s", cloud_fullpath.c_str());
        }
    }
}

//////////////////////////////////////////////////////////


//////////////////////////////////////////////


void ObjPoseService::load_vision_config(const std::string &path)
{
    try
    {
        std::ifstream file(path);
        YAML::Node config = YAML::Load(file);

        // 目标TF
        target_frame_ = config["target_frame"].as<std::string>();
        flag_seg_by_cluster_ = config["flag_seg_by_cluster"].as<bool>();

        // 图像分割
        img_seg_cfg_ = {
            (size_t)config["image_segmentation"]["inst_num_max"].as<int>(),
            (size_t)config["image_segmentation"]["point_num_min"].as<int>(),
            (size_t)config["image_segmentation"]["point_num_max"].as<int>(),
            (size_t)config["image_segmentation"]["rect_area_min"].as<int>(),
            (size_t)config["image_segmentation"]["rect_area_max"].as<int>(),
            config["image_segmentation"]["inst_score_min"].as<double>()};

        // 深度相机
        dcamera_model_ = std::make_shared<DCameraModel>(config["camera_info"]["distortion_model"].as<std::string>(),
                                                        config["camera_info"]["D"].as<std::vector<double>>(),
                                                        config["camera_info"]["K"].as<std::vector<double>>(),
                                                        config["camera_info"]["P"].as<std::vector<double>>(),
                                                        config["camera_info"]["metric"].as<double>());

        // 位姿计算
        pose_estimator_ = std::make_shared<PoseEstimator>(config["pose_estimator"]["workspace"].as<std::vector<double>>(),
                                                          config["pose_estimator"]["leaf_size"].as<double>());
        pose_estimator_->set_obj_point_num(config["pose_estimator"]["point_num_min"].as<size_t>(),
                                           config["pose_estimator"]["point_num_max"].as<size_t>());
        pose_estimator_->set_obj_size(config["pose_estimator"]["obj_size_min"].as<std::vector<double>>(),
                                      config["pose_estimator"]["obj_size_max"].as<std::vector<double>>());
        pose_estimator_->set_cluster_tolerance(config["pose_estimator"]["cluster_tolerance"].as<double>());
    }
    catch (const YAML::Exception &e)
    {
        // 处理异常
        RCLCPP_ERROR(this->get_logger(), "Error while loading YAML file: %s", e.what());
    }
}

void ObjPoseService::pub_rviz_markers(int type, const std::vector<papjia_vision_interface::msg::Object> &objs)
{
    visualization_msgs::msg::MarkerArray marker_array;
    int marker_id = 0;
    for (auto obj : objs)
    {
        visualization_msgs::msg::Marker marker;
        marker.header.frame_id = target_frame_;
        marker.header.stamp = rclcpp::Clock().now();
        marker.ns = "papjia_vision_objs";
        marker.id = marker_id;
        marker_id += 1;
        marker.type = type;
        marker.action = visualization_msgs::msg::Marker::ADD;
        marker.pose = obj.pose;
        marker.scale = obj.scale;
        marker.color.a = 0.3; // Don't forget to set the alpha!
        marker.color.r = 0.0;
        marker.color.g = 1.0;
        marker.color.b = 0.0;
        marker_array.markers.push_back(marker);
    }
    if (marker_array.markers.size() > 0)
    {
        pub_markers_->publish(marker_array);
    }
}

bool ObjPoseService::callback_object_detect(const papjia_vision_interface::srv::DetectObjs::Request::SharedPtr request,
                                            papjia_vision_interface::srv::DetectObjs::Response::SharedPtr response)
{
    RCLCPP_INFO(get_logger(), "Begin object detect service");

// ========= 新增：生成一次检测的根目录 =========
    std::string timestamp = getTimestampedFilename("session", ""); // 例如 session_20250119_202350
    std::string session_dir = "/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data_point_images/" + timestamp;
    if (!fs::create_directories(session_dir)) {
        RCLCPP_ERROR(get_logger(), "无法创建检测数据目录: %s", session_dir.c_str());
        return false;
    }
    RCLCPP_INFO(get_logger(), "本次检测数据保存路径: %s", session_dir.c_str());
////////////////////////////////////////////

    // 取得彩色图像
    sensor_msgs::msg::Image::ConstSharedPtr rgb, depth;
    int max_fetch_times = 10;
    int time_internal = 500;
    bool flag_rgb = false;
    bool flag_depth = false;
    while (max_fetch_times--)
    {
        if (flag_sync_image_)
        {
            std::lock_guard<std::mutex> lock(datas_mutex_); // 锁定互斥量
            if (!datas_.empty())
            {
                rgb = datas_.back().rgb;
                depth = datas_.back().depth;
                flag_rgb = true;
                flag_rgb = true;
            }
            else
            {
                RCLCPP_WARN(get_logger(), "No sync images");
            }
        }
        else
        {
            {
                std::lock_guard<std::mutex> lock(rgbs_mutex_); // 锁定互斥量
                if (!flag_rgb && !rgbs_.empty())
                {
                    rgb = rgbs_.back();
                    flag_rgb = true;
                }
                else
                {
                    RCLCPP_WARN(get_logger(), "No rgb images");
                }
            }
            {
                std::lock_guard<std::mutex> lock(depths_mutex_); // 锁定互斥量
                if (!flag_depth && !depths_.empty())
                {
                    depth = depths_.back();
                    flag_depth = true;
                }
                else
                {
                    RCLCPP_WARN(get_logger(), "No depth images");
                }
            }
        }
        if (flag_depth && flag_rgb)
        {
            break;
        }
        else
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(time_internal)); // 暂停500毫秒
        }
    }

    // // 分割
    // 构造SegImage request
    auto seg_request = std::make_shared<papjia_vision_interface::srv::SegImage::Request>();
    if (request->max_num > 0)
        seg_request->max_num = request->max_num;
    else
        seg_request->max_num = img_seg_cfg_.inst_num_max;
    if (request->min_score > 0)
        seg_request->min_score = request->min_score;
    else
        seg_request->min_score = img_seg_cfg_.inst_score_min;
    seg_request->image = *rgb;
    auto seg_result_future = client_image_seg_->async_send_request(seg_request);
    // 等待响应
    // Do this instead of rclcpp::spin_until_future_complete(), client_image_seg_有专门的回调群
    std::future_status status = seg_result_future.wait_for(2s); // timeout to guarantee a graceful finish
    if (status == std::future_status::ready)
    {
        auto result = seg_result_future.get();
        RCLCPP_INFO(get_logger(), "Insts num: %ld", result->objs_num);
        if (result->objs_num == 0) {
            response->success = true;
            return true;
        }
        
        for (size_t i = 0; i < result->objs_num; ++i)
        {
            RCLCPP_INFO(get_logger(), "inst-%ld category(%s), score(%.3lf)",
                        i, result->objects.objects[i].category.c_str(), result->objects.objects[i].score);
        }
        // 转化图像
        cv_bridge::CvImagePtr cv_ptr;
        cv::Mat img_depth, img_mask;
        std::vector<PointCloudT::Ptr> clouds;
        cv_ptr = cv_bridge::toCvCopy(depth, "16UC1");
        cv_ptr->image.copyTo(img_depth);
        // to_do
        // 保存深度图像【img_depth】
        // if (result->with_mask)
        // {
        //     cv_ptr = cv_bridge::toCvCopy(result->mask, "8UC1");
        //     cv_ptr->image.copyTo(img_mask);
        //     // 深度转点云
        //     dcamera_model_->depth_to_pointclouds(img_depth, img_mask, clouds, result->objs_num);
        //     // 调用保存函数
        //     saveDataWithTimestamp(session_dir, cv_bridge::toCvShare(rgb, "bgr8")->image, img_depth, clouds);

        // }
        if (result->with_mask)
        {
            // 1. 将 ROS 掩码消息转为 cv::Mat
            cv_ptr = cv_bridge::toCvCopy(result->mask, "8UC1");
            cv_ptr->image.copyTo(img_mask);

            // ======== 新增：创建并保存掩码叠加图 ========
            try
            {
                // 2. 将 ROS RGB 图像消息转为 cv::Mat (用于叠加)
                cv::Mat img_rgb = cv_bridge::toCvShare(rgb, "bgr8")->image;

                // 3. 创建一个彩色的掩码 (这里使用半透明的红色)
                //    a. 创建一个全黑的彩色图像
                cv::Mat color_mask_overlay = cv::Mat::zeros(img_rgb.size(), CV_8UC3);
                //    b. 在 img_mask (8UC1) 中像素值 > 0 的地方，将 color_mask_overlay 设为红色 (B=0, G=0, R=255)
                color_mask_overlay.setTo(cv::Scalar(0, 0, 255), img_mask > 0); 
                
                // 4. 将彩色掩码和原图叠加
                cv::Mat overlayed_image;
                double alpha = 0.5; // 掩码的透明度 (50%)
                cv::addWeighted(img_rgb, 1.0, color_mask_overlay, alpha, 0.0, overlayed_image);

                // 5. 保存叠加后的图像
                //    使用您已有的函数生成带时间戳的文件名
                std::string overlay_filename = getTimestampedFilename("overlay_mask", "png");
                std::string overlay_fullpath = (fs::path(session_dir) / overlay_filename).string();
                cv::imwrite(overlay_fullpath, overlayed_image);
                RCLCPP_INFO(get_logger(), "✅ 已保存掩码叠加图到: %s", overlay_fullpath.c_str());
            }
            catch (const cv_bridge::Exception& e)
            {
                RCLCPP_ERROR(get_logger(), "cv_bridge 转换失败: %s", e.what());
            }
            catch (const std::exception& e)
            {
                RCLCPP_ERROR(get_logger(), "保存掩码叠加图失败: %s", e.what());
            }
            // ============================================

            // 深度转点云 (您原有的代码)
            dcamera_model_->depth_to_pointclouds(img_depth, img_mask, clouds, result->objs_num);
            
            // 调用保存函数 (您原有的代码，保存原始彩色图、深度图和点云)
            saveDataWithTimestamp(session_dir, cv_bridge::toCvShare(rgb, "bgr8")->image, img_depth, clouds);
        }
            // to_do
            // 保存彩色图像
            // 保存深度图像
            // 保存点云【无rgb】

        else
        {
            std::vector<std::vector<int>> rects;
            for (size_t i = 0; i < result->objs_num; ++i)
            {
                std::vector<int> rect(4);
                auto &box = result->objects.objects[i].rect;
                rect[0] = box.x1;
                rect[1] = box.y1;
                rect[2] = box.x2;
                rect[3] = box.y2;
                rects.push_back(rect);
            }
            dcamera_model_->depth_to_pointclouds(img_depth, rects, clouds);
        }
        RCLCPP_INFO(get_logger(), "得到 %ld 个物体点云", clouds.size());

        // 测试整体点云转换
        if (flag_pub_cloud_transformed_)
        {
            PointCloudT::Ptr fcloud(new PointCloudT);
            pcl::PCLPointCloud2 cloud2;
            sensor_msgs::msg::PointCloud2 cloud_msg;
            dcamera_model_->depth_to_pointcloud(img_depth, fcloud);
            pcl::toPCLPointCloud2(*fcloud, cloud2);
            pcl_conversions::fromPCL(cloud2, cloud_msg);
            cloud_msg.header = depth->header;
            pub_cloud_->publish(cloud_msg);
        }

        // 坐标转换
        geometry_msgs::msg::TransformStamped transform_stamped;
        Eigen::Affine3d transform;
        try
        {
            // 查询从 source_frame 到 target_frame 的变换
            transform_stamped = tf_buffer_->lookupTransform(
                target_frame_,          // 替换成目标坐标系
                depth->header.frame_id, // 使用点云消息中的源坐标系
                tf2::TimePoint(),
                500ms);
            Eigen::Translation3d translation(transform_stamped.transform.translation.x,
                                             transform_stamped.transform.translation.y,
                                             transform_stamped.transform.translation.z);
            Eigen::Quaterniond rotation(transform_stamped.transform.rotation.w,
                                        transform_stamped.transform.rotation.x,
                                        transform_stamped.transform.rotation.y,
                                        transform_stamped.transform.rotation.z);
            transform = translation * rotation;
            RCLCPP_INFO(get_logger(), "得到 %s -> %s 的转换矩阵", depth->header.frame_id.c_str(), target_frame_.c_str());
        }
        catch (tf2::TransformException &ex)
        {
            RCLCPP_ERROR(this->get_logger(), "Transform not ready");
        }

        for (size_t i = 0; i < result->objs_num; ++i)
        {
            PointCloudT::Ptr cloud = clouds[i];
            if (cloud->size() <= 500)
            {
                continue;
            }
            PointCloudT::Ptr cloud_target(new PointCloudT), cloud_downsample(new PointCloudT);
            pcl::transformPointCloud(*cloud, *cloud_target, transform);
            RCLCPP_INFO(get_logger(), "转换点云到 %s", target_frame_.c_str());
            std::vector<PointCloudT::Ptr> clusters;
            pose_estimator_->downsample(cloud_target, cloud_downsample);
            if (flag_seg_by_cluster_)
            {
                if (cloud_downsample->size() <= 500)
                {
                    continue;
                }
                pose_estimator_->seg_by_cluster_extraction(cloud_downsample, clusters);
                RCLCPP_INFO(get_logger(), "聚类分割 1 -> %ld", clusters.size());
            }
            else
            {
                clusters.push_back(cloud_downsample);
            }
            if (clusters.size() > 0)
            {
                PointCloudT::Ptr cluster_downsample(new PointCloudT);
                pose_estimator_->downsample(clusters[0], cluster_downsample);
                RCLCPP_INFO(get_logger(), "降采样 %ld -> %ld", clusters[0]->size(), cluster_downsample->size());
                PointT min_point, max_point;
                pcl::getMinMax3D(*cluster_downsample, min_point, max_point);
                // 判断是否在空间内
                if (!pose_estimator_->is_valid_range(min_point, max_point))
                    continue;
                // 判断物体大小是否符合设定范围
                if (!pose_estimator_->is_valid_size(min_point, max_point))
                    continue;
                papjia_vision_interface::msg::Object obj;
                if (flag_use_pca_pose_)
                {
                    PointCloudT::Ptr cloud_pca(new PointCloudT);
                    Eigen::Matrix4d transform_pca;
                    Eigen::Vector4d pca_centroid;
                    Eigen::Quaterniond pca_quat;
                    pose_estimator_->pca_transform_z(cluster_downsample, cloud_pca, transform_pca, pca_centroid, pca_quat);
                    RCLCPP_INFO(get_logger(), "PCA位姿 (%.3lf, %.3lf, %.3lf) (%.3lf, %.3lf, %.3lf, %.3lf)",
                                pca_centroid(0), pca_centroid(1), pca_centroid(2),
                                pca_quat.x(), pca_quat.y(), pca_quat.z(), pca_quat.w());
                    pcl::getMinMax3D(*cloud_pca, min_point, max_point);
                    obj.category = result->objects.objects[i].category;
                    obj.scale.x = max_point.x - min_point.x;
                    obj.scale.y = max_point.y - min_point.y;
                    obj.scale.z = max_point.z - min_point.z;
                    obj.pose.position.x = pca_centroid(0);
                    obj.pose.position.y = pca_centroid(1);
                    obj.pose.position.z = pca_centroid(2);
                    obj.pose.orientation.w = pca_quat.w();
                    obj.pose.orientation.x = pca_quat.x();
                    obj.pose.orientation.y = pca_quat.y();
                    obj.pose.orientation.z = pca_quat.z();
                }
                else
                {
                    obj.category = result->objects.objects[i].category;
                    obj.scale.x = max_point.x - min_point.x;
                    obj.scale.y = max_point.y - min_point.y;
                    obj.scale.z = max_point.z - min_point.z;
                    obj.pose.position.x = (max_point.x + min_point.x) / 2.0;
                    obj.pose.position.y = (max_point.y + min_point.y) / 2.0;
                    obj.pose.position.z = (max_point.z + min_point.z) / 2.0;
                    obj.pose.orientation.w = 1.0;
                    obj.pose.orientation.x = 0.0;
                    obj.pose.orientation.y = 0.0;
                    obj.pose.orientation.z = 0.0;
                }
                response->objects.push_back(obj);
                RCLCPP_INFO(this->get_logger(), "物体 %s 大小[%.3lf, %.3lf, %.3lf]", obj.category.c_str(), obj.scale.x, obj.scale.y, obj.scale.z);
                // to_do
                // 保存类别【obj.category】大小【obj.scale】位姿【obj.pose】过滤后点云簇【cluster_downsample】物体原始点云【cloud_target】
            ////////////////////////////////////////////////////
                 try
                {
                    std::string obj_dir = session_dir + "/object_" + std::to_string(i);
                    fs::create_directories(obj_dir);
                    // 1. 保存原始物体点云（已变换）                    
                    std::string cloud_target_path = obj_dir + "/cloud_target.ply";
                    pcl::io::savePLYFileBinary(cloud_target_path, *cloud_target);  

                    // 2. 保存降采样后的点云簇
                    std::string cluster_path = obj_dir + "/cluster_downsampled.ply";
                    pcl::io::savePLYFileBinary(cluster_path, *cluster_downsample);          

                    // 3. 保存 JSON 元数据
                    std::string json_path = obj_dir + "/info.json";
                    json info_json;
                    info_json["category"] = obj.category;
                    info_json["scale"] = {obj.scale.x, obj.scale.y, obj.scale.z};
                    info_json["pose"] = {
                        {"position", {
                            {"x", obj.pose.position.x},
                            {"y", obj.pose.position.y},
                            {"z", obj.pose.position.z}
                        }},
                        {"orientation", {
                            {"w", obj.pose.orientation.w},
                            {"x", obj.pose.orientation.x},
                            {"y", obj.pose.orientation.y},
                            {"z", obj.pose.orientation.z}
                        }}
                    };
                    info_json["timestamp"] = timestamp;
                    info_json["source_index"] = i;

                    std::ofstream json_file(json_path);                
                    json_file << info_json.dump(4);
                    json_file.close();
                    RCLCPP_INFO(get_logger(), "✅ 保存物体 %zu 数据到 %s", i, obj_dir.c_str());
                   
                }
                catch (const std::exception& e)
                {
                    RCLCPP_ERROR(get_logger(), "保存物体 %zu 数据时发生异常: %s", i, e.what());
                }
            } // end for

            RCLCPP_INFO(get_logger(), "✅ 所有物体数据已保存至: %s", session_dir.c_str());
            //////////////////////////////////////////////////
            
        }
        response->success = true;
        pub_rviz_markers(visualization_msgs::msg::Marker::CUBE, response->objects);
        RCLCPP_INFO(this->get_logger(), "发布物体MarkerArray");
    }
    else
    {
        RCLCPP_ERROR(get_logger(), "service %s timeout", service_image_seg_.c_str());
        return true;
    }
    return true;
}

void ObjPoseService::callback_image_rgb(const sensor_msgs::msg::Image::ConstSharedPtr &msg)
{
    {
        std::lock_guard<std::mutex> lock(rgbs_mutex_); // 锁定互斥量
        rgbs_.clear();
        rgbs_.push_back(msg);
    }
    RCLCPP_DEBUG(this->get_logger(), "Rev rgb image with (%d x %d)", msg->width, msg->width);
}

void ObjPoseService::callback_image_depth(const sensor_msgs::msg::Image::ConstSharedPtr &msg)
{
    {
        std::lock_guard<std::mutex> lock(depths_mutex_); // 锁定互斥量
        depths_.clear();
        depths_.push_back(msg);
    }
    RCLCPP_DEBUG(this->get_logger(), "Rev depth image with (%d x %d)", msg->width, msg->width);
}

void ObjPoseService::image_callback(const sensor_msgs::msg::Image::ConstSharedPtr &msg1, const sensor_msgs::msg::Image::ConstSharedPtr &msg2)
{

    CombinedData data;
    data.depth = msg1;
    data.rgb = msg2;
    {
        std::lock_guard<std::mutex> lock(datas_mutex_); // 锁定互斥量
        datas_.clear();
        datas_.push_back(data);
    }
    RCLCPP_DEBUG(this->get_logger(), "Rev rgb/depth image with (%d x %d)", msg1->width, msg1->width);
}

#include "rclcpp_components/register_node_macro.hpp"

// Register the component with class_loader.
// This acts as a sort of entry point, allowing the component to be discoverable when its library
// is being loaded into a running process.
RCLCPP_COMPONENTS_REGISTER_NODE(ObjPoseService)