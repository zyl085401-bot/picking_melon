cmake_minimum_required(VERSION 3.8)
project(type_trans_behaviors)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(pluginlib REQUIRED)
find_package(papjia_behavior_tree REQUIRED)
find_package(papjia_vision_interface REQUIRED)
find_package(cv_bridge REQUIRED)

pluginlib_export_plugin_description_file(papjia_behavior_tree ${PROJECT_NAME}_plugin.xml)

set(
  THIS_PACKAGE_INCLUDE_DEPENDS
  papjia_behavior_tree
  behaviortree_cpp
  pluginlib
  papjia_vision_interface
)

add_library(${PROJECT_NAME} SHARED
  src/objects2d_to_json_action.cpp
  src/objects_to_json_action.cpp
  src/json_to_object_action.cpp
  src/remove_escape_charater_action.cpp
  src/get_object_from_dbjson_action.cpp
  src/pose_stamped_to_json_action.cpp
  src/register_behavior.cpp 
)
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(
  ${PROJECT_NAME}
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(${PROJECT_NAME} PRIVATE "PAPJIA_VISION_HEAVIORS_BUILDING_LIBRARY")

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
  TARGETS ${PROJECT_NAME}
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
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
