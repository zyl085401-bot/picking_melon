#include "papjia_vision_behaviors/object_detect_service_client.hpp"

namespace papjia
{
    namespace behaviors
    {
        DetectObjsServiceClient::DetectObjsServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                                       const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
            : papjia::behavior_tree::ServiceClientBehaviorBase<DetectObjs>(name, config, shared_resources)
        {
        }

        BT::PortsList DetectObjsServiceClient::providedPorts()
        {
            return BT::PortsList({
                BT::InputPort<std::string>("service_name"),
                BT::InputPort<std::uint64_t>("max_num"),
                BT::InputPort<double>("min_score"),
                BT::OutputPort<std::vector<papjia_vision_interface::msg::Object>>("objects")
            });
        }

        tl::expected<std::string, std::string> DetectObjsServiceClient::getServiceName()
        {
            const auto service_name = getInput<std::string>("service_name");
            if (const auto error = papjia::behavior_tree::maybe_error(service_name))
            {
                return tl::make_unexpected("Failed to get [service_name] from input data port: " + error.value());
            }
            return service_name.value();
        }

        tl::expected<DetectObjs::Request, std::string> DetectObjsServiceClient::createRequest()
        {
            const auto maybe_max_num = getInput<std::uint64_t>("max_num");
            std::uint64_t max_num;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_max_num))
            {
                max_num = 20;
            }
            else {
                max_num = maybe_max_num.value();
            }

            const auto maybe_min_score = getInput<double>("min_score");
            double min_score;
            if (const auto error = papjia::behavior_tree::maybe_error(maybe_min_score)) {
                min_score = 0.98;
            }
            else {
                min_score = maybe_min_score.value();
            }
            
            return papjia_vision_interface::build<DetectObjs::Request>().max_num(max_num).min_score(min_score);
        }

        tl::expected<bool, std::string> DetectObjsServiceClient::processResponse(const DetectObjs::Response& response)
        {
            if (!response.success)
            {
                return tl::make_unexpected("object detect service call failed");
            }
            setOutput<std::vector<papjia_vision_interface::msg::Object>>("objects", response.objects);
            return true;
        }
    }
}