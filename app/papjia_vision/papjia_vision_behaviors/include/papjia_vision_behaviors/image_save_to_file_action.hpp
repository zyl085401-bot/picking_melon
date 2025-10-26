#ifndef PAPJIA_GENERIC_BEHAVIORS__SAVE_IMAGE_TO_FILE
#define PAPJIA_GENERIC_BEHAVIORS__SAVE_IMAGE_TO_FILE

#include <papjia_behavior_tree/async_behavior_base.hpp>
#include <behaviortree_cpp/action_node.h>
#include <papjia_behavior_tree/check_error.hpp>
#include <opencv2/opencv.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>

namespace papjia::behaviors
{
    class ImageSaveToFileAction : public papjia::behavior_tree::AsyncBehaviorBase
    {
    public:
        ImageSaveToFileAction(const std::string &name, const BT::NodeConfig &config,
                        const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);

        static BT::PortsList providedPorts();

    private:
        tl::expected<bool, std::string> doWork() override;

        std::shared_future<tl::expected<bool, std::string>> &getFuture() override
        {
            return future_;
        }
        std::shared_future<tl::expected<bool, std::string>> future_;

        tl::expected<bool, std::string> saveImage(const sensor_msgs::msg::Image &image, const std::string &file_path);
    };
}

#endif