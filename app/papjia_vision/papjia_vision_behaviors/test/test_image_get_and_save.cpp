#include <gtest/gtest.h>

#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/node.hpp>

#include <papjia_behavior_tree/papjia_behavior_tree.hpp>

static const char *xml_text = R"(

 <root BTCPP_format="4" >

     <BehaviorTree ID="MainTree">
        <Sequence name="root">
            <ImageGetFromTopic topic_name="/camera/color_camera/image_raw" image="{image_msg}"/>
            <ImageSaveToFile image="{image_msg}" file_name="test.png"/>
        </Sequence>
     </BehaviorTree>

 </root>
 )";

TEST(BasicBehaviorTests, test_image_get_and_save)
{
    pluginlib::ClassLoader<papjia::behavior_tree::SharedResourcesNodeLoaderBase> class_loader(
        "papjia_behavior_tree", "papjia::behavior_tree::SharedResourcesNodeLoaderBase");

    auto node = std::make_shared<rclcpp::Node>("test_image_get_and_save_node");
    auto shared_resources = std::make_shared<papjia::behavior_tree::BehaviorContext>(node);

    BT::BehaviorTreeFactory factory;
    {
        auto plugin_instance = class_loader.createSharedInstance("papjia/vision_behaviors");
        try
        {
            plugin_instance->registerBehaviors(factory, shared_resources);
        }
        catch (const std::exception &e)
        {
            std::cerr << "Exception caught: " << e.what() << std::endl;
        }
        ASSERT_THROW(plugin_instance->registerBehaviors(factory, shared_resources), std::exception);
    }

    // factory.instantiateTreeNode("test_behavior_name", "ImageGetFromTopic", BT::NodeConfig());
    // factory.instantiateTreeNode("test_behavior_name", "ImageSaveToFile", BT::NodeConfig());

    auto tree = factory.createTreeFromText(xml_text);
    tree.tickWhileRunning();
    std::cout << "test finish" << std::endl;
}

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}