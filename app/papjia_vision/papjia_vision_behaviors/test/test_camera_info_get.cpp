#include <gtest/gtest.h>

#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/node.hpp>

#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <sensor_msgs/msg/camera_info.hpp>

static const char *xml_text = R"(

 <root BTCPP_format="4" >

     <BehaviorTree ID="MainTree">
        <Sequence name="root">
            <CameraInfoGetFromTopic topic_name="/gazebo/kinect/camera_info" camera_info="{camera_info_msg}"/>
        </Sequence>
     </BehaviorTree>

 </root>
 )";

TEST(BasicBehaviorTests, test_camera_info_get)
{
    pluginlib::ClassLoader<papjia::behavior_tree::SharedResourcesNodeLoaderBase> class_loader(
        "papjia_behavior_tree", "papjia::behavior_tree::SharedResourcesNodeLoaderBase");

    auto node = std::make_shared<rclcpp::Node>("test_camera_info_get_node");
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

    // factory.instantiateTreeNode("test_behavior_name", "CameraInfoGetFromTopic", BT::NodeConfig());

    BT::Blackboard::Ptr blackboard = BT::Blackboard::create();
    auto tree = factory.createTreeFromText(xml_text, blackboard);

    tree.tickWhileRunning();

    // 从黑板上获取categories输出
    auto keys = blackboard->getKeys();
    for (auto key : keys)
    {
        std::cout << "key: " << key << std::endl;
    }
    auto msg = blackboard->get<sensor_msgs::msg::CameraInfo>("camera_info_msg");

    std::cout << "Received CameraInfo:" << std::endl;

    // 输出分辨率
    std::cout << "Resolution: " << msg.width << "x" << msg.height << std::endl;

    // 输出内参矩阵 (K)
    std::cout << "Camera Matrix (K):" << std::endl;
    for (int i = 0; i < 3; ++i)
    {
        for (int j = 0; j < 3; ++j)
        {
            std::cout << std::fixed << std::setprecision(3) << msg.k[i * 3 + j] << " ";
        }
        std::cout << std::endl;
    }

    // 输出畸变参数
    std::cout << "Distortion Coefficients: ";
    for (double d : msg.d)
    {
        std::cout << std::fixed << std::setprecision(3) << d << " ";
    }
    std::cout << std::endl;

    // 输出投影矩阵 (P)
    std::cout << "Projection Matrix (P):" << std::endl;
    for (int i = 0; i < 3; ++i)
    {
        for (int j = 0; j < 4; ++j)
        {
            std::cout << std::fixed << std::setprecision(3) << msg.p[i * 4 + j] << " ";
        }
        std::cout << std::endl;
    }
    std::cout << "test finish" << std::endl;
}

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}