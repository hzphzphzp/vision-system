#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像切片工具模块

对匹配到的目标区域进行精确切片处理，支持多结果浏览。

Author: Vision System Team
Date: 2026-02-27
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ImageData, ToolParameter, ToolRegistry, VisionAlgorithmToolBase
from data.image_data import ResultData
from utils.exceptions import ToolException


class SliceMode:
    """切片模式"""
    EXTRACT = "extract"
    REMOVE = "remove"


@ToolRegistry.register
class ImageSliceTool(VisionAlgorithmToolBase):
    """
    图像切片工具

    对匹配到的目标区域进行精确切片处理。
    支持从上游工具获取匹配结果，并对其进行处理。

    参数说明：
    - match_source: 匹配数据来源（从上游工具获取）
    - slice_mode: 切片模式（提取/去除）
    - slice_region: 切片区域类型（匹配区域/自定义）
    - offset_x: X方向偏移
    - offset_y: Y方向偏移
    - slice_width: 切片宽度（0表示使用匹配区域宽度）
    - slice_height: 切片高度（0表示使用匹配区域高度）
    - current_result_index: 当前结果索引
    """

    tool_name = "图像切片"
    tool_category = "Vision"
    tool_description = "对匹配目标进行精确切片处理，支持多结果浏览"

    PARAM_DEFINITIONS = {
        "目标连接": ToolParameter(
            name="目标连接",
            param_type="data_content",
            default="",
            description="从上游工具获取匹配结果",
        ),
        "切片模式": ToolParameter(
            name="切片模式",
            param_type="enum",
            default="extract",
            description="切片模式",
            options=["extract", "remove"],
            option_labels={
                "extract": "提取（保留选中区域）",
                "remove": "去除（删除选中区域）",
            },
        ),
        "切片区域": ToolParameter(
            name="切片区域",
            param_type="enum",
            default="match",
            description="切片区域类型",
            options=["match", "custom"],
            option_labels={
                "match": "使用匹配区域",
                "custom": "自定义区域",
            },
        ),
        "偏移X": ToolParameter(
            name="偏移X",
            param_type="integer",
            default=0,
            description="X方向偏移（像素）",
            min_value=-1000,
            max_value=1000,
        ),
        "偏移Y": ToolParameter(
            name="偏移Y",
            param_type="integer",
            default=0,
            description="Y方向偏移（像素）",
            min_value=-1000,
            max_value=1000,
        ),
        "宽度": ToolParameter(
            name="宽度",
            param_type="integer",
            default=0,
            description="切片宽度（0表示使用匹配区域宽度）",
            min_value=0,
            max_value=5000,
        ),
        "高度": ToolParameter(
            name="高度",
            param_type="integer",
            default=0,
            description="切片高度（0表示使用匹配区域高度）",
            min_value=0,
            max_value=5000,
        ),
        "结果索引": ToolParameter(
            name="结果索引",
            param_type="integer",
            default=0,
            description="当前结果索引（用于多结果浏览）",
            min_value=0,
            max_value=1000,
        ),
        "自动切换": ToolParameter(
            name="自动切换",
            param_type="boolean",
            default=True,
            description="切换索引后自动运行流程",
        ),
        "运行后递增": ToolParameter(
            name="运行后递增",
            param_type="boolean",
            default=False,
            description="每次运行完成后索引自动+1，实现循环浏览",
        ),
    }

    _auto_run_callback = None
    _upstream_tool_name: str = None
    _all_matches: List[Dict[str, Any]] = []
    _current_match_index: int = 0

    def __init__(self, name: str = None):
        super().__init__(name)
        self._input_matches: List[Dict[str, Any]] = []
        self._current_index: int = 0

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("目标连接", "")
        self.set_param("切片模式", "extract")
        self.set_param("切片区域", "match")
        self.set_param("偏移X", 0)
        self.set_param("偏移Y", 0)
        self.set_param("宽度", 0)
        self.set_param("高度", 0)
        self.set_param("结果索引", 0)
        self.set_param("自动切换", True)
        self.set_param("运行后递增", False)

    @classmethod
    def set_auto_run_callback(cls, callback):
        """设置自动运行回调函数
        
        Args:
            callback: 切换索引后调用的函数
        """
        cls._auto_run_callback = callback

    def set_upstream_data(self, tool_name: str, matches: List[Dict[str, Any]]):
        """设置上游工具的匹配结果
        
        Args:
            tool_name: 上游工具名称
            matches: 匹配结果列表
        """
        self._upstream_tool_name = tool_name
        self._all_matches = matches
        self._current_match_index = 0
        self.set_param("结果索引", 0)
        self._logger.info(f"接收到上游工具 {tool_name} 的 {len(matches)} 个匹配结果")

    def get_current_match(self) -> Optional[Dict[str, Any]]:
        """获取当前索引的匹配结果"""
        if not self._all_matches:
            return None
        if 0 <= self._current_match_index < len(self._all_matches):
            return self._all_matches[self._current_match_index]
        return None

    def get_match_count(self) -> int:
        """获取匹配结果总数"""
        return len(self._all_matches)

    def previous_result(self) -> bool:
        """切换到上一个结果
        
        Returns:
            是否切换成功
        """
        if not self._all_matches:
            return False

        if self._current_match_index > 0:
            self._current_match_index -= 1
        else:
            self._current_match_index = len(self._all_matches) - 1

        self.set_param("结果索引", self._current_match_index)
        self._logger.info(f"切换到上一个结果: [{self._current_match_index + 1}/{len(self._all_matches)}]")

        self._trigger_auto_run()
        return True

    def next_result(self) -> bool:
        """切换到下一个结果
        
        Returns:
            是否切换成功
        """
        if not self._all_matches:
            return False

        if self._current_match_index < len(self._all_matches) - 1:
            self._current_match_index += 1
        else:
            self._current_match_index = 0

        self.set_param("结果索引", self._current_match_index)
        self._logger.info(f"切换到下一个结果: [{self._current_match_index + 1}/{len(self._all_matches)}]")

        self._trigger_auto_run()
        return True

    def goto_result(self, index: int) -> bool:
        """跳转到指定索引的结果
        
        Args:
            index: 目标索引
            
        Returns:
            是否跳转成功
        """
        if not self._all_matches:
            return False

        if 0 <= index < len(self._all_matches):
            self._current_match_index = index
            self.set_param("结果索引", index)
            self._logger.info(f"跳转到结果 {index}: [{index + 1}/{len(self._all_matches)}]")
            self._trigger_auto_run()
            return True
        return False

    def _trigger_auto_run(self):
        """触发自动运行流程"""
        auto_run = self.get_param("自动切换", True)

        if auto_run and self._auto_run_callback:
            try:
                if callable(self._auto_run_callback):
                    self._auto_run_callback()
            except Exception as e:
                self._logger.error(f"自动运行失败: {e}")

    def _collect_input_matches(self) -> List[Dict[str, Any]]:
        """从上游工具收集匹配结果"""
        if not self.has_input():
            self._logger.warning("无输入图像")
            return []

        data_connection = self.get_param("目标连接", "")
        if not data_connection:
            self._logger.warning("未设置数据连接")
            return []

        try:
            upstream_values = self.get_upstream_values()
        except Exception as e:
            self._logger.warning(f"获取上游数据失败: {e}")
            return []

        if not upstream_values:
            self._logger.warning("上游数据为空")
            return []

        matches = []

        for key, value in upstream_values.items():
            if key in ["matches", "match_results", "detections"]:
                if isinstance(value, list) and len(value) > 0:
                    for item in value:
                        if isinstance(item, tuple):
                            matches.append({
                                "x": item[0],
                                "y": item[1],
                                "score": item[2] if len(item) > 2 else 0,
                            })
                        elif isinstance(item, dict):
                            matches.append(item)
            elif key == "match_count" and isinstance(value, int):
                count = value
                for i in range(count):
                    match_key = f"match_{i}"
                    if match_key in upstream_values:
                        matches.append(upstream_values[match_key])
            elif key in ["best_x", "best_y", "best_score"]:
                if not matches:
                    best_match = {
                        "x": upstream_values.get("best_x", 0),
                        "y": upstream_values.get("best_y", 0),
                        "score": upstream_values.get("best_score", 0),
                    }
                    width = upstream_values.get("template_width", 0)
                    height = upstream_values.get("template_height", 0)
                    if width and height:
                        best_match["width"] = width
                        best_match["height"] = height
                    if best_match.get("score", 0) > 0:
                        matches.append(best_match)

        self._logger.info(f"从上游数据中提取到 {len(matches)} 个匹配结果，上游数据键: {list(upstream_values.keys())}")
        return matches

    def _calculate_slice_region(
        self, 
        match: Optional[Dict[str, Any]], 
        image_width: int, 
        image_height: int
    ) -> Tuple[int, int, int, int]:
        """计算切片区域
        
        Args:
            match: 匹配结果
            image_width: 图像宽度
            image_height: 图像高度
            
        Returns:
            (x, y, width, height) 切片区域
        """
        slice_region_type = self.get_param("切片区域", "match")
        offset_x = self.get_param("偏移X", 0)
        offset_y = self.get_param("偏移Y", 0)
        custom_width = self.get_param("宽度", 0)
        custom_height = self.get_param("高度", 0)

        if slice_region_type == "custom" or match is None:
            if custom_width > 0 and custom_height > 0:
                x = max(0, min(offset_x, image_width - custom_width))
                y = max(0, min(offset_y, image_height - custom_height))
                return x, y, custom_width, custom_height
            elif match is not None:
                x = match.get("x", 0) + offset_x
                y = match.get("y", 0) + offset_y
                w = match.get("width", custom_width if custom_width > 0 else 100)
                h = match.get("height", custom_height if custom_height > 0 else 100)
                return x, y, w, h
            else:
                return offset_x, offset_y, custom_width if custom_width > 0 else 100, custom_height if custom_height > 0 else 100
        else:
            x = match.get("x", 0) + offset_x
            y = match.get("y", 0) + offset_y
            w = custom_width if custom_width > 0 else match.get("width", 100)
            h = custom_height if custom_height > 0 else match.get("height", 100)
            return x, y, w, h

    def _run_impl(self):
        """执行图像切片"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data
        h, w = input_image.shape[:2]

        self._all_matches = self._collect_input_matches()

        self._current_index = self.get_param("结果索引", 0)
        self._current_match_index = self._current_index

        if self._current_index >= len(self._all_matches):
            self._current_index = 0
            self._current_match_index = 0

        match = self.get_current_match()

        slice_mode = self.get_param("切片模式", "extract")

        x, y, slice_w, slice_h = self._calculate_slice_region(match, w, h)

        x = int(max(0, min(x, w - 1)))
        y = int(max(0, min(y, h - 1)))
        slice_w = int(max(1, min(slice_w, w - x)))
        slice_h = int(max(1, min(slice_h, h - y)))

        self._logger.info(
            f"切片区域: x={x}, y={y}, width={slice_w}, height={slice_h}, "
            f"模式={slice_mode}, 匹配数={len(self._all_matches)}, 当前索引={self._current_index}"
        )
        self._logger.debug(f"输入图像尺寸: {w}x{h}, 切片后图像尺寸: {slice_w}x{slice_h}")

        if slice_mode == "extract":
            sliced_image = input_image[y : y + slice_h, x : x + slice_w].copy()
            output_image = sliced_image
        else:
            output_image = input_image.copy()
            output_image[y : y + slice_h, x : x + slice_w] = 0

        self._result_data = ResultData()
        self._result_data.tool_name = self._name
        self._result_data.result_category = "slice"
        self._result_data.set_value("slice_x", x)
        self._result_data.set_value("slice_y", y)
        self._result_data.set_value("slice_width", slice_w)
        self._result_data.set_value("slice_height", slice_h)
        self._result_data.set_value("slice_mode", slice_mode)
        self._result_data.set_value("match_count", len(self._all_matches))
        self._result_data.set_value("current_index", self._current_index)
        self._result_data.set_value("match_info", match)

        if match:
            self._result_data.set_value("match_x", match.get("x", 0))
            self._result_data.set_value("match_y", match.get("y", 0))
            self._result_data.set_value("match_score", match.get("score", 0))

        img_data = ImageData(output_image, slice_w, slice_h, output_image.shape[2] if len(output_image.shape) > 2 else 1)

        self._logger.info(
            f"图像切片完成: 模式={slice_mode}, 结果数={len(self._all_matches)}, "
            f"当前索引={self._current_index}"
        )

        auto_increment = self.get_param("运行后递增", False)
        if auto_increment and len(self._all_matches) > 0:
            next_index = (self._current_index + 1) % len(self._all_matches)
            self.set_param("结果索引", next_index)
            self._current_match_index = next_index
            self._logger.info(f"运行后递增索引: {self._current_index} -> {next_index}, 参数已更新")

        return {
            "OutputImage": img_data,
            "SliceX": x,
            "SliceY": y,
            "SliceWidth": slice_w,
            "SliceHeight": slice_h,
            "MatchCount": len(self._all_matches),
            "CurrentIndex": self._current_index,
        }

    def get_result(self, key: str = None):
        """获取结果数据"""
        if self._result_data is None:
            self._result_data = ResultData()
            self._result_data.tool_name = self._name
        return self._result_data

    def reset(self):
        """重置工具状态"""
        super().reset()
        self._current_index = 0
        self._all_matches = []
        self._logger.info("图像切片工具已重置")

    def get_available_results_list(self) -> List[str]:
        """获取可用结果列表（用于下拉框显示）"""
        if not self._all_matches:
            return ["无匹配结果"]

        result = []
        for i, match in enumerate(self._all_matches):
            score = match.get("score", 0)
            x = match.get("x", 0)
            y = match.get("y", 0)
            marker = "▶ " if i == self._current_index else "   "
            result.append(f"{marker}[{i + 1}/{len(self._all_matches)}] 分数:{score:.2f} 位置:({x},{y})")
        return result
