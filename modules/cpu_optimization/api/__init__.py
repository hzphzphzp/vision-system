#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU检测器API接口模块

提供完整的API接口，支持模型加载、参数配置、推理执行、结果返回等功能

Author: Vision System Team
Date: 2026-01-26
"""

from .cpu_detector import (
    APIConfig,
    BackendType,
    CPUDetectorAPI,
    DetectionResult,
    DetectorState,
    create_detector_api,
)

__all__ = [
    "CPUDetectorAPI",
    "APIConfig",
    "DetectionResult",
    "BackendType",
    "DetectorState",
    "create_detector_api",
]
