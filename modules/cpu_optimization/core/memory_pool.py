#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存池管理

提供高效的内存池管理，减少内存分配开销，优化内存访问模式

Author: Vision System Team
Date: 2026-01-26
"""

import logging
import os
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

import numpy as np

logger = logging.getLogger("CPUOptimization.MemoryPool")

T = TypeVar("T")


@dataclass
class MemoryBlock:
    """内存块"""

    data: np.ndarray
    size: int
    is_allocated: bool = False
    last_access: float = 0.0
    access_count: int = 0


class MemoryPool:
    """
    通用内存池

    预先分配固定大小的内存块，减少运行时内存分配开销
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
        self._pools: Dict[str, List[np.ndarray]] = {}
        self._pool_sizes: Dict[str, int] = {}
        self._max_pool_size: int = 1024 * 1024 * 1024  # 最大1GB
        self._total_allocated: int = 0
        self._hit_count: int = 0
        self._miss_count: int = 0

        logger.info("内存池初始化完成")

    def create_pool(
        self, name: str, block_size: int, num_blocks: int, dtype=np.float32
    ):
        """
        创建内存池

        Args:
            name: 池名称
            block_size: 每个块的大小（字节）
            num_blocks: 块数量
            dtype: 数据类型
        """
        with self._lock:
            if name in self._pools:
                logger.warning(f"内存池 {name} 已存在，将被替换")

            total_size = block_size * num_blocks
            if self._total_allocated + total_size > self._max_pool_size:
                logger.warning(f"内存池 {name} 超出最大内存限制，已调整块数量")
                num_blocks = max(
                    1,
                    (self._max_pool_size - self._total_allocated)
                    // block_size,
                )

            pool = []
            for _ in range(num_blocks):
                try:
                    block = np.zeros(block_size, dtype=dtype)
                    pool.append(block)
                except MemoryError:
                    logger.error(f"无法分配内存块: {block_size} bytes")
                    break

            self._pools[name] = pool
            self._pool_sizes[name] = block_size * len(pool)
            self._total_allocated += self._pool_sizes[name]

            logger.info(
                f"内存池创建成功: {name}, 块大小={block_size}, 块数量={len(pool)}, 总大小={self._pool_sizes[name]/1024/1024:.2f}MB"
            )

    def get(self, name: str) -> Optional[np.ndarray]:
        """
        从池中获取内存块

        Args:
            name: 池名称

        Returns:
            内存块，如果池为空则返回None
        """
        with self._lock:
            if name not in self._pools or not self._pools[name]:
                self._miss_count += 1
                return None

            block = self._pools[name].pop()
            self._hit_count += 1
            return block

    def release(self, name: str, block: np.ndarray):
        """
        将内存块释放回池

        Args:
            name: 池名称
            block: 要释放的内存块
        """
        with self._lock:
            if name not in self._pools:
                logger.warning(f"未找到内存池: {name}")
                return

            # 检查是否需要清零
            if block.dtype == np.float32:
                block.fill(0)
            elif block.dtype == np.uint8:
                block.fill(0)

            self._pools[name].append(block)

    @contextmanager
    def allocated(self, name: str, shape: tuple, dtype=np.float32):
        """
        上下文管理器方式的内存分配

        Args:
            name: 池名称
            shape: 数组形状
            dtype: 数据类型

        Usage:
            with memory_pool.allocated("temp", (640, 480)) as arr:
                # 使用arr进行计算
                pass
            # 自动释放回池
        """
        total_size = int(np.prod(shape))
        block_size = total_size * np.dtype(dtype).itemsize

        # 尝试从池获取，或创建新块
        block = self.get(name)
        if block is None or block.size < total_size:
            if block is not None:
                self.release(name, block)
            try:
                block = np.zeros(total_size, dtype=dtype)
            except MemoryError:
                logger.error(f"无法分配内存: {total_size} elements")
                raise

        # 重塑为所需形状
        original_shape = block.shape
        try:
            block = block.reshape(shape)
            yield block
        finally:
            # 恢复原始形状并释放
            block = block.reshape(original_shape)
            self.release(name, block)

    def get_stats(self) -> Dict[str, Any]:
        """获取内存池统计信息"""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (
                (self._hit_count / total_requests * 100)
                if total_requests > 0
                else 0
            )

            return {
                "total_allocated_mb": self._total_allocated / (1024 * 1024),
                "max_size_mb": self._max_pool_size / (1024 * 1024),
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": f"{hit_rate:.2f}%",
                "pools": {
                    name: {
                        "blocks": len(blocks),
                        "size_mb": self._pool_sizes[name] / (1024 * 1024),
                    }
                    for name, blocks in self._pools.items()
                },
            }

    def clear_pool(self, name: str):
        """清空指定内存池"""
        with self._lock:
            if name in self._pools:
                self._pools[name].clear()
                self._total_allocated -= self._pool_sizes[name]
                del self._pool_sizes[name]
                logger.info(f"内存池已清空: {name}")

    def clear_all(self):
        """清空所有内存池"""
        with self._lock:
            self._pools.clear()
            self._pool_sizes.clear()
            self._total_allocated = 0
            logger.info("所有内存池已清空")

    def set_max_size(self, max_size_mb: float):
        """设置最大内存池大小"""
        self._max_pool_size = int(max_size_mb * 1024 * 1024)
        logger.info(f"最大内存池大小已设置为: {max_size_mb}MB")


