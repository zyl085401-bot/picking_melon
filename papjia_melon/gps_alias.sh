alias base="ros2 launch nav2_gps_waypoint_follower_demo base.launch.py"
alias camera="ros2 launch nav2_gps_waypoint_follower_demo camera.launch.py"
alias rviz="ros2 launch nav2_gps_waypoint_follower_demo rviz.launch.py"
alias gps="ros2 launch nav2_gps_waypoint_follower_demo gps.launch.py"
alias rl="ros2 launch nav2_gps_waypoint_follower_demo dual_ekf_navsat.launch.py"
alias nav="ros2 launch nav2_gps_waypoint_follower_demo nav.launch.py"
alias w="terminator --layout=gps"

alias colcon_build_nav2_config="cd /home/lab2/workspace/agriculture_ws && colcon build --packages-select nav2_gps_waypoint_follower_demo"