find_package(ament_cmake_gtest REQUIRED)

ament_add_gtest(
    test_move_straight
    test_move_straight.cpp
)
target_link_libraries(test_move_straight)
ament_target_dependencies(test_move_straight ${THIS_PACKAGE_INCLUDE_DEPENDS} )
