#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外观检测工具模块

提供表面缺陷检测、外观检测、瑕疵识别功能。

Author: Vision System Team
Date: 2026-01-30
"""

import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import ToolParameter, ToolRegistry, VisionAlgorithmToolBase
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException
from utils.image_processing_utils import (
    preprocess_image,
    resize_image,
    remove_duplicate_defects,
    classify_defect,
    calculate_confidence,
    get_defect_name,
    draw_detection_result
)


class DetectionType(Enum):
    """检测类型"""

    SURFACE_DEFECT = "surface_defect"
    APPEARANCE = "appearance"
    BLEMISH = "blemish"
    ALL = "all"


class DefectType(Enum):
    """缺陷类型"""

    SCRATCH = "scratch"
    DENT = "dent"
    STAIN = "stain"
    FOREIGN_MATTER = "foreign_matter"
    CRACK = "crack"
    MISSING_MATERIAL = "missing_material"
    ALL = "all"


@ToolRegistry.register
class AppearanceDetector(VisionAlgorithmToolBase):
    """
    外观检测工具

    支持表面缺陷检测、外观检测、瑕疵识别。

    参数说明：
    - detection_type: 检测类型
    - defect_type: 缺陷类型
    - threshold: 检测阈值
    - min_area: 最小缺陷面积
    - max_area: 最大缺陷面积
    - use_roi: 是否使用ROI
    - draw_result: 是否绘制结果
    """

    tool_name = "外观检测"
    tool_category = "Vision"
    tool_description = "检测表面缺陷和外观瑕疵"

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "detection_type": ToolParameter(
            name="检测类型",
            param_type="enum",
            default="all",
            description="检测类型",
            options=["all", "surface_defect", "appearance", "blemish"],
        ),
        "defect_type": ToolParameter(
            name="缺陷类型",
            param_type="enum",
            default="all",
            description="缺陷类型",
            options=[
                "all",
                "scratch",
                "dent",
                "stain",
                "foreign_matter",
                "crack",
                "missing_material",
            ],
        ),
        "threshold": ToolParameter(
            name="检测阈值",
            param_type="float",
            default=0.5,
            description="检测阈值",
            min_value=0.1,
            max_value=1.0,
        ),
        "min_area": ToolParameter(
            name="最小面积",
            param_type="integer",
            default=100,
            description="最小缺陷面积",
            min_value=10,
        ),
        "max_area": ToolParameter(
            name="最大面积",
            param_type="integer",
            default=10000,
            description="最大缺陷面积",
            min_value=100,
        ),
        "use_roi": ToolParameter(
            name="使用ROI",
            param_type="boolean",
            default=False,
            description="是否使用感兴趣区域",
        ),
        "draw_result": ToolParameter(
            name="绘制结果",
            param_type="boolean",
            default=True,
            description="是否绘制检测结果",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("detection_type", "all")
        self.set_param("defect_type", "all")
        self.set_param("threshold", 0.5)
        self.set_param("min_area", 100)
        self.set_param("max_area", 10000)
        self.set_param("use_roi", False)
        self.set_param("draw_result", True)

    def _run_impl(self):
        """执行外观检测"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data
        output_image = input_image.copy()

        # 获取参数
        detection_type = self.get_param("detection_type", "all")
        defect_type = self.get_param("defect_type", "all")
        threshold = self.get_param("threshold", 0.5)
        min_area = self.get_param("min_area", 100)
        max_area = self.get_param("max_area", 10000)
        use_roi = self.get_param("use_roi", False)
        draw_result = self.get_param("draw_result", True)

        # 转换为灰度
        gray_image = preprocess_image(input_image)

        # 应用高斯模糊降噪
        blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)

        # 边缘检测
        edges = cv2.Canny(blurred, 50, 150)

        # 查找轮廓
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 过滤和分析缺陷
        defects = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # 面积过滤
            if area < min_area or area > max_area:
                continue

            # 计算轮廓特征
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter**2)
            else:
                circularity = 0

            # 边界框
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0

            # 缺陷分类
            defect_class = classify_defect(
                contour, area, circularity, aspect_ratio
            )

            # 根据参数过滤缺陷类型
            if defect_type != "all" and defect_class != defect_type:
                continue

            # 计算置信度
            confidence = calculate_confidence(contour, area, circularity)

            # 阈值过滤
            if confidence < threshold:
                continue

            defect_info = {
                "type": defect_class,
                "area": area,
                "confidence": confidence,
                "location": {"x": x, "y": y, "width": w, "height": h},
                "contour": contour.tolist(),
            }
            defects.append(defect_info)

            # 绘制结果
            if draw_result:
                output_image = draw_detection_result(output_image, [defect_info])

        # 保存结果
        self._result_data = ResultData()
        self._result_data.set_value("defects", defects)
        self._result_data.set_value("defect_count", len(defects))
        self._result_data.set_value(
            "status", "OK" if defects else "No defects found"
        )
        self._result_data.set_value("detection_type", detection_type)
        self._result_data.set_value("defect_type", defect_type)

        # 设置输出图像
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image

        self._logger.info(f"外观检测完成: 发现 {len(defects)} 个缺陷")




