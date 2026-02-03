#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IO控制工具模块

参考海康VisionMaster SDK设计，完全自主实现：
- 数字IO输入输出控制
- 触发信号生成
- 信号同步
- IO状态监控

Author: Vision System Team
Date: 2026-02-03
"""

import os
import sys
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.tool_base import ToolBase, ToolParameter, ToolRegistry


class IOType(Enum):
    """IO类型"""
    DI = "DI"   # 数字输入
    DO = "DO"   # 数字输出
    AI = "AI"   # 模拟输入
    AO = "AO"   # 模拟输出


class IOState(Enum):
    """IO状态"""
    OFF = 0
    ON = 1
    UNKNOWN = -1


class VirtualIOController:
    """虚拟IO控制器

    模拟真实的IO控制器，用于测试和开发。
    在实际部署时，可以替换为真实的硬件IO控制。
    """

    def __init__(self):
        self._di_states: Dict[int, bool] = {}  # 数字输入状态
        self._do_states: Dict[int, bool] = {}   # 数字输出状态
        self._ai_values: Dict[int, float] = {}  # 模拟输入值
        self._ao_values: Dict[int, float] = {}  # 模拟输出值
        self._lock = threading.Lock()
        self._callbacks: Dict[int, List[Callable]] = {}  # 状态变化回调

    def set_di(self, channel: int, state: bool):
        """设置数字输入"""
        with self._lock:
            old_state = self._di_states.get(channel, False)
            self._di_states[channel] = state
            if old_state != state and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, state, IOType.DI)
                    except:
                        pass

    def get_di(self, channel: int) -> bool:
        """获取数字输入"""
        return self._di_states.get(channel, False)

    def set_do(self, channel: int, state: bool):
        """设置数字输出"""
        with self._lock:
            old_state = self._do_states.get(channel, False)
            self._do_states[channel] = state
            if old_state != state and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, state, IOType.DO)
                    except:
                        pass

    def get_do(self, channel: int) -> bool:
        """获取数字输出"""
        return self._do_states.get(channel, False)

    def set_ai(self, channel: int, value: float):
        """设置模拟输入"""
        with self._lock:
            old_value = self._ai_values.get(channel, 0.0)
            self._ai_values[channel] = value
            if abs(old_value - value) > 0.001 and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, value, IOType.AI)
                    except:
                        pass

    def get_ai(self, channel: int) -> float:
        """获取模拟输入"""
        return self._ai_values.get(channel, 0.0)

    def set_ao(self, channel: int, value: float):
        """设置模拟输出"""
        with self._lock:
            old_value = self._ao_values.get(channel, 0.0)
            self._ao_values[channel] = value
            if abs(old_value - value) > 0.001 and channel in self._callbacks:
                for cb in self._callbacks[channel]:
                    try:
                        cb(channel, value, IOType.AO)
                    except:
                        pass

    def get_ao(self, channel: int) -> float:
        """获取模拟输出"""
        return self._ao_values.get(channel, 0.0)

    def register_callback(self, channel: int, callback: Callable):
        """注册状态变化回调"""
        if channel not in self._callbacks:
            self._callbacks[channel] = []
        self._callbacks[channel].append(callback)

    def get_all_states(self) -> Dict:
        """获取所有IO状态"""
        with self._lock:
            return {
                "DI": dict(self._di_states),
                "DO": dict(self._do_states),
                "AI": dict(self._ai_values),
                "AO": dict(self._ao_values)
            }

    def reset_all(self):
        """重置所有IO"""
        with self._lock:
            self._di_states.clear()
            self._do_states.clear()
            self._ai_values.clear()
            self._ao_values.clear()
            self._callbacks.clear()


# 全局虚拟IO控制器
_io_controller = None


def get_io_controller() -> VirtualIOController:
    """获取IO控制器单例"""
    global _io_controller
    if _io_controller is None:
        _io_controller = VirtualIOController()
    return _io_controller


@ToolRegistry.register
class DigitalInputTool(ToolBase):
    """数字输入工具

    读取数字输入信号。

    功能特性:
    - 多通道支持
    - 状态滤波
    - 边沿检测
    - 回调触发

    端口:
    - 输出端口: OutputState (布尔值)
    """

    tool_name = "数字输入"
    tool_category = "IO"
    tool_description = "读取数字输入信号，支持多通道和边沿检测"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._io_controller = get_io_controller()
        self._last_state = False
        self._rising_edge = False
        self._falling_edge = False
        self._init_parameters()

    def _init_parameters(self):
        """初始化参数"""
        self.set_param("channel", 1, description="通道号", min_value=1, max_value=32)
        self.set_param("invert", False, description="反转信号")
        self.set_param("filter_enable", True, description="启用滤波")
        self.set_param("filter_time", 10, description="滤波时间(ms)", min_value=0, max_value=1000)
        self.set_param("edge_detection", "none", description="边沿检测",
                      options=["none", "rising", "falling", "both"])

    def _run_impl(self) -> Dict:
        """运行实现"""
        channel = self.get_param("channel")
        invert = self.get_param("invert")
        edge_detection = self.get_param("edge_detection")
        
        # 获取IO状态
        raw_state = self._io_controller.get_di(channel)
        state = not raw_state if invert else raw_state
        
        # 边沿检测
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
            "channel": channel
        }


@ToolRegistry.register
class DigitalOutputTool(ToolBase):
    """数字输出工具

    控制数字输出信号。

    功能特性:
    - 多通道支持
    - 输出模式：电平/脉冲
    - 脉冲宽度控制
    - 输出使能

    端口:
    - 输入端口: InputTrigger (触发信号，可选)
    """

    tool_name = "数字输出"
    tool_category = "IO"
    tool_description = "控制数字输出信号，支持电平和脉冲模式"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._io_controller = get_io_controller()
        self._pulse_timer = None
        self._init_parameters()

    def _init_parameters(self):
        """初始化参数"""
        self.set_param("channel", 1, description="通道号", min_value=1, max_value=32)
        self.set_param("output_mode", "level", description="输出模式",
                      options=["level", "pulse", "toggle"])
        self.set_param("pulse_width", 100, description="脉冲宽度(ms)", min_value=1, max_value=10000)
        self.set_param("invert", False, description="反转信号")
        self.set_param("initial_state", False, description="初始状态")

    def _output_pulse(self, channel: int, state: bool, pulse_width: int):
        """输出脉冲"""
        self._io_controller.set_do(channel, state)
        
        # 延迟复位
        def reset_output():
            time.sleep(pulse_width / 1000.0)
            self._io_controller.set_do(channel, not state)
        
        if self._pulse_timer and self._pulse_timer.is_alive():
            self._pulse_timer.cancel()
        self._pulse_timer = threading.Thread(target=reset_output, daemon=True)
        self._pulse_timer.start()

    def _run_impl(self) -> Dict:
        """运行实现"""
        channel = self.get_param("channel")
        output_mode = self.get_param("output_mode")
        invert = self.get_param("invert")
        initial_state = self.get_param("initial_state")
        
        # 获取触发信号
        trigger = False
        if self.has_input("InputTrigger"):
            input_data = self.get_input("InputTrigger")
            if hasattr(input_data, 'data'):
                trigger = bool(input_data.data)
            elif isinstance(input_data, bool):
                trigger = input_data
            elif isinstance(input_data, (int, float)) and input_data != 0:
                trigger = True
        
        # 计算输出状态
        raw_state = initial_state
        if output_mode == "toggle":
            # 触发时翻转状态
            if trigger:
                raw_state = not self._io_controller.get_do(channel)
        elif output_mode == "pulse":
            # 触发时输出脉冲
            if trigger:
                pulse_width = self.get_param("pulse_width")
                self._output_pulse(channel, not invert if initial_state else not initial_state, pulse_width)
                raw_state = initial_state  # 脉冲模式下返回初始状态
        else:
            # 电平模式：触发信号控制输出
            raw_state = trigger if not initial_state else not trigger
        
        # 应用反转
        state = not raw_state if invert else raw_state
        
        # 输出到IO控制器
        self._io_controller.set_do(channel, state)
        
        return {
            "status": True,
            "OutputState": state,
            "channel": channel,
            "trigger": trigger
        }


@ToolRegistry.register
class TriggerTool(ToolBase):
    """触发器工具

    生成触发信号，用于同步多个工具。

    功能特性:
    - 触发类型：边沿/电平
    - 触发延时
    - 触发次数控制
    - 周期触发

    端口:
    - 输入端口: InputTrigger (触发输入，可选)
    - 输出端口: OutputTrigger (触发输出)
    """

    tool_name = "触发器"
    tool_category = "IO"
    tool_description = "生成触发信号，支持边沿、电平和周期触发"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._trigger_count = 0
        self._last_trigger_time = 0
        self._init_parameters()

    def _init_parameters(self):
        """初始化参数"""
        self.set_param("trigger_type", "rising", description="触发类型",
                      options=["rising", "falling", "level", "periodic"])
        self.set_param("delay", 0, description="触发延时(ms)", min_value=0, max_value=10000)
        self.set_param("pulse_width", 10, description="脉冲宽度(ms)", min_value=1, max_value=1000)
        self.set_param("periodic_interval", 1000, description="周期间隔(ms)", min_value=100, max_value=60000)
        self.set_param("max_count", 0, description="最大触发次数(0=无限)", min_value=0, max_value=10000)
        self.set_param("retriggerable", True, description="可重触发")

    def _run_impl(self) -> Dict:
        """运行实现"""
        trigger_type = self.get_param("trigger_type")
        delay = self.get_param("delay")
        pulse_width = self.get_param("pulse_width")
        periodic_interval = self.get_param("periodic_interval")
        max_count = self.get_param("max_count")
        retriggerable = self.get_param("retriggerable")
        
        # 获取输入触发
        input_trigger = False
        if self.has_input("InputTrigger"):
            input_data = self.get_input("InputTrigger")
            if hasattr(input_data, 'data'):
                input_trigger = bool(input_data.data)
            elif isinstance(input_data, bool):
                input_trigger = input_data
            elif isinstance(input_data, (int, float)) and input_data != 0:
                input_trigger = True
        
        # 检查触发条件
        should_trigger = False
        current_time = time.time()
        
        if trigger_type == "rising":
            should_trigger = input_trigger and (retriggerable or self._trigger_count == 0)
        elif trigger_type == "falling":
            should_trigger = not input_trigger and (retriggerable or self._trigger_count == 0)
        elif trigger_type == "level":
            should_trigger = input_trigger
        elif trigger_type == "periodic":
            should_trigger = (current_time - self._last_trigger_time) >= (periodic_interval / 1000.0)
        
        # 检查最大次数
        if max_count > 0 and self._trigger_count >= max_count:
            should_trigger = False
        
        # 触发输出
        output_trigger = False
        if should_trigger:
            self._trigger_count += 1
            self._last_trigger_time = current_time
            output_trigger = True
            
            # 延时处理
            if delay > 0:
                time.sleep(delay / 1000.0)
        
        return {
            "status": True,
            "OutputTrigger": output_trigger,
            "trigger_count": self._trigger_count,
            "trigger_type": trigger_type
        }


@ToolRegistry.register
class IOSynchronizationTool(ToolBase):
    """IO同步工具

    同步多个IO操作，确保时序正确。

    功能特性:
    - 同步组管理
    - 同步延迟控制
    - 同步触发

    端口:
    - 输入端口: SyncTrigger (同步触发)
    """

    tool_name = "IO同步"
    tool_category = "IO"
    tool_description = "同步多个IO操作，确保时序正确"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._io_controller = get_io_controller()
        self._sync_groups: Dict[str, Dict] = {}
        self._init_parameters()

    def _init_parameters(self):
        """初始化参数"""
        self.set_param("sync_mode", "simultaneous", description="同步模式",
                      options=["simultaneous", "sequential", "custom"])
        self.set_param("channel_1", 1, description="通道1", min_value=1, max_value=32)
        self.set_param("channel_2", 2, description="通道2", min_value=1, max_value=32)
        self.set_param("channel_3", 0, description="通道3(0=禁用)", min_value=0, max_value=32)
        self.set_param("channel_4", 0, description="通道4(0=禁用)", min_value=0, max_value=32)
        self.set_param("delay_1", 0, description="通道1延迟(ms)", min_value=0, max_value=1000)
        self.set_param("delay_2", 0, description="通道2延迟(ms)", min_value=0, max_value=1000)
        self.set_param("delay_3", 0, description="通道3延迟(ms)", min_value=0, max_value=1000)
        self.set_param("delay_4", 0, description="通道4延迟(ms)", min_value=0, max_value=1000)
        self.set_param("output_state", True, description="输出状态")

    def _run_impl(self) -> Dict:
        """运行实现"""
        channels = [
            (self.get_param("channel_1"), self.get_param("delay_1")),
            (self.get_param("channel_2"), self.get_param("delay_2")),
            (self.get_param("channel_3"), self.get_param("delay_3")),
            (self.get_param("channel_4"), self.get_param("delay_4")),
        ]
        output_state = self.get_param("output_state")
        sync_mode = self.get_param("sync_mode")
        
        # 同步输出
        results = []
        for channel, delay in channels:
            if channel > 0:
                if delay > 0:
                    time.sleep(delay / 1000.0)
                self._io_controller.set_do(channel, output_state)
                results.append({"channel": channel, "delay": delay, "state": output_state})
        
        return {
            "status": True,
            "sync_results": results,
            "sync_mode": sync_mode,
            "channels_activated": len(results)
        }


# 导出
__all__ = [
    'IOType', 'IOState', 'VirtualIOController', 'get_io_controller',
    'DigitalInputTool', 'DigitalOutputTool', 'TriggerTool', 'IOSynchronizationTool'
]
