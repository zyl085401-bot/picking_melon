cmake_minimum_required(VERSION 3.8)
cmake_policy(SET CMP0074 NEW)         # 启用新行为
project(papjia_pose)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(papjia_vision_interface REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(message_filters REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(OpenCV REQUIRED)
find_package(PCL REQUIRED)
find_package(yaml-cpp REQUIRED)

include_directories(
  include 
  ${OpenCV_INCLUDE_DIRS} 
  ${YAML_CPP_INCLUDE_DIR}
  ${PCL_INCLUDE_DIRS}
)

add_definitions(${PCL_DEFINITIONS})

add_library(obj_pose_component SHARED
  src/obj_pose.cpp)
target_link_libraries(obj_pose_component yaml-cpp ${PCL_LIBRARIES})
target_compile_definitions(obj_pose_component
  PRIVATE "COMPOSITION_BUILDING_DLL")
set(dependencies rclcpp rclcpp_components sensor_msgs papjia_vision_interface message_filters cv_bridge tf2_ros tf2 pcl_conversions visualization_msgs)
ament_target_dependencies(obj_pose_component ${dependencies})
rclcpp_components_register_nodes(obj_pose_component "ObjPoseService")
set(node_plugins "${node_plugins}ObjPoseService;$<TARGET_FILE:obj_pose_component>\n")

install(TARGETS
  obj_pose_component # 库文件
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

add_executable(${PROJECT_NAME}_node src/main.cpp)
target_link_libraries(${PROJECT_NAME}_node obj_pose_component)
set(dependencies rclcpp sensor_msgs papjia_vision_interface message_filters cv_bridge tf2_ros tf2 pcl_conversions)
ament_target_dependencies(${PROJECT_NAME}_node ${dependencies})
install(TARGETS
  ${PROJECT_NAME}_node # 执行程序
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch # launch
  DESTINATION share/${PROJECT_NAME}
)

install(
  DIRECTORY config # launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
