#ifndef PAPJIA_VISION_BEHAVIORS__FETCH_IMAGE_SERVICE_CLIENT_HPP
#define PAPJIA_VISION_BEHAVIORS__FETCH_IMAGE_SERVICE_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_vision_interface/srv/fetch_image.hpp>

using FetchImage = papjia_vision_interface::srv::FetchImage;

namespace papjia
{
    namespace behaviors
    {
        class FetchImageServiceClient final : public papjia::behavior_tree::ServiceClientBehaviorBase<FetchImage>
        {
        public:
            FetchImageServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                    const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
            static BT::PortsList providedPorts();

        private:
            tl::expected<std::string, std::string> getServiceName() override;

            tl::expected<FetchImage::Request, std::string> createRequest() override;

            tl::expected<bool, std::string> processResponse(const FetchImage::Response &response) override;
        };
    }
}

#endif