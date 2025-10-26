#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>

#include "papjia_melon_behaviors/control_gripper_client.hpp"
#include "papjia_melon_behaviors/control_shears_client.hpp"
#include "papjia_melon_behaviors/action_nodes.hpp"


namespace papjia::behaviors
{
    class PapjiaMelonBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehavior<ControlGripperClient>(factory, "ControlGripper", shared_resources);
            papjia::behavior_tree::registerBehavior<ControlShearsClient>(factory, "ControlShears", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<FilterObject>(factory, "FilterObject", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<GetGraspWaypoints>(factory, "GetGraspWaypoints", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::PapjiaMelonBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)