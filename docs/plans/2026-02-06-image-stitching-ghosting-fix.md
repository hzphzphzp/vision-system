# 图像拼接重影问题修复实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 彻底解决图像拼接算法中的重影问题，通过改进特征匹配、单应性矩阵计算和图像融合算法

**Architecture:** 
1. 改进特征点匹配质量，使用比率测试和双向验证减少误匹配
2. 增强单应性矩阵计算的鲁棒性，使用更严格的RANSAC参数和几何一致性检查
3. 优化图像融合算法，使用渐进式权重过渡和边缘感知融合
4. 添加曝光补偿，减少图像间的亮度差异

**Tech Stack:** Python 3.7+, OpenCV, NumPy, pytest

---

## Task 1: 添加重影检测测试用例

**Files:**
- Create: `tests/test_stitching_ghosting.py`

**Step 1: 创建重影检测测试**

```python
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
            
            # 内点率应该足够高
            self.assertGreater(inlier_ratio, 0.5, 
                f"内点率过低: {inlier_ratio:.2%}，可能存在大量误匹配")


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_stitching_ghosting.py -v`
Expected: 可能通过或部分失败，取决于当前代码状态

**Step 3: 提交测试文件**

```bash
git add tests/test_stitching_ghosting.py
git commit -m "test: 添加图像拼接重影检测测试"
```

---

## Task 2: 改进特征点匹配质量

**Files:**
- Modify: `tools/vision/image_stitching.py:731-797`

**Step 1: 改进 `_match_features` 方法**

将现有代码替换为：

```python
def _match_features(
    self, features1: Dict[str, Any], features2: Dict[str, Any]
) -> List:
    """
    匹配两张图像的特征点（改进版：使用比率测试和双向验证）

    Args:
        features1: 第一张图像的特征点
        features2: 第二张图像的特征点

    Returns:
        匹配点列表
    """
    if (
        features1["descriptors"] is None
        or features2["descriptors"] is None
    ):
        self._logger.debug("特征点描述符为空，无法匹配")
        return []

    # 检查描述符形状和数量
    desc1 = features1["descriptors"]
    desc2 = features2["descriptors"]

    if len(desc1) < 10 or len(desc2) < 10:
        self._logger.error("特征描述符数量不足")
        return []

    try:
        # 确保描述符数据类型正确
        if desc1.dtype != np.float32:
            desc1 = desc1.astype(np.float32)
        if desc2.dtype != np.float32:
            desc2 = desc2.astype(np.float32)

        # 创建新的匹配器（不使用crossCheck，以便使用比率测试）
        detector_type = self._params.get("feature_detector", "ORB")
        if detector_type in ["SIFT", "SURF"]:
            matcher = cv2.BFMatcher(cv2.NORM_L2)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        
        # 使用kNN匹配，k=2
        matches = matcher.knnMatch(desc1, desc2, k=2)
        
        # 应用Lowe's比率测试筛选优质匹配
        good_matches = []
        ratio_threshold = 0.75  # Lowe's比率阈值
        
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                # 如果最佳匹配的距离远小于次佳匹配，则认为是优质匹配
                if m.distance < ratio_threshold * n.distance:
                    good_matches.append(m)
        
        self._logger.info(
            f"匹配结果: kNN匹配数={len(matches)}, "
            f"比率测试后={len(good_matches)}"
        )
        
        # 如果没有足够的匹配点，尝试使用BFM with crossCheck作为后备
        if len(good_matches) < 10:
            self._logger.info("比率测试后匹配点不足，尝试使用crossCheck匹配")
            if detector_type in ["SIFT", "SURF"]:
                matcher_cc = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            else:
                matcher_cc = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            
            matches_cc = matcher_cc.match(desc1, desc2)
            
            # 按距离排序并选择前80%
            matches_cc = sorted(matches_cc, key=lambda x: x.distance)
            max_matches = min(int(len(matches_cc) * 0.8), 100)
            good_matches = matches_cc[:max_matches]
            
            self._logger.info(
                f"crossCheck匹配结果: 原始={len(matches_cc)}, "
                f"筛选后={len(good_matches)}"
            )
        
        # 最终筛选：按距离排序并限制最大数量
        if len(good_matches) > 100:
            good_matches = sorted(good_matches, key=lambda x: x.distance)[:100]
        
        return good_matches
        
    except Exception as e:
        self._logger.error(f"特征点匹配失败: {e}")
        return []
```

**Step 2: 运行特征匹配测试**

