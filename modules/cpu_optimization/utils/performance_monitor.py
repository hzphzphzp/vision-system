#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块

提供实时性能监控功能，包括CPU利用率、内存占用、推理耗时等关键指标

Author: Vision System Team
Date: 2026-01-26
"""

import os
import sys
import time
import threading
import psutil
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import statistics

logger = logging.getLogger("CPUOptimization.Monitor")


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float = 0
    cpu_percent: float = 0
    memory_percent: float = 0
    memory_used_mb: float = 0
    memory_available_mb: float = 0
    inference_time_ms: float = 0
    fps: float = 0
    queue_size: int = 0
    thread_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_available_mb": round(self.memory_available_mb, 2),
            "inference_time_ms": round(self.inference_time_ms, 2),
            "fps": round(self.fps, 2),
            "queue_size": self.queue_size,
            "thread_count": self.thread_count
        }
    
    def to_display_dict(self) -> Dict[str, str]:
        """转换为显示友好的字典"""
        return {
            "CPU利用率": f"{self.cpu_percent:.1f}%",
            "内存占用": f"{self.memory_used_mb:.1f} MB ({self.memory_percent:.1f}%)",
            "推理耗时": f"{self.inference_time_ms:.2f} ms",
            "处理速度": f"{self.fps:.1f} FPS",
            "队列长度": str(self.queue_size),
            "线程数": str(self.thread_count)
        }


class PerformanceMonitor:
    """
    性能监控器
    
    提供实时性能监控功能：
    - CPU利用率
    - 内存占用
    - 推理耗时统计
    - FPS计算
    - 历史数据记录
    """
    
    def __init__(self, sample_interval: float = 1.0, max_history: int = 3600):
        """
        初始化性能监控器
        
        Args:
            sample_interval: 采样间隔（秒）
            max_history: 最大历史记录数
        """
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread = None
        self._sample_interval = sample_interval
        self._max_history = max_history
        
        # 当前指标
        self._current_metrics = PerformanceMetrics()
        
        # 历史数据
        self._history: List[PerformanceMetrics] = []
        
        # 推理时间历史（用于计算统计）
        self._inference_times: List[float] = []
        self._max_inference_samples = 100
        
        # 回调函数
        self._callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        # 统计信息
        self._stats = {
            "total_inferences": 0,
            "total_inference_time": 0,
            "min_inference_time": float('inf'),
            "max_inference_time": 0,
            "avg_inference_time": 0,
            "start_time": None,
            "last_inference_time": None
        }
        
        # 系统信息
        self._cpu_count = psutil.cpu_count(logical=True)
        self._physical_cpu_count = psutil.cpu_count(logical=False)
        self._memory_total = psutil.virtual_memory().total
        
        logger.info(f"性能监控器初始化完成: CPU核心数={self._cpu_count}, 采样间隔={sample_interval}s")
    
    def start(self):
        """开始监控"""
        if self._running:
            logger.warning("性能监控已在运行")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self._monitor_thread.start()
        self._stats["start_time"] = time.time()
        logger.info("性能监控已启动")
    
    def stop(self):
        """停止监控"""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        process = psutil.Process()
        
        while self._running:
            try:
                # 获取系统指标
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_info = psutil.virtual_memory()
                memory_percent = memory_info.percent
                memory_used = memory_info.used / (1024 * 1024)  # MB
                memory_available = memory_info.available / (1024 * 1024)  # MB
                
                # 获取进程指标
                process_memory = process.memory_info().rss / (1024 * 1024)  # MB
                thread_count = process.num_threads()
                
                # 更新当前指标
                metrics = PerformanceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_used_mb=memory_used,
                    memory_available_mb=memory_available,
                    thread_count=thread_count
                )
                
                with self._lock:
                    self._current_metrics = metrics
                    
                    # 添加到历史
                    self._history.append(metrics)
                    if len(self._history) > self._max_history:
                        self._history.pop(0)
                
                # 触发回调
                self._trigger_callbacks(metrics)
                
                # 等待下一次采样
                time.sleep(self._sample_interval)
                
            except Exception as e:
                logger.error(f"性能监控错误: {e}")
                time.sleep(1.0)
    
    def record_inference(self, inference_time_ms: float):
        """
        记录推理时间
        
        Args:
            inference_time_ms: 推理耗时（毫秒）
        """
        with self._lock:
            # 更新推理时间
            self._current_metrics.inference_time_ms = inference_time_ms
            self._inference_times.append(inference_time_ms)
            
            # 保持样本数量限制
            if len(self._inference_times) > self._max_inference_samples:
                self._inference_times.pop(0)
            
            # 更新统计
            self._stats["total_inferences"] += 1
            self._stats["total_inference_time"] += inference_time_ms
            self._stats["min_inference_time"] = min(
                self._stats["min_inference_time"], inference_time_ms
            )
            self._stats["max_inference_time"] = max(
                self._stats["max_inference_time"], inference_time_ms
            )
            self._stats["avg_inference_time"] = (
                self._stats["total_inference_time"] / self._stats["total_inferences"]
            )
            self._stats["last_inference_time"] = inference_time_ms
            
            # 计算FPS
            if self._inference_times:
                avg_time = statistics.mean(self._inference_times)
                self._current_metrics.fps = 1000 / avg_time if avg_time > 0 else 0
    
    def record_queue_size(self, size: int):
        """记录队列大小"""
        with self._lock:
            self._current_metrics.queue_size = size
    
    def _trigger_callbacks(self, metrics: PerformanceMetrics):
        """触发回调函数"""
        for callback in self._callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"性能回调函数错误: {e}")
    
    def register_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """
        注册性能回调函数
        
        Args:
            callback: 回调函数，接收PerformanceMetrics参数
        """
        self._callbacks.append(callback)
        logger.debug(f"已注册性能回调函数")
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标"""
        with self._lock:
            return self._current_metrics
    
    def get_metrics_history(self, 
                           last_n_seconds: float = None,
                           max_samples: int = None) -> List[PerformanceMetrics]:
        """
        获取性能指标历史
        
        Args:
            last_n_seconds: 获取最近N秒的数据
            max_samples: 最大样本数
            
        Returns:
            性能指标列表
        """
        with self._lock:
            history = self._history.copy()
        
        if last_n_seconds:
            cutoff_time = time.time() - last_n_seconds
            history = [m for m in history if m.timestamp >= cutoff_time]
        
        if max_samples and len(history) > max_samples:
            history = history[-max_samples:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats["avg_fps"] = (
                1000 / stats["avg_inference_time"] 
                if stats["avg_inference_time"] > 0 else 0
            )
            
            # 计算推理时间百分位数
            if self._inference_times:
                sorted_times = sorted(self._inference_times)
                n = len(sorted_times)
                stats["p50_inference_time"] = sorted_times[n // 2]
                stats["p95_inference_time"] = sorted_times[int(n * 0.95)] if n >= 20 else sorted_times[-1]
                stats["p99_inference_time"] = sorted_times[int(n * 0.99)] if n >= 100 else sorted_times[-1]
            
            # 添加系统信息
            stats["cpu_count"] = self._cpu_count
            stats["physical_cpu_count"] = self._physical_cpu_count
            stats["memory_total_mb"] = self._memory_total / (1024 * 1024)
            
            # 运行时间
            if stats["start_time"]:
                stats["uptime_seconds"] = time.time() - stats["start_time"]
            
            return stats
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        metrics = self.get_current_metrics()
        stats = self.get_statistics()
        
        return {
            "实时指标": metrics.to_display_dict(),
            "统计信息": {
                "总推理次数": stats["total_inferences"],
                "平均推理时间": f"{stats['avg_inference_time']:.2f} ms",
                "最快推理时间": f"{stats['min_inference_time']:.2f} ms",
                "最慢推理时间": f"{stats['max_inference_time']:.2f} ms",
                "平均FPS": f"{stats['avg_fps']:.1f}",
                "P95推理时间": f"{stats.get('p95_inference_time', 0):.2f} ms"
            },
            "系统资源": {
                "CPU核心数": stats["cpu_count"],
                "总内存": f"{stats['memory_total_mb']:.1f} MB",
                "运行时间": f"{stats.get('uptime_seconds', 0):.1f} 秒"
            }
        }
    
    def export_history(self, filepath: str, 
                      format: str = "json") -> bool:
        """
        导出历史数据
        
        Args:
            filepath: 导出文件路径
            format: 格式（json, csv）
            
        Returns:
            是否导出成功
        """
        history = self.get_metrics_history()
        
        try:
            if format == "json":
                import json
                data = [m.to_dict() for m in history]
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format == "csv":
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        "timestamp", "cpu_percent", "memory_percent",
                        "memory_used_mb", "inference_time_ms", "fps"
                    ])
                    writer.writeheader()
                    for m in history:
                        writer.writerow(m.to_dict())
            else:
                logger.error(f"不支持的格式: {format}")
                return False
            
            logger.info(f"历史数据已导出: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False
    
    def reset(self):
        """重置监控数据"""
        with self._lock:
            self._history.clear()
            self._inference_times.clear()
            self._stats = {
                "total_inferences": 0,
                "total_inference_time": 0,
                "min_inference_time": float('inf'),
                "max_inference_time": 0,
                "avg_inference_time": 0,
                "start_time": time.time(),
                "last_inference_time": None
            }
        logger.info("性能监控数据已重置")
    
    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()
        
        print("\n" + "=" * 50)
        print("  性能监控摘要")
        print("=" * 50)
        
        print("\n实时指标:")
        for key, value in summary["实时指标"].items():
            print(f"  {key}: {value}")
        
        print("\n统计信息:")
        for key, value in summary["统计信息"].items():
            print(f"  {key}: {value}")
        
        print("\n系统资源:")
        for key, value in summary["系统资源"].items():
            print(f"  {key}: {value}")
        
        print("=" * 50 + "\n")


class PerformanceWidget:
    """
    性能监控窗口部件
    
    提供简单的性能显示界面
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        """
        初始化性能窗口部件
        
        Args:
            monitor: 性能监控器实例
        """
        self._monitor = monitor
        self._visible = False
    
    def show(self):
        """显示性能窗口"""
        self._visible = True
        print("\n[性能监控 - 开启]")
        self._monitor.register_callback(self._update_display)
    
    def hide(self):
        """隐藏性能窗口"""
        self._visible = False
    
    def _update_display(self, metrics: PerformanceMetrics):
        """更新显示"""
        if not self._visible:
            return
        
        # 清屏并重新打印
        print(f"\rCPU: {metrics.cpu_percent:5.1f}% | "
              f"内存: {metrics.memory_used_mb:6.1f} MB | "
              f"推理: {metrics.inference_time_ms:6.2f} ms | "
              f"FPS: {metrics.fps:5.1f}     ", end="", flush=True)
    
    def get_metrics(self) -> PerformanceMetrics:
        """获取当前指标"""
        return self._monitor.get_current_metrics()


# 全局性能监控器实例
_monitor_instance = None


def get_performance_monitor(sample_interval: float = 1.0) -> PerformanceMonitor:
    """
    获取全局性能监控器实例
    
    Args:
        sample_interval: 采样间隔
        
    Returns:
        PerformanceMonitor实例
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor(sample_interval)
        _monitor_instance.start()
    
    return _monitor_instance


if __name__ == "__main__":
    print("测试性能监控...")
    
    # 创建监控器
    monitor = PerformanceMonitor(sample_interval=0.5)
    monitor.start()
    
    # 创建窗口部件
    widget = PerformanceWidget(monitor)
    widget.show()
    
    # 模拟一些推理
    print("\n开始模拟推理...")
    for i in range(10):
        time.sleep(0.3)
        inference_time = 20 + np.random.randn() * 5
        monitor.record_inference(inference_time)
        print(f"推理 {i+1}/10 完成，耗时: {inference_time:.2f}ms")
    
    # 打印摘要
    monitor.print_summary()
    
    # 停止监控
    monitor.stop()
    
    print("测试完成!")
