cmake_minimum_required(VERSION 3.8)
project(duco_hardware_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

# include DucoCobot API
include_directories(
  include 
)
link_directories(
  lib
)

set(THIS_PACKAGE_INCLUDE_DEPENDS
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

add_library(duco_hardware_interface
  SHARED
  src/duco_hardware_interface.cpp
)
target_link_libraries(duco_hardware_interface DucoCobotAPI)
ament_target_dependencies(duco_hardware_interface ${THIS_PACKAGE_INCLUDE_DEPENDS}
)
target_include_directories(duco_hardware_interface
  PRIVATE
  include
)
# prevent pluginlib from using boost
target_compile_definitions(duco_hardware_interface PUBLIC "PLUGINLIB__DISABLE_BOOST_FUNCTIONS")

pluginlib_export_plugin_description_file(
  hardware_interface duco_hardware_interface.xml)

install(
  TARGETS
  duco_hardware_interface
  RUNTIME DESTINATION bin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  PROGRAMS lib/libDucoCobotAPI.so
  DESTINATION lib
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  add_subdirectory(test)
endif()

ament_export_include_directories(
  include
)
ament_export_libraries(
  duco_hardware_interface
)
ament_export_dependencies(
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

ament_package()
