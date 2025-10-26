import cv2
import numpy as np
import os
import time
from typing import List, Dict, Any
from papjia_logger.logger import logger


class MaskDetector(object):
    """使用深度学习模型完成物体检测"""

    def __init__(self, config: Dict[str, Any] = {}) -> None:
        """初始化，完成模型和类别加载

        Args:
            config (dict, optional): 参数配置，至少包含模型路径和类别路径.
        """
        logger.debug("Init MaskDetector ...")
        self.model = None
        self.labels = []
        self.device = "cuda:0"  # "cpu" or "cuda:0"
        self.with_mask = True
        self.prepare_times = 1
        self.data_root = ""
        self.model_path = ""
        self.sample_image_path = ""

        if "device" in config.keys():  # GPU or CPU
            self.device = config["device"]
            logger.info("use device %s", self.device)
        else:
            logger.warn("No device config")

        if "with_mask" in config.keys():  # 语义分割 or 物体检测
            self.with_mask = config["with_mask"]
            logger.info("with_mask %s", self.with_mask)
        else:
            logger.warn("No with_mask config")

        if "prepare_times" in config.keys():  # 预热次数
            self.prepare_times = config["prepare_times"]
            logger.info("prepare_times %s", self.prepare_times)
        else:
            logger.warn("No prepare_times config")

        if "data_root" in config.keys():  # 数据根目录
            self.data_root = os.path.abspath(config["data_root"])
            logger.info("data_root %s", self.data_root)
        else:
            logger.error("No data_root config")

        if "model_path" in config.keys():  # 模型文件路径
            self.model_path = os.path.abspath(
                os.path.join(self.data_root, config["model_path"])
            )
            self.load_model(self.model_path)
        else:
            logger.error("No model_path config")

        if "sample_image" in config.keys():  # 样例图像
            self.sample_image_path = os.path.abspath(
                os.path.join(self.data_root, config["sample_image"])
            )
            logger.info("sample image %s", self.sample_image_path)
        else:
            logger.warn("No sample_image config")

        self.prepare()
        logger.debug("Init MaskDetector finished")

    def load_model(self, path: str) -> None:
        """加载神经网络模型"""
        logger.info("Loading model from %s", path)
        if self.with_mask is True:
            from papjia_detector.yolo_predict_seg import YOLOInference

            self.model = YOLOInference(weights=path, device=self.device)
        else:
            from papjia_detector.yolo_predict import YOLOInference

            self.model = YOLOInference(weights=path, device=self.device)
        logger.info("Loaded model")

    def prepare(self) -> None:
        """预热模型"""
        n = 0
        while n < self.prepare_times:
            self.seg_from_file(self.sample_image_path)
            n += 1

    def seg_from_file(self, path: str) -> None:
        """从指定路径加载图像文件并进行分割

        Args:
            path (string): 图像文件路径
        """
        logger.debug("Begin segment from file ...")
        img = cv2.imread(path)
        if img is None:
            logger.error(f"Could not load image at {path}")
            return
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        logger.debug("from BGR to RGB")
        self.seg(img, max_num=10, min_score=0.3)  # 分割
        logger.debug("Finished segment from file")

    def seg(
        self, img: np.ndarray, max_num: int = 100, min_score: float = 0.99
    ) -> List[Dict[str, Any]]:
        """对图像进行分割或检测

        Args:
            img (numpy.ndarray): 待分割的图像数据
            max_num (int, optional): 允许的最大实例个数，超出数目的实例结果摒弃. Defaults to 100.
            min_score (float, optional): 分割实例最小评分限制，小于此分数摒弃. Defaults to 0.99.

        Returns:
            List[Dict[str, Any]]: 检测/分割结果列表，每个结果包含bbox、area、label、score等信息
        """
        logger.debug("Begin segment ...")
        start = time.perf_counter()

        if self.with_mask:
            labels, boxes, scores, masks, rects_rotated = self.model.inference(img, calc_rotated_bbox=True)
        else:
            labels, boxes, scores = self.model.inference(img)
            masks = None

        end = time.perf_counter()
        logger.info("seg time usage %f", end - start)

        # 构造结果[{},{},{}]
        res = []
        for i in range(len(boxes)):
            if scores[i] < min_score:
                logger.debug("drop %s score %f", labels[i], scores[i])
                continue

            mask = {}
            x1, y1, x2, y2 = boxes[i][0:4]
            mask["bbox"] = [
                int(x1),
                int(y1),
                int(x2),
                int(y2),
            ]
            mask["rect_rotated"] = [
                rects_rotated[i][0][0],
                rects_rotated[i][0][1],
                rects_rotated[i][1][0],
                rects_rotated[i][1][1],
                rects_rotated[i][2],
            ]
            mask["area"] = abs(x2 - x1) * abs(y2 - y1)
            mask["label"] = labels[i]
            mask["score"] = scores[i]

            if masks and i < len(masks):
                mask["segmentation"] = masks[i]
                mask["points_num"] = np.sum(masks[i] != 0)
            else:
                mask["segmentation"] = None
                mask["points_num"] = 0

            res.append(mask)
            logger.debug(
                "accept %s with score=%f area=%.2f",
                mask["label"],
                mask["score"],
                mask["area"],
            )

        # 排序和过滤
        if self.with_mask is True:
            res.sort(key=lambda x: x["points_num"], reverse=True)
        else:
            res.sort(key=lambda x: x["area"], reverse=True)

        num = min(max_num, len(res))
        end = time.perf_counter()
        logger.debug("Finished segment, time usage %f", end - start)
        return res[:num]
