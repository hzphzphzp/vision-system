#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一IO控制工具模块

将数字输入、数字输出、触发器功能合并为一个工具，通过模式切换。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from data.image_data import ResultData


class IOType(Enum):
    """IO类型"""
    DI = "DI"
    DO = "DO"
    AI = "AI"
    AO = "AO"


class IOState(Enum):
    """IO状态"""
    OFF = 0
    ON = 1
    UNKNOWN = -1


class VirtualIOController:
    """虚拟IO控制器"""

    def __init__(self):
        self._di_states: Dict[int, bool] = {}
        self._do_states: Dict[int, bool] = {}
        self._ai_values: Dict[int, float] = {}
        self._ao_values: Dict[int, float] = {}
        self._lock = threading.Lock()
        self._callbacks: Dict[int, List[Callable]] = {}

    def set_di(self, channel: int, state: bool):
        with self._lock:
            old_state = self._di_states.get(channel, False)
            self._di_states[channel] = state
            if old_state != state and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, state, IOType.DI)
                    except Exception:
                        pass

    def get_di(self, channel: int) -> bool:
        return self._di_states.get(channel, False)

    def set_do(self, channel: int, state: bool):
        with self._lock:
            old_state = self._do_states.get(channel, False)
            self._do_states[channel] = state
            if old_state != state and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, state, IOType.DO)
                    except Exception:
                        pass

    def get_do(self, channel: int) -> bool:
        return self._do_states.get(channel, False)

    def set_ai(self, channel: int, value: float):
        with self._lock:
            old_value = self._ai_values.get(channel, 0.0)
            self._ai_values[channel] = value
            if abs(old_value - value) > 0.001 and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, value, IOType.AI)
                    except Exception:
                        pass

    def get_ai(self, channel: int) -> float:
        return self._ai_values.get(channel, 0.0)

    def set_ao(self, channel: int, value: float):
        with self._lock:
            old_value = self._ao_values.get(channel, 0.0)
            self._ao_values[channel] = value
            if abs(old_value - value) > 0.001 and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, value, IOType.AO)
                    except Exception:
                        pass

    def get_ao(self, channel: int) -> float:
        return self._ao_values.get(channel, 0.0)

    def register_callback(self, channel: int, callback: Callable):
        if channel not in self._callbacks:
            self._callbacks[channel] = []
        self._callbacks[channel].append(callback)

    def get_all_states(self) -> Dict:
        with self._lock:
            return {
                "DI": dict(self._di_states),
                "DO": dict(self._do_states),
                "AI": dict(self._ai_values),
                "AO": dict(self._ao_values)
            }

    def reset_all(self):
        with self._lock:
            self._di_states.clear()
            self._do_states.clear()
            self._ai_values.clear()
            self._ao_values.clear()
            self._callbacks.clear()


_io_controller = None


def get_io_controller() -> VirtualIOController:
    global _io_controller
    if _io_controller is None:
        _io_controller = VirtualIOController()
    return _io_controller


