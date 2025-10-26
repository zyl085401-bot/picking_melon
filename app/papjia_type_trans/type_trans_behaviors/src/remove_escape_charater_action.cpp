#include <regex>
#include <nlohmann/json.hpp>
#include "type_trans_behaviors/remove_escape_charater_action.hpp"

namespace papjia::behaviors
{
    void RemovePatternWithBackslash(std::string &input)
    {
        std::string regex_pattern = R"(\\)";
        std::regex pattern(regex_pattern); // 使用拼接后的字符串构造 regex 对象

        // 替换为目标字符串，或清空以移除匹配内容
        input = std::regex_replace(input, pattern, "");
    }
    RemoveEscapeCharacterAction::RemoveEscapeCharacterAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList RemoveEscapeCharacterAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("json_input"),
                              BT::OutputPort<std::string>("json_result")});
    }

    BT::NodeStatus RemoveEscapeCharacterAction::tick()
    {
        std::string json_input;
        auto maybe_json_input = getInput<std::string>("json_input");
        if (maybe_json_input)
        {
            json_input = maybe_json_input.value();
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("RemoveEscapeCharacterAction"), "Failed get [json_input]");
            return BT::NodeStatus::FAILURE;
        }

        std::string json_result = json_input;

        RemovePatternWithBackslash(json_result);

        setOutput("json_result", json_result);

        RCLCPP_INFO(rclcpp::get_logger("RemoveEscapeCharacterAction"), "set [result_json] = %s", json_result.c_str());

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors