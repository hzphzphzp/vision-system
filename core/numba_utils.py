#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numba 加速工具模块

提供基于 Numba 的高性能计算函数。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from typing import Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUMBA_AVAILABLE = False

try:
    from numba import jit, prange, njit
    NUMBA_AVAILABLE = True
except ImportError:
    pass


if NUMBA_AVAILABLE:

    @jit(nopython=True, cache=True)
    def ssd_match(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """计算SSD匹配（Sum of Squared Differences）

        Args:
            image: 输入图像
            template: 模板图像

        Returns:
            匹配结果矩阵
        """
        h, w = image.shape
        th, tw = template.shape
        result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

        for i in range(h - th + 1):
            for j in range(w - tw + 1):
                ssd = 0.0
                for ii in range(th):
                    for jj in range(tw):
                        diff = float(image[i + ii, j + jj]) - float(template[ii, jj])
                        ssd += diff * diff
                result[i, j] = ssd

        return result


    @jit(nopython=True, parallel=True, cache=True)
    def ssd_match_parallel(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """并行计算SSD匹配

        Args:
            image: 输入图像
            template: 模板图像

        Returns:
            匹配结果矩阵
        """
        h, w = image.shape
        th, tw = template.shape
        result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

        for i in prange(h - th + 1):
            for j in range(w - tw + 1):
                ssd = 0.0
                for ii in range(th):
                    for jj in range(tw):
                        diff = float(image[i + ii, j + jj]) - float(template[ii, jj])
                        ssd += diff * diff
                result[i, j] = ssd

        return result


    @jit(nopython=True, cache=True)
    def normalized_cross_correlation(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """归一化互相关匹配

        Args:
            image: 输入图像
            template: 模板图像

        Returns:
            匹配结果矩阵
        """
        h, w = image.shape
        th, tw = template.shape

        template_mean = np.mean(template)
        template_std = np.std(template)

        result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

        for i in range(h - th + 1):
            for j in range(w - tw + 1):
                roi = image[i:i+th, j:j+tw]
                roi_mean = np.mean(roi)
                roi_std = np.std(roi)

                if roi_std > 0:
                    ncc = np.sum((roi - roi_mean) * (template - template_mean)) / (th * tw * roi_std * template_std)
                    result[i, j] = ncc
                else:
                    result[i, j] = 0

        return result


    @jit(nopython=True, cache=True)
    def calculate_histogram(image: np.ndarray, bins: int = 256) -> np.ndarray:
        """计算图像直方图（Numba加速）

        Args:
            image: 输入图像
            bins: 直方图bin数量

        Returns:
            直方图数组
        """
        hist = np.zeros(bins, dtype=np.int32)
        h, w = image.shape

        for i in range(h):
            for j in range(w):
                val = int(image[i, j])
                if 0 <= val < bins:
                    hist[val] += 1

        return hist


    @jit(nopython=True, parallel=True, cache=True)
    def fast_gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """快速高斯模糊（简化版）

        Args:
            image: 输入图像
            kernel_size: 卷积核大小

        Returns:
            模糊后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.float32)
        pad = kernel_size // 2

        for i in prange(h):
            for j in range(w):
                sum_val = 0.0
                count = 0
                for ki in range(-pad, pad + 1):
                    for kj in range(-pad, pad + 1):
                        ni = i + ki
                        nj = j + kj
                        if 0 <= ni < h and 0 <= nj < w:
                            sum_val += float(image[ni, nj])
                            count += 1
                result[i, j] = sum_val / count if count > 0 else 0

        return result.astype(np.uint8)


    @jit(nopython=True, cache=True)
    def template_match_ncc(image: np.ndarray, template: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """模板匹配返回最佳位置（NCC）

        Args:
            image: 输入图像
            template: 模板图像

        Returns:
            (匹配结果矩阵, 最佳x, 最佳y)
        """
        result = normalized_cross_correlation(image, template)
        h, w = result.shape

        max_val = -1.0
        max_x, max_y = 0, 0

        for i in range(h):
            for j in range(w):
                if result[i, j] > max_val:
                    max_val = result[i, j]
                    max_x, max_y = j, i

        return result, max_x, max_y


    def warmup():
        """预热Numba JIT编译器"""
        dummy = np.zeros((10, 10), dtype=np.uint8)
        ssd_match(dummy, dummy)
        ssd_match_parallel(dummy, dummy)
        normalized_cross_correlation(dummy, dummy)
        calculate_histogram(dummy)
        fast_gaussian_blur(dummy)

else:

    def ssd_match(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """Fallback SSD match using numpy"""
        import cv2
        return cv2.matchTemplate(image, template, cv2.TM_SQDIFF).astype(np.float32)

    def ssd_match_parallel(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """Fallback SSD match"""
        return ssd_match(image, template)

    def normalized_cross_correlation(image: np.ndarray, template: np.ndarray) -> np.ndarray:
        """Fallback NCC match using numpy"""
        import cv2
        return cv2.matchTemplate(image, template, cv2.TM_CCORR_NORMED).astype(np.float32)

    def calculate_histogram(image: np.ndarray, bins: int = 256) -> np.ndarray:
        """Fallback histogram using numpy"""
        hist, _ = np.histogram(image.ravel(), bins=bins, range=(0, 256))
        return hist.astype(np.int32)

    def fast_gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Fallback gaussian blur using numpy"""
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(image.astype(np.float32), kernel_size/3).astype(np.uint8)

    def template_match_ncc(image: np.ndarray, template: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """Fallback NCC match"""
        import cv2
        result = cv2.matchTemplate(image, template, cv2.TM_CCORR_NORMED).astype(np.float32)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        return result, max_loc[0], max_loc[1]

    def warmup():
        """No-op when numba is not available"""
        pass
