import cv2
import torch
import numpy as np
from pathlib import Path
import os
import sys
from typing import List, Tuple, Union
from ultralytics import YOLO


class YOLOInference:
    def __init__(
        self,
        weights: str = "yolov5s.pt",
        device: str = "cuda:0",
        img_size: int = 640,
        conf_thres: float = 0.3,
        iou_thres: float = 0.25,
    ):
        """Initialize YOLOv5 inference for object detection.

        Args:
            weights (str): Path to model weights
            device (str): Device to run inference on ('cuda:0' or 'cpu')
            img_size (int): Input image size
            conf_thres (float): Confidence threshold
            iou_thres (float): IoU threshold for NMS
        """
        self.device = device
        self.model = YOLO(weights)
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def load_image(self, img_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load image and convert to BGR and RGB formats.

        Args:
            img_path (str): Path to image file

        Returns:
            Tuple[np.ndarray, np.ndarray]: RGB and BGR versions of the image
        """
        bgr = cv2.imread(img_path)
        if bgr is None:
            raise ValueError(f"Could not load image at {img_path}")
        rgb = bgr[:, :, ::-1]
        return rgb, bgr

    def inference(
        self, img: np.ndarray, conf_thres: float = -1.0, iou_thres: float = -1.0
    ) -> Tuple[List[str], List[List[int]], List[float]]:
        """Run inference on an image.

        Args:
            img (np.ndarray): Input image
            conf_thres (float): Confidence threshold override
            iou_thres (float): IoU threshold override

        Returns:
            Tuple containing:
                - List of class labels
                - List of bounding boxes
                - List of confidence scores
        """
        results = self.model(
            img,
            conf=conf_thres if conf_thres > 0 else self.conf_thres,
            iou=iou_thres if iou_thres > 0 else self.iou_thres,
        )

        labels = []
        rects = []
        scores = []

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            clses = result.boxes.cls.int().cpu().numpy()
            names = [result.names[c] for c in clses]

            for box, conf, name in zip(boxes, confs, names):
                labels.append(name)
                rects.append(box.astype(int).tolist())
                scores.append(float(conf))

        return labels, rects, scores

    def visualize(
        self,
        img: np.ndarray,
        labels: List[str],
        rects: List[List[int]],
        scores: List[float],
        alpha: float = 0.4,
    ) -> None:
        """Visualize detection results.

        Args:
            img (np.ndarray): Original image
            labels (List[str]): Class labels
            rects (List[List[int]]): Bounding boxes
            scores (List[float]): Confidence scores
            alpha (float): Transparency for overlay
        """
        # Create overlay for boxes
        overlay = np.zeros_like(img)

        # Draw bounding boxes and labels
        for label, rect, score in zip(labels, rects, scores):
            x1, y1, x2, y2 = map(int, rect)
            color = np.random.randint(0, 255, size=(3,), dtype=np.uint8)
            color = (int(color[0]), int(color[1]), int(color[2]))

            # Draw rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label_text = f"{label} {score:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                img, (x1, y1 - label_height - 5), (x1 + label_width, y1), color, -1
            )
            cv2.putText(
                img,
                label_text,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        # Resize for display
        height, width = img.shape[:2]
        new_width = 640
        new_height = int((new_width / width) * height)
        img = cv2.resize(img, (new_width, new_height))

        # Show result
        cv2.imshow("Result", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def run_inference(
        self, img_path: str
    ) -> Tuple[np.ndarray, List[str], List[List[int]], List[float]]:
        """Run inference on a single image.

        Args:
            img_path (str): Path to image file

        Returns:
            Tuple containing original image and inference results
        """
        img, img0 = self.load_image(img_path)
        labels, rects, scores = self.inference(img)
        return img0, labels, rects, scores

    def run_inference_on_directory(self, directory_path: str) -> None:
        """Run inference on all images in a directory.

        Args:
            directory_path (str): Path to directory containing images
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        image_paths = [
            str(p)
            for p in Path(directory_path).rglob("*")
            if p.suffix.lower() in image_extensions
        ]

        for img_path in image_paths:
            print(f"Processing {img_path}")
            try:
                img0, labels, rects, scores = self.run_inference(img_path)
                self.visualize(img0, labels, rects, scores)
            except Exception as e:
                print(f"Error processing {img_path}: {str(e)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run YOLOv5 inference on a directory of images."
    )
    parser.add_argument(
        "--weights", type=str, default="yolov5s.pt", help="path to weights file"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="datasets/microbial/images/val",
        help="path to image directory",
    )
    parser.add_argument("--device", type=str, default="cuda:0", help="device to run on")
    parser.add_argument("--img-size", type=int, default=1280, help="input image size")
    parser.add_argument(
        "--conf-thres", type=float, default=0.5, help="confidence threshold"
    )
    parser.add_argument("--iou-thres", type=float, default=0.45, help="IoU threshold")

    args = parser.parse_args()

    yolo_inference = YOLOInference(
        weights=args.weights,
        device=args.device,
        img_size=args.img_size,
        conf_thres=args.conf_thres,
        iou_thres=args.iou_thres,
    )
    yolo_inference.run_inference_on_directory(args.dir)
