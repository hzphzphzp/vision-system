#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模块测试

测试data.image_data模块中的ImageData和ResultData类
"""

import pytest
import numpy as np
from data.image_data import ImageData, ResultData


class TestImageData:
    """测试ImageData类"""
    
    def test_image_creation(self, sample_image):
        """测试图像数据创建"""
        assert sample_image is not None
        assert sample_image.data is not None
        assert sample_image.width > 0
        assert sample_image.height > 0
        assert sample_image.is_valid
    
    def test_gray_image_creation(self, sample_gray_image):
        """测试灰度图像数据创建"""
        assert sample_gray_image is not None
        assert sample_gray_image.data is not None
        assert sample_gray_image.width > 0
        assert sample_gray_image.height > 0
        assert sample_gray_image.is_valid
    
    def test_invalid_image(self, invalid_image):
        """测试无效图像数据"""
        assert invalid_image is not None
        assert invalid_image.data is None
        assert not invalid_image.is_valid
    
    def test_image_copy(self, sample_image):
        """测试图像数据复制"""
        copied_image = sample_image.copy()
        assert copied_image is not sample_image  # 不同对象
        assert copied_image.width == sample_image.width
        assert copied_image.height == sample_image.height
        assert np.array_equal(copied_image.data, sample_image.data)
    
    def test_image_properties(self, sample_image):
        """测试图像数据属性"""
        original_shape = sample_image.data.shape
        assert sample_image.shape == original_shape
        assert sample_image.channels == original_shape[2]
    
    def test_gray_image_properties(self, sample_gray_image):
        """测试灰度图像数据属性"""
        original_shape = sample_gray_image.data.shape
        assert sample_gray_image.shape == original_shape
        assert sample_gray_image.channels == 1  # 灰度图像只有1个通道
    
    def test_image_set_data(self):
        """测试设置图像数据"""
        image = ImageData()
        assert not image.is_valid
        
        # 设置新数据
        new_data = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        image.set_data(new_data)
        assert image.is_valid
        assert image.width == 200
        assert image.height == 200
        assert image.channels == 3


class TestResultData:
    """测试ResultData类"""
    
    def test_result_creation(self):
        """测试结果数据创建"""
        result = ResultData()
        assert result is not None
        assert result.is_valid
        assert result.status is True
        assert result.message == "Success"
    
    def test_result_set_value(self):
        """测试设置结果值"""
        result = ResultData()
        result.set_value("count", 10)
        assert result.get_value("count") == 10
        
        # 设置多个值
        result.set_value("accuracy", 0.95)
        result.set_value("status", True)
        assert result.get_value("accuracy") == 0.95
        assert result.get_value("status") == True
    
    def test_result_get_all_values(self):
        """测试获取所有结果值"""
        result = ResultData()
        result.set_value("count", 10)
        result.set_value("accuracy", 0.95)
        
        all_values = result.get_all_values()
        assert "count" in all_values
        assert "accuracy" in all_values
        assert all_values["count"] == 10
        assert all_values["accuracy"] == 0.95
    
    def test_result_status(self):
        """测试结果状态"""
        result = ResultData()
        assert result.status is True
        
        # 设置失败状态
        result.status = False
        result.message = "Failed"
        assert result.status is False
        assert result.message == "Failed"
    
    def test_result_invalid(self):
        """测试无效结果"""
        result = ResultData()
        result.status = False
        assert not result.is_valid
    
    def test_result_copy(self):
        """测试结果数据复制"""
        original = ResultData()
        original.set_value("count", 10)
        original.set_value("accuracy", 0.95)
        
        copied = original.copy()
        assert copied is not original  # 不同对象
        assert copied.get_value("count") == original.get_value("count")
        assert copied.get_value("accuracy") == original.get_value("accuracy")
        assert copied.status == original.status
        assert copied.message == original.message
