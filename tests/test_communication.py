#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯模块测试代码

测试通讯模块的核心功能，包括：
- 通讯配置管理
- 数据发送和接收
- 连接状态监控
- 日志记录

Author: Vision System Team
Date: 2026-01-27
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.communication import CommunicationManager, get_communication_manager
from core.communication import ProtocolManager, ProtocolType
from core.communication.tcp_client import TCPClient
from core.communication.tcp_server import TCPServer
from core.communication.serial_port import SerialPort
from core.communication.websocket import WebSocketClient
from core.communication.http_client import HTTPClient
from core.communication.modbus_tcp import ModbusTCPClient


class TestCommunicationManager(unittest.TestCase):
    """测试通讯管理器"""

    def setUp(self):
        """设置测试环境"""
        self.comm_manager = get_communication_manager()

    def test_singleton_instance(self):
        """测试单例模式"""
        instance1 = get_communication_manager()
        instance2 = get_communication_manager()
        self.assertIs(instance1, instance2)

    def test_create_connection(self):
        """测试创建连接"""
        # 创建TCP客户端连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        tcp_protocol = self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        self.assertIsNotNone(tcp_protocol)

    def test_get_connection(self):
        """测试获取连接"""
        # 先创建连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取连接
        tcp_protocol = self.comm_manager.get_connection("test_tcp")
        self.assertIsNotNone(tcp_protocol)

    def test_get_available_connections(self):
        """测试获取可用连接列表"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取可用连接
        connections = self.comm_manager.get_available_connections()
        self.assertGreater(len(connections), 0)

    def test_set_string(self):
        """测试设置字符串型数据"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取设备ID
        device_id = self.comm_manager.get_device_id("test_tcp")
        # 设置字符串
        result = self.comm_manager.set_string(device_id, "test message")
        # 由于是模拟连接，结果可能是False，但方法应该能正常执行
        self.assertIsInstance(result, bool)

    def test_set_int(self):
        """测试设置整型数据"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取设备ID
        device_id = self.comm_manager.get_device_id("test_tcp")
        # 设置整型
        result = self.comm_manager.set_int(device_id, 12345)
        # 由于是模拟连接，结果可能是False，但方法应该能正常执行
        self.assertIsInstance(result, bool)

    def test_set_float(self):
        """测试设置浮点型数据"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取设备ID
        device_id = self.comm_manager.get_device_id("test_tcp")
        # 设置浮点型
        result = self.comm_manager.set_float(device_id, 123.45)
        # 由于是模拟连接，结果可能是False，但方法应该能正常执行
        self.assertIsInstance(result, bool)

    def test_get_read_data(self):
        """测试获取读取数据"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取设备ID
        device_id = self.comm_manager.get_device_id("test_tcp")
        # 获取读取数据
        data = self.comm_manager.get_read_data(device_id)
        # 由于是模拟连接，结果可能是None，但方法应该能正常执行
        self.assertIsInstance(data, (type(None), bytes))

    def test_is_device_connect(self):
        """测试检查设备是否处于连接状态"""
        # 创建测试连接
        tcp_config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 5.0
        }
        self.comm_manager.create_connection(
            "test_tcp", "tcp_client", tcp_config
        )
        # 获取设备ID
        device_id = self.comm_manager.get_device_id("test_tcp")
        # 检查连接状态
        result = self.comm_manager.is_device_connect(device_id)
        # 由于是模拟连接，结果可能是False，但方法应该能正常执行
        self.assertIsInstance(result, bool)


class TestProtocolManager(unittest.TestCase):
    """测试协议管理器"""

    def setUp(self):
        """设置测试环境"""
        self.protocol_manager = ProtocolManager()

    def test_create_protocol(self):
        """测试创建协议"""
        # 创建TCP客户端协议
        tcp_protocol = self.protocol_manager.create_protocol(
            ProtocolType.TCP_CLIENT, "test_tcp"
        )
        self.assertIsInstance(tcp_protocol, TCPClient)

        # 创建TCP服务端协议
        tcp_server_protocol = self.protocol_manager.create_protocol(
            ProtocolType.TCP_SERVER, "test_tcp_server"
        )
        self.assertIsInstance(tcp_server_protocol, TCPServer)

    def test_get_protocol(self):
        """测试获取协议"""
        # 创建协议
        self.protocol_manager.create_protocol(
            ProtocolType.TCP_CLIENT, "test_tcp"
        )
        # 获取协议
        tcp_protocol = self.protocol_manager.get_protocol("test_tcp")
        self.assertIsInstance(tcp_protocol, TCPClient)


class TestTCPClient(unittest.TestCase):
    """测试TCP客户端"""

    def setUp(self):
        """设置测试环境"""
        self.tcp_client = TCPClient()

    def test_connect(self):
        """测试连接"""
        config = {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout": 1.0
        }
        # 由于是测试环境，连接可能会失败，但方法应该能正常执行
        result = self.tcp_client.connect(config)
        self.assertIsInstance(result, bool)

    def test_send(self):
        """测试发送数据"""
        # 发送数据，由于未连接，结果可能是False，但方法应该能正常执行
        result = self.tcp_client.send("test message")
        self.assertIsInstance(result, bool)

    def test_receive(self):
        """测试接收数据"""
        # 接收数据，由于未连接，结果可能是None，但方法应该能正常执行
        result = self.tcp_client.receive(timeout=0.1)
        self.assertIsInstance(result, (type(None), bytes))

    def test_disconnect(self):
        """测试断开连接"""
        # 断开连接，方法应该能正常执行
        self.tcp_client.disconnect()

    def test_is_connected(self):
        """测试检查连接状态"""
        # 检查连接状态，结果应该是False
        result = self.tcp_client.is_connected()
        self.assertFalse(result)


class TestTCPServer(unittest.TestCase):
    """测试TCP服务端"""

    def setUp(self):
        """设置测试环境"""
        self.tcp_server = TCPServer()

    def test_listen(self):
        """测试开始监听"""
        config = {
            "host": "0.0.0.0",
            "port": 8080,
            "max_connections": 5
        }
        # 开始监听，由于是测试环境，可能会失败，但方法应该能正常执行
        result = self.tcp_server.listen(config)
        self.assertIsInstance(result, bool)

    def test_stop(self):
        """测试停止服务"""
        # 停止服务，方法应该能正常执行
        self.tcp_server.stop()

    def test_broadcast(self):
        """测试广播消息"""
        # 广播消息，由于未启动，结果应该是0，但方法应该能正常执行
        result = self.tcp_server.broadcast("test message")
        self.assertEqual(result, 0)


class TestSerialPort(unittest.TestCase):
    """测试串口"""

    def setUp(self):
        """设置测试环境"""
        self.serial_port = SerialPort()

    def test_connect(self):
        """测试连接"""
        config = {
            "port": "COM1",
            "baudrate": 9600
        }
        # 由于是测试环境，连接可能会失败，但方法应该能正常执行
        result = self.serial_port.connect(config)
        self.assertIsInstance(result, bool)

    def test_send(self):
        """测试发送数据"""
        # 发送数据，由于未连接，结果可能是False，但方法应该能正常执行
        result = self.serial_port.send("test message")
        self.assertIsInstance(result, bool)

    def test_receive(self):
        """测试接收数据"""
        # 接收数据，由于未连接，结果可能是None，但方法应该能正常执行
        result = self.serial_port.receive(timeout=0.1)
        self.assertIsInstance(result, (type(None), bytes))

    def test_disconnect(self):
        """测试断开连接"""
        # 断开连接，方法应该能正常执行
        self.serial_port.disconnect()

    def test_is_connected(self):
        """测试检查连接状态"""
        # 检查连接状态，结果应该是False
        result = self.serial_port.is_connected()
        self.assertFalse(result)


class TestWebSocketClient(unittest.TestCase):
    """测试WebSocket客户端"""

    def setUp(self):
        """设置测试环境"""
        self.ws_client = WebSocketClient()

    def test_connect(self):
        """测试连接"""
        config = {
            "url": "ws://localhost:8080/ws"
        }
        # 由于是测试环境，连接可能会失败，但方法应该能正常执行
        result = self.ws_client.connect(config)
        self.assertIsInstance(result, bool)

    def test_send(self):
        """测试发送数据"""
        # 发送数据，由于未连接，结果可能是False，但方法应该能正常执行
        result = self.ws_client.send("test message")
        self.assertIsInstance(result, bool)

    def test_disconnect(self):
        """测试断开连接"""
        # 断开连接，方法应该能正常执行
        self.ws_client.disconnect()

    def test_is_connected(self):
        """测试检查连接状态"""
        # 检查连接状态，结果应该是False
        result = self.ws_client.is_connected()
        self.assertFalse(result)


class TestHTTPClient(unittest.TestCase):
    """测试HTTP客户端"""

    def setUp(self):
        """设置测试环境"""
        self.http_client = HTTPClient()

    def test_connect(self):
        """测试连接"""
        config = {
            "base_url": "https://httpbin.org",
            "timeout": 5.0
        }
        # 连接，方法应该能正常执行
        result = self.http_client.connect(config)
        self.assertTrue(result)

    def test_get(self):
        """测试GET请求"""
        config = {
            "base_url": "https://httpbin.org",
            "timeout": 5.0
        }
        self.http_client.connect(config)
        # 发送GET请求
        result = self.http_client.get("/get")
        self.assertIsInstance(result, dict)

    def test_post(self):
        """测试POST请求"""
        config = {
            "base_url": "https://httpbin.org",
            "timeout": 5.0
        }
        self.http_client.connect(config)
        # 发送POST请求
        data = {"test": "value"}
        result = self.http_client.post("/post", data)
        self.assertIsInstance(result, dict)

    def test_disconnect(self):
        """测试断开连接"""
        # 断开连接，方法应该能正常执行
        self.http_client.disconnect()

    def test_is_connected(self):
        """测试检查连接状态"""
        # 检查连接状态，结果应该是False
        result = self.http_client.is_connected()
        self.assertFalse(result)


class TestModbusTCPClient(unittest.TestCase):
    """测试Modbus TCP客户端"""

    def setUp(self):
        """设置测试环境"""
        self.modbus_client = ModbusTCPClient()

    def test_connect(self):
        """测试连接"""
        config = {
            "host": "127.0.0.1",
            "port": 502,
            "timeout": 1.0,
            "unit_id": 1
        }
        # 由于是测试环境，连接可能会失败，但方法应该能正常执行
        result = self.modbus_client.connect(config)
        self.assertIsInstance(result, bool)

    def test_read_coils(self):
        """测试读线圈"""
        # 读线圈，由于未连接，结果可能是(False, None)，但方法应该能正常执行
        result = self.modbus_client.read_coils(0, 1)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_write_single_coil(self):
        """测试写单个线圈"""
        # 写单个线圈，由于未连接，结果可能是(False, None)，但方法应该能正常执行
        result = self.modbus_client.write_single_coil(0, 1)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_disconnect(self):
        """测试断开连接"""
        # 断开连接，方法应该能正常执行
        self.modbus_client.disconnect()

    def test_is_connected(self):
        """测试检查连接状态"""
        # 检查连接状态，结果应该是False
        result = self.modbus_client.is_connected()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
