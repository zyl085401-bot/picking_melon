#ifndef PAPJIA_BEHAVIOR_TREE__ADD_TWO_INTS_SERVICE_CLIENT_HPP
#define PAPJIA_BEHAVIOR_TREE__ADD_TWO_INTS_SERVICE_CLIENT_HPP

#include <papjia_behavior_tree/papjia_behavior_tree.hpp>
#include <papjia_behavior_tree/check_error.hpp>
#include <papjia_move_msgs/srv/straight_move.hpp>

using StraightMove = papjia_move_msgs::srv::StraightMove;

namespace papjia
{
    namespace behaviors
    {
        class StraightMoveServiceClient final : public papjia::behavior_tree::ServiceClientBehaviorBase<StraightMove>
        {
        public:
            StraightMoveServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                      const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources);

            static BT::PortsList providedPorts();

        private:
            tl::expected<std::string, std::string> getServiceName() override;

            tl::expected<StraightMove::Request, std::string> createRequest() override;

            tl::expected<bool, std::string> processResponse(const StraightMove::Response &response) override;
        };
    }
}

#endif