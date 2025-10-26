#!/bin/bash
###
 # @Descripttion: 
 # @version: 
 # @Author: 崔译文
 # @Date: 2024-03-24 11:50:43
 # @LastEditors: 崔译文
 # @LastEditTime: 2024-05-20 16:57:45
### 

# 运行第一个命令，在第一个终端Tab中打开turtlebot3_gazebo
gnome-terminal --tab --title="turtlebot3_gazebo" -- bash -c "ros2 launch turtlebot3_gazebo empty_world.launch.py; exec bash"

# 等待一段时间
sleep 1

# 运行第二个命令，在第二个终端Tab中打开papjia_move
gnome-terminal --tab --title="papjia_move" -- bash -c "ros2 launch papjia_move move_gazebo.launch.py; exec bash"

# 等待一段时间
sleep 1

# 运行第三个命令，在第三个终端Tab中打开papjia_line_tracing
gnome-terminal --tab --title="papjia_line_tracing" -- bash -c "ros2 launch papjia_line_tracing tracing_sim.launch.py; exec bash"

# 等待一段时间
# sleep 1

# # 运行第四个命令，在第四个终端Tab中打开车道线分割
# gnome-terminal --tab --title="seg" -- bash -c "ros2 launch papjia_line_tracing lane.launch.py; exec bash"

# 等待一段时间
sleep 5

# 运行第五个命令，在第五个终端Tab中打开rqt
gnome-terminal --tab --title="rqt" -- bash -c "rqt; exec bash"

# # 运行第六个命令，在第六个终端Tab中打开rviz
# gnome-terminal --tab --title="rviz2" -- bash -c "rviz2; exec bash"
