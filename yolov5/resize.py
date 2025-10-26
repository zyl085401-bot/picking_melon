import os
import cv2


def resize_images(input_dir, output_dir, target_width):
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历输入目录中的所有文件
    for filename in os.listdir(input_dir):
        if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            img_path = os.path.join(input_dir, filename)
            img = cv2.imread(img_path)
            height, width = img.shape[:2]
            scale = target_width / width
            target_height = int(height * scale)
            resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, resized_img)
            print(f"Resized image saved to {output_path}")


input_directory = "/home/yw/Documents/车道线/Origin"
output_directory = "/home/yw/Documents/车道线/640"
target_width = 640  # 你希望的宽度

resize_images(input_directory, output_directory, target_width)
