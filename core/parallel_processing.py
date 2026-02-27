#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理工具模块

提供多进程并行处理功能，用于批量图像处理和算法加速。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from typing import Any, Callable, List, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from joblib import Parallel, delayed, parallel_backend

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ParallelProcessor:
    """并行处理器

    支持多进程和多线程并行处理，适用于批量图像处理场景。
    """

    def __init__(self, n_jobs: int = -1, backend: str = "loky", prefer: str = "threads"):
        """初始化并行处理器

        Args:
            n_jobs: 并行任务数量，-1表示使用所有CPU核心
            backend: joblib后端 ('loky', 'multiprocessing', 'threading')
            prefer: 优先模式 ('threads' for I/O bound, 'processes' for CPU bound)
        """
        self.n_jobs = n_jobs
        self.backend = backend
        self.prefer = prefer

    def map(self, func: Callable, items: List[Any], desc: str = "Processing") -> List[Any]:
        """并行映射处理

        Args:
            func: 处理函数
            items: 输入项列表
            desc: 描述信息

        Returns:
            处理结果列表
        """
        if self.n_jobs == 1 or len(items) <= 1:
            return [func(item) for item in items]

        with parallel_backend(self.backend, n_jobs=self.n_jobs):
            results = Parallel(prefer=self.prefer)(
                delayed(func)(item) for item in items
            )
        return results

    def process_images(self, image_paths: List[str], process_func: Callable,
                      n_jobs: int = None) -> List[Any]:
        """并行处理图像

        Args:
            image_paths: 图像路径列表
            process_func: 图像处理函数，接收图像路径返回处理结果
            n_jobs: 并行数量，默认使用初始化值

        Returns:
            处理结果列表
        """
        n = n_jobs if n_jobs is not None else self.n_jobs

        if n == 1 or len(image_paths) <= 1:
            return [process_func(path) for path in image_paths]

        with ProcessPoolExecutor(max_workers=n) as executor:
            futures = {executor.submit(process_func, path): path for path in image_paths}
            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"处理失败: {futures[future]}, 错误: {e}")
                    results.append(None)
        return results


def parallel_map(func: Callable, items: List[Any], n_jobs: int = -1,
                backend: str = "loky") -> List[Any]:
    """便捷的并行映射函数

    Args:
        func: 处理函数
        items: 输入项列表
        n_jobs: 并行任务数量
        backend: 并行后端

    Returns:
        处理结果列表
    """
    processor = ParallelProcessor(n_jobs=n_jobs, backend=backend)
    return processor.map(func, items)


def batch_process_images(image_paths: List[str], process_func: Callable,
                        batch_size: int = 4) -> List[Any]:
    """批量处理图像（带内存控制）

    Args:
        image_paths: 图像路径列表
        process_func: 图像处理函数
        batch_size: 每批处理数量

    Returns:
        处理结果列表
    """
    results = []
    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i + batch_size]
        processor = ParallelProcessor(n_jobs=batch_size)
        batch_results = processor.map(process_func, batch, desc=f"Batch {i//batch_size + 1}")
        results.extend(batch_results)
    return results
