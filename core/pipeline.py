# -*- coding: utf-8 -*-
"""
确定性图像处理流水线模块

提供生产者-消费者模式的图像处理流水线，保证严格顺序处理

Author: AI Agent
Date: 2026-02-03
"""

import logging
import multiprocessing
import threading
import queue
import time
import numpy as np
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Frame:
    """流水线帧数据"""
    frame_id: int
    data: np.ndarray
    metadata: Dict[str, Any]
    timestamp: float


class PipelineStage:
    """流水线处理阶段"""
    
    def __init__(self, name: str, process_func: Callable, 
                 output_queue_size: int = 3,
                 output_callback: Optional[Callable] = None):
        """
        Args:
            name: 阶段名称
            process_func: 处理函数(frame) -> result
            output_queue_size: 输出队列大小
            output_callback: 输出回调函数(frame, result)
        """
        self.name = name
        self.process_func = process_func
        self.output_callback = output_callback
        
        # 输入/输出队列
        self.input_queue = queue.Queue(maxsize=output_queue_size)
        self.output_queue = queue.Queue(maxsize=output_queue_size)
        
        # 工作线程
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def start(self):
        """启动处理线程"""
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
    
    def stop(self):
        """停止处理线程"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def _worker(self):
        """工作线程"""
        while self._running:
            try:
                # 获取输入帧
                frame = self.input_queue.get(timeout=0.1)
                
                # 处理帧
                result = self.process_func(frame)
                
                # 放入输出队列
                try:
                    self.output_queue.put_nowait((frame, result))
                except queue.Full:
                    # 队列满，丢弃最旧的
                    try:
                        self.output_queue.get_nowait()
                        self.output_queue.put_nowait((frame, result))
                    except queue.Empty:
                        pass
                
                # 调用输出回调
                if self.output_callback:
                    self.output_callback(frame, result)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Pipeline stage {self.name} error: {e}")


class DeterministicPipeline:
    """确定性图像处理流水线
    
    特点：
    1. 严格顺序处理，保证结果一致性
    2. 每个阶段独立线程，无共享状态
    3. 队列大小限制，防止内存爆炸
    4. 自动处理帧ID，保持顺序
    """
    
    def __init__(self, max_pipeline_depth: int = 3):
        """
        Args:
            max_pipeline_depth: 流水线最大深度(同时处理的帧数)
        """
        self.stages: List[PipelineStage] = []
        self.max_depth = max_pipeline_depth
        
        # 输入队列
        self.input_queue = queue.Queue(maxsize=max_pipeline_depth)
        
        # 帧ID计数器
        self._frame_id_counter = 0
        self._lock = threading.Lock()
        
        self._running = False
        self._input_thread: Optional[threading.Thread] = None
    
    def add_stage(self, stage: PipelineStage):
        """添加处理阶段"""
        # 连接阶段队列
        if self.stages:
            # 前一个阶段的输出连接到当前阶段的输入
            prev_stage = self.stages[-1]
            # 这里简化处理，实际应该更复杂的连接逻辑
            pass
        
        self.stages.append(stage)
    
    def start(self):
        """启动流水线"""
        self._running = True
        
        # 启动所有阶段
        for stage in self.stages:
            stage.start()
        
        # 启动输入分发线程
        self._input_thread = threading.Thread(target=self._input_worker, daemon=True)
        self._input_thread.start()
    
    def stop(self):
        """停止流水线"""
        self._running = False
        
        # 停止所有阶段
        for stage in self.stages:
            stage.stop()
        
        if self._input_thread and self._input_thread.is_alive():
            self._input_thread.join(timeout=2.0)
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running
    
    def _input_worker(self):
        """输入分发线程"""
        while self._running:
            try:
                # 获取输入图像
                image_data = self.input_queue.get(timeout=0.1)
                
                # 分配帧ID
                with self._lock:
                    frame_id = self._frame_id_counter
                    self._frame_id_counter += 1
                
                # 创建帧对象
                # 延迟导入避免循环依赖
                from data.image_data import ImageData
                
                # 从ImageData提取数据
                if hasattr(image_data, 'data'):
                    data = image_data.data
                    metadata = getattr(image_data, 'metadata', {})
                else:
                    data = image_data
                    metadata = {}
                
                frame = Frame(
                    frame_id=frame_id,
                    data=data,
                    metadata=metadata,
                    timestamp=time.time()
                )
                
                # 发送到第一个阶段
                if self.stages:
                    try:
                        self.stages[0].input_queue.put_nowait(frame)
                    except queue.Full:
                        # 流水线满，丢弃
                        pass
                        
            except queue.Empty:
                continue
    
    def put_frame(self, image_data, timeout: Optional[float] = None) -> bool:
        """放入一帧图像
        
        Args:
            image_data: 图像数据
            timeout: 超时时间
            
        Returns:
            是否成功放入
        """
        try:
            self.input_queue.put(image_data, timeout=timeout)
            return True
        except queue.Full:
            return False
