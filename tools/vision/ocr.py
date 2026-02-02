#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR工具模块

提供文字识别功能，基于EasyOCR。

Author: Vision System Team
Date: 2025-01-12
"""

import gc
import logging
import os
import sys
import time
from threading import Lock
from typing import Any, Dict, List, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config.config_manager import get_config
from core.tool_base import RecognitionToolBase, ToolParameter, ToolRegistry
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException

_logger = logging.getLogger("OCR")


@ToolRegistry.register
class OCRReader(RecognitionToolBase):
    """
    OCR文字识别工具

    基于EasyOCR，支持中英文识别。

    参数说明：
    - language: 识别语言，支持ch_sim(简体中文)、en(英文)等
    - min_confidence: 最小置信度阈值
    - text_only: 是否只返回文本（不返回位置信息）
    """

    tool_name = "OCR识别"
    tool_category = "Recognition"
    tool_description = "识别图像中的文字"

    _ocr_model = None
    _ocr_model_lock = Lock()
    _last_used_time = 0
    _max_idle_time = 300  # 5分钟无使用则自动释放（秒）

    PARAM_DEFINITIONS = {
        "language": ToolParameter(
            name="识别语言",
            param_type="enum",
            default="ch_sim",
            description="OCR识别语言",
            options=[
                "ch_sim",
                "en",
                "ja",
                "ko",
                "ch_sim+en",
                "en+ch_sim",
                "all",
            ],
        ),
        "min_confidence": ToolParameter(
            name="最小置信度",
            param_type="float",
            default=0.5,
            description="最小置信度阈值(0-1)",
            min_value=0.0,
            max_value=1.0,
        ),
        "text_only": ToolParameter(
            name="仅返回文本",
            param_type="boolean",
            default=True,
            description="是否只返回识别文本，不返回位置信息",
        ),
        "skip_special": ToolParameter(
            name="过滤特殊字符",
            param_type="boolean",
            default=True,
            description="是否过滤非打印字符",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        # 从配置管理器获取默认配置
        default_language = get_config("ocr.language", "ch_sim")
        default_confidence = get_config("ocr.min_confidence", 0.5)
        default_text_only = get_config("ocr.text_only", True)
        default_skip_special = get_config("ocr.skip_special", True)

        self.set_param("language", default_language)
        self.set_param("min_confidence", default_confidence)
        self.set_param("text_only", default_text_only)
        self.set_param("skip_special", default_skip_special)

    @classmethod
    def _get_ocr_model(cls):
        """获取OCR模型（单例模式）"""
        # 检查是否需要自动释放（超过最大空闲时间）
        if cls._ocr_model is not None:
            idle_time = time.time() - cls._last_used_time
            if idle_time > cls._max_idle_time:
                _logger.info(f"OCR模型空闲{idle_time:.1f}秒，自动释放内存")
                cls.release_model()

        if cls._ocr_model is None:
            with cls._ocr_model_lock:
                if cls._ocr_model is None:
                    _logger.info("初始化EasyOCR模型...")
                    try:
                        import easyocr

                        cls._ocr_model = easyocr.Reader(
                            ["ch_sim", "en"], gpu=False
                        )
                        cls._last_used_time = time.time()
                        _logger.info("EasyOCR模型初始化完成")
                    except Exception as e:
                        _logger.error(f"初始化EasyOCR失败: {e}")
                        raise ToolException(f"OCR模型初始化失败: {e}")

        # 更新最后使用时间
        cls._last_used_time = time.time()
        return cls._ocr_model

    @classmethod
    def release_model(cls):
        """释放OCR模型内存"""
        with cls._ocr_model_lock:
            if cls._ocr_model is not None:
                _logger.info("释放OCR模型内存...")
                try:
                    # 删除模型引用
                    del cls._ocr_model
                    cls._ocr_model = None
                    cls._last_used_time = 0
                    # 强制垃圾回收
                    gc.collect()
                    _logger.info("OCR模型内存已释放")
                except Exception as e:
                    _logger.warning(f"释放OCR模型时发生错误: {e}")

    @classmethod
    def get_model_memory_usage(cls) -> Dict[str, Any]:
        """获取模型内存使用情况"""
        with cls._ocr_model_lock:
            if cls._ocr_model is None:
                return {"loaded": False, "idle_time": 0}

            idle_time = time.time() - cls._last_used_time
            return {
                "loaded": True,
                "idle_time": idle_time,
                "max_idle_time": cls._max_idle_time,
                "will_auto_release": idle_time > cls._max_idle_time,
            }

    def _run_impl(self):
        """执行OCR识别"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data
        h, w = input_image.shape[:2]

        language = self.get_param("language", "ch_sim")
        min_confidence = self.get_param("min_confidence", 0.5)
        text_only = self.get_param("text_only", True)
        skip_special = self.get_param("skip_special", True)

        self._logger.info(
            f"开始OCR识别: language={language}, min_confidence={min_confidence}"
        )

        try:
            reader = self._get_ocr_model()

            if len(input_image.shape) == 3:
                result = reader.readtext(input_image)
            else:
                result = reader.readtext(
                    cv2.cvtColor(input_image, cv2.COLOR_GRAY2BGR)
                )

            texts = []
            detailed_results = []

            for detection in result:
                bbox, text, confidence = detection

                if confidence < min_confidence:
                    continue

                if skip_special:
                    cleaned_text = "".join(c for c in text if c.isprintable())
                else:
                    cleaned_text = text

                if cleaned_text.strip():
                    texts.append(cleaned_text)

                    if not text_only:
                        detailed_results.append(
                            {
                                "text": cleaned_text,
                                "confidence": float(confidence),
                                "bbox": [[int(x), int(y)] for x, y in bbox],
                            }
                        )

            self._result_data = ResultData()
            self._result_data.set_value("text_count", len(texts))
            self._result_data.set_value("texts", texts)
            self._result_data.set_value("full_text", "\n".join(texts))

            if not text_only:
                self._result_data.set_value("results", detailed_results)

            # 绘制结果到输出图像
            output_image = input_image.copy()
            if len(output_image.shape) == 2:
                output_image = cv2.cvtColor(output_image, cv2.COLOR_GRAY2BGR)

            # 转换为PIL图像以支持中文
            pil_image = Image.fromarray(
                cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            )
            draw = ImageDraw.Draw(pil_image)

            # 尝试加载中文字体
            try:
                font_path = "C:/Windows/Fonts/msyh.ttc"
                font = ImageFont.truetype(font_path, 16)
            except:
                font = ImageFont.load_default()

            # 只有当detailed_results存在时才绘制
            if detailed_results:
                for i, (text, conf, bbox) in enumerate(
                    zip(
                        texts,
                        [d["confidence"] for d in detailed_results],
                        [d["bbox"] for d in detailed_results],
                    )
                ):
                    # 绘制检测框
                    pts = [tuple(p) for p in bbox]
                    draw.line(pts + [pts[0]], fill=(0, 255, 0), width=2)

                    # 绘制文本（使用PIL支持中文）
                    text_pos = (bbox[0][0], bbox[0][1] - 20)
                    draw.text(
                        text_pos,
                        f"{text} ({conf:.2f})",
                        fill=(0, 255, 0),
                        font=font,
                    )

            # 转回OpenCV格式
            output_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            self._output_data = self._input_data.copy()
            self._output_data.data = output_image

            self._logger.info(f"OCR识别完成: 找到{len(texts)}个文本")

        except Exception as e:
            self._logger.error(f"OCR识别失败: {e}")
            raise ToolException(f"OCR识别失败: {e}")


