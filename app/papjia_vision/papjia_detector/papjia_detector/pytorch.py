"""
Descripttion: 基于深度学习进行物体检测
version: 2.0
Author: 崔译文
Date: 2023-12-18 09:02:20
@LastEditors: 崔译文
@LastEditTime: 2023-12-21 13:42:58
"""
import torch
import torchvision
import time
import os
import yaml
import cv2
import numpy as np
from papjia_logger.logger import logger


class MaskDetector(object):
    """使用深度学习模型完成物体检测"""

    def __init__(self, config={}) -> None:
        """初始化，完成模型和类别加载

        Args:
            config (dict, optional): 参数配置，至少包含模型路径和类别路径.
        """
        logger.debug("Init MaskDetector ...")
        self.model = None
        self.labels = []
        self.device = "cuda"  # "cpu" or "cuda"
        if "device" in config.keys():  # GPU or CPU
            self.device = config["device"]
            logger.info("use device %s", self.device)
        else:
            logger.warn("No device config")
        if "prepare_times" in config.keys():  # GPU or CPU
            self.prepare_times = config["prepare_times"]
            logger.info("prepare_times %s", self.prepare_times)
        else:
            logger.warn("No prepare_times config")
        if "data_root" in config.keys():  # 数据根目录
            self.data_root = os.path.abspath(config["data_root"])
        else:
            logger.error("No data_root config")
        if "model_path" in config.keys():  # 模型文件路径
            self.model_path = os.path.abspath(
                os.path.join(self.data_root, config["model_path"])
            )
            self.load_model(self.model_path)
        else:
            logger.error("No model_path config")
        if "labels" in config.keys():  # 类别文件路径
            self.labels = config["labels"]
        else:
            logger.error("No label_path config")
        if "sample_image" in config.keys():  # 样例图像
            self.sample_image_path = os.path.abspath(
                os.path.join(self.data_root, config["sample_image"])
            )
            logger.info("sample image %s", self.sample_image_path)
        else:
            logger.warn("No device config")
        self.prepare()
        logger.debug("Init MaskDetector finished")

    def load_model(self, path):
        """加载神经网络模型"""
        logger.info("Loading model from %s", path)
        self.model = torch.jit.load(path)
        self.model.eval()
        logger.info("Loaded model")

    def prepare(self):
        n = 0
        while n < self.prepare_times:
            self.seg_from_file(self.sample_image_path)
            n += 1

    def seg_from_file(self, path):
        """从指定路径加载图像文件并进行分割

        Args:
            path (string): 图像文件路径
        """
        logger.debug("Begin segment from file ...")
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 图像通道转换
        self.seg(img)  # 分割
        logger.debug("Finished segment from file")

    def seg(self, img, max_num=100, min_score=0.99):
        """_summary_

        Args:
            img (numpy三维数组): 待分割的图像数据
            max_num (int, optional): 允许的最大实例个数，超出数目的实例结果摒弃. Defaults to 100.
            min_score (float, optional): 分割实例最小评分限制，小于此分数摒弃. Defaults to 0.99.

        Returns:
            _type_: _description_
        """
        logger.debug("Begin segment ...")
        start = time.perf_counter()
        image = img[:, :, ::-1]
        image_tensor = torch.as_tensor(image.astype("float32").transpose(2, 0, 1)).to(
            self.device
        )
        # 分割
        with torch.no_grad():
            traced_outputs = self.model.to(self.device)(image_tensor)
        end = time.perf_counter()
        logger.info("seg time usage %f", end - start)
        # 获取分割结果
        predictions = {}
        predictions["pred_boxes"] = traced_outputs[0].to("cpu")
        predictions["pred_classes"] = traced_outputs[1].to("cpu")
        predictions["pred_masks"] = traced_outputs[2].to("cpu")
        predictions["scores"] = traced_outputs[3].to("cpu")
        boxes = predictions["pred_boxes"]
        scores = predictions["scores"]
        classes = predictions["pred_classes"]
        masks = np.asarray(predictions["pred_masks"])
        bbs = boxes.detach().numpy()
        # 构造结果[{},{},{}]
        res = []
        for i in range(len(masks)):
            if scores[i] < min_score:
                logger.debug("drop %s score %f", self.labels[classes[i]], scores[i])
                continue
            mask = {}
            mask["segmentation"] = masks[i]
            mask["bbox"] = [
                int(bbs[i][0]),
                int(bbs[i][1]),
                int(bbs[i][2]),
                int(bbs[i][3]),
            ]
            mask["label"] = self.labels[classes[i]]
            mask["class"] = classes[i]
            mask["score"] = scores[i]
            mask["points_num"] = np.sum(masks[i])
            res.append(mask)
            logger.debug(
                "accept %s score %f point num %d",
                mask["label"],
                mask["score"],
                mask["points_num"],
            )
        # 排序和过滤
        res.sort(key=lambda x: x["points_num"], reverse=True)
        num = min(max_num, len(res))
        end = time.perf_counter()
        logger.debug("Finished segment, time usage %f", end - start)
        return res[:num]
