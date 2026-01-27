#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理引擎

提供多线程并行处理能力，优化CPU计算性能

Author: Vision System Team
Date: 2026-01-26
"""

import os
import sys
import threading
import concurrent.futures
from typing import List, Callable, Any, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("CPUOptimization.ParallelEngine")


class CPUAffinity(Enum):
    """CPU亲和性模式"""
    AUTO = "auto"              # 自动分配
    BALANCED = "balanced"      # 负载均衡
    PERFORMANCE = "performance"  # 性能优先
    EFFICIENCY = "efficiency"  # 能效优先


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ParallelTask:
    """并行任务"""
    task_id: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    depends_on: List[str] = None
    callback: Callable = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class ParallelEngine:
    """
    并行处理引擎
    
    提供高效的CPU并行计算能力，支持：
    - 线程池管理
    - 任务调度和优先级
    - CPU亲和性控制
    - 任务依赖管理
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._lock = threading.Lock()
        self._executors: Dict[str, ThreadPoolExecutor] = {}
        self._task_queue: List[ParallelTask] = []
        self._running_tasks: Dict[str, concurrent.futures.Future] = {}
        self._completed_tasks: List[ParallelTask] = []
        self._cpu_count = os.cpu_count() or 4
        self._max_workers = min(self._cpu_count, 8)  # 限制最大工作线程数
        self._active_executor = None
        
        self._setup_default_executor()
        logger.info(f"并行引擎初始化完成: CPU核心数={self._cpu_count}, 最大工作线程={self._max_workers}")
    
    def _setup_default_executor(self):
        """设置默认执行器"""
        self._active_executor = ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="CPUWorker",
            initializer=self._worker_init,
            initargs=()
        )
        self._executors["default"] = self._active_executor
    
    @staticmethod
    def _worker_init():
        """工作线程初始化"""
        import threading
        threading.current_thread().name = threading.current_thread().name.replace("ThreadPoolExecutor", "Worker")
    
    def set_affinity_mode(self, mode: CPUAffinity, core_list: List[int] = None):
        """
        设置CPU亲和性模式
        
        Args:
            mode: 亲和性模式
            core_list: 指定使用的CPU核心列表
        """
        try:
            if sys.platform == 'win32':
                self._set_windows_affinity(core_list if core_list else list(range(self._cpu_count)))
            elif sys.platform == 'linux':
                self._set_linux_affinity(core_list if core_list else list(range(self._cpu_count)))
            logger.info(f"CPU亲和性设置为: {mode.value}")
        except Exception as e:
            logger.warning(f"无法设置CPU亲和性: {e}")
    
    def _set_windows_affinity(self, core_list: List[int]):
        """Windows平台设置CPU亲和性"""
        try:
            import psutil
            proc = psutil.Process()
            mask = 0
            for core in core_list:
                mask |= (1 << core)
            proc.cpu_affinity([mask])
        except AttributeError:
            logger.warning("当前系统不支持CPU亲和性设置")
    
    def _set_linux_affinity(self, core_list: List[int]):
        """Linux平台设置CPU亲和性"""
        try:
            os.sched_setaffinity(0, set(core_list))
        except AttributeError:
            logger.warning("当前系统不支持CPU亲和性设置")
    
    def submit_task(self, task: ParallelTask) -> str:
        """
        提交任务到并行队列
        
        Args:
            task: 并行任务
            
        Returns:
            任务ID
        """
        with self._lock:
            self._task_queue.append(task)
            task_id = task.task_id
            logger.debug(f"任务已提交: {task_id}")
        return task_id
    
    def execute_parallel(self, tasks: List[ParallelTask], 
                        max_workers: int = None,
                        wait_for_completion: bool = True) -> List[Any]:
        """
        并行执行多个任务
        
        Args:
            tasks: 任务列表
            max_workers: 最大工作线程数
            wait_for_completion: 是否等待完成
            
        Returns:
            执行结果列表
        """
        if not tasks:
            return []
        
        # 使用专用执行器
        executor = ThreadPoolExecutor(
            max_workers=max_workers or self._max_workers,
            thread_name_prefix="ParallelWorker"
        )
        
        try:
            futures = []
            for task in tasks:
                future = executor.submit(task.function, *task.args, **task.kwargs)
                futures.append((task, future))
            
            if wait_for_completion:
                results = []
                for task, future in futures:
                    try:
                        result = future.result()
                        results.append(result)
                        if task.callback:
                            task.callback(result)
                    except Exception as e:
                        logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
                        results.append(None)
                return results
            else:
                return [f for _, f in futures]
        finally:
            executor.shutdown(wait=wait_for_completion)
    
    def map_function(self, func: Callable, 
                    data_list: List[Any],
                    use_threading: bool = True,
                    chunk_size: int = None) -> List[Any]:
        """
        对数据列表并行应用函数
        
        Args:
            func: 要应用的函数
            data_list: 数据列表
            use_threading: 是否使用线程（False使用进程）
            chunk_size: 数据块大小
            
        Returns:
            结果列表
        """
        if not data_list:
            return []
        
        executor_class = ThreadPoolExecutor if use_threading else ProcessPoolExecutor
        chunk_size = chunk_size or max(1, len(data_list) // (self._max_workers * 2))
        
        with executor_class(max_workers=self._max_workers) as executor:
            results = list(executor.map(func, data_list, chunksize=chunk_size))
        
        return results
    
    def parallel_for(self, start: int, end: int, 
                    func: Callable[[int], Any],
                    num_workers: int = None) -> List[Any]:
        """
        并行for循环
        
        Args:
            start: 起始索引
            end: 结束索引
            func: 处理函数
            num_workers: 工作线程数
            
        Returns:
            结果列表
        """
        indices = list(range(start, end))
        num_workers = num_workers or self._max_workers
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(executor.map(func, indices))
        
        return results
    
    def get_worker_count(self) -> int:
        """获取工作线程数"""
        return self._max_workers
    
    def get_queue_size(self) -> int:
        """获取待执行任务数量"""
        with self._lock:
            return len(self._task_queue)
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        with self._lock:
            self._completed_tasks.clear()
            logger.debug("已完成任务已清理")
    
    def shutdown(self):
        """关闭并行引擎"""
        with self._lock:
            for name, executor in self._executors.items():
                executor.shutdown(wait=True)
            self._executors.clear()
            self._task_queue.clear()
            self._running_tasks.clear()
            logger.info("并行引擎已关闭")
    
    @property
    def cpu_count(self) -> int:
        """获取CPU核心数"""
        return self._cpu_count


def parallel_map(func: Callable, 
                data_list: List[Any],
                workers: int = None,
                use_threading: bool = True) -> List[Any]:
    """
    便捷的并行映射函数
    
    Args:
        func: 处理函数
        data_list: 数据列表
        workers: 工作线程数
        use_threading: 是否使用线程
        
    Returns:
        结果列表
    """
    engine = ParallelEngine()
    return engine.map_function(func, data_list, use_threading=use_threading)


def parallel_for_range(start: int, end: int,
                      func: Callable[[int], Any],
                      workers: int = None) -> List[Any]:
    """
    便捷的并行for循环函数
    
    Args:
        start: 起始索引
        end: 结束索引
        func: 处理函数
        workers: 工作线程数
        
    Returns:
        结果列表
    """
    engine = ParallelEngine()
    return engine.parallel_for(start, end, func, num_workers=workers)


# 便利的并行化装饰器
class parallel:
    """
    并行化装饰器
    
    使用示例:
        @parallel(workers=4)
        def process_image(image):
            # 处理逻辑
            return result
    """
    
    def __init__(self, workers: int = None, use_threading: bool = True):
        self.workers = workers
        self.use_threading = use_threading
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            engine = ParallelEngine()
            if isinstance(args[0], (list, tuple)) and len(args) == 1:
                # 单参数列表
                return engine.map_function(func, args[0], use_threading=self.use_threading)
            elif isinstance(args[0], (list, tuple)) and len(args[0]) > 1:
                # 多参数列表
                return engine.map_function(
                    lambda x: func(*x) if isinstance(x, tuple) else func(x),
                    list(zip(*args)),
                    use_threading=self.use_threading
                )
            else:
                return func(*args, **kwargs)
        return wrapper


# 批量处理函数
def batch_process(items: List[Any],
                 process_func: Callable,
                 batch_size: int = 32,
                 workers: int = None,
                 show_progress: bool = False) -> List[Any]:
    """
    批量处理数据
    
    Args:
        items: 数据列表
        process_func: 处理函数
        batch_size: 批次大小
        workers: 工作线程数
        show_progress: 显示进度
        
    Returns:
        处理结果列表
    """
    engine = ParallelEngine()
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]
        
        batch_results = engine.map_function(process_func, batch, use_threading=True)
        results.extend(batch_results)
        
        if show_progress:
            progress = (batch_idx + 1) / total_batches * 100
            print(f"\r处理进度: {progress:.1f}%", end="", flush=True)
    
    if show_progress:
        print()
    
    return results


