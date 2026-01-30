#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共图像滤波工具函数

提供统一的滤波处理接口，减少重复代码。

Author: Vision System Team
Date: 2026-01-19
"""

from typing import Callable, Optional

import cv2
import numpy as np


def apply_filter(image: np.ndarray, filter_type: str, **params) -> np.ndarray:
    """统一的滤波处理函数

    Args:
        image: 输入图像
        filter_type: 滤波类型
        **params: 滤波参数

    Returns:
        处理后的图像
    """
    filter_methods = {
        "box": _apply_box_filter,
        "mean": _apply_mean_filter,
        "gaussian": _apply_gaussian_filter,
        "median": _apply_median_filter,
        "bilateral": _apply_bilateral_filter,
    }

    if filter_type not in filter_methods:
        raise ValueError(f"不支持的滤波类型: {filter_type}")

    return filter_methods[filter_type](image, **params)


def _apply_box_filter(
    image: np.ndarray, kernel_size: int = 3, normalize: bool = True
) -> np.ndarray:
    """方框滤波"""
    return cv2.boxFilter(
        image, -1, (kernel_size, kernel_size), normalize=normalize
    )


def _apply_mean_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """均值滤波"""
    return cv2.blur(image, (kernel_size, kernel_size))


def _apply_gaussian_filter(
    image: np.ndarray,
    kernel_size: int = 3,
    sigma_x: float = 0,
    sigma_y: float = 0,
) -> np.ndarray:
    """高斯滤波"""
    return cv2.GaussianBlur(
        image, (kernel_size, kernel_size), sigma_x, sigma_y
    )


def _apply_median_filter(
    image: np.ndarray, kernel_size: int = 3
) -> np.ndarray:
    """中值滤波"""
    return cv2.medianBlur(image, kernel_size)


def _apply_bilateral_filter(
    image: np.ndarray,
    diameter: int = 9,
    sigma_color: float = 75,
    sigma_space: float = 75,
) -> np.ndarray:
    """双边滤波"""
    return cv2.bilateralFilter(image, diameter, sigma_color, sigma_space)


def apply_morphology(
    image: np.ndarray,
    operation: str,
    kernel_size: int = 3,
    iterations: int = 1,
) -> np.ndarray:
    """统一的形态学处理函数

    Args:
        image: 输入图像
        operation: 操作类型 (erode/dilate/open/close/gradient/tophat/blackhat)
        kernel_size: 核大小
        iterations: 迭代次数

    Returns:
        处理后的图像
    """
    morph_operations = {
        "erode": cv2.MORPH_ERODE,
        "dilate": cv2.MORPH_DILATE,
        "open": cv2.MORPH_OPEN,
        "close": cv2.MORPH_CLOSE,
        "gradient": cv2.MORPH_GRADIENT,
        "tophat": cv2.MORPH_TOPHAT,
        "blackhat": cv2.MORPH_BLACKHAT,
    }

    if operation not in morph_operations:
        raise ValueError(f"不支持的形态学操作: {operation}")

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (kernel_size, kernel_size)
    )
    return cv2.morphologyEx(
        image, morph_operations[operation], kernel, iterations=iterations
    )


def validate_kernel_size(
    kernel_size: int, param_name: str = "kernel_size"
) -> int:
    """验证并修正核大小

    Args:
        kernel_size: 输入的核大小
        param_name: 参数名称（用于日志）

    Returns:
        修正后的核大小（正奇数）
    """
    if kernel_size <= 0:
        return 1
    if int(kernel_size) % 2 == 0:
        return int(kernel_size) + 1
    return int(kernel_size)
