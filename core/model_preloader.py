#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型预加载管理器

在程序启动时预加载OCR和YOLO模型，提升首次使用时的响应速度。

Author: Vision System Team
Date: 2026-03-11
"""

import logging
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_logger = logging.getLogger("ModelPreloader")


class ModelPreloader:
    """模型预加载管理器（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._preload_thread = None
        self._preload_complete = threading.Event()
        self._models_to_preload = []
        self._preload_status = {
            "ocr": {"loading": False, "loaded": False, "error": None},
            "yolo": {"loading": False, "loaded": False, "error": None},
        }

    def preload_all(self, model_types=None):
        """预加载所有模型

        Args:
            model_types: 要预加载的模型类型列表，None表示全部
        """
        if model_types is None:
            model_types = ["ocr", "yolo"]

        self._models_to_preload = model_types
        _logger.info(f"开始预加载模型: {model_types}")

        for model_type in model_types:
            if model_type == "ocr":
                self._preload_ocr_async()
            elif model_type == "yolo":
                self._preload_yolo_async()

    def _preload_ocr_async(self):
        """异步预加载OCR模型"""
        if self._preload_status["ocr"]["loaded"]:
            _logger.info("OCR模型已预加载")
            return

        if self._preload_status["ocr"]["loading"]:
            _logger.info("OCR模型正在加载中")
            return

        self._preload_status["ocr"]["loading"] = True
        thread = threading.Thread(
            target=self._preload_ocr,
            name="OCR_Preloader",
            daemon=True
        )
        thread.start()
        _logger.info("OCR模型预加载线程已启动")

    def _preload_ocr(self):
        """预加载OCR模型"""
        try:
            _logger.info("开始预加载OCR模型...")
            from tools.vision.ocr import OCRReader

            model = OCRReader._get_ocr_model()
            if model is not None:
                self._preload_status["ocr"]["loaded"] = True
                _logger.info("OCR模型预加载完成")
            else:
                self._preload_status["ocr"]["error"] = "模型初始化失败"
                _logger.error("OCR模型预加载失败")
        except Exception as e:
            self._preload_status["ocr"]["error"] = str(e)
            _logger.error(f"OCR模型预加载异常: {e}")
        finally:
            self._preload_status["ocr"]["loading"] = False

    def _preload_yolo_async(self):
        """异步预加载YOLO模型"""
        if self._preload_status["yolo"]["loaded"]:
            _logger.info("YOLO模型已预加载")
            return

        if self._preload_status["yolo"]["loading"]:
            _logger.info("YOLO模型正在加载中")
            return

        self._preload_status["yolo"]["loading"] = True
        thread = threading.Thread(
            target=self._preload_yolo,
            name="YOLO_Preloader",
            daemon=True
        )
        thread.start()
        _logger.info("YOLO模型预加载线程已启动")

    def _preload_yolo(self):
        """预加载YOLO模型"""
        try:
            _logger.info("开始预加载YOLO模型...")
            from tools.vision.cpu_optimization import CPUDetector
            from modules.cpu_optimization.models.yolo26_cpu import YOLO26CPUDetector
            from modules.cpu_optimization.models.yolo26_cpu import CPUInferenceConfig

            config = CPUInferenceConfig(conf_threshold=0.25, nms_threshold=0.45)
            detector = YOLO26CPUDetector(config)

            model_path = "data/models/yolo26n.pt"
            if os.path.exists(model_path):
                detector.load_model(model_path)
                self._preload_status["yolo"]["loaded"] = True
                _logger.info(f"YOLO模型预加载完成: {model_path}")
            else:
                self._preload_status["yolo"]["error"] = f"模型文件不存在: {model_path}"
                _logger.warning(f"YOLO模型文件不存在: {model_path}")
        except Exception as e:
            self._preload_status["yolo"]["error"] = str(e)
            _logger.error(f"YOLO模型预加载异常: {e}")
        finally:
            self._preload_status["yolo"]["loading"] = False

    def wait_for_completion(self, timeout=None):
        """等待模型预加载完成

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否所有模型都加载成功
        """
        self._preload_complete.wait(timeout)

        all_loaded = all(
            status["loaded"] or status["error"] is not None
            for status in self._preload_status.values()
        )
        return all_loaded

    def get_status(self):
        """获取预加载状态

        Returns:
            dict: 预加载状态
        """
        return self._preload_status.copy()

    def is_model_ready(self, model_type: str) -> bool:
        """检查模型是否就绪

        Args:
            model_type: 模型类型 ("ocr" 或 "yolo")

        Returns:
            bool: 模型是否就绪
        """
        return self._preload_status.get(model_type, {}).get("loaded", False)


def preload_models(model_types=None, wait=True):
    """便捷函数：预加载模型

    Args:
        model_types: 要预加载的模型类型列表
        wait: 是否等待加载完成

    Returns:
        ModelPreloader: 预加载器实例
    """
    preloader = ModelPreloader()
    preloader.preload_all(model_types)

    if wait:
        preloader.wait_for_completion(timeout=120)

    return preloader


def is_model_ready(model_type: str) -> bool:
    """便捷函数：检查模型是否就绪

    Args:
        model_type: 模型类型

    Returns:
        bool: 模型是否就绪
    """
    return ModelPreloader().is_model_ready(model_type)
