#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外观检测工具测试

测试外观检测和表面缺陷检测功能。

Author: Vision System Team
Date: 2026-01-30
"""

import os
import sys
import unittest

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.image_data import ImageData
from tools.appearance_detection import (
    AppearanceDetector,
    SurfaceDefectDetector,
)
from utils.exceptions import ToolException


class TestAppearanceDetection(unittest.TestCase):
    """外观检测工具测试"""

    def setUp(self):
        """设置测试环境"""
        # 创建测试图像
        self.test_image = self._create_test_image()
        self.image_data = ImageData(self.test_image)

    def _create_test_image(self) -> np.ndarray:
        """创建测试图像"""
        # 创建一个带有缺陷的测试图像
        image = np.ones((480, 640, 3), dtype=np.uint8) * 255

        # 添加一些模拟缺陷

        # 1. 划痕（红色）
        cv2.line(image, (100, 100), (300, 100), (0, 0, 255), 2)

        # 2. 污点（蓝色）
        cv2.circle(image, (400, 200), 10, (255, 0, 0), -1)

        # 3. 凹痕（绿色）
        cv2.rectangle(image, (200, 200), (250, 250), (0, 255, 0), 2)

        # 4. 异物（黄色）
        cv2.circle(image, (500, 300), 20, (0, 255, 255), -1)

        return image

    def test_appearance_detector_initialization(self):
        """测试外观检测器初始化"""
        detector = AppearanceDetector()
        self.assertEqual(detector.tool_name, "外观检测")
        self.assertEqual(detector.tool_category, "Vision")
        self.assertTrue(detector.is_enabled)

    def test_appearance_detector_params(self):
        """测试外观检测器参数设置"""
        detector = AppearanceDetector()

        # 测试默认参数
        self.assertEqual(detector.get_param("detection_type"), "all")
        self.assertEqual(detector.get_param("defect_type"), "all")
        self.assertEqual(detector.get_param("threshold"), 0.5)
        self.assertEqual(detector.get_param("min_area"), 100)
        self.assertEqual(detector.get_param("max_area"), 10000)

        # 测试参数设置
        detector.set_param("threshold", 0.7)
        self.assertEqual(detector.get_param("threshold"), 0.7)

    def test_appearance_detector_execution(self):
        """测试外观检测器执行"""
        detector = AppearanceDetector()
        detector.set_input(self.image_data)

        # 执行检测
        result = detector.run()
        self.assertTrue(result)

        # 检查结果
        defect_count = detector.get_result("defect_count")
        self.assertGreaterEqual(defect_count, 0)

        defects = detector.get_result("defects")
        self.assertIsInstance(defects, list)

    def test_appearance_detector_no_input(self):
        """测试外观检测器无输入情况"""
        detector = AppearanceDetector()

        # 无输入应该抛出异常
        with self.assertRaises(ToolException):
            detector.run()

    def test_surface_defect_detector_initialization(self):
        """测试表面缺陷检测器初始化"""
        detector = SurfaceDefectDetector()
        self.assertEqual(detector.tool_name, "表面缺陷检测")
        self.assertEqual(detector.tool_category, "Vision")
        self.assertTrue(detector.is_enabled)

    def test_surface_defect_detector_params(self):
        """测试表面缺陷检测器参数设置"""
        detector = SurfaceDefectDetector()

        # 测试默认参数
        self.assertEqual(detector.get_param("sensitivity"), 0.6)
        self.assertEqual(detector.get_param("min_size"), 50)
        self.assertEqual(detector.get_param("max_size"), 5000)
        self.assertTrue(detector.get_param("use_multiscale"))
        self.assertTrue(detector.get_param("adaptive_threshold"))

        # 测试参数设置
        detector.set_param("sensitivity", 0.8)
        self.assertEqual(detector.get_param("sensitivity"), 0.8)

    def test_surface_defect_detector_execution(self):
        """测试表面缺陷检测器执行"""
        detector = SurfaceDefectDetector()
        detector.set_input(self.image_data)

        # 执行检测
        result = detector.run()
        self.assertTrue(result)

        # 检查结果
        defect_count = detector.get_result("defect_count")
        self.assertGreaterEqual(defect_count, 0)

        defects = detector.get_result("defects")
        self.assertIsInstance(defects, list)

    def test_surface_defect_detector_no_input(self):
        """测试表面缺陷检测器无输入情况"""
        detector = SurfaceDefectDetector()

        # 无输入应该抛出异常
        with self.assertRaises(ToolException):
            detector.run()

    def test_defect_classification(self):
        """测试缺陷分类功能"""
        detector = AppearanceDetector()

        # 创建测试轮廓
        # 1. 划痕轮廓
        scratch_contour = np.array(
            [[[100, 100]], [[300, 100]], [[300, 102]], [[100, 102]]],
            dtype=np.int32,
        )
        scratch_type = detector._classify_defect(
            scratch_contour, 400, 0.1, 20.0
        )
        self.assertEqual(scratch_type, "scratch")

        # 2. 污点轮廓
        stain_contour = np.array(
            [[[400, 200]], [[410, 200]], [[410, 210]], [[400, 210]]],
            dtype=np.int32,
        )
        stain_type = detector._classify_defect(stain_contour, 100, 0.9, 1.0)
        self.assertEqual(stain_type, "stain")

    def test_confidence_calculation(self):
        """测试置信度计算"""
        detector = AppearanceDetector()

        # 创建测试轮廓
        contour = np.array(
            [[[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]]],
            dtype=np.int32,
        )
        confidence = detector._calculate_confidence(contour, 1000, 0.8)

        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_result_drawing(self):
        """测试结果绘制"""
        detector = AppearanceDetector()
        detector.set_input(self.image_data)
        detector.set_param("draw_result", True)

        # 执行检测
        detector.run()

        # 检查输出图像
        output = detector.get_output()
        self.assertIsNotNone(output)
        self.assertTrue(output.is_valid)


class TestAppearanceDetectionEdgeCases(unittest.TestCase):
    """外观检测边缘情况测试"""

    def test_empty_image(self):
        """测试空图像"""
        detector = AppearanceDetector()

        # 创建空图像
        empty_image = np.zeros((100, 100, 3), dtype=np.uint8)
        image_data = ImageData(empty_image)

        detector.set_input(image_data)
        result = detector.run()
        self.assertTrue(result)

        # 应该没有缺陷
        defect_count = detector.get_result("defect_count")
        self.assertEqual(defect_count, 0)

    def test_no_defects_image(self):
        """测试无缺陷图像"""
        detector = AppearanceDetector()

        # 创建无缺陷图像
        clean_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        image_data = ImageData(clean_image)

        detector.set_input(image_data)
        result = detector.run()
        self.assertTrue(result)

        # 应该没有缺陷
        defect_count = detector.get_result("defect_count")
        self.assertEqual(defect_count, 0)

    def test_small_defects(self):
        """测试小缺陷"""
        detector = AppearanceDetector()
        detector.set_param("min_area", 10)

        # 创建带有小缺陷的图像
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.circle(image, (50, 50), 2, (0, 0, 255), -1)  # 小划痕

        image_data = ImageData(image)
        detector.set_input(image_data)
        result = detector.run()
        self.assertTrue(result)

    def test_multiscale_detection(self):
        """测试多尺度检测"""
        detector = SurfaceDefectDetector()
        detector.set_param("use_multiscale", True)

        # 创建测试图像
        image = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.line(image, (50, 50), (150, 50), (0, 0, 255), 2)

        image_data = ImageData(image)
        detector.set_input(image_data)
        result = detector.run()
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
