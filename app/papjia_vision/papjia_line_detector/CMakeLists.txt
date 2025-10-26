cmake_minimum_required(VERSION 3.8)
project(papjia_line_detector)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(papjia_vision_interface REQUIRED)
find_package(OpenCV REQUIRED)
include_directories(include ${OpenCV_INCLUDE_DIRS})

add_library(line_seg_component SHARED
  src/line_detector.cpp)
target_compile_definitions(line_seg_component
  PRIVATE "COMPOSITION_BUILDING_DLL")
set(dependencies rclcpp rclcpp_components sensor_msgs papjia_vision_interface cv_bridge)
ament_target_dependencies(line_seg_component ${dependencies})
rclcpp_components_register_nodes(line_seg_component "LineDetectorService")
set(node_plugins "${node_plugins}LineDetectorService;$<TARGET_FILE:line_seg_component>\n")

install(TARGETS
  line_seg_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(
  DIRECTORY include/ # 头文件
  DESTINATION include/${PROJECT_NAME}
)
ament_export_include_directories("include/${PROJECT_NAME}") #不可缺少，头文件

install(
  DIRECTORY launch # launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(${PROJECT_NAME}_pose_test test/test_pose.cpp)
  target_include_directories(${PROJECT_NAME}_pose_test PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
  )
  target_link_libraries(${PROJECT_NAME}_pose_test ${OpenCV_LIBS})
  ament_target_dependencies(${PROJECT_NAME}_pose_test
    rclcpp
    std_msgs
    papjia_vision_interface
    cv_bridge
  )

  ament_add_gtest(${PROJECT_NAME}_seg_test test/test_seg.cpp)
  target_include_directories(${PROJECT_NAME}_seg_test PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
  )
  target_link_libraries(${PROJECT_NAME}_seg_test ${OpenCV_LIBS})
  ament_target_dependencies(${PROJECT_NAME}_seg_test
    rclcpp
    std_msgs
    papjia_vision_interface
    cv_bridge
  )
endif()

ament_package()
