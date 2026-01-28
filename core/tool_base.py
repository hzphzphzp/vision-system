#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具基类模块

提供所有算法工具的基类ToolBase，定义统一的接口和功能，
方便后续实现具体的算法工具。

Author: Vision System Team
Date: 2025-01-04
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Type
from dataclasses import dataclass, field

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.image_data import ImageData, ResultData
from utils.exceptions import VisionMasterException, ToolException, ParameterException, ImageException, CameraException
from utils.error_management import log_error, get_error_message
from utils.error_recovery import recover_from_error


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str                    # 参数显示名称
    param_type: str              # 参数类型: int/float/bool/string/file/rect/color/enum
    default: Any                 # 默认值
    description: str = ""        # 参数描述
    min_value: Any = None        # 最小值(数值类型)
    max_value: Any = None        # 最大值(数值类型)
    options: Optional[List[str]] = None    # 可选值列表(枚举类型)
    option_labels: Optional[Dict[str, str]] = None  # 选项值到中文标签的映射
    unit: str = ""               # 单位


# 参数中文名称映射
PARAM_CHINESE_NAMES = {
    # 通用参数
    "enabled": "启用状态",
    "name": "工具名称",
    "description": "工具描述",
    "threshold": "阈值",
    "min_area": "最小面积",
    "max_area": "最大面积",
    "sensitivity": "灵敏度",
    "kernel_size": "核大小",
    "blur_size": "模糊半径",
    "filter_type": "滤波器类型",
    "iteration": "迭代次数",
    "normalize": "归一化",
    
    # 图像源参数
    "source_type": "图像源类型",
    "file_path": "文件路径",
    "auto_rotate": "自动旋转",
    
    # 匹配参数
    "match_score": "匹配分数",
    "match_mode": "匹配模式",
    "angle_range": "角度范围",
    "scale_range": "缩放范围",
    "pyramid_level": "金字塔层级",
    
    # 检测参数
    "detect_type": "检测类型",
    "min_size": "最小尺寸",
    "max_size": "最大尺寸",
    "aspect_ratio": "宽高比",
    "fill_holes": "填充孔洞",
    "remove_noise": "去除噪点",
    
    # 位置参数
    "roi_x": "感兴趣区域X坐标",
    "roi_y": "感兴趣区域Y坐标",
    "roi_width": "感兴趣区域宽度",
    "roi_height": "感兴趣区域高度",
    "offset_x": "X方向偏移",
    "offset_y": "Y方向偏移",
    
    # 图像参数
    "brightness": "亮度",
    "contrast": "对比度",
    "gamma": "伽马值",
    "exposure": "曝光时间",
    "gain": "增益",
    
    # 颜色参数
    "lower_color": "下限颜色",
    "upper_color": "上限颜色",
    "color_space": "颜色空间",
    "tolerance": "颜色容差",
    
    # 通信参数
    "ip_address": "IP地址",
    "port": "端口号",
    "device_id": "设备ID",
    "timeout": "超时时间",
    
    # 绘制参数
    "draw_contours": "绘制轮廓",
    "draw_centroids": "绘制中心",
    "draw_bounding_boxes": "绘制边界框",
    "line_color": "线条颜色",
    "line_width": "线条宽度",
    "fill_color": "填充颜色",
    
    # 插值参数
    "interpolation": "插值算法",
    
    # 形态学参数
    "operation": "操作类型",
    
    # 匹配参数
    "min_score": "最小匹配分数",
    "max_count": "最大匹配数量",
    "template_path": "模板图像路径",
    "is_roi_set": "是否已设置ROI",
    "enable_roi": "启用ROI",
    
    # 直线查找参数
    "rho": "距离分辨率",
    "theta": "角度分辨率",
    "min_line_length": "最小线段长度",
    "max_line_gap": "最大线间隙",
    
    # 圆查找参数
    "min_radius": "最小半径",
    "max_radius": "最大半径",
    "param1": "Canny阈值1",
    "param2": "圆心累加器阈值",
    "min_dist": "最小圆心距离",
    
    # 几何参数
    "min_circularity": "最小圆形度",
    "max_circularity": "最大圆形度",
    "min_aspect_ratio": "最小宽高比",
    "max_aspect_ratio": "最大宽高比",
    
    # 颜色阈值参数
    "lower_bound": "下限阈值",
    "upper_bound": "上限阈值",
    "count_black": "统计黑色像素",
    "count_white": "统计白色像素",
    "count_range": "统计范围像素",
    
    # 直方图参数
    "histogram_type": "直方图类型",
    "hist_size": "直方图大小",
    
    # 卡尺测量参数
    "caliper_count": "卡尺数量",
    "step_size": "步进尺寸",
    "edge_threshold": "边缘阈值",
    "edge_width": "边缘宽度",
    "search_region": "搜索区域",
    "edge_polarity": "边缘极性",
    "draw_caliper": "绘制卡尺",
    "draw_edges": "绘制边缘",
    "draw_result": "绘制结果",
    "angle_start": "起始角度",
    "angle_end": "结束角度",
    "canny_threshold1": "Canny阈值1",
    "canny_threshold2": "Canny阈值2",
    
    # 滤波参数
    "sigma_x": "X方向标准差",
    "sigma_y": "Y方向标准差",
    "diameter": "邻域直径",
    "sigma_color": "颜色空间标准差",
    "sigma_space": "坐标空间标准差",
    
    # 图像尺寸参数
    "width": "宽度",
    "height": "高度",
    
    # 相机参数
    "fps": "帧率",
    "interval": "采集间隔",
}


