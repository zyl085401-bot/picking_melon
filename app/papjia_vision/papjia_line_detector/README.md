<!--
 * @Descripttion: ROS2 C++ Package说明
 * @version: 1.0
 * @Author: 崔译文
 * @Date: 2023-12-25 17:44:08
 * @LastEditors: 崔译文
 * @LastEditTime: 2024-01-10 10:47:37
-->

## 头文件

- service 以及 msg 文件对应的头文件是小写的，如`SegImage.srv`对应的头文件为`seg_image.hpp`
- 导出头文件（可以被其他包使用），在 CMakeLists.txt 中添加

```
install(
  DIRECTORY include/
  DESTINATION include/${PROJECT_NAME}
)
ament_export_include_directories("include/${PROJECT_NAME}")
```

## 服务/消息生成

- 服务或者消息生成，CMakeLists.txt 中需要添加

```
rosidl_generate_interfaces(${PROJECT_NAME} # 必须使用rosidl_generate_interfaces和${PROJECT_NAME}
  "msg/Object.msg"
  "msg/Rect.msg"
  "srv/SegImage.srv"
  "srv/DetectObjs.srv"
  "srv/DetectLine.srv"
  DEPENDENCIES geometry_msgs sensor_msgs # 必须添加依赖，即自定义服务中的类型依赖的ROS包
)
```

此外，package.xml 中需要添加

```
  <build_depend>rosidl_default_generators</build_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
```

## 包依赖
- 非ROS包，头文件以及库依赖和一般的 CMakeLists.txt 相同，例子如下

```
find_package(OpenCV REQUIRED) # 查找OpenCV依赖配置
include_directories(include ${OpenCV_INCLUDE_DIRS}) # OpenCV头文件
add_executable(${PROJECT_NAME}_node src/line_detector.cpp)
target_link_libraries(${PROJECT_NAME}_node ${OpenCV_LIBS}) # OpenCV库文件依赖
```

- ROS 包的依赖必须添加，使用 ament_target_dependencies，如下

```
set(dependencies rclcpp sensor_msgs papjia_vision_interface cv_bridge OpenCV)
ament_target_dependencies(${PROJECT_NAME}_node ${dependencies}) # 使用ament_target_dependencies添加ROS包依赖
```

# launch文件生效
- 配置 launch 文件，在 CMakeLists.txt 中添加

```
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
```

## 测试

- 需要修改 package.xml 文件，添加

```
<test_depend>ament_cmake_gtest</test_depend>
```

- 需要修改 CMakeLists.txt 文件，下面是一个例子（service_test.cpp 对应的编译配置）

```
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED) # 必须有
  ament_add_gtest(${PROJECT_NAME}_test test/service_test.cpp) # 必须有，service_test.cpp为测试代码
  target_include_directories(${PROJECT_NAME}_test PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
  ) # 必须有
  target_link_libraries(${PROJECT_NAME}_test ${OpenCV_LIBS}) # 有ROS外的依赖时必须有
  ament_target_dependencies(${PROJECT_NAME}_test
    rclcpp
    std_msgs
    papjia_vision_interface
    cv_bridge
  ) # 依赖的ROS包使用ament_target_dependencies
endif()
```

- 进入工作空间根目录，运行下面的命令进行测试

```
colcon test --packages-select papjia_line_detector --event-handlers console_cohesion+ --ctest-args tests
```

# LOG 颜色

- 使用 launch 启动的节点，需要添加特殊的配置才能输出彩色 log，下面是一个例子

```
node = Node(
        package="papjia_line_detector",
        name="papjia_line_node",
        executable="papjia_line_detector_node",
        output="screen",
        emulate_tty=True, # 需要添加这个设置
        parameters=[
            {
                "line_service_topic": "/papjia_detector/line_detect_service",
                "topic_image_line": "/papjia_detector/line_result",
                "flag_pub_line": True,
            }
        ],
    )
```

## 组合节点
- launch编写参考文件```line.launch.py```
- CMakeLists.txt需要添加插件，下面是一个例子
```
find_package(rclcpp_components REQUIRED) # 需要rclcpp_components

add_library(line_seg_component SHARED # line_seg_component为生成库的名字
  src/line_detector.cpp)
target_link_libraries(line_seg_component spdlog::spdlog) ## 非ROS依赖
target_compile_definitions(line_seg_component
  PRIVATE "COMPOSITION_BUILDING_DLL") # 需要添加COMPOSITION_BUILDING_DLL
set(dependencies rclcpp rclcpp_components sensor_msgs papjia_vision_interface cv_bridge)
ament_target_dependencies(line_seg_component ${dependencies}) # ROS依赖
rclcpp_components_register_nodes(line_seg_component "LineDetectorService") # LineDetectorService为类名
set(node_plugins "${node_plugins}LineDetectorService;$<TARGET_FILE:line_seg_component>\n") # 需要类名和库文件
```
- 代码编写例子见```line_detector.hpp```和```line_detector.cpp```
