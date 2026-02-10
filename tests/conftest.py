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

# 检测是否运行在GUI环境
import os
RUNNING_IN_CI = os.environ.get('CI', 'false').lower() == 'true'
RUNNING_IN_HEADLESS = os.environ.get('DISPLAY', '') == '' and sys.platform != 'win32'
HAS_QT = False

try:
    # 尝试导入Qt，但不初始化QApplication
    from PyQt5.QtCore import QT_VERSION_STR
    HAS_QT = True
except ImportError:
    pass

# 定义测试标记
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "gui: 标记需要GUI的测试")
    config.addinivalue_line("markers", "slow: 标记运行缓慢的测试")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "unit: 标记单元测试")


def pytest_collection_modifyitems(config, items):
    """修改测试项，跳过不需要的测试"""
    skip_gui = pytest.mark.skip(reason="跳过GUI测试（使用 --gui 启用）")
    skip_slow = pytest.mark.skip(reason="跳过慢速测试（使用 --runslow 启用）")
    
    for item in items:
        # 如果没有指定--gui选项，跳过GUI测试
        if "gui" in item.keywords and not config.getoption("--gui"):
            item.add_marker(skip_gui)
        
        # 如果没有指定--runslow选项，跳过慢速测试
        if "slow" in item.keywords and not config.getoption("--runslow"):
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--gui", action="store_true", default=False, help="运行GUI测试"
    )
    parser.addoption(
        "--runslow", action="store_true", default=False, help="运行慢速测试"
    )


# 安全导入ImageData，避免GUI初始化
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
