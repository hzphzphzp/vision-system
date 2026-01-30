#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI工具混入类

为需要ROI功能的工具类提供通用的ROI支持。

提供功能：
- ROI参数初始化
- set_roi() 方法
- ROI数据解析辅助方法

Usage:
    class MyTool(ROIToolMixin, VisionAlgorithmToolBase):
        def _run_impl(self):
            roi = self.get_roi_from_params()
            if roi:
                x, y, width, height = roi
                # 使用ROI区域
                pass
"""

import logging
from typing import Any, Dict, Optional, Tuple

from core.tool_base import ToolParameter, VisionAlgorithmToolBase


class ROIToolMixin:
    """
    ROI工具混入类

    为视觉算法工具提供通用的ROI功能支持。
    继承此类的工具将自动获得ROI参数管理和设置功能。

    使用方法:
        class MyTool(ROIToolMixin, VisionAlgorithmToolBase):
            tool_name = "MyTool"
            tool_category = "Vision"

            def _run_impl(self):
                # 获取ROI参数
                roi = self.get_roi_from_params()
                if roi:
                    roi_x, roi_y, roi_width, roi_height = roi
                    # 处理ROI区域
                    pass
    """

    DEFAULT_ROI_WIDTH = 100
    DEFAULT_ROI_HEIGHT = 100

    @classmethod
    def get_roi_param_definitions(cls) -> Dict[str, ToolParameter]:
        """获取ROI参数定义

        Returns:
            ROI参数字典
        """
        return {
            "roi": ToolParameter(
                name="ROI区域",
                param_type="roi_rect",
                default=None,
                description="ROI矩形区域（点击按钮绘制）",
            )
        }

    def _init_roi_params(self):
        """初始化ROI相关参数（子类应调用此方法）"""
        self._roi_x = 0
        self._roi_y = 0
        self._roi_width = self.DEFAULT_ROI_WIDTH
        self._roi_height = self.DEFAULT_ROI_HEIGHT
        self._is_roi_set = False

    def set_roi(self, x: int, y: int, width: int, height: int):
        """设置ROI区域

        Args:
            x: 左上角X坐标
            y: 左上角Y坐标
            width: 宽度
            height: 高度
        """
        self._roi_x = x
        self._roi_y = y
        self._roi_width = width
        self._roi_height = height
        self._is_roi_set = True
        self._logger.info(f"ROI已设置: ({x}, {y}, {width}, {height})")

    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """获取当前ROI区域

        Returns:
            (x, y, width, height) 或 None（如果未设置）
        """
        if self._is_roi_set:
            return (
                self._roi_x,
                self._roi_y,
                self._roi_width,
                self._roi_height,
            )
        return None

    def is_roi_set(self) -> bool:
        """检查ROI是否已设置

        Returns:
            ROI是否已设置
        """
        return self._is_roi_set

    def get_roi_from_params(
        self, image_width: int = None, image_height: int = None
    ) -> Optional[Tuple[int, int, int, int]]:
        """从参数中获取ROI区域

        优先从以下来源获取ROI:
        1. 参数中的 "roi" 字典
        2. 内部变量 _roi_x, _roi_y, _roi_width, _roi_height

        Args:
            image_width: 图像宽度（用于边界检查）
            image_height: 图像高度（用于边界检查）

        Returns:
            (roi_x, roi_y, roi_width, roi_height) 或 None
        """
        roi_data = self.get_param("roi", None)

        # 1. 优先从参数中的roi字典获取
        if roi_data and isinstance(roi_data, dict) and "x" in roi_data:
            roi_x = int(roi_data.get("x", 0))
            roi_y = int(roi_data.get("y", 0))
            roi_width = int(roi_data.get("width", self.DEFAULT_ROI_WIDTH))
            roi_height = int(roi_data.get("height", self.DEFAULT_ROI_HEIGHT))

            # 边界检查
            if image_width is not None:
                roi_x = max(0, min(roi_x, image_width - 1))
                roi_y = max(0, min(roi_y, image_height - 1))
                roi_width = max(1, min(roi_width, image_width - roi_x))
                roi_height = max(1, min(roi_height, image_height - roi_y))

            return (roi_x, roi_y, roi_width, roi_height)

        # 2. 从内部变量获取（向后兼容）
        if self._is_roi_set:
            roi_x = self._roi_x
            roi_y = self._roi_y
            roi_width = self._roi_width
            roi_height = self._roi_height

            # 边界检查
            if image_width is not None:
                roi_x = max(0, min(roi_x, image_width - 1))
                roi_y = max(0, min(roi_y, image_height - 1))
                roi_width = max(1, min(roi_width, image_width - roi_x))
                roi_height = max(1, min(roi_height, image_height - roi_y))

            return (roi_x, roi_y, roi_width, roi_height)

        return None

    def clear_roi(self):
        """清除ROI设置"""
        self._is_roi_set = False
        self._roi_x = 0
        self._roi_y = 0
        self._roi_width = self.DEFAULT_ROI_WIDTH
        self._roi_height = self.DEFAULT_ROI_HEIGHT
        self._logger.info("ROI已清除")

    def extract_roi_region(self, image) -> Optional:
        """从图像中提取ROI区域

        Args:
            image: 输入图像

        Returns:
            ROI区域图像 或 None（如果未设置ROI）
        """
        roi = self.get_roi_from_params(image.shape[1], image.shape[0])
        if roi:
            roi_x, roi_y, roi_width, roi_height = roi
            return image[
                roi_y : roi_y + roi_height, roi_x : roi_x + roi_width
            ].copy()
        return None
