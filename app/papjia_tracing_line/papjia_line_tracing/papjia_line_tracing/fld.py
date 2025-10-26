"""
@Descripttion: 直线检测
@version: 1.0
@Author: 崔译文
@Date: 2024-03-07 15:24:40
@LastEditors: 崔译文
@LastEditTime: 2024-03-26 16:14:10
"""

import cv2


class FastLineDetector:
    def __init__(
        self, length_threshold=20, canny_th1=150, canny_th2=220, canny_aperture_size=5, do_merge=True
    ):
        """初始化检测器

        Args:
            length_threshold (int, optional): 直线段最小长度. Defaults to 20.
            canny_th1 (int, optional): canny检测的第一个阈值. Defaults to 150.
            canny_th2 (int, optional): canny检测的第二个阈值. Defaults to 220.
            canny_aperture_size (int, optional): canny检测中sobel算子的孔径大小. Defaults to 5.
            do_merge (bool, optional): 是否增量合并线段. Defaults to True.
        """
        self.length_threshold = length_threshold
        self.canny_th1 = canny_th1
        self.canny_th2 = canny_th2
        self.canny_aperture_size = canny_aperture_size
        self.do_merge = do_merge
        self.fld = cv2.ximgproc.createFastLineDetector(
            length_threshold=self.length_threshold,
            canny_th1=self.canny_th1,
            canny_th2=self.canny_th2,
            canny_aperture_size=self.canny_aperture_size,
            do_merge=self.do_merge,
        )

    def detect(self, img, show=False, save=False):
        """直线段检测

        Args:
            img (np.ndarray): 彩色图像
            show (bool, optional): 是否可视化检测结果. Defaults to False.

        Returns:
            np.ndarray: 直线在图像中的坐标[n, 4]
        """
        # 执行检测结果
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dlines = self.fld.detect(gray)
        lines = []
        if dlines is not None:
            for dline in dlines:
                x0, y0, x1, y1 = dline[0][0:4]
                if y0 > y1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                lines.append([x0, y0, x1, y1])
        return lines
