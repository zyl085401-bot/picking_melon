#include <gtest/gtest.h>

#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/node.hpp>

#include <papjia_behavior_tree/papjia_behavior_tree.hpp>


TEST(VisionBehaviorTests, test_vision_behavior_plugins)
{
    pluginlib::ClassLoader<papjia::behavior_tree::SharedResourcesNodeLoaderBase> class_loader(
        "papjia_behavior_tree", "papjia::behavior_tree::SharedResourcesNodeLoaderBase");

    auto node = std::make_shared<rclcpp::Node>("test_node");
    auto shared_resources = std::make_shared<papjia::behavior_tree::BehaviorContext>(node);

    BT::BehaviorTreeFactory factory;
    {   
        
        auto plugin_instance = class_loader.createSharedInstance("papjia::behaviors::VisionBehaviorLoader");
        try {
            plugin_instance->registerBehaviors(factory, shared_resources);
        } catch (const std::exception& e) {
            std::cerr << "Exception caught: " << e.what() << std::endl;
        }
        ASSERT_THROW(plugin_instance->registerBehaviors(factory, shared_resources), std::exception);
    }

    // factory.instantiateTreeNode("test_behavior_name", "ObjectDetect", BT::NodeConfig());
}

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);

    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}