# 图像分块并行处理
def process_image_tiles(image, 
                       process_func: Callable,
                       tile_size: int = 256,
                       overlap: int = 32,
                       workers: int = None) -> Any:
    """
    将图像分块后并行处理
    
    Args:
        image: 输入图像
        process_func: 图像块处理函数
        tile_size: 块大小
        overlap: 块重叠区域
        workers: 工作线程数
        
    Returns:
        处理后的图像或结果
    """
    engine = ParallelEngine()
    h, w = image.shape[:2]
    
    # 计算分块位置
    tiles = []
    for y in range(0, h, tile_size - overlap):
        for x in range(0, w, tile_size - overlap):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            tiles.append((y, x, y_end, x_end))
    
    if not tiles:
        return process_func(image)
    
    # 提取图像块
    patches = []
    for y, x, y_end, x_end in tiles:
        patch = image[y:y_end, x:x_end]
        patches.append(patch)
    
    # 并行处理
    results = engine.map_function(process_func, patches, use_threading=True)
    
    return results, tiles


if __name__ == "__main__":
    # 测试并行引擎
    print("测试并行处理引擎...")
    
    engine = ParallelEngine()
    print(f"CPU核心数: {engine.cpu_count}")
    print(f"工作线程数: {engine.get_worker_count()}")
    
    # 测试并行计算
    import time
    import numpy as np
    
    def heavy_computation(x):
        time.sleep(0.1)
        return x ** 2
    
    data = list(range(10))
    start = time.time()
    results = engine.map_function(heavy_computation, data)
    elapsed = time.time() - start
    print(f"并行处理10个任务耗时: {elapsed:.3f}秒")
    print(f"结果: {results}")
    
    print("测试完成!")
