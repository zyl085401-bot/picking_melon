#!/bin/bash
###
 # @Descripttion: 
 # @version: 
 # @Author: 崔译文
 # @Date: 2024-03-24 11:50:43
 # @LastEditors: 崔译文
 # @LastEditTime: 2024-05-21 09:16:43
### 

# 运行第一个命令，在第一个终端Tab中打开摄像头驱动
gnome-terminal --tab --title="camera" -- bash -c "ros2 launch usb_cam camera.launch.py; exec bash"

# 等待一段时间
sleep 1

# 运行第二个命令，在第二个终端Tab中打开papjia_move
gnome-terminal --tab --title="papjia_move" -- bash -c "ros2 launch papjia_move move.launch.py; exec bash"

# 等待一段时间
sleep 1

# 运行第三个命令，在第三个终端Tab中打开papjia_line_tracing
gnome-terminal --tab --title="papjia_line_tracing" -- bash -c "ros2 launch papjia_line_tracing tracing.launch.py; exec bash"

# 等待一段时间
sleep 1

# 运行第四个命令，在第四个终端Tab中打开车道线分割
gnome-terminal --tab --title="seg" -- bash -c "ros2 launch papjia_line_tracing lane.launch.py; exec bash"

# 等待一段时间
sleep 5

# 运行第五个命令，在第五个终端Tab中打开rqt
gnome-terminal --tab --title="rqt" -- bash -c "rqt; exec bash"
