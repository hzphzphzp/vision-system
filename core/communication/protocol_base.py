#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯协议基类定义

提供所有通讯协议的抽象基类和通用功能。

Author: Vision System Team
Date: 2026-01-13
"""

import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger("Communication")


class ProtocolType(Enum):
    """协议类型枚举"""
    TCP_CLIENT = "tcp_client"
    TCP_SERVER = "tcp_server"
    SERIAL = "serial"
    WEBSOCKET = "websocket"
    HTTP = "http"
    MODBUS_TCP = "modbus_tcp"


class ConnectionState(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ProtocolBase:
    """通讯协议基类
    
    所有具体协议实现必须继承此类并实现所有抽象方法。
    
    使用示例:
        class MyProtocol(ProtocolBase):
            def connect(self, config: dict) -> bool:
                # 实现连接逻辑
                pass
    """
    
    protocol_name: str = "BaseProtocol"
    
    def __init__(self):
        self._state = ConnectionState.DISCONNECTED
        self._config: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}
    
    @property
    def state(self) -> ConnectionState:
        """获取当前连接状态"""
        return self._state
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self._config.copy()
    
    def register_callback(self, event: str, callback: Callable):
        """注册事件回调
        
        Args:
            event: 事件名称
            callback: 回调函数
        """
        self._callbacks[event] = callback
    
    def _emit(self, event: str, *args, **kwargs):
        """触发事件回调"""
        if event in self._callbacks:
            try:
                self._callbacks[event](*args, **kwargs)
            except Exception as e:
                logger.error(f"[{self.protocol_name}] 回调函数执行失败: {e}")
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接
        
        Args:
            config: 连接配置字典
            
        Returns:
            bool: 连接是否成功
        """
        raise NotImplementedError("子类必须实现connect方法")
    
    def disconnect(self):
        """断开连接"""
        raise NotImplementedError("子类必须实现disconnect方法")
    
    def send(self, data: Any) -> bool:
        """发送数据
        
        Args:
            data: 要发送的数据
            
        Returns:
            bool: 发送是否成功
        """
        raise NotImplementedError("子类必须实现send方法")
    
    def receive(self, timeout: float = None) -> Any:
        """接收数据
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            接收到的数据
        """
        raise NotImplementedError("子类必须实现receive方法")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._state == ConnectionState.CONNECTED
    
    def set_state(self, state: ConnectionState):
        """设置连接状态"""
        old_state = self._state
        self._state = state
        if old_state != state:
            logger.debug(f"[{self.protocol_name}] 状态变更: {old_state.value} -> {state.value}")
    
    def __enter__(self):
        """支持上下文管理器使用"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器时自动断开连接"""
        self.disconnect()
        return False


class DataParser:
    """数据解析器基类"""
    
    def parse(self, raw_data: bytes) -> Any:
        """解析原始数据"""
        return raw_data
    
    def format(self, data: Any) -> bytes:
        """格式化要发送的数据"""
        if isinstance(data, str):
            return data.encode('utf-8')
        elif isinstance(data, bytes):
            return data
        else:
            return str(data).encode('utf-8')


class TextParser(DataParser):
    """文本数据解析器"""
    
    def __init__(self, encoding: str = 'utf-8', delimiter = '\n'):
        self.encoding = encoding
        self.delimiter = delimiter
        self._buffer = b''
    
    def parse(self, raw_data: bytes) -> str:
        """解析为文本，支持分割"""
        self._buffer += raw_data
        delimiter_bytes = self.delimiter.encode(self.encoding) if isinstance(self.delimiter, str) else self.delimiter
        if delimiter_bytes in self._buffer:
            lines = self._buffer.split(delimiter_bytes)
            self._buffer = lines[-1]
            return lines[0].decode(self.encoding) if lines[0] else None
        return None
    
    def format(self, data: Any) -> bytes:
        if isinstance(data, str):
            data_bytes = data.encode(self.encoding)
        else:
            data_bytes = str(data).encode(self.encoding)
        
        if isinstance(self.delimiter, bytes):
            return data_bytes + self.delimiter
        else:
            return data_bytes + self.delimiter.encode(self.encoding)


class JSONParser(DataParser):
    """JSON数据解析器"""
    
    def parse(self, raw_data: bytes) -> dict:
        """解析为JSON字典"""
        import json
        try:
            return json.loads(raw_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"[DataParser] JSON解析错误: {e}")
            return {}
    
    def format(self, data: Any) -> bytes:
        import json
        if isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False).encode('utf-8')
        return str(data).encode('utf-8')


class BinaryParser(DataParser):
    """二进制数据解析器"""
    
    def __init__(self, struct_format: str = None):
        import struct
        self.struct_format = struct_format
    
    def parse(self, raw_data: bytes) -> Any:
        """解析二进制数据"""
        import struct
        if self.struct_format:
            return struct.unpack(self.struct_format, raw_data)
        return raw_data
    
    def format(self, data: Any) -> bytes:
        import struct
        if self.struct_format:
            return struct.pack(self.struct_format, data)
        if isinstance(data, (int, float)):
            return struct.pack('!d', data)
        return data if isinstance(data, bytes) else b''