class TensorPool:
    """
    张量池

    专门用于管理深度学习张量的内存池
    """

    def __init__(self, max_tensors: int = 100):
        self._lock = threading.Lock()
        self._tensor_pools: Dict[tuple, List[np.ndarray]] = {}
        self._tensor_shapes: Dict[str, tuple] = {}
        self._max_tensors = max_tensors
        self._lru_order: List[str] = []

    def get_tensor(
        self, shape: tuple, dtype=np.float32
    ) -> Optional[np.ndarray]:
        """
        获取张量

        Args:
            shape: 张量形状
            dtype: 数据类型

        Returns:
            张量或None
        """
        with self._lock:
            pool_key = (shape, dtype)

            if pool_key in self._tensor_pools and self._tensor_pools[pool_key]:
                tensor = self._tensor_pools[pool_key].pop()
                self._update_lru(tensor)
                return tensor

            return None

    def release_tensor(self, tensor: np.ndarray):
        """
        释放张量

        Args:
            tensor: 要释放的张量
        """
        if tensor is None:
            return

        with self._lock:
            # 查找张量的原始形状
            tensor_id = id(tensor)
            shape = None
            dtype = tensor.dtype

            for pool_key, tensors in self._tensor_pools.items():
                for t in tensors:
                    if id(t) == tensor_id:
                        shape = pool_key[0]
                        break

            if shape is None:
                shape = tensor.shape

            pool_key = (shape, dtype)

            # 检查是否超出限制
            current_count = sum(
                len(tensors) for pk, tensors in self._tensor_pools.items()
            )
            if current_count >= self._max_tensors:
                # 移除最少使用的张量
                self._evict_lru()

            if pool_key not in self._tensor_pools:
                self._tensor_pools[pool_key] = []

            # 清零并添加回池
            if dtype == np.float32:
                tensor.fill(0)
            elif dtype == np.uint8:
                tensor.fill(0)

            self._tensor_pools[pool_key].append(tensor)
            self._lru_order.append(id(tensor))

    def _update_lru(self, tensor: np.ndarray):
        """更新LRU顺序"""
        tensor_id = id(tensor)
        if tensor_id in self._lru_order:
            self._lru_order.remove(tensor_id)
        self._lru_order.append(tensor_id)

    def _evict_lru(self):
        """驱逐最少使用的张量"""
        while (
            self._lru_order and self._get_total_tensors() >= self._max_tensors
        ):
            oldest_id = self._lru_order.pop(0)
            for pool_key, tensors in list(self._tensor_pools.items()):
                for i, t in enumerate(tensors):
                    if id(t) == oldest_id:
                        tensors.pop(i)
                        if not tensors:
                            del self._tensor_pools[pool_key]
                        return

    def _get_total_tensors(self) -> int:
        """获取总张量数"""
        return sum(len(tensors) for tensors in self._tensor_pools.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_tensors": self._get_total_tensors(),
                "max_tensors": self._max_tensors,
                "pool_count": len(self._tensor_pools),
                "pools": {
                    str(k): len(v) for k, v in self._tensor_pools.items()
                },
            }

    def clear(self):
        """清空所有张量池"""
        with self._lock:
            self._tensor_pools.clear()
            self._lru_order.clear()