# 参数类型中文名称映射
PARAM_TYPE_CHINESE_NAMES = {
    "string": "字符串",
    "integer": "整数",
    "float": "浮点数",
    "boolean": "布尔值",
    "enum": "枚举",
    "file_path": "文件路径",
    "directory_path": "目录路径",
    "image_source_type": "图像源类型",
    "image_file_path": "图片文件路径",
    "interpolation": "插值算法",
    "operation": "操作类型",
    "roi_rect": "矩形ROI",
    "roi_line": "直线ROI",
    "roi_circle": "圆形ROI",
}


# 插值算法中文名称映射
INTERPOLATION_CHINESE_NAMES = {
    "nearest": "最近邻插值",
    "linear": "双线性插值",
    "cubic": "双三次插值",
    "area": "区域插值",
    "lanczos4": "Lanczos插值",
}


# 形态学操作中文名称映射
MORPH_OPERATION_CHINESE_NAMES = {
    "open": "开运算",
    "close": "闭运算",
    "morph_gradient": "梯度运算",
    "top_hat": "顶帽变换",
    "black_hat": "底帽变换",
}


# 工具类别中文名称映射
TOOL_CATEGORY_CHINESE_NAMES = {
    "ImageSource": "图像源",
    "ImageFilter": "图像滤波",
    "Vision": "视觉检测",
    "Measurement": "尺寸测量",
    "Recognition": "模式识别",
    "Communication": "通信工具",
    "Default": "默认工具",
}


@dataclass
class ToolPort:
    """工具端口定义"""
    name: str           # 端口名称
    direction: str      # 输入(input)或输出(output)
    data_type: str      # 数据类型: image/point/line/circle/rect/value/string
    description: str = ""


