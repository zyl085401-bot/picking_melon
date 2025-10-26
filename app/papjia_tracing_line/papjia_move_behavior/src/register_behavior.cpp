#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>

#include "papjia_move_behavior/papjia_move_behavior_client.hpp"

namespace papjia::behaviors
{
    class MoveBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehavior<StraightMoveServiceClient>(factory, "StraightMove", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::MoveBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)