<!--
 * @Descripttion: 位姿估计说明
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2024-01-19 11:01:50
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-19 11:12:15
-->
# 位姿估计有插件形式，即组合节点，但实际运行的为多线程执行器
# 文件说明
- obj_pose.hpp，物体的位姿估计服务提供者
- dcamera.hpp，深度相机模型，将深度图像转化为点云
- pose_estimator.hpp，根据点云估计物体位姿

# 运行
- 开启相机图像（测试，注意图像路径），运行```ros2 launch papjia_detector image_pub.launch.py```
- 开启TF（测试），运行```ros2 launch papjia_pose tf.launch.py```
- 开启位姿估计服务，运行```ros2 launch papjia_pose pose.launch.py```
- 调用位姿估计服务，运行```ros2 service call /papjia_vision/service_object_detect papjia_vision_interface/srv/DetectObjs```