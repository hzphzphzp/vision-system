#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像计算工具模块

提供常见的图像计算功能，包括图像加法、减法、乘法、除法、逻辑运算等。

Author: Vision System Team
Date: 2026-02-02
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import ToolBase, ToolParameter, ToolPort, ToolRegistry
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException

_logger = logging.getLogger("ImageCalculation")


@ToolRegistry.register
class ImageCalculationTool(ToolBase):
    """
    图像计算工具

    支持多种图像计算操作：
    - 加法：图像1 + 图像2（或常数）
    - 减法：图像1 - 图像2（或常数）
    - 乘法：图像1 * 图像2（或常数）
    - 除法：图像1 / 图像2（或常数）
    - 绝对差：|图像1 - 图像2|
    - 加权融合：图像1 * 权重1 + 图像2 * 权重2
    - 逻辑运算：AND, OR, XOR, NOT
    """

    tool_name = "图像计算"
    tool_category = "ImageProcessing"
    tool_description = "对两幅图像进行数学计算或逻辑运算"

    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像1"),
        ToolPort("InputImage2", "input", "image", "输入图像2"),
    ]

    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像"),
    ]

    PARAM_DEFINITIONS = {
        "operation": ToolParameter(
            name="计算类型",
            param_type="enum",
            default="加法",
            description="选择图像计算操作类型",
            options=[
                "加法",
                "减法",
                "乘法",
                "除法",
                "绝对差",
                "加权融合",
                "逻辑与",
                "逻辑或",
                "逻辑异或",
                "逻辑非",
            ],
        ),
        "constant_value": ToolParameter(
            name="常数值",
            param_type="float",
            default=0.0,
            description="当只有一个输入图像时使用的常数值",
            min_value=-1000.0,
            max_value=1000.0,
        ),
        "weight1": ToolParameter(
            name="图像1权重",
            param_type="float",
            default=0.5,
            description="加权融合时图像1的权重",
            min_value=0.0,
            max_value=1.0,
        ),
        "weight2": ToolParameter(
            name="图像2权重",
            param_type="float",
            default=0.5,
            description="加权融合时图像2的权重",
            min_value=0.0,
            max_value=1.0,
        ),
        "clip_result": ToolParameter(
            name="裁剪结果",
            param_type="boolean",
            default=True,
            description="是否将结果裁剪到0-255范围",
        ),
        "normalize_result": ToolParameter(
            name="归一化结果",
            param_type="boolean",
            default=False,
            description="是否将结果归一化到0-255范围",
        ),
    }

    def __init__(self, name: str = None):
        """初始化工具"""
        super().__init__(name)
        self._input_data_2 = None

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("operation", "加法")
        self.set_param("constant_value", 0.0)
        self.set_param("weight1", 0.5)
        self.set_param("weight2", 0.5)
        self.set_param("clip_result", True)
        self.set_param("normalize_result", False)

    def set_input(self, image_data: ImageData, port: str = "InputImage"):
        """
        设置输入数据，支持两个输入端口
        如果端口名称为默认的InputImage，会自动分配到不同的输入

        Args:
            image_data: 输入图像数据
            port: 输入端口名称 (InputImage 或 InputImage2)
        """
        # 如果使用默认端口名，自动分配到不同的输入（支持多个连接）
        if port == "InputImage":
            if self._input_data is None or self._input_count == 0:
                # 第一个连接使用 InputImage1
                self._input_data = image_data
                self._input_count = 1
                _logger.info(f"设置输入图像1 (自动分配): {image_data.width}x{image_data.height}")
            else:
                # 后续连接使用 InputImage2
                self._input_data_2 = image_data
                self._input_count = 2
                _logger.info(f"设置输入图像2 (自动分配): {image_data.width}x{image_data.height}")
        elif port == "InputImage2":
            self._input_data_2 = image_data
            _logger.info(f"设置输入图像2: {image_data.width}x{image_data.height}")
        else:
            # 其他端口名，默认使用 InputImage1
            self._input_data = image_data
            _logger.info(f"设置输入图像: {image_data.width}x{image_data.height}")

    def _run_impl(self):
        """执行图像计算"""
        # 获取输入数据
        if not self.has_input():
            raise ToolException("没有输入图像")

        input_data = self._input_data
        img1 = input_data.data

        # 获取参数
        operation = self.get_param("operation", "add")
        constant_value = self.get_param("constant_value", 0.0)
        weight1 = self.get_param("weight1", 0.5)
        weight2 = self.get_param("weight2", 0.5)
        clip_result = self.get_param("clip_result", True)
        normalize_result = self.get_param("normalize_result", False)

        # 检查是否有第二个输入（通过InputImage2端口）
        img2 = None
        if self._input_data_2 is not None:
            img2 = self._input_data_2.data

        # 确保图像是numpy数组
        if not isinstance(img1, np.ndarray):
            raise ToolException("输入1不是有效的图像数据")

        if img2 is not None and not isinstance(img2, np.ndarray):
            raise ToolException("输入2不是有效的图像数据")

        # 如果只有一个图像，使用常数作为第二个操作数
        if img2 is None:
            if operation in ["bitwise_and", "bitwise_or", "bitwise_xor"]:
                # 逻辑运算需要整数
                img2 = np.full_like(img1, int(constant_value))
            else:
                img2 = np.full_like(img1, constant_value, dtype=np.float32)

        # 确保两幅图像尺寸相同
        if img1.shape != img2.shape:
            _logger.info(f"图像尺寸不匹配，调整图像2尺寸: {img1.shape} vs {img2.shape}")
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # 确保图像类型一致
        if img1.dtype != np.float32:
            img1_float = img1.astype(np.float32)
        else:
            img1_float = img1

        if img2.dtype != np.float32:
            img2_float = img2.astype(np.float32)
        else:
            img2_float = img2

        # 执行计算
        try:
            if operation == "加法":
                result = cv2.add(img1_float, img2_float)
                operation_name = "加法"
            elif operation == "减法":
                result = cv2.subtract(img1_float, img2_float)
                operation_name = "减法"
            elif operation == "乘法":
                result = cv2.multiply(img1_float, img2_float)
                operation_name = "乘法"
            elif operation == "除法":
                # 避免除以0
                img2_safe = np.where(img2_float == 0, 1, img2_float)
                result = cv2.divide(img1_float, img2_safe)
                operation_name = "除法"
            elif operation == "绝对差":
                result = cv2.absdiff(img1_float, img2_float)
                operation_name = "绝对差"
            elif operation == "加权融合":
                result = cv2.addWeighted(img1_float, weight1, img2_float, weight2, 0)
                operation_name = "加权融合"
            elif operation == "逻辑与":
                # 转换为uint8进行逻辑运算
                img1_uint8 = img1.astype(np.uint8)
                img2_uint8 = img2.astype(np.uint8)
                result = cv2.bitwise_and(img1_uint8, img2_uint8)
                operation_name = "逻辑与"
            elif operation == "逻辑或":
                img1_uint8 = img1.astype(np.uint8)
                img2_uint8 = img2.astype(np.uint8)
                result = cv2.bitwise_or(img1_uint8, img2_uint8)
                operation_name = "逻辑或"
            elif operation == "逻辑异或":
                img1_uint8 = img1.astype(np.uint8)
                img2_uint8 = img2.astype(np.uint8)
                result = cv2.bitwise_xor(img1_uint8, img2_uint8)
                operation_name = "逻辑异或"
            elif operation == "逻辑非":
                img1_uint8 = img1.astype(np.uint8)
                result = cv2.bitwise_not(img1_uint8)
                operation_name = "逻辑非"
            else:
                raise ToolException(f"未知的计算类型: {operation}")

            # 后处理
            if operation not in ["bitwise_and", "bitwise_or", "bitwise_xor", "bitwise_not"]:
                if normalize_result:
                    # 归一化到0-255
                    result_min = result.min()
                    result_max = result.max()
                    if result_max > result_min:
                        result = ((result - result_min) / (result_max - result_min) * 255).astype(np.uint8)
                    else:
                        # 当图像没有变化时（如相同图像的绝对差），显示中间灰度值
                        if operation in ["绝对差", "减法"] and result_max == result_min:
                            result = np.full_like(result, 128, dtype=np.uint8)  # 灰色表示无变化
                        else:
                            result = np.zeros_like(result, dtype=np.uint8)
                elif clip_result:
                    # 裁剪到0-255
                    result = np.clip(result, 0, 255).astype(np.uint8)
                else:
                    # 转换回uint8
                    result = result.astype(np.uint8)

            # 创建输出图像
            output_image = ImageData(data=result)

            # 设置结果
            self._result_data = ResultData()
            self._result_data.set_value("operation", operation_name)
            self._result_data.set_value("input1_shape", list(img1.shape))
            self._result_data.set_value("input2_shape", list(img2.shape))
            self._result_data.set_value("output_shape", list(result.shape))
            self._result_data.set_value("result_min", float(result.min()))
            self._result_data.set_value("result_max", float(result.max()))
            self._result_data.set_value("result_mean", float(result.mean()))

            _logger.info(f"图像计算完成: {operation_name}, 输出尺寸: {result.shape}")

            # 返回输出数据（基类run方法会处理返回值）
            return output_image

        except Exception as e:
            _logger.error(f"图像计算失败: {e}")
            raise ToolException(f"图像计算失败: {e}")

@ToolRegistry.register
class ImageAddTool(ImageCalculationTool):
    """图像加法工具（快捷方式）"""

    tool_name = "图像加法"
    tool_category = "ImageProcessing"
    tool_description = "两幅图像相加"

    def _init_params(self):
        """初始化默认参数"""
        super()._init_params()
        self.set_param("operation", "add")


@ToolRegistry.register
class ImageSubtractTool(ImageCalculationTool):
    """图像减法工具（快捷方式）"""

    tool_name = "图像减法"
    tool_category = "ImageProcessing"
    tool_description = "两幅图像相减"

    def _init_params(self):
        """初始化默认参数"""
        super()._init_params()
        self.set_param("operation", "subtract")


@ToolRegistry.register
class ImageBlendTool(ImageCalculationTool):
    """图像融合工具（快捷方式）"""

    tool_name = "图像融合"
    tool_category = "ImageProcessing"
    tool_description = "按权重融合两幅图像"

    def _init_params(self):
        """初始化默认参数"""
        super()._init_params()
        self.set_param("operation", "weighted")
        self.set_param("weight1", 0.5)
        self.set_param("weight2", 0.5)
