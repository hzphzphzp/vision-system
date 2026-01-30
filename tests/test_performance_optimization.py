#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化测试

测试并行处理引擎和内存池管理功能
"""

import os
import sys
import time

import numpy as np
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cpu_optimization.core.memory_pool import (
    ImageMemoryPool,
    MemoryPool,
    get_image_pool,
    get_memory_pool,
)
from modules.cpu_optimization.core.parallel_engine import (
    ParallelEngine,
    batch_process,
    parallel_for_range,
    parallel_map,
)
from modules.cpu_optimization.core.simd_optimizations import (
    SIMDOptimizer,
    get_simd_optimizer,
)


class TestParallelEngine:
    """测试并行处理引擎"""

    def test_parallel_engine_initialization(self):
        """测试并行引擎初始化"""
        engine = ParallelEngine()
        assert engine is not None
        assert engine.cpu_count > 0
        assert engine.get_worker_count() > 0

    def test_parallel_map(self):
        """测试并行映射功能"""
        # 测试数据
        data = list(range(100))

        # 测试函数
        def square(x):
            time.sleep(0.01)  # 添加一些延迟来模拟计算密集型任务
            return x * x

        # 串行处理
        start_time = time.time()
        serial_results = [square(x) for x in data]
        serial_time = time.time() - start_time

        # 并行处理
        start_time = time.time()
        parallel_results = parallel_map(square, data)
        parallel_time = time.time() - start_time

        # 验证结果
        assert len(parallel_results) == len(serial_results)
        assert all(p == s for p, s in zip(parallel_results, serial_results))

        # 验证并行处理速度更快
        assert parallel_time < serial_time

    def test_parallel_for_range(self):
        """测试并行for循环功能"""

        # 测试函数
        def compute(i):
            time.sleep(0.005)  # 添加一些延迟
            return i * 2

        # 串行处理
        start_time = time.time()
        serial_results = [compute(i) for i in range(50)]
        serial_time = time.time() - start_time

        # 并行处理
        start_time = time.time()
        parallel_results = parallel_for_range(0, 50, compute)
        parallel_time = time.time() - start_time

        # 验证结果
        assert len(parallel_results) == 50
        assert all(p == s for p, s in zip(parallel_results, serial_results))

        # 验证并行处理速度更快
        assert parallel_time < serial_time

    def test_batch_process(self):
        """测试批量处理功能"""
        # 测试数据
        data = list(range(100))

        # 测试函数
        def process_item(x):
            time.sleep(0.005)  # 添加一些延迟
            return x + 1

        # 测试批量处理
        results = batch_process(
            data, process_item, batch_size=20, show_progress=False
        )

        # 验证结果
        assert len(results) == 100
        assert all(r == i + 1 for r, i in zip(results, data))

    def test_cpu_affinity(self):
        """测试CPU亲和性设置"""
        engine = ParallelEngine()
        # 测试设置CPU亲和性
        engine.set_affinity_mode("balanced")
        # 这里不进行断言，因为不同平台的行为可能不同
        # 只确保方法调用不会抛出异常


class TestMemoryPool:
    """测试内存池管理"""

    def test_memory_pool_initialization(self):
        """测试内存池初始化"""
        pool = get_memory_pool()
        assert pool is not None

    def test_create_and_get_block(self):
        """测试创建和获取内存块"""
        pool = get_memory_pool()

        # 创建内存池
        pool.create_pool("test_pool", 1024, 10, dtype=np.float32)

        # 获取内存块
        block = pool.get("test_pool")
        assert block is not None
        assert block.dtype == np.float32
        assert block.size >= 1024

        # 释放内存块
        pool.release("test_pool", block)

    def test_memory_pool_stats(self):
        """测试内存池统计信息"""
        pool = get_memory_pool()
        stats = pool.get_stats()
        assert isinstance(stats, dict)
        assert "total_allocated_mb" in stats
        assert "max_size_mb" in stats
        assert "hit_count" in stats
        assert "miss_count" in stats
        assert "pools" in stats


class TestImageMemoryPool:
    """测试图像处理内存池"""

    def test_image_pool_initialization(self):
        """测试图像内存池初始化"""
        img_pool = get_image_pool()
        assert img_pool is not None

    def test_get_image_buffer(self):
        """测试获取图像缓冲区"""
        img_pool = get_image_pool()

        # 获取图像缓冲区
        buffer = img_pool.get_image_buffer(640, 480, 3)
        assert buffer is not None
        assert buffer.shape == (480, 640, 3)
        assert buffer.dtype == np.uint8

        # 释放图像缓冲区
        img_pool.release_image_buffer(buffer)

    def test_image_context_manager(self):
        """测试图像上下文管理器"""
        img_pool = get_image_pool()

        # 使用上下文管理器
        with img_pool.image_context(640, 480, 3) as buffer:
            assert buffer is not None
            assert buffer.shape == (480, 640, 3)
            # 测试修改缓冲区
            buffer[:] = 128
            assert np.all(buffer == 128)

        # 上下文管理器结束后，缓冲区应该被自动释放

    def test_get_tensor(self):
        """测试获取张量"""
        img_pool = get_image_pool()

        # 获取张量
        tensor = img_pool.get_tensor(4, 224, 224, 3)
        assert tensor is not None
        assert tensor.shape == (4, 3, 224, 224)
        assert tensor.dtype == np.float32

        # 释放张量
        img_pool.release_tensor(tensor)


class TestSIMDOptimizations:
    """测试SIMD优化"""

    def test_simd_optimizer_initialization(self):
        """测试SIMD优化器初始化"""
        optimizer = get_simd_optimizer()
        assert optimizer is not None
        assert optimizer.capabilities is not None

    def test_optimized_functions(self):
        """测试优化的函数"""
        optimizer = get_simd_optimizer()

        # 测试ReLU
        data = np.random.randn(1000).astype(np.float32)
        result = optimizer._optimized_relu(data)
        assert result.shape == data.shape
        assert np.all(result >= 0)

        # 测试Softmax
        data = np.random.randn(10, 5).astype(np.float32)
        result = optimizer._optimized_softmax(data)
        assert result.shape == data.shape
        assert np.allclose(np.sum(result, axis=1), 1.0, atol=1e-5)

        # 测试归一化
        data = np.random.randn(10, 5).astype(np.float32)
        result = optimizer._optimized_normalize(data)
        assert result.shape == data.shape

    def test_nms(self):
        """测试非极大值抑制"""
        optimizer = get_simd_optimizer()

        # 测试数据
        boxes = np.array(
            [[10, 10, 50, 50], [15, 15, 55, 55], [100, 100, 150, 150]]
        )
        scores = np.array([0.9, 0.8, 0.7])

        # 测试NMS
        keep = optimizer.nms(boxes, scores)
        assert isinstance(keep, np.ndarray)
        assert keep.dtype == np.int32

    def test_quantization(self):
        """测试量化功能"""
        optimizer = get_simd_optimizer()

        # 测试数据
        data = np.random.randn(1000).astype(np.float32) * 10

        # 测试量化
        quantized, scale, zp = optimizer.quantize(data, 8)
        assert quantized.dtype == np.int8

        # 测试反量化
        dequantized = optimizer.dequantize(quantized, scale, zp)
        assert dequantized.dtype == np.float32
        assert dequantized.shape == data.shape


if __name__ == "__main__":
    # 运行测试
    test_parallel_engine = TestParallelEngine()
    test_parallel_engine.test_parallel_engine_initialization()
    test_parallel_engine.test_parallel_map()
    test_parallel_engine.test_parallel_for_range()
    test_parallel_engine.test_batch_process()
    test_parallel_engine.test_cpu_affinity()

    test_memory_pool = TestMemoryPool()
    test_memory_pool.test_memory_pool_initialization()
    test_memory_pool.test_create_and_get_block()
    test_memory_pool.test_memory_pool_stats()

    test_image_memory_pool = TestImageMemoryPool()
    test_image_memory_pool.test_image_pool_initialization()
    test_image_memory_pool.test_get_image_buffer()
    test_image_memory_pool.test_image_context_manager()
    test_image_memory_pool.test_get_tensor()

    test_simd = TestSIMDOptimizations()
    test_simd.test_simd_optimizer_initialization()
    test_simd.test_optimized_functions()
    test_simd.test_nms()
    test_simd.test_quantization()

    print("所有测试通过！")
