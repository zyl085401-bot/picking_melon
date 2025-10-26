<!--
 * @Descripttion: 节点说明文档
 * @version: 2.0
 * @Author: 崔译文
 * @Date: 2023-12-20 12:43:25
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-05-12 17:13:19
-->

## 创建

- 使用命令`ros2 pkg create --build-type ament_python --node-name papjia_mask_node papjia_detector --dependencies sensor_msgs std_msgs`创建此包

## 启动

- 需要先`source`动作空间下的`install/setup.bash`文件，工作空间，即执行`colcon build`命令的目录
- 使用`ros2 launch papjia_detector mask.launch.py`启动服务

## 测试

- 进入工作空间，即执行`colcon build`命令的目录
- 使用`colcon test --packages-select papjia_detector --event-handlers console_cohesion+ --pytest-args -s -k test_service_sync`测试服务是否正常工作
- 也可以使用`colcon test --packages-select papjia_detector --pytest-args -s -k test_service_async`测试服务是否正常工作


## 线筒Line测试
- 从```https://papjia.coding.net/p/papjia_pickplace/files/all```下载模型文件```model_line.jit```，将其放在目录```papjia_detector/resource```中
- 修改```papjia_detector/config/net.yaml```文件，将字段```data_root```修改为目录```papjia_detector/resource```的绝对路径
- 使用`ros2 launch papjia_detector mask.launch.py`启动服务
- ```test_service_async```和```test_service_sync```有测试的样例代码
- 结果的可视化图像发布在```/papjia_vision/service_image_segment/result_image```

## YOLO5
- 需要从```https://papjia.coding.net/p/papjia_pickplace/files/all```下载yolov5并解压，下载```ripeness.pt```和```picking.pt```到目录```papjia_detector/resource/weights```
- 将```papjia_detector/papjia_detector/yolo.py```中```sys.path.append("/workspace/yolov5")```修改为你自己的yolov5的路径
- 使用```ros2 launch papjia_detector yolo.launch.py model_path:=weights/model_loofah_ripeness.pt```启动成熟度识别
