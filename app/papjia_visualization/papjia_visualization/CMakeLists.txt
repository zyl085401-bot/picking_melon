cmake_minimum_required(VERSION 3.8)
project(papjia_visualization)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(papjia_visualization_interface REQUIRED)

# 引入头文件夹
include_directories(include)

# 添加可执行文件
add_executable(papjia_visualization_service
  src/visualization_service.cpp
)

# 添加依赖
ament_target_dependencies(papjia_visualization_service
  rclcpp
  visualization_msgs
  geometry_msgs
  papjia_visualization_interface
)

# 安装可执行文件
install(TARGETS papjia_visualization_service
  DESTINATION lib/${PROJECT_NAME}
)

# 添加launch文件
install(DIRECTORY launch
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
