#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像分析工具模块

提供各种图像分析工具，包括斑点分析、像素计数、直方图等。

Author: Vision System Team
Date: 2026-01-05
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
from data.image_data import ROI, ImageData, ResultData
from utils.exceptions import ToolExecutionException as VisionAlgorithmException


@ToolRegistry.register
class BlobFind(VisionAlgorithmToolBase):
    """
    斑点分析工具

    对图像进行斑点分析，检测和分析图像中的连通区域。

    参数说明：
    - threshold_method: 阈值方法 (binary/binary_inv/trunc/tozero/tozero_inv/otsu)
    - threshold_value: 阈值，当threshold_method为otsu时无效
    - min_area: 最小面积
    - max_area: 最大面积
    - min_circularity: 最小圆度 (0-1)
    - max_circularity: 最大圆度 (0-1)
    - min_aspect_ratio: 最小长宽比
    - max_aspect_ratio: 最大长宽比
    - fill_holes: 是否填充孔洞
    - draw_contours: 是否绘制轮廓
    - draw_centroids: 是否绘制中心点
    - draw_bounding_boxes: 是否绘制外接矩形
    """

    tool_name = "斑点分析"
    tool_category = "Analysis"
    tool_description = "对图像进行斑点检测和分析"

    THRESHOLD_METHODS = {
        "binary": cv2.THRESH_BINARY,
        "binary_inv": cv2.THRESH_BINARY_INV,
        "trunc": cv2.THRESH_TRUNC,
        "tozero": cv2.THRESH_TOZERO,
        "tozero_inv": cv2.THRESH_TOZERO_INV,
        "otsu": cv2.THRESH_OTSU,
    }

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "threshold_method": ToolParameter(
            name="阈值方法",
            param_type="enum",
            default="binary",
            description="阈值方法",
            options=[
                "binary",
                "binary_inv",
                "trunc",
                "tozero",
                "tozero_inv",
                "otsu",
            ],
        ),
        "threshold_value": ToolParameter(
            name="阈值",
            param_type="integer",
            default=127,
            description="阈值",
            min_value=0,
            max_value=255,
        ),
        "min_area": ToolParameter(
            name="最小面积",
            param_type="integer",
            default=100,
            description="最小面积",
            min_value=1,
            max_value=1000000,
        ),
        "max_area": ToolParameter(
            name="最大面积",
            param_type="integer",
            default=100000,
            description="最大面积",
            min_value=1,
            max_value=10000000,
        ),
        "min_circularity": ToolParameter(
            name="最小圆度",
            param_type="float",
            default=0.1,
            description="最小圆度",
            min_value=0.0,
            max_value=1.0,
        ),
        "max_circularity": ToolParameter(
            name="最大圆度",
            param_type="float",
            default=1.0,
            description="最大圆度",
            min_value=0.0,
            max_value=1.0,
        ),
        "min_aspect_ratio": ToolParameter(
            name="最小长宽比",
            param_type="float",
            default=0.1,
            description="最小长宽比",
            min_value=0.01,
            max_value=100.0,
        ),
        "max_aspect_ratio": ToolParameter(
            name="最大长宽比",
            param_type="float",
            default=10.0,
            description="最大长宽比",
            min_value=0.01,
            max_value=100.0,
        ),
        "fill_holes": ToolParameter(
            name="填充孔洞",
            param_type="boolean",
            default=True,
            description="填充孔洞",
        ),
        "draw_contours": ToolParameter(
            name="绘制轮廓",
            param_type="boolean",
            default=True,
            description="绘制轮廓",
        ),
        "draw_centroids": ToolParameter(
            name="绘制中心点",
            param_type="boolean",
            default=True,
            description="绘制中心点",
        ),
        "draw_bounding_boxes": ToolParameter(
            name="绘制外接矩形",
            param_type="boolean",
            default=True,
            description="绘制外接矩形",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("threshold_method", "binary")
        self.set_param("threshold_value", 127)
        self.set_param("min_area", 100)
        self.set_param("max_area", 100000)
        self.set_param("min_circularity", 0.1)
        self.set_param("max_circularity", 1.0)
        self.set_param("min_aspect_ratio", 0.1)
        self.set_param("max_aspect_ratio", 10.0)
        self.set_param("fill_holes", True)
        self.set_param("draw_contours", True)
        self.set_param("draw_centroids", True)
        self.set_param("draw_bounding_boxes", True)

    def _run_impl(self):
        """执行斑点分析"""
        if not self.has_input():
            raise VisionAlgorithmException("无输入图像")

        input_image = self._input_data.data
        gray = input_image.copy()

        # 如果是彩色图像，转换为灰度图
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

        # 获取参数
        threshold_method_name = self.get_param("threshold_method", "binary")
        threshold_value = self.get_param("threshold_value", 127)
        min_area = self.get_param("min_area", 100)
        max_area = self.get_param("max_area", 100000)
        min_circularity = self.get_param("min_circularity", 0.1)
        max_circularity = self.get_param("max_circularity", 1.0)
        min_aspect_ratio = self.get_param("min_aspect_ratio", 0.1)
        max_aspect_ratio = self.get_param("max_aspect_ratio", 10.0)
        fill_holes = self.get_param("fill_holes", True)
        draw_contours = self.get_param("draw_contours", True)
        draw_centroids = self.get_param("draw_centroids", True)
        draw_bounding_boxes = self.get_param("draw_bounding_boxes", True)

        # 确定阈值方法
        threshold_method = self.THRESHOLD_METHODS.get(
            threshold_method_name, cv2.THRESH_BINARY
        )

        # 执行阈值处理
        if threshold_method_name == "otsu":
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:
            _, binary = cv2.threshold(
                gray, threshold_value, 255, threshold_method
            )

        # 填充孔洞
        if fill_holes:
            binary = cv2.morphologyEx(
                binary, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
            )

        # 查找轮廓
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 创建输出图像
        output = (
            cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            if len(input_image.shape) == 2
            else input_image.copy()
        )

        # 分析每个轮廓 - 设置最大数量限制以避免内存问题
        max_blobs = 1000  # 最多保留1000个斑点
        blobs = []
        blob_count = 0
        for i, contour in enumerate(contours):
            # 计算面积
            area = cv2.contourArea(contour)

            # 面积过滤
            if area < min_area or area > max_area:
                continue

            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)

            # 计算长宽比
            aspect_ratio = float(w) / h if h != 0 else 0

            # 长宽比过滤
            if (
                aspect_ratio < min_aspect_ratio
                or aspect_ratio > max_aspect_ratio
            ):
                continue

            # 计算圆度
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                circularity = 0
            else:
                circularity = 4 * np.pi * area / (perimeter * perimeter)

            # 圆度过滤
            if circularity < min_circularity or circularity > max_circularity:
                continue

            # 计算中心点
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # 计算最小外接圆
            (cx_circle, cy_circle), radius = cv2.minEnclosingCircle(contour)

            # 保存斑点信息 - 只存储必要的信息，不存储完整轮廓以避免内存泄漏
            blob = {
                "id": i,
                "area": float(area),
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "aspect_ratio": float(aspect_ratio),
                "circularity": float(circularity) if circularity else 0.0,
                "cx": int(cx),
                "cy": int(cy),
                # 不保存 "contour": contour，避免内存泄漏
            }
            blobs.append(blob)
            blob_count += 1

            # 达到最大数量后停止保存
            if blob_count >= max_blobs:
                self._logger.warning(
                    f"斑点数量已达到最大限制 {max_blobs}，停止保存"
                )
                break

            # 绘制结果
            if draw_contours:
                cv2.drawContours(output, [contour], -1, (0, 255, 0), 2)

            if draw_bounding_boxes:
                cv2.rectangle(output, (x, y), (x + w, y + h), (0, 0, 255), 2)

            if draw_centroids:
                cv2.circle(output, (cx, cy), 5, (255, 0, 0), -1)

        # 设置输出数据
        self._output_data = self._input_data.copy()
        self._output_data.data = output

        # 设置结果
        self._result_data = ResultData()
        self._result_data.set_value("blob_count", len(blobs))
        self._result_data.set_value("blobs", blobs)

        self._logger.info(f"斑点分析完成，检测到 {len(blobs)} 个斑点")


