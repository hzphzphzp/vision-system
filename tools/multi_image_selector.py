#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多图像选择器工具模块

支持加载多张图片，提供上一张/下一张切换功能
切换图片后自动运行流程

Author: Vision System Team
Date: 2026-02-09
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import (
    ImageData,
    ImageSourceToolBase,
    ToolParameter,
    ToolRegistry,
)
from data.image_data import ResultData


@ToolRegistry.register
class MultiImageSelector(ImageSourceToolBase):
    """多图像选择器工具 - 支持加载多张图片并切换"""

    tool_name = "多图像选择器"
    tool_category = "ImageSource"
    tool_description = "加载多张图片，支持上一张/下一张切换，切换后自动运行流程"

    _auto_run_callback = None

    def __init__(self, name: str = None):
        super().__init__(name)
        self._image_paths: List[str] = []
        self._current_index: int = 0
        self._last_index: int = -1

    def _init_params(self):
        """初始化默认参数"""
        self.set_param(
            "图像文件列表",
            [],
            param_type="file_list",
            description="图像文件列表(可多选)",
        )
        self.set_param(
            "当前图像索引",
            0,
            param_type="integer",
            description="当前图像索引",
        )
        self.set_param(
            "自动运行",
            True,
            param_type="boolean",
            description="切换图像后自动运行流程",
        )
        self.set_param(
            "循环模式",
            True,
            param_type="boolean",
            description="循环模式(到最后一张后回到第一张)",
        )

    @classmethod
    def set_auto_run_callback(cls, callback):
        """设置自动运行回调函数
        
        Args:
            callback: 切换图像后调用的函数，无参数
        """
        cls._auto_run_callback = callback

    def load_images(self, file_paths: List[str]):
        """加载多张图片
        
        Args:
            file_paths: 图片文件路径列表
        """
        if not file_paths:
            return
        
        valid_paths = [p for p in file_paths if os.path.exists(p)]
        if not valid_paths:
            raise Exception("没有有效的图像文件")
        
        self._image_paths = valid_paths
        self._current_index = 0
        self.set_param("图像文件列表", valid_paths)
        self.set_param("当前图像索引", 0)
        
        self._logger.info(f"加载了 {len(valid_paths)} 张图片")

    def add_images(self, file_paths: List[str]):
        """添加图片到列表
        
        Args:
            file_paths: 要添加的图片文件路径列表
        """
        if not file_paths:
            return
        
        valid_paths = [p for p in file_paths if os.path.exists(p)]
        self._image_paths.extend(valid_paths)
        self.set_param("图像文件列表", self._image_paths)
        
        self._logger.info(f"添加了 {len(valid_paths)} 张图片，总共 {len(self._image_paths)} 张")

    def clear_images(self):
        """清空图片列表"""
        self._image_paths = []
        self._current_index = 0
        self.set_param("图像文件列表", [])
        self.set_param("当前图像索引", 0)
        self._logger.info("清空图片列表")

    def get_current_image_path(self) -> Optional[str]:
        """获取当前图片路径"""
        if not self._image_paths:
            return None
        if 0 <= self._current_index < len(self._image_paths):
            return self._image_paths[self._current_index]
        return None

    def get_current_image_info(self) -> Dict[str, Any]:
        """获取当前图片信息"""
        return {
            "index": self._current_index,
            "total": len(self._image_paths),
            "path": self.get_current_image_path(),
            "file_name": os.path.basename(self.get_current_image_path()) if self.get_current_image_path() else "",
        }

    def previous_image(self) -> bool:
        """切换到上一张图片
        
        Returns:
            是否切换成功
        """
        if not self._image_paths:
            return False
        
        loop_mode = self.get_param("循环模式", True)
        
        if self._current_index > 0:
            self._current_index -= 1
        elif loop_mode:
            self._current_index = len(self._image_paths) - 1
        else:
            return False
        
        self.set_param("当前图像索引", self._current_index)
        info = self.get_current_image_info()
        self._logger.info(f"切换到上一张: [{info['index']+1}/{info['total']}] {info.get('file_name', '')}")
        
        self._trigger_auto_run()
        return True

    def next_image(self) -> bool:
        """切换到下一张图片
        
        Returns:
            是否切换成功
        """
        if not self._image_paths:
            return False
        
        loop_mode = self.get_param("循环模式", True)
        
        if self._current_index < len(self._image_paths) - 1:
            self._current_index += 1
        elif loop_mode:
            self._current_index = 0
        else:
            return False
        
        self.set_param("当前图像索引", self._current_index)
        info = self.get_current_image_info()
        self._logger.info(f"切换到下一张: [{info['index']+1}/{info['total']}] {info.get('file_name', '')}")
        
        self._trigger_auto_run()
        return True

    def goto_image(self, index: int) -> bool:
        """跳转到指定索引的图片
        
        Args:
            index: 目标索引
            
        Returns:
            是否跳转成功
        """
        if not self._image_paths:
            return False
        
        if 0 <= index < len(self._image_paths):
            self._current_index = index
            self.set_param("当前图像索引", index)
            info = self.get_current_image_info()
            self._logger.info(f"跳转到图片 {index}: [{info['index']+1}/{info['total']}] {info.get('file_name', '')}")
            
            self._trigger_auto_run()
            return True
        return False

    def _trigger_auto_run(self):
        """触发自动运行流程"""
        auto_run = self.get_param("自动运行", True)
        
        if auto_run and self._auto_run_callback:
            if self._current_index != self._last_index:
                self._last_index = self._current_index
                self._logger.info("触发自动运行流程")
                try:
                    if callable(self._auto_run_callback):
                        self._auto_run_callback()
                except TypeError as te:
                    self._logger.warning(f"回调函数参数不匹配: {te}")
                    try:
                        callback = self._auto_run_callback
                        if hasattr(callback, '__func__'):
                            callback.__func__()
                    except Exception as e2:
                        self._logger.error(f"自动运行失败: {e2}")
                except Exception as e:
                    self._logger.error(f"自动运行失败: {e}")

    def _run_impl(self):
        """执行图像采集 - 加载当前索引的图片"""
        image_files = self.get_param("图像文件列表", [])
        if image_files:
            self._image_paths = image_files
        
        if not self._image_paths:
            raise Exception("没有加载图像文件，请先选择图像文件")
        
        self._current_index = self.get_param("当前图像索引", 0)
        
        if self._current_index >= len(self._image_paths):
            self._current_index = 0
        
        current_path = self.get_current_image_path()
        if not current_path:
            raise Exception("当前没有可读取的图像")
        
        try:
            image_data = np.fromfile(current_path, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        except Exception:
            image = cv2.imread(current_path)
        
        if image is None:
            raise Exception(f"无法读取图像: {current_path}")
        
        height, width, channels = image.shape
        img_data = ImageData(image, width, height, channels)
        
        self._result_data = ResultData()
        self._result_data.tool_name = self._name
        self._result_data.result_category = "image"
        self._result_data.set_value("current_index", self._current_index)
        self._result_data.set_value("total_images", len(self._image_paths))
        self._result_data.set_value("current_path", current_path)
        self._result_data.set_value("file_name", os.path.basename(current_path))
        
        return {
            "OutputImage": img_data,
            "Width": width,
            "Height": height,
            "Channels": channels,
            "CurrentIndex": self._current_index,
            "TotalImages": len(self._image_paths),
            "CurrentPath": current_path,
            "FileName": os.path.basename(current_path),
        }

    def get_result(self, key: str = None):
        """获取结果数据
        
        Args:
            key: 可选的键名（为了兼容基类接口）
        """
        if self._result_data is None:
            self._result_data = ResultData()
            self._result_data.tool_name = self._name
        return self._result_data

    def reset(self):
        """重置工具状态"""
        super().reset()
        self._current_index = 0
        self._last_index = -1
        self._logger.info("多图像选择器已重置")

    def get_available_images_list(self) -> List[str]:
        """获取可用图片列表(用于下拉框显示)"""
        if not self._image_paths:
            return ["未加载图片"]
        
        result = []
        for i, path in enumerate(self._image_paths):
            filename = os.path.basename(path)
            marker = "▶ " if i == self._current_index else "   "
            result.append(f"{marker}[{i+1}/{len(self._image_paths)}] {filename}")
        return result

    def refresh_from_params(self):
        """从参数刷新内部状态"""
        image_files = self.get_param("图像文件列表", [])
        if image_files:
            self._image_paths = image_files
        self._current_index = self.get_param("当前图像索引", 0)
