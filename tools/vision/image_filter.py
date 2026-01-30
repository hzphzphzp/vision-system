#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像滤波工具模块

提供各种图像滤波工具，包括方框滤波、均值滤波、高斯滤波、中值滤波等。

Author: Vision System Team
Date: 2025-01-04
"""

import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import ImageProcessToolBase, ToolParameter, ToolRegistry
from data.image_data import ROI, ImageData
from utils.exceptions import ImageProcessException


class FilterType(Enum):
    """滤波类型"""

    BOX_FILTER = "box"
    MEAN_FILTER = "mean"
    GAUSSIAN_FILTER = "gaussian"
    MEDIAN_FILTER = "median"
    BILATERAL_FILTER = "bilateral"


@ToolRegistry.register
class BoxFilter(ImageProcessToolBase):
    """
    方框滤波工具

    对图像进行方框滤波处理。

    参数说明：
    - kernel_size: 核大小，必须为正奇数
    - normalize: 是否归一化
    """

    tool_name = "方框滤波"
    tool_category = "ImageFilter"
    tool_description = "对图像进行方框滤波"

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("kernel_size", 3)
        self.set_param("normalize", True)

    def _run_impl(self):
        """执行方框滤波"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        kernel_size = self.get_param("kernel_size", 3)
        normalize = self.get_param("normalize", True)

        # 执行滤波
        output = cv2.boxFilter(
            input_image, -1, (kernel_size, kernel_size), normalize=normalize
        )

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(
            f"方框滤波完成: kernel={kernel_size}, normalize={normalize}"
        )


@ToolRegistry.register
class MeanFilter(ImageProcessToolBase):
    """
    均值滤波工具

    对图像进行均值滤波（归一化的方框滤波）。

    参数说明：
    - kernel_size: 核大小，必须为正奇数
    """

    tool_name = "均值滤波"
    tool_category = "ImageFilter"
    tool_description = "对图像进行均值滤波"

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("kernel_size", 3)

    def _run_impl(self):
        """执行均值滤波"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        kernel_size = self.get_param("kernel_size", 3)

        # 执行滤波
        output = cv2.blur(input_image, (kernel_size, kernel_size))

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(f"均值滤波完成: kernel={kernel_size}")


@ToolRegistry.register
class GaussianFilter(ImageProcessToolBase):
    """
    高斯滤波工具

    对图像进行高斯滤波处理。

    参数说明：
    - kernel_size: 核大小，必须为正奇数
    - sigma_x: X方向标准差
    - sigma_y: Y方向标准差，如果为0则与sigma_x相同
    """

    tool_name = "高斯滤波"
    tool_category = "ImageFilter"
    tool_description = "对图像进行高斯滤波"

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("kernel_size", 3)
        self.set_param("sigma_x", 0)
        self.set_param("sigma_y", 0)

    def _run_impl(self):
        """执行高斯滤波"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        kernel_size = self.get_param("kernel_size", 3)
        sigma_x = self.get_param("sigma_x", 0)
        sigma_y = self.get_param("sigma_y", 0)

        # 执行滤波
        output = cv2.GaussianBlur(
            input_image, (kernel_size, kernel_size), sigma_x, sigma_y
        )

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(
            f"高斯滤波完成: kernel={kernel_size}, sigma_x={sigma_x}, sigma_y={sigma_y}"
        )


@ToolRegistry.register
class MedianFilter(ImageProcessToolBase):
    """
    中值滤波工具

    对图像进行中值滤波处理，对椒盐噪声有很好的抑制效果。

    参数说明：
    - kernel_size: 核大小，必须为正奇数
    """

    tool_name = "中值滤波"
    tool_category = "ImageFilter"
    tool_description = "对图像进行中值滤波"

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("kernel_size", 3)

    def _run_impl(self):
        """执行中值滤波"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        kernel_size = self.get_param("kernel_size", 3)

        # 执行滤波
        output = cv2.medianBlur(input_image, kernel_size)

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(f"中值滤波完成: kernel={kernel_size}")


@ToolRegistry.register
class BilateralFilter(ImageProcessToolBase):
    """
    双边滤波工具

    对图像进行双边滤波处理，在保持边缘的同时进行平滑处理。

    参数说明：
    - diameter: 邻域直径
    - sigma_color: 颜色空间标准差
    - sigma_space: 坐标空间标准差
    """

    tool_name = "双边滤波"
    tool_category = "ImageFilter"
    tool_description = "对图像进行双边滤波"

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("diameter", 9)
        self.set_param("sigma_color", 75)
        self.set_param("sigma_space", 75)

    def _run_impl(self):
        """执行双边滤波"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        diameter = self.get_param("diameter", 9)
        sigma_color = self.get_param("sigma_color", 75)
        sigma_space = self.get_param("sigma_space", 75)

        # 执行滤波
        output = cv2.bilateralFilter(
            input_image, diameter, sigma_color, sigma_space
        )

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(
            f"双边滤波完成: diameter={diameter}, sigma_color={sigma_color}, sigma_space={sigma_space}"
        )


