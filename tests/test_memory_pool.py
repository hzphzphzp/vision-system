# -*- coding: utf-8 -*-
"""
Memory pool tests for ImageBufferPool

Author: AI Agent
Date: 2026-02-03
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_pool import ImageBufferPool


def test_buffer_pool_creation():
    """测试内存池创建"""
    pool = ImageBufferPool(max_size=5, buffer_shape=(480, 640, 3))
    assert pool is not None
    assert pool.available_count() == 5


def test_buffer_acquire_release():
    """测试内存获取和释放"""
    pool = ImageBufferPool(max_size=3, buffer_shape=(480, 640, 3))
    
    # 获取缓冲区
    buf1 = pool.acquire()
    assert buf1 is not None
    assert pool.available_count() == 2
    
    # 释放缓冲区
    pool.release(buf1)
    assert pool.available_count() == 3


def test_buffer_exhaustion():
    """测试内存耗尽时的行为"""
    pool = ImageBufferPool(max_size=2, buffer_shape=(100, 100, 3))
    
    buf1 = pool.acquire()
    buf2 = pool.acquire()
    
    # 第三个应该阻塞或返回None
    buf3 = pool.acquire(timeout=0.1)
    assert buf3 is None  # 或者阻塞直到有可用
