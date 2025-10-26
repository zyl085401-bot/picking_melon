#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>

#include "pan_tilt_behaviors/control_pan_tilt_action_client.hpp"

namespace papjia::behaviors
{
    class PanTiltBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehavior<ControlPanTiltActionClient>(factory, "ControlPanTilt", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::PanTiltBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)