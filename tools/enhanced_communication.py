#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的通讯工具模块 - 最简化版本

Author: Vision System Team
Date: 2026-01-22
"""

import sys
import os
import json
import time
import threading
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ToolBase, ToolRegistry, ToolParameter

@ToolRegistry.register
class EnhancedSendData(ToolBase):
    """发送数据工具"""
    tool_name = "发送数据"
    tool_category = "Communication"
    tool_description = "发送数据到指定连接"
    
    PARAM_DEFINITIONS = [
        ToolParameter("连接", "enum", "",
                     description="选择已配置的通讯连接"),
        ToolParameter("数据来源", "enum", "custom",
                     options=["custom", "result", "formula"],
                     option_labels={"custom": "自定义内容", "result": "从结果获取", "formula": "公式计算"}),
        ToolParameter("数据格式", "enum", "json",
                     options=["json", "text", "hex", "xml"])
    ]
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._is_auto_sending = False
        self._send_count = 0
        self._fail_count = 0
    
    def _init_params(self):
        self.set_param("发送内容", '{"status": "ok"}')
        self.set_param("自动发送", False)
        self.set_param("发送间隔", 1.0)
    
    def _run_impl(self):
        content = self.get_param("发送内容", "")
        print(f"发送数据: {content}")
        return {"status": "sent", "content": content}
    
    def _start_auto_send(self):
        """启动自动发送"""
        if self._is_auto_sending:
            return
        self._is_auto_sending = True
    
    def _stop_auto_send(self):
        """停止自动发送"""
        self._is_auto_sending = False

@ToolRegistry.register
class EnhancedReceiveData(ToolBase):
    """接收数据工具"""
    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "从指定连接接收数据"
    
    PARAM_DEFINITIONS = [
        ToolParameter("连接", "enum", ""),
        ToolParameter("数据格式", "enum", "json",
                     options=["json", "text", "binary"])
    ]
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._is_receiving = False
    
    def _init_params(self):
        self.set_param("超时时间", 1.0)
        self.set_param("自动接收", False)
    
    def _run_impl(self):
        print("接收数据...")
        return {"status": "receiving"}
