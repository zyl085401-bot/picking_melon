find_package(ament_cmake_gtest REQUIRED)

ament_add_gtest(
    test_vision_behavior_plugins
    test_vision_behavior_plugins.cpp
)
target_link_libraries(test_vision_behavior_plugins)
ament_target_dependencies(test_vision_behavior_plugins ${THIS_PACKAGE_INCLUDE_DEPENDS} )

ament_add_gtest(
    test_vision_behavior_mask_detect
    test_vision_behavior_mask_detect.cpp
)
target_link_libraries(test_vision_behavior_mask_detect)
ament_target_dependencies(test_vision_behavior_mask_detect ${THIS_PACKAGE_INCLUDE_DEPENDS} )

ament_add_gtest(
    test_image_get_and_save
    test_image_get_and_save.cpp
)
target_link_libraries(test_image_get_and_save)
ament_target_dependencies(test_image_get_and_save ${THIS_PACKAGE_INCLUDE_DEPENDS} )

ament_add_gtest(
    test_camera_info_get
    test_camera_info_get.cpp
)
target_link_libraries(test_camera_info_get)
ament_target_dependencies(test_camera_info_get ${THIS_PACKAGE_INCLUDE_DEPENDS} )

ament_add_gtest(
    test_vision_behavior_tags_detect
    test_vision_behavior_tags_detect.cpp
)
target_link_libraries(test_vision_behavior_tags_detect)
ament_target_dependencies(test_vision_behavior_tags_detect ${THIS_PACKAGE_INCLUDE_DEPENDS} )