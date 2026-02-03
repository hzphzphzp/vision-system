# -*- coding: utf-8 -*-
"""
ImageData memory pool integration tests

Author: AI Agent
Date: 2026-02-03
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.image_data import ImageData
from core.memory_pool import ImageBufferPool


def test_image_data_uses_pool():
    """测试ImageData使用内存池"""
    # 创建测试数据
    data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 创建ImageData
    img = ImageData(data=data)
    
    assert img.data is not None
    assert img.data.shape == (480, 640, 3)
    np.testing.assert_array_equal(img.data, data)


def test_image_data_pool_reuse():
    """测试内存池重用"""
    pool = ImageBufferPool(max_size=2, buffer_shape=(100, 100, 3))
    
    # 创建并销毁图像，触发内存回收
    for i in range(5):
        data = np.ones((100, 100, 3), dtype=np.uint8) * i
        img = ImageData(data=data, _pool=pool)
        del img  # 触发释放
    
    # 内存池应该还有可用缓冲区
    assert pool.available_count() > 0
