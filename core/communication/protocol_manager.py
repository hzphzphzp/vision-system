#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协议管理器模块

统一管理和调度各种通讯协议，提供简化的API接口。

功能特性:
- 协议实例管理
- 统一配置接口
- 事件广播
- 连接池管理

Usage:
    from core.communication import ProtocolManager, ProtocolType

    manager = ProtocolManager()

    # 创建TCP客户端
    tcp = manager.create_protocol(ProtocolType.TCP_CLIENT)
    tcp.connect({"host": "192.168.1.100", "port": 8080})

    # 创建串口
    serial = manager.create_protocol(ProtocolType.SERIAL)
    serial.connect({"port": "COM1", "baudrate": 9600})

    # 发送数据
    tcp.send("Hello")

    # 断开所有连接
    manager.disconnect_all()
"""

import logging
import os
import sys
from enum import Enum
from typing import Any, Callable, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import (
    ConnectionState,
    ProtocolBase,
    ProtocolType,
)

logger = logging.getLogger("ProtocolManager")


class ProtocolManager:
    """协议管理器

    统一管理和调度各种通讯协议。
    """

    def __init__(self):
        self._protocols: Dict[str, ProtocolBase] = {}
        self._protocol_lock = __import__("threading").Lock()

    def create_protocol(
        self, protocol_type: ProtocolType, name: str = None
    ) -> ProtocolBase:
        """创建协议实例

        Args:
            protocol_type: 协议类型
            name: 自定义名称

        Returns:
            ProtocolBase: 协议实例
        """
        protocol_id = name or f"{protocol_type.value}_{id(self)}"

        if protocol_id in self._protocols:
            logger.warning(
                f"[ProtocolManager] 协议 {protocol_id} 已存在，将返回现有实例"
            )
            return self._protocols[protocol_id]

        protocol = self._create_protocol_instance(protocol_type)
        protocol.register_callback(
            "on_error",
            lambda msg: logger.error(f"[{protocol.protocol_name}] {msg}"),
        )

        with self._protocol_lock:
            self._protocols[protocol_id] = protocol

        logger.info(
            f"[ProtocolManager] 创建协议: {protocol_id} ({protocol_type.value})"
        )
        return protocol

    def _create_protocol_instance(
        self, protocol_type: ProtocolType
    ) -> ProtocolBase:
        """创建协议实例"""
        if protocol_type == ProtocolType.TCP_CLIENT:
            from core.communication.tcp_client import TCPClient

            return TCPClient()
        elif protocol_type == ProtocolType.TCP_SERVER:
            from core.communication.tcp_server import TCPServer

            return TCPServer()
        elif protocol_type == ProtocolType.SERIAL:
            from core.communication.serial_port import SerialPort

            return SerialPort()
        elif protocol_type == ProtocolType.WEBSOCKET:
            from core.communication.websocket import WebSocketClient

            return WebSocketClient()
        elif protocol_type == ProtocolType.HTTP:
            from core.communication.http_client import HTTPClient

            return HTTPClient()
        elif protocol_type == ProtocolType.MODBUS_TCP:
            from core.communication.modbus_tcp import ModbusTCPClient

            return ModbusTCPClient()
        else:
            raise ValueError(f"不支持的协议类型: {protocol_type}")

    def get_protocol(self, name: str) -> Optional[ProtocolBase]:
        """获取协议实例"""
        return self._protocols.get(name)

    def get_protocols(self) -> Dict[str, ProtocolBase]:
        """获取所有协议实例"""
        return self._protocols.copy()

    def connect(self, name: str, config: Dict[str, Any]) -> bool:
        """连接协议"""
        protocol = self.get_protocol(name)
        if not protocol:
            logger.error(f"[ProtocolManager] 协议 {name} 不存在")
            return False
        return protocol.connect(config)

    def disconnect(self, name: str):
        """断开协议连接"""
        protocol = self.get_protocol(name)
        if protocol:
            protocol.disconnect()

    def disconnect_all(self):
        """断开所有连接"""
        with self._protocol_lock:
            for protocol in list(self._protocols.values()):
                protocol.disconnect()
        logger.info("[ProtocolManager] 已断开所有连接")

    def remove_protocol(self, name: str):
        """移除协议实例"""
        with self._protocol_lock:
            if name in self._protocols:
                protocol = self._protocols[name]
                protocol.disconnect()
                del self._protocols[name]
                logger.info(f"[ProtocolManager] 已移除协议: {name}")

    def remove_all(self):
        """移除所有协议"""
        self.disconnect_all()
        with self._protocol_lock:
            self._protocols.clear()
        logger.info("[ProtocolManager] 已移除所有协议")

    def broadcast(self, data: Any) -> int:
        """广播消息到所有已连接的协议"""
        count = 0
        with self._protocol_lock:
            for protocol in self._protocols.values():
                if protocol.is_connected():
                    if protocol.send(data):
                        count += 1
        return count

    def get_connection_stats(self) -> Dict[str, Dict]:
        """获取连接状态统计"""
        stats = {}
        with self._protocol_lock:
            for name, protocol in self._protocols.items():
                stats[name] = {
                    "type": protocol.protocol_name,
                    "connected": protocol.is_connected(),
                    "state": protocol.state.value,
                    "config": protocol.config,
                }
        return stats

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.remove_all()
        return False


class ProtocolBuilder:
    """协议构建器

    提供流式API来配置和创建协议。
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}

    def tcp_client(self, name: str = None) -> "ProtocolBuilder":
        """创建TCP客户端"""
        self._type = ProtocolType.TCP_CLIENT
        self._name = name
        return self

    def tcp_server(self, name: str = None) -> "ProtocolBuilder":
        """创建TCP服务端"""
        self._type = ProtocolType.TCP_SERVER
        self._name = name
        return self

    def serial(self, name: str = None) -> "ProtocolBuilder":
        """创建串口"""
        self._type = ProtocolType.SERIAL
        self._name = name
        return self

    def websocket(self, name: str = None) -> "ProtocolBuilder":
        """创建WebSocket"""
        self._type = ProtocolType.WEBSOCKET
        self._name = name
        return self

    def http(self, name: str = None) -> "ProtocolBuilder":
        """创建HTTP客户端"""
        self._type = ProtocolType.HTTP
        self._name = name
        return self

    def host(self, host: str) -> "ProtocolBuilder":
        """设置主机地址"""
        self._config["host"] = host
        return self

    def port(self, port: int) -> "ProtocolBuilder":
        """设置端口"""
        self._config["port"] = port
        return self

    def url(self, url: str) -> "ProtocolBuilder":
        """设置URL"""
        self._config["url"] = url
        return self

    def base_url(self, base_url: str) -> "ProtocolBuilder":
        """设置基础URL"""
        self._config["base_url"] = base_url
        return self

    def baudrate(self, baudrate: int) -> "ProtocolBuilder":
        """设置波特率"""
        self._config["baudrate"] = baudrate
        return self

    def timeout(self, timeout: float) -> "ProtocolBuilder":
        """设置超时"""
        self._config["timeout"] = timeout
        return self

    def auto_reconnect(self, enabled: bool = True) -> "ProtocolBuilder":
        """设置自动重连"""
        self._config["auto_reconnect"] = enabled
        return self

    def on_connect(self, callback: Callable) -> "ProtocolBuilder":
        """连接回调"""
        self._callbacks["on_connect"] = callback
        return self

    def on_disconnect(self, callback: Callable) -> "ProtocolBuilder":
        """断开回调"""
        self._callbacks["on_disconnect"] = callback
        return self

    def on_receive(self, callback: Callable) -> "ProtocolBuilder":
        """接收回调"""
        self._callbacks["on_receive"] = callback
        return self

    def on_error(self, callback: Callable) -> "ProtocolBuilder":
        """错误回调"""
        self._callbacks["on_error"] = callback
        return self

    def build(self, manager: ProtocolManager = None) -> ProtocolBase:
        """构建协议实例"""
        if not hasattr(self, "_type"):
            raise ValueError("请先选择协议类型")

        protocol = manager.create_protocol(self._type, self._name)

        for event, callback in self._callbacks.items():
            protocol.register_callback(event, callback)

        return protocol

    def connect(self, manager: ProtocolManager = None) -> bool:
        """构建并连接"""
        protocol = self.build(manager)
        return protocol.connect(self._config)


if __name__ == "__main__":
    import json
    import logging

    logging.basicConfig(level=logging.INFO)

    manager = ProtocolManager()

    # 使用构建器创建TCP客户端
    print("\n=== TCP客户端示例 ===")
    tcp = (
        ProtocolBuilder()
        .tcp_client("my_tcp")
        .host("127.0.0.1")
        .port(8888)
        .timeout(10)
        .auto_reconnect(False)
        .on_connect(lambda: print("TCP连接成功"))
        .on_receive(lambda data: print(f"TCP收到: {data}"))
        .build(manager)
    )

    stats = manager.get_connection_stats()
    print(f"连接状态: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 创建串口
    print("\n=== 串口示例 ===")
    serial = (
        ProtocolBuilder()
        .serial("my_serial")
        .port("COM1")
        .baudrate(9600)
        .timeout(1)
        .build(manager)
    )

    # 清理
    manager.remove_all()
    print("\n清理完成")