class ToolBase(ABC):
    """
    工具基类，所有算法工具的父类
    
    提供统一的接口和功能：
    - 参数管理 (设置/获取参数)
    - 输入输出管理 (设置输入/获取输出)
    - 执行控制 (运行/重置)
    - 状态管理 (启用/禁用)
    - 日志记录
    
    子类必须实现：
    - tool_name: 工具名称
    - tool_category: 工具类别
    - _run_impl(): 实际执行逻辑
    
    示例：
        class MyTool(ToolBase):
            tool_name = "我的工具"
            tool_category = "Custom"
            
            def _run_impl(self):
                # 实现具体的处理逻辑
                pass
    """
    
    # 子类必须重写这些属性
    tool_name: str = "BaseTool"
    tool_category: str = "Base"
    tool_description: str = ""
    
    # 默认输入输出端口
    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像")
    ]
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像"),
        ToolPort("Result", "output", "value", "检测结果")
    ]
    
    def __init__(self, name: str = None):
        """
        初始化工具
        
        Args:
            name: 工具名称，如果为None则使用默认名称
        """
        self._id = id(self)
        self._name = name or f"{self.tool_category}_{self._id}"
        self._params: Dict[str, Any] = {}
        self._input_data: Optional[ImageData] = None
        self._output_data: Optional[ImageData] = None
        self._result_data: Optional[ResultData] = None
        self._is_enabled = True
        self._is_running = False
        self._last_error: Optional[str] = None
        self._execution_time = 0.0
        
        # 获取日志器
        self._logger = logging.getLogger(f"Tool.{self.tool_category}.{self.tool_name}")
        
        # 初始化参数
        self._init_params()
    
    def _init_params(self):
        """初始化参数，子类可以重写添加默认参数"""
        # 从PARAM_DEFINITIONS加载默认值
        if hasattr(self, 'PARAM_DEFINITIONS') and self.PARAM_DEFINITIONS:
            for key, param_def in self.PARAM_DEFINITIONS.items():
                if hasattr(param_def, 'default'):
                    self._params[key] = param_def.default
                    self._logger.debug(f"初始化参数: {self._name}.{key} = {param_def.default}")
    
    @property
    def id(self) -> int:
        """获取工具ID"""
        return self._id
    
    @property
    def name(self) -> str:
        """获取工具名称"""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """设置工具名称"""
        self._name = value
    
    @property
    def full_name(self) -> str:
        """获取完整名称 (类别_名称)"""
        return f"{self.tool_category}_{self._name}"
    
    @property
    def is_enabled(self) -> bool:
        """获取启用状态"""
        return self._is_enabled
    
    @is_enabled.setter
    def is_enabled(self, value: bool):
        """设置启用状态"""
        self._is_enabled = value
    
    @property
    def is_running(self) -> bool:
        """获取运行状态"""
        return self._is_running
    
    @property
    def last_error(self) -> Optional[str]:
        """获取最后错误"""
        return self._last_error
    
    @property
    def execution_time(self) -> float:
        """获取执行时间(秒)"""
        return self._execution_time
    
    @property
    def input_ports(self) -> List[ToolPort]:
        """获取输入端口列表"""
        return self.INPUT_PORTS.copy()
    
    @property
    def output_ports(self) -> List[ToolPort]:
        """获取输出端口列表"""
        return self.OUTPUT_PORTS.copy()
    
    def set_param(self, key: str, value: Any, param_type: str = None, description: str = None, options: List[str] = None):
        """
        设置参数
        
        Args:
            key: 参数名称
            value: 参数值
            param_type: 参数类型（可选）
            description: 参数描述（可选）
            options: 枚举选项列表（可选）
            
        Returns:
            实际设置的参数值（可能被修正）
            
        Raises:
            ParameterException: 参数设置失败
        """
        # 验证并修正参数值
        fixed_value = self._validate_and_fix_param(key, value)
        
        # 如果值被修正，记录日志
        if fixed_value != value:
            self._logger.debug(f"参数 {key} 自动修正: {value} -> {fixed_value}")
        
        try:
            old_value = self._params.get(key)
            self._params[key] = fixed_value
            
            # 保存额外的参数信息
            if param_type is not None:
                self._params[f"__type_{key}"] = param_type
            if description is not None:
                self._params[f"__desc_{key}"] = description
            if options is not None:
                self._params[f"__options_{key}"] = options
            
            self._logger.debug(f"设置参数: {self._name}.{key} = {fixed_value}")
            
            # 触发参数变更回调
            self._on_param_changed(key, old_value, fixed_value)
            
            return fixed_value
            
        except Exception as e:
            raise ParameterException(f"设置参数失败: {key}, 错误: {str(e)}")
    
    def _validate_and_fix_param(self, key: str, value: Any) -> Any:
        """验证并修正参数值
        
        子类可以重写此方法来添加特定的验证和修正逻辑
        
        Args:
            key: 参数名称
            value: 原始参数值
            
        Returns:
            修正后的参数值
        """
        # ==================== 图像滤波参数 ====================
        # 核大小必须为正奇数
        if key == "kernel_size":
            if isinstance(value, (int, float)):
                if value <= 0:
                    return 1  # 最小为1
                if int(value) % 2 == 0:
                    return int(value) + 1  # 偶数变奇数
        
        # 直径必须为正奇数
        if key == "diameter":
            if isinstance(value, (int, float)):
                if value <= 0:
                    return 3
                if int(value) % 2 == 0:
                    return int(value) + 1
        
        # 迭代次数必须为正整数
        if key in ["iteration", "iterations"]:
            if isinstance(value, (int, float)):
                return max(1, int(value))
        
        # 归一化参数
        if key == "normalize":
            return bool(value)
        
        # ==================== 图像尺寸参数 ====================
        # 宽高必须为正整数
        if key in ["width", "height"]:
            if isinstance(value, (int, float)):
                return max(1, int(value))
        
        # ==================== ROI参数 ====================
        # ROI坐标和尺寸必须为非负数
        if key in ["roi_x", "roi_y", "roi_width", "roi_height", "offset_x", "offset_y"]:
            if isinstance(value, (int, float)) and value < 0:
                return 0
        
        # ==================== 阈值参数 ====================
        # 阈值必须在0-255之间
        if key in ["threshold", "threshold_value", "canny_threshold1", "canny_threshold2"]:
            if isinstance(value, (int, float)):
                return max(0, min(255, value))
        
        # ==================== 匹配参数 ====================
        # 匹配分数必须在0-1之间
        if key in ["min_score", "match_score"]:
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, round(value, 4)))
        
        # 最大匹配数量必须为正整数
        if key == "max_count":
            if isinstance(value, (int, float)):
                return max(1, int(value))
        
        # ==================== 面积和尺寸参数 ====================
        # 最小面积必须为非负数
        if key in ["min_area", "min_size", "min_radius"]:
            if isinstance(value, (int, float)) and value < 0:
                return 0
        
        # 最大面积必须大于最小值
        if key in ["max_area", "max_size", "max_radius"]:
            if isinstance(value, (int, float)):
                if value <= 0:
                    return 1
                return value
        
        # ==================== 圆形度和宽高比参数 ====================
        # 最小圆形度必须在0-1之间
        if key == "min_circularity":
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, value))
        
        # 最大圆形度必须在0-1之间
        if key == "max_circularity":
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, value))
        
        # 宽高比必须在合理范围内
        if key in ["min_aspect_ratio", "max_aspect_ratio"]:
            if isinstance(value, (int, float)):
                if value < 0:
                    return 0.1
                return value
        
        # ==================== Hough变换参数 ====================
        # rho必须是正数
        if key == "rho":
            if isinstance(value, (int, float)) and value <= 0:
                return 1
        
        # theta必须是正数
        if key == "theta":
            if isinstance(value, (int, float)) and value <= 0:
                return 0.01745  # 约1度
        
        # Hough阈值必须是正整数
        if key == "threshold":
            if isinstance(value, (int, float)) and value <= 0:
                return 100
        
        # 最小线段长度必须为正数
        if key == "min_line_length":
            if isinstance(value, (int, float)) and value <= 0:
                return 50
        
        # 最大线间隙必须为非负数
        if key == "max_line_gap":
            if isinstance(value, (int, float)) and value < 0:
                return 0
        
        # ==================== 霍夫圆检测参数 ====================
        # param1 (Canny阈值) 必须在1-200之间
        if key == "param1":
            if isinstance(value, (int, float)):
                return max(1, min(200, int(value)))
        
        # param2 (圆心阈值) 必须是正数
        if key == "param2":
            if isinstance(value, (int, float)) and value <= 0:
                return 50
        
        # 最小圆心距离必须为正数
        if key == "min_dist":
            if isinstance(value, (int, float)) and value <= 0:
                return 20
        
        # ==================== 颜色阈值参数 ====================
        # 下限必须小于上限
        if key == "lower_bound":
            if isinstance(value, (int, float)):
                return max(0, min(255, value))
        
        if key == "upper_bound":
            if isinstance(value, (int, float)):
                return max(0, min(255, value))
        
        # ==================== 直方图参数 ====================
        # 直方图大小必须是正整数
        if key == "hist_size":
            if isinstance(value, (int, float)):
                return max(1, int(value))
        
        # ==================== 相机参数 ====================
        # 帧率必须是正数
        if key == "fps":
            if isinstance(value, (int, float)) and value <= 0:
                return 30
        
        # 曝光时间必须为正数
        if key == "exposure":
            if isinstance(value, (int, float)):
                if value < 0:
                    return -1  # 保持自动曝光
                return value
        
        # 增益必须为正数
        if key == "gain":
            if isinstance(value, (int, float)):
                if value < 0:
                    return -1  # 保持自动增益
                return value
        
        # 采集间隔必须为非负数
        if key == "interval":
            if isinstance(value, (int, float)) and value < 0:
                return 0
        
        # ==================== 角度参数 ====================
        # 角度范围
        if key in ["angle_start", "angle_end", "angle_range"]:
            if isinstance(value, (int, float)):
                return value  # 角度可以正负
        
        # ==================== 插值参数 ====================
        # 插值类型保持字符串
        
        # ==================== 布尔参数 ====================
        # 各种布尔参数
        if key in ["is_roi_set", "enable_roi", "fill_holes", "remove_noise",
                   "draw_contours", "draw_centroids", "draw_bounding_boxes",
                   "count_black", "count_white", "count_range", "auto_rotate"]:
            return bool(value)
        
        # ==================== 字符串参数 ====================
        # 路径、模式等字符串参数
        if key in ["source_type", "file_path", "template_path", "match_mode",
                   "operation", "interpolation", "threshold_method", "histogram_type",
                   "template_image_path"]:
            return str(value) if value is not None else ""
        
        return value
    
    def _is_param_valid(self, key: str, value: Any) -> bool:
        """检查参数是否有效，子类可以重写"""
        return True
    
    def _on_param_changed(self, key: str, old_value: Any, new_value: Any):
        """参数变更回调，子类可以重写"""
        pass
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """
        获取参数
        
        Args:
            key: 参数名称
            default: 默认值
            
        Returns:
            参数值，如果不存在则返回默认值
        """
        return self._params.get(key, default)
    
    def get_all_params(self) -> Dict[str, Any]:
        """获取所有参数"""
        return self._params.copy()
    
    def get_param_with_details(self) -> Dict[str, Dict[str, Any]]:
        """获取参数详细信息（包含中文名称和描述）
        
        Returns:
            参数字典，键为参数名，值为包含以下信息的字典:
            - value: 参数值
            - display_name: 参数中文名称
            - description: 参数描述
            - type: 参数类型
            - type_display: 参数类型中文名称
            - unit: 参数单位
            - options: 枚举选项列表
            - option_labels: 选项值到中文标签的映射
        """
        result = {}
        
        # 获取 PARAM_DEFINITIONS（可能是列表或字典）
        param_definitions_raw = getattr(self, 'PARAM_DEFINITIONS', [])
        
        # 如果是列表，转换为字典方便查找
        param_definitions = {}
        if isinstance(param_definitions_raw, list):
            for param_def in param_definitions_raw:
                # 使用参数定义中的 name 属性作为键
                if hasattr(param_def, 'name'):
                    param_definitions[param_def.name] = param_def
        elif isinstance(param_definitions_raw, dict):
            param_definitions = param_definitions_raw

        for param_name, param_value in self._params.items():
            # 跳过内部参数
            if param_name.startswith("__"):
                continue
            
            # 优先从 PARAM_DEFINITIONS 获取信息
            if param_name in param_definitions:
                param_def = param_definitions[param_name]
                # 处理字典类型的参数定义
                if isinstance(param_def, dict):
                    display_name = param_def.get('name', param_name)
                    description = param_def.get('description', '')
                    param_type = param_def.get('param_type', 'string')
                    options = param_def.get('options', None)
                    option_labels = param_def.get('option_labels', None)
                    unit = param_def.get('unit', '')
                else:
                    # 处理对象类型的参数定义
                    display_name = getattr(param_def, 'name', param_name)
                    description = getattr(param_def, 'description', '')
                    param_type = getattr(param_def, 'param_type', 'string')
                    options = getattr(param_def, 'options', None)
                    option_labels = getattr(param_def, 'option_labels', None)
                    unit = getattr(param_def, 'unit', '')
            else:
                # 回退到全局映射
                display_name = PARAM_CHINESE_NAMES.get(param_name, param_name)
                param_type = self._get_param_type(param_name)
                description = self._get_param_description(param_name)
                options = self._params.get(f"__options_{param_name}")
                option_labels = self._params.get(f"__option_labels_{param_name}")
                unit = self._get_param_unit(param_name)
            
            type_display = PARAM_TYPE_CHINESE_NAMES.get(param_type, param_type)
            
            result[param_name] = {
                'value': param_value,
                'display_name': display_name,
                'description': description,
                'type': param_type,
                'type_display': type_display,
                'unit': unit,
                'options': options,
                'option_labels': option_labels
            }
        
        return result
    
    def _get_param_type(self, param_name: str) -> str:
        """获取参数类型"""
        # 优先使用保存的参数类型
        saved_type = self._params.get(f"__type_{param_name}")
        if saved_type:
            return saved_type
        
        value = self._params.get(param_name)
        
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            # 尝试识别特殊类型
            # 图片文件路径（包含常见图片扩展名）
            if any(ext in value.lower() for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']):
                return "image_file_path"
            # 图像源类型
            elif param_name == "source_type":
                return "image_source_type"
            # 文件路径
            elif os.path.exists(value) or value.startswith('/') or value.startswith('.'):
                return "file_path"
            return "string"
        else:
            return "string"
    
    def _get_param_description(self, param_name: str) -> str:
        """获取参数描述"""
        # 优先使用保存的描述
        saved_desc = self._params.get(f"__desc_{param_name}")
        if saved_desc:
            return saved_desc
        
        # 使用默认中文名称
        return PARAM_CHINESE_NAMES.get(param_name, param_name)
    
    def _get_param_unit(self, param_name: str) -> str:
        """获取参数单位"""
        # 常见参数单位映射
        unit_mapping = {
            "threshold": "",
            "min_area": "像素²",
            "max_area": "像素²",
            "kernel_size": "像素",
            "blur_size": "像素",
            "match_score": "%",
            "angle_range": "度",
            "brightness": "",
            "contrast": "",
            "gamma": "",
            "exposure": "微秒",
            "gain": "dB",
            "roi_x": "像素",
            "roi_y": "像素",
            "roi_width": "像素",
            "roi_height": "像素",
            "offset_x": "像素",
            "offset_y": "像素",
            "tolerance": "",
            "timeout": "毫秒",
            "port": "",
            "iteration": "次",
        }
        
        return unit_mapping.get(param_name, "")
    
    def reset_params(self):
        """重置所有参数为默认值"""
        self._params.clear()
        self._init_params()
    
    def set_input(self, image_data: ImageData, port: str = "InputImage"):
        """
        设置输入数据
        
        Args:
            image_data: 输入图像数据
            port: 输入端口名称
        """
        self._input_data = image_data
        self._logger.debug(f"设置输入: {port}, shape={image_data.shape if image_data.is_valid else 'None'}")
    
    def get_input(self, port: str = "InputImage") -> Optional[ImageData]:
        """
        获取输入数据
        
        Args:
            port: 输入端口名称
            
        Returns:
            输入图像数据，如果不存在则返回None
        """
        return self._input_data
    
    def get_output(self, port: str = "OutputImage") -> Optional[ImageData]:
        """
        获取输出数据
        
        Args:
            port: 输出端口名称
            
        Returns:
            输出图像数据，如果不存在则返回None
        """
        return self._output_data
    
    def get_result(self, key: str = None) -> ResultData:
        """
        获取结果数据
        
        Args:
            key: 结果键，如果为None则返回完整结果
            
        Returns:
            结果数据
        """
        if key is None:
            return self._result_data
        return self._result_data.get_value(key) if self._result_data else None
    
    def has_input(self) -> bool:
        """检查是否有输入数据"""
        return self._input_data is not None and self._input_data.is_valid
    
    def has_output(self) -> bool:
        """检查是否有输出数据"""
        return self._output_data is not None and self._output_data.is_valid
    
    def run(self) -> bool:
        """
        执行工具处理
        
        Returns:
            执行成功返回True，失败返回False
            
        Raises:
            ToolException: 执行失败
        """
        if not self._is_enabled:
            self._logger.debug(f"工具已禁用，跳过执行: {self._name}")
            return True
        
        if self._is_running:
            self._logger.warning(f"工具正在运行中: {self._name}")
            return False
        
        self._is_running = True
        self._last_error = None
        self._result_data = ResultData()
        
        start_time = time.time()
        
        try:
            self._logger.info(f"开始执行: {self._name}")
            
            # 检查输入
            if not self._check_input():
                raise ToolException("输入数据无效", error_code=400, details={"tool": self._name, "check": "input"})
            
            # 执行实际处理
            output = self._run_impl()
            
            # 处理输出数据
            if output is not None:
                if isinstance(output, dict):
                    # 处理字典形式的输出
                    for key, value in output.items():
                        if isinstance(value, ImageData):
                            # 如果有 OutputImage，设置为主输出
                            if key == "OutputImage":
                                self._output_data = value
                            # 将其他输出也存入结果
                            self._result_data.set_value(key, value)
                        else:
                            # 其他数值结果
                            self._result_data.set_value(key, value)
                elif isinstance(output, ImageData):
                    # 直接返回 ImageData
                    self._output_data = output
            
            # 执行后处理
            self._post_process()
            
            self._execution_time = time.time() - start_time
            self._logger.info(f"执行完成: {self._name}, 耗时={self._execution_time*1000:.2f}ms")
            
            return True
            
        except ParameterException as e:
            self._last_error = str(e)
            self._result_data.status = False
            self._result_data.message = get_error_message(400, self._last_error)
            self._result_data.error_code = 400
            self._result_data.error_type = "ParameterError"
            self._execution_time = time.time() - start_time
            
            # 使用错误管理模块记录错误
            log_error(400, f"{self._name}: {self._last_error}", {"tool": self._name})
            
            # 执行错误恢复
            recover_from_error(
                error_type="ParameterError",
                error_code=400,
                error_message=self._last_error,
                component=self._name,
                details={"tool": self._name, "error": str(e)}
            )
            
            raise ToolException(get_error_message(400, f"{self._name}: {self._last_error}"), error_code=400, details={"tool": self._name, "error": str(e)})
            
        except ImageException as e:
            self._last_error = str(e)
            self._result_data.status = False
            self._result_data.message = get_error_message(422, self._last_error)
            self._result_data.error_code = 422
            self._result_data.error_type = "ImageError"
            self._execution_time = time.time() - start_time
            
            # 使用错误管理模块记录错误
            log_error(422, f"{self._name}: {self._last_error}", {"tool": self._name})
            
            # 执行错误恢复
            recover_from_error(
                error_type="ImageError",
                error_code=422,
                error_message=self._last_error,
                component=self._name,
                details={"tool": self._name, "error": str(e)}
            )
            
            raise ToolException(get_error_message(422, f"{self._name}: {self._last_error}"), error_code=422, details={"tool": self._name, "error": str(e)})
            
        except CameraException as e:
            self._last_error = str(e)
            self._result_data.status = False
            self._result_data.message = get_error_message(502, self._last_error)
            self._result_data.error_code = 502
            self._result_data.error_type = "CameraError"
            self._execution_time = time.time() - start_time
            
            # 使用错误管理模块记录错误
            log_error(502, f"{self._name}: {self._last_error}", {"tool": self._name})
            
            # 执行错误恢复
            recover_from_error(
                error_type="CameraError",
                error_code=502,
                error_message=self._last_error,
                component=self._name,
                details={"tool": self._name, "error": str(e)}
            )
            
            raise ToolException(get_error_message(502, f"{self._name}: {self._last_error}"), error_code=502, details={"tool": self._name, "error": str(e)})
            
        except Exception as e:
            self._last_error = str(e)
            self._result_data.status = False
            self._result_data.message = get_error_message(500, self._last_error)
            self._result_data.error_code = 500
            self._result_data.error_type = "InternalError"
            self._execution_time = time.time() - start_time
            
            # 捕获并分类系统异常
            import traceback
            error_trace = traceback.format_exc()
            details = {
                "tool": self._name,
                "error": str(e),
                "traceback": error_trace,
                "execution_time": self._execution_time
            }
            
            # 使用错误管理模块记录错误
            log_error(500, f"{self._name}: {self._last_error}", details)
            
            # 执行错误恢复
            recover_from_error(
                error_type="InternalError",
                error_code=500,
                error_message=self._last_error,
                component=self._name,
                details=details
            )
            
            raise ToolException(get_error_message(500, f"{self._name}: {self._last_error}"), error_code=500, details=details)
        
        finally:
            self._is_running = False
    
    def _check_input(self) -> bool:
        """检查输入数据有效性，子类可以重写"""
        return self.has_input()
    
    @abstractmethod
    def _run_impl(self):
        """
        实际执行逻辑，子类必须重写
        
        在此方法中：
        - 从self._input_data获取输入
        - 执行算法处理
        - 设置self._output_data为输出
        - 设置self._result_data为结果
        """
        pass
    
    def _post_process(self):
        """执行后处理，子类可以重写"""
        pass
    
    def reset(self):
        """重置工具状态"""
        self._output_data = None
        self._result_data = None
        self._is_running = False
        self._last_error = None
        self._execution_time = 0.0
        self._logger.debug(f"工具已重置: {self._name}")
    
    def clear_input(self):
        """清除输入数据"""
        self._input_data = None
    
    def clear_output(self):
        """清除输出数据"""
        self._output_data = None
    
    def clear(self):
        """清除所有数据"""
        self.clear_input()
        self.clear_output()
        self.reset()
    
    def copy(self) -> 'ToolBase':
        """创建工具拷贝"""
        new_tool = self.__class__(self._name)
        new_tool._params = self._params.copy()
        return new_tool
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "id": self._id,
            "name": self._name,
            "tool_name": self.tool_name,
            "tool_category": self.tool_category,
            "tool_description": self.tool_description,
            "is_enabled": self._is_enabled,
            "is_running": self._is_running,
            "execution_time": self._execution_time,
            "params": self._params.copy(),
            "input_ports": [p.name for p in self.input_ports],
            "output_ports": [p.name for p in self.output_ports]
        }
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self._name}, "
                f"category={self.tool_category}, "
                f"enabled={self._is_enabled})")
    
    def __str__(self) -> str:
        return self.__repr__()


