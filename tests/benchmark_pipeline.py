# -*- coding: utf-8 -*-
"""
性能基准测试

Author: AI Agent
Date: 2026-02-03
"""

import time
import numpy as np
import statistics
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.solution import Solution
from data.image_data import ImageData
from core.memory_pool import ImageBufferPool


def benchmark_normal_mode(iterations=50):
    """测试普通模式性能"""
    solution = Solution("benchmark_normal")
    
    times = []
    for i in range(iterations):
        data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        img = ImageData(data=data)
        
        start = time.time()
        solution.run(img)
        elapsed = time.time() - start
        times.append(elapsed * 1000)  # ms
    
    return {
        "mode": "normal",
        "iterations": iterations,
        "avg_ms": statistics.mean(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "fps": 1000 / statistics.mean(times)
    }


def benchmark_pipeline_mode(iterations=50):
    """测试流水线模式性能"""
    solution = Solution("benchmark_pipeline")
    solution.enable_pipeline_mode(buffer_size=5)
    
    # 预热
    for _ in range(5):
        data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        img = ImageData(data=data)
        solution.put_input(img)
    time.sleep(0.3)
    
    # 正式测试
    start = time.time()
    for i in range(iterations):
        data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        img = ImageData(data=data)
        solution.put_input(img)
    
    # 等待完成
    time.sleep(0.5)
    elapsed = time.time() - start
    
    return {
        "mode": "pipeline",
        "iterations": iterations,
        "total_ms": elapsed * 1000,
        "avg_ms": (elapsed / iterations) * 1000,
        "fps": iterations / elapsed
    }


def benchmark_memory_pool():
    """测试内存池性能"""
    # 普通分配
    start = time.time()
    for _ in range(500):
        buf = np.zeros((480, 640, 3), dtype=np.uint8)
        del buf
    normal_time = time.time() - start
    
    # 内存池
    pool = ImageBufferPool(max_size=10, buffer_shape=(480, 640, 3))
    start = time.time()
    for _ in range(500):
        buf = pool.acquire()
        pool.release(buf)
    pool_time = time.time() - start
    
    return {
        "normal_ms": normal_time * 1000,
        "pool_ms": pool_time * 1000,
        "speedup": normal_time / pool_time
    }


if __name__ == "__main__":
    print("Running benchmarks...")
    
    print("\n1. Memory Pool Benchmark:")
    result = benchmark_memory_pool()
    print(f"   Normal: {result['normal_ms']:.2f}ms")
    print(f"   Pool: {result['pool_ms']:.2f}ms")
    print(f"   Speedup: {result['speedup']:.2f}x")
    
    print("\n2. Normal Mode Benchmark:")
    result = benchmark_normal_mode(iterations=30)
    print(f"   Avg: {result['avg_ms']:.2f}ms")
    print(f"   Min: {result['min_ms']:.2f}ms")
    print(f"   Max: {result['max_ms']:.2f}ms")
    print(f"   FPS: {result['fps']:.2f}")
    
    print("\n3. Pipeline Mode Benchmark:")
    result = benchmark_pipeline_mode(iterations=30)
    print(f"   Avg: {result['avg_ms']:.2f}ms")
    print(f"   FPS: {result['fps']:.2f}")
    
    print("\nBenchmarks completed!")