@ToolRegistry.register
class OCREnglish(RecognitionToolBase):
    """
    英文字符识别工具

    专门优化用于英文识别，速度更快。

    参数说明：
    - min_confidence: 最小置信度阈值
    - text_only: 是否只返回文本
    """

    tool_name = "英文OCR"
    tool_category = "Recognition"
    tool_description = "识别图像中的英文字符"

    _ocr_model = None
    _ocr_model_lock = Lock()
    _last_used_time = 0
    _max_idle_time = 300  # 5分钟无使用则自动释放（秒）

    PARAM_DEFINITIONS = {
        "min_confidence": ToolParameter(
            name="最小置信度",
            param_type="float",
            default=0.5,
            description="最小置信度阈值(0-1)",
            min_value=0.0,
            max_value=1.0,
        ),
        "text_only": ToolParameter(
            name="仅返回文本",
            param_type="boolean",
            default=True,
            description="是否只返回识别文本，不返回位置信息",
        ),
        "skip_special": ToolParameter(
            name="过滤特殊字符",
            param_type="boolean",
            default=True,
            description="是否过滤非打印字符",
        ),
    }

    def _init_params(self):
        """初始化默认参数"""
        # 从配置管理器获取默认配置
        default_confidence = get_config("ocr.min_confidence", 0.5)
        default_text_only = get_config("ocr.text_only", True)
        default_skip_special = get_config("ocr.skip_special", True)

        self.set_param("min_confidence", default_confidence)
        self.set_param("text_only", default_text_only)
        self.set_param("skip_special", default_skip_special)

    @classmethod
    def _get_ocr_model(cls):
        """获取OCR模型（单例模式）"""
        # 检查是否需要自动释放（超过最大空闲时间）
        if cls._ocr_model is not None:
            idle_time = time.time() - cls._last_used_time
            if idle_time > cls._max_idle_time:
                _logger.info(f"英文OCR模型空闲{idle_time:.1f}秒，自动释放内存")
                cls.release_model()

        if cls._ocr_model is None:
            with cls._ocr_model_lock:
                if cls._ocr_model is None:
                    _logger.info("初始化英文OCR模型...")
                    try:
                        import easyocr

                        cls._ocr_model = easyocr.Reader(["en"], gpu=False)
                        cls._last_used_time = time.time()
                        _logger.info("英文OCR模型初始化完成")
                    except Exception as e:
                        _logger.error(f"初始化英文OCR失败: {e}")
                        raise ToolException(f"OCR模型初始化失败: {e}")

        # 更新最后使用时间
        cls._last_used_time = time.time()
        return cls._ocr_model

    @classmethod
    def release_model(cls):
        """释放OCR模型内存"""
        with cls._ocr_model_lock:
            if cls._ocr_model is not None:
                _logger.info("释放英文OCR模型内存...")
                try:
                    # 删除模型引用
                    del cls._ocr_model
                    cls._ocr_model = None
                    cls._last_used_time = 0
                    # 强制垃圾回收
                    gc.collect()
                    _logger.info("英文OCR模型内存已释放")
                except Exception as e:
                    _logger.warning(f"释放英文OCR模型时发生错误: {e}")

    @classmethod
    def get_model_memory_usage(cls) -> Dict[str, Any]:
        """获取模型内存使用情况"""
        with cls._ocr_model_lock:
            if cls._ocr_model is None:
                return {"loaded": False, "idle_time": 0}

            idle_time = time.time() - cls._last_used_time
            return {
                "loaded": True,
                "idle_time": idle_time,
                "max_idle_time": cls._max_idle_time,
                "will_auto_release": idle_time > cls._max_idle_time,
            }

    def _run_impl(self):
        """执行英文OCR识别"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data

        min_confidence = self.get_param("min_confidence", 0.5)
        text_only = self.get_param("text_only", True)
        skip_special = self.get_param("skip_special", True)

        self._logger.info(f"开始英文OCR识别: min_confidence={min_confidence}")

        try:
            reader = self._get_ocr_model()

            if len(input_image.shape) == 3:
                result = reader.readtext(input_image)
            else:
                result = reader.readtext(
                    cv2.cvtColor(input_image, cv2.COLOR_GRAY2BGR)
                )

            texts = []
            detailed_results = []

            for detection in result:
                bbox, text, confidence = detection

                if confidence < min_confidence:
                    continue

                if skip_special:
                    cleaned_text = "".join(c for c in text if c.isprintable())
                else:
                    cleaned_text = text

                if cleaned_text.strip():
                    texts.append(cleaned_text)

                    if not text_only:
                        detailed_results.append(
                            {
                                "text": cleaned_text,
                                "confidence": float(confidence),
                                "bbox": [[int(x), int(y)] for x, y in bbox],
                            }
                        )

            self._result_data = ResultData()
            self._result_data.set_value("text_count", len(texts))
            self._result_data.set_value("texts", texts)
            self._result_data.set_value("full_text", "\n".join(texts))

            if not text_only:
                self._result_data.set_value("results", detailed_results)

            # 绘制结果到输出图像
            output_image = input_image.copy()
            if len(output_image.shape) == 2:
                output_image = cv2.cvtColor(output_image, cv2.COLOR_GRAY2BGR)

            # 转换为PIL图像以支持中文
            pil_image = Image.fromarray(
                cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
            )
            draw = ImageDraw.Draw(pil_image)

            # 尝试加载中文字体
            try:
                font_path = "C:/Windows/Fonts/msyh.ttc"
                font = ImageFont.truetype(font_path, 16)
            except:
                font = ImageFont.load_default()

            # 只有当detailed_results存在时才绘制
            if detailed_results:
                for i, (text, conf, bbox) in enumerate(
                    zip(
                        texts,
                        [d["confidence"] for d in detailed_results],
                        [d["bbox"] for d in detailed_results],
                    )
                ):
                    # 绘制检测框
                    pts = [tuple(p) for p in bbox]
                    draw.line(pts + [pts[0]], fill=(0, 255, 0), width=2)

                    # 绘制文本（使用PIL支持中文）
                    text_pos = (bbox[0][0], bbox[0][1] - 20)
                    draw.text(
                        text_pos,
                        f"{text} ({conf:.2f})",
                        fill=(0, 255, 0),
                        font=font,
                    )

            # 转回OpenCV格式
            output_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            self._output_data = self._input_data.copy()
            self._output_data.data = output_image

            self._logger.info(f"英文OCR识别完成: 找到{len(texts)}个文本")

        except Exception as e:
            self._logger.error(f"英文OCR识别失败: {e}")
            raise ToolException(f"OCR识别失败: {e}")
