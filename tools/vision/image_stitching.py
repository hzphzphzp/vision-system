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
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ),
)

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
        "performance_mode": {
            "name": "性能模式",
            "param_type": "enum",
            "default": "balanced",
            "description": "选择算法性能与质量的平衡模式",
            "options": ["fast", "balanced", "quality"],
            "option_labels": {
                "fast": "快速模式 (速度优先)",
                "balanced": "平衡模式 (推荐)",
                "quality": "高质量模式 (质量优先)",
            },
        },
        "fast_mode": {
            "name": "快速预处理",
            "param_type": "boolean",
            "default": True,
            "description": "启用快速预处理模式，减少图像预处理时间",
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

        # 算法参数（优化版）
        self._params = {
            "feature_detector": "ORB",  # 默认使用ORB（比SIFT快10倍）
            "matcher_type": "BFM",  # 使用BFM（更稳定，crossCheck=True）
            "min_match_count": 8,  # 降低最小匹配点数要求
            "ransac_reproj_threshold": 3.0,  # 更严格的RANSAC阈值
            "blend_method": "feather",  # 使用羽化融合（比multi_band快）
            "blend_strength": 3,  # 降低融合强度
            "parallel_processing": False,  # 禁用并行处理
            "max_workers": 2,  # 减少线程数
            "performance_mode": "balanced",  # 性能模式: fast, balanced, quality
            "fast_mode": True,  # 启用快速预处理模式
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
        创建特征点检测器（优化版）

        Returns:
            特征点检测器实例
        """
        detector_type = self._params.get("feature_detector", "ORB")

        # 根据性能模式调整特征点数量
        performance_mode = self._params.get("performance_mode", "balanced")
        if performance_mode == "fast":
            nfeatures = 800  # 快速模式：大幅减少特征点
            nlevels = 4
            fast_threshold = 25
        elif performance_mode == "balanced":
            nfeatures = 1500  # 平衡模式
            nlevels = 6
            fast_threshold = 20
        else:  # quality
            nfeatures = 3000  # 高质量模式
            nlevels = 8
            fast_threshold = 15

        if detector_type == "SIFT":
            return cv2.SIFT_create(
                nfeatures=nfeatures,
                nOctaveLayers=3,
                contrastThreshold=0.04,
                edgeThreshold=10,
                sigma=1.6,
            )
        elif detector_type == "SURF":
            try:
                return cv2.xfeatures2d.SURF_create()
            except Exception:
                return cv2.SIFT_create(nfeatures=nfeatures)
        elif detector_type == "ORB":
            return cv2.ORB_create(
                nfeatures=nfeatures,
                scaleFactor=1.2,  # 增大尺度因子，减少层数
                nlevels=nlevels,
                patchSize=31,
                edgeThreshold=31,
                firstLevel=0,
                WTA_K=2,
                scoreType=cv2.ORB_HARRIS_SCORE,
                fastThreshold=fast_threshold,
            )
        elif detector_type == "AKAZE":
            return cv2.AKAZE_create(
                descriptor_type=cv2.AKAZE_DESCRIPTOR_MLDB,
                descriptor_size=0,
                descriptor_channels=3,
                threshold=0.001,
                nOctaves=4,
                nOctaveLayers=4,
                diffusivity=cv2.KAZE_DIFF_PM_G2,
            )
        else:
            return cv2.ORB_create(nfeatures=nfeatures)

    def _create_matcher(self):
        """
        创建特征点匹配器（优化版）

        Returns:
            特征点匹配器实例
        """
        matcher_type = self._params.get(
            "matcher_type", "BFM"
        )  # 默认使用BFM（更稳定）
        detector_type = self._params.get("feature_detector", "ORB")

        # 根据性能模式调整匹配参数
        performance_mode = self._params.get("performance_mode", "balanced")
        if performance_mode == "fast":
            checks = 32  # 快速模式：减少检查次数
        elif performance_mode == "balanced":
            checks = 50
        else:  # quality
            checks = 100

        if matcher_type == "FLANN":
            try:
                if detector_type in ["SIFT", "SURF"]:
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(
                        algorithm=FLANN_INDEX_KDTREE,
                        trees=4,  # 减少树数量，提升速度
                    )
                    search_params = dict(checks=checks)
                    return cv2.FlannBasedMatcher(index_params, search_params)
                else:
                    # ORB and AKAZE use LSH (Locality Sensitive Hashing)
                    index_params = dict(
                        algorithm=6,
                        table_number=6,
                        key_size=12,
                        multi_probe_level=1,
                    )
                    search_params = dict(checks=checks)
                    return cv2.FlannBasedMatcher(index_params, search_params)
            except Exception:
                # 降级到BFM匹配器
                if detector_type in ["SIFT", "SURF"]:
                    return cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
                else:
                    return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        else:  # BFM - 使用crossCheck=True提高匹配质量
            if detector_type in ["SIFT", "SURF"]:
                return cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            else:
                return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

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

    def _detect_stitch_direction(self, img1: np.ndarray, img2: np.ndarray) -> str:
        """
        检测拼接方向 - 水平或垂直
        
        Returns:
            "horizontal" 或 "vertical"
        """
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # 使用ORB检测特征点
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
            return "horizontal"  # 默认水平
        
        # 匹配特征点
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        if len(matches) < 8:
            return "horizontal"  # 默认水平
        
        # 分析匹配点的位置差异
        h_diffs = []
        v_diffs = []
        
        for match in matches:
            pt1 = kp1[match.queryIdx].pt
            pt2 = kp2[match.trainIdx].pt
            h_diffs.append(abs(pt1[0] - pt2[0]))
            v_diffs.append(abs(pt1[1] - pt2[1]))
        
        avg_h = np.mean(h_diffs)
        avg_v = np.mean(v_diffs)
        
        # 如果垂直位移明显大于水平位移，说明是垂直拼接
        direction = "vertical" if avg_v > avg_h * 1.2 else "horizontal"
        self._logger.info(f"检测到拼接方向: {direction} (水平差异:{avg_h:.1f}, 垂直差异:{avg_v:.1f})")
        return direction

    def _stitch_with_opencv(self, images: List[ImageData]) -> ImageData:
        """
        使用OpenCV内置Stitcher进行拼接（智能方向检测）
        
        Args:
            images: 输入图像列表
            
        Returns:
            拼接后的图像
        """
        cv_images = [img.data for img in images]
        
        # 检测拼接方向
        if len(cv_images) >= 2:
            direction = self._detect_stitch_direction(cv_images[0], cv_images[1])
        else:
            direction = "horizontal"
        
        # 创建Stitcher
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        
        if direction == "vertical":
            # 垂直拼接：旋转90度后水平拼接，再转回来
            self._logger.info("使用垂直拼接模式（自动旋转）")
            rotated_images = [cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE) for img in cv_images]
            status, stitched_rot = stitcher.stitch(rotated_images)
            
            if status == cv2.Stitcher_OK:
                stitched = cv2.rotate(stitched_rot, cv2.ROTATE_90_COUNTERCLOCKWISE)
                self._logger.info("垂直拼接成功")
                return ImageData(data=stitched)
        else:
            # 水平拼接：直接使用
            status, stitched = stitcher.stitch(cv_images)
            
            if status == cv2.Stitcher_OK:
                self._logger.info("水平拼接成功")
                return ImageData(data=stitched)
        
        raise Exception(f"OpenCV Stitcher失败，状态码: {status}")

    def process(self, input_data: List[ImageData]) -> ResultData:
        """
        处理输入图像，执行拼接融合
        
        策略：
        1. 首先尝试使用OpenCV内置Stitcher（质量最好，无黑线）
        2. 如果失败，回退到自定义算法

        Args:
            input_data: 输入图像列表

        Returns:
            拼接结果
        """
        result = ResultData()
        result.tool_name = self._name

        # 修复：每次处理前清空输入数据列表，防止累积
        # 注意：必须在处理开始前清空，因为上游工具可能已经通过 set_input 累积了数据
        if hasattr(self, '_input_data_list'):
            if len(self._input_data_list) > len(input_data):
                self._logger.debug(f"清空累积的输入数据列表 (之前长度: {len(self._input_data_list)}, 实际使用: {len(input_data)})")
                self._input_data_list.clear()
                # 重新添加传入的数据
                for img in input_data:
                    self._input_data_list.append(img)

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

            # 策略1：首先尝试OpenCV内置Stitcher（质量最好）
            stitched_image = None
            try:
                self._logger.info("步骤1: 尝试OpenCV内置Stitcher")
                stitched_image = self._stitch_with_opencv(input_data)
                self._logger.info("OpenCV Stitcher成功")
            except Exception as e:
                self._logger.warning(f"OpenCV Stitcher失败: {e}，回退到自定义算法")
                
                # 策略2：使用自定义算法作为备选
                self._logger.info("步骤1: 使用自定义算法")
                
                # 特征点检测与匹配
                features = self._detect_and_match_features(input_data)
                
                # 检查特征点检测结果
                valid_features = [
                    f for f in features if f["descriptors"] is not None
                ]
                self._logger.info(
                    f"特征点检测完成: 有效特征={len(valid_features)}/{len(features)}"
                )

                # 图像排序
                sorted_indices = self._sort_images(features)
                sorted_images = [input_data[i] for i in sorted_indices]
                sorted_features = [features[i] for i in sorted_indices]
                self._logger.info(f"图像排序完成: 排序顺序={sorted_indices}")

                # 图像拼接
                stitched_image = self._stitch_images(
                    sorted_images, sorted_features
                )

            # 记录处理时间
            processing_time = time.time() - start_time

            # 构建结果
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
                result.set_value("processing_time", processing_time)
                result.set_value("input_images_count", len(input_data))
                result.set_value("stitched_width", input_data[0].width)
                result.set_value("stitched_height", input_data[0].height)
            self._logger.error(f"拼接过程发生异常: {e}", exc_info=True)

        # 修复：处理完成后清空输入数据列表，防止累积
        if hasattr(self, '_input_data_list'):
            self._logger.debug(f"清空输入数据列表 (之前长度: {len(self._input_data_list)})")
            self._input_data_list.clear()

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
        self._logger.info(
            f"结果已缓存: {cache_key} (当前缓存大小: {len(self._result_cache)}/{self._max_cache_size})"
        )

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

    def preprocess_image(
        self, image: np.ndarray, fast_mode: bool = True
    ) -> np.ndarray:
        """图像预处理：增强对比度，适配高对比度图案（优化版）

        Args:
            image: 输入图像
            fast_mode: 是否使用快速模式（减少预处理步骤）
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if fast_mode:
            # 快速模式：只进行必要的高斯模糊降噪
            gray = cv2.GaussianBlur(gray, (3, 3), 0.5)
        else:
            # 高质量模式：完整预处理
            # 自适应直方图均衡化
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

            # 形态学闭运算
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 高斯模糊
            gray = cv2.GaussianBlur(gray, (5, 5), 1)

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
                self._logger.info(
                    "比率测试后匹配点不足，尝试使用crossCheck匹配"
                )
                if detector_type in ["SIFT", "SURF"]:
                    matcher_cc = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
                else:
                    matcher_cc = cv2.BFMatcher(
                        cv2.NORM_HAMMING, crossCheck=True
                    )

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
                good_matches = sorted(good_matches, key=lambda x: x.distance)[
                    :100
                ]

            return good_matches

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
                # 提取匹配点（改进版：使用比率测试后的优质匹配点）
                sorted_matches = sorted(matches, key=lambda m: m.distance)

                # 选择质量最好的匹配点（前60%）
                good_match_count = max(
                    int(len(sorted_matches) * 0.6), min_match_count
                )
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

                self._logger.info(
                    f"使用 {len(best_matches)} 个高质量匹配点进行单应性计算"
                )

                # 几何一致性预检查：计算匹配点之间的相对距离
                if len(src_pts) >= 4:
                    # 计算源图像中匹配点之间的距离矩阵
                    src_dist_matrix = np.sqrt(
                        np.sum(
                            (src_pts[:, np.newaxis] - src_pts[np.newaxis, :])
                            ** 2,
                            axis=2,
                        )
                    )
                    # 计算目标图像中匹配点之间的距离矩阵
                    dst_dist_matrix = np.sqrt(
                        np.sum(
                            (dst_pts[:, np.newaxis] - dst_pts[np.newaxis, :])
                            ** 2,
                            axis=2,
                        )
                    )

                    # 检查距离一致性（距离变化应该在合理范围内）
                    dist_ratio = dst_dist_matrix / (src_dist_matrix + 1e-6)
                    consistent_mask = (dist_ratio > 0.5) & (dist_ratio < 2.0)
                    consistent_ratio = np.mean(consistent_mask)

                    self._logger.info(
                        f"几何一致性预检查: 一致率={consistent_ratio:.2%}"
                    )

                    # 如果一致率过低，可能是严重的误匹配，需要更严格的筛选
                    if consistent_ratio < 0.3:
                        self._logger.warning(
                            "几何一致性过低，尝试更严格的筛选"
                        )
                        # 只使用前30%的高质量匹配点
                        strict_count = max(int(len(sorted_matches) * 0.3), 8)
                        best_matches = sorted_matches[:strict_count]
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

                # 双向单应性矩阵计算（使用更严格的RANSAC参数）
                self._logger.info("计算双向单应性矩阵（鲁棒性增强版）")

                # 使用更严格的RANSAC参数
                ransac_threshold = self._params.get(
                    "ransac_reproj_threshold", 2.0
                )

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
                            (
                                inlier_dst_pts
                                if direction == 1
                                else inlier_src_pts
                            ),
                            (
                                inlier_src_pts
                                if direction == 1
                                else inlier_dst_pts
                            ),
                            method=0,  # 最小二乘法
                        )

                        if refined_M is not None:
                            best_M = refined_M
                            self._logger.info(
                                f"使用{len(inlier_src_pts)}个内点优化了单应性矩阵"
                            )

                self._logger.info(
                    f"选择方向{direction}，内点数量={best_inliers}"
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
        img1_balanced, img2_balanced = self._balance_brightness(
            img1, img2, overlap
        )

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
            transition_mask = (ratio > inner_threshold) & (
                ratio < outer_threshold
            )
            if np.any(transition_mask):
                # 在过渡区域内进行线性插值
                t = (ratio[transition_mask] - inner_threshold) / (
                    outer_threshold - inner_threshold
                )
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
        实际执行逻辑
        """
        # 修复：运行前立即清空累积数据
        if hasattr(self, "_input_data_list") and len(self._input_data_list) > 2:
            self._logger.debug(f"_run_impl: 清空累积的 {len(self._input_data_list)} 张图像")
            self._input_data_list.clear()
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
                    self._input_count = 0
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
            self._last_input_time = 0
            self._input_count = 0  # 记录当前执行周期的输入数量

        # 修复：检查是否是新的执行周期
        import time
        current_time = time.time()
        time_diff = current_time - self._last_input_time if hasattr(self, '_last_input_time') else 999
        
        # 条件：超过1秒认为是新周期，清空旧数据
        if time_diff > 1.0:
            if len(self._input_data_list) > 0:
                self._logger.debug(f"新的执行周期，清空 {len(self._input_data_list)} 张旧图像")
                self._input_data_list.clear()
            self._input_count = 0
            
        self._last_input_time = current_time

        # 对于图像拼接，我们需要累积输入数据
        if input_data:
            # 添加新的输入数据
            self._input_data_list.append(input_data)
            self._input_count += 1

            # 限制列表长度，只保留最近的N张图像
            max_images = 9
            if len(self._input_data_list) > max_images:
                self._input_data_list = self._input_data_list[-max_images:]
                self._input_count = len(self._input_data_list)

            # 记录输入数据信息
            self._logger.info(
                f"添加输入图像 #{len(self._input_data_list)}: {input_data.width}x{input_data.height}, 当前周期输入数: {self._input_count}"
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
