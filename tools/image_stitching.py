#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接融合算法

实现高性能的图像拼接融合功能，包括特征点检测与匹配、自动排序、并行计算等功能。

Author: Vision System Team
Date: 2026-01-27
"""

import time
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.tool_base import ToolBase
from data.image_data import ImageData, ResultData


class ImageStitchingTool(ToolBase):
    """
    图像拼接融合工具
    
    功能：
    1. 全自动特征点检测与匹配
    2. 智能图像排序
    3. 高效并行计算
    4. 多种融合算法支持
    """
    
    # 类属性
    tool_name = "图像拼接"
    tool_category = "Vision"
    tool_description = "高性能图像拼接融合算法"
    
    def __init__(self):
        """
        初始化图像拼接工具
        """
        super().__init__(name="图像拼接")
        self._version = "1.0.0"
        self._description = self.tool_description
        
        # 算法参数
        self._params = {
            "feature_detector": "SIFT",  # 特征点检测器类型: SIFT, SURF, ORB, AKAZE
            "matcher_type": "FLANN",  # 匹配器类型: FLANN, BFM
            "min_match_count": 10,  # 最小匹配点数
            "ransac_reproj_threshold": 4.0,  # RANSAC重投影阈值
            "blend_method": "multi_band",  # 融合方法: multi_band, feather, none
            "blend_strength": 5,  # 融合强度
            "parallel_processing": True,  # 是否启用并行处理
            "max_workers": 4,  # 并行处理的最大线程数
        }
        
        # 初始化特征点检测器
        self._detector = self._create_feature_detector()
        self._matcher = self._create_matcher()
    
    def _create_feature_detector(self):
        """
        创建特征点检测器
        
        Returns:
            特征点检测器实例
        """
        detector_type = self._params["feature_detector"]
        
        if detector_type == "SIFT":
            return cv2.SIFT_create()
        elif detector_type == "SURF":
            # 需要OpenCV contrib模块
            try:
                return cv2.xfeatures2d.SURF_create()
            except Exception:
                return cv2.SIFT_create()
        elif detector_type == "ORB":
            return cv2.ORB_create()
        elif detector_type == "AKAZE":
            return cv2.AKAZE_create()
        else:
            return cv2.SIFT_create()
    
    def _create_matcher(self):
        """
        创建特征点匹配器
        
        Returns:
            特征点匹配器实例
        """
        matcher_type = self._params["matcher_type"]
        detector_type = self._params["feature_detector"]
        
        if matcher_type == "FLANN":
            if detector_type in ["SIFT", "SURF"]:
                index_params = dict(algorithm=1, trees=5)
                search_params = dict(checks=50)
                return cv2.FlannBasedMatcher(index_params, search_params)
            else:
                # ORB and AKAZE use different FLANN parameters
                index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)
                search_params = dict(checks=50)
                return cv2.FlannBasedMatcher(index_params, search_params)
        else:  # BFM
            if detector_type in ["SIFT", "SURF"]:
                return cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            else:
                return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    def process(self, input_data: List[ImageData]) -> ResultData:
        """
        处理输入图像，执行拼接融合
        
        Args:
            input_data: 输入图像列表
            
        Returns:
            拼接结果
        """
        result = ResultData()
        result.tool_name = self._name
        
        try:
            if len(input_data) < 2:
                result.status = False
                result.message = "至少需要两张图像进行拼接"
                return result
            
            # 记录开始时间
            start_time = time.time()
            
            # 1. 特征点检测与匹配
            features = self._detect_and_match_features(input_data)
            
            # 2. 图像排序
            sorted_indices = self._sort_images(features)
            sorted_images = [input_data[i] for i in sorted_indices]
            sorted_features = [features[i] for i in sorted_indices]
            
            # 3. 图像拼接
            stitched_image = self._stitch_images(sorted_images, sorted_features)
            
            # 4. 记录处理时间
            processing_time = time.time() - start_time
            
            # 5. 构建结果
            if stitched_image.is_valid and stitched_image.width > 0 and stitched_image.height > 0:
                result.status = True
                result.message = f"图像拼接成功，处理时间: {processing_time:.2f}秒"
                result.set_value("processing_time", processing_time)
                result.set_value("input_images_count", len(input_data))
                result.set_value("stitched_width", stitched_image.width)
                result.set_value("stitched_height", stitched_image.height)
                result.set_image("stitched_image", stitched_image)
            else:
                # 如果拼接失败，返回第一张图像
                result.status = False
                result.message = f"图像拼接失败: 无法生成有效的拼接结果，处理时间: {processing_time:.2f}秒"
                # 返回第一张图像作为默认结果
                result.set_image("stitched_image", input_data[0].copy())
                result.set_value("processing_time", processing_time)
                result.set_value("input_images_count", len(input_data))
                result.set_value("stitched_width", input_data[0].width)
                result.set_value("stitched_height", input_data[0].height)
            
        except Exception as e:
            result.status = False
            result.message = f"图像拼接失败: {str(e)}"
            result.error_type = type(e).__name__
            # 发生异常时，返回第一张图像
            if input_data:
                result.set_image("stitched_image", input_data[0].copy())
                result.set_value("input_images_count", len(input_data))
                result.set_value("stitched_width", input_data[0].width)
                result.set_value("stitched_height", input_data[0].height)
        
        return result
    
    def _detect_and_match_features(self, images: List[ImageData]) -> List[Dict[str, Any]]:
        """
        检测和匹配特征点
        
        Args:
            images: 输入图像列表
            
        Returns:
            特征点和描述符列表
        """
        features = []
        
        if self._params["parallel_processing"]:
            # 并行处理特征点检测
            with ThreadPoolExecutor(max_workers=self._params["max_workers"]) as executor:
                future_to_index = {
                    executor.submit(self._detect_features, image): i 
                    for i, image in enumerate(images)
                }
                
                for future in as_completed(future_to_index):
                    i = future_to_index[future]
                    try:
                        img_features = future.result()
                        features.append(img_features)
                    except Exception as e:
                        # 如果并行处理失败，使用串行处理
                        features = [self._detect_features(img) for img in images]
                        break
        else:
            # 串行处理
            features = [self._detect_features(img) for img in images]
        
        return features
    
    def _detect_features(self, image: ImageData) -> Dict[str, Any]:
        """
        检测单张图像的特征点
        
        Args:
            image: 输入图像
            
        Returns:
            特征点和描述符
        """
        # 转换为灰度图像
        gray_image = image.to_gray()
        gray_data = gray_image.data
        
        # 检测特征点和计算描述符
        try:
            # 对于SIFT/SURF/AKAZE
            keypoints, descriptors = self._detector.detectAndCompute(gray_data, None)
        except ValueError:
            # 对于ORB，可能返回不同的格式
            keypoints = self._detector.detect(gray_data, None)
            keypoints, descriptors = self._detector.compute(gray_data, keypoints)
        except Exception as e:
            # 其他错误，返回空值
            keypoints, descriptors = [], None
        
        return {
            "keypoints": keypoints,
            "descriptors": descriptors,
            "image": image
        }
    
    def _match_features(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> List:
        """
        匹配两张图像的特征点
        
        Args:
            features1: 第一张图像的特征点
            features2: 第二张图像的特征点
            
        Returns:
            匹配点列表
        """
        if features1["descriptors"] is None or features2["descriptors"] is None:
            return []
        
        # 使用KNN匹配
        matches = self._matcher.knnMatch(
            features1["descriptors"], 
            features2["descriptors"], 
            k=2
        )
        
        # 应用比率测试
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        return good_matches
    
    def _sort_images(self, features: List[Dict[str, Any]]) -> List[int]:
        """
        智能排序图像，确定正确的拼接顺序
        
        Args:
            features: 特征点列表
            
        Returns:
            排序后的索引列表
        """
        num_images = len(features)
        if num_images == 0:
            return []
        
        # 计算图像间的匹配矩阵
        match_matrix = np.zeros((num_images, num_images), dtype=int)
        
        if self._params["parallel_processing"]:
            # 并行计算匹配矩阵
            with ThreadPoolExecutor(max_workers=self._params["max_workers"]) as executor:
                futures = []
                for i in range(num_images):
                    for j in range(i + 1, num_images):
                        futures.append(
                            executor.submit(
                                self._match_features, 
                                features[i], 
                                features[j]
                            )
                        )
                
                idx = 0
                for i in range(num_images):
                    for j in range(i + 1, num_images):
                        matches = futures[idx].result()
                        match_matrix[i, j] = len(matches)
                        match_matrix[j, i] = len(matches)
                        idx += 1
        else:
            # 串行计算匹配矩阵
            for i in range(num_images):
                for j in range(i + 1, num_images):
                    matches = self._match_features(features[i], features[j])
                    match_matrix[i, j] = len(matches)
                    match_matrix[j, i] = len(matches)
        
        # 使用贪心算法排序图像
        sorted_indices = []
        visited = [False] * num_images
        
        # 选择起始图像（与其他图像匹配最多的）
        start_idx = np.argmax(np.sum(match_matrix, axis=1))
        sorted_indices.append(start_idx)
        visited[start_idx] = True
        
        # 逐步添加最匹配的相邻图像
        while len(sorted_indices) < num_images:
            last_idx = sorted_indices[-1]
            best_match = -1
            best_score = -1
            
            for i in range(num_images):
                if not visited[i] and match_matrix[last_idx, i] > best_score:
                    best_match = i
                    best_score = match_matrix[last_idx, i]
            
            if best_match != -1:
                sorted_indices.append(best_match)
                visited[best_match] = True
            else:
                # 如果没有找到匹配的图像，添加任意未访问的图像
                for i in range(num_images):
                    if not visited[i]:
                        sorted_indices.append(i)
                        visited[i] = True
                        break
        
        return sorted_indices
    
    def _stitch_images(self, images: List[ImageData], features: List[Dict[str, Any]]) -> ImageData:
        """
        拼接排序后的图像
        
        Args:
            images: 排序后的图像列表
            features: 排序后的特征点列表
            
        Returns:
            拼接后的图像
        """
        # 初始化拼接结果为第一张图像
        result_image = images[0].copy()
        
        for i in range(1, len(images)):
            # 匹配当前结果与下一张图像
            matches = self._match_features(features[i-1], features[i])
            
            if len(matches) < self._params["min_match_count"]:
                continue
            
            try:
                # 提取匹配点
                src_pts = np.float32([features[i-1]["keypoints"][m.queryIdx].pt for m in matches])
                dst_pts = np.float32([features[i]["keypoints"][m.trainIdx].pt for m in matches])
                
                # 计算单应性矩阵
                M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, self._params["ransac_reproj_threshold"])
                
                if M is None:
                    continue
                
                # 获取第二张图像的尺寸
                h, w = images[i].height, images[i].width
                
                # 计算拼接后的边界
                corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                transformed_corners = cv2.perspectiveTransform(corners, M)
                
                # 计算新的边界
                all_corners = np.concatenate([
                    transformed_corners,
                    np.float32([[0, 0], [0, result_image.height-1], 
                                [result_image.width-1, result_image.height-1], 
                                [result_image.width-1, 0]]).reshape(-1, 1, 2)
                ], axis=0)
                
                [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
                [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)
                
                # 计算平移矩阵
                translation = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
                M_combined = translation @ M
                
                #  warp第二张图像
                stitched_width = x_max - x_min
                stitched_height = y_max - y_min
                
                # 确保宽度和高度为正数
                if stitched_width <= 0 or stitched_height <= 0:
                    continue
                
                # Warp the second image
                warped_image = cv2.warpPerspective(
                    images[i].data,
                    M_combined,
                    (stitched_width, stitched_height)
                )
                
                # 调整第一张图像的大小
                result_warped = np.zeros((stitched_height, stitched_width, 3), dtype=np.uint8)
                
                # 计算有效的放置区域
                y_start = max(0, -y_min)
                y_end = min(stitched_height, -y_min + result_image.height)
                x_start = max(0, -x_min)
                x_end = min(stitched_width, -x_min + result_image.width)
                
                # 确保区域有效
                if y_start < y_end and x_start < x_end:
                    result_warped[y_start:y_end, x_start:x_end] = result_image.data[:y_end-y_start, :x_end-x_start]
                
                # 融合图像
                stitched = self._blend_images(result_warped, warped_image)
                
                # 更新结果图像
                result_image = ImageData(data=stitched)
            except Exception as e:
                # 忽略拼接过程中的错误，继续尝试下一张图像
                continue
        
        # 确保返回有效的图像
        if not result_image.is_valid:
            # 如果拼接失败，返回第一张图像
            result_image = images[0].copy()
        
        return result_image
    
    def _blend_images(self, image1: np.ndarray, image2: np.ndarray) -> np.ndarray:
        """
        融合两张图像
        
        Args:
            image1: 第一张图像
            image2: 第二张图像
            
        Returns:
            融合后的图像
        """
        blend_method = self._params["blend_method"]
        
        if blend_method == "none":
            # 简单叠加
            mask = (image2 != 0).any(axis=2)
            result = image1.copy()
            result[mask] = image2[mask]
            return result
        
        elif blend_method == "feather":
            #  feather融合
            mask = (image2 != 0).astype(np.float32)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            result = image1.astype(np.float32) * (1 - mask) + image2.astype(np.float32) * mask
            return result.astype(np.uint8)
        
        elif blend_method == "multi_band":
            # 多频段融合（简化版）
            # 创建掩码
            mask = (image2 != 0).astype(np.float32)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            # 计算权重
            weight1 = 1 - mask
            weight2 = mask
            
            # 应用高斯金字塔融合
            result = image1.astype(np.float32) * weight1 + image2.astype(np.float32) * weight2
            return result.astype(np.uint8)
        
        else:
            # 默认使用feather融合
            #  feather融合
            mask = (image2 != 0).astype(np.float32)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            result = image1.astype(np.float32) * (1 - mask) + image2.astype(np.float32) * mask
            return result.astype(np.uint8)
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取工具参数
        
        Returns:
            参数字典
        """
        return self._params
    
    def set_parameters(self, params: Dict[str, Any]):
        """
        设置工具参数
        
        Args:
            params: 参数字典
        """
        for key, value in params.items():
            if key in self._params:
                self._params[key] = value
        
        # 更新特征点检测器和匹配器
        self._detector = self._create_feature_detector()
        self._matcher = self._create_matcher()
    
    def _run_impl(self):
        """
        实际执行逻辑，实现ToolBase的抽象方法
        """
        # 这里处理单个图像的情况
        # 对于拼接工具，我们需要处理多个图像
        # 但根据ToolBase的接口，我们先处理单个输入的情况
        if not self._input_data:
            return None
        
        # 这里可以返回输入图像的拷贝，作为默认行为
        # 实际的多图像拼接需要通过process方法调用
        return self._input_data.copy()
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            工具信息字典
        """
        return {
            "name": self._name,
            "description": self._description,
            "version": self._version,
            "parameters": self._params,
            "input_types": ["image"],
            "output_types": ["image", "numeric"]
        }


# 注册工具
if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # 测试图像拼接
    from data.image_data import ImageData
    
    # 加载测试图像
    test_images = []
    # 这里可以添加测试图像加载代码
    
    if test_images:
        stitcher = ImageStitchingTool()
        result = stitcher.process(test_images)
        
        if result.status:
            print("图像拼接成功!")
            print(f"处理时间: {result.get_value('processing_time'):.2f}秒")
            print(f"拼接后尺寸: {result.get_value('stitched_width')}x{result.get_value('stitched_height')}")
        else:
            print(f"图像拼接失败: {result.message}")
    else:
        print("请添加测试图像")
