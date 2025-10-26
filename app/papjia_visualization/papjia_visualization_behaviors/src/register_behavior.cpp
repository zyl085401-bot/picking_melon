#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>
#include "papjia_visualization_behaviors/visualization_service_client.hpp"

namespace papjia::behaviors
{
    class VisualizationBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehavior<VisualizationServiceClient>(factory, "Visualization", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::VisualizationBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)
