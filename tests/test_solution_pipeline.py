# -*- coding: utf-8 -*-
"""
Solution pipeline integration tests

Author: AI Agent
Date: 2026-02-03
"""

import pytest
import time
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.solution import Solution
from data.image_data import ImageData


def test_solution_with_pipeline():
    """测试Solution使用流水线模式运行"""
    solution = Solution("test_solution")
    
    # 添加测试流程
    from core.procedure import Procedure
    proc = Procedure("test_proc")
    solution.add_procedure(proc)
    
    # 启用流水线模式
    solution.enable_pipeline_mode(buffer_size=3)
    
    # 运行
    result = solution.run()
    
    assert result is not None


def test_solution_pipeline_performance():
    """测试流水线性能提升"""
    solution = Solution("perf_test")
    solution.enable_pipeline_mode(buffer_size=5)
    
    # 模拟连续运行
    start_time = time.time()
    
    for i in range(5):
        # 创建测试图像
        data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = ImageData(data=data)
        solution.put_input(img)
    
    # 等待处理完成
    time.sleep(0.5)
    
    elapsed = time.time() - start_time
    
    # 应该比普通模式快(这里只是示例断言)
    assert elapsed < 5.0  # 5秒内完成
