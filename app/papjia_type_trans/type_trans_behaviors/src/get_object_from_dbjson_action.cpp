#include <nlohmann/json.hpp>
#include "type_trans_behaviors/get_object_from_dbjson_action.hpp"

namespace papjia::behaviors
{
    void logVector(const std::vector<double> &vec)
    {
        std::ostringstream oss;
        oss << "[";
        for (size_t i = 0; i < vec.size(); ++i)
        {
            oss << vec[i];
            if (i < vec.size() - 1)
            {
                oss << ", ";
            }
        }
        oss << "]";

        RCLCPP_INFO(rclcpp::get_logger("GetObjectFromDBJsonAction"), "Vector Data: %s", oss.str().c_str());
    }

    GetObjectFromDBJsonAction::GetObjectFromDBJsonAction(const std::string &name, const BT::NodeConfig &config)
        : BT::SyncActionNode(name, config)
    {
    }

    BT::PortsList GetObjectFromDBJsonAction::providedPorts()
    {
        return BT::PortsList({BT::InputPort<std::string>("json_input"),
                              BT::InputPort<std::string>("key"),
                              BT::OutputPort<std::vector<double>>("result")});
    }

    BT::NodeStatus GetObjectFromDBJsonAction::tick()
    {
        nlohmann::json json_data;
        auto maybe_json = getInput<std::string>("json_input");
        if (maybe_json)
        {
            json_data = nlohmann::json::parse(maybe_json.value());
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("GetObjectFromDBJsonAction"), "json data is not provided");
            return BT::NodeStatus::FAILURE;
        }

        std::string key;
        auto maybe_key = getInput<std::string>("key");
        if (maybe_key)
        {
            key = maybe_key.value();
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("GetObjectFromDBJsonAction"), "key is not provided");
            return BT::NodeStatus::FAILURE;
        }

        std::vector<double> result;

        // 判断是否包含 SUCCESS 并且不为空
        if (json_data.contains("SUCCESS") && json_data["SUCCESS"].is_array())
        {
            bool found = false;
            for (const auto &item : json_data["SUCCESS"])
            {
                if (item.contains(key) && item[key].is_array())
                {
                    result.push_back(item[key][0]);
                    result.push_back(item[key][1]);
                    result.push_back(item[key][2]);
                    result.push_back(item[key][3]);
                    result.push_back(item[key][4]);
                    result.push_back(item[key][5]);
                    result.push_back(item[key][6]);
                    found = true;
                    break;
                }
            }
            if (!found)
            {
                RCLCPP_ERROR(rclcpp::get_logger("GetObjectFromDBJsonAction"), "%s not found in SUCCESS array", key.c_str());
                return BT::NodeStatus::FAILURE;
            }
        }
        else
        {
            RCLCPP_ERROR(rclcpp::get_logger("GetObjectFromDBJsonAction"), "SUCCESS array not found or empty");
            return BT::NodeStatus::FAILURE;
        }

        setOutput("result", result);
        logVector(result);

        return BT::NodeStatus::SUCCESS;
    }
} // namespace papjia::behaviors