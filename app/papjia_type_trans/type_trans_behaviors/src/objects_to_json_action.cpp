#include <nlohmann/json.hpp>
#include <papjia_vision_interface/msg/object.hpp>
#include "type_trans_behaviors/objects_to_json_action.hpp"

namespace papjia::behaviors
{
    ObjectsToJsonAction::ObjectsToJsonAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList ObjectsToJsonAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::vector<papjia_vision_interface::msg::Object>>("objects"),
                              BT::OutputPort<std::string>("json_result")});
    }

    BT::NodeStatus ObjectsToJsonAction::tick()
    {
        nlohmann::json json_data;
        nlohmann::json json_list = nlohmann::json::array();

        std::vector<papjia_vision_interface::msg::Object> objects;
        auto maybe_objects = getInput<std::vector<papjia_vision_interface::msg::Object>>("objects");
        if (maybe_objects)
        {
            objects = maybe_objects.value();
        }

        for (auto &obj : objects)
        {
            nlohmann::json item;

            item["category"] = obj.category;
            item["pose"] = {obj.pose.position.x, obj.pose.position.y, obj.pose.position.z, obj.pose.orientation.x, obj.pose.orientation.y, obj.pose.orientation.z, obj.pose.orientation.w};
            item["scale"] = {obj.scale.x, obj.scale.y, obj.scale.z};

            // 将每个项添加到 json_list 中
            json_list.push_back(item);
        }

        std::string json_str = json_list.dump();
        setOutput("json_result", json_str);

        RCLCPP_INFO(rclcpp::get_logger("ObjectsToJsonAction"), json_str.c_str());

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors