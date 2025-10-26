#!/bin/bash
set -e

# 启动udev守护进程
/lib/systemd/systemd-udevd --daemon
# 重新加载udev规则
udevadm control --reload-rules
# 触发设备事件
udevadm trigger

# 执行CMD命令
exec "$@"