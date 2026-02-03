#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块包

包含各种功能模块。

注意：使用延迟导入以避免循环导入问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def __getattr__(name):
    """延迟导入子模块"""
    if name == "cpu_optimization":
        from . import cpu_optimization
        return cpu_optimization
    if name == "camera":
        from . import camera
        return camera
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# 重新导出常用模块（延迟）
def get_cpu_optimization():
    """获取CPU优化模块"""
    from . import cpu_optimization
    return cpu_optimization


def get_camera():
    """获取相机模块"""
    from . import camera
    return camera


__all__ = [
    'get_cpu_optimization',
    'get_camera',
    'cpu_optimization',
    'camera',
]
