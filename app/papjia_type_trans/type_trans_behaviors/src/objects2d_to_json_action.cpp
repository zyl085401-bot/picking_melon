#include <nlohmann/json.hpp>
#include <papjia_vision_interface/msg/objects2d.hpp>
#include "type_trans_behaviors/objects2d_to_json_action.hpp"

namespace papjia::behaviors
{
    Objects2dToJsonAction::Objects2dToJsonAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList Objects2dToJsonAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<papjia_vision_interface::msg::Objects2d>("objects"),
                              BT::OutputPort<std::string>("json_result")});
    }

    BT::NodeStatus Objects2dToJsonAction::tick()
    {
        nlohmann::json json_data;
        nlohmann::json json_list = nlohmann::json::array();

        papjia_vision_interface::msg::Objects2d objects;
        auto maybe_objects = getInput<papjia_vision_interface::msg::Objects2d>("objects");
        if (maybe_objects)
        {
            objects = maybe_objects.value();
        }

        for (auto &obj : objects.objects)
        {
            nlohmann::json item;

            item["category"] = obj.category;
            item["score"] = obj.score;
            item["rect"] = {obj.rect.x1, obj.rect.y1, obj.rect.x2, obj.rect.y2};
            item["points_num"] = obj.points_num;

            // 将每个项添加到 json_list 中
            json_list.push_back(item);
        }

        std::string json_str = json_list.dump();
        setOutput("json_result", json_str);

        RCLCPP_INFO(rclcpp::get_logger("Objects2dToJsonAction"), json_str.c_str());

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors