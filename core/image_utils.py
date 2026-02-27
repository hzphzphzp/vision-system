#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像工具模块

提供高效的图像加载、处理和转换功能。
优先使用Pillow-SIMD进行加速。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from typing import Optional, Tuple, Union

import cv2
import numpy as np

PIL_AVAILABLE = False
PIL_SIMD = False
Image = None

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
    Image = PILImage
    PIL_SIMD = hasattr(PILImage, 'FAST_MOSAIC')
except ImportError:
    pass


def load_image_fast(path: str, mode: str = "RGB") -> Optional[np.ndarray]:
    """快速加载图像

    Args:
        path: 图像路径
        mode: 加载模式 ('RGB', 'BGR', 'GRAY')

    Returns:
        图像数组
    """
    if not os.path.exists(path):
        return None

    if PIL_AVAILABLE:
        try:
            with PILImage.open(path) as img:
                if mode == "GRAY":
                    img = img.convert("L")
                else:
                    img = img.convert("RGB")
                img_array = np.array(img)
                if mode == "BGR":
                    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                return img_array
        except Exception:
            pass

    img = cv2.imread(path)
    if img is None:
        return None

    if mode == "RGB":
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif mode == "GRAY":
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def resize_image_fast(image: Union[np.ndarray, str],
                     width: int, height: int,
                     interpolation: str = "LANCZOS") -> np.ndarray:
    """快速调整图像大小

    Args:
        image: 图像数组或路径
        width: 目标宽度
        height: 目标高度
        interpolation: 插值方法 ('LANCZOS', 'BILINEAR', 'BICUBIC', 'NEAREST')

    Returns:
        调整大小后的图像
    """
    if isinstance(image, str):
        if PIL_AVAILABLE:
            try:
                with PILImage.open(image) as img:
                    img = img.resize((width, height), PILImage.LANCZOS)
                    return np.array(img)
            except Exception:
                pass
        else:
            image = cv2.imread(image)
            if image is None:
                return None

    if PIL_AVAILABLE and isinstance(image, np.ndarray):
        try:
            if len(image.shape) == 3:
                img = PILImage.fromarray(image)
            else:
                img = PILImage.fromarray(image)
            img_resized = img.resize((width, height), PILImage.LANCZOS)
            return np.array(img_resized)
        except Exception:
            pass

    interp_map = {
        "LANCZOS": cv2.INTER_LANCZOS4,
        "BILINEAR": cv2.INTER_LINEAR,
        "BICUBIC": cv2.INTER_CUBIC,
        "NEAREST": cv2.INTER_NEAREST,
    }
    return cv2.resize(image, (width, height), interpolation=interp_map.get(interpolation, cv2.INTER_LANCZOS4))


def convert_color_fast(image: np.ndarray, target: str = "RGB") -> np.ndarray:
    """快速色彩空间转换

    Args:
        image: 输入图像
        target: 目标色彩空间 ('RGB', 'BGR', 'GRAY')

    Returns:
        转换后的图像
    """
    if PIL_AVAILABLE:
        try:
            if len(image.shape) == 2:
                if target == "GRAY":
                    return image
                img = PILImage.fromarray(image).convert("RGB")
                result = np.array(img)
            else:
                img = PILImage.fromarray(image)
                result = np.array(img)

            if target == "BGR":
                return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            elif target == "GRAY":
                return cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
            return result
        except Exception:
            pass

    if target == "BGR":
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if len(image.shape) == 3 else image
    elif target == "GRAY":
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image


