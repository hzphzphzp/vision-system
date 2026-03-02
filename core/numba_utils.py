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


    @jit(nopython=True, parallel=True, cache=True)
    def fast_box_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """快速盒子滤波（均值滤波）

        Args:
            image: 输入图像
            kernel_size: 卷积核大小

        Returns:
            滤波后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.float64)
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

        return result.astype(image.dtype)


    @jit(nopython=True, cache=True)
    def fast_histogram_equalization(image: np.ndarray) -> np.ndarray:
        """快速直方图均衡化

        Args:
            image: 输入图像 (灰度图)

        Returns:
            均衡化后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.uint8)

        hist = np.zeros(256, dtype=np.int32)
        for i in range(h):
            for j in range(w):
                hist[image[i, j]] += 1

        cdf = np.zeros(256, dtype=np.float64)
        cdf[0] = hist[0]
        for i in range(1, 256):
            cdf[i] = cdf[i-1] + hist[i]

        cdf_min = 0
        for i in range(256):
            if cdf[i] > 0:
                cdf_min = cdf[i]
                break

        if cdf[-1] > cdf_min:
            scale = 255.0 / (cdf[-1] - cdf_min)
        else:
            scale = 1.0

        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            lut[i] = int((cdf[i] - cdf_min) * scale)

        for i in range(h):
            for j in range(w):
                result[i, j] = lut[image[i, j]]

        return result


    @jit(nopython=True, parallel=True, cache=True)
    def fast_threshold(image: np.ndarray, threshold: int, method: str = "binary") -> np.ndarray:
        """快速阈值处理

        Args:
            image: 输入图像
            threshold: 阈值 (0-255)
            method: 阈值方法 ('binary', 'otsu')

        Returns:
            二值化后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.uint8)

        if method == "otsu":
            best_threshold = 0
            max_variance = 0.0

            for t in range(256):
                bg_pixels = 0
                fg_pixels = 0
                bg_sum = 0
                fg_sum = 0

                for i in range(h):
                    for j in range(w):
                        val = image[i, j]
                        if val < t:
                            bg_pixels += 1
                            bg_sum += val
                        else:
                            fg_pixels += 1
                            fg_sum += val

                if bg_pixels > 0:
                    bg_mean = bg_sum / bg_pixels
                else:
                    bg_mean = 0

                if fg_pixels > 0:
                    fg_mean = fg_sum / fg_pixels
                else:
                    fg_mean = 0

                variance = bg_pixels * fg_pixels * (bg_mean - fg_mean) ** 2

                if variance > max_variance:
                    max_variance = variance
                    best_threshold = t

            threshold = best_threshold

        for i in prange(h):
            for j in range(w):
                result[i, j] = 255 if image[i, j] >= threshold else 0

        return result


    @jit(nopython=True, parallel=True, cache=True)
    def fast_pixel_operation(image: np.ndarray, operation: str, value: float = 0) -> np.ndarray:
        """快速像素级操作

        Args:
            image: 输入图像
            operation: 操作类型 ('add', 'subtract', 'multiply', 'divide', 'invert', 'normalize')
            value: 操作值

        Returns:
            处理后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.float64)

        if operation == "add":
            for i in prange(h):
                for j in range(w):
                    result[i, j] = min(255, max(0, float(image[i, j]) + value))
        elif operation == "subtract":
            for i in prange(h):
                for j in range(w):
                    result[i, j] = min(255, max(0, float(image[i, j]) - value))
        elif operation == "multiply":
            for i in prange(h):
                for j in range(w):
                    result[i, j] = min(255, max(0, float(image[i, j]) * value))
        elif operation == "divide":
            for i in prange(h):
                for j in range(w):
                    if value != 0:
                        result[i, j] = min(255, max(0, float(image[i, j]) / value))
                    else:
                        result[i, j] = image[i, j]
        elif operation == "invert":
            for i in prange(h):
                for j in range(w):
                    result[i, j] = 255 - image[i, j]
        elif operation == "normalize":
            min_val = float(np.min(image))
            max_val = float(np.max(image))
            if max_val > min_val:
                scale = 255.0 / (max_val - min_val)
                for i in prange(h):
                    for j in range(w):
                        result[i, j] = (float(image[i, j]) - min_val) * scale
            else:
                for i in prange(h):
                    for j in range(w):
                        result[i, j] = image[i, j]
        else:
            for i in prange(h):
                for j in range(w):
                    result[i, j] = image[i, j]

        return result.astype(image.dtype)


    @jit(nopython=True, parallel=True, cache=True)
    def fast_erode_dilate(image: np.ndarray, kernel_size: int = 3, operation: str = "erode") -> np.ndarray:
        """快速腐蚀/膨胀操作

        Args:
            image: 输入图像 (二值图)
            kernel_size: 卷积核大小
            operation: 操作类型 ('erode', 'dilate')

        Returns:
            处理后的图像
        """
        h, w = image.shape
        result = np.zeros_like(image, dtype=np.uint8)
        pad = kernel_size // 2

        for i in prange(h):
            for j in range(w):
                if operation == "erode":
                    found = True
                    for ki in range(-pad, pad + 1):
                        for kj in range(-pad, pad + 1):
                            ni = i + ki
                            nj = j + kj
                            if 0 <= ni < h and 0 <= nj < w:
                                if image[ni, nj] == 0:
                                    found = False
                                    break
                        if not found:
                            break
                    result[i, j] = 255 if found else 0
                else:
                    found = False
                    for ki in range(-pad, pad + 1):
                        for kj in range(-pad, pad + 1):
                            ni = i + ki
                            nj = j + kj
                            if 0 <= ni < h and 0 <= nj < w:
                                if image[ni, nj] == 255:
                                    found = True
                                    break
                        if found:
                            break
                    result[i, j] = 255 if found else 0

        return result


    def warmup():
        """预热Numba JIT编译器"""
        dummy = np.zeros((10, 10), dtype=np.uint8)
        ssd_match(dummy, dummy)
        ssd_match_parallel(dummy, dummy)
        normalized_cross_correlation(dummy, dummy)
        calculate_histogram(dummy)
        fast_gaussian_blur(dummy)
        fast_box_filter(dummy, 3)
        fast_histogram_equalization(dummy)
        fast_threshold(dummy, 128, "binary")
        fast_pixel_operation(dummy, "add", 10)
        fast_erode_dilate(dummy, 3, "erode")

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

    def fast_box_filter(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Fallback box filter using cv2"""
        import cv2
        return cv2.blur(image, (kernel_size, kernel_size))

    def fast_histogram_equalization(image: np.ndarray) -> np.ndarray:
        """Fallback histogram equalization using cv2"""
        import cv2
        return cv2.equalizeHist(image)

    def fast_threshold(image: np.ndarray, threshold: int, method: str = "binary") -> np.ndarray:
        """Fallback threshold using cv2"""
        import cv2
        if method == "otsu":
            _, result = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return result
        else:
            _, result = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
            return result

    def fast_pixel_operation(image: np.ndarray, operation: str, value: float = 0) -> np.ndarray:
        """Fallback pixel operation using numpy"""
        import cv2
        result = image.astype(np.float64)
        if operation == "add":
            result = np.clip(result + value, 0, 255)
        elif operation == "subtract":
            result = np.clip(result - value, 0, 255)
        elif operation == "multiply":
            result = np.clip(result * value, 0, 255)
        elif operation == "divide":
            result = np.clip(result / value, 0, 255) if value != 0 else result
        elif operation == "invert":
            result = 255 - result
        elif operation == "normalize":
            result = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        return result.astype(image.dtype)

    def fast_erode_dilate(image: np.ndarray, kernel_size: int = 3, operation: str = "erode") -> np.ndarray:
        """Fallback erode/dilate using cv2"""
        import cv2
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        if operation == "erode":
            return cv2.erode(image, kernel)
        else:
            return cv2.dilate(image, kernel)
