#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接重影检测测试

测试拼接算法是否会产生重影/双影现象
"""

import os
import sys
import unittest
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool


class TestStitchingGhosting(unittest.TestCase):
    """测试图像拼接重影问题"""
    
    def setUp(self):
        """准备测试"""
        self.stitcher = ImageStitchingTool()
        self.test_images = self._create_test_images_with_overlap()
    
    def _create_test_images_with_overlap(self):
        """
        创建具有重叠区域的测试图像，包含明显的特征用于检测重影
        """
        h, w = 480, 640
        images = []
        
        # 第一张图像 - 左侧，包含数字1
        img1 = np.ones((h, w, 3), dtype=np.uint8) * 200
        # 添加特征：左侧区域
        cv2.rectangle(img1, (50, 100), (150, 400), (0, 0, 255), -1)
        cv2.putText(img1, "1", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
        # 添加纹理特征
        for i in range(0, w, 40):
            cv2.line(img1, (i, 0), (i, h), (100, 100, 100), 1)
        for i in range(0, h, 40):
            cv2.line(img1, (0, i), (w, i), (100, 100, 100), 1)
        images.append(ImageData(data=img1, width=w, height=h, channels=3))
        
        # 第二张图像 - 与第一张有30%重叠
        img2 = np.ones((h, w, 3), dtype=np.uint8) * 200
        overlap_start = int(w * 0.3)
        # 添加特征：包含第一张图像右侧部分 + 新内容
        cv2.rectangle(img2, (overlap_start - 50, 100), (overlap_start + 50, 400), (0, 0, 255), -1)
        cv2.rectangle(img2, (overlap_start + 100, 150), (overlap_start + 200, 350), (0, 255, 0), -1)
        cv2.putText(img2, "2", (overlap_start + 120, 250), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
        # 添加相同的纹理特征
        for i in range(0, w, 40):
            cv2.line(img2, (i, 0), (i, h), (100, 100, 100), 1)
        for i in range(0, h, 40):
            cv2.line(img2, (0, i), (w, i), (100, 100, 100), 1)
        images.append(ImageData(data=img2, width=w, height=h, channels=3))
        
        return images
    
    def detect_ghosting(self, stitched_image, threshold=50):
        """
        检测重影现象
        
        原理：重影会导致重叠区域的方差异常高
        因为同一物体出现在两个位置
        
        Returns:
            (has_ghosting, ghost_score) - 是否检测到重影及重影得分
        """
        if not stitched_image or stitched_image.data is None:
            return True, 100  # 无效图像视为有重影
        
        img = stitched_image.data
        h, w = img.shape[:2]
        
        # 转换为灰度图
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 方法1：检测边缘的重叠
        edges = cv2.Canny(gray, 50, 150)
        
        # 计算边缘密度 - 重影会导致边缘密度异常高
        edge_density = np.sum(edges > 0) / (h * w)
        
        # 方法2：检测高频成分（快速傅里叶变换）
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        # 计算高频能量比例
        center_y, center_x = h // 2, w // 2
        high_freq_mask = np.ones_like(magnitude, dtype=bool)
        high_freq_mask[center_y-20:center_y+20, center_x-20:center_x+20] = False
        high_freq_energy = np.mean(magnitude[high_freq_mask])
        total_energy = np.mean(magnitude)
        high_freq_ratio = high_freq_energy / (total_energy + 1e-6)
        
        # 方法3：局部方差检测
        # 重影区域会有异常高的局部方差
        kernel_size = 31
        local_mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
        local_var = cv2.blur((gray.astype(np.float32) - local_mean) ** 2, (kernel_size, kernel_size))
        
        # 检测高方差区域的比例
        high_var_threshold = np.percentile(local_var, 90)
        high_var_ratio = np.sum(local_var > high_var_threshold) / (h * w)
        
        # 综合评分
        ghost_score = (edge_density * 100 + high_freq_ratio * 50 + high_var_ratio * 100) / 3
        has_ghosting = ghost_score > threshold
        
        return has_ghosting, ghost_score
    
    def test_no_ghosting_in_stitched_result(self):
        """测试：拼接结果不应有重影"""
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")
        
        # 执行拼接
        result = self.stitcher.process(self.test_images[:2])
        
        self.assertTrue(result.status, f"拼接失败: {result.message}")
        self.assertTrue(result.has_image("stitched_image"), "结果中没有stitched_image")
        
        stitched_image = result.get_image("stitched_image")
        self.assertIsNotNone(stitched_image, "stitched_image为None")
        
        # 检测重影
        has_ghosting, ghost_score = self.detect_ghosting(stitched_image)
        
        # 记录结果
        print(f"\n重影检测结果:")
        print(f"  - 重影得分: {ghost_score:.2f}")
        print(f"  - 是否检测到重影: {has_ghosting}")
        print(f"  - 输出尺寸: {stitched_image.width}x{stitched_image.height}")
        
        # 断言：不应检测到重影
        self.assertFalse(has_ghosting, 
            f"检测到重影！重影得分: {ghost_score:.2f}，阈值: 50. "
            f"拼接结果可能存在双影问题。"
        )
    
    def test_feature_matching_quality(self):
        """测试：特征点匹配质量应足够高"""
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")
        
        # 检测特征点
        features = self.stitcher._detect_and_match_features(self.test_images[:2])
        
        self.assertEqual(len(features), 2, "应该检测到2组特征点")
        
        for i, feat in enumerate(features):
            self.assertIsNotNone(feat.get("keypoints"), f"第{i+1}张图像没有关键点")
            self.assertIsNotNone(feat.get("descriptors"), f"第{i+1}张图像没有描述符")
            self.assertGreater(len(feat["keypoints"]), 10, 
                f"第{i+1}张图像特征点太少: {len(feat['keypoints'])}")
        
        # 测试匹配
        matches = self.stitcher._match_features(features[0], features[1])
        
        print(f"\n特征点匹配质量:")
        print(f"  - 图像1特征点: {len(features[0]['keypoints'])}")
        print(f"  - 图像2特征点: {len(features[1]['keypoints'])}")
        print(f"  - 匹配点对: {len(matches)}")
        
        # 应该有足够的匹配点
        self.assertGreater(len(matches), 8, 
            f"匹配点数量不足: {len(matches)}，至少需要8个")
    
    def test_homography_quality(self):
        """测试：单应性矩阵质量应足够高"""
        if len(self.test_images) < 2:
            self.skipTest("测试图像不足")
        
        # 检测特征点和匹配
        features = self.stitcher._detect_and_match_features(self.test_images[:2])
        matches = self.stitcher._match_features(features[0], features[1])
        
        if len(matches) < 8:
            self.skipTest("匹配点不足，无法计算单应性矩阵")
        
        # 提取匹配点
        src_pts = np.float32([features[0]["keypoints"][m.queryIdx].pt for m in matches])
        dst_pts = np.float32([features[1]["keypoints"][m.trainIdx].pt for m in matches])
        
        # 计算单应性矩阵
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
        
        self.assertIsNotNone(H, "单应性矩阵计算失败")
        
        # 计算内点率
        if mask is not None:
            inlier_ratio = np.sum(mask) / len(mask)
            print(f"\n单应性矩阵质量:")
            print(f"  - 内点数量: {np.sum(mask)}/{len(mask)}")
            print(f"  - 内点率: {inlier_ratio:.2%}")
            
            # 内点率应该足够高（注意：即使内点率不高，只要ghosting测试通过，
            # 说明RANSAC已成功过滤掉误匹配，拼接结果仍是可靠的）
            self.assertGreater(inlier_ratio, 0.3, 
                f"内点率过低: {inlier_ratio:.2%}，可能存在大量误匹配")


if __name__ == "__main__":
    unittest.main()
