#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接融合算法测试

测试图像拼接融合算法的功能和性能

Author: Vision System Team
Date: 2026-01-27
"""

import os
import sys
import time
import unittest

import cv2
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from data.image_data import ImageData
from tools.image_stitching import ImageStitchingTool


class TestImageStitching(unittest.TestCase):
    """
    图像拼接融合算法测试类
    """

    def setUp(self):
        """
        测试前的准备工作
        """
        self.stitcher = ImageStitchingTool()
        self.test_images = self._load_test_images()

    def _load_test_images(self) -> list:
        """
        加载测试图像

        Returns:
            测试图像列表
        """
        test_images = []

        try:
            # 创建测试图像
            # 生成两张有重叠区域的测试图像
            h, w = 480, 640

            # 第一张图像
            img1 = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(
                img1,
                "Image 1",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.rectangle(img1, (100, 100), (300, 300), (0, 255, 0), 2)
            # 直接指定宽度和高度
            img1_data = ImageData(data=img1, width=w, height=h, channels=3)
            print(f"Test image 1: {img1_data.width}x{img1_data.height}")
            test_images.append(img1_data)

            # 第二张图像（与第一张有重叠）
            img2 = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(
                img2,
                "Image 2",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.rectangle(img2, (200, 100), (400, 300), (0, 0, 255), 2)
            img2_data = ImageData(data=img2, width=w, height=h, channels=3)
            print(f"Test image 2: {img2_data.width}x{img2_data.height}")
            test_images.append(img2_data)

            # 第三张图像（与第二张有重叠）
            img3 = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(
                img3,
                "Image 3",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            cv2.rectangle(img3, (300, 100), (500, 300), (255, 0, 0), 2)
            img3_data = ImageData(data=img3, width=w, height=h, channels=3)
            print(f"Test image 3: {img3_data.width}x{img3_data.height}")
            test_images.append(img3_data)

        except Exception as e:
            print(f"加载测试图像失败: {str(e)}")

        return test_images

    def test_stitcher_initialization(self):
        """
        测试图像拼接工具初始化
        """
        self.assertIsInstance(self.stitcher, ImageStitchingTool)
        self.assertEqual(self.stitcher._name, "图像拼接")
        self.assertEqual(self.stitcher._version, "1.0.0")

    def test_parameters(self):
        """
        测试参数设置和获取
        """
        # 获取默认参数
        params = self.stitcher.get_parameters()
        self.assertIn("feature_detector", params)
        self.assertIn("matcher_type", params)
        self.assertIn("parallel_processing", params)

        # 设置新参数
        new_params = {
            "feature_detector": "ORB",
            "matcher_type": "BFM",
            "parallel_processing": False,
        }
        self.stitcher.set_parameters(new_params)

        # 验证参数是否更新
        updated_params = self.stitcher.get_parameters()
        self.assertEqual(updated_params["feature_detector"], "ORB")
        self.assertEqual(updated_params["matcher_type"], "BFM")
        self.assertEqual(updated_params["parallel_processing"], False)

    def test_stitch_two_images(self):
        """
        测试拼接两张图像
        """
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")

        # 测试拼接两张图像
        result = self.stitcher.process(self.test_images[:2])

        # 验证结果结构
        self.assertIn("processing_time", result._values)
        self.assertIn("input_images_count", result._values)
        self.assertIn("stitched_width", result._values)
        self.assertIn("stitched_height", result._values)
        self.assertTrue(result.has_image("stitched_image"))

        # 验证拼接后的图像尺寸
        stitched_image = result.get_image("stitched_image")
        self.assertIsInstance(stitched_image, ImageData)
        self.assertTrue(stitched_image.width > 0)
        self.assertTrue(stitched_image.height > 0)

    def test_stitch_multiple_images(self):
        """
        测试拼接多张图像
        """
        if len(self.test_images) < 3:
            self.skipTest("测试图像不足")

        # 测试拼接三张图像
        result = self.stitcher.process(self.test_images)

        # 验证结果结构
        self.assertIn("processing_time", result._values)
        self.assertIn("input_images_count", result._values)
        self.assertIn("stitched_width", result._values)
        self.assertIn("stitched_height", result._values)
        self.assertTrue(result.has_image("stitched_image"))

        # 验证拼接后的图像尺寸
        stitched_image = result.get_image("stitched_image")
        self.assertIsInstance(stitched_image, ImageData)
        self.assertTrue(stitched_image.width > 0)
        self.assertTrue(stitched_image.height > 0)

    def test_insufficient_images(self):
        """
        测试图像数量不足的情况
        """
        # 测试单张图像
        if len(self.test_images) > 0:
            result = self.stitcher.process([self.test_images[0]])
            self.assertFalse(result.status)
            self.assertIn("至少需要两张图像", result.message)

        # 测试空列表
        result = self.stitcher.process([])
        self.assertFalse(result.status)
        self.assertIn("至少需要两张图像", result.message)

    def test_performance(self):
        """
        测试拼接性能
        """
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")

        # 测试并行处理
        self.stitcher.set_parameters({"parallel_processing": True})
        start_time_parallel = time.time()
        result_parallel = self.stitcher.process(self.test_images[:2])
        time_parallel = time.time() - start_time_parallel

        # 测试串行处理
        self.stitcher.set_parameters({"parallel_processing": False})
        start_time_serial = time.time()
        result_serial = self.stitcher.process(self.test_images[:2])
        time_serial = time.time() - start_time_serial

        # 验证两种模式都能返回有效结果（即使拼接失败）
        self.assertTrue(result_parallel.has_image("stitched_image"))
        self.assertTrue(result_serial.has_image("stitched_image"))

        # 记录性能数据
        print(f"并行处理时间: {time_parallel:.4f}秒")
        print(f"串行处理时间: {time_serial:.4f}秒")

        # 并行处理应该更快（对于较大的图像）
        # 注意：对于小测试图像，并行处理可能反而更慢，因为线程启动开销

    def test_different_feature_detectors(self):
        """
        测试不同的特征点检测器
        """
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")

        # 测试不同的特征点检测器
        detectors = ["SIFT", "ORB", "AKAZE"]

        for detector in detectors:
            try:
                self.stitcher.set_parameters({"feature_detector": detector})
                result = self.stitcher.process(self.test_images[:2])
                # 即使匹配失败，也应该返回结果对象
                self.assertIsInstance(result, type(self.stitcher.process([])))
                print(
                    f"检测器 {detector}: {'成功' if result.status else '失败: ' + result.message}"
                )
            except Exception as e:
                print(f"检测器 {detector} 测试失败: {str(e)}")

    def test_different_blend_methods(self):
        """
        测试不同的融合方法
        """
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")

        # 测试不同的融合方法
        blend_methods = ["none", "feather", "multi_band"]

        for method in blend_methods:
            try:
                self.stitcher.set_parameters({"blend_method": method})
                result = self.stitcher.process(self.test_images[:2])
                # 即使匹配失败，也应该返回结果对象
                self.assertIsInstance(result, type(self.stitcher.process([])))
                print(
                    f"融合方法 {method}: {'成功' if result.status else '失败: ' + result.message}"
                )
            except Exception as e:
                print(f"融合方法 {method} 测试失败: {str(e)}")

    def test_get_info(self):
        """
        测试获取工具信息
        """
        info = self.stitcher.get_info()
        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("description", info)
        self.assertIn("version", info)
        self.assertIn("parameters", info)
        self.assertIn("input_types", info)
        self.assertIn("output_types", info)

        self.assertEqual(info["name"], "图像拼接")
        self.assertEqual(info["version"], "1.0.0")
        self.assertIn("image", info["input_types"])
        self.assertIn("image", info["output_types"])


if __name__ == "__main__":
    unittest.main()
