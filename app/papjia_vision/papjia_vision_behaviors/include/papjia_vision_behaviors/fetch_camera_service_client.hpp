#ifndef PAPJIA_VISION_BEHAVIORS__FETCH_CAMERA_SERVICE_CLIENT_HPP
#define PAPJIA_VISION_BEHAVIORS__FETCH_CAMERA_SERVICE_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_vision_interface/srv/fetch_camera.hpp>

using FetchCamera = papjia_vision_interface::srv::FetchCamera;

namespace papjia::behaviors {
    class FetchCameraServiceClient  final : public papjia::behavior_tree::ServiceClientBehaviorBase<FetchCamera>
    {
    public:
        FetchCameraServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
        static BT::PortsList providedPorts();
    private:
        tl::expected<std::string, std::string> getServiceName() override;
        tl::expected<FetchCamera::Request, std::string> createRequest() override;
        tl::expected<bool, std::string> processResponse(const FetchCamera::Response &response) override;
    };
}

#endif
