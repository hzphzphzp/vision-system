#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMD优化模块

提供SIMD指令集优化，包括：
- 向量化操作
- 批量数据处理优化
- 矩阵运算加速

Author: Vision System Team
Date: 2026-01-26
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple

import numpy as np

logger = logging.getLogger("CPUOptimization.SIMD")


@dataclass
class SIMDCapabilities:
    """SIMD能力检测结果"""

    sse2: bool = False
    sse3: bool = False
    sse4_1: bool = False
    sse4_2: bool = False
    avx: bool = False
    avx2: bool = False
    avx512f: bool = False
    neon: bool = False
    optimization_level: str = "none"


class SIMDOptimizer:
    """
    SIMD优化器

    提供基于CPU SIMD能力的自动优化
    """

    _instance = None
    _capabilities: SIMDCapabilities = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._capabilities = cls._instance._detect_capabilities()
        return cls._instance

    def _detect_capabilities(self) -> SIMDCapabilities:
        """检测CPU SIMD能力"""
        caps = SIMDCapabilities()

        try:
            import cpuinfo

            cpu_info = cpuinfo.get_cpu_info()
            flags = cpu_info.get("flags", [])

            caps.sse2 = "sse2" in flags
            caps.sse3 = "sse3" in flags
            caps.sse4_1 = "sse4_1" in flags
            caps.sse4_2 = "sse4_2" in flags
            caps.avx = "avx" in flags
            caps.avx2 = "avx2" in flags
            caps.avx512f = "avx512f" in flags
            caps.neon = "asimd" in flags or "neon" in flags

        except ImportError:
            caps = self._manual_detect()

        # 确定优化级别
        if caps.avx512f:
            caps.optimization_level = "avx512"
        elif caps.avx2:
            caps.optimization_level = "avx2"
        elif caps.sse4_2:
            caps.optimization_level = "sse4"
        elif caps.sse3:
            caps.optimization_level = "sse3"
        else:
            caps.optimization_level = "none"

        logger.info(f"SIMD能力检测: {caps.optimization_level}")
        return caps

    def _manual_detect(self) -> SIMDCapabilities:
        """手动检测SIMD能力"""
        caps = SIMDCapabilities()

        try:
            if sys.platform == "linux":
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    caps.sse2 = "sse2" in cpuinfo
                    caps.sse3 = "sse3" in cpuinfo
                    caps.sse4_1 = "sse4_1" in cpuinfo
                    caps.sse4_2 = "sse4_2" in cpuinfo
                    caps.avx = "avx" in cpuinfo
                    caps.avx2 = "avx2" in cpuinfo
                    caps.avx512f = "avx512f" in cpuinfo
                    caps.neon = "asimd" in cpuinfo or "neon" in cpuinfo
            elif sys.platform == "darwin":
                import subprocess

                result = subprocess.run(
                    ["sysctl", "hw.optional"], capture_output=True, text=True
                )
                output = result.stdout
                caps.sse2 = "SSE2" in output
                caps.sse3 = "SSE3" in output
                caps.sse4_1 = "SSE4.1" in output
                caps.sse4_2 = "SSE4.2" in output
                caps.avx = "AVX1.0" in output
                caps.avx2 = "AVX2" in output
        except Exception as e:
            logger.warning(f"无法检测SIMD能力: {e}")

        return caps

    @property
    def capabilities(self) -> SIMDCapabilities:
        """获取SIMD能力"""
        return self._capabilities

    def get_optimized_function(self, func_name: str) -> Callable:
        """
        获取优化的函数版本

        Args:
            func_name: 函数名称

        Returns:
            优化后的函数
        """
        optimization_map = {
            "convolution": self._optimized_convolution,
            "pooling": self._optimized_pooling,
            "relu": self._optimized_relu,
            "softmax": self._optimized_softmax,
            "normalize": self._optimized_normalize,
            "matmul": self._optimized_matmul,
        }

        return optimization_map.get(func_name, lambda x: x)

    def _optimized_convolution(
        self,
        input_data: np.ndarray,
        kernel: np.ndarray,
        stride: Tuple[int, int] = (1, 1),
        padding: Tuple[int, int] = (0, 0),
    ) -> np.ndarray:
        """
        优化的卷积操作

        使用NumPy的向量化操作替代循环
        """
        # 输入维度
        if input_data.ndim == 3:
            batch, height, width = input_data.shape
            channels = 1
        else:
            raise ValueError("只支持2D灰度图像")

        kernel_h, kernel_w = kernel.shape
        stride_h, stride_w = stride
        pad_h, pad_w = padding

        # 计算输出尺寸
        out_h = (height + 2 * pad_h - kernel_h) // stride_h + 1
        out_w = (width + 2 * pad_w - kernel_w) // stride_w + 1

        # 填充输入
        if pad_h > 0 or pad_w > 0:
            padded = np.pad(
                input_data,
                ((0, 0), (pad_h, pad_h), (pad_w, pad_w)),
                mode="constant",
                constant_values=0,
            )
        else:
            padded = input_data

        # 使用im2col + 矩阵乘法优化
        cols = self._im2col(padded, kernel_h, kernel_w, stride_h, stride_w)

        # 展平核
        kernel_flat = kernel.flatten().reshape(-1, 1)

        # 矩阵乘法
        output = np.dot(cols, kernel_flat).reshape(batch, out_h, out_w)

        return output

    def _im2col(
        self,
        input_data: np.ndarray,
        kernel_h: int,
        kernel_w: int,
        stride_h: int,
        stride_w: int,
    ) -> np.ndarray:
        """图像到列的转换，用于卷积优化"""
        batch, height, width = input_data.shape

        out_h = (height - kernel_h) // stride_h + 1
        out_w = (width - kernel_w) // stride_w + 1

        # 展平图像块
        shape = (batch, kernel_h, kernel_w, out_h, out_w)
        strides = (
            input_data.strides[0],
            input_data.strides[1] * stride_h,
            input_data.strides[2] * stride_w,
            input_data.strides[1],
            input_data.strides[2],
        )

        patches = np.lib.stride_tricks.as_strided(
            input_data, shape=shape, strides=strides
        )

        return patches.reshape(batch * out_h * out_w, kernel_h * kernel_w)

    def _optimized_pooling(
        self,
        input_data: np.ndarray,
        pool_size: Tuple[int, int] = (2, 2),
        stride: Tuple[int, int] = (2, 2),
        mode: str = "max",
    ) -> np.ndarray:
        """
        优化的池化操作

        使用步长和形状技巧避免循环
        """
        if input_data.ndim == 3:
            batch, height, width = input_data.shape
        else:
            raise ValueError("输入必须为3维 [batch, height, width]")

        pool_h, pool_w = pool_size
        stride_h, stride_w = stride

        out_h = (height - pool_h) // stride_h + 1
        out_w = (width - pool_w) // stride_w + 1

        # 使用视图进行池化
        shape = (batch, out_h, pool_h, out_w, pool_w)
        strides = (
            input_data.strides[0],
            input_data.strides[1] * stride_h,
            input_data.strides[1],
            input_data.strides[2] * stride_w,
            input_data.strides[2],
        )

        view = np.lib.stride_tricks.as_strided(
            input_data, shape=shape, strides=strides
        )

        if mode == "max":
            return view.max(axis=(2, 4))
        elif mode == "avg":
            return view.mean(axis=(2, 4))
        else:
            raise ValueError(f"不支持的池化模式: {mode}")

    def _optimized_relu(
        self, input_data: np.ndarray, negative_slope: float = 0.0
    ) -> np.ndarray:
        """
        优化的ReLU激活函数

        使用np.maximum进行向量化操作
        """
        return np.maximum(input_data, negative_slope * input_data)

    def _optimized_softmax(
        self, input_data: np.ndarray, axis: int = -1
    ) -> np.ndarray:
        """
        优化的Softmax函数

        数值稳定的Softmax实现
        """
        input_max = np.max(input_data, axis=axis, keepdims=True)
        exp_inputs = np.exp(input_data - input_max)
        exp_sum = np.sum(exp_inputs, axis=axis, keepdims=True)
        return exp_inputs / exp_sum

    def _optimized_normalize(
        self, input_data: np.ndarray, method: str = "l2"
    ) -> np.ndarray:
        """
        优化的归一化操作

        支持L1、L2归一化
        """
        if method == "l2":
            norm = np.sqrt(np.sum(input_data**2, axis=-1, keepdims=True))
            norm = np.maximum(norm, 1e-8)
            return input_data / norm
        elif method == "l1":
            norm = np.sum(np.abs(input_data), axis=-1, keepdims=True)
            norm = np.maximum(norm, 1e-8)
            return input_data / norm
        else:
            raise ValueError(f"不支持的归一化方法: {method}")

    def _optimized_matmul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        优化的矩阵乘法

        利用NumPy的BLAS优化
        """
        return np.dot(a, b)

    def batch_normalize(
        self,
        data: np.ndarray,
        mean: np.ndarray = None,
        std: np.ndarray = None,
        epsilon: float = 1e-8,
    ) -> np.ndarray:
        """
        批量标准化（用于推理）

        Args:
            data: 输入数据
            mean: 均值，如果为None则从数据计算
            std: 标准差，如果为None则从数据计算
            epsilon: 防止除零的小常数

        Returns:
            标准化后的数据
        """
        if mean is None:
            mean = data.mean(axis=(0, 2, 3), keepdims=True)
        if std is None:
            std = data.std(axis=(0, 2, 3), keepdims=True)

        std = np.maximum(std, epsilon)
        return (data - mean) / std

    def nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        iou_threshold: float = 0.5,
        score_threshold: float = 0.01,
    ) -> np.ndarray:
        """
        非极大值抑制优化版本

        使用向量化操作加速
        """
        if len(boxes) == 0:
            return np.array([], dtype=np.int32)

        # 过滤低分框
        mask = scores >= score_threshold
        boxes = boxes[mask]
        scores = scores[mask]

        if len(boxes) == 0:
            return np.array([], dtype=np.int32)

        # 按分数排序
        order = scores.argsort()[::-1]
        boxes = boxes[order]

        keep = []
        while len(boxes) > 0:
            # 选择最高分的框
            keep.append(order[0])

            if len(boxes) == 1:
                break

            # 计算与最高分框的IoU
            ious = self._compute_iou(boxes[0], boxes[1:])

            # 过滤高IoU的框
            mask = ious < iou_threshold
            boxes = boxes[1:][mask]
            order = order[1:][mask]

        return np.array(keep, dtype=np.int32)

    def _compute_iou(self, box: np.ndarray, others: np.ndarray) -> np.ndarray:
        """
        计算一个框与多个框的IoU

        向量化实现
        """
        # 交集区域
        inter_x1 = np.maximum(box[0], others[:, 0])
        inter_y1 = np.maximum(box[1], others[:, 1])
        inter_x2 = np.minimum(box[2], others[:, 2])
        inter_y2 = np.minimum(box[3], others[:, 3])

        inter_area = np.maximum(0, inter_x2 - inter_x1) * np.maximum(
            0, inter_y2 - inter_y1
        )

        # 并集区域
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        other_areas = (others[:, 2] - others[:, 0]) * (
            others[:, 3] - others[:, 1]
        )

        union_area = box_area + other_areas - inter_area

        return inter_area / (union_area + 1e-8)

    def quantize(
        self, data: np.ndarray, num_bits: int = 8
    ) -> Tuple[np.ndarray, float, float]:
        """
        动态量化

        将float32量化为int8/int16

        Args:
            data: 输入数据
            num_bits: 量化位数 (8 或 16)

        Returns:
            量化后的数据, scale, zero_point
        """
        if num_bits == 8:
            dtype = np.int8
            min_val = -128
            max_val = 127
        else:
            dtype = np.int16
            min_val = -32768
            max_val = 32767

        # 计算scale和zero_point
        data_min = data.min()
        data_max = data.max()

        scale = (data_max - data_min) / (max_val - min_val)
        zero_point = min_val - data_min / scale

        # 量化
        quantized = np.round(data / scale + zero_point).astype(dtype)

        return quantized, scale, zero_point

    def dequantize(
        self, data: np.ndarray, scale: float, zero_point: float
    ) -> np.ndarray:
        """
        反量化

        将量化数据还原为float32
        """
        return (data.astype(np.float32) - zero_point) * scale


# 获取全局SIMD优化器实例
def get_simd_optimizer() -> SIMDOptimizer:
    """获取全局SIMD优化器实例"""
    return SIMDOptimizer()


if __name__ == "__main__":
    print("测试SIMD优化器...")

    optimizer = SIMDOptimizer()
    caps = optimizer.capabilities

    print(f"优化级别: {caps.optimization_level}")
    print(f"SSE2: {caps.sse2}")
    print(f"SSE3: {caps.sse3}")
    print(f"SSE4.1: {caps.sse4_1}")
    print(f"SSE4.2: {caps.sse4_2}")
    print(f"AVX: {caps.avx}")
    print(f"AVX2: {caps.avx2}")
    print(f"AVX512: {caps.avx512f}")
    print(f"NEON: {caps.neon}")

    # 测试优化的ReLU
    data = np.random.randn(100, 100).astype(np.float32)
    result = optimizer._optimized_relu(data)
    print(f"ReLU优化测试完成，输出形状: {result.shape}")

    # 测试NMS
    boxes = np.array(
        [[10, 10, 50, 50], [15, 15, 55, 55], [100, 100, 150, 150]]
    )
    scores = np.array([0.9, 0.8, 0.7])
    keep = optimizer.nms(boxes, scores)
    print(f"NMS测试完成，保留框索引: {keep}")

    # 测试量化
    data = np.random.randn(1000).astype(np.float32) * 10
    quantized, scale, zp = optimizer.quantize(data, 8)
    dequantized = optimizer.dequantize(quantized, scale, zp)
    error = np.abs(data - dequantized).mean()
    print(f"量化测试完成，平均误差: {error:.6f}")

    print("测试完成!")
