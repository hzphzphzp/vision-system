#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯管理模块

提供多种工业通讯协议的支持，包括TCP/IP、串口、WebSocket、HTTP、Modbus TCP等。
采用模块化设计，各协议组件相互独立，便于扩展和维护。

模块结构:
- protocol_base.py: 协议基类定义
- tcp_client.py: TCP客户端
- tcp_server: TCP服务端
- serial_port.py: 串口通讯
- websocket.py: WebSocket通讯
- http_client.py: HTTP REST API客户端
- modbus_tcp.py: Modbus TCP协议
- protocol_manager.py: 协议管理器

Author: Vision System Team
Date: 2026-01-13
"""

from core.communication.http_client import HTTPClient
from core.communication.modbus_tcp import ModbusTCPClient
from core.communication.protocol_base import (
    BinaryParser,
    ConnectionState,
    DataParser,
    JSONParser,
    ProtocolBase,
    ProtocolType,
    TextParser,
)
from core.communication.protocol_manager import (
    ProtocolBuilder,
    ProtocolManager,
)
from core.communication.serial_port import SerialPort
from core.communication.tcp_client import TCPClient
from core.communication.tcp_server import TCPServer
from core.communication.websocket import WebSocketClient

__all__ = [
    "ProtocolBase",
    "ProtocolType",
    "ConnectionState",
    "DataParser",
    "TextParser",
    "JSONParser",
    "BinaryParser",
    "TCPClient",
    "TCPServer",
    "SerialPort",
    "WebSocketClient",
    "HTTPClient",
    "ModbusTCPClient",
    "ProtocolManager",
    "ProtocolBuilder",
]
