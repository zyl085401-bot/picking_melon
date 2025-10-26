#ifndef PAPJIA_GENERIC_BEHAVIORS__CROP_IMAGE_MSG
#define PAPJIA_GENERIC_BEHAVIORS__CROP_IMAGE_MSG

#include <papjia_behavior_tree/async_behavior_base.hpp>
#include <behaviortree_cpp/action_node.h>
#include <papjia_behavior_tree/check_error.hpp>
#include <opencv2/opencv.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>

namespace papjia::behaviors
{
    class CropImageMsgAction : public papjia::behavior_tree::AsyncBehaviorBase
    {
    public:
        CropImageMsgAction(const std::string &name, const BT::NodeConfig &config,
                              const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);

        static BT::PortsList providedPorts();

    private:
        tl::expected<bool, std::string> doWork() override;

        std::shared_future<tl::expected<bool, std::string>> &getFuture() override
        {
            return future_;
        }
        std::shared_future<tl::expected<bool, std::string>> future_;
    };
}

#endif