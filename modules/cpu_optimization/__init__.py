#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU优化模块

提供基于CPU的高性能计算优化方案，包括：
- 多线程并行处理
- SIMD指令集优化
- 内存访问模式优化
- 计算任务分块策略

与YOLO26模型集成，实现CPU环境下的高效推理

Author: Vision System Team
Date: 2026-01-26
"""

import sys
from pathlib import Path

# 添加模块路径
_module_path = Path(__file__).parent
if str(_module_path) not in sys.path:
    sys.path.insert(0, str(_module_path))

from .core.parallel_engine import ParallelEngine, CPUAffinity
from .core.memory_pool import MemoryPool, TensorPool
from .core.simd_optimizations import SIMDOptimizer
from .models.yolo26_cpu import YOLO26CPUDetector, CPUInferenceConfig
from .api.cpu_detector import CPUDetectorAPI, DetectionResult
from .utils.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    get_performance_monitor,
)
from .utils.model_downloader import YOLO26ModelDownloader, get_downloader

__version__ = "1.0.0"
__author__ = "Vision System Team"

__all__ = [
    # 核心优化引擎
    "ParallelEngine",
    "CPUAffinity",
    "MemoryPool",
    "TensorPool",
    "SIMDOptimizer",
    # 模型层
    "YOLO26CPUDetector",
    "CPUInferenceConfig",
    # API接口
    "CPUDetectorAPI",
    "DetectionResult",
    # 性能监控
    "PerformanceMonitor",
    "PerformanceMetrics",
    "get_performance_monitor",
    # 模型下载
    "YOLO26ModelDownloader",
    "get_downloader",
]


def get_module_info():
    """获取模块信息"""
    return {
        "name": "CPU优化模块",
        "version": __version__,
        "author": __author__,
        "description": "基于CPU的高性能计算优化模块，支持YOLO26模型推理",
        "features": [
            "多线程并行处理",
            "SIMD指令集优化",
            "内存池管理",
            "张量池管理",
            "任务分块处理",
            "性能实时监控",
            "YOLO26模型自动下载",
        ],
        "requirements": ["Python 3.8+", "NumPy", "OpenCV", "psutil"],
    }


def check_system_capabilities():
    """检查系统CPU优化能力"""
    import platform

    capabilities = {
        "platform": platform.system(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": 0,
        "simd_support": [],
        "memory_info": {},
    }

    try:
        import psutil

        capabilities["cpu_count"] = psutil.cpu_count(logical=True)
        capabilities["physical_cpu_count"] = psutil.cpu_count(logical=False)
        capabilities["memory_info"] = {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
        }
    except ImportError:
        capabilities["cpu_count"] = 4  # 默认值
        capabilities["memory_info"] = {"total": "unknown", "available": "unknown"}

    # 检查SIMD支持
    try:
        import cpuinfo

        cpu_info = cpuinfo.get_cpu_info()
        capabilities["brand"] = cpu_info.get("brand", "Unknown")
        capabilities["simd_support"] = cpu_info.get("flags", [])
    except ImportError:
        # 手动检查SIMD
        capabilities["simd_support"] = []
        try:
            import subprocess

            result = subprocess.run(["lscpu"], capture_output=True, text=True)
            if "Flags:" in result.stdout:
                flags = result.stdout.split("Flags:")[1].split("\n")[0].strip()
                capabilities["simd_support"] = flags.split()
        except Exception:
            pass

    return capabilities


def print_system_info():
    """打印系统信息"""
    info = get_module_info()
    capabilities = check_system_capabilities()

    print("=" * 60)
    print(f"  {info['name']} v{info['version']}")
    print("=" * 60)
    print(f"平台: {capabilities['platform']}")
    print(f"处理器: {capabilities.get('brand', capabilities['processor'])}")
    print(
        f"CPU核心数: {capabilities['cpu_count']} (物理: {capabilities.get('physical_cpu_count', 'N/A')})"
    )
    print(f"Python版本: {capabilities['python_version']}")
    print(
        f"总内存: {capabilities['memory_info'].get('total', 'N/A') / (1024**3):.2f} GB"
    )
    print(
        "SIMD支持:",
        ", ".join(
            [
                f
                for f in capabilities["simd_support"]
                if f.startswith(("sse", "avx", "neon"))
            ]
        )
        or "无检测到",
    )
    print("-" * 60)
    print("可用优化功能:")
    for feature in info["features"]:
        print(f"  ✓ {feature}")
    print("=" * 60)


if __name__ == "__main__":
    print_system_info()
