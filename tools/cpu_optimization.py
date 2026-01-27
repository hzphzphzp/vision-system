#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU优化工具模块

提供基于CPU的高性能计算优化工具，包括并行处理、内存优化和SIMD加速。

Author: Vision System Team
Date: 2026-01-26
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import VisionAlgorithmToolBase, ToolRegistry, ToolParameter
from data.image_data import ImageData, ROI, ResultData

# 延迟导入CPU优化模块
CPU_OPTIMIZATION_AVAILABLE = None
_CPU_OPTIMIZATION_IMPORTED = False

def _ensure_cpu_optimization_imported():
    """确保CPU优化模块已导入（延迟加载）"""
    global CPU_OPTIMIZATION_AVAILABLE, _CPU_OPTIMIZATION_IMPORTED
    if _CPU_OPTIMIZATION_IMPORTED:
        return CPU_OPTIMIZATION_AVAILABLE
    
    try:
        from modules.cpu_optimization.models.yolo26_cpu import YOLO26CPUDetector
        globals().update({'YOLO26CPUDetector': YOLO26CPUDetector})
        CPU_OPTIMIZATION_AVAILABLE = True
        logging.info("YOLO26检测器已加载")
    except ImportError as e:
        CPU_OPTIMIZATION_AVAILABLE = False
        logging.warning(f"YOLO26检测器不可用: {e}")
    
    _CPU_OPTIMIZATION_IMPORTED = True
    return CPU_OPTIMIZATION_AVAILABLE


