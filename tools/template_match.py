#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板匹配工具模块

提供各种模板匹配工具，包括灰度匹配、形状匹配等。

Author: Vision System Team
Date: 2025-01-04
"""

import logging
import time
from typing import Optional, Dict, Any, List
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import VisionAlgorithmToolBase, ToolRegistry, ToolParameter
from core.roi_tool_mixin import ROIToolMixin
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException


class MatchMode(Enum):
    """匹配模式"""
    SQDIFF = "sqdiff"
    SQDIFF_NORMED = "sqdiff_normed"
    CCORR = "ccorr"
    CCORR_NORMED = "ccorr_normed"
    CCOEFF = "ccoeff"
    CCOEFF_NORMED = "ccoeff_normed"


class SearchMode(Enum):
    """搜索模式"""
    ALL_BEST = "all_best"
    ALL_MAX = "all_max"
    SINGLE_BEST = "single_best"


@ToolRegistry.register
class GrayMatch(ROIToolMixin, VisionAlgorithmToolBase):
    """
    灰度匹配工具
    
    在图像中搜索与模板最匹配的位置。
    
    参数说明：
    - template_path: 模板图像路径
    - match_mode: 匹配模式
    - min_score: 最小分数阈值 (0-1)
    - max_count: 最大匹配数量
    - greedy: 贪婪度 (0-1)
    - angle_start: 起始角度
    - angle_end: 结束角度
    - angle_step: 角度步长
    """
    
    tool_name = "灰度匹配"
    tool_category = "Vision"
    tool_description = "在图像中搜索与模板最匹配的位置"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "template_path": ToolParameter(
            name="模板路径",
            param_type="string",
            default="",
            description="模板图像路径（留空可使用ROI模板）"
        ),
        "match_mode": ToolParameter(
            name="匹配模式",
            param_type="enum",
            default="ccoeff_normed",
            description="匹配模式",
            options=["sqdiff", "sqdiff_normed", "ccorr", "ccorr_normed", "ccoeff", "ccoeff_normed"]
        ),
        "min_score": ToolParameter(
            name="最小分数",
            param_type="float",
            default=0.7,
            description="最小分数阈值",
            min_value=0.0,
            max_value=1.0
        ),
        "max_count": ToolParameter(
            name="最大数量",
            param_type="integer",
            default=10,
            description="最大匹配数量",
            min_value=1,
            max_value=100
        ),
        "roi": ToolParameter(
            name="ROI模板",
            param_type="roi_rect",
            default=None,
            description="ROI模板区域（点击按钮绘制ROI作为模板）"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("template_path", "")
        self.set_param("match_mode", "ccoeff_normed")
        self.set_param("min_score", 0.7)
        self.set_param("max_count", 10)
        self.set_param("roi", None)
        self._init_roi_params()  # 使用mixin的初始化方法
        self._template_image = None
    
    MATCH_MODE_MAP = {
        "sqdiff": cv2.TM_SQDIFF,
        "sqdiff_normed": cv2.TM_SQDIFF_NORMED,
        "ccorr": cv2.TM_CCORR,
        "ccorr_normed": cv2.TM_CCORR_NORMED,
        "ccoeff": cv2.TM_CCOEFF,
        "ccoeff_normed": cv2.TM_CCOEFF_NORMED
    }
    
    def _load_template(self):
        """加载模板图像"""
        template_path = self.get_param("template_path", "")
        
        if template_path:
            try:
                self._template_image = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if self._template_image is None:
                    data = np.fromfile(template_path, dtype=np.uint8)
                    self._template_image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
                
                if self._template_image is None:
                    raise ToolException(f"无法加载模板图像: {template_path}")
                
                return True
            except Exception as e:
                self._logger.error(f"加载模板失败: {e}")
                return False
        
        return True
    
    def _run_impl(self):
        """执行灰度匹配"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        h, w = input_image.shape[:2]
        
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        template_path = self.get_param("template_path", "")
        
        if template_path:
            if not self._load_template():
                raise ToolException("无法加载模板")
        else:
            # 使用mixin的通用ROI获取方法
            roi = self.get_roi_from_params(w, h)
            if roi:
                roi_x, roi_y, roi_width, roi_height = roi
                self._template_image = gray_image[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width].copy()
                self._logger.info(f"使用ROI模板: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
            else:
                self._output_data = self._input_data.copy()
                raise ToolException("请设置模板图像路径或使用ROI绘制模板")
        
        if self._template_image is None or self._template_image.size == 0:
            self._output_data = self._input_data.copy()
            raise ToolException("未设置模板")
        
        match_mode_name = self.get_param("match_mode", "ccoeff_normed")
        min_score = self.get_param("min_score", 0.7)
        max_count = self.get_param("max_count", 10)
        
        match_mode = self.MATCH_MODE_MAP.get(match_mode_name, cv2.TM_CCOEFF_NORMED)
        
        result = cv2.matchTemplate(gray_image, self._template_image, match_mode)
        
        # 使用numpy向量化操作，大幅提高性能
        if match_mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            if match_mode == cv2.TM_SQDIFF:
                valid_mask = result < min_score * 1000000
            else:
                valid_mask = result < 1 - min_score
        elif match_mode in [cv2.TM_CCORR_NORMED, cv2.TM_CCOEFF_NORMED]:
            # 标准化模式直接使用min_score
            valid_mask = result >= min_score
        elif match_mode in [cv2.TM_CCORR, cv2.TM_CCOEFF]:
            # 非标准化模式返回原始值，需要根据最大值计算阈值
            max_val = result.max()
            threshold = max_val * min_score
            valid_mask = result >= threshold
        else:
            valid_mask = result >= min_score
        
        # 快速获取所有有效坐标
        y_indices, x_indices = np.where(valid_mask)
        
        if len(x_indices) == 0:
            filtered_locations = []
        else:
            # 获取对应分数并排序
            scores = result[y_indices, x_indices]
            if match_mode not in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                sorted_idx = np.argsort(scores)[::-1]
            else:
                sorted_idx = np.argsort(scores)
            
            # 构建排序后的位置列表
            sorted_x = x_indices[sorted_idx]
            sorted_y = y_indices[sorted_idx]
            sorted_scores = scores[sorted_idx]
            
            # 转换为列表格式
            locations = [(int(sorted_x[i]), int(sorted_y[i]), float(sorted_scores[i])) 
                        for i in range(len(sorted_x))]
            
            # 非极大值抑制
            filtered_locations = self._non_maximum_suppression(
                locations, 
                self._template_image.shape[1],
                self._template_image.shape[0]
            )[:max_count]
        
        # 保存结果
        self._result_data = ResultData()
        self._result_data.set_value("match_count", len(filtered_locations))
        self._result_data.set_value("matches", filtered_locations)
        
        # 保存第一个匹配位置
        if filtered_locations:
            best_match = filtered_locations[0]
            self._result_data.set_value("best_x", best_match[0])
            self._result_data.set_value("best_y", best_match[1])
            self._result_data.set_value("best_score", best_match[2])
            self._result_data.set_value("template_width", self._template_image.shape[1])
            self._result_data.set_value("template_height", self._template_image.shape[0])
        
        # 绘制结果
        output_image = input_image.copy()
        for x, y, score in filtered_locations:
            pt1 = (x, y)
            pt2 = (x + self._template_image.shape[1], y + self._template_image.shape[0])
            cv2.rectangle(output_image, pt1, pt2, (0, 255, 0), 2)
            cv2.putText(output_image, f"{score:.2f}", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
        
        self._logger.info(f"灰度匹配完成: 找到 {len(filtered_locations)} 个匹配")
    
    def _non_maximum_suppression(self, locations: List, width: int, height: int,
                                 overlap_thresh: float = 0.5) -> List:
        """非极大值抑制"""
        if not locations:
            return []
        
        filtered = []
        locations = sorted(locations, key=lambda x: x[2], reverse=True)
        
        while locations:
            # 保留第一个
            best = locations[0]
            filtered.append(best)
            
            # 移除重叠的
            remaining = []
            best_x, best_y, _ = best
            for loc in locations[1:]:
                x, y, score = loc
                # 计算重叠比例
                overlap_x = max(0, min(best_x + width, x + width) - max(best_x, x))
                overlap_y = max(0, min(best_y + height, y + height) - max(best_y, y))
                overlap_area = overlap_x * overlap_y
                total_area = width * height + width * height - overlap_area
                
                if overlap_area / total_area < overlap_thresh:
                    remaining.append(loc)
            
            locations = remaining
        
        return filtered
    
    def set_template(self, template_image: ImageData):
        """设置模板图像"""
        if template_image.is_gray:
            self._template_image = template_image.data.copy()
        else:
            self._template_image = cv2.cvtColor(template_image.data, cv2.COLOR_BGR2GRAY)
        self.set_param("template_path", "")


@ToolRegistry.register
class ShapeMatch(ROIToolMixin, VisionAlgorithmToolBase):
    """
    形状匹配工具
    
    使用边缘特征和Hu矩进行形状匹配，支持旋转匹配。
    
    参数说明：
    - min_score: 最小分数阈值 (0-1)
    - max_count: 最大匹配数量
    - angle_start: 起始角度
    - angle_end: 结束角度
    - canny_threshold1: Canny边缘检测低阈值
    - canny_threshold2: Canny边缘检测高阈值
    - roi: ROI模板区域（点击按钮绘制ROI作为模板）
    """
    
    tool_name = "形状匹配"
    tool_category = "Vision"
    tool_description = "使用边缘特征进行形状匹配"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "min_score": ToolParameter(
            name="最小分数",
            param_type="float",
            default=0.7,
            description="最小分数阈值",
            min_value=0.0,
            max_value=1.0
        ),
        "max_count": ToolParameter(
            name="最大数量",
            param_type="integer",
            default=10,
            description="最大匹配数量",
            min_value=1,
            max_value=100
        ),
        "angle_start": ToolParameter(
            name="起始角度",
            param_type="integer",
            default=-180,
            description="起始角度",
            min_value=-180,
            max_value=180
        ),
        "angle_end": ToolParameter(
            name="结束角度",
            param_type="integer",
            default=180,
            description="结束角度",
            min_value=-180,
            max_value=180
        ),
        "canny_threshold1": ToolParameter(
            name="边缘阈值1",
            param_type="integer",
            default=50,
            description="Canny低阈值",
            min_value=1,
            max_value=255
        ),
        "canny_threshold2": ToolParameter(
            name="边缘阈值2",
            param_type="integer",
            default=150,
            description="Canny高阈值",
            min_value=1,
            max_value=255
        ),
        "roi": ToolParameter(
            name="ROI模板",
            param_type="roi_rect",
            default=None,
            description="ROI模板区域（点击按钮绘制ROI作为模板）"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("min_score", 0.7)
        self.set_param("max_count", 10)
        self.set_param("angle_start", -180)
        self.set_param("angle_end", 180)
        self.set_param("canny_threshold1", 50)
        self.set_param("canny_threshold2", 150)
        self.set_param("roi", None)
        self._init_roi_params()  # 使用mixin的初始化方法
        self._template_contour = None
        self._template_hu_moments = None
        self._template_mask = None
    
    def _preprocess_image(self, image):
        """预处理图像为灰度图"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        return gray
    
    def _extract_contour(self, gray_image, threshold1=50, threshold2=150):
        """提取图像中的最大轮廓"""
        edges = cv2.Canny(gray_image, threshold1, threshold2)
        
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        if area < 100:
            return None
        
        return max_contour
    
    def _compute_hu_moments(self, contour):
        """计算轮廓的Hu矩"""
        moments = cv2.moments(contour)
        if moments['m00'] == 0:
            return None
        
        hu_moments = cv2.HuMoments(moments)
        for i in range(7):
            hu_moments[i] = -np.sign(hu_moments[i]) * np.log10(abs(hu_moments[i] + 1e-10))
        
        return hu_moments.flatten()
    
    def _hu_distance(self, hu1, hu2):
        """计算两个Hu矩之间的距离（越小越相似）"""
        diff = hu1 - hu2
        distance = np.sqrt(np.sum(diff ** 2))
        return distance
    
    def _rotate_contour(self, contour, center, angle):
        """旋转轮廓"""
        angle_rad = np.radians(angle)
        cos_val = np.cos(angle_rad)
        sin_val = np.sin(angle_rad)
        
        rotation_matrix = np.array([
            [cos_val, -sin_val],
            [sin_val, cos_val]
        ])
        
        centered = contour - center
        rotated = centered.dot(rotation_matrix) + center
        
        return rotated.astype(np.int32)
    
    def _match_contour_with_rotation(self, template_hu, target_contour, center, 
                                      angle_start, angle_end, angle_step):
        """在指定角度范围内匹配轮廓"""
        best_score = 0
        best_angle = 0
        best_distance = float('inf')
        
        for angle in range(angle_start, angle_end + 1, angle_step):
            rotated = self._rotate_contour(target_contour, center, angle)
            target_hu = self._compute_hu_moments(rotated)
            
            if target_hu is None:
                continue
            
            distance = self._hu_distance(template_hu, target_hu)
            
            if distance < best_distance:
                best_distance = distance
                best_angle = angle
        
        if best_distance == float('inf'):
            return 0, 0
        
        score = max(0, 1 - best_distance / 10)
        
        return score, best_angle
    
    def _run_impl(self):
        """执行形状匹配"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        h, w = input_image.shape[:2]
        gray_image = self._preprocess_image(input_image)
        
        min_score = self.get_param("min_score", 0.7)
        max_count = self.get_param("max_count", 10)
        angle_start = self.get_param("angle_start", -30)
        angle_end = self.get_param("angle_end", 30)
        angle_step = max(1, abs(int((angle_end - angle_start) / 20)))
        canny_t1 = self.get_param("canny_threshold1", 50)
        canny_t2 = self.get_param("canny_threshold2", 150)
        
        # 使用mixin的通用ROI获取方法
        template_roi = self.get_roi_from_params(w, h)
        if template_roi:
            roi_x, roi_y, roi_width, roi_height = template_roi
            self._logger.info(f"使用ROI模板: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
        
        # 如果没有模板轮廓，尝试从ROI区域提取
        if self._template_contour is None and template_roi is not None:
            roi_x, roi_y, roi_width, roi_height = template_roi
            roi_image = gray_image[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
            self._template_contour = self._extract_contour(roi_image, canny_t1, canny_t2)
            if self._template_contour is not None:
                self._template_hu_moments = self._compute_hu_moments(self._template_contour)
                self._logger.info(f"从ROI区域提取模板轮廓成功")
            else:
                self._template_hu_moments = None
        
        if self._template_contour is None:
            self._result_data = ResultData()
            self._result_data.set_value("match_count", 0)
            self._result_data.set_value("message", "请先设置模板图像或使用ROI绘制模板")
            self._output_data = self._input_data.copy()
            self._logger.warning("形状匹配失败: 未设置模板")
            return
        
        # 提取所有轮廓
        edges = cv2.Canny(gray_image, canny_t1, canny_t2)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤有效轮廓（面积大于100）
        valid_contours = [c for c in contours if cv2.contourArea(c) >= 100]
        
        if not valid_contours:
            self._result_data = ResultData()
            self._result_data.set_value("match_count", 0)
            self._result_data.set_value("message", "未检测到有效轮廓")
            self._output_data = self._input_data.copy()
            self._logger.warning("形状匹配失败: 未检测到有效轮廓")
            return
        
        # 对每个轮廓进行匹配
        matches = []
        for contour in valid_contours:
            target_center = tuple(contour.mean(axis=0).flatten().astype(int))
            score, best_angle = self._match_contour_with_rotation(
                self._template_hu_moments,
                contour,
                target_center,
                angle_start,
                angle_end,
                angle_step
            )
            
            if score >= min_score:
                x, y, cw, ch = cv2.boundingRect(contour)
                matches.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(cw),
                    "height": int(ch),
                    "score": float(score),
                    "angle": float(best_angle)
                })
        
        # 按分数排序
        matches.sort(key=lambda m: m["score"], reverse=True)
        
        # 限制数量
        matches = matches[:max_count]
        
        self._result_data = ResultData()
        self._result_data.set_value("match_count", len(matches))
        self._result_data.set_value("matches", matches)
        
        if matches:
            best = matches[0]
            self._result_data.set_value("best_x", best["x"])
            self._result_data.set_value("best_y", best["y"])
            self._result_data.set_value("best_score", best["score"])
            self._result_data.set_value("best_angle", best["angle"])
        
        output_image = input_image.copy()
        for match in matches:
            x, y, w, h = match["x"], match["y"], match["width"], match["height"]
            cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"{match['score']:.2f}"
            cv2.putText(output_image, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
        
        self._logger.info(f"形状匹配完成: 找到 {len(matches)} 个匹配")
    
    def set_template(self, template_image: ImageData):
        """设置模板图像"""
        if template_image is None:
            self._template_contour = None
            self._template_hu_moments = None
            return
        
        template_data = template_image.data
        gray = self._preprocess_image(template_data)
        
        self._template_contour = self._extract_contour(gray)
        
        if self._template_contour is not None:
            self._template_hu_moments = self._compute_hu_moments(self._template_contour)
            self._logger.info(f"模板已设置，轮廓面积: {cv2.contourArea(self._template_contour)}")
        else:
            self._template_hu_moments = None
            self._logger.warning("无法提取模板轮廓")


@ToolRegistry.register
class LineFind(ROIToolMixin, VisionAlgorithmToolBase):
    """
    直线查找工具
    
    在图像中查找直线。
    
    参数说明：
    - rho: 距离分辨率（像素）
    - theta: 角度分辨率（弧度）
    - threshold: 投票阈值
    - min_line_length: 最小直线长度
    - max_line_gap: 最大线段间隙
    """
    
    tool_name = "直线查找"
    tool_category = "Vision"
    tool_description = "在图像中查找直线"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "rho": ToolParameter(
            name="rho",
            param_type="integer",
            default=1,
            description="距离分辨率（像素）",
            min_value=1,
            max_value=100
        ),
        "theta": ToolParameter(
            name="角度分辨率",
            param_type="float",
            default=0.01745,
            description="角度分辨率（弧度）",
            min_value=0.001,
            max_value=0.1
        ),
        "threshold": ToolParameter(
            name="投票阈值",
            param_type="integer",
            default=100,
            description="投票阈值",
            min_value=1,
            max_value=1000
        ),
        "min_line_length": ToolParameter(
            name="最小长度",
            param_type="integer",
            default=50,
            description="最小直线长度",
            min_value=1,
            max_value=2000
        ),
        "max_line_gap": ToolParameter(
            name="最大间隙",
            param_type="integer",
            default=20,
            description="最大线段间隙",
            min_value=1,
            max_value=500
        ),
        "roi": ToolParameter(
            name="搜索区域",
            param_type="roi_rect",
            default=None,
            description="ROI搜索区域（点击按钮绘制ROI）"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("rho", 1)
        self.set_param("theta", 3.14159 / 180)
        self.set_param("threshold", 100)
        self.set_param("min_line_length", 50)
        self.set_param("max_line_gap", 20)
        self.set_param("roi", {}, param_type="roi_rect", description="点击按钮选择ROI区域")
        self._init_roi_params()  # 使用mixin的初始化方法
    
    def _run_impl(self):
        """执行直线查找"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        h, w = input_image.shape[:2]
        
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        rho = self.get_param("rho", 1)
        theta = self.get_param("theta", 3.14159 / 180)
        threshold = self.get_param("threshold", 100)
        min_line_length = self.get_param("min_line_length", 50)
        max_line_gap = self.get_param("max_line_gap", 20)
        
        # 使用mixin的通用ROI获取方法
        roi = self.get_roi_from_params(w, h)
        if roi:
            roi_x, roi_y, roi_width, roi_height = roi
        else:
            roi_x, roi_y, roi_width, roi_height = 0, 0, w, h
        
        self._logger.info(f"使用ROI区域: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
        
        # 在ROI区域内查找直线
        roi_gray = gray_image[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
        edges = cv2.Canny(roi_gray, 50, 150)
        lines = cv2.HoughLinesP(
            edges, rho, theta, threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )
        
        lines_list = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                lines_list.append({
                    "x1": int(x1 + roi_x), "y1": int(y1 + roi_y),
                    "x2": int(x2 + roi_x), "y2": int(y2 + roi_y)
                })
        
        self._result_data = ResultData()
        
        if lines_list:
            self._result_data.set_value("line_count", len(lines_list))
            self._result_data.set_value("lines", lines_list)
            
            output_image = input_image.copy()
            for line in lines_list:
                pt1 = (line["x1"], line["y1"])
                pt2 = (line["x2"], line["y2"])
                cv2.line(output_image, pt1, pt2, (0, 255, 0), 2)
        else:
            self._result_data.set_value("line_count", 0)
            output_image = input_image.copy()
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
        
        self._logger.info(f"直线查找完成: 找到 {self._result_data.get_value('line_count', 0)} 条直线")


@ToolRegistry.register
class CircleFind(ROIToolMixin, VisionAlgorithmToolBase):
    """
    圆查找工具
    
    在图像中查找圆。
    
    参数说明：
    - min_radius: 最小半径
    - max_radius: 最大半径
    - param1: Canny边缘检测高阈值
    - param2: 圆心投票阈值
    - min_dist: 圆心最小距离
    """
    
    tool_name = "圆查找"
    tool_category = "Vision"
    tool_description = "在图像中查找圆"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "min_radius": ToolParameter(
            name="最小半径",
            param_type="integer",
            default=10,
            description="最小半径",
            min_value=1,
            max_value=1000
        ),
        "max_radius": ToolParameter(
            name="最大半径",
            param_type="integer",
            default=100,
            description="最大半径",
            min_value=1,
            max_value=1000
        ),
        "param1": ToolParameter(
            name="边缘阈值",
            param_type="integer",
            default=100,
            description="Canny边缘高阈值",
            min_value=1,
            max_value=500
        ),
        "param2": ToolParameter(
            name="投票阈值",
            param_type="integer",
            default=50,
            description="圆心投票阈值",
            min_value=1,
            max_value=500
        ),
        "min_dist": ToolParameter(
            name="圆心间距",
            param_type="integer",
            default=20,
            description="圆心最小距离",
            min_value=1,
            max_value=500
        ),
        "roi": ToolParameter(
            name="搜索区域",
            param_type="roi_rect",
            default=None,
            description="ROI搜索区域（点击按钮绘制ROI）"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("min_radius", 10)
        self.set_param("max_radius", 100)
        self.set_param("param1", 100)
        self.set_param("param2", 50)
        self.set_param("min_dist", 20)
        self.set_param("roi", {}, param_type="roi_rect", description="点击按钮选择ROI区域")
        self._init_roi_params()  # 使用mixin的初始化方法
    
    def _run_impl(self):
        """执行圆查找"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        h, w = input_image.shape[:2]
        
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        min_radius = self.get_param("min_radius", 10)
        max_radius = self.get_param("max_radius", 100)
        param1 = self.get_param("param1", 100)
        param2 = self.get_param("param2", 50)
        min_dist = self.get_param("min_dist", 20)
        
        # 使用mixin的通用ROI获取方法
        roi = self.get_roi_from_params(w, h)
        if roi:
            roi_x, roi_y, roi_width, roi_height = roi
        else:
            roi_x, roi_y, roi_width, roi_height = 0, 0, w, h
        
        self._logger.info(f"使用ROI区域: x={roi_x}, y={roi_y}, width={roi_width}, height={roi_height}")
        
        # 在ROI区域内查找圆
        roi_gray = gray_image[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
        
        circles = cv2.HoughCircles(
            roi_gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        
        # 保存结果
        self._result_data = ResultData()
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype(int)
            circles_list = []
            for (x, y, r) in circles:
                circles_list.append({
                    "x": int(x + roi_x), "y": int(y + roi_y), "radius": int(r)
                })
            
            self._result_data.set_value("circle_count", len(circles_list))
            self._result_data.set_value("circles", circles_list)
            
            output_image = input_image.copy()
            
            for circle in circles_list:
                center = (circle["x"], circle["y"])
                radius = circle["radius"]
                cv2.circle(output_image, center, radius, (0, 255, 0), 2)
                cv2.circle(output_image, center, 3, (0, 0, 255), -1)
        else:
            self._result_data.set_value("circle_count", 0)
            output_image = input_image.copy()
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
        
        self._logger.info(f"圆查找完成: 找到 {self._result_data.get_value('circle_count', 0)} 个圆")
