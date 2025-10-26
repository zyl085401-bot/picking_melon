import json
import matplotlib.pyplot as plt
import numpy as np


def load_and_visualize_coordinates(file_path):
    # 读取JSON文件
    with open(file_path, "r") as f:
        data = json.load(f)

    # 提取前两个值（x, y坐标）
    coordinates = np.array([point[:2] for point in data])

    # 创建2D图
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    # 绘制散点图
    ax.scatter(coordinates[:, 0], coordinates[:, 1], c="b", marker="o", alpha=0.6)

    # 设置坐标轴标签
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)

    # 设置标题
    ax.set_title("visualize_coordinates")

    # 保存图片
    file_name = file_path.split("/")[-1].split(".")[0]
    plt.savefig(f"data/{file_name}.png")

    # 显示图形
    plt.show()


if __name__ == "__main__":
    # 请替换为您的JSON文件路径
    file_path = "data/观测点_左_success.json"
    load_and_visualize_coordinates(file_path)
