#include "papjia_move_behavior/papjia_move_behavior_client.hpp"

namespace papjia
{
  namespace behaviors
  {
    StraightMoveServiceClient::StraightMoveServiceClient(const std::string &name, const BT::NodeConfiguration &config,
                                                         const std::shared_ptr<papjia::behavior_tree::BehaviorContext> &shared_resources)
        : papjia::behavior_tree::ServiceClientBehaviorBase<StraightMove>(name, config, shared_resources)
    {
    }

    BT::PortsList StraightMoveServiceClient::providedPorts()
    {
      return BT::PortsList({
          BT::InputPort<std::string>("service_name"),
          BT::InputPort<float>("result_timeout"),
          BT::InputPort<float>("distance"),
          BT::InputPort<float>("speed"),
          BT::InputPort<bool>("use_integral"),
          BT::InputPort<bool>("follow_line"),
          BT::InputPort<std::string>("line_frame"),
          BT::InputPort<std::vector<double>>("line_start"),
          BT::InputPort<std::vector<double>>("line_end"),
          BT::OutputPort<bool>("success")
      });
    }

    tl::expected<std::string, std::string> StraightMoveServiceClient::getServiceName()
    {
      const auto service_name = getInput<std::string>("service_name");
      // TODO maybe errir
      // if (const auto error = )
      return service_name.value();
    }

    tl::expected<StraightMove::Request, std::string> StraightMoveServiceClient::createRequest()
    {
      const auto distance = getInput<float>("distance");
      if (const auto error = papjia::behavior_tree::maybe_error(distance))
      {
        return tl::make_unexpected("Failed to get [distance] from input data port: " + error.value());
      }

      const auto speed = getInput<float>("speed");
      if (const auto error = papjia::behavior_tree::maybe_error(speed))
      {
        return tl::make_unexpected("Failed to get [speed] from input data port: " + error.value());
      }

      const auto use_integral = getInput<bool>("use_integral");
      if (const auto error = papjia::behavior_tree::maybe_error(use_integral))
      {
        return tl::make_unexpected("Failed to get [use_integral] from input data port: " + error.value());
      }

      bool follow_line;
      std::string line_frame;
      std::vector<double> line_start;
      std::vector<double> line_end;
      const auto maybe_follow_line = getInput<bool>("follow_line");
      if (const auto error = papjia::behavior_tree::maybe_error(maybe_follow_line))
      {
        follow_line = false;
      }
      else
      {
        follow_line = maybe_follow_line.value();
      }

      if (follow_line)
      {
        const auto maybe_line_frame = getInput<std::string>("line_frame");
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_line_frame))
        {
          return tl::make_unexpected("Failed to get [line_frame] from input data port: " + error.value());
        }
        else
        {
          line_frame = maybe_line_frame.value();
        }

        const auto maybe_line_start = getInput<std::vector<double>>("line_start");
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_line_start))
        {
          return tl::make_unexpected("Failed to get [line_start] from input data port: " + error.value());
        }
        else
        {
          line_start = maybe_line_start.value();
        }

        const auto maybe_line_end = getInput<std::vector<double>>("line_end");
        if (const auto error = papjia::behavior_tree::maybe_error(maybe_line_end))
        {
          return tl::make_unexpected("Failed to get [line_end] from input data port: " + error.value());
        }
        else
        {
          line_end = maybe_line_end.value();
        }
      }



      return papjia_move_msgs::build<StraightMove::Request>().distance(distance.value()).speed(speed.value()).use_integral(use_integral.value()).follow_line(follow_line).line_frame(line_frame).line_start(line_start).line_end(line_end);
    }

    tl::expected<bool, std::string> StraightMoveServiceClient::processResponse(const StraightMove::Response &response)
    {
      if (response.success)
        return true;
      else
        return tl::make_unexpected("move straight service call failed");
    }
  }
}