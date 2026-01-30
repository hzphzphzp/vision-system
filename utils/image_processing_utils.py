#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理通用工具函数

提供图像预处理、结果绘制、轮廓分析等通用功能。

Author: Vision System Team
Date: 2026-01-30
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    预处理图像为灰度图
    
    Args:
        image: 输入图像
    
    Returns:
        灰度图像
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image.copy()


def resize_image(image: np.ndarray, scale: float) -> np.ndarray:
    """
    调整图像大小
    
    Args:
        image: 输入图像
        scale: 缩放比例
    
    Returns:
        调整大小后的图像
    """
    new_width = int(image.shape[1] * scale)
    new_height = int(image.shape[0] * scale)
    return cv2.resize(
        image, (new_width, new_height), interpolation=cv2.INTER_LINEAR
    )


def calculate_iou(box1: Dict[str, int], box2: Dict[str, int]) -> float:
    """
    计算两个边界框的IOU
    
    Args:
        box1: 第一个边界框 {x, y, width, height}
        box2: 第二个边界框 {x, y, width, height}
    
    Returns:
        IOU值
    """
    x1 = max(box1["x"], box2["x"])
    y1 = max(box1["y"], box2["y"])
    x2 = min(box1["x"] + box1["width"], box2["x"] + box2["width"])
    y2 = min(box1["y"] + box1["height"], box2["y"] + box2["height"])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = box1["width"] * box1["height"]
    area2 = box2["width"] * box2["height"]
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def non_maximum_suppression(
    locations: List[Tuple[int, int, float]],
    width: int,
    height: int,
    overlap_thresh: float = 0.5
) -> List[Tuple[int, int, float]]:
    """
    非极大值抑制
    
    Args:
        locations: 位置列表 [(x, y, score), ...]
        width: 目标宽度
        height: 目标高度
        overlap_thresh: 重叠阈值
    
    Returns:
        过滤后的位置列表
    """
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
            overlap_x = max(
                0, min(best_x + width, x + width) - max(best_x, x)
            )
            overlap_y = max(
                0, min(best_y + height, y + height) - max(best_y, y)
            )
            overlap_area = overlap_x * overlap_y
            total_area = width * height + width * height - overlap_area
            
            if overlap_area / total_area < overlap_thresh:
                remaining.append(loc)
        
        locations = remaining
    
    return filtered