@ToolRegistry.register
class IOControlTool(ToolBase):
    """统一IO控制工具

    集成数字输入、数字输出、触发器功能于一个工具。
    通过"控制模式"参数切换不同功能。

    功能模式:
    - 数字输入: 读取数字输入信号，支持边沿检测
    - 数字输出: 控制数字输出信号，支持电平/脉冲模式
    - 触发器: 生成触发信号，支持周期触发
    """

    tool_name = "IO控制"
    tool_category = "IO"
    tool_description = "统一IO控制工具，支持数字输入/输出和触发器功能"

    PARAM_DEFINITIONS = {
        "控制模式": ToolParameter(
            name="控制模式",
            param_type="enum",
            default="digital_input",
            description="选择IO控制模式",
            options=["digital_input", "digital_output", "trigger"],
            option_labels={
                "digital_input": "数字输入（读取信号）",
                "digital_output": "数字输出（控制信号）",
                "trigger": "触发器（生成信号）",
            },
        ),
        "通道号": ToolParameter(
            name="通道号",
            param_type="integer",
            default=1,
            description="IO通道号",
            min_value=1,
            max_value=32,
        ),
        "反转信号": ToolParameter(
            name="反转信号",
            param_type="boolean",
            default=False,
            description="是否反转信号",
        ),
        "边沿检测": ToolParameter(
            name="边沿检测",
            param_type="enum",
            default="none",
            description="边沿检测类型（数字输入模式）",
            options=["none", "rising", "falling", "both"],
            option_labels={
                "none": "无检测",
                "rising": "上升沿",
                "falling": "下降沿",
                "both": "双边沿",
            },
        ),
        "输出模式": ToolParameter(
            name="输出模式",
            param_type="enum",
            default="level",
            description="输出模式（数字输出模式）",
            options=["level", "pulse", "toggle"],
            option_labels={
                "level": "电平输出",
                "pulse": "脉冲输出",
                "toggle": "翻转输出",
            },
        ),
        "输出状态": ToolParameter(
            name="输出状态",
            param_type="boolean",
            default=True,
            description="输出状态（数字输出模式）",
        ),
        "脉冲宽度": ToolParameter(
            name="脉冲宽度",
            param_type="integer",
            default=100,
            description="脉冲宽度(ms)",
            min_value=1,
            max_value=10000,
        ),
        "触发类型": ToolParameter(
            name="触发类型",
            param_type="enum",
            default="rising",
            description="触发类型（触发器模式）",
            options=["rising", "falling", "level", "periodic"],
            option_labels={
                "rising": "上升沿触发",
                "falling": "下降沿触发",
                "level": "电平触发",
                "periodic": "周期触发",
            },
        ),
        "触发延时": ToolParameter(
            name="触发延时",
            param_type="integer",
            default=0,
            description="触发延时(ms)",
            min_value=0,
            max_value=10000,
        ),
        "周期间隔": ToolParameter(
            name="周期间隔",
            param_type="integer",
            default=1000,
            description="周期触发间隔(ms)",
            min_value=100,
            max_value=60000,
        ),
        "最大触发次数": ToolParameter(
            name="最大触发次数",
            param_type="integer",
            default=0,
            description="最大触发次数(0=无限)",
            min_value=0,
            max_value=10000,
        ),
    }

    def __init__(self, name: str = None):
        super().__init__(name)
        self._io_controller = get_io_controller()
        self._last_state = False
        self._rising_edge = False
        self._falling_edge = False
        self._trigger_count = 0
        self._last_trigger_time = 0
        self._pulse_timer = None

    def _init_params(self):
        """初始化参数"""
        self.set_param("控制模式", "digital_input")
        self.set_param("通道号", 1)
        self.set_param("反转信号", False)
        self.set_param("边沿检测", "none")
        self.set_param("输出模式", "level")
        self.set_param("输出状态", True)
        self.set_param("脉冲宽度", 100)
        self.set_param("触发类型", "rising")
        self.set_param("触发延时", 0)
        self.set_param("周期间隔", 1000)
        self.set_param("最大触发次数", 0)

    def _run_digital_input(self) -> Dict:
        """数字输入模式"""
        channel = self.get_param("通道号", 1)
        invert = self.get_param("反转信号", False)
        edge_detection = self.get_param("边沿检测", "none")

        raw_state = self._io_controller.get_di(channel)
        state = not raw_state if invert else raw_state

        if edge_detection == "rising":
            self._rising_edge = state and not self._last_state
            self._falling_edge = False
        elif edge_detection == "falling":
            self._rising_edge = False
            self._falling_edge = not state and self._last_state
        elif edge_detection == "both":
            self._rising_edge = state and not self._last_state
            self._falling_edge = not state and self._last_state
        else:
            self._rising_edge = False
            self._falling_edge = False

        self._last_state = state

        return {
            "status": True,
            "OutputState": state,
            "rising_edge": self._rising_edge,
            "falling_edge": self._falling_edge,
            "channel": channel,
            "mode": "digital_input"
        }

    def _run_digital_output(self) -> Dict:
        """数字输出模式"""
        channel = self.get_param("通道号", 1)
        output_mode = self.get_param("输出模式", "level")
        invert = self.get_param("反转信号", False)
        output_state = self.get_param("输出状态", True)
        pulse_width = self.get_param("脉冲宽度", 100)

        trigger = False
        if self.has_input("InputTrigger"):
            input_data = self.get_input("InputTrigger")
            if hasattr(input_data, 'data'):
                trigger = bool(input_data.data)
            elif isinstance(input_data, bool):
                trigger = input_data
            elif isinstance(input_data, (int, float)) and input_data != 0:
                trigger = True

        raw_state = output_state
        if output_mode == "toggle":
            if trigger:
                raw_state = not self._io_controller.get_do(channel)
        elif output_mode == "pulse":
            if trigger:
                self._output_pulse(channel, not invert if output_state else not output_state, pulse_width)
                raw_state = output_state
        else:
            raw_state = trigger if not output_state else not trigger

        state = not raw_state if invert else raw_state
        self._io_controller.set_do(channel, state)

        return {
            "status": True,
            "OutputState": state,
            "channel": channel,
            "trigger": trigger,
            "mode": "digital_output"
        }

    def _output_pulse(self, channel: int, state: bool, pulse_width: int):
        """输出脉冲"""
        self._io_controller.set_do(channel, state)

        def reset_output():
            time.sleep(pulse_width / 1000.0)
            self._io_controller.set_do(channel, not state)

        if self._pulse_timer and self._pulse_timer.is_alive():
            self._pulse_timer.cancel()
        self._pulse_timer = threading.Thread(target=reset_output, daemon=True)
        self._pulse_timer.start()

    def _run_trigger(self) -> Dict:
        """触发器模式"""
        trigger_type = self.get_param("触发类型", "rising")
        delay = self.get_param("触发延时", 0)
        periodic_interval = self.get_param("周期间隔", 1000)
        max_count = self.get_param("最大触发次数", 0)

        input_trigger = False
        if self.has_input("InputTrigger"):
            input_data = self.get_input("InputTrigger")
            if hasattr(input_data, 'data'):
                input_trigger = bool(input_data.data)
            elif isinstance(input_data, bool):
                input_trigger = input_data
            elif isinstance(input_data, (int, float)) and input_data != 0:
                input_trigger = True

        should_trigger = False
        current_time = time.time()

        if trigger_type == "rising":
            should_trigger = input_trigger and self._trigger_count == 0
        elif trigger_type == "falling":
            should_trigger = not input_trigger and self._trigger_count == 0
        elif trigger_type == "level":
            should_trigger = input_trigger
        elif trigger_type == "periodic":
            should_trigger = (current_time - self._last_trigger_time) >= (periodic_interval / 1000.0)

        if max_count > 0 and self._trigger_count >= max_count:
            should_trigger = False

        output_trigger = False
        if should_trigger:
            self._trigger_count += 1
            self._last_trigger_time = current_time
            output_trigger = True

            if delay > 0:
                time.sleep(delay / 1000.0)

        return {
            "status": True,
            "OutputTrigger": output_trigger,
            "trigger_count": self._trigger_count,
            "trigger_type": trigger_type,
            "mode": "trigger"
        }

    def _run_impl(self) -> Dict:
        """运行实现"""
        mode = self.get_param("控制模式", "digital_input")

        if mode == "digital_input":
            return self._run_digital_input()
        elif mode == "digital_output":
            return self._run_digital_output()
        elif mode == "trigger":
            return self._run_trigger()
        else:
            return {"status": False, "message": f"未知模式: {mode}"}

    def get_result(self, key: str = None):
        """获取结果数据"""
        if self._result_data is None:
            self._result_data = ResultData()
            self._result_data.tool_name = self._name
        return self._result_data

    def reset(self):
        """重置工具状态"""
        super().reset()
        self._last_state = False
        self._rising_edge = False
        self._falling_edge = False
        self._trigger_count = 0
        self._last_trigger_time = 0
        self._logger.info("IO控制工具已重置")


__all__ = [
    'IOType', 'IOState', 'VirtualIOController', 'get_io_controller',
    'IOControlTool'
]