@ToolRegistry.register
class Morphology(ImageProcessToolBase):
    """
    形态学处理工具

    对图像进行形态学处理，包括腐蚀、膨胀、开运算、闭运算等。

    参数说明：
    - operation: 操作类型 (erode/dilate/open/close/gradient/tophat/blackhat)
    - kernel_size: 核大小
    - iterations: 迭代次数
    """

    tool_name = "形态学处理"
    tool_category = "ImageFilter"
    tool_description = "对图像进行形态学处理"

    MORPH_OPERATIONS = {
        "erode": cv2.MORPH_ERODE,
        "dilate": cv2.MORPH_DILATE,
        "open": cv2.MORPH_OPEN,
        "close": cv2.MORPH_CLOSE,
        "gradient": cv2.MORPH_GRADIENT,
        "tophat": cv2.MORPH_TOPHAT,
        "blackhat": cv2.MORPH_BLACKHAT,
    }

    # 中文参数定义
    PARAM_DEFINITIONS = {
        "operation": ToolParameter(
            name="操作类型",
            param_type="enum",
            default="open",
            description="形态学操作类型",
            options=[
                "erode",
                "dilate",
                "open",
                "close",
                "gradient",
                "tophat",
                "blackhat",
            ],
        ),
        "kernel_size": ToolParameter(
            name="核大小",
            param_type="integer",
            default=3,
            description="卷积核大小",
            min_value=1,
            max_value=31,
        ),
        "iterations": ToolParameter(
            name="迭代次数",
            param_type="integer",
            default=1,
            description="形态学操作迭代次数",
            min_value=1,
            max_value=20,
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("operation", "open")
        self.set_param("kernel_size", 3)
        self.set_param("iterations", 1)

    def _run_impl(self):
        """执行形态学处理"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        operation_name = self.get_param("operation", "open")
        kernel_size = self.get_param("kernel_size", 3)
        iterations = self.get_param("iterations", 1)

        # 创建核
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (kernel_size, kernel_size)
        )

        # 获取操作码
        operation = self.MORPH_OPERATIONS.get(operation_name, cv2.MORPH_OPEN)

        # 执行形态学操作
        output = cv2.morphologyEx(
            input_image, operation, kernel, iterations=iterations
        )

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(
            f"形态学处理完成: operation={operation_name}, kernel={kernel_size}, iterations={iterations}"
        )


@ToolRegistry.register
class ImageResize(ImageProcessToolBase):
    """
    图像缩放工具

    对图像进行缩放处理。

    参数说明：
    - width: 目标宽度
    - height: 目标高度
    - interpolation: 插值方法
    """

    tool_name = "图像缩放"
    tool_category = "ImageFilter"
    tool_description = "对图像进行缩放"

    INTERPOLATION_METHODS = {
        "nearest": cv2.INTER_NEAREST,
        "linear": cv2.INTER_LINEAR,
        "cubic": cv2.INTER_CUBIC,
        "area": cv2.INTER_AREA,
        "lanczos4": cv2.INTER_LANCZOS4,
    }

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("width", 640)
        self.set_param("height", 480)
        self.set_param(
            "interpolation",
            "linear",
            param_type="enum",
            description="选择图像缩放时使用的插值算法",
            options=["nearest", "linear", "cubic", "area", "lanczos4"],
        )

    def _run_impl(self):
        """执行图像缩放"""
        if not self.has_input():
            raise ImageProcessException("无输入图像")

        input_image = self._input_data.data
        width = self.get_param("width", 640)
        height = self.get_param("height", 480)
        interpolation_name = self.get_param("interpolation", "linear")

        # 获取插值方法
        interpolation = self.INTERPOLATION_METHODS.get(
            interpolation_name, cv2.INTER_LINEAR
        )

        # 执行缩放
        output = cv2.resize(
            input_image, (width, height), interpolation=interpolation
        )

        self._output_data = self._input_data.copy()
        self._output_data.data = output

        self._logger.info(
            f"图像缩放完成: {input_image.shape[1]}x{input_image.shape[0]} -> {width}x{height}"
        )
