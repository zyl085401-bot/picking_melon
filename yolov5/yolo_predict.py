import cv2
import torch
import numpy as np
from pathlib import Path
import os
import sys
import argparse

# 确保你的工作目录是在 yolov5 项目根目录
yolo_path = '/home/yw/projects/yolov5'
sys.path.append(yolo_path)  # 或指定 yolov5 目录的路径

from models.common import DetectMultiBackend
from utils.general import non_max_suppression, check_img_size, scale_boxes
from utils.augmentations import letterbox
from utils.torch_utils import select_device

class YOLOv5Detection:
    def __init__(self, weights="yolov5s.pt", device="", img_size=640, conf_thres=0.3, iou_thres=0.45):
        """
        初始化对象，用于目标检测。

        Args:
            weights (str): 模型的权重文件路径，默认为 "yolov5s.pt"。
            device (str): 运行设备的名称，可以为 "cpu"、"cuda:0" 等，默认为 ""，表示自动选择设备。
            img_size (int): 输入图片的大小，默认为 640。
            conf_thres (float): 置信度阈值，用于筛选检测结果，默认为 0.50。
            iou_thres (float): NMS 的 IOU 阈值，用于筛选重叠的检测结果，默认为 0.45。

        Returns:
            None
        """
        self.device = select_device(device)
        self.model = DetectMultiBackend(weights, device=self.device, dnn=False, data=None, fp16=False)
        self.stride, self.names, self.pt = self.model.stride, self.model.names, self.model.pt
        self.img_size = check_img_size(img_size, s=self.stride)
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def load_image(self, img_path):
        """加载图片并转换为 BGR 和 RGB 格式。"""
        bgr = cv2.imread(img_path)
        rgb = bgr[:, :, ::-1]
        return rgb, bgr

    def inference(self, img, conf_thres =-1.0, iou_thres = -1.0):
        """
        对输入图像进行目标检测，返回检测结果。

        Args:
            img (np.ndarray): 输入的RGB图像。

        Returns:
            tuple: (labels, rects, scores) 分别为目标标签、边界框和置信度。
        """
        img0 = img.copy()
        img = letterbox(img, self.img_size, stride=self.stride, auto=True)[0]
        img = img.transpose(2, 0, 1)
        img = np.ascontiguousarray(img)

        img = torch.from_numpy(img).to(self.device).float()
        img /= 255.0  # 归一化
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        pred = self.model(img)[0]
        if conf_thres > 0 and iou_thres > 0:
            pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=None, agnostic=False)
        else:
            pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=None, agnostic=False)

        labels, rects, scores = [], [], []

        for det in pred:  # 每张图片的检测结果
            if len(det):
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img0.shape).round()
                labels = [self.names[int(c)] for c in det[:, 5].cpu().numpy()]
                rects = det[:, :4].cpu().numpy().astype(int).tolist()
                scores = det[:, 4].cpu().numpy().tolist()

        return labels, rects, scores, []

    def visualize(self, img, labels, rects, scores):
        """
        在图像上可视化检测结果。

        Args:
            img (np.ndarray): 输入的图像。
            labels (list): 检测到的标签列表。
            rects (list): 边界框列表，格式为 (x1, y1, x2, y2)。
            scores (list): 置信度得分列表。

        Returns:
            None
        """
        for label, rect, score in zip(labels, rects, scores):
            x1, y1, x2, y2 = rect
            color = np.random.randint(0, 255, (1, 3), dtype=np.uint8).tolist()[0]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f"{label} {score:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imshow("Detection Result", img)
        cv2.waitKey(0)

    def run_inference(self, img_path):
        """对单张图片进行推理并可视化结果。"""
        rgb, bgr = self.load_image(img_path)
        labels, rects, scores = self.inference(rgb)
        self.visualize(bgr, labels, rects, scores)

    def run_inference_on_directory(self, directory_path):
        """对指定目录中的所有图片进行推理和可视化。"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_paths = [str(p) for p in Path(directory_path).rglob('*') if p.suffix.lower() in image_extensions]

        for img_path in image_paths:
            print(f"Processing {img_path}")
            self.run_inference(img_path)

# 使用示例
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv5 object detection on images.")
    parser.add_argument('--weights', type=str, default=os.path.join(yolo_path, 'runs/train/exp/weights/best.pt'), help='Path to weights file')
    parser.add_argument('--dir', type=str, default=os.path.join(yolo_path, 'datasets/images/val'), help='Path to image directory')
    args = parser.parse_args()

    detector = YOLOv5Detection(weights=args.weights)
    detector.run_inference_on_directory(args.dir)
