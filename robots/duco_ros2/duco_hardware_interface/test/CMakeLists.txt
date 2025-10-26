find_package(ament_cmake_gtest REQUIRED)

# test_duco_cobot_api
ament_add_gtest(test_duco_cobot_api test_duco_cobot_api.cpp)
target_include_directories(test_duco_cobot_api PRIVATE ../include)

ament_target_dependencies(test_duco_cobot_api)
target_link_libraries(test_duco_cobot_api DucoCobotAPI)

# # test nw_client
# ament_add_gtest(test_nw_client nw_client/test_nw_client.cpp)
# target_include_directories(test_nw_client PRIVATE ../src)

# ament_target_dependencies(test_nw_client)
# target_link_libraries(test_nw_client nw_client)

# # test nw_client
# ament_add_gmock(test_nw_hardware_interface test_nw_hardware_interface.cpp)
# target_include_directories(test_nw_hardware_interface PRIVATE ../include)
# ament_target_dependencies(
#     test_nw_hardware_interface
#     hardware_interface
#     pluginlib
#     ros2_control_test_assets
# )