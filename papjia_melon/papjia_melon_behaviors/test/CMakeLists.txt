find_package(ament_cmake_gtest REQUIRED)

ament_add_gtest(
    test_behavior_plugins
    test_behavior_plugins.cpp
)
target_link_libraries(test_behavior_plugins)
ament_target_dependencies(test_behavior_plugins ${THIS_PACKAGE_INCLUDE_DEPENDS} )
