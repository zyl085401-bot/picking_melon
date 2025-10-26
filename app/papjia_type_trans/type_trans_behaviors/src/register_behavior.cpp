#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>
#include "type_trans_behaviors/objects2d_to_json_action.hpp"
#include "type_trans_behaviors/objects_to_json_action.hpp"
#include "type_trans_behaviors/pose_stamped_to_json_action.hpp"
#include "type_trans_behaviors/json_to_object_action.hpp"
#include "type_trans_behaviors/get_object_from_dbjson_action.hpp"
#include "type_trans_behaviors/remove_escape_charater_action.hpp"

namespace papjia::behaviors
{
    class TypeTransBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehaviorNotSharedResources<Objects2dToJsonAction>(factory, "Object2dToJson", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<ObjectsToJsonAction>(factory, "ObjectToJson", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<JsonToObjectAction>(factory, "JsonToObject", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<GetObjectFromDBJsonAction>(factory, "GetObjectFromDBJson", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<RemoveEscapeCharacterAction>(factory, "RemoveEscapeCharacter", shared_resources);
            papjia::behavior_tree::registerBehaviorNotSharedResources<PoseStampedToJsonAction>(factory, "PoseStampedToJson", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::TypeTransBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)