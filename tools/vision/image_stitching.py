#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接融合算法

实现高性能的图像拼接融合功能，包括特征点检测与匹配、自动排序、并行计算等功能。

Author: Vision System Team
Date: 2026-01-27
"""

import os
import sys
import pickle
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cv2
import numpy as np

from core.tool_base import ToolBase, ToolRegistry
from data.image_data import ImageData, ResultData


@ToolRegistry.register
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

    # 参数定义
    PARAM_DEFINITIONS = {
        "feature_detector": {
            "name": "特征点检测器",
            "param_type": "enum",
            "default": "SIFT",
            "description": "选择特征点检测算法",
            "options": ["SIFT", "ORB", "AKAZE"],
            "option_labels": {
                "SIFT": "SIFT (高精确度)",
                "ORB": "ORB (快速)",
                "AKAZE": "AKAZE (平衡)",
            },
        },
        "matcher_type": {
            "name": "匹配器类型",
            "param_type": "enum",
            "default": "FLANN",
            "description": "选择特征点匹配算法",
            "options": ["FLANN", "BFM"],
            "option_labels": {"FLANN": "FLANN (快速)", "BFM": "BFM (精确)"},
        },
        "min_match_count": {
            "name": "最小匹配点数",
            "param_type": "integer",
            "default": 10,
            "description": "进行拼接所需的最小匹配点数",
            "min_value": 1,
            "max_value": 100,
        },
        "ransac_reproj_threshold": {
            "name": "RANSAC阈值",
            "param_type": "float",
            "default": 4.0,
            "description": "RANSAC重投影误差阈值",
            "min_value": 0.1,
            "max_value": 10.0,
        },
        "blend_method": {
            "name": "融合方法",
            "param_type": "enum",
            "default": "multi_band",
            "description": "选择图像融合算法",
            "options": ["multi_band", "feather", "none"],
            "option_labels": {
                "multi_band": "多频段融合 (最佳)",
                "feather": "羽化融合 (快速)",
                "none": "无融合 (简单叠加)",
            },
        },
        "blend_strength": {
            "name": "融合强度",
            "param_type": "integer",
            "default": 5,
            "description": "融合效果的强度",
            "min_value": 1,
            "max_value": 10,
        },
        "parallel_processing": {
            "name": "并行处理",
            "param_type": "boolean",
            "default": True,
            "description": "是否启用并行计算以提高性能",
        },
        "max_workers": {
            "name": "最大线程数",
            "param_type": "integer",
            "default": 4,
            "description": "并行处理的最大线程数",
            "min_value": 1,
            "max_value": 16,
        },
    }

    def __init__(self, name: str = None):
        """
        初始化图像拼接工具

        Args:
            name: 工具名称
        """
        super().__init__(name or self.tool_name)
        self._version = "1.0.0"
        self._description = self.tool_description

        # 设置随机种子，确保结果可重复
        np.random.seed(42)
        # 设置OpenCV的随机种子
        cv2.setRNGSeed(42)

        # 算法参数
        self._params = {
            "feature_detector": "SIFT",  # 特征点检测器类型: SIFT, SURF, ORB, AKAZE
            "matcher_type": "FLANN",  # 匹配器类型: FLANN, BFM
            "min_match_count": 10,  # 最小匹配点数
            "ransac_reproj_threshold": 4.0,  # RANSAC重投影阈值
            "blend_method": "multi_band",  # 融合方法: multi_band, feather, none
            "blend_strength": 5,  # 融合强度
            "parallel_processing": False,  # 禁用并行处理，确保结果一致
            "max_workers": 4,  # 并行处理的最大线程数
        }

        # 从PARAM_DEFINITIONS加载默认参数
        if hasattr(self, "PARAM_DEFINITIONS") and self.PARAM_DEFINITIONS:
            for key, param_def in self.PARAM_DEFINITIONS.items():
                if "default" in param_def:
                    self._params[key] = param_def["default"]

        # 加载持久化参数
        self._load_persistent_params()

        # 结果缓存（带大小限制，防止内存泄漏）
        self._result_cache = {}
        self._max_cache_size = 10  # 最大缓存条目数
        self._cache_access_order = []  # 记录缓存访问顺序（用于LRU淘汰）

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
            # 配置更多特征点和更精细的参数
            return cv2.SIFT_create(
                nfeatures=20000,  # 大幅增加特征点数量
                contrastThreshold=0.001,  # 更低阈值，检测更多弱特征
                edgeThreshold=5,  # 更低阈值，保留更多边缘特征
            )
        elif detector_type == "SURF":
            # 需要OpenCV contrib模块
            try:
                return cv2.xfeatures2d.SURF_create()
            except Exception:
                return cv2.SIFT_create()
        elif detector_type == "ORB":
            # 配置更多特征点和更精细的参数
            return cv2.ORB_create(
                nfeatures=25000,  # 大幅增加特征点数量
                scaleFactor=1.02,  # 更精细的尺度金字塔
                patchSize=31,
                edgeThreshold=10,  # 更低阈值，保留更多边缘特征
                firstLevel=0,
                WTA_K=2,
                scoreType=cv2.ORB_HARRIS_SCORE,
                nlevels=8,
                fastThreshold=20,
            )
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
            try:
                if detector_type in ["SIFT", "SURF"]:
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(
                        algorithm=FLANN_INDEX_KDTREE, trees=8
                    )  # 增加树数量，提升匹配精度
                    search_params = dict(
                        checks=100
                    )  # 增加检查次数，提升匹配精度
                    return cv2.FlannBasedMatcher(index_params, search_params)
                else:
                    # ORB and AKAZE use different FLANN parameters
                    index_params = dict(
                        algorithm=6,
                        table_number=6,
                        key_size=12,
                        multi_probe_level=1,
                    )
                    search_params = dict(
                        checks=100
                    )  # 增加检查次数，提升匹配精度
                    return cv2.FlannBasedMatcher(index_params, search_params)
            except Exception:
                # 降级到BFM匹配器
                if detector_type in ["SIFT", "SURF"]:
                    return cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
                else:
                    return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        else:  # BFM
            if detector_type in ["SIFT", "SURF"]:
                return cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            else:
                return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def _load_persistent_params(self):
        """
        加载持久化参数
        """
        try:
            params_file = os.path.join(
                os.path.dirname(__file__), "stitching_params.pkl"
            )
            if os.path.exists(params_file):
                with open(params_file, "rb") as f:
                    saved_params = pickle.load(f)
                    self._params.update(saved_params)
                    self._logger.info(f"加载持久化参数成功: {saved_params}")
        except Exception as e:
            self._logger.warning(f"加载持久化参数失败: {e}")

    def _save_persistent_params(self):
        """
        保存持久化参数
        """
        try:
            params_file = os.path.join(
                os.path.dirname(__file__), "stitching_params.pkl"
            )
            # 确保目录存在
            os.makedirs(os.path.dirname(params_file), exist_ok=True)
            with open(params_file, "wb") as f:
                pickle.dump(self._params, f)
                self._logger.info(f"保存持久化参数成功: {self._params}")
        except Exception as e:
            self._logger.warning(f"保存持久化参数失败: {e}")

    def _calculate_image_hash(self, image: ImageData) -> str:
        """
        计算图像的哈希值，用于缓存

        Args:
            image: 图像数据

        Returns:
            图像哈希值
        """
        try:
            # 转换为灰度图像
            if len(image.data.shape) == 3:
                gray = cv2.cvtColor(image.data, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.data

            # 缩小图像尺寸
            resized = cv2.resize(gray, (32, 32))

            # 计算平均值
            mean = np.mean(resized)

            # 计算哈希值
            hash_value = "".join(
                ["1" if pixel > mean else "0" for pixel in resized.flatten()]
            )

            # 转换为十六进制
            hex_hash = hex(int(hash_value, 2))[2:]
            return hex_hash
        except Exception as e:
            self._logger.warning(f"计算图像哈希失败: {e}")
            return str(hash(image.data.tobytes()))

    def _calculate_input_hash(self, input_data: List[ImageData]) -> str:
        """
        计算输入数据的哈希值，用于缓存

        Args:
            input_data: 输入图像列表

        Returns:
            输入数据哈希值
        """
        try:
            # 计算每张图像的哈希值
            image_hashes = [
                self._calculate_image_hash(img) for img in input_data
            ]

            # 排序哈希值，确保顺序不影响结果
            image_hashes.sort()

            # 组合哈希值
            combined_hash = "_".join(image_hashes)

            # 添加参数哈希
            params_hash = str(hash(str(self._params)))

            # 最终哈希值
            final_hash = combined_hash + "_" + params_hash
            return final_hash
        except Exception as e:
            self._logger.warning(f"计算输入哈希失败: {e}")
            return str(hash(str(input_data)))

    def _get_cache_key(self, input_data: List[ImageData]) -> str:
        """
        获取缓存键

        Args:
            input_data: 输入图像列表

        Returns:
            缓存键
        """
        return self._calculate_input_hash(input_data)

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
                self._logger.warning(result.message)
                return result

            # 检查缓存
            cache_key = self._get_cache_key(input_data)
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                self._logger.info(f"从缓存中获取结果: {cache_key}")
                return cached_result

            # 记录开始时间
            start_time = time.time()

            # 记录输入图像信息
            input_sizes = [f"{img.width}x{img.height}" for img in input_data]
            self._logger.info(
                f"开始处理 {len(input_data)} 张图像: {input_sizes}"
            )

            # 建立图像尺寸一致性验证机制
            self._logger.info("步骤0: 图像尺寸一致性验证")
            # 检查所有图像尺寸是否一致
            widths = [img.width for img in input_data]
            heights = [img.height for img in input_data]

            # 计算平均尺寸
            avg_width = int(sum(widths) / len(widths))
            avg_height = int(sum(heights) / len(heights))
            self._logger.info(
                f"图像尺寸统计: 宽度范围={min(widths)}-{max(widths)}, 高度范围={min(heights)}-{max(heights)}, 平均尺寸={avg_width}x{avg_height}"
            )

            # 1. 特征点检测与匹配
            self._logger.info("步骤1: 特征点检测与匹配")
            features = self._detect_and_match_features(input_data)

            # 检查特征点检测结果
            valid_features = [
                f for f in features if f["descriptors"] is not None
            ]
            self._logger.info(
                f"特征点检测完成: 有效特征={len(valid_features)}/{len(features)}"
            )

            # 2. 图像排序
            self._logger.info("步骤2: 图像排序")
            sorted_indices = self._sort_images(features)
            sorted_images = [input_data[i] for i in sorted_indices]
            sorted_features = [features[i] for i in sorted_indices]
            self._logger.info(f"图像排序完成: 排序顺序={sorted_indices}")

            # 3. 图像拼接
            self._logger.info("步骤3: 图像拼接")
            stitched_image = self._stitch_images(
                sorted_images, sorted_features
            )

            # 4. 记录处理时间
            processing_time = time.time() - start_time

            # 5. 构建结果
            if (
                stitched_image.is_valid
                and stitched_image.width > 0
                and stitched_image.height > 0
            ):
                result.status = True
                result.message = (
                    f"图像拼接成功，处理时间: {processing_time:.2f}秒"
                )
                result.set_value("processing_time", processing_time)
                result.set_value("input_images_count", len(input_data))
                result.set_value("stitched_width", stitched_image.width)
                result.set_value("stitched_height", stitched_image.height)
                result.set_image("stitched_image", stitched_image)
                self._logger.info(
                    f"拼接成功! 输出尺寸: {stitched_image.width}x{stitched_image.height}, 处理时间: {processing_time:.2f}秒"
                )

                # 保存到缓存（带大小限制）
                self._add_to_cache(cache_key, result)
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
                self._logger.error(result.message)

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
            self._logger.error(f"拼接过程发生异常: {e}", exc_info=True)

        return result

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

        # 保存持久化参数
        self._save_persistent_params()

        # 清空缓存
        self._result_cache.clear()
        self._cache_access_order.clear()
        self._logger.info("参数已更新，缓存已清空")

    def _add_to_cache(self, cache_key: str, result: ResultData):
        """
        添加结果到缓存（带LRU淘汰机制）

        Args:
            cache_key: 缓存键
            result: 结果数据
        """
        # 如果缓存已满，移除最久未使用的条目
        if len(self._result_cache) >= self._max_cache_size:
            # 移除最旧的缓存条目
            oldest_key = self._cache_access_order.pop(0)
            if oldest_key in self._result_cache:
                del self._result_cache[oldest_key]
                self._logger.info(f"缓存已满，移除旧条目: {oldest_key}")

        # 添加新条目
        self._result_cache[cache_key] = result
        self._cache_access_order.append(cache_key)
        self._logger.info(f"结果已缓存: {cache_key} (当前缓存大小: {len(self._result_cache)}/{self._max_cache_size})")

    def _get_from_cache(self, cache_key: str) -> Optional[ResultData]:
        """
        从缓存获取结果（更新访问顺序）

        Args:
            cache_key: 缓存键

        Returns:
            缓存的结果数据，如果不存在则返回None
        """
        if cache_key in self._result_cache:
            # 更新访问顺序（移到末尾表示最近使用）
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
            self._cache_access_order.append(cache_key)
            return self._result_cache[cache_key]
        return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self._result_cache),
            "max_cache_size": self._max_cache_size,
            "cache_keys": list(self._result_cache.keys()),
            "access_order": self._cache_access_order.copy(),
        }

    def clear_cache(self):
        """清空结果缓存"""
        self._result_cache.clear()
        self._cache_access_order.clear()
        self._logger.info("图像拼接缓存已清空")

    def _detect_and_match_features(
        self, images: List[ImageData]
    ) -> List[Dict[str, Any]]:
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
            with ThreadPoolExecutor(
                max_workers=self._params["max_workers"]
            ) as executor:
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
                        features = [
                            self._detect_features(img) for img in images
                        ]
                        break
        else:
            # 串行处理
            features = [self._detect_features(img) for img in images]

        return features

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理：增强对比度，适配高对比度图案"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 自适应直方图均衡化（比普通均衡化更自然）
        clahe = cv2.createCLAHE(
            clipLimit=1.5, tileGridSize=(16, 16)
        )  # 降低clipLimit，避免过曝
        gray = clahe.apply(gray)

        # 形态学闭运算，填充小缝隙，统一纹理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

        # 轻微高斯模糊，降低噪声
        gray = cv2.GaussianBlur(gray, (5, 5), 1)  # 增大模糊核，提升降噪效果
        return gray

    def _detect_features(self, image: ImageData) -> Dict[str, Any]:
        """
        检测单张图像的特征点

        Args:
            image: 输入图像

        Returns:
            特征点和描述符
        """
        # 转换为灰度图像并进行预处理
        gray_data = self.preprocess_image(image.data)

        # 检测特征点和计算描述符
        try:
            # 确保图像数据类型正确
            if gray_data.dtype != np.uint8:
                gray_data = gray_data.astype(np.uint8)

            # 对于SIFT/SURF/AKAZE
            keypoints, descriptors = self._detector.detectAndCompute(
                gray_data, None
            )
            self._logger.info(f"检测到 {len(keypoints)} 个特征点")
        except ValueError:
            # 对于ORB，可能返回不同的格式
            keypoints = self._detector.detect(gray_data, None)
            keypoints, descriptors = self._detector.compute(
                gray_data, keypoints
            )
            self._logger.info(f"检测到 {len(keypoints)} 个特征点 (ORB格式)")
        except Exception as e:
            # 其他错误，返回空值
            self._logger.error(f"特征点检测失败: {e}")
            keypoints, descriptors = [], None

        return {
            "keypoints": keypoints,
            "descriptors": descriptors,
            "image": image,
        }

    def _match_features(
        self, features1: Dict[str, Any], features2: Dict[str, Any]
    ) -> List:
        """
        匹配两张图像的特征点（双向匹配，顺序不敏感版）

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

        if len(desc1) < 20 or len(desc2) < 20:
            self._logger.error("特征描述符数量不足")
            return []

        # 检查描述符形状
        desc1_shape = desc1.shape if hasattr(desc1, "shape") else "未知"
        desc2_shape = desc2.shape if hasattr(desc2, "shape") else "未知"
        self._logger.debug(
            f"描述符形状: 图像1={desc1_shape}, 图像2={desc2_shape}"
        )

        try:
            # 确保描述符数据类型正确
            if desc1.dtype != np.float32:
                desc1 = desc1.astype(np.float32)
            if desc2.dtype != np.float32:
                desc2 = desc2.astype(np.float32)

            # 方向1：features1 → features2
            matches1 = self._matcher.knnMatch(desc1, desc2, k=2)

            # 应用比率测试筛选良好匹配点
            good_matches1 = []
            for m, n in matches1:
                if m.distance < 0.8 * n.distance:
                    good_matches1.append(m)

            # 方向2：features2 → features1
            matches2 = self._matcher.knnMatch(desc2, desc1, k=2)

            # 应用比率测试筛选良好匹配点
            good_matches2 = []
            for m, n in matches2:
                if m.distance < 0.8 * n.distance:
                    good_matches2.append(m)

            # 寻找互匹配点（双向一致性检查）
            mutual_matches = []
            # 创建匹配点映射
            match_map1 = {m.queryIdx: m.trainIdx for m in good_matches1}

            for m2 in good_matches2:
                # m2.queryIdx是desc2中的索引，m2.trainIdx是desc1中的索引
                # 检查是否存在互匹配
                if (
                    m2.trainIdx in match_map1
                    and match_map1[m2.trainIdx] == m2.queryIdx
                ):
                    # 找到互匹配点，添加到结果中
                    # 使用方向1的匹配点格式
                    for m1 in good_matches1:
                        if (
                            m1.queryIdx == m2.trainIdx
                            and m1.trainIdx == m2.queryIdx
                        ):
                            mutual_matches.append(m1)
                            break

            # 确定最终匹配结果
            final_matches = []

            # 优先使用互匹配点
            if len(mutual_matches) >= 10:
                final_matches = mutual_matches
                self._logger.info(
                    f"使用互匹配点: {len(final_matches)}个匹配点"
                )
            else:
                # 互匹配点不足，选择匹配点更多且质量更好的方向
                # 计算平均距离，评估匹配质量
                avg_dist1 = (
                    np.mean([m.distance for m in good_matches1])
                    if good_matches1
                    else float("inf")
                )
                avg_dist2 = (
                    np.mean([m.distance for m in good_matches2])
                    if good_matches2
                    else float("inf")
                )

                # 综合考虑匹配点数量和质量
                score1 = len(good_matches1) / (avg_dist1 + 1e-6)  # 避免除零
                score2 = len(good_matches2) / (avg_dist2 + 1e-6)

                if score1 >= score2:
                    final_matches = good_matches1
                    self._logger.info(
                        f"使用方向1匹配点: {len(final_matches)}个匹配点, 平均距离={avg_dist1:.2f}"
                    )
                else:
                    # 转换方向2的匹配点格式为方向1的格式
                    class Match:
                        def __init__(self, queryIdx, trainIdx, distance):
                            self.queryIdx = queryIdx
                            self.trainIdx = trainIdx
                            self.distance = distance

                    final_matches = []
                    for m in good_matches2:
                        final_matches.append(
                            Match(m.trainIdx, m.queryIdx, m.distance)
                        )
                    self._logger.info(
                        f"使用方向2匹配点: {len(final_matches)}个匹配点, 平均距离={avg_dist2:.2f}"
                    )

            self._logger.info(
                f"匹配结果: 方向1良好匹配数={len(good_matches1)}, 方向2良好匹配数={len(good_matches2)}, 互匹配数={len(mutual_matches)}, 最终匹配数={len(final_matches)}"
            )
            return final_matches
        except Exception as e:
            self._logger.error(f"特征点匹配失败: {e}")
            return []

    def _sort_images(self, features: List[Dict[str, Any]]) -> List[int]:
        """
        智能排序图像，确定正确的拼接顺序（基于图论的最佳路径，顺序不敏感版）

        Args:
            features: 特征点列表

        Returns:
            排序后的索引列表
        """
        num_images = len(features)
        if num_images == 0:
            return []
        elif num_images == 1:
            return [0]

        # 计算图像间的匹配矩阵
        match_matrix = np.zeros((num_images, num_images), dtype=int)

        # 串行计算匹配矩阵，确保结果一致
        for i in range(num_images):
            for j in range(i + 1, num_images):
                matches = self._match_features(features[i], features[j])
                match_matrix[i, j] = len(matches)
                match_matrix[j, i] = len(matches)

        # 计算相似度矩阵（将匹配数转换为相似度）
        # 为了处理匹配数为0的情况，添加一个小的常数
        similarity_matrix = match_matrix + 1

        # 使用最小生成树（MST）找到最佳拼接路径
        # Kruskal算法构建最小生成树
        def kruskal_mst(num_nodes, similarity_matrix):
            """使用Kruskal算法构建最大生成树（因为相似度越高越好）"""
            # 创建边列表
            edges = []
            for i in range(num_nodes):
                for j in range(i + 1, num_nodes):
                    weight = similarity_matrix[i][j]
                    # 添加边，同时记录节点索引，用于确定性排序
                    edges.append(
                        (-weight, min(i, j), max(i, j), i, j)
                    )  # 使用负权重将最大生成树问题转换为最小生成树问题

            # 按权重排序，权重相同时按节点索引排序，确保确定性
            edges.sort(key=lambda x: (x[0], x[1], x[2]))

            # 并查集数据结构
            parent = list(range(num_nodes))

            def find(u):
                if parent[u] != u:
                    parent[u] = find(parent[u])
                return parent[u]

            def union(u, v):
                root_u = find(u)
                root_v = find(v)
                if root_u != root_v:
                    # 确保合并操作的确定性，总是将较小索引的根作为父节点
                    if root_u < root_v:
                        parent[root_v] = root_u
                    else:
                        parent[root_u] = root_v
                    return True
                return False

            # 构建MST
            mst_edges = []
            for edge in edges:
                weight, _, _, u, v = edge
                if union(u, v):
                    mst_edges.append((u, v, -weight))  # 恢复原始权重
                if len(mst_edges) == num_nodes - 1:
                    break

            return mst_edges

        # 构建最大生成树
        mst_edges = kruskal_mst(num_images, similarity_matrix)

        # 从MST构建邻接表
        adj_list = {i: [] for i in range(num_images)}
        for u, v, weight in mst_edges:
            adj_list[u].append((v, weight))
            adj_list[v].append((u, weight))

        # 使用深度优先搜索（DFS）遍历MST，生成拼接顺序
        def dfs_order(start_node, adj_list):
            visited = set()
            order = []

            def dfs(node):
                if node not in visited:
                    visited.add(node)
                    order.append(node)
                    # 按相似度排序邻居，优先访问相似度高的，相似度相同时按节点索引排序
                    neighbors = sorted(
                        adj_list[node], key=lambda x: (-x[1], x[0])
                    )
                    for neighbor, weight in neighbors:
                        dfs(neighbor)

            dfs(start_node)
            return order

        # 选择起始节点（与其他图像总相似度最高的）
        total_similarity = np.sum(similarity_matrix, axis=1)

        # 找到总相似度最高的节点，当多个节点相似度相同时，选择索引最小的
        max_similarity = np.max(total_similarity)
        start_indices = np.where(total_similarity == max_similarity)[0]
        start_idx = min(start_indices)  # 选择索引最小的，确保确定性

        # 生成拼接顺序
        sorted_indices = dfs_order(start_idx, adj_list)

        # 验证排序结果
        if len(sorted_indices) != num_images:
            # 如果DFS遍历不完整，使用贪心算法作为后备
            self._logger.warning("MST排序不完整，使用贪心算法作为后备")
            sorted_indices = []
            visited = [False] * num_images

            # 选择起始图像
            start_idx = np.argmax(np.sum(match_matrix, axis=1))
            sorted_indices.append(start_idx)
            visited[start_idx] = True

            # 逐步添加最匹配的相邻图像
            while len(sorted_indices) < num_images:
                last_idx = sorted_indices[-1]
                best_match = -1
                best_score = -1

                for i in range(num_images):
                    if not visited[i]:
                        # 计算综合得分，当得分相同时，选择索引较小的
                        score = match_matrix[last_idx, i]
                        if score > best_score or (
                            score == best_score and i < best_match
                        ):
                            best_match = i
                            best_score = score

                if best_match != -1:
                    sorted_indices.append(best_match)
                    visited[best_match] = True
                else:
                    # 如果没有找到匹配的图像，添加索引最小的未访问图像
                    for i in range(num_images):
                        if not visited[i]:
                            sorted_indices.append(i)
                            visited[i] = True
                            break

        self._logger.info(f"图像排序完成: 排序顺序={sorted_indices}")
        return sorted_indices

    def check_mirror(self, img1: np.ndarray, img2: np.ndarray) -> bool:
        """
        检测是否需要水平翻转第二张图（针对RO1文字区域，顺序不敏感版）

        Args:
            img1: 第一张图像
            img2: 第二张图像

        Returns:
            是否需要水平翻转
        """
        try:
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]

            # 提取左上角文字区域（RO1所在区域）
            roi1 = img1[0 : int(h1 * 0.2), 0 : int(w1 * 0.2)]
            roi2 = img2[0 : int(h2 * 0.2), 0 : int(w2 * 0.2)]

            # 计算原始/翻转后的相似度
            roi2_flip = cv2.flip(roi2, 1)
            sim_original = cv2.matchTemplate(roi1, roi2, cv2.TM_CCOEFF_NORMED)[
                0
            ][0]
            sim_flip = cv2.matchTemplate(
                roi1, roi2_flip, cv2.TM_CCOEFF_NORMED
            )[0][0]

            # 为了确保顺序不敏感，也计算反向的相似度
            roi1_flip = cv2.flip(roi1, 1)
            sim_original_reverse = cv2.matchTemplate(
                roi2, roi1, cv2.TM_CCOEFF_NORMED
            )[0][0]
            sim_flip_reverse = cv2.matchTemplate(
                roi2, roi1_flip, cv2.TM_CCOEFF_NORMED
            )[0][0]

            # 综合考虑两个方向的相似度
            avg_sim_original = (sim_original + sim_original_reverse) / 2
            avg_sim_flip = (sim_flip + sim_flip_reverse) / 2

            self._logger.info(
                f"镜像检测：原始相似度={avg_sim_original:.3f}, 翻转后={avg_sim_flip:.3f}"
            )

            # 翻转判定：翻转后相似度更高且>0.2
            return avg_sim_flip > avg_sim_original and avg_sim_flip > 0.2
        except Exception as e:
            self._logger.warning(f"镜像检测失败，默认不翻转: {str(e)}")
            return False

    def _stitch_images(
        self, images: List[ImageData], features: List[Dict[str, Any]]
    ) -> ImageData:
        """
        拼接排序后的图像（顺序不敏感版）

        Args:
            images: 排序后的图像列表
            features: 排序后的特征点列表

        Returns:
            拼接后的图像
        """
        # 初始化拼接结果为第一张图像
        result_image = images[0].copy()
        self._logger.info(
            f"初始化拼接结果尺寸: {result_image.width}x{result_image.height}"
        )

        for i in range(1, len(images)):
            self._logger.info(f"拼接图像 {i}/{len(images)-1}")

            # 检查镜像问题
            need_flip = self.check_mirror(result_image.data, images[i].data)
            if need_flip:
                # 翻转图像
                flipped_image = ImageData(data=cv2.flip(images[i].data, 1))
                # 重新检测翻转后图像的特征点
                flipped_features = self._detect_features(flipped_image)
                # 更新当前图像和特征
                current_image = flipped_image
                current_features = flipped_features
                self._logger.info("执行水平翻转，校正镜像问题")
            else:
                current_image = images[i]
                current_features = features[i]

            # 匹配当前结果与下一张图像
            matches = self._match_features(features[i - 1], current_features)

            min_match_count = self._params["min_match_count"]
            self._logger.info(
                f"特征点匹配数: {len(matches)}, 最小要求: {min_match_count}"
            )

            # 降低最小匹配点数要求，提高拼接成功率
            adjusted_min_match = max(5, min_match_count)  # 至少需要5个匹配点
            if len(matches) < adjusted_min_match:
                self._logger.warning(f"匹配点不足，跳过图像 {i}")
                continue

            try:
                # 提取匹配点
                src_pts = np.float32(
                    [
                        features[i - 1]["keypoints"][m.queryIdx].pt
                        for m in matches
                    ]
                )
                dst_pts = np.float32(
                    [
                        current_features["keypoints"][m.trainIdx].pt
                        for m in matches
                    ]
                )

                # 双向单应性矩阵计算
                self._logger.info("计算双向单应性矩阵")

                # 方向1：第二张图向第一张图对齐 (dst_pts → src_pts)
                M1, mask1 = cv2.findHomography(
                    dst_pts,
                    src_pts,
                    cv2.RANSAC,
                    5.0,
                    maxIters=2000,
                    confidence=0.99,
                )

                # 方向2：第一张图向第二张图对齐 (src_pts → dst_pts)
                M2, mask2 = cv2.findHomography(
                    src_pts,
                    dst_pts,
                    cv2.RANSAC,
                    5.0,
                    maxIters=2000,
                    confidence=0.99,
                )

                # 评估两个方向的单应性矩阵
                best_M = None
                best_inliers = 0
                direction = 1

                if M1 is not None:
                    inliers1 = mask1.sum()
                    self._logger.info(
                        f"方向1（第二张图向第一张图对齐）内点数量={inliers1}/{len(matches)}"
                    )
                    best_M = M1
                    best_inliers = inliers1

                if M2 is not None:
                    inliers2 = mask2.sum()
                    self._logger.info(
                        f"方向2（第一张图向第二张图对齐）内点数量={inliers2}/{len(matches)}"
                    )
                    if inliers2 > best_inliers:
                        best_M = M2
                        best_inliers = inliers2
                        direction = 2
                    elif inliers2 == best_inliers and direction == 1:
                        # 内点数量相同时，优先选择方向1，确保一致性
                        self._logger.info("内点数量相同，优先选择方向1")

                if best_M is None:
                    self._logger.warning("单应性矩阵计算失败")
                    continue

                self._logger.info(
                    f"选择最佳方向{direction}，内点数量={best_inliers}/{len(matches)}"
                )
                M = best_M

                # 根据选择的方向调整图像处理逻辑
                if direction == 2:
                    # 方向2：需要交换图像角色，将第一张图向第二张图对齐
                    self._logger.info("使用方向2：第一张图向第二张图对齐")
                    # 交换结果图像和当前图像
                    temp_image = result_image
                    result_image = current_image
                    current_image = temp_image
                    # 交换特征
                    temp_features = features[i - 1]
                    features[i - 1] = current_features
                    current_features = temp_features

                # 获取第二张图像的尺寸
                h, w = current_image.height, current_image.width
                self._logger.info(f"第二张图像尺寸: {w}x{h}")

                # 计算拼接后的边界
                corners = np.float32(
                    [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]
                ).reshape(-1, 1, 2)
                transformed_corners = cv2.perspectiveTransform(corners, M)

                # 计算新的边界
                all_corners = np.concatenate(
                    [
                        transformed_corners,
                        np.float32(
                            [
                                [0, 0],
                                [0, result_image.height - 1],
                                [
                                    result_image.width - 1,
                                    result_image.height - 1,
                                ],
                                [result_image.width - 1, 0],
                            ]
                        ).reshape(-1, 1, 2),
                    ],
                    axis=0,
                )

                # 计算画布的最小/最大坐标（留出10像素边距）
                [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel()) - 10
                [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel()) + 10

                # 确保画布尺寸为正
                x_min = min(0, x_min)
                y_min = min(0, y_min)
                canvas_w = x_max - x_min
                canvas_h = y_max - y_min

                # 确保画布尺寸有效
                if canvas_w <= 0 or canvas_h <= 0:
                    self._logger.warning(
                        f"无效的画布尺寸: {canvas_w}x{canvas_h}"
                    )
                    continue

                self._logger.info(f"拼接画布尺寸：{canvas_w}x{canvas_h}")

                # 构建平移矩阵（避免变换后图像偏移出画布）
                H_trans = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
                M_combined = H_trans @ M  # 组合平移和单应性变换

                # 变换第二张图到第一张图的坐标系
                self._logger.info("执行图像变换")
                warped_image = cv2.warpPerspective(
                    current_image.data,
                    M_combined,
                    (canvas_w, canvas_h),
                    flags=cv2.INTER_LINEAR,  # 线性插值，保证画质
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0, 0, 0),
                )

                # 创建第一张图的画布（平移后）
                result_warped = np.zeros(
                    (canvas_h, canvas_w, 3), dtype=np.uint8
                )

                # 计算有效的放置区域
                y_start = max(0, -y_min)
                y_end = min(canvas_h, -y_min + result_image.height)
                x_start = max(0, -x_min)
                x_end = min(canvas_w, -x_min + result_image.width)

                self._logger.info(
                    f"放置区域: x[{x_start},{x_end}], y[{y_start},{y_end}]"
                )

                # 确保区域有效
                if y_start < y_end and x_start < x_end:
                    self._logger.info("放置第一张图像到拼接区域")
                    # 确保索引不越界
                    result_h, result_w = result_image.data.shape[:2]
                    copy_h = min(y_end - y_start, result_h)
                    copy_w = min(x_end - x_start, result_w)
                    if copy_h > 0 and copy_w > 0:
                        result_warped[
                            y_start : y_start + copy_h,
                            x_start : x_start + copy_w,
                        ] = result_image.data[:copy_h, :copy_w]
                    else:
                        self._logger.warning("复制区域无效")
                        continue
                else:
                    # 尝试使用默认位置放置图像
                    self._logger.warning("放置区域无效，尝试使用默认位置")
                    # 使用画布中心附近的位置
                    center_x = canvas_w // 2
                    center_y = canvas_h // 2
                    result_h, result_w = result_image.data.shape[:2]

                    # 计算默认放置位置
                    default_x_start = max(0, center_x - result_w // 2)
                    default_y_start = max(0, center_y - result_h // 2)
                    default_x_end = min(canvas_w, default_x_start + result_w)
                    default_y_end = min(canvas_h, default_y_start + result_h)

                    if (
                        default_y_end > default_y_start
                        and default_x_end > default_x_start
                    ):
                        self._logger.info(
                            f"使用默认位置放置图像: x[{default_x_start},{default_x_end}], y[{default_y_start},{default_y_end}]"
                        )
                        copy_h = default_y_end - default_y_start
                        copy_w = default_x_end - default_x_start
                        result_warped[
                            default_y_start:default_y_end,
                            default_x_start:default_x_end,
                        ] = result_image.data[:copy_h, :copy_w]
                    else:
                        self._logger.warning("默认放置区域也无效，跳过此图像")
                        continue

                # 确定实际使用的放置位置
                if y_start < y_end and x_start < x_end:
                    actual_y_start = y_start
                    actual_y_end = y_end
                    actual_x_start = x_start
                    actual_x_end = x_end
                else:
                    # 使用默认位置
                    center_x = canvas_w // 2
                    center_y = canvas_h // 2
                    result_h, result_w = result_image.data.shape[:2]
                    actual_x_start = max(0, center_x - result_w // 2)
                    actual_y_start = max(0, center_y - result_h // 2)
                    actual_x_end = min(canvas_w, actual_x_start + result_w)
                    actual_y_end = min(canvas_h, actual_y_start + result_h)

                # 创建掩码（用于融合）
                mask1 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
                mask1[
                    actual_y_start:actual_y_end, actual_x_start:actual_x_end
                ] = 255

                mask2 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
                mask2[warped_image.sum(axis=2) > 0] = 255

                # 融合图像
                self._logger.info("融合图像")
                stitched = self._blend_images(
                    result_warped, warped_image, mask1, mask2
                )
                self._logger.info(
                    f"融合后尺寸: {stitched.shape[1]}x{stitched.shape[0]}"
                )

                # 裁剪多余黑边
                self._logger.info("裁剪多余黑边")
                stitched_cropped = self._crop_black_borders(stitched)

                # 检查裁剪后的尺寸
                if (
                    stitched_cropped.size > 0
                    and stitched_cropped.shape[0] > 0
                    and stitched_cropped.shape[1] > 0
                ):
                    stitched_final = stitched_cropped
                    self._logger.info(
                        f"裁剪后尺寸: {stitched_final.shape[1]}x{stitched_final.shape[0]}"
                    )
                else:
                    # 裁剪失败，使用原始融合结果
                    stitched_final = stitched
                    self._logger.warning(
                        f"裁剪失败，使用融合结果: {stitched_final.shape[1]}x{stitched_final.shape[0]}"
                    )

                # 更新结果图像
                self._logger.info(
                    f"更新结果图像: {stitched_final.shape[1]}x{stitched_final.shape[0]}"
                )
                result_image = ImageData(data=stitched_final)
                self._logger.info(
                    f"更新后ImageData尺寸: {result_image.width}x{result_image.height}"
                )

                # 检查结果图像是否有效
                if result_image.is_valid:
                    self._logger.info("拼接步骤成功")
                else:
                    self._logger.warning("拼接步骤失败: 结果图像无效")

            except Exception as e:
                self._logger.error(f"拼接过程发生异常: {e}", exc_info=True)
                # 忽略拼接过程中的错误，继续尝试下一张图像
                continue

        # 确保返回有效的图像
        if (
            result_image.is_valid
            and result_image.width > 0
            and result_image.height > 0
        ):
            self._logger.info(
                f"拼接完成! 最终结果尺寸: {result_image.width}x{result_image.height}"
            )
        else:
            # 检查是否至少有部分拼接成功
            success_count = 0
            for i in range(1, len(images)):
                # 检查是否有拼接成功的记录
                # 这里我们通过检查result_image是否与第一张图像不同来判断
                if result_image.data.size > 0 and not np.array_equal(
                    result_image.data, images[0].data
                ):
                    success_count += 1
                    break

            if success_count > 0:
                self._logger.warning(
                    "拼接过程中有部分成功，但最终结果尺寸无效，尝试修复"
                )
                # 尝试裁剪或调整结果图像
                if result_image.data.size > 0:
                    # 尝试裁剪黑边
                    stitched = self._crop_black_borders(result_image.data)
                    if (
                        stitched.size > 0
                        and stitched.shape[0] > 0
                        and stitched.shape[1] > 0
                    ):
                        result_image = ImageData(data=stitched)
                        self._logger.info(
                            f"修复后结果尺寸: {result_image.width}x{result_image.height}"
                        )
                    else:
                        # 裁剪失败，保留原始拼接结果
                        self._logger.warning("裁剪黑边失败，保留原始拼接结果")
                        # 直接使用原始拼接结果，不进行裁剪
                        # 确保ImageData对象有效
                        if result_image.data.size > 0:
                            # 重新创建ImageData对象，确保尺寸信息正确
                            result_image = ImageData(data=result_image.data)
                            self._logger.info(
                                f"保留原始拼接结果尺寸: {result_image.width}x{result_image.height}"
                            )

            # 如果仍然无效，返回第一张图像
            if (
                not result_image.is_valid
                or result_image.width <= 0
                or result_image.height <= 0
            ):
                self._logger.error(
                    "拼接失败: 最终结果图像无效，返回第一张图像"
                )
                result_image = images[0].copy()

        return result_image

    def _crop_black_borders(self, image: np.ndarray) -> np.ndarray:
        """
        裁剪拼接结果的多余黑边

        Args:
            image: 拼接后的图像

        Returns:
            裁剪后的图像
        """
        # 检查输入图像是否有效
        if image is None or image.size == 0:
            self._logger.warning("裁剪黑边失败：输入图像无效")
            return image

        # 检查图像通道数
        if len(image.shape) != 3:
            self._logger.warning(f"裁剪黑边失败：图像形状无效 {image.shape}")
            return image

        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 二值化，区分黑边和有效区域
            _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            # 找到有效区域的边界
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                self._logger.warning("裁剪黑边失败：未找到轮廓")
                return image

            # 找到最大轮廓（有效图像区域）
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # 检查裁剪区域是否有效
            if w <= 0 or h <= 0:
                self._logger.warning(f"裁剪黑边失败：裁剪区域无效 {w}x{h}")
                return image

            # 加5像素边距，避免裁剪过紧
            x = max(0, x - 5)
            y = max(0, y - 5)
            w = min(image.shape[1] - x, w + 10)
            h = min(image.shape[0] - y, h + 10)

            # 再次检查裁剪区域
            if w <= 0 or h <= 0:
                self._logger.warning(
                    f"裁剪黑边失败：调整后裁剪区域无效 {w}x{h}"
                )
                return image

            # 裁剪
            cropped = image[y : y + h, x : x + w]
            self._logger.info(
                f"裁剪黑边成功：从 {image.shape[1]}x{image.shape[0]} 裁剪到 {cropped.shape[1]}x{cropped.shape[0]}"
            )
            return cropped
        except Exception as e:
            self._logger.error(f"裁剪黑边失败: {e}")
            return image

    def _balance_brightness(
        self, img1: np.ndarray, img2: np.ndarray, mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        均衡两张图的亮度/对比度，消除融合区域的明暗差异

        Args:
            img1: 第一张图像
            img2: 第二张图像
            mask: 重叠区域掩码

        Returns:
            亮度均衡后的两张图像
        """
        # 只在重叠区域计算亮度均值
        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # 提取重叠区域的像素
        overlap_pixels1 = img1_gray[mask > 0]
        overlap_pixels2 = img2_gray[mask > 0]

        if len(overlap_pixels1) == 0 or len(overlap_pixels2) == 0:
            return img1, img2

        # 计算亮度均值和方差
        mean1, std1 = np.mean(overlap_pixels1), np.std(overlap_pixels1)
        mean2, std2 = np.mean(overlap_pixels2), np.std(overlap_pixels2)

        # 将img2的亮度/对比度匹配到img1
        img2_float = img2.astype(np.float32)
        img2_balanced = ((img2_float - mean2) * (std1 / (std2 + 1e-6))) + mean1

        # 伽马校正进一步匹配亮度
        gamma = mean1 / (mean2 + 1e-6)
        img2_balanced = np.clip(img2_balanced, 0, 255).astype(np.uint8)
        img2_balanced = np.power(img2_balanced / 255.0, gamma) * 255.0
        img2_balanced = np.clip(img2_balanced, 0, 255).astype(np.uint8)

        return img1, img2_balanced

    def _blend_images(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        mask1: np.ndarray = None,
        mask2: np.ndarray = None,
    ) -> np.ndarray:
        """
        无缝融合两张图像（基于参考代码的优化版本）

        Args:
            img1: 第一张图像
            img2: 第二张图像
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
        if np.sum(overlap) == 0:
            self._logger.info("无重叠区域，直接拼接")
            result = img1.copy()
            result[mask2 > 0] = img2[mask2 > 0]
            return result

        # 先均衡重叠区域的亮度/对比度
        img1_balanced, img2_balanced = self._balance_brightness(
            img1, img2, overlap
        )

        # 优化重叠区域检测：从轮廓改为距离变换，生成软掩码
        # 计算mask1到mask2的距离，生成线性渐变权重
        dist1 = cv2.distanceTransform(mask1, cv2.DIST_L2, 5)
        dist2 = cv2.distanceTransform(mask2, cv2.DIST_L2, 5)

        # 归一化距离到0-1
        dist1 = cv2.normalize(dist1, None, 0, 1.0, cv2.NORM_MINMAX)
        dist2 = cv2.normalize(dist2, None, 0, 1.0, cv2.NORM_MINMAX)

        # 生成平滑的权重图（基于距离的线性渐变，比sigmoid更自然）
        weight1 = dist1 / (dist1 + dist2 + 1e-6)  # 避免除0
        weight2 = dist2 / (dist1 + dist2 + 1e-6)

        # 只在重叠区域应用权重，非重叠区域权重为1/0
        non_overlap1 = cv2.bitwise_and(mask1, cv2.bitwise_not(mask2))
        non_overlap2 = cv2.bitwise_and(mask2, cv2.bitwise_not(mask1))

        weight1[non_overlap1 > 0] = 1.0
        weight2[non_overlap1 > 0] = 0.0
        weight1[non_overlap2 > 0] = 0.0
        weight2[non_overlap2 > 0] = 1.0

        # 增大高斯模糊核，提升过渡平滑度
        kernel_size = 41  # 固定大核，更适合高对比度图案
        if kernel_size % 2 == 0:
            kernel_size += 1
        weight1 = cv2.GaussianBlur(weight1, (kernel_size, kernel_size), 10)
        weight2 = cv2.GaussianBlur(weight2, (kernel_size, kernel_size), 10)

        # 扩展权重图为3通道
        weight1_map_3d = np.stack([weight1] * 3, axis=-1)
        weight2_map_3d = np.stack([weight2] * 3, axis=-1)

        # 转换为float32避免溢出
        img1_float = img1_balanced.astype(np.float32)
        img2_float = img2_balanced.astype(np.float32)

        # 融合重叠区域
        result = img1_float * weight1_map_3d + img2_float * weight2_map_3d

        # 后处理：全局轻微模糊，消除最后残留的细微边界
        result_uint8 = result.astype(np.uint8)
        result_uint8 = cv2.GaussianBlur(result_uint8, (3, 3), 0)

        return result_uint8

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
        # 处理单个图像的情况
        if not self._input_data:
            return None

        # 检查是否有多张图像需要拼接
        if (
            hasattr(self, "_input_data_list")
            and len(self._input_data_list) >= 2
        ):
            # 记录输入图像信息
            input_sizes = [
                f"{img.width}x{img.height}" for img in self._input_data_list
            ]
            self._logger.info(
                f"开始拼接 {len(self._input_data_list)} 张图像: {input_sizes}"
            )

            # 调用process方法进行多图像拼接
            process_result = self.process(self._input_data_list)

            if process_result.status and hasattr(process_result, "get_image"):
                stitched_image = process_result.get_image("stitched_image")
                if stitched_image:
                    # 记录拼接结果信息
                    self._logger.info(
                        f"拼接成功! 输入: {len(self._input_data_list)}张图像, 输出尺寸: {stitched_image.width}x{stitched_image.height}"
                    )

                    self._output_data = stitched_image
                    # 清空输入数据列表，准备接收新数据
                    self._input_data_list.clear()
                    return {"OutputImage": stitched_image}
            else:
                # 拼接失败，记录错误信息
                error_msg = getattr(process_result, "message", "Unknown error")
                self._logger.error(f"拼接失败: {error_msg}")

        # 对于单张图像，返回输入图像
        self._logger.info(
            f"处理单张图像: {self._input_data.width}x{self._input_data.height}"
        )
        return {"OutputImage": self._input_data}

    def run(self):
        """
        运行工具，处理输入数据并返回输出
        """
        # 检查是否有输入数据
        if not self._input_data:
            return None

        # 对于图像拼接，我们需要特殊处理
        # 检查是否有多张图像需要拼接
        if (
            hasattr(self, "_input_data_list")
            and len(self._input_data_list) >= 2
        ):
            # 记录输入图像信息
            input_sizes = [
                f"{img.width}x{img.height}" for img in self._input_data_list
            ]
            self._logger.info(
                f"开始拼接 {len(self._input_data_list)} 张图像: {input_sizes}"
            )

            # 调用process方法进行多图像拼接
            process_result = self.process(self._input_data_list)

            if process_result.status and hasattr(process_result, "get_image"):
                stitched_image = process_result.get_image("stitched_image")
                if stitched_image:
                    # 记录拼接结果信息
                    self._logger.info(
                        f"拼接成功! 输入: {len(self._input_data_list)}张图像, 输出尺寸: {stitched_image.width}x{stitched_image.height}"
                    )

                    self._output_data = stitched_image
                    # 清空输入数据列表，准备接收新数据
                    self._input_data_list.clear()
                    return {"OutputImage": stitched_image}
            else:
                # 拼接失败，记录错误信息
                error_msg = getattr(process_result, "message", "Unknown error")
                self._logger.error(f"拼接失败: {error_msg}")

        # 对于单张图像，返回输入图像
        self._logger.info(
            f"处理单张图像: {self._input_data.width}x{self._input_data.height}"
        )
        return {"OutputImage": self._input_data}

    def set_input(self, input_data, port_name="InputImage"):
        """
        设置输入数据

        Args:
            input_data: 输入数据
            port_name: 端口名称
        """
        super().set_input(input_data, port_name)

        # 初始化输入数据列表，用于多图像拼接
        if not hasattr(self, "_input_data_list"):
            self._input_data_list = []

        # 对于图像拼接，我们需要累积输入数据
        # 但要确保列表不会无限增长
        if input_data:
            # 添加新的输入数据
            self._input_data_list.append(input_data)

            # 限制列表长度，只保留最近的N张图像
            # 根据需求，最大支持9张图像拼接
            max_images = 9
            if len(self._input_data_list) > max_images:
                # 移除最旧的图像
                self._input_data_list = self._input_data_list[-max_images:]

            # 记录输入数据信息
            self._logger.debug(
                f"添加输入图像 #{len(self._input_data_list)}: {input_data.width}x{input_data.height}"
            )

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
            "output_types": ["image", "numeric"],
        }


# 注册工具
if __name__ == "__main__":
    # 测试代码
    import os
    import sys

    # 添加项目根目录到Python路径
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )

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
            print(
                f"拼接后尺寸: {result.get_value('stitched_width')}x{result.get_value('stitched_height')}"
            )
        else:
            print(f"图像拼接失败: {result.message}")
    else:
        print("请添加测试图像")