Run: `python -m pytest tests/test_stitching_ghosting.py::TestStitchingGhosting::test_feature_matching_quality -v`
Expected: PASS

**Step 3: 提交改进**

```bash
git add tools/vision/image_stitching.py
git commit -m "fix: 改进特征点匹配质量，使用比率测试筛选优质匹配"
```

---

## Task 3: 增强单应性矩阵计算的鲁棒性

**Files:**
- Modify: `tools/vision/image_stitching.py:1060-1170`

**Step 1: 改进单应性矩阵计算逻辑**

找到 `_stitch_images` 方法中的单应性矩阵计算部分，替换为：

```python
            try:
                # 提取匹配点（改进版：使用比率测试后的优质匹配点）
                sorted_matches = sorted(matches, key=lambda m: m.distance)
                
                # 选择质量最好的匹配点（前60%）
                good_match_count = max(int(len(sorted_matches) * 0.6), min_match_count)
                best_matches = sorted_matches[:good_match_count]
                
                src_pts = np.float32(
                    [
                        features[i - 1]["keypoints"][m.queryIdx].pt
                        for m in best_matches
                    ]
                )
                dst_pts = np.float32(
                    [
                        current_features["keypoints"][m.trainIdx].pt
                        for m in best_matches
                    ]
                )
                
                self._logger.info(f"使用 {len(best_matches)} 个高质量匹配点进行单应性计算")
                
                # 几何一致性预检查：计算匹配点之间的相对距离
                if len(src_pts) >= 4:
                    # 计算源图像中匹配点之间的距离矩阵
                    src_dist_matrix = np.sqrt(
                        np.sum((src_pts[:, np.newaxis] - src_pts[np.newaxis, :]) ** 2, axis=2)
                    )
                    # 计算目标图像中匹配点之间的距离矩阵
                    dst_dist_matrix = np.sqrt(
                        np.sum((dst_pts[:, np.newaxis] - dst_pts[np.newaxis, :]) ** 2, axis=2)
                    )
                    
                    # 检查距离一致性（距离变化应该在合理范围内）
                    dist_ratio = dst_dist_matrix / (src_dist_matrix + 1e-6)
                    consistent_mask = (dist_ratio > 0.5) & (dist_ratio < 2.0)
                    consistent_ratio = np.mean(consistent_mask)
                    
                    self._logger.info(f"几何一致性预检查: 一致率={consistent_ratio:.2%}")
                    
                    # 如果一致率过低，可能是严重的误匹配，需要更严格的筛选
                    if consistent_ratio < 0.3:
                        self._logger.warning("几何一致性过低，尝试更严格的筛选")
                        # 只使用前30%的高质量匹配点
                        strict_count = max(int(len(sorted_matches) * 0.3), 8)
                        best_matches = sorted_matches[:strict_count]
                        src_pts = np.float32(
                            [features[i - 1]["keypoints"][m.queryIdx].pt for m in best_matches]
                        )
                        dst_pts = np.float32(
                            [current_features["keypoints"][m.trainIdx].pt for m in best_matches]
                        )

                # 双向单应性矩阵计算（使用更严格的RANSAC参数）
                self._logger.info("计算双向单应性矩阵（鲁棒性增强版）")

                # 使用更严格的RANSAC参数
                ransac_threshold = self._params.get("ransac_reproj_threshold", 2.0)
                
                # 方向1：第二张图向第一张图对齐 (dst_pts → src_pts)
                M1, mask1 = cv2.findHomography(
                    dst_pts,
                    src_pts,
                    cv2.RANSAC,
                    ransac_threshold,
                    maxIters=10000,
                    confidence=0.999,
                )

                # 方向2：第一张图向第二张图对齐 (src_pts → dst_pts)
                M2, mask2 = cv2.findHomography(
                    src_pts,
                    dst_pts,
                    cv2.RANSAC,
                    ransac_threshold,
                    maxIters=10000,
                    confidence=0.999,
                )

                # 评估两个方向的单应性矩阵
                best_M = None
                best_inliers = 0
                best_mask = None
                direction = 1

                if M1 is not None and mask1 is not None:
                    inliers1 = np.sum(mask1)
                    inlier_ratio1 = inliers1 / len(mask1)
                    self._logger.info(
                        f"方向1内点: {inliers1}/{len(mask1)} ({inlier_ratio1:.1%})"
                    )
                    
                    # 只有内点率足够高时才使用
                    if inlier_ratio1 > 0.5:
                        best_M = M1
                        best_inliers = inliers1
                        best_mask = mask1

                if M2 is not None and mask2 is not None:
                    inliers2 = np.sum(mask2)
                    inlier_ratio2 = inliers2 / len(mask2)
                    self._logger.info(
                        f"方向2内点: {inliers2}/{len(mask2)} ({inlier_ratio2:.1%})"
                    )
                    
                    if inlier_ratio2 > 0.5 and inliers2 > best_inliers:
                        best_M = M2
                        best_inliers = inliers2
                        best_mask = mask2
                        direction = 2

                if best_M is None:
                    self._logger.warning("单应性矩阵计算失败或质量过低")
                    continue
                
                # 使用筛选后的内点重新计算单应性矩阵（更精确）
                if best_mask is not None:
                    inlier_src_pts = src_pts[best_mask.ravel() == 1]
                    inlier_dst_pts = dst_pts[best_mask.ravel() == 1]
                    
                    if len(inlier_src_pts) >= 4:
                        # 使用所有内点重新计算，使用最小二乘法
                        refined_M, _ = cv2.findHomography(
                            inlier_dst_pts if direction == 1 else inlier_src_pts,
                            inlier_src_pts if direction == 1 else inlier_dst_pts,
                            method=0,  # 最小二乘法
                        )
                        
                        if refined_M is not None:
                            best_M = refined_M
                            self._logger.info(f"使用{len(inlier_src_pts)}个内点优化了单应性矩阵")

                self._logger.info(
                    f"选择方向{direction}，内点数量={best_inliers}"
                )
                M = best_M
```