@ToolRegistry.register
class PixelCount(VisionAlgorithmToolBase):
    """
    像素计数工具

    统计图像中不同区域的像素数量。

    参数说明：
    - threshold_method: 阈值方法
    - threshold_value: 阈值
    - lower_bound: 像素值下限（用于范围计数）
    - upper_bound: 像素值上限（用于范围计数）
    - count_black: 统计黑色像素
    - count_white: 统计白色像素
    - count_range: 统计指定范围像素
    """

    tool_name = "像素计数"
    tool_category = "Analysis"
    tool_description = "统计图像中不同区域的像素数量"

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "threshold_method": ToolParameter(
            name="阈值方法",
            param_type="enum",
            default="binary",
            description="阈值方法",
            options=[
                "binary",
                "binary_inv",
                "trunc",
                "tozero",
                "tozero_inv",
                "otsu",
            ],
        ),
        "threshold_value": ToolParameter(
            name="阈值",
            param_type="integer",
            default=127,
            description="阈值",
            min_value=0,
            max_value=255,
        ),
        "lower_bound": ToolParameter(
            name="像素值下限",
            param_type="integer",
            default=0,
            description="像素值下限",
            min_value=0,
            max_value=255,
        ),
        "upper_bound": ToolParameter(
            name="像素值上限",
            param_type="integer",
            default=255,
            description="像素值上限",
            min_value=0,
            max_value=255,
        ),
        "count_black": ToolParameter(
            name="统计黑色像素",
            param_type="boolean",
            default=True,
            description="统计黑色像素",
        ),
        "count_white": ToolParameter(
            name="统计白色像素",
            param_type="boolean",
            default=True,
            description="统计白色像素",
        ),
        "count_range": ToolParameter(
            name="统计指定范围",
            param_type="boolean",
            default=False,
            description="统计指定范围像素",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("threshold_method", "binary")
        self.set_param("threshold_value", 127)
        self.set_param("lower_bound", 0)
        self.set_param("upper_bound", 255)
        self.set_param("count_black", True)
        self.set_param("count_white", True)
        self.set_param("count_range", False)

    def _run_impl(self):
        """执行像素计数"""
        if not self.has_input():
            raise VisionAlgorithmException("无输入图像")

        input_image = self._input_data.data
        gray = input_image.copy()

        # 如果是彩色图像，转换为灰度图
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

        # 获取参数
        threshold_method_name = self.get_param("threshold_method", "binary")
        threshold_value = self.get_param("threshold_value", 127)
        lower_bound = self.get_param("lower_bound", 0)
        upper_bound = self.get_param("upper_bound", 255)
        count_black = self.get_param("count_black", True)
        count_white = self.get_param("count_white", True)
        count_range = self.get_param("count_range", False)

        # 执行阈值处理
        threshold_method = BlobFind.THRESHOLD_METHODS.get(
            threshold_method_name, cv2.THRESH_BINARY
        )
        _, binary = cv2.threshold(gray, threshold_value, 255, threshold_method)

        # 像素计数
        total_pixels = gray.shape[0] * gray.shape[1]

        results = {"total_pixels": total_pixels}

        if count_black:
            black_pixels = cv2.countNonZero(255 - binary)
            results["black_pixels"] = black_pixels
            results["black_ratio"] = black_pixels / total_pixels

        if count_white:
            white_pixels = cv2.countNonZero(binary)
            results["white_pixels"] = white_pixels
            results["white_ratio"] = white_pixels / total_pixels

        if count_range:
            range_pixels = cv2.inRange(gray, lower_bound, upper_bound)
            range_count = cv2.countNonZero(range_pixels)
            results["range_pixels"] = range_count
            results["range_ratio"] = range_count / total_pixels

        # 设置输出数据
        self._output_data = self._input_data.copy()

        # 设置结果
        self._result_data = ResultData()
        for key, value in results.items():
            self._result_data.set_value(key, value)

        self._logger.info(f"像素计数完成，总像素数: {total_pixels}")


@ToolRegistry.register
class Histogram(VisionAlgorithmToolBase):
    """
    直方图工具

    生成图像的直方图。

    参数说明：
    - histogram_type: 直方图类型 (gray/color)
    - hist_size: 直方图大小
    - range_min: 像素值范围最小值
    - range_max: 像素值范围最大值
    - show_histogram: 是否显示直方图
    """

    tool_name = "直方图"
    tool_category = "Analysis"
    tool_description = "生成图像的直方图"

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "histogram_type": ToolParameter(
            name="直方图类型",
            param_type="enum",
            default="gray",
            description="直方图类型",
            options=["gray", "color"],
        ),
        "hist_size": ToolParameter(
            name="直方图大小",
            param_type="integer",
            default=256,
            description="直方图大小",
            min_value=2,
            max_value=256,
        ),
        "range_min": ToolParameter(
            name="像素值下限",
            param_type="integer",
            default=0,
            description="像素值范围最小值",
            min_value=0,
            max_value=255,
        ),
        "range_max": ToolParameter(
            name="像素值上限",
            param_type="integer",
            default=255,
            description="像素值范围最大值",
            min_value=0,
            max_value=255,
        ),
        "show_histogram": ToolParameter(
            name="显示直方图",
            param_type="boolean",
            default=True,
            description="显示直方图",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("histogram_type", "gray")
        self.set_param("hist_size", 256)
        self.set_param("range_min", 0)
        self.set_param("range_max", 255)
        self.set_param("show_histogram", True)

    def _run_impl(self):
        """生成直方图"""
        if not self.has_input():
            raise VisionAlgorithmException("无输入图像")

        input_image = self._input_data.data
        histogram_type = self.get_param("histogram_type", "gray")
        hist_size = self.get_param("hist_size", 256)
        range_min = self.get_param("range_min", 0)
        range_max = self.get_param("range_max", 255)
        show_histogram = self.get_param("show_histogram", True)

        # 设置输出数据
        self._output_data = self._input_data.copy()

        # 生成直方图
        if histogram_type == "gray":
            # 转换为灰度图
            if len(input_image.shape) == 3:
                gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = input_image

            # 计算直方图
            hist = cv2.calcHist(
                [gray], [0], None, [hist_size], [range_min, range_max]
            )

            # 归一化
            hist = cv2.normalize(hist, hist).flatten()

            # 设置结果
            self._result_data = ResultData()
            self._result_data.set_value("histogram", hist)
            self._result_data.set_value("histogram_type", "gray")

        elif histogram_type == "color":
            # 分离通道
            channels = cv2.split(input_image)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

            histograms = {}
            for i, (channel, color) in enumerate(zip(channels, colors)):
                # 计算直方图
                hist = cv2.calcHist(
                    [channel], [0], None, [hist_size], [range_min, range_max]
                )
                # 归一化
                hist = cv2.normalize(hist, hist).flatten()
                histograms[f"channel_{i}"] = hist

            # 设置结果
            self._result_data = ResultData()
            self._result_data.set_value("histograms", histograms)
            self._result_data.set_value("histogram_type", "color")

        self._logger.info(f"直方图生成完成，类型: {histogram_type}")


@ToolRegistry.register
class Caliper(VisionAlgorithmToolBase):
    """
    卡尺测量工具

    沿指定路径进行边缘检测和测量，用于测量距离、宽度等。

    参数说明：
    - caliper_count: 卡尺数量
    - step_size: 步长
    - edge_threshold: 边缘阈值
    - edge_polarity: 边缘极性 (positive/negative/any)
    - edge_width: 边缘宽度
    - search_region: 搜索区域大小
    - draw_caliper: 是否绘制卡尺
    - draw_edges: 是否绘制检测到的边缘
    - draw_result: 是否绘制测量结果
    """

    tool_name = "卡尺测量"
    tool_category = "Analysis"
    tool_description = "沿指定路径进行边缘检测和测量"

    EDGE_POLARITIES = {
        "positive": 0,  # 从暗到亮
        "negative": 1,  # 从亮到暗
        "any": 2,  # 任意方向
    }

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "caliper_count": ToolParameter(
            name="卡尺数量",
            param_type="integer",
            default=5,
            description="卡尺数量",
            min_value=1,
            max_value=50,
        ),
        "step_size": ToolParameter(
            name="卡尺间距",
            param_type="integer",
            default=10,
            description="卡尺间距",
            min_value=1,
            max_value=100,
        ),
        "edge_threshold": ToolParameter(
            name="边缘阈值",
            param_type="integer",
            default=30,
            description="边缘阈值",
            min_value=1,
            max_value=255,
        ),
        "edge_polarity": ToolParameter(
            name="边缘极性",
            param_type="enum",
            default="any",
            description="边缘极性",
            options=["positive", "negative", "any"],
        ),
        "edge_width": ToolParameter(
            name="边缘宽度",
            param_type="integer",
            default=5,
            description="边缘宽度",
            min_value=1,
            max_value=50,
        ),
        "search_region": ToolParameter(
            name="搜索区域",
            param_type="integer",
            default=20,
            description="搜索区域大小",
            min_value=1,
            max_value=100,
        ),
        "draw_caliper": ToolParameter(
            name="绘制卡尺",
            param_type="boolean",
            default=True,
            description="绘制卡尺",
        ),
        "draw_edges": ToolParameter(
            name="绘制边缘",
            param_type="boolean",
            default=True,
            description="绘制边缘",
        ),
        "draw_result": ToolParameter(
            name="绘制结果",
            param_type="boolean",
            default=True,
            description="绘制结果",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("caliper_count", 5)
        self.set_param("step_size", 10)
        self.set_param("edge_threshold", 30)
        self.set_param("edge_polarity", "any")
        self.set_param("edge_width", 5)
        self.set_param("search_region", 20)
        self.set_param("draw_caliper", True)
        self.set_param("draw_edges", True)
        self.set_param("draw_result", True)

    def _run_impl(self):
        """执行卡尺测量"""
        if not self.has_input():
            raise VisionAlgorithmException("无输入图像")

        input_image = self._input_data.data
        gray = input_image.copy()

        # 如果是彩色图像，转换为灰度图
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

        # 获取参数
        caliper_count = self.get_param("caliper_count", 5)
        step_size = self.get_param("step_size", 10)
        edge_threshold = self.get_param("edge_threshold", 30)
        edge_polarity = self.get_param("edge_polarity", "any")
        edge_width = self.get_param("edge_width", 5)
        search_region = self.get_param("search_region", 20)
        draw_caliper = self.get_param("draw_caliper", True)
        draw_edges = self.get_param("draw_edges", True)
        draw_result = self.get_param("draw_result", True)

        # 创建输出图像
        output = (
            cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            if len(input_image.shape) == 2
            else input_image.copy()
        )

        # 定义卡尺测量区域（这里使用默认的水平中心线，实际应用中应从ROI或参数中获取）
        height, width = gray.shape
        center_y = height // 2
        start_x = 50
        end_x = width - 50

        # 计算每个卡尺的位置
        caliper_results = []
        for i in range(caliper_count):
            # 计算当前卡尺的Y位置
            caliper_y = center_y + (i - caliper_count // 2) * step_size

            # 确保卡尺在图像范围内
            if caliper_y < 0 or caliper_y >= height:
                continue

            # 提取沿卡尺线的像素值
            profile = gray[caliper_y, start_x:end_x]

            # 计算梯度（边缘检测）
            gradient = np.gradient(profile)

            # 寻找边缘
            edges = []
            for x in range(len(gradient) - 1):
                # 计算梯度绝对值
                grad_value = abs(gradient[x])

                # 梯度阈值过滤
                if grad_value < edge_threshold:
                    continue

                # 边缘极性过滤
                current_polarity = 0 if gradient[x] > 0 else 1
                if edge_polarity != "any":
                    if self.EDGE_POLARITIES[edge_polarity] != current_polarity:
                        continue

                edges.append(
                    {
                        "position": start_x + x,
                        "y": caliper_y,
                        "gradient": gradient[x],
                        "polarity": current_polarity,
                    }
                )

            # 保存卡尺结果
            caliper_result = {
                "caliper_id": i,
                "position": caliper_y,
                "edges": edges,
                "edge_count": len(edges),
            }

            # 如果有边缘，计算距离
            if len(edges) >= 2:
                # 计算第一个和最后一个边缘之间的距离
                distance = abs(edges[-1]["position"] - edges[0]["position"])
                caliper_result["distance"] = distance

            caliper_results.append(caliper_result)

            # 绘制卡尺
            if draw_caliper:
                # 绘制卡尺中心线
                cv2.line(
                    output,
                    (start_x, caliper_y),
                    (end_x, caliper_y),
                    (0, 255, 0),
                    1,
                )
                # 绘制搜索区域
                cv2.rectangle(
                    output,
                    (start_x, caliper_y - search_region // 2),
                    (end_x, caliper_y + search_region // 2),
                    (0, 255, 0),
                    1,
                )

            # 绘制边缘
            if draw_edges:
                for edge in edges:
                    cv2.circle(
                        output,
                        (edge["position"], edge["y"]),
                        3,
                        (0, 0, 255),
                        -1,
                    )

            # 绘制测量结果
            if draw_result and "distance" in caliper_result:
                mid_x = (start_x + end_x) // 2
                cv2.putText(
                    output,
                    f"{caliper_result['distance']:.1f}",
                    (mid_x, caliper_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

        # 设置输出数据
        self._output_data = self._input_data.copy()
        self._output_data.data = output

        # 设置结果
        self._result_data = ResultData()
        self._result_data.set_value("caliper_results", caliper_results)
        self._result_data.set_value(
            "total_edges",
            sum(result["edge_count"] for result in caliper_results),
        )

        self._logger.info(
            f"卡尺测量完成，共 {len(caliper_results)} 个卡尺，检测到 {self._result_data.get_value('total_edges')} 个边缘"
        )
