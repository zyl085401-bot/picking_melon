"""
Descripttion: 基于深度学习进行物体检测
version: 2.0
Author: 崔译文
Date: 2023-12-18 09:02:20
@LastEditors: 崔译文
@LastEditTime: 2023-12-21 13:42:23
"""
import torch
import torchvision
import time
import os
import json
import yaml
import cv2
import numpy as np
from detectron2.config import get_cfg
from detectron2.engine.defaults import DefaultPredictor
from detectron2.data import MetadataCatalog
from papjia_logger.logger import logger


class MaskDetector(object):
    """使用深度学习模型完成物体检测"""

    def __init__(self, config={}) -> None:
        """初始化，完成模型和类别加载

        Args:
            config (dict, optional): 参数配置，至少包含模型路径、模型配置文件、数据集路径
        """
        logger.debug("Init MaskDetector ...")
        # 加载类别
        self.labels = config['labels']
        logger.info("load labels [%s]", ", ".join(self.labels))
        # 加载模型文件
        self.model_cfg = get_cfg()
        model_cfg_file = os.path.abspath(
            os.path.join(config["data_root"], config["model_cfg"])
        )
        self.model_cfg.merge_from_file(model_cfg_file)
        logger.info("load model config from %s", model_cfg_file)
        # 加载训练好的模型文件
        model_file = os.path.abspath(
            os.path.join(config["data_root"], config["model_path"])
        )
        self.model_cfg.MODEL.WEIGHTS = os.path.abspath(model_file)
        logger.info("load model weight from %s", model_file)
        # 创建推理器
        self.predictor = DefaultPredictor(self.model_cfg)
        logger.debug("Init MaskDetector finished")

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
        # 获取分割结果
        output = self.predictor(img)
        end = time.perf_counter()
        logger.info("seg time usage %f", end - start)
        predictions = output["instances"].to("cpu")
        boxes = predictions.pred_boxes if predictions.has("pred_boxes") else None
        scores = predictions.scores if predictions.has("scores") else None
        classes = (
            predictions.pred_classes.tolist()
            if predictions.has("pred_classes")
            else None
        )
        if predictions.has("pred_masks"):
            masks = np.asarray(predictions.pred_masks)
        else:
            masks = None
        bbs = boxes.tensor.detach().numpy()
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