def apply_filter_fast(image: np.ndarray, filter_type: str = "BLUR") -> np.ndarray:
    """快速应用滤镜

    Args:
        image: 输入图像
        filter_type: 滤镜类型 ('BLUR', 'SHARPEN', 'EDGE', 'SMOOTH')

    Returns:
        处理后的图像
    """
    if PIL_AVAILABLE:
        try:
            img = PILImage.fromarray(image)
            if filter_type == "BLUR":
                img = img.filter(PILImage.BLUR)
            elif filter_type == "SHARPEN":
                img = img.filter(PILImage.SHARPEN)
            elif filter_type == "SMOOTH":
                img = img.filter(PILImage.SMOOTH)
            elif filter_type == "EDGE":
                img = img.filter(PILImage.FIND_EDGES)
            return np.array(img)
        except Exception:
            pass

    if filter_type == "BLUR":
        return cv2.blur(image, (5, 5))
    elif filter_type == "SHARPEN":
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)
    elif filter_type == "SMOOTH":
        return cv2.bilateralFilter(image, 9, 75, 75)
    elif filter_type == "EDGE":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return cv2.Canny(gray, 50, 150)
    return image


def save_image_fast(image: np.ndarray, path: str, quality: int = 95) -> bool:
    """快速保存图像

    Args:
        image: 图像数组 (BGR格式)
        path: 保存路径
        quality: JPEG质量 (1-100)

    Returns:
        是否成功
    """
    try:
        if PIL_AVAILABLE:
            # 检查图像是否为BGR格式（3通道且不是灰度）
            if len(image.shape) == 3 and image.shape[2] == 3:
                # 将BGR转换为RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img = PILImage.fromarray(image)
            img.save(path, quality=quality, optimize=True)
            return True
    except Exception:
        pass

    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        return cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imwrite(path, image)


def thumbnail_fast(image: np.ndarray, max_size: Tuple[int, int],
                  maintain_aspect: bool = True) -> np.ndarray:
    """快速生成缩略图

    Args:
        image: 输入图像
        max_size: 最大尺寸 (width, height)
        maintain_aspect: 是否保持宽高比

    Returns:
        缩略图
    """
    if PIL_AVAILABLE:
        try:
            img = PILImage.fromarray(image)
            if maintain_aspect:
                img.thumbnail(max_size, PILImage.LANCZOS)
            else:
                img = img.resize(max_size, PILImage.LANCZOS)
            return np.array(img)
        except Exception:
            pass

    h, w = image.shape[:2]
    max_w, max_h = max_size

    if maintain_aspect:
        ratio = min(max_w / w, max_h / h)
        new_w, new_h = int(w * ratio), int(h * ratio)
    else:
        new_w, new_h = max_w, max_h

    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """裁剪图像

    Args:
        image: 输入图像
        x, y: 裁剪起始坐标
        width, height: 裁剪尺寸

    Returns:
        裁剪后的图像
    """
    h, w = image.shape[:2]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    width = min(width, w - x)
    height = min(height, h - y)
    return image[y:y + height, x:x + width]


def rotate_image_fast(image: np.ndarray, angle: float,
                     expand: bool = True) -> np.ndarray:
    """快速旋转图像

    Args:
        image: 输入图像
        angle: 旋转角度（度）
        expand: 是否扩展画布以容纳整个图像

    Returns:
        旋转后的图像
    """
    if PIL_AVAILABLE:
        try:
            img = PILImage.fromarray(image)
            img = img.rotate(angle, expand=expand, resample=PILImage.BICUBIC)
            return np.array(img)
        except Exception:
            pass

    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    if expand:
        cos = np.abs(matrix[0, 0])
        sin = np.abs(matrix[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        matrix[0, 2] += (new_w / 2) - center[0]
        matrix[1, 2] += (new_h / 2) - center[1]
        return cv2.warpAffine(image, matrix, (new_w, new_h), flags=cv2.INTER_CUBIC)

    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC)


def get_image_info(path: str) -> Optional[dict]:
    """获取图像信息

    Args:
        path: 图像路径

    Returns:
        包含图像信息的字典
    """
    if not os.path.exists(path):
        return None

    if PIL_AVAILABLE:
        try:
            with PILImage.open(path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": os.path.getsize(path),
                }
        except Exception:
            pass

    img = cv2.imread(path)
    if img is None:
        return None

    return {
        "width": img.shape[1],
        "height": img.shape[0],
        "channels": img.shape[2] if len(img.shape) > 2 else 1,
        "size_bytes": os.path.getsize(path),
    }
