#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像源工具模块 - 简化版本用于避免语法问题

Author: Vision System Team
Date: 2026-01-22
"""

import sys
import os
import cv2
import numpy as np
import time
import logging
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ImageSourceToolBase, ToolRegistry, ToolParameter, ImageData


@ToolRegistry.register
class ImageSource(ImageSourceToolBase):
    """图像读取器工具"""
    tool_name = "图像读取器"
    tool_category = "ImageSource"
    tool_description = "从文件或相机获取图像"
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._file_path = None
        self._camera = None
        self._is_connected = False
        self._last_frame_time = 0
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("file_path", "", param_type="image_file_path", 
                       description="本地图片文件路径")
        self.set_param("auto_rotate", False, 
                       description="是否自动旋转90度")
    
    def _run_impl(self):
        """执行图像采集"""
        file_path = self.get_param("file_path", "")
        
        if not file_path:
            raise Exception("未指定图像文件路径")
        
        try:
            image_data = np.fromfile(file_path, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        except:
            image = cv2.imread(file_path)
        
        if image is None:
            raise Exception(f"无法读取图像: {file_path}")
        
        height, width, channels = image.shape
        image_data = ImageData(image, width, height, channels)
        
        return {
            "OutputImage": image_data,
            "Width": width,
            "Height": height,
            "Channels": channels
        }

@ToolRegistry.register  
class CameraSource(ImageSourceToolBase):
    """相机图像源工具"""
    tool_name = "相机"
    tool_category = "ImageSource"
    tool_description = "从相机采集图像"
    
    def __init__(self, name: str = None):
        super().__init__(name)
    
    def _init_params(self):
        """初始化默认参数"""
        pass
    
    def _run_impl(self):
        """执行图像采集"""
        return {
            "OutputImage": ImageData(640, 480, 1, None),
            "message": "相机采集功能需要硬件支持"
        }
