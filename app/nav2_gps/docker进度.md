### PC端：
docker文件位于`/docker_ws`内。

`\nav2_gps`下是运行仿真GPS导航的文件，运行方式见`\nav2_gps\README.md`

`\nav2_gps\src`下是相关的代码，其中
- `nav2_gps_waypoint_follower_demo`是导航功能包
- `nav2_obstacle_stop_controller`是具备障碍物检测和急停的控制包
- `nav2_straight_line_planner`是规划直线的规划包
- `papjia_joy_control`（手柄包）与`pointcloud_to_laserscan`（开源仓库）

### Jetson端：
docker文件位于`/docker_ws`内。

`\tracked_vehicle`下是运行仿真GPS导航的文件，运行方式见`\tracked_vehicle\README.md`

`\tracked_vehicle\src`下是相关的代码，其中
- `nav2_gps`现有的功能：启动D435i和点云-雷达转换接口
- `realsense-ros`（相机驱动，开源仓库）与`pointcloud_to_laserscan`（开源仓库）

### 合并docker注意事项
- 基础镜像不同
- jetson中apt对网络要求较敏感，可以手动编写`sources.list`进行替换，注意arm64架构软件源与x86架构不同
- realsense驱动下载方式依照jetson上的dockerfile成功率较高