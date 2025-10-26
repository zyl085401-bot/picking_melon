"""
Descripttion: 图像分割服务
version: 3.0
Author: 崔译文
Date: 2023-12-18 09:00:50
@LastEditors: 崔译文
@LastEditTime: 2024-05-23 16:15:39
"""

import rclpy
import os
import yaml
import cv2
import random
import numpy as np
from rclpy.node import Node
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
from papjia_vision_interface.srv import SegImage
from papjia_vision_interface.msg import Rect, Object2d, Objects2d, RectRotated
from geometry_msgs.msg import Vector3
from papjia_logger.logger import logger
from sensor_msgs.msg import Image

from datetime import datetime


class ImageSegService(Node):
    """图像分割服务的ROS接口类

    Args:
        Node (_type_): ROS节点
    """

    def __init__(self):
        super().__init__("papjia_detector_node")
        # 声明ROS参数
        self.declare_parameters(
            namespace="",
            parameters=[
                ("service_topic", ""),
                ("model_type", ""),
                ("result_image_topic", ""),
                ("data_root", ""),
                ("model_path", ""),
                ("device", "cuda"),
                ("labels", [""]),
                ("sample_image", ""),
                ("prepare_times", 0),
                ("model_cfg", ""),
                ("resource_dir", ""),
                ("channels", ""),
                ("rect", [0]),
                ("with_mask", True),
                ("rect_height_ratio", 1.0),
            ],
        )
        self.result_image_topic = self.get_parameter("result_image_topic").get_parameter_value().string_value
        self.seg_image_publisher = self.create_publisher(Image, self.result_image_topic, 1)
        # 获取服务名称
        self.service_topic = self.get_parameter("service_topic").get_parameter_value().string_value
        # 加载channels顺序
        self.channels = self.get_parameter("channels").get_parameter_value().string_value
        # 加载模型
        model_type = self.get_parameter("model_type").get_parameter_value().string_value
        # 加载rect用来过滤
        self.rect = self.get_parameter("rect").get_parameter_value().integer_array_value
        # 是否使用mask
        self.with_mask = self.get_parameter("with_mask").get_parameter_value().bool_value
        # 是否使用mask
        self.rect_height_ratio = self.get_parameter("rect_height_ratio").get_parameter_value().double_value
        # 模型配置文件
        config = {
            "data_root": self.get_parameter("resource_dir").get_parameter_value().string_value,
            "model_path": self.get_parameter("model_path").get_parameter_value().string_value,
            "device": self.get_parameter("device").get_parameter_value().string_value,
            "labels": self.get_parameter("labels").get_parameter_value().string_array_value,
            "sample_image": self.get_parameter("sample_image").get_parameter_value().string_value,
            "prepare_times": self.get_parameter("prepare_times").get_parameter_value().integer_value,
            "with_mask": self.with_mask
        }
        if model_type == "detectron2":  # detectron2推理器
            from papjia_detector.detectron2 import MaskDetector as Detectron2

            config["model_cfg"] = self.get_parameter("model_cfg").get_parameter_value().string_value
            self.detector = Detectron2(config)
        elif model_type == "pytorch":  # 基础的pytorch推理
            from papjia_detector.pytorch import MaskDetector as NormalDetector

            self.detector = NormalDetector(config)
        elif model_type == "yolo":
            from papjia_detector.yolo_detector import MaskDetector as YOLODetector

            self.detector = YOLODetector(config)
        else:
            logger.error("Unknown model type %s", model_type)
        self.result_frame = "camera_link"
        # cv bridge
        self.bridge = CvBridge()
        # load service
        self.seg_service = self.create_service(SegImage, self.service_topic, self.seg_image_callback)

    def seg_image_callback(self, request, response):
        if request.image.encoding == "yuv422_yuy2":
            cv_image_yuv = self.bridge.imgmsg_to_cv2(request.image, desired_encoding="passthrough")
            img = cv2.cvtColor(cv_image_yuv, cv2.COLOR_YUV2BGR_YUYV)
        else:
            img = self.bridge.imgmsg_to_cv2(request.image, "8UC3")
        self.result_frame = request.image.header.frame_id
        logger.debug("begin to segment...")
        logger.debug("image size(%d, %d)", img.shape[1], img.shape[0])
        origin_size = img.shape[0:2]
        if self.channels == "rgb":
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            logger.debug("from BGR to RGB")
        if request.max_num > 0:
            objs = self.detector.seg(img, request.max_num, request.min_score)
        else:
            objs = self.detector.seg(img)
        logger.debug("finished segment")
        seg_mask = None
        if len(objs) > 0:
            if self.with_mask is True:
                seg_mask_size = objs[0]["segmentation"].shape[0:2]
                seg_mask = np.zeros(seg_mask_size, dtype=np.uint8)
            for obj in objs:
                object2d = Object2d()
                # 使用rect过滤
                x1, y1, x2, y2 = self.rect
                rect = Rect()
                rect.x1 = obj["bbox"][0]
                rect.y1 = obj["bbox"][1]
                rect.x2 = obj["bbox"][2]
                rect.y2 = obj["bbox"][3]
                if self.rect_height_ratio < 0.98:
                    rect.y1 = int(rect.y2 - (rect.y2 - rect.y1) * self.rect_height_ratio)

                if rect.x1 < x1 or rect.x2 > x2 or rect.y1 < y1 or rect.y2 > y2:
                    logger.warn("filter({}) by rect({})".format([rect.x1, rect.y1, rect.x2, rect.y2], [x1, y1, x2, y2]))
                    continue
                if request.allowed_roi and len(request.allowed_roi) == 4:
                    x1, y1, x2, y2 = request.allowed_roi
                    if rect.x1 < x1 or rect.x2 > x2 or rect.y1 < y1 or rect.y2 > y2:
                        logger.warn("filter({}) by allowed roi({})".format([rect.x1, rect.y1, rect.x2, rect.y2], [x1, y1, x2, y2]))
                        continue
                if request.allowed_categories and len(request.allowed_categories) > 0:
                    if obj["label"] not in request.allowed_categories:
                        logger.warn("filter({}) by allowed categories({})".format(obj["label"], request.allowed_categories))
                        continue
                object2d.category = obj["label"]
                object2d.score = obj["score"]
                object2d.rect = rect
                if "rect_rotated" in obj:
                    rect_rotated = RectRotated()
                    rect_rotated.center_x = int(obj["rect_rotated"][0])
                    rect_rotated.center_y = int(obj["rect_rotated"][1])
                    rect_rotated.width = int(obj["rect_rotated"][2])
                    rect_rotated.height = int(obj["rect_rotated"][3])
                    rect_rotated.angle = obj["rect_rotated"][4]
                    object2d.rect_rotated = rect_rotated
                if self.with_mask is True:
                    seg_mask[obj["segmentation"] != 0] = len(response.objects.objects) + 1
                    object2d.points_num = int(obj["points_num"])
                response.objects.objects.append(object2d)
                logger.info("Found obj {} with score {}".format(object2d.category, object2d.score))

            if self.with_mask is True:
                # 分割的掩码和原始图像大小不一致需要特殊处理
                if origin_size[0] != seg_mask_size[0] or origin_size[1] != seg_mask_size[1]:
                    logger.warn("image size({}) != seg mask size({})".format(origin_size, seg_mask_size))
                    h, w = origin_size[:2]
                    hh, ww = seg_mask.shape[:2]
                    rh = h / hh
                    rw = w / ww
                    seg_mask = cv2.resize(seg_mask, (w, h), interpolation=cv2.INTER_AREA)
                    for obj in enumerate(response.objects.objects):
                        obj.rect.x1 = int(obj.rect.x1 * rw)
                        obj.rect.y1 = int(obj.rect.y1 * rh)
                        obj.rect.x2 = int(obj.rect.x2 * rw)
                        obj.rect.y2 = int(obj.rect.y2 * rh)
                # to_do
                # 用flag控制是否保存彩色原始图像 & 掩码 & 标签【object2d.category】& 分数【object2d.score】
            response.mask = self.bridge.cv2_to_imgmsg(seg_mask)
            response.objs_num = len(response.objects.objects)
            response.with_mask = self.with_mask
            response.success = True
            self.publish_segment_result_image(img, response)
            #####################################################
            self.save_results(img, seg_mask, response)
            ####################################################
        return response
    