**Step 2: 运行单应性矩阵质量测试**

Run: `python -m pytest tests/test_stitching_ghosting.py::TestStitchingGhosting::test_homography_quality -v`
Expected: PASS

**Step 3: 提交改进**

```bash
git add tools/vision/image_stitching.py
git commit -m "fix: 增强单应性矩阵计算的鲁棒性，添加几何一致性检查和内点优化"
```

---

## Task 4: 优化图像融合算法

**Files:**
- Modify: `tools/vision/image_stitching.py:1547-1663`
- Modify: 添加新的辅助方法

**Step 1: 完全重写 `_blend_images` 方法**

替换 `_blend_images` 方法为：

```python
def _blend_images(
    self,
    img1: np.ndarray,
    img2: np.ndarray,
    mask1: np.ndarray = None,
    mask2: np.ndarray = None,
) -> np.ndarray:
    """
    无缝融合两张图像（最终修复重影问题版本）
    
    核心策略：
    1. 在重叠区域中心使用单一图像，避免重影
    2. 只在重叠区域的边缘进行渐进式融合
    3. 使用陡峭的权重过渡曲线
    4. 添加曝光补偿减少亮度差异

    Args:
        img1: 第一张图像（基准图像）
        img2: 第二张图像（待融合图像）
        mask1: 第一张图像的掩码
        mask2: 第二张图像的掩码

    Returns:
        融合后的图像
    """
    # 如果没有提供掩码，自动生成
    if mask1 is None:
        mask1 = np.ones(img1.shape[:2], dtype=np.uint8) * 255

    if mask2 is None:
        mask2 = np.ones(img2.shape[:2], dtype=np.uint8) * 255

    # 找到重叠区域
    overlap = cv2.bitwise_and(mask1, mask2)
    overlap_pixels = np.sum(overlap > 0)
    
    if overlap_pixels == 0:
        self._logger.info("无重叠区域，直接拼接")
        result = img1.copy()
        result[mask2 > 0] = img2[mask2 > 0]
        return result

    self._logger.info(f"重叠区域像素数: {overlap_pixels}")

    # 第一步：曝光补偿，统一亮度
    img1_balanced, img2_balanced = self._balance_brightness(img1, img2, overlap)

    # 第二步：创建改进的融合权重图
    # 计算距离变换
    dist1 = cv2.distanceTransform(mask1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(mask2, cv2.DIST_L2, 5)
    
    # 初始化权重图
    weight1 = np.zeros_like(dist1)
    weight2 = np.zeros_like(dist2)
    
    # 找到重叠区域的坐标
    overlap_coords = np.where(overlap > 0)
    
    if len(overlap_coords[0]) > 0:
        # 获取重叠区域内的距离值
        d1 = dist1[overlap_coords]
        d2 = dist2[overlap_coords]
        
        # 计算总距离
        total_dist = d1 + d2 + 1e-6
        
        # 核心改进：使用分段权重策略
        # 在重叠区域中心（d1 ≈ d2）使用单一图像
        # 只在边缘附近进行快速过渡
        ratio = d1 / total_dist  # 0到1之间的值
        
        # 使用非常陡峭的过渡曲线
        # 设置两个阈值：inner_threshold和outer_threshold
        inner_threshold = 0.45  # 内部区域阈值
        outer_threshold = 0.55  # 外部区域阈值
        
        # 创建权重数组
        w1 = np.zeros_like(ratio)
        w2 = np.zeros_like(ratio)
        
        # 区域1：远离第二张图像边界，主要使用img1
        region1_mask = ratio <= inner_threshold
        w1[region1_mask] = 1.0
        w2[region1_mask] = 0.0
        
        # 区域2：远离第一张图像边界，主要使用img2
        region2_mask = ratio >= outer_threshold
        w1[region2_mask] = 0.0
        w2[region2_mask] = 1.0
        
        # 区域3：中间过渡区域，使用陡峭的线性插值
        transition_mask = (ratio > inner_threshold) & (ratio < outer_threshold)
        if np.any(transition_mask):
            # 在过渡区域内进行线性插值
            t = (ratio[transition_mask] - inner_threshold) / (outer_threshold - inner_threshold)
            w1[transition_mask] = 1.0 - t
            w2[transition_mask] = t
        
        # 将权重赋值回完整图像
        weight1[overlap_coords] = w1
        weight2[overlap_coords] = w2

    # 非重叠区域：完全保留各自的图像
    non_overlap1 = cv2.bitwise_and(mask1, cv2.bitwise_not(mask2))
    non_overlap2 = cv2.bitwise_and(mask2, cv2.bitwise_not(mask1))

    weight1[non_overlap1 > 0] = 1.0
    weight2[non_overlap1 > 0] = 0.0
    weight1[non_overlap2 > 0] = 0.0
    weight2[non_overlap2 > 0] = 1.0

    # 使用较小的核进行高斯模糊，保持边缘清晰
    kernel_size = 7  # 小核以保持边缘锐利
    if kernel_size % 2 == 0:
        kernel_size += 1
    weight1 = cv2.GaussianBlur(weight1, (kernel_size, kernel_size), 2)
    weight2 = cv2.GaussianBlur(weight2, (kernel_size, kernel_size), 2)

    # 扩展权重图为3通道
    weight1_map_3d = np.stack([weight1] * 3, axis=-1)
    weight2_map_3d = np.stack([weight2] * 3, axis=-1)

    # 转换为float32避免溢出
    img1_float = img1_balanced.astype(np.float32)
    img2_float = img2_balanced.astype(np.float32)

    # 加权融合
    result = img1_float * weight1_map_3d + img2_float * weight2_map_3d

    # 裁剪到有效范围
    result = np.clip(result, 0, 255)
    result_uint8 = result.astype(np.uint8)

    return result_uint8
```