# 预定义的图像处理内存池
class ImageMemoryPool:
    """
    图像处理专用内存池

    针对图像处理场景优化，预分配常用大小的内存块
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
        self._general_pool = MemoryPool()
        self._tensor_pool = TensorPool(max_tensors=50)

        # 预定义图像尺寸池
        self._setup_image_pools()

    def _setup_image_pools(self):
        """设置图像处理内存池"""
        # 常用图像尺寸
        common_sizes = [
            (320, 240),  # QVGA
            (640, 480),  # VGA
            (1280, 720),  # HD
            (1920, 1080),  # Full HD
        ]

        for h, w in common_sizes:
            size = h * w * 4  # 4通道
            self._general_pool.create_pool(
                f"image_{h}x{w}", size, num_blocks=10, dtype=np.uint8
            )

    def get_image_buffer(
        self, width: int, height: int, channels: int = 4
    ) -> np.ndarray:
        """
        获取图像缓冲区

        Args:
            width: 宽度
            height: 高度
            channels: 通道数

        Returns:
            图像缓冲区
        """
        size = width * height * channels

        # 查找最匹配的标准尺寸池
        pool_name = None
        for h, w in [(240, 320), (480, 640), (720, 1280), (1080, 1920)]:
            if h >= height and w >= width:
                pool_name = f"image_{h}x{w}"
                break

        if pool_name:
            buffer = self._general_pool.get(pool_name)
            if buffer is not None:
                # 重塑为目标大小
                return buffer[: height * width * channels].reshape(
                    height, width, channels
                )

        # 如果没有匹配的池，创建新缓冲区
        return np.zeros((height, width, channels), dtype=np.uint8)

    def release_image_buffer(self, buffer: np.ndarray):
        """释放图像缓冲区"""
        h, w = buffer.shape[:2]
        pool_name = f"image_{h}x{w}"
        self._general_pool.release(pool_name, buffer)

    @contextmanager
    def image_context(self, width: int, height: int, channels: int = 4):
        """
        图像缓冲区上下文管理器

        Usage:
            with image_pool.image_context(640, 480, 3) as img:
                # 使用img进行处理
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        """
        buffer = self.get_image_buffer(width, height, channels)
        try:
            yield buffer
        finally:
            self.release_image_buffer(buffer)

    def get_tensor(
        self, batch: int, height: int, width: int, channels: int = 3
    ) -> np.ndarray:
        """获取批处理张量"""
        shape = (batch, channels, height, width)
        tensor = self._tensor_pool.get_tensor(shape, dtype=np.float32)

        if tensor is None:
            tensor = np.zeros(shape, dtype=np.float32)

        return tensor

    def release_tensor(self, tensor: np.ndarray):
        """释放张量"""
        self._tensor_pool.release_tensor(tensor)


# 获取全局内存池实例
def get_memory_pool() -> MemoryPool:
    """获取全局内存池实例"""
    return MemoryPool()


def get_image_pool() -> ImageMemoryPool:
    """获取图像处理内存池实例"""
    return ImageMemoryPool()


if __name__ == "__main__":
    print("测试内存池管理...")

    # 测试通用内存池
    pool = MemoryPool()
    pool.create_pool("test_pool", 1024, 100)

    # 测试获取和释放
    block = pool.get("test_pool")
    print(f"获取内存块: {block.shape}, 大小: {block.nbytes} bytes")
    pool.release("test_pool", block)

    # 测试统计信息
    stats = pool.get_stats()
    print(f"内存池统计: {stats}")

    # 测试图像内存池
    img_pool = ImageMemoryPool()
    with img_pool.image_context(640, 480, 3) as img:
        img[:] = 128  # 填充测试值
        print(f"图像缓冲区形状: {img.shape}, 数据类型: {img.dtype}")

    print("测试完成!")
