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
            <ImageGetFromTopic topic_name="/camera1/rgb/image_raw" image="{image_msg}"/>
            <ImageSaveToFile image="{image_msg}" file_name="/home/yw/test.png"/>
            <MaskDetect service_name="/papjia_vision/service_image_segment" image="{image_msg}" max_num="10" min_score="0.85" categories="{categories_msg}"/>
        </Sequence>
     </BehaviorTree>

 </root>
 )";

TEST(VisionBehaviorTests, test_vision_behavior_mask_detect)
{
    pluginlib::ClassLoader<papjia::behavior_tree::SharedResourcesNodeLoaderBase> class_loader(
        "papjia_behavior_tree", "papjia::behavior_tree::SharedResourcesNodeLoaderBase");

    auto node = std::make_shared<rclcpp::Node>("test_node");
    auto shared_resources = std::make_shared<papjia::behavior_tree::BehaviorContext>(node);

    BT::BehaviorTreeFactory factory;
    {   
        
        auto plugin_instance = class_loader.createSharedInstance("papjia/vision_behaviors");
        try {
            plugin_instance->registerBehaviors(factory, shared_resources);
        } catch (const std::exception& e) {
            std::cerr << "Exception caught: " << e.what() << std::endl;
        }
        ASSERT_THROW(plugin_instance->registerBehaviors(factory, shared_resources), std::exception);
    }

    // factory.instantiateTreeNode("test_behavior_name1", "ImageGetFromTopic", BT::NodeConfig());
    // factory.instantiateTreeNode("test_behavior_name2", "ImageSaveToFile", BT::NodeConfig());
    // factory.instantiateTreeNode("test_behavior_name3", "MaskDetect", BT::NodeConfig());

    BT::Blackboard::Ptr blackboard = BT::Blackboard::create();
    auto tree = factory.createTreeFromText(xml_text, blackboard);

    tree.tickWhileRunning();

    // 从黑板上获取categories输出
    auto keys = blackboard->getKeys();
    for (auto key : keys) {
        std::cout << "key: " << key << std::endl;
    }
    auto categories = blackboard->get<std::vector<std::string>>("categories_msg");

    std::cout << "Categories detected:" << std::endl;
    for (auto category : categories) {
        std::cout << "- " << category << std::endl;
    }

    std::cout << "test finish" << std::endl;
}

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);

    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}