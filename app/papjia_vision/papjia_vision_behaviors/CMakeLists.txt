cmake_minimum_required(VERSION 3.8)
project(papjia_vision_behaviors)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_ros REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(papjia_behavior_tree REQUIRED)
find_package(papjia_vision_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)

pluginlib_export_plugin_description_file(papjia_behavior_tree papjia_vision_behaviors_plugin.xml)

set(
  THIS_PACKAGE_INCLUDE_DEPENDS
  papjia_behavior_tree
  papjia_vision_interface
  pluginlib
  cv_bridge
)

add_library(papjia_vision_behaviors SHARED
  src/camera_info_get_from_topic_action.cpp
  src/image_get_from_topic_action.cpp
  src/image_save_to_file_action.cpp
  src/object_detect_service_client.cpp
  src/mask_detect_service_client.cpp
  src/tags_detect_service_client.cpp
  src/image_fetch_service_client.cpp
  src/fetch_camera_service_client.cpp
  src/crop_image_msg_action.cpp
  src/register_behavior.cpp 
)
target_include_directories(papjia_vision_behaviors PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${OpenCV_INCLUDE_DIRS}
)
ament_target_dependencies(
  papjia_vision_behaviors
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

target_link_libraries(papjia_vision_behaviors
  ${OpenCV_LIBRARIES}
)

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(papjia_vision_behaviors PRIVATE "PAPJIA_VISION_BEHAVIORS_BUILDING_LIBRARY")

install(
  DIRECTORY
    config launch
  DESTINATION
    share/${PROJECT_NAME}
)


install(
  DIRECTORY include/
  DESTINATION include
)
install(
  TARGETS papjia_vision_behaviors
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  add_subdirectory(test)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_include_directories(
  include
)

ament_export_libraries(
  papjia_vision_behaviors
)
ament_export_targets(
  export_${PROJECT_NAME}
)

ament_package()
