#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision System 测试套件

包含所有模块的单元测试和集成测试。

Usage:
    # 运行所有测试
    pytest tests/ -v
    
    # 运行特定测试文件
    pytest tests/test_core.py -v
    pytest tests/test_tools.py -v
    pytest tests/test_zoomable_image.py -v
    
    # 运行特定测试
    pytest tests/test_tool_registry.py::test_tool_categories -v
    
    # 生成覆盖率报告
    pytest tests/ --cov=core --cov=data --cov=tools --cov-report=html
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
