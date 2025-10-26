cmake_minimum_required(VERSION 3.8)
project(papjia_melon_behaviors)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_ros REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(papjia_behavior_tree REQUIRED)
find_package(papjia_melon_interface REQUIRED)
find_package(papjia_vision_interface REQUIRED)
find_package(papjia_mtc_bt REQUIRED)
find_package(moveit_simple_controller_manager REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(pluginlib REQUIRED)
pluginlib_export_plugin_description_file(papjia_behavior_tree plugins.xml)

set(
  THIS_PACKAGE_INCLUDE_DEPENDS
  papjia_behavior_tree
  papjia_melon_interface
  papjia_vision_interface
  papjia_mtc_bt
  tf2_ros
  tf2
  pluginlib
)

add_library(papjia_melon_behaviors
  src/control_gripper_client.cpp 
  src/control_shears_client.cpp
  src/action_nodes.cpp
  src/register_behavior.cpp 
)
target_include_directories(papjia_melon_behaviors PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(
  papjia_melon_behaviors
  "papjia_behavior_tree"
  "papjia_melon_interface"
  "papjia_vision_interface"
  "papjia_mtc_bt"
  "pluginlib"
  "tf2_ros"
)

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(papjia_melon_behaviors PRIVATE "PAPJIA_MELON_HEAVIORS_BUILDING_LIBRARY")

install(
  DIRECTORY
    config
  DESTINATION
    share/${PROJECT_NAME}
)


install(
  DIRECTORY include/
  DESTINATION include
)
install(
  TARGETS papjia_melon_behaviors
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_export_include_directories(
  include
)

ament_export_libraries(
  papjia_melon_behaviors
)
ament_export_targets(
  export_${PROJECT_NAME}
)

ament_package()

