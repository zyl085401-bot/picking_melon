#ifndef PAPJIA_VISION_BEHAVIORS__TAGS_DETECT_SERVICE_CLIENT_HPP
#define PAPJIA_VISION_BEHAVIORS__TAGS_DETECT_SERVICE_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_vision_interface/srv/detect_tags.hpp>

using DetectTags = papjia_vision_interface::srv::DetectTags;

namespace papjia
{
    namespace behaviors
    {
        class DetectTagsServiceClient final : public papjia::behavior_tree::ServiceClientBehaviorBase<DetectTags>
        {
        public:
            DetectTagsServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                   const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
            static BT::PortsList providedPorts();

        private:
            tl::expected<std::string, std::string> getServiceName() override;

            tl::expected<DetectTags::Request, std::string> createRequest() override;

            tl::expected<bool, std::string> processResponse(const DetectTags::Response &response) override;
        };
    }
}

#endif