@ToolRegistry.register
class SurfaceDefectDetector(VisionAlgorithmToolBase):
    """
    表面缺陷检测器

    专注于表面缺陷的高精度检测。

    参数说明：
    - sensitivity: 检测灵敏度
    - min_size: 最小缺陷尺寸
    - max_size: 最大缺陷尺寸
    - use_multiscale: 是否使用多尺度检测
    - adaptive_threshold: 是否使用自适应阈值
    """

    tool_name = "表面缺陷检测"
    tool_category = "Vision"
    tool_description = "高精度表面缺陷检测"

    PARAM_DEFINITIONS = {
        "sensitivity": ToolParameter(
            name="检测灵敏度",
            param_type="float",
            default=0.6,
            description="检测灵敏度",
            min_value=0.1,
            max_value=1.0,
        ),
        "min_size": ToolParameter(
            name="最小缺陷尺寸",
            param_type="integer",
            default=50,
            description="最小缺陷尺寸",
            min_value=10,
        ),
        "max_size": ToolParameter(
            name="最大缺陷尺寸",
            param_type="integer",
            default=5000,
            description="最大缺陷尺寸",
            min_value=100,
        ),
        "use_multiscale": ToolParameter(
            name="使用多尺度",
            param_type="boolean",
            default=True,
            description="是否使用多尺度检测",
        ),
        "adaptive_threshold": ToolParameter(
            name="自适应阈值",
            param_type="boolean",
            default=True,
            description="是否使用自适应阈值",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("sensitivity", 0.6)
        self.set_param("min_size", 50)
        self.set_param("max_size", 5000)
        self.set_param("use_multiscale", True)
        self.set_param("adaptive_threshold", True)

    def _run_impl(self):
        """执行表面缺陷检测"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data
        output_image = input_image.copy()

        # 获取参数
        sensitivity = self.get_param("sensitivity", 0.6)
        min_size = self.get_param("min_size", 50)
        max_size = self.get_param("max_size", 5000)
        use_multiscale = self.get_param("use_multiscale", True)
        adaptive_threshold = self.get_param("adaptive_threshold", True)

        # 转换为灰度
        gray_image = preprocess_image(input_image)

        # 多尺度检测
        if use_multiscale:
            defects = []
            scales = [0.5, 1.0, 1.5]

            for scale in scales:
                scaled_image = self._resize_image(gray_image, scale)
                scale_defects = self._detect_at_scale(
                    scaled_image,
                    sensitivity,
                    min_size,
                    max_size,
                    adaptive_threshold,
                )

                # 转换回原始坐标
                for defect in scale_defects:
                    defect["location"]["x"] = int(
                        defect["location"]["x"] / scale
                    )
                    defect["location"]["y"] = int(
                        defect["location"]["y"] / scale
                    )
                    defect["location"]["width"] = int(
                        defect["location"]["width"] / scale
                    )
                    defect["location"]["height"] = int(
                        defect["location"]["height"] / scale
                    )
                    defects.append(defect)
        else:
            defects = self._detect_at_scale(
                gray_image, sensitivity, min_size, max_size, adaptive_threshold
            )

        # 去重
        defects = self._remove_duplicates(defects)

        # 绘制结果
        for defect in defects:
            self._draw_defect(output_image, defect)

        # 保存结果
        self._result_data = ResultData()
        self._result_data.set_value("defects", defects)
        self._result_data.set_value("defect_count", len(defects))
        self._result_data.set_value(
            "status", "OK" if defects else "No defects found"
        )

        # 设置输出图像
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image

        self._logger.info(f"表面缺陷检测完成: 发现 {len(defects)} 个缺陷")

    def _resize_image(self, image: np.ndarray, scale: float) -> np.ndarray:
        """调整图像大小"""
        new_width = int(image.shape[1] * scale)
        new_height = int(image.shape[0] * scale)
        return cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_LINEAR
        )

    def _detect_at_scale(
        self,
        image: np.ndarray,
        sensitivity: float,
        min_size: int,
        max_size: int,
        adaptive_threshold: bool,
    ) -> List[Dict[str, Any]]:
        """在特定尺度上检测缺陷"""
        defects = []

        # 应用高斯模糊
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # 阈值处理
        if adaptive_threshold:
            binary = cv2.adaptiveThreshold(
                blurred,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2,
            )
        else:
            _, binary = cv2.threshold(
                blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )

        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 分析轮廓
        for contour in contours:
            area = cv2.contourArea(contour)

            if area < min_size or area > max_size:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            perimeter = cv2.arcLength(contour, True)
            circularity = (
                4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
            )

            defect_type = classify_defect(
                contour, area, circularity, aspect_ratio
            )
            confidence = calculate_confidence(contour, area, circularity)

            if confidence >= sensitivity:
                defect_info = {
                    "type": defect_type,
                    "area": area,
                    "confidence": confidence,
                    "location": {"x": x, "y": y, "width": w, "height": h},
                }
                defects.append(defect_info)

        return defects

    def _remove_duplicates(
        self, defects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去除重复缺陷"""
        return remove_duplicate_defects(defects)