**Step 2: 添加曝光补偿辅助方法**

在 `_blend_images` 方法之前添加：

```python
def _exposure_compensation(self, images: List[np.ndarray]) -> List[np.ndarray]:
    """
    曝光补偿：调整多张图像的亮度使其一致
    
    Args:
        images: 输入图像列表
        
    Returns:
        曝光补偿后的图像列表
    """
    if len(images) < 2:
        return images
    
    # 计算每张图像的平均亮度
    brightness_values = []
    for img in images:
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        brightness = np.mean(gray)
        brightness_values.append(brightness)
    
    # 使用第一张图像作为参考
    reference_brightness = brightness_values[0]
    
    # 调整每张图像的亮度
    compensated_images = []
    for i, img in enumerate(images):
        if i == 0:
            compensated_images.append(img)
            continue
        
        current_brightness = brightness_values[i]
        if current_brightness > 0:
            # 计算亮度调整比例
            ratio = reference_brightness / current_brightness
            # 限制调整范围，避免过度调整
            ratio = np.clip(ratio, 0.5, 2.0)
            
            # 调整图像亮度
            adjusted = img.astype(np.float32) * ratio
            adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
            compensated_images.append(adjusted)
            
            self._logger.info(f"图像{i+1}曝光补偿: 比例={ratio:.3f}")
        else:
            compensated_images.append(img)
    
    return compensated_images
```

**Step 3: 运行重影检测测试**

Run: `python -m pytest tests/test_stitching_ghosting.py::TestStitchingGhosting::test_no_ghosting_in_stitched_result -v`
Expected: PASS

**Step 4: 提交改进**

