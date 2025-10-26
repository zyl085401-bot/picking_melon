cmake_minimum_required(VERSION 3.8)
project(papjia_move_behavior)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(papjia_behavior_tree REQUIRED)
find_package(pluginlib REQUIRED)
find_package(papjia_move_msgs REQUIRED)

pluginlib_export_plugin_description_file(papjia_behavior_tree plugin.xml)

set(
  THIS_PACKAGE_INCLUDE_DEPENDS
  behaviortree_cpp
  papjia_behavior_tree
  pluginlib
  papjia_move_msgs
)

add_library(papjia_move_behavior SHARED
  src/papjia_move_behavior_client.cpp
  src/register_behavior.cpp
)

target_include_directories(papjia_move_behavior PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(papjia_move_behavior PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
ament_target_dependencies(
  papjia_move_behavior
  ${THIS_PACKAGE_INCLUDE_DEPENDS}
)

target_compile_definitions(papjia_move_behavior PRIVATE "PAPJIA_MOVE_HEAVIOR_BUILDING_LIBRARY")

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
  TARGETS papjia_move_behavior
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
  papjia_move_behavior
)
ament_export_targets(
  export_${PROJECT_NAME}
)

ament_package()
