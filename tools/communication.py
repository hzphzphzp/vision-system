#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯工具模块（VisionMaster风格优化版）

提供数据发送和接收功能，支持多种通讯协议：
- CommunicationManager: 通讯连接管理器（复用 ProtocolManager）
- SendData: 发送数据到外部设备
- ReceiveData: 接收外部设备数据

功能特性:
- 连接持久化：关闭界面后保持连接
- 连接复用：多个工具可共享同一连接
- 连接选择：可选择已配置的通讯连接
- 动态IO：支持多种数据类型输出
- 设备ID管理：支持PLC和Modbus

Author: Vision System Team
Date: 2026-01-15
"""

import sys
import os
import json
import time
import threading
from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ToolBase, ToolRegistry, ToolParameter
from core.communication import ProtocolManager, ProtocolType, ConnectionState


IO_TYPE = {
    "INT": 1,
    "FLOAT": 2,
    "STRING": 3,
    "IMAGE": 4,
    "BYTE": 6,
    "POINT_F": 7,
    "LINE": 9,
    "CIRCLE": 10,
    "RECT_F": 11,
    "ROIBOX": 13,
    "ANNULUS": 16,
    "CLASSINFO": 18,
    "POSTURE": 20,
    "POLYGON": 21,
    "ELLIPSE": 22,
}


class CommunicationManager:
    """通讯连接管理器（复用 ProtocolManager 版本）
    
    管理所有通讯连接，支持：
    - 创建和保存通讯连接（复用 ProtocolManager）
    - 连接持久化（不自动断开）
    - 多工具共享连接
    - 设备ID管理
    - 动态IO数据收发
    """
    
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
        self._protocol_manager = ProtocolManager()
        self._connections: Dict[str, Any] = {}
        self._connection_configs: Dict[str, Dict] = {}
        self._device_counter = 1000
        self._device_map: Dict[str, int] = {}
    
    def _get_protocol_type_enum(self, protocol_type: str) -> ProtocolType:
        """将字符串协议类型转换为枚举"""
        type_map = {
            "tcp_client": ProtocolType.TCP_CLIENT,
            "tcp_server": ProtocolType.TCP_SERVER,
            "serial": ProtocolType.SERIAL,
            "websocket": ProtocolType.WEBSOCKET,
            "http": ProtocolType.HTTP,
            "modbus_tcp": ProtocolType.MODBUS_TCP
        }
        return type_map.get(protocol_type, ProtocolType.TCP_CLIENT)
    
    def create_connection(self, name: str, protocol_type: str, config: Dict) -> Optional[Any]:
        """创建并保存通讯连接（复用 ProtocolManager）"""
        if name in self._connections:
            existing = self._connections[name]
            if existing and existing.is_connected():
                return existing
        
        protocol_type_enum = self._get_protocol_type_enum(protocol_type)
        protocol = self._protocol_manager.create_protocol(protocol_type_enum, name)
        
        success = protocol.connect(config)
        
        if success:
            self._connections[name] = protocol
            self._connection_configs[name] = {
                "protocol_type": protocol_type,
                "config": config.copy()
            }
            self._device_map[name] = self._device_counter
            self._device_counter += 1
            return protocol
        else:
            return None
    
    def get_connection(self, name: str) -> Optional[Any]:
        """获取已保存的连接"""
        return self._connections.get(name)
    
    def get_connection_by_device_id(self, device_id: int) -> Optional[Any]:
        """根据设备ID获取连接（VisionMaster风格）"""
        for name, dev_id in self._device_map.items():
            if dev_id == device_id:
                return self._connections.get(name)
        return None
    
    def get_device_id(self, name: str) -> Optional[int]:
        """获取设备的设备ID"""
        return self._device_map.get(name)
    
    def get_available_connections(self) -> List[Dict[str, Any]]:
        """获取所有可用的连接列表"""
        result = []
        for name, protocol in self._connections.items():
            if protocol and protocol.is_connected():
                config = self._connection_configs.get(name, {})
                protocol_type = config.get("protocol_type", "unknown")
                device_id = self._device_map.get(name, 0)
                host = config.get("config", {}).get("host", config.get("url", ""))
                port = config.get("config", {}).get("port", "")
                result.append({
                    "name": name,
                    "device_id": device_id,
                    "protocol_type": protocol_type,
                    "display_name": f"[{device_id}] {protocol_type.upper()} - {name} ({host}:{port})",
                    "connected": True
                })
        return result
    
    def set_string(self, device_id: int, value: str, address_id: int = -1) -> bool:
        """设置字符串型数据（VisionMaster风格）"""
        return self._set_data(device_id, "string", value, address_id)
    
    def set_int(self, device_id: int, value: Union[int, List[int]], address_id: int = -1) -> bool:
        """设置整型数据（仅支持PLC和Modbus）"""
        values = [value] if isinstance(value, int) else value
        return self._set_data(device_id, "int", values, address_id)
    
    def set_float(self, device_id: int, value: Union[float, List[float]], address_id: int = -1) -> bool:
        """设置浮点型数据（仅支持PLC和Modbus）"""
        values = [value] if isinstance(value, (int, float)) else value
        return self._set_data(device_id, "float", values, address_id)
    
    def set_bytes(self, device_id: int, value: bytes, address_id: int = -1) -> bool:
        """设置二进制数据（不支持PLC）"""
        return self._set_data(device_id, "bytes", value, address_id)
    
    def _set_data(self, device_id: int, data_type: str, value: Any, address_id: int) -> bool:
        """内部数据设置方法"""
        for name, dev_id in self._device_map.items():
            if dev_id == device_id:
                protocol = self._connections.get(name)
                if protocol and protocol.is_connected():
                    if data_type == "string":
                        return protocol.send(str(value))
                    elif data_type in ("int", "float"):
                        formatted = ", ".join(map(str, value))
                        return protocol.send(formatted)
                    elif data_type == "bytes":
                        return protocol.send(value)
                break
        return False
    
    def get_read_data(self, device_id: int, max_len: int = 4096, address_id: int = -1) -> Optional[bytes]:
        """获取读取数据（VisionMaster风格）"""
        for name, dev_id in self._device_map.items():
            if dev_id == device_id:
                protocol = self._connections.get(name)
                if protocol and protocol.is_connected():
                    return protocol.receive(timeout=5.0)
                break
        return None
    
    def is_device_connect(self, device_id: int) -> bool:
        """检查设备是否处于连接状态"""
        for name, dev_id in self._device_map.items():
            if dev_id == device_id:
                protocol = self._connections.get(name)
                return protocol.is_connected() if protocol else False
        return False
    
    def disconnect(self, name: str):
        """断开指定连接"""
        if name in self._connections:
            protocol = self._connections[name]
            if protocol:
                protocol.disconnect()
            del self._connections[name]
            if name in self._device_map:
                del self._device_map[name]
    
    def disconnect_all(self):
        """断开所有连接"""
        for name, protocol in self._connections.items():
            if protocol:
                protocol.disconnect()
        self._connections.clear()
        self._device_map.clear()
    
    def get_connection_names(self) -> List[str]:
        """获取所有连接名称"""
        return list(self._connections.keys())


_comm_manager = None

def get_communication_manager() -> CommunicationManager:
    """获取通讯连接管理器单例"""
    global _comm_manager
    if _comm_manager is None:
        _comm_manager = CommunicationManager()
    return _comm_manager


# 注释掉原版本，使用增强版本
# @ToolRegistry.register
# class SendData(ToolBase):
    """发送数据工具（VisionMaster风格优化版）
    
    将工具结果数据或自定义内容发送到外部设备。
    
    功能特性:
    - 支持多种通讯协议：TCP客户端/服务端、串口、WebSocket、HTTP、Modbus TCP
    - 灵活的数据来源：可选择从结果数据获取或使用自定义内容
    - 多种数据格式：JSON、ASCII、HEX、二进制
    - 设备ID选择：可选择已创建的通讯连接
    - 连接持久化：关闭界面后保持连接
    - Modbus支持：支持寄存器地址和批量写入
    - 数据格式化：支持变量替换和格式化字符串
    """
    
    tool_name = "发送数据"
    tool_category = "Communication"
    tool_description = "将检测结果或自定义数据发送到外部设备，支持TCP/串口/WebSocket等多种协议"
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._comm_manager = get_communication_manager()
        self._protocol = None
        self._last_send_time = 0
        self._send_count = 0
        self._fail_count = 0
        self._use_existing_connection = False
        self._device_id = None
        self._modbus_client = None
        self._update_connection_options()
    
    def _update_connection_options(self):
        """更新连接选项"""
        available_connections = self._comm_manager.get_available_connections()
        connection_options = ["__new__"]
        connection_labels = {"__new__": "+ 新建连接"}
        
        for conn in available_connections:
            device_id = conn.get("device_id", 0)
            display_name = conn.get("display_name", f"设备{device_id}")
            connection_options.append(str(device_id))
            connection_labels[str(device_id)] = display_name
        
        # 更新参数定义
        self.PARAM_DEFINITIONS = [
            ToolParameter("连接", "enum", "__new__",
                         description="选择通讯连接",
                         options=connection_options,
                         option_labels=connection_labels),
        ToolParameter("地址", "string", "127.0.0.1", description="目标地址（IP或串口）"),
        ToolParameter("端口", "integer", 8080, description="端口号", min_value=1, max_value=65535),
        ToolParameter("波特率", "integer", 9600, description="串口波特率",
                     min_value=110, max_value=4000000),
        ToolParameter("数据来源", "enum", "result",
                     description="选择发送数据的来源",
                     options=["result", "custom", "formula"],
                     option_labels={"result": "从结果获取", "custom": "自定义内容", "formula": "公式计算"}),
        ToolParameter("结果键名", "string", "",
                     description="从结果中获取数据的键名"),
        ToolParameter("自定义数据", "string", "",
                     description="自定义发送的内容"),
        ToolParameter("数据格式", "enum", "json",
                     description="发送数据的格式",
                     options=["json", "ascii", "hex", "binary"],
                     option_labels={"json": "JSON", "ascii": "ASCII文本", "hex": "HEX十六进制", "binary": "二进制"}),
        ToolParameter("自动发送", "boolean", False, description="启用自动重复发送"),
        ToolParameter("发送间隔", "float", 1.0,
                     description="自动发送的间隔时间（秒）", min_value=0.1, max_value=3600),
        ToolParameter("Modbus地址", "integer", 0,
                     description="Modbus寄存器起始地址", min_value=0, max_value=65535),
        ToolParameter("寄存器数量", "integer", 1,
                     description="Modbus寄存器数量", min_value=1, max_value=125),
        ToolParameter("触发发送", "boolean", False,
                     description="收到触发信号时发送数据"),
        ToolParameter("拆分发送", "boolean", False,
                     description="将数据拆分成多条发送"),
        ToolParameter("分隔符", "string", ",",
                     description="拆分数据时使用的分隔符"),
    ]
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._comm_manager = get_communication_manager()
        self._protocol = None
        self._last_send_time = 0
        self._send_count = 0
        self._fail_count = 0
        self._use_existing_connection = False
        self._device_id = None
        self._modbus_client = None
        
    def _init_params(self):
        """初始化参数"""
        self.set_param("连接", "__new__")
        self.set_param("协议类型", "tcp_client")
        self.set_param("地址", "127.0.0.1")
        self.set_param("端口", 8080)
        self.set_param("波特率", 9600)
        self.set_param("数据来源", "result")
        self.set_param("结果键名", "")
        self.set_param("自定义数据", "")
        self.set_param("数据格式", "json")
        self.set_param("自动发送", False)
        self.set_param("发送间隔", 1.0)
        self.set_param("Modbus地址", 0)
        self.set_param("寄存器数量", 1)
        self.set_param("触发发送", False)
        self.set_param("拆分发送", False)
        self.set_param("分隔符", ",")
    
    def get_available_connections(self) -> List[Dict[str, Any]]:
        """获取可用连接列表（供UI下拉框使用）"""
        connections = self._comm_manager.get_available_connections()
        result = [("__new__", "+ 新建连接")]
        for conn in connections:
            result.append((conn["device_id"], conn["display_name"]))
        return result
    
    def _run_impl(self):
        """执行发送逻辑"""
        data_source = self.get_param("数据来源")
        auto_send = self.get_param("自动发送")
        
        if auto_send:
            self._handle_auto_send()
        else:
            self._handle_single_send(data_source)
    
    def _handle_single_send(self, data_source: str):
        """处理单次发送"""
        data = self._prepare_send_data(data_source)
        
        if data is None:
            self._result_data.status = False
            self._result_data.message = "无可发送的数据"
            return
        
        success = self._send_to_protocol(data)
        
        self._result_data.status = success
        self._result_data.message = "发送成功" if success else "发送失败"
        self._result_data.set_value("发送成功次数", self._send_count)
        self._result_data.set_value("发送失败次数", self._fail_count)
        self._result_data.set_value("发送数据", data)
        self._result_data.set_value("设备ID", self._device_id)
    
    def _handle_auto_send(self):
        """处理自动发送"""
        current_time = time.time()
        send_interval = self.get_param("发送间隔", 1.0)
        
        if current_time - self._last_send_time >= send_interval:
            data_source = self.get_param("数据来源")
            data = self._prepare_send_data(data_source)
            
            if data is not None:
                success = self._send_to_protocol(data)
                self._last_send_time = current_time
                
                if success:
                    self._send_count += 1
                else:
                    self._fail_count += 1
    
    def _prepare_send_data(self, data_source: str) -> Optional[Any]:
        """准备发送数据"""
        if data_source == "result":
            result_key = self.get_param("结果键名", "")
            
            if result_key and self._result_data:
                return self._result_data.get_value(result_key)
            elif self._result_data:
                return self._result_data.get_all_values()
            else:
                return None
        else:
            custom_data = self.get_param("自定义数据", "")
            
            try:
                format_type = self.get_param("数据格式", "json")
                
                if format_type == "json":
                    return json.loads(custom_data) if custom_data.startswith("{") else custom_data
                else:
                    return custom_data
            except json.JSONDecodeError:
                return custom_data
    
    def _send_to_protocol(self, data: Any) -> bool:
        """通过协议发送数据"""
        try:
            connection = self.get_param("连接", "__new__")
            format_type = self.get_param("数据格式", "json")
            
            if connection != "__new__":
                try:
                    device_id = int(connection)
                    self._device_id = device_id
                    self._protocol = self._comm_manager.get_connection_by_device_id(device_id)
                    self._use_existing_connection = True
                except ValueError:
                    self._use_existing_connection = False
            else:
                self._use_existing_connection = False
            
            if not self._use_existing_connection or not self._protocol:
                protocol_type = self.get_param("协议类型", "tcp_client")
                host = self.get_param("地址", "127.0.0.1")
                port = self.get_param("端口", 8080)
                
                protocol_type_enum = {
                    "tcp_client": ProtocolType.TCP_CLIENT,
                    "tcp_server": ProtocolType.TCP_SERVER,
                    "serial": ProtocolType.SERIAL,
                    "websocket": ProtocolType.WEBSOCKET,
                    "http": ProtocolType.HTTP,
                    "modbus_tcp": ProtocolType.MODBUS_TCP
                }.get(protocol_type, ProtocolType.TCP_CLIENT)
                
                connection_name = f"{protocol_type}_{host}_{port}"
                
                self._protocol = self._comm_manager.create_connection(
                    connection_name,
                    protocol_type,
                    self._build_config(protocol_type, host, port)
                )
                
                if self._protocol:
                    self._device_id = self._comm_manager.get_device_id(connection_name)
            
            if self._protocol and self._protocol.is_connected():
                formatted_data = self._format_data(data, format_type)
                return self._protocol.send(formatted_data)
            else:
                self._fail_count += 1
                return False
                
        except Exception as e:
            self._fail_count += 1
            return False
    
    def _build_config(self, protocol_type: str, host: str, port: int) -> Dict:
        """构建通讯配置"""
        baudrate = self.get_param("波特率", 9600)
        
        if protocol_type == "tcp_client":
            return {"host": host, "port": port, "timeout": 5.0}
        elif protocol_type == "tcp_server":
            return {"host": host, "port": port, "max_connections": 5}
        elif protocol_type == "serial":
            return {"port": host if "/" not in host else host, "baudrate": baudrate}
        elif protocol_type == "websocket":
            return {"url": f"ws://{host}:{port}"}
        elif protocol_type == "http":
            return {"base_url": f"http://{host}:{port}"}
        elif protocol_type == "modbus_tcp":
            return {"host": host, "port": port, "unit_id": 1}
        else:
            return {"host": host, "port": port}
    
    def _format_data(self, data: Any, format_type: str) -> Any:
        """格式化数据"""
        if format_type == "json":
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)
            elif isinstance(data, str):
                return data
            else:
                return json.dumps(data, ensure_ascii=False)
        elif format_type == "ascii":
            if isinstance(data, str):
                return data.encode('ascii')
            elif isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False).encode('ascii')
            elif isinstance(data, bytes):
                return data.decode('ascii', errors='replace').encode('ascii')
            else:
                return str(data).encode('ascii')
        elif format_type == "hex":
            if isinstance(data, str):
                return data.encode('ascii').hex().upper()
            elif isinstance(data, dict):
                json_str = json.dumps(data, ensure_ascii=False)
                return json_str.encode('ascii').hex().upper()
            elif isinstance(data, bytes):
                return data.hex().upper()
            elif isinstance(data, (int, float)):
                import struct
                return struct.pack('!d', float(data)).hex().upper()
            else:
                return str(data).encode('ascii').hex().upper()
        elif format_type == "binary":
            if isinstance(data, str):
                return data.encode('utf-8')
            elif isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, (int, float)):
                import struct
                return struct.pack('!d', float(data))
            else:
                return str(data).encode('utf-8')
        else:
            if isinstance(data, dict):
                return str(data)
            return data
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "已连接": self._protocol.is_connected() if self._protocol else False,
            "连接状态": self._protocol.state.value if self._protocol else "disconnected",
            "设备ID": self._device_id,
            "发送成功次数": self._send_count,
            "发送失败次数": self._fail_count
        }
    
    def reset(self):
        """重置"""
        if not self._use_existing_connection:
            if self._protocol:
                self._protocol = None
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0
        self._device_id = None
        super().reset()


# 注释掉原版本，使用增强版本
# @ToolRegistry.register
# class ReceiveData(ToolBase):
    """接收数据工具（VisionMaster风格优化版）
    
    从外部设备接收数据，可作为流程输入传递给其他工具。
    
    功能特性:
    - 支持多种通讯协议：TCP客户端/服务端、串口、WebSocket
    - 动态IO输出：支持Int/Float/String/ByteArray多种类型
    - 设备ID选择：可选择已创建的通讯连接
    - 超时控制：避免长时间阻塞
    - 连接持久化：监听连接保持不断开
    - 数据过滤：支持起始符、结束符过滤
    - Modbus支持：支持读取保持寄存器
    """
    
    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "从外部设备接收数据，支持TCP/串口/WebSocket等多种协议"
    
    PARAM_DEFINITIONS = [
        ToolParameter("连接", "enum", "__new__",
                     description="选择通讯连接",
                     options=["__new__"],
                     option_labels={"__new__": "+ 新建连接"}),
        ToolParameter("协议类型", "enum", "tcp_server", 
                     description="选择通讯协议类型",
                     options=["tcp_client", "tcp_server", "serial", "websocket", "modbus_tcp"],
                     option_labels={
                         "tcp_client": "TCP客户端",
                         "tcp_server": "TCP服务端",
                         "serial": "串口",
                         "websocket": "WebSocket",
                         "modbus_tcp": "Modbus TCP"
                     }),
        ToolParameter("监听地址", "string", "0.0.0.0", description="本地监听地址"),
        ToolParameter("监听端口", "integer", 8081, description="监听端口号", min_value=1, max_value=65535),
        ToolParameter("波特率", "integer", 9600, description="串口波特率",
                     min_value=110, max_value=4000000),
        ToolParameter("输出类型", "enum", "string",
                     description="接收数据的输出类型",
                     options=["string", "int", "float", "hex", "json", "bytes"],
                     option_labels={
                         "string": "字符串",
                         "int": "整型",
                         "float": "浮点型",
                         "hex": "HEX十六进制",
                         "json": "JSON对象",
                         "bytes": "字节数组"
                     }),
        ToolParameter("超时时间", "float", 5.0,
                     description="接收数据的超时时间（秒）", min_value=0.1, max_value=60),
        ToolParameter("自动监听", "boolean", False, description="自动开始监听"),
        ToolParameter("最大字节数", "integer", 4096,
                     description="最大接收字节数", min_value=64, max_value=65536),
        ToolParameter("输出键名", "string", "received_data",
                     description="输出数据的键名"),
        ToolParameter("起始过滤符", "string", "",
                     description="数据起始过滤符"),
        ToolParameter("结束过滤符", "string", "",
                     description="数据结束过滤符"),
        ToolParameter("Modbus地址", "integer", 0,
                     description="Modbus寄存器起始地址", min_value=0, max_value=65535),
        ToolParameter("读取数量", "integer", 1,
                     description="Modbus寄存器读取数量", min_value=1, max_value=125),
    ]
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._comm_manager = get_communication_manager()
        self._protocol = None
        self._received_data: Optional[Any] = None
        self._receive_count = 0
        self._is_listening = False
        self._use_existing_connection = False
        self._device_id = None
        self._modbus_client = None
        
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
        self.set_param("起始过滤符", "")
        self.set_param("结束过滤符", "")
        self.set_param("Modbus地址", 0)
        self.set_param("读取数量", 1)
    
    def get_available_connections(self) -> List[Dict[str, Any]]:
        """获取可用连接列表"""
        connections = self._comm_manager.get_available_connections()
        result = [("__new__", "+ 新建连接")]
        for conn in connections:
            result.append((conn["device_id"], conn["display_name"]))
        return result
    
    def _run_impl(self):
        """执行接收逻辑"""
        auto_start = self.get_param("自动监听", False)
        
        if auto_start and not self._is_listening:
            self.start_listening()
        
        if self._is_listening:
            self._receive_data()
        else:
            self._result_data.status = False
            self._result_data.message = "未开始监听"
    
    def start_listening(self) -> bool:
        """开始监听"""
        try:
            connection = self.get_param("连接", "__new__")
            
            if connection != "__new__":
                try:
                    device_id = int(connection)
                    self._device_id = device_id
                    self._protocol = self._comm_manager.get_connection_by_device_id(device_id)
                    if self._protocol:
                        self._use_existing_connection = True
                        self._is_listening = True
                        return True
                except ValueError:
                    pass
            
            self._use_existing_connection = False
            
            protocol_type = self.get_param("协议类型", "tcp_server")
            host = self.get_param("监听地址", "0.0.0.0")
            port = self.get_param("监听端口", 8081)
            timeout = self.get_param("超时时间", 5.0)
            baudrate = self.get_param("波特率", 9600)
            
            protocol_type_enum = {
                "tcp_client": ProtocolType.TCP_CLIENT,
                "tcp_server": ProtocolType.TCP_SERVER,
                "serial": ProtocolType.SERIAL,
                "websocket": ProtocolType.WEBSOCKET,
                "modbus_tcp": ProtocolType.MODBUS_TCP
            }.get(protocol_type, ProtocolType.TCP_SERVER)
            
            connection_name = f"{protocol_type}_{host}_{port}"
            
            self._protocol = self._comm_manager.create_connection(
                connection_name,
                protocol_type,
                self._build_receive_config(protocol_type, host, port, baudrate)
            )
            
            if self._protocol and self._protocol.is_connected():
                self._device_id = self._comm_manager.get_device_id(connection_name)
                self._is_listening = True
                return True
            
            return False
            
        except Exception:
            return False
    
    def _build_receive_config(self, protocol_type: str, host: str, port: int, baudrate: int) -> Dict:
        """构建接收通讯配置"""
        timeout = self.get_param("超时时间", 5.0)
        
        if protocol_type == "tcp_server":
            return {"host": host, "port": port, "timeout": timeout}
        elif protocol_type == "tcp_client":
            return {"host": host, "port": port, "timeout": timeout}
        elif protocol_type == "serial":
            return {"port": host if "/" not in host else host, "baudrate": baudrate}
        elif protocol_type == "websocket":
            return {"url": f"ws://{host}:{port}"}
        elif protocol_type == "modbus_tcp":
            return {"host": host, "port": port, "unit_id": 1, "timeout": timeout}
        else:
            return {"host": host, "port": port}
    
    def stop_listening(self):
        """停止监听"""
        if not self._use_existing_connection:
            self._is_listening = False
    
    def _receive_data(self):
        """接收数据"""
        if not self._protocol or not self._protocol.is_connected():
            self._result_data.status = False
            self._result_data.message = "未连接"
            return
        
        try:
            output_type = self.get_param("output_type", "string")
            timeout = self.get_param("timeout", 5.0)
            max_bytes = self.get_param("max_bytes", 4096)
            
            raw_data = self._protocol.receive(timeout)
            
            if raw_data is None:
                self._result_data.status = False
                self._result_data.message = "接收超时"
                return
            
            self._received_data = self._parse_data(raw_data, output_type)
            self._receive_count += 1
            
            self._result_data.status = True
            self._result_data.message = "接收成功"
            self._result_data.set_value("接收数据", self._received_data)
            self._result_data.set_value("接收次数", self._receive_count)
            self._result_data.set_value("输出类型", output_type)
            self._result_data.set_value("设备ID", self._device_id)
            
            self._result_data.set_value("OutputInt", self._get_output_int())
            self._result_data.set_value("OutputFloat", self._get_output_float())
            self._result_data.set_value("OutputString", self._get_output_string())
            self._result_data.set_value("OutputHex", self._get_output_hex())
            self._result_data.set_value("OutputByteArray", self._get_output_bytes())
            
        except Exception as e:
            self._result_data.status = False
            self._result_data.message = f"接收失败: {str(e)}"
    
    def _parse_data(self, raw_data: Any, output_type: str) -> Any:
        """解析数据"""
        if output_type == "json":
            if isinstance(raw_data, bytes):
                try:
                    return json.loads(raw_data.decode('utf-8'))
                except json.JSONDecodeError:
                    return raw_data.decode('utf-8', errors='replace')
            elif isinstance(raw_data, str):
                try:
                    return json.loads(raw_data)
                except json.JSONDecodeError:
                    return raw_data
            return raw_data
        elif output_type == "int":
            try:
                if isinstance(raw_data, bytes):
                    return int(raw_data.decode('utf-8').strip())
                return int(str(raw_data).strip())
            except (ValueError, TypeError):
                return 0
        elif output_type == "float":
            try:
                if isinstance(raw_data, bytes):
                    return float(raw_data.decode('utf-8').strip())
                return float(str(raw_data).strip())
            except (ValueError, TypeError):
                return 0.0
        elif output_type == "hex":
            if isinstance(raw_data, bytes):
                return raw_data.hex().upper()
            return str(raw_data).encode('utf-8').hex().upper()
        else:
            if isinstance(raw_data, bytes):
                return raw_data.decode('utf-8', errors='replace')
            return raw_data
    
    def _get_output_int(self) -> int:
        """获取整型输出（VisionMaster风格动态接口）"""
        try:
            if isinstance(self._received_data, (int, float)):
                return int(self._received_data)
            return int(str(self._received_data).strip())
        except (ValueError, TypeError):
            return 0
    
    def _get_output_float(self) -> float:
        """获取浮点型输出（VisionMaster风格动态接口）"""
        try:
            if isinstance(self._received_data, (int, float)):
                return float(self._received_data)
            return float(str(self._received_data).strip())
        except (ValueError, TypeError):
            return 0.0
    
    def _get_output_string(self) -> str:
        """获取字符串输出（VisionMaster风格动态接口）"""
        if isinstance(self._received_data, str):
            return self._received_data
        elif isinstance(self._received_data, bytes):
            return self._received_data.decode('utf-8', errors='replace')
        return str(self._received_data)
    
    def _get_output_hex(self) -> str:
        """获取HEX输出"""
        if isinstance(self._received_data, bytes):
            return self._received_data.hex().upper()
        if isinstance(self._received_data, str):
            return self._received_data.encode('utf-8').hex().upper()
        return str(self._received_data).encode('utf-8').hex().upper()
    
    def _get_output_bytes(self) -> bytes:
        """获取二进制输出（VisionMaster风格动态接口）"""
        if isinstance(self._received_data, bytes):
            return self._received_data
        if isinstance(self._received_data, str):
            return self._received_data.encode('utf-8')
        return str(self._received_data).encode('utf-8')
    
    def get_received_data(self) -> Optional[Any]:
        """获取最近接收的数据"""
        return self._received_data
    
    def get_listening_status(self) -> Dict[str, Any]:
        """获取监听状态"""
        return {
            "正在监听": self._is_listening,
            "已连接": self._protocol.is_connected() if self._protocol else False,
            "设备ID": self._device_id,
            "接收次数": self._receive_count,
            "最后数据": self._received_data
        }
    
    def reset(self):
        """重置"""
        if not self._use_existing_connection:
            self._is_listening = False
        self._received_data = None
        self._receive_count = 0
        self._device_id = None
        super().reset()

# 注册增强版本的通信工具
try:
    from tools.enhanced_communication import EnhancedSendData, EnhancedReceiveData
    # 为了兼容旧代码，创建别名
    SendData = EnhancedSendData
    ReceiveData = EnhancedReceiveData
    ToolRegistry.register(EnhancedSendData)
    ToolRegistry.register(EnhancedReceiveData)
except ImportError as e:
    print(f"导入增强通信工具失败: {e}")