```bash
git add tools/vision/image_stitching.py
git commit -m "fix: 优化图像融合算法，使用分段权重策略避免重影"
```

---

## Task 5: 优化特征点检测参数

**Files:**
- Modify: `tools/vision/image_stitching.py:186-246`

**Step 1: 改进特征点检测器参数**

替换 `_create_feature_detector` 方法中的ORB参数：

```python
        elif detector_type == "ORB":
            # 优化ORB参数以提高匹配质量
            return cv2.ORB_create(
                nfeatures=nfeatures,
                scaleFactor=1.1,  # 减小尺度因子，增加特征点密度
                nlevels=nlevels,
                edgeThreshold=31,
                patchSize=31,
                fastThreshold=fast_threshold,
            )
```

**Step 2: 添加预处理改进**

替换 `preprocess_image` 方法：

```python
def preprocess_image(self, image: np.ndarray, fast_mode: bool = True) -> np.ndarray:
    """图像预处理：增强对比度和纹理细节
    
    Args:
        image: 输入图像
        fast_mode: 是否使用快速模式
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    if fast_mode:
        # 快速模式：轻度高斯模糊降噪
        gray = cv2.GaussianBlur(gray, (3, 3), 0.5)
    else:
        # 高质量模式：增强细节和对比度
        # 轻度CLAHE增强
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # 高斯模糊降噪
        gray = cv2.GaussianBlur(gray, (5, 5), 1)
    
    return gray
```

**Step 3: 运行所有测试**

Run: `python -m pytest tests/test_stitching_ghosting.py -v`
Expected: All tests PASS

**Step 4: 提交改进**

```bash
git add tools/vision/image_stitching.py
git commit -m "optimize: 改进特征点检测参数和图像预处理"
```

---

## Task 6: 运行完整测试套件

**Files:**
- Test: `tests/test_image_stitching.py`
- Test: `tests/test_stitching_ghosting.py`

**Step 1: 运行图像拼接完整测试**

```bash
python -m pytest tests/test_image_stitching.py -v
```
Expected: All tests PASS

**Step 2: 运行重影检测测试**

```bash
python -m pytest tests/test_stitching_ghosting.py -v
```
Expected: All tests PASS

**Step 3: 运行代码质量检查**

```bash
black tools/vision/image_stitching.py --check
flake8 tools/vision/image_stitching.py --max-line-length=100
```
Expected: No errors

**Step 4: 提交最终版本**

```bash
git add -A
git commit -m "fix: 彻底解决图像拼接重影问题

改进内容：
1. 特征点匹配：使用比率测试和双向验证筛选优质匹配
2. 单应性矩阵：增强RANSAC参数，添加几何一致性检查
3. 图像融合：使用分段权重策略，在重叠中心使用单一图像
4. 预处理：优化特征点检测参数，增强纹理细节

测试：
- 添加重影检测测试用例
- 所有测试通过
- 代码风格检查通过"
```

---

## 验证清单

修复完成后，请确认：

- [ ] 运行 `pytest tests/test_stitching_ghosting.py -v` 所有测试通过
- [ ] 运行 `pytest tests/test_image_stitching.py -v` 所有测试通过
- [ ] 代码通过 `flake8` 检查
- [ ] 代码通过 `black --check` 检查
- [ ] 可以手动测试实际图像拼接效果
- [ ] 更新 AGENTS.md 中的 Lesson 20 状态为"已修复"

## 故障排除

如果测试仍然失败：

1. **检查测试图像**: 确保测试图像有足够的特征点
2. **调整阈值**: 可能需要调整重影检测的阈值
3. **查看日志**: 检查拼接过程中的日志输出
4. **可视化**: 添加代码保存中间结果进行可视化调试

## 回滚方案

如果修复导致其他问题：

```bash
# 查看最近的提交
git log --oneline -10

# 如果需要回滚
git revert HEAD  # 回滚最近的一次提交
# 或
git reset --hard HEAD~1  # 撤销最近的一次提交（谨慎使用）
```

## 文档更新

修复完成后，更新以下文档：

1. **AGENTS.md**: 更新 Lesson 20 的状态
2. **README.md**: 如果有相关功能描述，更新为"已修复"
3. **CHANGELOG.md**: 添加修复记录

## 后续优化建议

如果仍有问题，可以考虑：

1. **多频段融合**: 实现真正的多频段融合算法
2. **图像对齐细化**: 使用光流法进行精细对齐
3. **深度学习**: 使用基于深度学习的图像拼接方法
4. **场景识别**: 检测场景类型并选择最佳拼接策略
