#include <nlohmann/json.hpp>
#include <papjia_vision_interface/msg/object.hpp>
#include "type_trans_behaviors/json_to_object_action.hpp"

namespace papjia::behaviors
{
    JsonToObjectAction::JsonToObjectAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList JsonToObjectAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("json_object"),
                              BT::OutputPort<papjia_vision_interface::msg::Object>("result_object")});
    }

    BT::NodeStatus JsonToObjectAction::tick()
    {
        auto maybe_json_object = getInput<std::string>("json_object");
        if (not maybe_json_object)
        {
            RCLCPP_ERROR(rclcpp::get_logger("JsonToObjectAction"), "json_object is not provided");
            return BT::NodeStatus::FAILURE;
        }

        nlohmann::json json_object = nlohmann::json::parse(maybe_json_object.value());
        papjia_vision_interface::msg::Object obj;

        // 解析category
        if (!json_object.contains("category") || !json_object["category"].is_string())
        {
            throw std::runtime_error("Missing or invalid category field");
        }
        obj.category = json_object["category"].get<std::string>();

        // 解析pose
        if (!json_object.contains("pose") || !json_object["pose"].is_array() || json_object["pose"].size() != 7)
        {
            throw std::runtime_error("Invalid pose field");
        }
        auto &pose = json_object["pose"];
        obj.pose.position.x = pose[0].get<double>();
        obj.pose.position.y = pose[1].get<double>();
        obj.pose.position.z = pose[2].get<double>();
        obj.pose.orientation.x = pose[3].get<double>();
        obj.pose.orientation.y = pose[4].get<double>();
        obj.pose.orientation.z = pose[5].get<double>();
        obj.pose.orientation.w = pose[6].get<double>();

        // 解析scale
        if (!json_object.contains("scale") || !json_object["scale"].is_array() || json_object["scale"].size() != 3)
        {
            throw std::runtime_error("Invalid scale field");
        }
        auto &scale = json_object["scale"];
        obj.scale.x = scale[0].get<double>();
        obj.scale.y = scale[1].get<double>();
        obj.scale.z = scale[2].get<double>();

        RCLCPP_INFO(rclcpp::get_logger("JsonToObjectAction"), "Parsed object: %s", obj.category.c_str());

        setOutput("result_object", obj);

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors