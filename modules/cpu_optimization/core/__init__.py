#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU优化核心模块

提供高性能计算的基础组件：
- 并行处理引擎
- 内存池管理
- SIMD优化

Author: Vision System Team
Date: 2026-01-26
"""

from .memory_pool import (
    ImageMemoryPool,
    MemoryBlock,
    MemoryPool,
    TensorPool,
    get_image_pool,
    get_memory_pool,
)
from .parallel_engine import (
    CPUAffinity,
    ParallelEngine,
    ParallelTask,
    TaskPriority,
    batch_process,
    parallel,
    parallel_for_range,
    parallel_map,
    process_image_tiles,
)
from .simd_optimizations import (
    SIMDCapabilities,
    SIMDOptimizer,
    get_simd_optimizer,
)

__all__ = [
    # 并行引擎
    "ParallelEngine",
    "CPUAffinity",
    "ParallelTask",
    "TaskPriority",
    "parallel_map",
    "parallel_for_range",
    "parallel",
    "batch_process",
    "process_image_tiles",
    # 内存池
    "MemoryPool",
    "MemoryBlock",
    "TensorPool",
    "ImageMemoryPool",
    "get_memory_pool",
    "get_image_pool",
    # SIMD优化
    "SIMDOptimizer",
    "SIMDCapabilities",
    "get_simd_optimizer",
]
