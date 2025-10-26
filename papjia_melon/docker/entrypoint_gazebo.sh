# source install/setup.bash
source /workspace/install/setup.bash
source /usr/share/gazebo/setup.bash
# Extract paths from AMENT_PREFIX_PATH and add '/share' to each, then add to GAZEBO_MODEL_PATH
if [ ! -z "$AMENT_PREFIX_PATH" ]; then
  for path in $(echo $AMENT_PREFIX_PATH | tr ":" "\n"); do
    export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$path/share"
  done
fi
# 获取ROS 2包路径并保存到变量
GAZEBO_PACKAGE_NAME="nav2_gps_waypoint_follower_demo"
GAZEBO_PACKAGE_PATH=$(ros2 pkg prefix nav2_gps_waypoint_follower_demo)
export GAZEBO_MODEL_PATH="$GAZEBO_MODEL_PATH:$GAZEBO_PACKAGE_PATH/share/$GAZEBO_PACKAGE_NAME/models":/workspace/src/app/nav2_gps/nav2_gps_waypoint_follower_demo/models
