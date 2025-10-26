#ifndef PAPJIA_VISUALIZATION_BEHAVIORS__VISUALIZATION_SERVICE_CLIENT_HPP
#define PAPJIA_VISUALIZATION_BEHAVIORS__VISUALIZATION_SERVICE_CLIENT_HPP

#include <string>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <papjia_behavior_tree/service_client_behavior_base.hpp>
#include <papjia_visualization_interface/srv/visualization.hpp>

using Visualization = papjia_visualization_interface::srv::Visualization;

namespace papjia::behaviors {
    class VisualizationServiceClient  final : public papjia::behavior_tree::ServiceClientBehaviorBase<Visualization>
    {
    public:
        VisualizationServiceClient(const std::string &name, const BT::NodeConfiguration &config, const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);
        static BT::PortsList providedPorts();
    private:
        tl::expected<std::string, std::string> getServiceName() override;
        tl::expected<Visualization::Request, std::string> createRequest() override;
        tl::expected<bool, std::string> processResponse(const Visualization::Response &response) override;
    };
}

#endif
