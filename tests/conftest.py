#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件

用于配置pytest测试框架，包括环境初始化、夹具(fixtures)定义等。
"""

import os
import sys

import numpy as np
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.image_data import ImageData


@pytest.fixture
def sample_image():
    """创建一个示例图像数据，用于测试"""
    # 创建一个300x300的随机彩色图像
    image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    return ImageData(data=image)


@pytest.fixture
def sample_gray_image():
    """创建一个示例灰度图像数据，用于测试"""
    # 创建一个300x300的随机灰度图像
    image = np.random.randint(0, 255, (300, 300), dtype=np.uint8)
    return ImageData(data=image)


@pytest.fixture
def invalid_image():
    """创建一个无效图像数据，用于测试异常处理"""
    return ImageData(data=None)


@pytest.fixture
def tool_registry():
    """获取工具注册表，用于测试工具创建"""
    import tools  # 导入所有工具模块
    from core.tool_base import ToolRegistry

    return ToolRegistry


@pytest.fixture
def sample_procedure():
    """创建一个示例流程，用于测试流程功能"""
    from core.procedure import Procedure

    return Procedure("测试流程")


@pytest.fixture
def sample_solution():
    """创建一个示例方案，用于测试方案功能"""
    from core.solution import Solution

    return Solution("测试方案")
