import os
import shutil
import random


def split_dataset(origin_dir, datasets_root, config_root, dataset_name, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1, mode="w"):
    # 确保比例总和接近1
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "The sum of train, val, and test ratios must be 1."

    # 读取类别标签
    class_file = os.path.join(origin_dir, "classification.txt")
    with open(class_file, "r") as f:
        class_names = [line.strip() for line in f.readlines()]

    # 创建目标目录结构
    base_dir = os.path.join(datasets_root, dataset_name)
    image_dirs = {
        "train": os.path.join(base_dir, "images", "train"),
        "val": os.path.join(base_dir, "images", "val"),
        "test": os.path.join(base_dir, "images", "test"),
    }
    label_dirs = {
        "train": os.path.join(base_dir, "labels", "train"),
        "val": os.path.join(base_dir, "labels", "val"),
        "test": os.path.join(base_dir, "labels", "test"),
    }

    for dir_path in list(image_dirs.values()) + list(label_dirs.values()):
        os.makedirs(dir_path, exist_ok=True)

    # 获取所有标注文件
    labels = [f for f in os.listdir(origin_dir) if f.endswith(".txt") and f != "classification.txt"]

    # 找到有对应图片的标注文件
    data = []
    for label in labels:
        image = label.replace(".txt", ".jpg")
        if os.path.exists(os.path.join(origin_dir, image)):
            data.append((image, label))
        image = label.replace(".txt", ".png")
        if os.path.exists(os.path.join(origin_dir, image)):
            data.append((image, label))

    # 将数据打乱
    random.shuffle(data)

    # 计算每个集合的大小
    total_count = len(data)
    train_count = int(total_count * train_ratio)
    val_count = int(total_count * val_ratio)
    test_count = total_count - train_count - val_count

    # 分配数据
    datasets = {"train": data[:train_count], "val": data[train_count : train_count + val_count], "test": data[train_count + val_count :]}
    
    # 生成 txt 文件
    txt_files = {
        "train": open(os.path.join(base_dir, "train.txt"), mode=mode),
        "val": open(os.path.join(base_dir, "val.txt"), mode=mode),
        "test": open(os.path.join(base_dir, "test.txt"), mode=mode),
    }

    # 移动文件到对应的目录，并写入 txt 文件
    for split, files in datasets.items():
        for image, label in files:
            shutil.copy(os.path.join(origin_dir, image), image_dirs[split])
            shutil.copy(os.path.join(origin_dir, label), label_dirs[split])
            txt_files[split].write(f"./images/{split}/{image}\n")

    # 关闭所有 txt 文件
    for f in txt_files.values():
        f.close()

    # 生成 yaml 配置文件
    yaml_content = f"""
path: ./{base_dir}
train: train.txt
val: val.txt
test: test.txt

nc: {len(class_names)}  # 类别数
names: {class_names}
"""
    os.makedirs(config_root, exist_ok=True)
    with open(os.path.join(config_root, f"{dataset_name}.yaml"), "w") as f:
        f.write(yaml_content)

    print("Dataset split completed successfully.")


# 使用示例
origin_dir = "/home/lab1/Desktop/caizhai_picture/melon_datas/bitter"  # 替换为你的原始图像和标注文件所在目录
dataset_name = "caizhai"  # 替换为你的数据集名称
datasets_root = "./datasets/"  # 替换为你的数据集根目录
config_root = "./data/"  # 替换为你的配置文件根目录
split_dataset(origin_dir, datasets_root, config_root, dataset_name, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, mode="a")
