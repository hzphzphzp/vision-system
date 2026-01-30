#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视觉工具包

包含各种视觉处理和检测工具。
"""

# 导入所有视觉工具
from .appearance_detection import AppearanceDetector, SurfaceDefectDetector
from .template_match import GrayMatch, ShapeMatch, LineFind, CircleFind
from .image_filter import BoxFilter, MeanFilter, GaussianFilter, MedianFilter, BilateralFilter, Morphology, ImageResize
from .image_stitching import ImageStitchingTool
from .ocr import OCRReader, OCREnglish
from .recognition import BarcodeReader, QRCodeReader
from .cpu_optimization import CPUDetector

__all__ = [
    'AppearanceDetector',
    'SurfaceDefectDetector',
    'GrayMatch',
    'ShapeMatch',
    'LineFind',
    'CircleFind',
    'BoxFilter',
    'MeanFilter',
    'GaussianFilter',
    'MedianFilter',
    'BilateralFilter',
    'Morphology',
    'ImageResize',
    'ImageStitchingTool',
    'OCRReader',
    'OCREnglish',
    'BarcodeReader',
    'QRCodeReader',
    'CPUDetector'
]
