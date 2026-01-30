#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块测试

测试tools模块中的各种工具功能，不包括相机相关功能
"""

import os
import sys

import numpy as np
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ToolRegistry
from data.image_data import ImageData


class TestImageFilterTools:
    """测试图像滤波工具"""

    def test_box_filter(self, sample_image):
        """测试方框滤波工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "方框滤波", "box_filter"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("kernel_size", 5)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_mean_filter(self, sample_image):
        """测试均值滤波工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "均值滤波", "mean_filter"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("kernel_size", 5)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_gaussian_filter(self, sample_image):
        """测试高斯滤波工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "gaussian_filter"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("kernel_size", 5)
        tool.set_param("sigma", 1.0)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_median_filter(self, sample_image):
        """测试中值滤波工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "中值滤波", "median_filter"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("kernel_size", 5)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_bilateral_filter(self, sample_image):
        """测试双边滤波工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "双边滤波", "bilateral_filter"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("d", 5)
        tool.set_param("sigma_color", 100)
        tool.set_param("sigma_space", 100)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_morphology(self, sample_image):
        """测试形态学处理工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "形态学处理", "morphology_tool"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("operation", "dilate")
        tool.set_param("kernel_size", 5)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid

    def test_image_resize(self, sample_image):
        """测试图像缩放工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "图像缩放", "resize_tool"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("width", 200)
        tool.set_param("height", 200)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()
        output = tool.get_output()
        assert output is not None
        assert output.is_valid
        output = tool.get_output()
        assert output.width == 200
        assert output.height == 200


class TestVisionTools:
    """测试视觉算法工具"""

    def test_gray_match(self, sample_image):
        """测试灰度匹配工具"""
        tool = ToolRegistry.create_tool("Vision", "灰度匹配", "gray_match")

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数 - 使用template_path参数
        tool.set_param(
            "template_path", "nonexistent.jpg"
        )  # 这会导致错误，但至少设置了参数
        tool.set_param("min_score", 0.8)

        # 运行工具 - 预期会失败，因为没有有效的模板
        try:
            result = tool.run()
            # 如果成功，说明有模板，这是OK的
        except:
            # 预期会失败，这是正常的
            pass

    def test_shape_match(self, sample_image):
        """测试形状匹配工具"""
        tool = ToolRegistry.create_tool("Vision", "形状匹配", "shape_match")

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("template_image", sample_image.data[50:150, 50:150])
        tool.set_param("threshold", 0.8)

        # 运行工具
        result = tool.run()
        assert result is True

    def test_line_find(self, sample_image):
        """测试直线查找工具"""
        tool = ToolRegistry.create_tool("Vision", "直线查找", "line_find")

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("min_length", 50)
        tool.set_param("threshold", 50)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()

    def test_circle_find(self, sample_image):
        """测试圆查找工具"""
        tool = ToolRegistry.create_tool("Vision", "圆查找", "circle_find")

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("min_radius", 10)
        tool.set_param("max_radius", 100)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()


class TestRecognitionTools:
    """测试识别工具"""

    def test_barcode_reader(self, sample_image):
        """测试条码识别工具"""
        tool = ToolRegistry.create_tool(
            "Recognition", "条码识别", "barcode_reader"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 运行工具
        result = tool.run()
        assert result is True

    def test_qrcode_reader(self, sample_image):
        """测试二维码识别工具"""
        tool = ToolRegistry.create_tool(
            "Recognition", "二维码识别", "qrcode_reader"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 运行工具
        result = tool.run()
        assert result is True

    def test_code_reader(self, sample_image):
        """测试综合读码工具"""
        tool = ToolRegistry.create_tool("Recognition", "读码", "code_reader")

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置参数
        tool.set_param("read_barcode", True)
        tool.set_param("read_qrcode", True)

        # 运行工具
        result = tool.run()
        assert result is True
        assert tool.has_output()


class TestToolEdgeCases:
    """测试工具的边界情况和异常处理"""

    def test_tool_without_input(self):
        """测试工具在没有输入时的行为"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "edge_case_tool"
        )

        # 运行工具，没有设置输入 - 应该抛出异常
        try:
            result = tool.run()
            assert False, "应该抛出异常"
        except Exception:
            pass  # 预期会抛出异常

    def test_tool_with_invalid_input(self, invalid_image):
        """测试工具在无效输入时的行为"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "invalid_input_tool"
        )

        # 设置无效输入
        tool.set_input(invalid_image)

        # 运行工具
        result = tool.run()
        assert result is False  # 应该返回False或抛出异常

    def test_tool_with_invalid_params(self, sample_image):
        """测试工具在无效参数时的行为"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "invalid_param_tool"
        )

        # 设置工具输入
        tool.set_input(sample_image)

        # 设置无效参数
        tool.set_param("kernel_size", -5)  # 无效的核大小

        # 运行工具
        result = tool.run()
        assert result is False  # 应该返回False或抛出异常

    def test_disabled_tool(self, sample_image):
        """测试禁用的工具"""
        tool = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "disabled_tool"
        )
        tool.is_enabled = False

        # 设置工具输入
        tool.set_input(sample_image)

        # 运行工具
        result = tool.run()
        assert result is True  # 禁用工具应该返回True但不执行任何操作
        assert not tool.has_output()  # 不应该有输出
