# 使用 papjia_core 作为基础镜像
FROM papjia-docker.pkg.coding.net/weishengwujiance/papjia_szyj/papjia_core:latest as base

# 设置工作目录
WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    python-is-python3 \
    python3-pip \
    python3-tk \
    language-pack-zh-hans \
    fonts-wqy-microhei

COPY papjia_config_manage /workspace/src/papjia_config_manage
COPY papjia_skill /workspace/src/papjia_skill

# 安装Python依赖
RUN pip install -r /workspace/src/papjia_config_manage/requirments.txt

# 构建 ROS 2 工作空间
SHELL ["/bin/bash", "-c"]
RUN source /opt/ros/humble/setup.bash
RUN source /papjia_core_ws/install/setup.bash
RUN source /opt/ros/humble/setup.bash && \
    source /papjia_core_ws/install/setup.bash && \
    colcon build \
        --event-handlers console_direct+ \
        --cmake-args -DCMAKE_BUILD_TYPE=Release


# 启动 bash 终端
WORKDIR /workspace/src/papjia_config_manage
# CMD ["/bin/bash", "-c", "chmod +x start.sh && ./start.sh"]

CMD ["bash"]