class ImageSourceToolBase(ToolBase):
    """图像源工具基类"""
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像")
    ]
    
    def _check_input(self) -> bool:
        """图像源工具不需要输入"""
        return True
    
    @abstractmethod
    def _run_impl(self):
        """图像源工具必须实现此方法"""
        pass


class ImageProcessToolBase(ToolBase):
    """图像处理工具基类"""
    
    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像")
    ]
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像")
    ]


class VisionAlgorithmToolBase(ToolBase):
    """视觉算法工具基类"""
    
    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像"),
        ToolPort("ROI", "input", "rect", "感兴趣区域")
    ]
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像"),
        ToolPort("Result", "output", "value", "检测结果")
    ]


class MeasurementToolBase(ToolBase):
    """测量工具基类"""
    
    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像")
    ]
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像"),
        ToolPort("Results", "output", "value", "测量结果")
    ]


class RecognitionToolBase(ToolBase):
    """识别工具基类"""
    
    INPUT_PORTS = [
        ToolPort("InputImage", "input", "image", "输入图像")
    ]
    
    OUTPUT_PORTS = [
        ToolPort("OutputImage", "output", "image", "输出图像"),
        ToolPort("Result", "output", "string", "识别结果")
    ]


class ToolRegistry:
    """工具注册表，用于管理所有可用的工具"""
    
    _instance = None
    _tools: Dict[str, Type[ToolBase]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, tool_class: Type[ToolBase]):
        """注册工具类"""
        key = f"{tool_class.tool_category}.{tool_class.tool_name}"
        cls._tools[key] = tool_class
        return tool_class
    
    @classmethod
    def get_tool_class(cls, category: str, name: str) -> Type[ToolBase]:
        """获取工具类"""
        key = f"{category}.{name}"
        return cls._tools.get(key)
    
    @classmethod
    def get_tools_by_category(cls, category: str) -> Dict[str, Type[ToolBase]]:
        """获取指定类别的所有工具"""
        return {
            k: v for k, v in cls._tools.items()
            if k.startswith(f"{category}.")
        }
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, Type[ToolBase]]:
        """获取所有已注册的工具"""
        return cls._tools.copy()
    
    @classmethod
    def create_tool(cls, category: str, name: str, *args, **kwargs) -> ToolBase:
        """创建工具实例"""
        tool_class = cls.get_tool_class(category, name)
        if tool_class is None:
            raise ValueError(f"未找到工具: {category}.{name}")
        return tool_class(*args, **kwargs)
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """获取所有工具类别"""
        categories = set()
        for key in cls._tools.keys():
            parts = key.split(".")
            if len(parts) >= 1:
                categories.add(parts[0])
        return list(categories)
