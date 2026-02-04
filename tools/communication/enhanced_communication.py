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
    """接收数据工具

    从外部设备接收数据。

    功能特性:
    - 支持多种通讯协议：TCP客户端/服务端、串口、WebSocket、Modbus TCP
    - 多种输出格式：String/Int/Float/Hex/JSON/Bytes
    - 动态IO类型输出
    - 超时控制
    - 连接持久化

    端口:
    - 输出端口: OutputData (接收的数据)
    """

    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "从外部设备接收数据，支持多种协议"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._comm_manager = _get_comm_manager()
        self._protocol = None
        self._device_id: Optional[int] = None
        self._received_data: Optional[Any] = None
        self._receive_count = 0

    def _init_params(self):
        """初始化参数"""
        self.set_param("连接", "__new__")
        self.set_param("协议类型", "tcp_server")
        self.set_param("监听地址", "0.0.0.0")
        self.set_param("监听端口", 8081)
        self.set_param("波特率", 9600)
        self.set_param("输出类型", "string")
        self.set_param("超时时间", 5.0)
        self.set_param("自动监听", False)
        self.set_param("最大字节数", 4096)
        self.set_param("输出键名", "received_data")
        self.set_param("Modbus地址", 0)
        self.set_param("读取数量", 1)

    def _run_impl(self):
        """执行接收逻辑"""
        auto_listen = self.get_param("自动监听", False)

        if auto_listen and not self._protocol:
            self._setup_connection()

        if self._protocol and self._protocol.is_connected():
            return self._receive_data()
        else:
            return {
                "status": False,
                "message": "未连接",
                "接收次数": self._receive_count
            }

    def _setup_connection(self) -> bool:
        """设置连接"""
        try:
            connection = self.get_param("连接", "__new__")

            if connection != "__new__":
                try:
                    device_id = int(connection)
                    self._device_id = device_id
                    self._protocol = self._comm_manager.get_connection_by_device_id(device_id)
                    if self._protocol and self._protocol.is_connected():
                        return True
                except ValueError:
                    pass

            # 创建新连接
            protocol_type = self.get_param("协议类型", "tcp_server")
            host = self.get_param("监听地址", "0.0.0.0")
            port = self.get_param("监听端口", 8081)
            baudrate = self.get_param("波特率", 9600)

            config = self._build_config(protocol_type, host, port, baudrate)
            connection_name = f"{protocol_type}_{host}_{port}"

            self._protocol = self._comm_manager.create_connection(
                connection_name, protocol_type, config
            )

            if self._protocol:
                self._device_id = self._comm_manager.get_device_id(connection_name)

            return bool(self._protocol and self._protocol.is_connected())

        except Exception:
            return False

    def _build_config(
        self, protocol_type: str, host: str, port: int, baudrate: int
    ) -> Dict:
        """构建接收配置"""
        timeout = self.get_param("超时时间", 5.0)

        if protocol_type == "tcp_server":
            return {"host": host, "port": port, "timeout": timeout}
        elif protocol_type == "tcp_client":
            return {"host": host, "port": port, "timeout": timeout}
        elif protocol_type == "serial":
            return {"port": host, "baudrate": baudrate}
        elif protocol_type == "websocket":
            return {"url": f"ws://{host}:{port}"}
        elif protocol_type == "modbus_tcp":
            return {"host": host, "port": port, "unit_id": 1, "timeout": timeout}
        else:
            return {"host": host, "port": port}

    def _receive_data(self) -> Dict:
        """接收数据"""
        try:
            output_type = self.get_param("输出类型", "string")
            timeout = self.get_param("超时时间", 5.0)
            max_bytes = self.get_param("最大字节数", 4096)

            raw_data = self._protocol.receive(timeout) if self._protocol else None

            if raw_data is None:
                return {
                    "status": False,
                    "message": "接收超时",
                    "接收次数": self._receive_count,
                    "设备ID": self._device_id
                }

            self._received_data = self._parse_data(raw_data, output_type)
            self._receive_count += 1

            result = {
                "status": True,
                "message": "接收成功",
                "接收数据": self._received_data,
                "接收次数": self._receive_count,
                "输出类型": output_type,
                "设备ID": self._device_id
            }

            # 添加动态IO输出
            result["OutputInt"] = self._get_output_int()
            result["OutputFloat"] = self._get_output_float()
            result["OutputString"] = self._get_output_string()
            result["OutputHex"] = self._get_output_hex()
            result["OutputByteArray"] = self._get_output_bytes()

            return result

        except Exception as e:
            return {
                "status": False,
                "message": f"接收失败: {str(e)}",
                "接收次数": self._receive_count
            }

    def _parse_data(self, raw_data: Any, output_type: str) -> Any:
        """解析数据"""
        if output_type == "json":
            if isinstance(raw_data, bytes):
                try:
                    return json.loads(raw_data.decode("utf-8"))
                except json.JSONDecodeError:
                    return raw_data.decode("utf-8", errors="replace")
            elif isinstance(raw_data, str):
                try:
                    return json.loads(raw_data)
                except json.JSONDecodeError:
                    return raw_data
            return raw_data
        elif output_type == "int":
            try:
                if isinstance(raw_data, bytes):
                    return int(raw_data.decode("utf-8").strip())
                return int(str(raw_data).strip())
            except (ValueError, TypeError):
                return 0
        elif output_type == "float":
            try:
                if isinstance(raw_data, bytes):
                    return float(raw_data.decode("utf-8").strip())
                return float(str(raw_data).strip())
            except (ValueError, TypeError):
                return 0.0
        elif output_type == "hex":
            if isinstance(raw_data, bytes):
                return raw_data.hex().upper()
            return str(raw_data).encode("utf-8").hex().upper()
        else:
            if isinstance(raw_data, bytes):
                return raw_data.decode("utf-8", errors="replace")
            return raw_data

    def _get_output_int(self) -> int:
        """获取整型输出"""
        try:
            if isinstance(self._received_data, (int, float)):
                return int(self._received_data)
            return int(str(self._received_data).strip())
        except (ValueError, TypeError):
            return 0

    def _get_output_float(self) -> float:
        """获取浮点型输出"""
        try:
            if isinstance(self._received_data, (int, float)):
                return float(self._received_data)
            return float(str(self._received_data).strip())
        except (ValueError, TypeError):
            return 0.0

    def _get_output_string(self) -> str:
        """获取字符串输出"""
        if isinstance(self._received_data, str):
            return self._received_data
        elif isinstance(self._received_data, bytes):
            return self._received_data.decode("utf-8", errors="replace")
        return str(self._received_data)

    def _get_output_hex(self) -> str:
        """获取HEX输出"""
        if isinstance(self._received_data, bytes):
            return self._received_data.hex().upper()
        if isinstance(self._received_data, str):
            return self._received_data.encode("utf-8").hex().upper()
        return str(self._received_data).encode("utf-8").hex().upper()

    def _get_output_bytes(self) -> bytes:
        """获取二进制输出"""
        if isinstance(self._received_data, bytes):
            return self._received_data
        if isinstance(self._received_data, str):
            return self._received_data.encode("utf-8")
        return str(self._received_data).encode("utf-8")

    def reset(self):
        """重置"""
        self._received_data = None
        self._receive_count = 0
        self._device_id = None
        self._protocol = None
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
