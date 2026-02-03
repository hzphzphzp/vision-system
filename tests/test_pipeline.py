# -*- coding: utf-8 -*-
"""
Pipeline tests for DeterministicPipeline

Author: AI Agent
Date: 2026-02-03
"""

import pytest
import time
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pipeline import DeterministicPipeline, PipelineStage


def test_pipeline_creation():
    """测试流水线创建"""
    pipeline = DeterministicPipeline()
    assert pipeline is not None
    assert not pipeline.is_running()


def test_pipeline_add_stage():
    """测试添加处理阶段"""
    pipeline = DeterministicPipeline()
    
    def dummy_process(frame):
        return frame
    
    stage = PipelineStage("test", dummy_process, output_queue_size=3)
    pipeline.add_stage(stage)
    
    assert len(pipeline.stages) == 1


def test_pipeline_deterministic():
    """测试确定性：多帧处理结果顺序一致"""
    pipeline = DeterministicPipeline()
    results = []
    
    def collect_result(frame, result):
        results.append((frame.frame_id, result))
    
    # 添加简单处理阶段
    def process_frame(frame):
        return frame.data.sum()
    
    stage = PipelineStage("process", process_frame, 
                         output_callback=collect_result)
    pipeline.add_stage(stage)
    
    # 模拟输入3帧
    for i in range(3):
        from data.image_data import ImageData
        data = np.ones((100, 100, 3), dtype=np.uint8) * i
        frame = ImageData(data=data)
        pipeline.input_queue.put(frame)
    
    pipeline.start()
    time.sleep(0.5)  # 等待处理
    pipeline.stop()
    
    # 验证结果顺序
    assert len(results) == 3
    for i, (frame_id, result) in enumerate(results):
        assert frame_id == i  # 顺序必须一致