@ToolRegistry.register
class CPUDetector(VisionAlgorithmToolBase):
    """
    YOLO26目标检测工具
    
    使用Ultralytics官方YOLO26 API进行目标检测
    
    参数说明：
    - model_path: 模型文件路径
    - conf_threshold: 置信度阈值
    - nms_threshold: NMS阈值
    """
    
    tool_name = "YOLO26-CPU"
    tool_category = "Vision"
    tool_description = "使用Ultralytics YOLO26进行目标检测"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "model_path": ToolParameter(
            name="模型路径",
            param_type="file_path",
            default="",
            description="YOLO26模型文件路径（.pt格式）"
        ),
        "model_type": ToolParameter(
            name="模型类型",
            param_type="enum",
            default="custom",
            description="选择预训练模型类型（custom为自定义模型）",
            options=["custom", "yolo26n", "yolo26s", "yolo26m", "yolo26l", "yolo26x"]
        ),
        "conf_threshold": ToolParameter(
            name="置信度阈值",
            param_type="float",
            default=0.25,
            description="检测置信度阈值",
            min_value=0.01,
            max_value=0.99
        ),
        "nms_threshold": ToolParameter(
            name="NMS阈值",
            param_type="float",
            default=0.45,
            description="非极大值抑制阈值",
            min_value=0.01,
            max_value=0.99
        ),
        "save_result_image": ToolParameter(
            name="保存结果图",
            param_type="boolean",
            default=True,
            description="是否在输出图像上绘制检测框"
        ),
        "class_filter": ToolParameter(
            name="过滤类别",
            param_type="string",
            default="",
            description="要检测的类别ID列表，逗号分隔，留空检测所有类别"
        )
    }
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._detector = None
    
    def initialize(self, parameters: Dict[str, Any]) -> bool:
        """初始化YOLO26检测器"""
        try:
            # 确保模块已导入
            if not _ensure_cpu_optimization_imported():
                self._logger.error("YOLO26检测器模块不可用")
                return False
            
            model_path = parameters.get("model_path", "")
            model_type = parameters.get("model_type", "custom")
            conf_threshold = parameters.get("conf_threshold", 0.25)
            nms_threshold = parameters.get("nms_threshold", 0.45)
            class_filter = parameters.get("class_filter", "")
            
            # 创建检测器
            self._detector = YOLO26CPUDetector(
                conf_threshold=conf_threshold,
                nms_threshold=nms_threshold
            )
            
            # 保存配置参数
            self._class_filter = [int(x.strip()) for x in class_filter.split(",") if x.strip().isdigit()]
            self._save_result_image = parameters.get("save_result_image", True)
            
            # 加载模型
            model_loaded = False
            
            # 1. 首先检查用户指定的模型路径
            if model_path and os.path.exists(model_path):
                if self._detector.load_model(model_path):
                    model_loaded = True
                    self._logger.info(f"已加载模型: {model_path}")
                else:
                    self._logger.warning(f"无法加载指定模型: {model_path}")
            
            # 2. 如果没有指定模型或加载失败，尝试使用本地模型
            if not model_loaded and model_type and model_type != "custom":
                try:
                    from modules.cpu_optimization.utils.model_downloader import get_downloader
                    # 使用正确的模型目录
                    downloader = get_downloader("modules/cpu_optimization/models")
                    
                    if downloader.is_model_available(model_type):
                        default_model = str(downloader.get_model_path(model_type))
                        if self._detector.load_model(default_model):
                            model_loaded = True
                            self._logger.info(f"已加载本地模型: {default_model}")
                    else:
                        self._logger.info(f"开始下载模型: {model_type}")
                        if downloader.download_model(model_type):
                            default_model = str(downloader.get_model_path(model_type))
                            if self._detector.load_model(default_model):
                                model_loaded = True
                                self._logger.info(f"已下载并加载模型: {default_model}")
                except Exception as e:
                    self._logger.warning(f"模型下载失败: {e}")
            
            if not model_loaded:
                self._logger.warning("未加载任何模型，请手动选择模型文件")
            
            self._logger.info(f"YOLO26-CPU检测器已初始化")
            return True
            
        except Exception as e:
            self._logger.error(f"YOLO26-CPU检测器初始化失败: {e}")
            return False
    
    def _run_impl(self) -> Dict[str, Any]:
        """执行目标检测"""
        if not self._detector:
            height, width = self._input_data.data.shape[:2]
            output_image_data = ImageData(self._input_data.data, width, height, 3)
            return {
                "OutputImage": output_image_data,
                "error": "检测器未初始化",
                "detection_count": 0
            }
        
        if not self._detector.is_loaded:
            height, width = self._input_data.data.shape[:2]
            output_image_data = ImageData(self._input_data.data, width, height, 3)
            return {
                "OutputImage": output_image_data,
                "error": "模型未加载，请在属性面板中配置模型路径",
                "detection_count": 0
            }
        
        if not self._input_data or not self._input_data.is_valid:
            return {"error": "输入图像无效"}
        
        # 执行检测
        result = self._detector.detect(self._input_data.data)
        
        if "error" in result:
            height, width = self._input_data.data.shape[:2]
            output_image_data = ImageData(self._input_data.data, width, height, 3)
            return {
                "OutputImage": output_image_data,
                "error": result["error"],
                "detection_count": 0
            }
        
        # 过滤检测结果
        detections = result.get("detections", [])
        filtered_detections = []
        for det in detections:
            if hasattr(self, '_class_filter') and self._class_filter:
                if det["class_id"] not in self._class_filter:
                    continue
            filtered_detections.append(det)
        
        # 创建输出图像（带检测框）
        output_image = self._input_data.data.copy()
        if self._save_result_image:
            for det in filtered_detections:
                bbox = det["bbox"]
                x1 = int(bbox["x1"] * output_image.shape[1])
                y1 = int(bbox["y1"] * output_image.shape[0])
                x2 = int(bbox["x2"] * output_image.shape[1])
                y2 = int(bbox["y2"] * output_image.shape[0])
                
                # 随机颜色
                color = tuple(np.random.randint(0, 255, 3).tolist())
                
                # 绘制边界框
                cv2.rectangle(output_image, (x1, y1), (x2, y2), color, 2)
                
                # 绘制标签
                label = f"{det['class_name']}: {det['confidence']:.2f}"
                cv2.putText(output_image, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 创建输出图像数据
        height, width = output_image.shape[:2]
        output_image_data = ImageData(output_image, width, height, 3)
        
        return {
            "OutputImage": output_image_data,
            "detection_count": len(filtered_detections),
            "total_detections": result.get("total_detections", 0),
            "inference_time_ms": result.get("inference_time_ms", 0),
            "detections": filtered_detections
        }
    
    def release(self):
        """释放资源"""
        if self._detector:
            self._detector.release()
        self._detector = None
