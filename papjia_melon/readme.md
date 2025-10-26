# Melon 机器人采摘项目

## 1. Docker环境配置

切换到项目的docker目录下操作
#### 编译Docker镜像
```bash
docker compose build papjia_melon
```

#### 进入Docker容器
```bash
# 启动容器
docker compose up

# 如果容器已经在运行，可以使用以下命令进入
docker compose exec papjia_melon bash
```

## 2. 启动

### 启动机械臂
```bash
# 启动模拟机械臂
ros2 launch papjia_melon_config arm.launch.py use_mock_hardware:=true
# 启动真实机械臂
ros2 launch papjia_melon_config arm.launch.py
```

### 启动BT
```bash
# 启动行为树
ros2 papjia_melon_config bt.launch.py
```

## 3. 点位配置

### 配置文件位置
点位配置文件位于 `papjia_melon_config/config/waypoint_configs.json`

### 配置方式
1. 直接修改文件内的值
2. 通过浏览器访问：http://localhost:5173/waypoint-config

通过浏览器控制手臂运动时，会先规划，机器人将要执行的轨迹会在rviz中看到（添加Trajectory显示），此时需要主动发一个service请求，机器人才会执行轨迹
```bash
ros2 service call /pause_until_signal papjia_behavior_interface/srv/TriggerSignal "{signal_id: ''}"
```


## 4. 任务构建和执行
查看：papjia_melon/papjia_melon_config/papjia_melon_config/task.py


## 注意事项
2. 启动顺序：先启动机械臂，再启动BT控制节点
4. 运行任务前请确保机械臂处于安全位置
