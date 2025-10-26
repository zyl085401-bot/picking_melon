import os
import shutil


def rename_and_save_images(input_dir, output_dir, start_num=0):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取输入目录中的所有文件
    image_files = [f for f in os.listdir(input_dir) if f.endswith((".jpg", ".jpeg", ".png"))]

    n = start_num
    # 按排序后的顺序处理文件
    for i, filename in enumerate(sorted(image_files)):
        img_path = os.path.join(input_dir, filename)

        # 生成新的文件名，格式为数字（如001, 111, 0001）
        new_filename = f"{n+1:03}{os.path.splitext(filename)[1]}"  # :03表示数字格式化为三位数，不足前面补0
        n += 1

        output_path = os.path.join(output_dir, new_filename)
        shutil.copy(img_path, output_path)
        print(f"Image copied to {output_path}")


# 设置输入和输出目录
input_directory = "/home/yw/Pictures/melon_datas/hand"
output_directory = "/home/yw/Pictures/melon_datas/bitter"

rename_and_save_images(input_directory, output_directory, start_num=460)
