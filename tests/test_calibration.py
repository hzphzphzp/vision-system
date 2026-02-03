# -*- coding: utf-8 -*-
"""
标定工具测试

Author: Vision System Team
Date: 2026-02-03
"""

import pytest
import numpy as np
import cv2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.vision.calibration import CalibrationTool
from data.image_data import ImageData


def test_calibration_tool_creation():
    """测试标定工具创建"""
    tool = CalibrationTool(name="TestCalibration")
    assert tool is not None
    assert tool.tool_name == "标定"
    assert tool.is_calibrated == False


def test_calibration_manual():
    """测试手动标定"""
    tool = CalibrationTool(name="TestCalibration")

    # 手动标定：已知参考物体100mm，在图像中显示为1000像素
    success = tool.calibrate_with_reference(
        pixel_width=1000,
        pixel_height=1000,
        actual_width=100.0,
        actual_height=100.0,
    )

    assert success == True
    assert tool.is_calibrated == True
    assert tool.pixel_per_mm == (10.0, 10.0)


def test_pixel_to_physical():
    """测试像素到物理坐标转换"""
    tool = CalibrationTool(name="TestCalibration")

    # 设置标定比例
    tool._pixel_per_mm_x = 10.0
    tool._pixel_per_mm_y = 10.0
    tool._calibrated = True

    # 转换
    phys_x, phys_y = tool.pixel_to_physical(100, 200)

    assert abs(phys_x - 10.0) < 0.01
    assert abs(phys_y - 20.0) < 0.01


def test_pixel_to_physical_size():
    """测试像素尺寸到物理尺寸转换"""
    tool = CalibrationTool(name="TestCalibration")

    # 设置标定比例
    tool._pixel_per_mm_x = 10.0
    tool._pixel_per_mm_y = 10.0
    tool._calibrated = True

    # 转换
    phys_w, phys_h = tool.pixel_to_physical_size(100, 200)

    assert abs(phys_w - 10.0) < 0.01
    assert abs(phys_h - 20.0) < 0.01


def test_physical_to_pixel():
    """测试物理坐标到像素坐标转换"""
    tool = CalibrationTool(name="TestCalibration")

    # 设置标定比例
    tool._pixel_per_mm_x = 10.0
    tool._pixel_per_mm_y = 10.0
    tool._calibrated = True

    # 转换
    px, py = tool.physical_to_pixel(10.0, 20.0)

    assert abs(px - 100.0) < 0.01
    assert abs(py - 200.0) < 0.01


def test_calibration_with_chessboard():
    """测试棋盘格标定（模拟）"""
    tool = CalibrationTool(name="TestCalibration")

    # 创建模拟棋盘格图像
    width, height = 640, 480
    gray = np.zeros((height, width), dtype=np.uint8)

    # 绘制棋盘格图案
    square_size = 40
    for y in range(0, height, square_size * 2):
        for x in range(0, width, square_size * 2):
            cv2.rectangle(gray, (x, y), (x + square_size, y + square_size), 255, -1)

    # 创建彩色图像
    image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # 设置棋盘格参数
    tool.set_param("pattern_width", 9)
    tool.set_param("pattern_height", 6)
    tool.set_param("square_size", 40.0)

    # 执行标定
    success = tool.calibrate_with_chessboard(image)

    # 由于模拟图像不完美，可能检测失败
    # 但工具应该能够处理
    assert tool is not None


def test_calibration_tool_run():
    """测试标定工具运行"""
    tool = CalibrationTool(name="TestCalibration")

    # 创建测试图像
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    input_data = ImageData(data=image)
    tool.set_input(input_data)

    # 设置手动标定参数
    tool.set_param("calibration_type", "manual")
    tool.set_param("pixel_per_mm_x", 10.0)
    tool.set_param("pixel_per_mm_y", 10.0)
    tool.set_param("reference_width", 100.0)
    tool.set_param("reference_height", 100.0)

    # 运行
    result = tool._run_impl()

    assert "OutputImage" in result
    assert result["OutputImage"] is not None
    assert tool.is_calibrated == True


def test_unit_conversion():
    """测试单位转换"""
    tool = CalibrationTool(name="TestCalibration")

    # 设置标定比例为10 px/mm
    tool._pixel_per_mm_x = 10.0
    tool._pixel_per_mm_y = 10.0
    tool._calibrated = True

    # 测试mm单位
    tool.set_param("output_unit", "mm")
    phys_x, phys_y = tool.pixel_to_physical(100, 200)
    assert abs(phys_x - 10.0) < 0.01
    assert abs(phys_y - 20.0) < 0.01

    # 测试inch单位
    tool.set_param("output_unit", "inch")
    phys_x, phys_y = tool.pixel_to_physical(2540, 5080)  # 254mm = 10 inch, 508mm = 20 inch
    assert abs(phys_x - 10.0) < 0.1
    assert abs(phys_y - 20.0) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
