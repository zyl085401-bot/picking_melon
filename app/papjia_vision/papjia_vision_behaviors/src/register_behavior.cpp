#include <behaviortree_cpp/bt_factory.h>
#include <papjia_behavior_tree/behavior_context.hpp>
#include <papjia_behavior_tree/shared_resources_node_loader.hpp>

#include "papjia_vision_behaviors/image_get_from_topic_action.hpp"
#include "papjia_vision_behaviors/image_save_to_file_action.hpp"
#include "papjia_vision_behaviors/object_detect_service_client.hpp"
#include "papjia_vision_behaviors/mask_detect_service_client.hpp"
#include "papjia_vision_behaviors/camera_info_get_from_topic_action.hpp"
#include "papjia_vision_behaviors/tags_detect_service_client.hpp"
#include "papjia_vision_behaviors/image_fetch_service_client.hpp"
#include "papjia_vision_behaviors/crop_image_msg_action.hpp"
#include "papjia_vision_behaviors/fetch_camera_service_client.hpp"

namespace papjia::behaviors
{
    class VisionBehaviorLoader : public papjia::behavior_tree::SharedResourcesNodeLoaderBase
    {
    public:
        void registerBehaviors(BT::BehaviorTreeFactory &factory,
                               const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources) override
        {
            papjia::behavior_tree::registerBehavior<DetectObjsServiceClient>(factory, "ObjectDetect", shared_resources);
            papjia::behavior_tree::registerBehavior<DetectMasksServiceClient>(factory, "MaskDetect", shared_resources);
            papjia::behavior_tree::registerBehavior<DetectTagsServiceClient>(factory, "TagDetect", shared_resources);
            papjia::behavior_tree::registerBehavior<ImageGetFromTopicAction>(factory, "ImageGetFromTopic", shared_resources);
            papjia::behavior_tree::registerBehavior<ImageSaveToFileAction>(factory, "ImageSaveToFile", shared_resources);
            papjia::behavior_tree::registerBehavior<CameraInfoGetFromTopicAction>(factory, "CameraInfoGetFromTopic", shared_resources);
            papjia::behavior_tree::registerBehavior<FetchImageServiceClient>(factory, "FetchImage", shared_resources);
            papjia::behavior_tree::registerBehavior<CropImageMsgAction>(factory, "CropImageMsg", shared_resources);
            papjia::behavior_tree::registerBehavior<FetchCameraServiceClient>(factory, "FetchCamera", shared_resources);
        }
    };
}

#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(papjia::behaviors::VisionBehaviorLoader, papjia::behavior_tree::SharedResourcesNodeLoaderBase)