#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO26 CPU模型模块

提供YOLO26模型在CPU环境下的推理能力

Author: Vision System Team
Date: 2026-01-26
"""

from .yolo26_cpu import (
    YOLO26CPUDetector,
    create_detector
)

__all__ = [
    "YOLO26CPUDetector",
    "create_detector"
]