######################################################################################
    def save_results(self, img, seg_mask, response):
        """保存分割结果（原图、掩码、类别、分数、框信息）"""
        # 固定根目录
        root_dir = "/workspace/src/papjia_melon/papjia_melon_calibration/test_savedata/data_point_images/detector"
        # 每天一个子文件夹
        today = datetime.now().strftime("%Y%m%d")
        base_dir = os.path.join(root_dir, today)
        os.makedirs(base_dir, exist_ok=True)

        # 时间戳文件名前缀
        timestamp = datetime.now().strftime("%H%M%S")

        # 1. 保存原始图像
        origin_path = os.path.join(base_dir, f"{timestamp}_origin.jpg")
        cv2.imwrite(origin_path, img)

        # 2. 保存掩码图像
        mask_path = None
        if seg_mask is not None:
            mask_path = os.path.join(base_dir, f"{timestamp}_mask.png")
            cv2.imwrite(mask_path, seg_mask)

        # 3. 保存元数据（标签、分数、边界框等）
        meta = []
        for obj in response.objects.objects:
            item = {
                "category": obj.category,
                "score": float(obj.score),
                "bbox": [obj.rect.x1, obj.rect.y1, obj.rect.x2, obj.rect.y2],
            }
            if obj.rect_rotated.width > 0:  # 有旋转框才保存
                item["rect_rotated"] = {
                    "cx": obj.rect_rotated.center_x,
                    "cy": obj.rect_rotated.center_y,
                    "w": obj.rect_rotated.width,
                    "h": obj.rect_rotated.height,
                    "angle": obj.rect_rotated.angle,
                }
            meta.append(item)

        meta_path = os.path.join(base_dir, f"{timestamp}_meta.yaml")
        with open(meta_path, "w") as f:
            yaml.dump(meta, f, allow_unicode=True)

        # 4. 保存可视化结果（方便快速查看）
        vis_img = img.copy()
        if seg_mask is not None:
            color_mask = np.zeros_like(img)
            for i in np.unique(seg_mask):
                if i == 0:  # 背景跳过
                    continue
                color = [random.randint(0, 255) for _ in range(3)]
                color_mask[seg_mask == i] = color
            vis_img = cv2.addWeighted(vis_img, 0.6, color_mask, 0.4, 0)

        for obj in response.objects.objects:
            rect = obj.rect
            cv2.rectangle(vis_img, (rect.x1, rect.y1), (rect.x2, rect.y2), (0, 255, 0), 2)
            cv2.putText(vis_img, f"{obj.category} {obj.score:.2f}",
                        (rect.x1, max(0, rect.y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        vis_path = os.path.join(base_dir, f"{timestamp}_vis.jpg")
        cv2.imwrite(vis_path, vis_img)

        logger.info(f"结果已保存: {origin_path}, {mask_path}, {meta_path}, {vis_path}")

######################################################################################
    def publish_segment_result_image(self, img, res):
        h, w = img.shape[0:2]
        # 掩码图像
        img2 = np.zeros((h, w, 3), np.uint8)
        if self.with_mask:
            # 转换为Opencv格式图像
            mask = self.bridge.imgmsg_to_cv2(res.mask)
            img2[mask > 0, :] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
            img_blending = cv2.addWeighted(src1=img, alpha=0.5, src2=img2, beta=0.5, gamma=0.0)
        else:
            img_blending = img
        for i in range(res.objs_num):
            rect = res.objects.objects[i].rect
            # 添加rect
            cv2.rectangle(
                img_blending,
                (rect.x1, rect.y1),
                (rect.x2, rect.y2),
                (100, 200, 0),
                1,
                lineType=cv2.LINE_AA,
            )
            # 添加类别
            cv2.putText(
                img_blending,
                res.objects.objects[i].category,
                (rect.x1, max(rect.y1 - 5, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 200, 200),
                1,
            )
        segment_rgb_mgs = self.bridge.cv2_to_imgmsg(img_blending, "bgr8")
        segment_rgb_mgs.header.frame_id = self.result_frame
        self.seg_image_publisher.publish(segment_rgb_mgs)


def main(args=None):
    rclpy.init(args=args)
    node = ImageSegService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()