import cv2
import torch
import numpy as np
from pathlib import Path
import os
import sys
import argparse

# 确保你的工作目录是在 yolov5 项目根目录
yolo_path = '/home/lab1/Desktop/yolov5/yolov5'
sys.path.append(yolo_path)  # or specify the path to the yolov5 directory if not in the root

from models.common import DetectMultiBackend
from utils.general import (non_max_suppression, check_img_size, scale_boxes)
from utils.segment.general import process_mask, scale_image
from utils.augmentations import letterbox
from utils.torch_utils import select_device

class YOLOv5Inference:
    def __init__(self, weights='yolov5s-seg.pt', device='cuda:0', img_size=640, conf_thres=0.3, iou_thres=0.25):
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

    def inference(self, img, conf_thres=-1.0, iou_thres=-1.0):
        img0 = img.copy()
        img = letterbox(img, self.img_size, stride=self.stride, auto=True)[0]
        img = img.transpose(2, 0, 1)
        img = np.ascontiguousarray(img)

        img = torch.from_numpy(img).to(self.device)
        img = img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        pred, proto = self.model(img)[:2]
        if conf_thres > 0 and iou_thres > 0:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes=None, agnostic=False, nm=32)
        else:
            pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=None, agnostic=False, nm=32)

        labels = []
        masks = []
        rects = []
        scores = []
        masks_scaled = []

        for i, det in enumerate(pred):  # detections per image
            if len(det):
                masks = process_mask(proto[i], det[:, 6:], det[:, :4], img.shape[2:], upsample=True)  # HWC
                masks = masks.permute(1, 2, 0)
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img0.shape).round()
                num = len(det)
                labels = [self.names[i] for i in det[:, 5].cpu().numpy().astype(int).tolist()]
                scores = [round(i, 3) for i in det[:, 4].cpu().numpy().tolist()]
                rects = det[:, :4].cpu().numpy().astype(int).tolist()
                masks_scaled = [
                    (
                        scale_image(masks.shape[:2], masks[:, :, i].cpu().numpy().astype(np.uint8), img0.shape)[
                            :, :, 0
                        ]
                        > 0
                    ).astype(np.uint8)
                    * (det[:, 5].cpu().numpy().astype(int).tolist()[i] + 1)
                    for i in range(masks.shape[-1])
                ]

        return labels, rects, scores, masks_scaled

    def visualize(self, img, labels, rects, scores, masks, alpha=0.4):
        # 初始化一个全黑的掩码图层
        overlay = np.zeros(img.shape, dtype=np.uint8)
        for mask in masks:
            overlay[mask > 0] = np.random.randint(0, 255, (1, 3), dtype=np.uint8).tolist()[0]
        
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        for label, rect, score in zip(labels, rects, scores):
            x1, y1, x2, y2 = rect
            color = np.random.randint(0, 255, (1, 3), dtype=np.uint8).tolist()[0]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f'{label} {score:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
        # 显示图像
        cv2.imshow("result", img)
        cv2.waitKey(0)

    def run_inference(self, img_path):
        img, img0 = self.load_image(img_path)
        labels, rects, scores, masks = self.inference(img)
        return img0, labels, rects, scores, masks

    def run_inference_on_directory(self, directory_path):
        # 获取目录下的所有图像文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_paths = [str(p) for p in Path(directory_path).rglob('*') if p.suffix.lower() in image_extensions]

        for img_path in image_paths:
            print(f"Processing {img_path}")
            img0, labels, rects, scores, masks = self.run_inference(img_path)
            self.visualize(img0, labels, rects, scores, masks)

# 使用示例
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv5 inference on a directory of images.")
    parser.add_argument('--weights', type=str, default=os.path.join(yolo_path, 'runs/train-seg/exp/weights/best.pt'), help='path to weights file')
    parser.add_argument('--dir', type=str, default=os.path.join(yolo_path, 'datasets/microbial/images/val'), help='path to image directory')
    args = parser.parse_args()

    yolo_inference = YOLOv5Inference(weights=args.weights, device='cuda:0', img_size=640, conf_thres=0.3, iou_thres=0.45)
    yolo_inference.run_inference_on_directory(args.dir)
