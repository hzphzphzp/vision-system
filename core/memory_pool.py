# -*- coding: utf-8 -*-
"""
图像缓冲区内存池模块

提供预分配的图像内存缓冲区管理，避免频繁的malloc/free操作

Author: AI Agent
Date: 2026-02-03
"""

import numpy as np
import threading
import queue
from typing import Optional, Tuple, Set


class ImageBufferPool:
    """图像缓冲区内存池
    
    预分配固定大小的图像内存，避免频繁的malloc/free
    线程安全
    """
    
    def __init__(self, max_size: int = 10, buffer_shape: Tuple = (480, 640, 3), 
                 dtype=np.uint8):
        """
        Args:
            max_size: 缓冲区最大数量
            buffer_shape: 图像形状 (H, W, C)
            dtype: 数据类型
        """
        self._max_size = max_size
        self._buffer_shape = buffer_shape
        self._dtype = dtype
        
        # 预分配缓冲区
        self._available = queue.Queue(maxsize=max_size)
        self._in_use: Set[int] = set()  # 使用id()来跟踪
        self._lock = threading.Lock()
        self._buffer_map: dict = {}  # id -> buffer映射
        
        # 预分配内存
        for _ in range(max_size):
            buffer = np.zeros(buffer_shape, dtype=dtype)
            self._available.put(buffer)
            self._buffer_map[id(buffer)] = buffer
    
    def acquire(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """获取一个缓冲区
        
        Args:
            timeout: 等待超时时间(秒)，None表示无限等待
            
        Returns:
            可用的缓冲区，或None(如果超时)
        """
        try:
            buffer = self._available.get(timeout=timeout)
            with self._lock:
                self._in_use.add(id(buffer))
            return buffer
        except queue.Empty:
            return None
    
    def release(self, buffer: Optional[np.ndarray]) -> None:
        """释放缓冲区回内存池
        
        Args:
            buffer: 要释放的缓冲区
        """
        if buffer is None:
            return
            
        buffer_id = id(buffer)
        with self._lock:
            if buffer_id in self._in_use:
                self._in_use.discard(buffer_id)
                # 重置缓冲区内容(可选)
                buffer.fill(0)
                try:
                    self._available.put_nowait(buffer)
                except queue.Full:
                    pass  # 队列已满，丢弃
    
    def available_count(self) -> int:
        """获取可用缓冲区数量"""
        return self._available.qsize()
    
    def in_use_count(self) -> int:
        """获取正在使用的缓冲区数量"""
        with self._lock:
            return len(self._in_use)
    
    def resize(self, new_shape: Tuple) -> None:
        """调整缓冲区大小(释放所有并重新分配)"""
        # 清空现有缓冲区
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except queue.Empty:
                break
        
        self._buffer_shape = new_shape
        
        # 重新分配
        for _ in range(self._max_size):
            buffer = np.zeros(new_shape, dtype=self._dtype)
            self._available.put(buffer)


class PooledImageData:
    """使用内存池的图像数据类"""
    
    def __init__(self, pool: ImageBufferPool, data: Optional[np.ndarray] = None):
        self._pool = pool
        self._buffer = pool.acquire()
        
        if data is not None and self._buffer is not None:
            # 复制数据到缓冲区
            np.copyto(self._buffer, data)
    
    def __del__(self):
        """析构时自动释放回内存池"""
        if hasattr(self, '_pool') and self._pool is not None and self._buffer is not None:
            self._pool.release(self._buffer)
    
    @property
    def data(self) -> Optional[np.ndarray]:
        return self._buffer
