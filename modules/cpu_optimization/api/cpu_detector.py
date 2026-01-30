#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU检测器API接口

提供完整的API接口，支持模型加载、参数配置、推理执行、结果返回等功能

Author: Vision System Team
Date: 2026-01-26
"""

import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger("CPUOptimization.API")


class BackendType(Enum):
    """推理后端类型"""

    AUTO = "auto"
    ONNX_RUNTIME = "onnxruntime"
    OPENCV_DNN = "opencv"


class DetectorState(Enum):
    """检测器状态"""

    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class DetectionResult:
    """检测结果"""

    success: bool
    boxes: List[Dict[str, Any]] = field(default_factory=list)
    image: Optional[np.ndarray] = None
    inference_time_ms: float = 0
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "boxes": self.boxes,
            "inference_time_ms": self.inference_time_ms,
            "error_message": self.error_message,
            "num_boxes": len(self.boxes),
        }


@dataclass
class APIConfig:
    """API配置"""

    model_path: str = ""
    class_names_path: str = ""
    backend: BackendType = BackendType.AUTO
    num_threads: int = 0
    confidence_threshold: float = 0.25
    nms_threshold: float = 0.45
    input_size: Tuple[int, int] = (640, 640)
    max_batch_size: int = 1
    use_gpu: bool = False
    enable_profiling: bool = False
    callback_url: str = ""


class CPUDetectorAPI:
    """
    CPU检测器API接口

    提供完整的API接口，支持：
    - 模型加载和管理
    - 参数配置和动态调整
    - 图像推理和批处理
    - 实时性能监控
    - 状态管理
    """

    def __init__(self, config: APIConfig = None):
        """
        初始化API接口

        Args:
            config: API配置
        """
        self.config = config or APIConfig()
        self._detector = None
        self._state = DetectorState.UNINITIALIZED
        self._state_lock = threading.Lock()
        self._performance_stats = {}
        self._callbacks = {}

        # 导入内部模块
        self._setup_detector()

    def _setup_detector(self):
        """设置检测器"""
        try:
            from ..models.yolo26_cpu import (
                CPUInferenceConfig,
                YOLO26CPUDetector,
            )

            # 创建内部配置
            inference_config = CPUInferenceConfig(
                num_threads=self.config.num_threads,
                conf_threshold=self.config.confidence_threshold,
                nms_threshold=self.config.nms_threshold,
                input_size=self.config.input_size,
                batch_size=self.config.max_batch_size,
            )

            self._detector = YOLO26CPUDetector(inference_config)

        except ImportError as e:
            logger.error(f"无法导入检测器模块: {e}")
            self._state = DetectorState.ERROR

    def set_config(self, **kwargs):
        """
        设置配置参数

        支持的参数:
            - confidence_threshold: 置信度阈值
            - nms_threshold: NMS阈值
            - num_threads: 线程数
            - input_size: 输入尺寸
        """
        allowed_params = {
            "confidence_threshold",
            "nms_threshold",
            "num_threads",
            "input_size",
            "max_batch_size",
        }

        for key, value in kwargs.items():
            if key in allowed_params:
                if key == "confidence_threshold":
                    self.config.confidence_threshold = value
                    if self._detector:
                        self._detector.config.conf_threshold = value
                elif key == "nms_threshold":
                    self.config.nms_threshold = value
                    if self._detector:
                        self._detector.config.nms_threshold = value
                elif key == "num_threads":
                    self.config.num_threads = value
                elif key == "input_size":
                    self.config.input_size = tuple(value)
                    if self._detector:
                        self._detector.config.input_size = tuple(value)
                elif key == "max_batch_size":
                    self.config.max_batch_size = value
                    if self._detector:
                        self._detector.config.batch_size = value

                logger.debug(f"配置已更新: {key} = {value}")
            else:
                logger.warning(f"未知配置参数: {key}")

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "model_path": self.config.model_path,
            "backend": self.config.backend.value,
            "num_threads": self.config.num_threads,
            "confidence_threshold": self.config.confidence_threshold,
            "nms_threshold": self.config.nms_threshold,
            "input_size": self.config.input_size,
            "max_batch_size": self.config.max_batch_size,
            "state": self._state.value,
        }

    def load_model(self, model_path: str, class_names_path: str = "") -> bool:
        """
        加载模型

        Args:
            model_path: 模型文件路径
            class_names_path: 类别名称文件路径

        Returns:
            是否加载成功
        """
        with self._state_lock:
            self._state = DetectorState.LOADING

        self.config.model_path = model_path
        self.config.class_names_path = class_names_path

        if not self._detector:
            self._setup_detector()

        success = self._detector.load_model(
            model_path, class_names_path if class_names_path else None
        )

        if success:
            self._state = DetectorState.READY
            self._trigger_callback("on_model_loaded", {"path": model_path})
            logger.info(f"模型加载成功: {model_path}")
        else:
            self._state = DetectorState.ERROR
            self._trigger_callback(
                "on_error", {"message": f"无法加载模型: {model_path}"}
            )

        return success

    def warmup(self, num_iterations: int = 5) -> bool:
        """
        预热模型

        Args:
            num_iterations: 预热迭代次数

        Returns:
            是否预热成功
        """
        if self._state != DetectorState.READY:
            logger.error("模型未就绪，请先加载模型")
            return False

        try:
            self._detector.warmup(num_iterations)
            self._trigger_callback(
                "on_warmup_complete", {"iterations": num_iterations}
            )
            return True
        except Exception as e:
            logger.error(f"预热失败: {e}")
            return False

    def detect(
        self,
        image: np.ndarray,
        draw_results: bool = False,
        return_image: bool = False,
    ) -> DetectionResult:
        """
        检测图像

        Args:
            image: 输入图像 (H, W, BGR)
            draw_results: 是否在图像上绘制检测结果
            return_image: 是否返回带结果的图像

        Returns:
            DetectionResult: 检测结果
        """
        if self._state not in [DetectorState.READY, DetectorState.RUNNING]:
            return DetectionResult(success=False, error_message="检测器未就绪")

        with self._state_lock:
            self._state = DetectorState.RUNNING

        start_time = time.time()

        try:
            # 执行检测
            result = self._detector.detect(image)
            inference_time = result.inference_time_ms

            # 准备返回结果
            boxes_data = []
            for box in result.boxes:
                box_dict = {
                    "x1": float(box.x1),
                    "y1": float(box.y1),
                    "x2": float(box.x2),
                    "y2": float(box.y2),
                    "confidence": float(box.confidence),
                    "class_id": box.class_id,
                    "class_name": box.class_name,
                }
                boxes_data.append(box_dict)

            # 绘制结果（如果需要）
            output_image = None
            if draw_results or return_image:
                output_image = self._draw_results(image.copy(), result.boxes)

            # 更新性能统计
            self._update_performance_stats(inference_time)

            with self._state_lock:
                self._state = DetectorState.READY

            return DetectionResult(
                success=True,
                boxes=boxes_data,
                image=output_image if return_image else None,
                inference_time_ms=inference_time,
            )

        except Exception as e:
            logger.error(f"检测失败: {e}")
            with self._state_lock:
                self._state = DetectorState.ERROR

            return DetectionResult(
                success=False,
                error_message=str(e),
                inference_time_ms=(time.time() - start_time) * 1000,
            )

    def detect_batch(
        self, images: List[np.ndarray], progress_callback: callable = None
    ) -> List[DetectionResult]:
        """
        批量检测图像

        Args:
            images: 图像列表
            progress_callback: 进度回调函数 (completed, total)

        Returns:
            检测结果列表
        """
        results = []
        total = len(images)

        for i, image in enumerate(images):
            result = self.detect(image)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def detect_from_path(
        self, image_path: str, draw_results: bool = False
    ) -> DetectionResult:
        """
        从文件路径检测图像

        Args:
            image_path: 图像文件路径
            draw_results: 是否绘制检测结果

        Returns:
            DetectionResult
        """
        if not os.path.exists(image_path):
            return DetectionResult(
                success=False, error_message=f"文件不存在: {image_path}"
            )

        image = cv2.imread(image_path)
        if image is None:
            return DetectionResult(
                success=False, error_message=f"无法读取图像: {image_path}"
            )

        result = self.detect(image, draw_results=draw_results)

        if draw_results and result.success and result.image is not None:
            output_path = self._get_output_path(image_path)
            cv2.imwrite(output_path, result.image)
            result.output_path = output_path

        return result

    def detect_from_bytes(
        self,
        image_bytes: bytes,
        image_format: str = "jpeg",
        draw_results: bool = False,
    ) -> DetectionResult:
        """
        从字节数据检测图像

        Args:
            image_bytes: 图像字节数据
            image_format: 图像格式 (jpeg, png等)
            draw_results: 是否绘制检测结果

        Returns:
            DetectionResult
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return DetectionResult(
                success=False, error_message="无法解码图像数据"
            )

        return self.detect(image, draw_results=draw_results)

    def _draw_results(self, image: np.ndarray, boxes: List) -> np.ndarray:
        """绘制检测结果"""
        for box in boxes:
            # 边界框
            x1 = int(box.x1 * image.shape[1])
            y1 = int(box.y1 * image.shape[0])
            x2 = int(box.x2 * image.shape[1])
            y2 = int(box.y2 * image.shape[0])

            # 随机颜色
            color = tuple(np.random.randint(0, 255, 3).tolist())

            # 绘制边界框
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            # 绘制标签
            label = f"{box.class_name}: {box.confidence:.2f}"
            cv2.putText(
                image,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        return image

    def _get_output_path(self, input_path: str) -> str:
        """获取输出文件路径"""
        path = Path(input_path)
        return str(path.parent / f"detected_{path.name}")

    def _update_performance_stats(self, inference_time: float):
        """更新性能统计"""
        current_time = time.time()

        if "last_inference_time" not in self._performance_stats:
            self._performance_stats["last_inference_time"] = inference_time
            self._performance_stats["total_inferences"] = 1
            self._performance_stats["total_time"] = inference_time
        else:
            self._performance_stats["total_inferences"] += 1
            self._performance_stats["total_time"] += inference_time

        avg_time = (
            self._performance_stats["total_time"]
            / self._performance_stats["total_inferences"]
        )
        self._performance_stats["avg_inference_time"] = avg_time
        self._performance_stats["fps"] = 1000 / avg_time if avg_time > 0 else 0
        self._performance_stats["last_update"] = current_time

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "last_inference_time_ms": self._performance_stats.get(
                "last_inference_time", 0
            ),
            "total_inferences": self._performance_stats.get(
                "total_inferences", 0
            ),
            "avg_inference_time_ms": self._performance_stats.get(
                "avg_inference_time", 0
            ),
            "fps": self._performance_stats.get("fps", 0),
            "state": self._state.value,
        }

    def reset_stats(self):
        """重置统计"""
        self._performance_stats = {}
        if self._detector:
            self._detector.reset_stats()

    def register_callback(self, event: str, callback: callable):
        """
        注册回调函数

        支持的事件:
            - on_model_loaded: 模型加载完成
            - on_warmup_complete: 预热完成
            - on_detection_complete: 检测完成
            - on_error: 发生错误
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _trigger_callback(self, event: str, data: dict):
        """触发回调"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {e}")

    def get_state(self) -> str:
        """获取当前状态"""
        return self._state.value

    def get_class_names(self) -> List[str]:
        """获取类别名称"""
        if self._detector:
            return self._detector.class_names
        return []

    def get_input_size(self) -> Tuple[int, int]:
        """获取输入尺寸"""
        if self._detector:
            return self._detector.input_size
        return self.config.input_size

    def release(self):
        """释放资源"""
        if self._detector:
            self._detector.release()
        self._state = DetectorState.UNINITIALIZED
        logger.info("检测器资源已释放")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()

    def __del__(self):
        """析构函数"""
        self.release()


# 便捷函数
def create_detector_api(
    model_path: str, config: APIConfig = None
) -> CPUDetectorAPI:
    """
    创建CPU检测器API的便捷函数

    Args:
        model_path: 模型文件路径
        config: API配置

    Returns:
        CPUDetectorAPI实例
    """
    api = CPUDetectorAPI(config)

    if model_path:
        if not api.load_model(model_path):
            raise RuntimeError(f"无法加载模型: {model_path}")

    return api


if __name__ == "__main__":
    print("测试CPU检测器API...")

    # 创建API实例
    api = CPUDetectorAPI()

    # 获取配置
    print("当前配置:")
    print(json.dumps(api.get_config(), indent=2, ensure_ascii=False))

    # 检查状态
    print(f"当前状态: {api.get_state()}")

    print("API测试完成!")