def remove_duplicate_defects(
    defects: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    去除重复缺陷
    
    Args:
        defects: 缺陷列表
    
    Returns:
        去重后的缺陷列表
    """
    if len(defects) <= 1:
        return defects
    
    unique_defects = []
    for i, defect1 in enumerate(defects):
        duplicate = False
        for defect2 in unique_defects:
            # 计算IOU
            iou = calculate_iou(
                defect1["location"], defect2["location"]
            )
            if iou > 0.5:
                duplicate = True
                break
        if not duplicate:
            unique_defects.append(defect1)
    
    return unique_defects


def draw_detection_result(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    label_key: str = "type",
    score_key: str = "confidence",
    location_key: str = "location"
) -> np.ndarray:
    """
    绘制检测结果
    
    Args:
        image: 输入图像
        detections: 检测结果列表
        label_key: 标签键名
        score_key: 分数键名
        location_key: 位置键名
    
    Returns:
        绘制后的图像
    """
    output_image = image.copy()
    
    for detection in detections:
        location = detection[location_key]
        x, y, w, h = (
            location["x"],
            location["y"],
            location["width"],
            location["height"]
        )
        
        # 随机颜色
        color = tuple(np.random.randint(0, 255, 3).tolist())
        
        # 绘制边界框
        cv2.rectangle(output_image, (x, y), (x + w, y + h), color, 2)
        
        # 绘制标签
        label = f"{detection[label_key]}: {detection[score_key]:.2f}"
        cv2.putText(
            output_image,
            label,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )
    
    return output_image


def draw_matches(
    image: np.ndarray,
    matches: List[Tuple[int, int, float]],
    template_width: int,
    template_height: int
) -> np.ndarray:
    """
    绘制匹配结果
    
    Args:
        image: 输入图像
        matches: 匹配位置列表 [(x, y, score), ...]
        template_width: 模板宽度
        template_height: 模板高度
    
    Returns:
        绘制后的图像
    """
    output_image = image.copy()
    
    for x, y, score in matches:
        pt1 = (x, y)
        pt2 = (
            x + template_width,
            y + template_height,
        )
        cv2.rectangle(output_image, pt1, pt2, (0, 255, 0), 2)
        cv2.putText(
            output_image,
            f"{score:.2f}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )
    
    return output_image


def draw_lines(
    image: np.ndarray,
    lines: List[Dict[str, int]]
) -> np.ndarray:
    """
    绘制直线
    
    Args:
        image: 输入图像
        lines: 直线列表 [{x1, y1, x2, y2}, ...]
    
    Returns:
        绘制后的图像
    """
    output_image = image.copy()
    
    for line in lines:
        pt1 = (line["x1"], line["y1"])
        pt2 = (line["x2"], line["y2"])
        cv2.line(output_image, pt1, pt2, (0, 255, 0), 2)
    
    return output_image


def draw_circles(
    image: np.ndarray,
    circles: List[Dict[str, int]]
) -> np.ndarray:
    """
    绘制圆
    
    Args:
        image: 输入图像
        circles: 圆列表 [{x, y, radius}, ...]
    
    Returns:
        绘制后的图像
    """
    output_image = image.copy()
    
    for circle in circles:
        center = (circle["x"], circle["y"])
        radius = circle["radius"]
        cv2.circle(output_image, center, radius, (0, 255, 0), 2)
        cv2.circle(output_image, center, 3, (0, 0, 255), -1)
    
    return output_image


def extract_contour(
    gray_image: np.ndarray,
    threshold1: int = 50,
    threshold2: int = 150
) -> Optional[np.ndarray]:
    """
    提取图像中的最大轮廓
    
    Args:
        gray_image: 灰度图像
        threshold1: Canny低阈值
        threshold2: Canny高阈值
    
    Returns:
        最大轮廓或None
    """
    edges = cv2.Canny(gray_image, threshold1, threshold2)
    
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    edges = cv2.erode(edges, kernel, iterations=1)
    
    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    if not contours:
        return None
    
    max_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(max_contour)
    
    if area < 100:
        return None
    
    return max_contour


def compute_hu_moments(contour: np.ndarray) -> Optional[np.ndarray]:
    """
    计算轮廓的Hu矩
    
    Args:
        contour: 轮廓
    
    Returns:
        Hu矩或None
    """
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None
    
    hu_moments = cv2.HuMoments(moments)
    for i in range(7):
        hu_moments[i] = -np.sign(hu_moments[i]) * np.log10(
            abs(hu_moments[i] + 1e-10)
        )
    
    return hu_moments.flatten()


def rotate_contour(
    contour: np.ndarray,
    center: Tuple[int, int],
    angle: float
) -> np.ndarray:
    """
    旋转轮廓
    
    Args:
        contour: 轮廓
        center: 旋转中心
        angle: 旋转角度（度）
    
    Returns:
        旋转后的轮廓
    """
    angle_rad = np.radians(angle)
    cos_val = np.cos(angle_rad)
    sin_val = np.sin(angle_rad)
    
    rotation_matrix = np.array([[cos_val, -sin_val], [sin_val, cos_val]])
    
    centered = contour - center
    rotated = centered.dot(rotation_matrix) + center
    
    return rotated.astype(np.int32)


def classify_defect(
    contour: np.ndarray,
    area: float,
    circularity: float,
    aspect_ratio: float
) -> str:
    """
    分类缺陷类型
    
    Args:
        contour: 轮廓
        area: 面积
        circularity: 圆形度
        aspect_ratio: 长宽比
    
    Returns:
        缺陷类型
    """
    if aspect_ratio > 3.0:
        # 狭长形状 -> 划痕
        return "scratch"
    elif circularity > 0.7:
        # 圆形 -> 污点或异物
        if area < 500:
            return "stain"
        else:
            return "foreign_matter"
    elif 0.3 < circularity < 0.7:
        # 不规则形状 -> 凹痕
        return "dent"
    else:
        # 其他形状 -> 裂纹或材料缺失
        if area > 1000:
            return "crack"
        else:
            return "missing_material"


def calculate_confidence(
    contour: np.ndarray,
    area: float,
    circularity: float
) -> float:
    """
    计算缺陷检测置信度
    
    Args:
        contour: 轮廓
        area: 面积
        circularity: 圆形度
    
    Returns:
        置信度 (0-1)
    """
    # 基于面积和形状的置信度计算
    area_score = min(area / 1000, 1.0)
    shape_score = circularity if circularity < 1.0 else 1.0
    
    # 综合置信度
    confidence = area_score * 0.6 + shape_score * 0.4
    return round(confidence, 2)


def get_defect_name(defect_type: str) -> str:
    """
    获取缺陷类型的中文名称
    
    Args:
        defect_type: 缺陷类型
    
    Returns:
        中文名称
    """
    name_map = {
        "scratch": "划痕",
        "dent": "凹痕",
        "stain": "污点",
        "foreign_matter": "异物",
        "crack": "裂纹",
        "missing_material": "材料缺失",
    }
    return name_map.get(defect_type, defect_type)
