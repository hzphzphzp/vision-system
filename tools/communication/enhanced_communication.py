#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的通讯工具模块

提供完整的数据发送和接收功能，支持多种通讯协议：
- SendDataTool: 发送数据到外部设备
- ReceiveDataTool: 接收外部设备数据

功能特性:
- 多种协议支持：TCP客户端/服务端、串口、WebSocket、Modbus TCP
- 多种数据格式：JSON、ASCII、HEX、二进制
- 动态IO类型：支持Int/Float/String/Point/Circle/Rect/Posture等
- 连接管理：持久化连接、连接复用、设备ID管理

Author: Vision System Team
Date: 2026-02-03
"""

import json
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication import ConnectionState, ProtocolManager, ProtocolType
from core.communication.dynamic_io import (
    IoType, IoDataFactory, DynamicOutputParser,
    PointF, Circle, RectBox, Posture, Fixture
)
from core.tool_base import ToolBase, ToolParameter, ToolRegistry


def _get_comm_manager():
    """获取通讯管理器"""
    from tools.communication.communication import get_communication_manager
    return get_communication_manager()


@ToolRegistry.register
class SendDataTool(ToolBase):
    """发送数据工具（重构版）

    将数据发送到外部设备。通过连接ID使用已有的通讯连接，
    专注于数据处理和路由，不负责连接管理。

    功能特性:
    - 使用已有连接：通过连接ID引用ConnectionManager中的连接
    - 数据映射：支持将上游工具输出映射为发送格式
    - 发送条件控制：总是/成功时/失败时
    - 仅发送变化的数据：避免重复发送相同数据
    - 多种数据格式：JSON、ASCII、HEX、二进制

    端口:
    - 输入端口: InputTrigger (触发信号，可选)
    """

    tool_name = "发送数据"
    tool_category = "Communication"
    tool_description = "发送数据到外部设备，通过连接ID使用已有连接"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._data_mapper = None  # 数据映射器实例
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0
        self._last_sent_data = None  # 上次发送的数据，用于变化检测

    def _init_params(self):
        """初始化参数"""
        # 连接选择
        self.set_param("连接ID", "")  # 连接标识符
        
        # 数据配置
        self.set_param("数据格式", "json")  # json/ascii/hex/binary
        self.set_param("数据映射", "")  # JSON字符串，定义数据映射规则
        
        # 发送控制
        self.set_param("发送条件", "总是")  # 总是/成功时/失败时
        self.set_param("仅发送变化的数据", False)  # 是否只发送变化的数据

    def _run_impl(self):
        """执行发送逻辑"""
        try:
            # 1. 检查连接ID
            connection_id = self.get_param("连接ID", "")
            if not connection_id:
                return {
                    "status": False,
                    "message": "未选择连接",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 2. 获取连接
            conn_manager = _get_comm_manager()
            connection = conn_manager.get_connection(connection_id)
            
            if not connection:
                return {
                    "status": False,
                    "message": f"未找到连接: {connection_id}",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }
            
            # 3. 检查连接状态
            protocol_instance = connection.protocol_instance
            if not protocol_instance or not protocol_instance.is_connected():
                return {
                    "status": False,
                    "message": "连接未建立",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 4. 收集上游输入数据
            input_data = self._collect_input_data()
            if not input_data:
                input_data = {}

            # 5. 检查发送条件
            send_condition = self.get_param("发送条件", "总是")
            if not self._should_send(send_condition, input_data):
                return {
                    "status": True,
                    "message": "不满足发送条件",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 6. 应用数据映射
            data_to_send = self._apply_data_mapping(input_data)

            # 7. 检查数据变化
            only_on_change = self.get_param("仅发送变化的数据", False)
            if only_on_change and self._is_data_unchanged(data_to_send):
                return {
                    "status": True,
                    "message": "数据未变化，跳过发送",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 8. 格式化数据
            format_type = self.get_param("数据格式", "json")
            formatted_data = self._format_data(data_to_send, format_type)

            # 9. 发送数据
            success = protocol_instance.send(formatted_data)

            if success:
                self._send_count += 1
                self._last_sent_data = data_to_send.copy() if isinstance(data_to_send, dict) else data_to_send
                message = "发送成功"
            else:
                self._fail_count += 1
                message = "发送失败"

            return {
                "status": success,
                "message": message,
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count,
                "连接ID": connection_id,
                "OutputData": data_to_send
            }

        except Exception as e:
            self._fail_count += 1
            return {
                "status": False,
                "message": f"发送异常: {str(e)}",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }

    def _collect_input_data(self) -> Dict[str, Any]:
        """收集上游工具的输入数据"""
        input_data = {}
        
        # 从_result_data获取数据（上游工具的输出）
        if self._result_data:
            try:
                all_values = self._result_data.get_all_values()
                if all_values:
                    input_data.update(all_values)
            except Exception:
                pass
        
        return input_data

    def _should_send(self, condition: str, input_data: Dict[str, Any]) -> bool:
        """检查是否应该发送数据"""
        if condition == "总是":
            return True
        elif condition == "成功时":
            # 检查是否有result字段且为True
            result = input_data.get("result", input_data.get("status", False))
            return bool(result)
        elif condition == "失败时":
            # 检查是否有result字段且为False
            result = input_data.get("result", input_data.get("status", True))
            return not bool(result)
        return True

    def _apply_data_mapping(self, input_data: Dict[str, Any]) -> Any:
        """应用数据映射"""
        mapping_json = self.get_param("数据映射", "")
        
        if not mapping_json:
            # 没有映射规则，直接返回原始数据
            return input_data
        
        try:
            # 解析映射规则
            mapping_rules = json.loads(mapping_json)
            
            # 如果有映射规则，应用映射
            if isinstance(mapping_rules, dict):
                from core.data_mapping import DataMapper, DataMappingRule
                
                mapper = DataMapper()
                for source_field, target_field in mapping_rules.items():
                    rule = DataMappingRule(
                        source_field=source_field,
                        target_field=target_field
                    )
                    mapper.add_rule(rule)
                
                return mapper.map(input_data)
            
            return input_data
        except (json.JSONDecodeError, Exception):
            # 解析失败，返回原始数据
            return input_data

    def _is_data_unchanged(self, data: Any) -> bool:
        """检查数据是否未变化"""
        if self._last_sent_data is None:
            return False
        
        # 简单比较，对于字典使用字符串化比较
        if isinstance(data, dict) and isinstance(self._last_sent_data, dict):
            return json.dumps(data, sort_keys=True) == json.dumps(self._last_sent_data, sort_keys=True)
        
        return data == self._last_sent_data

    def _format_data(self, data: Any, format_type: str) -> Any:
        """格式化数据"""
        if format_type == "json":
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)
            return json.dumps({"data": data}, ensure_ascii=False)
        elif format_type == "ascii":
            if isinstance(data, str):
                return data.encode("ascii")
            return str(data).encode("ascii")
        elif format_type == "hex":
            if isinstance(data, str):
                return data.encode("utf-8").hex().upper()
            elif isinstance(data, bytes):
                return data.hex().upper()
            return str(data).encode("utf-8").hex().upper()
        elif format_type == "binary":
            if isinstance(data, str):
                return data.encode("utf-8")
            elif isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False).encode("utf-8")
            return str(data).encode("utf-8")
        else:
            return str(data)

    def reset(self):
        """重置"""
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0.0
        self._last_sent_data = None
        self._data_mapper = None
        super().reset()


@ToolRegistry.register
class ReceiveDataTool(ToolBase):
    """接收数据工具（重构版）

    从外部设备接收数据。通过连接ID使用已有的通讯连接，
    专注于数据接收和解析，不负责连接管理。

    功能特性:
    - 使用已有连接：通过连接ID引用ConnectionManager中的连接
    - 多种数据格式解析：JSON、String、Int、Float、Hex、Bytes
    - 数据提取规则：支持从复杂数据中提取特定字段
    - 超时控制：可配置的接收超时时间

    端口:
    - 输出端口: OutputData (接收的数据)
    """

    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "从外部设备接收数据，通过连接ID使用已有连接"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._receive_count = 0
        self._fail_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0

    def _init_params(self):
        """初始化参数"""
        # 连接选择（关键变更：只选择已有连接，不创建新连接）
        self.set_param("连接ID", "", description="选择已有的通讯连接ID")

        # 接收配置
        self.set_param("输出格式", "json",
                      options=["json", "string", "int", "float", "hex", "bytes"],
                      description="接收数据的解析格式")
        self.set_param("超时时间", 5.0,
                      description="接收超时时间（秒）")
        self.set_param("缓冲区大小", 4096,
                      description="接收缓冲区大小（字节）")

        # 数据提取
        self.set_param("数据提取规则", "",
                      description='从接收数据中提取字段，如{"status": "result.status"}')

    def _run_impl(self):
        """执行接收逻辑（重构版）"""
        # 1. 检查连接ID
        connection_id = self.get_param("连接ID", "")
        if not connection_id:
            return {
                "status": False,
                "message": "未选择通讯连接，请在参数中选择已建立的连接",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

        # 2. 获取已有连接
        conn_manager = _get_comm_manager()
        connection = conn_manager.get_connection(connection_id)

        if not connection:
            return {
                "status": False,
                "message": f"未找到连接 {connection_id}，请先在通讯配置中建立连接",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

        # 3. 检查连接状态
        protocol_instance = connection.protocol_instance
        if not protocol_instance or not protocol_instance.is_connected():
            return {
                "status": False,
                "message": f"连接 {connection.name} 未建立，请先连接",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

        # 4. 检查接收接口
        if not hasattr(protocol_instance, 'receive'):
            return {
                "status": False,
                "message": f"连接 {connection.name} 无接收接口",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

        # 5. 从已有连接接收数据
        try:
            timeout = self.get_param("超时时间", 5.0)
            raw_data = protocol_instance.receive(timeout)

            if raw_data is None:
                self._fail_count += 1
                return {
                    "status": False,
                    "message": "接收超时，未收到数据",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 6. 解析数据
            format_type = self.get_param("输出格式", "json")
            parsed_data = self._parse_data(raw_data, format_type)

            # 7. 应用数据提取规则
            extracted_data = self._extract_data(parsed_data)

            # 8. 更新统计
            self._receive_count += 1
            self._last_received_data = extracted_data
            self._last_receive_time = time.time()

            # 9. 构建输出
            result = {
                "status": True,
                "message": f"从 {connection.name} 接收到数据",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count,
                "接收数据": extracted_data,
                "OutputStatus": True,
                "OutputData": extracted_data
            }

            return result

        except Exception as e:
            self._fail_count += 1
            return {
                "status": False,
                "message": f"接收异常：{str(e)}",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

    def _parse_data(self, raw_data: Any, format_type: str) -> Any:
        """解析接收到的数据"""
        try:
            if format_type == "json":
                if isinstance(raw_data, bytes):
                    return json.loads(raw_data.decode('utf-8'))
                elif isinstance(raw_data, str):
                    return json.loads(raw_data)
                return raw_data

            elif format_type == "string":
                if isinstance(raw_data, bytes):
                    return raw_data.decode('utf-8', errors='replace')
                return str(raw_data)

            elif format_type == "int":
                if isinstance(raw_data, bytes):
                    return int(raw_data.decode('utf-8').strip())
                return int(str(raw_data).strip())

            elif format_type == "float":
                if isinstance(raw_data, bytes):
                    return float(raw_data.decode('utf-8').strip())
                return float(str(raw_data).strip())

            elif format_type == "hex":
                if isinstance(raw_data, bytes):
                    return raw_data.hex().upper()
                return str(raw_data).encode('utf-8').hex().upper()

            elif format_type == "bytes":
                if isinstance(raw_data, str):
                    return raw_data.encode('utf-8')
                return raw_data

            else:
                return raw_data

        except Exception as e:
            return raw_data

    def _extract_data(self, data: Any) -> Any:
        """根据规则提取数据"""
        extract_rules = self.get_param("数据提取规则", "")

        if not extract_rules:
            return data

        try:
            import json
            rules = json.loads(extract_rules)

            if not isinstance(data, dict):
                return data

            result = {}
            for target_field, source_path in rules.items():
                value = self._get_nested_value(data, source_path)
                if value is not None:
                    result[target_field] = value

            return result if result else data

        except Exception:
            return data

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """获取嵌套字段值"""
        if not isinstance(data, dict):
            return None

        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def reset(self):
        """重置"""
        self._receive_count = 0
        self._fail_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0
        self._received_data = None
        super().reset()


# 兼容性别名
EnhancedSendData = SendDataTool
EnhancedReceiveData = ReceiveDataTool


# 导出
__all__ = [
    'SendDataTool',
    'ReceiveDataTool',
    'EnhancedSendData',
    'EnhancedReceiveData'
]
