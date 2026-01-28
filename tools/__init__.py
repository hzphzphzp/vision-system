#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块初始化

导出所有工具类。

Author: Vision System Team
Date: 2025-01-04
"""

# 导入所有工具模块
from tools.image_source import ImageSource, CameraSource
from tools.image_filter import (
    BoxFilter,
    MeanFilter,
    GaussianFilter,
    MedianFilter,
    BilateralFilter,
    Morphology,
    ImageResize
)
from tools.template_match import (
    GrayMatch,
    ShapeMatch,
    LineFind,
    CircleFind
)
from tools.recognition import (
    BarcodeReader,
    QRCodeReader,
    CodeReader
)
from tools.ocr import (
    OCRReader,
    OCREnglish
)
from tools.analysis import (
    BlobFind,
    PixelCount,
    Histogram
)
from tools.template_match import (
    GrayMatch,
    ShapeMatch,
    LineFind,
    CircleFind
)
from tools.recognition import (
    BarcodeReader,
    QRCodeReader,
    CodeReader
)
from tools.ocr import (
    OCRReader,
    OCREnglish
)
from tools.analysis import (
    BlobFind,
    PixelCount,
    Histogram
)
# 注释掉原版本通信工具导入
# from tools.communication import (
#     SendData,
#     ReceiveData
# )

# 导入增强版本的通信工具
try:
    from tools.enhanced_communication import EnhancedSendData, EnhancedReceiveData
    print('[INFO] 增强通信工具导入成功')
except ImportError as e:
    EnhancedSendData = None
    EnhancedReceiveData = None
    print(f'[ERROR] 增强通信工具导入失败: {e}')

# 导入CPU优化工具
try:
    from tools.cpu_optimization import (
        CPUDetector
    )
    print('[INFO] YOLO26-CPU工具导入成功')
except ImportError as e:
    CPUDetector = None
    print(f'[ERROR] YOLO26-CPU工具导入失败: {e}')

# 导入图像拼接工具
try:
    from tools.image_stitching import ImageStitchingTool
    print('[INFO] 图像拼接工具导入成功')
except ImportError as e:
    ImageStitchingTool = None
    print(f'[ERROR] 图像拼接工具导入失败: {e}')

# 导入相机参数设置工具
try:
    from tools.camera_parameter_setting import CameraParameterSettingTool
    print('[INFO] 相机参数设置工具导入成功')
except ImportError as e:
    CameraParameterSettingTool = None
    print(f'[ERROR] 相机参数设置工具导入失败: {e}')

__all__ = [
    # 图像源
    'ImageSource',
    'CameraSource',
    
    # 图像滤波
    'BoxFilter',
    'MeanFilter',
    'GaussianFilter',
    'MedianFilter',
    'BilateralFilter',
    'Morphology',
    'ImageResize',
    
    # 模板匹配
    'GrayMatch',
    'ShapeMatch',
    'LineFind',
    'CircleFind',
    
    # 读码识别
    'BarcodeReader',
    'QRCodeReader',
    'CodeReader',
    
    # OCR识别
    'OCRReader',
    'OCRLEnglish',
    
    # 图像分析
    'BlobFind',
    'PixelCount',
    'Histogram',
    
    # 通讯工具（使用增强版本）
    'EnhancedSendData',
    'EnhancedReceiveData',
    
    # CPU优化工具
    'CPUDetector',
    
    # 图像拼接工具
    'ImageStitchingTool',
    
    # 相机参数设置工具
    'CameraParameterSettingTool',
]
