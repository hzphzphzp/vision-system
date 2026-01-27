#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯模块测试用例

测试各种通讯协议的功能和兼容性。

Usage:
    pytest tests/test_communication.py -v
    python tests/test_communication.py
"""

import sys
import os
import unittest
import logging
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import (
    ProtocolBase, ConnectionState, DataParser, TextParser, JSONParser
)
from core.communication.protocol_manager import ProtocolType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestCommunication")


class TestProtocolBase(unittest.TestCase):
    """测试协议基类"""
    
    def test_protocol_base_creation(self):
        """测试协议基类创建"""
        class TestProtocol(ProtocolBase):
            protocol_name = "TestProtocol"
            
            def connect(self, config):
                return True
            
            def disconnect(self):
                pass
            
            def send(self, data):
                return True
            
            def receive(self, timeout=None):
                return None
            
            def is_connected(self):
                return True
        
        protocol = TestProtocol()
        self.assertEqual(protocol.state, ConnectionState.DISCONNECTED)
        self.assertEqual(protocol.protocol_name, "TestProtocol")
        logger.info("✅ 协议基类创建测试通过")
    
    def test_callback_registration(self):
        """测试回调注册"""
        class TestProtocol(ProtocolBase):
            protocol_name = "TestProtocol"
            
            def connect(self, config):
                return True
            
            def disconnect(self):
                pass
            
            def send(self, data):
                return True
            
            def receive(self, timeout=None):
                return None
        
        protocol = TestProtocol()
        
        callback_called = [False]
        
        def on_test():
            callback_called[0] = True
        
        protocol.register_callback("on_connect", on_test)
        protocol._emit("on_connect")
        
        self.assertTrue(callback_called[0])
        logger.info("✅ 回调注册测试通过")
    
    def test_context_manager(self):
        """测试上下文管理器"""
        class TestProtocol(ProtocolBase):
            protocol_name = "TestProtocol"
            disconnected = [False]
            
            def connect(self, config):
                return True
            
            def disconnect(self):
                TestProtocol.disconnected[0] = True
            
            def send(self, data):
                return True
        
        with TestProtocol() as protocol:
            protocol.connect({})
        
        self.assertTrue(TestProtocol.disconnected[0])
        logger.info("✅ 上下文管理器测试通过")


class TestDataParser(unittest.TestCase):
    """测试数据解析器"""
    
    def test_data_parser(self):
        """测试基础数据解析器"""
        parser = DataParser()
        
        result = parser.parse(b"hello")
        self.assertEqual(result, b"hello")
        
        result = parser.format("world")
        self.assertEqual(result, b"world")
        
        result = parser.format(123)
        self.assertEqual(result, b"123")
        
        logger.info("✅ 基础数据解析器测试通过")
    
    def test_text_parser(self):
        """测试文本解析器"""
        parser = TextParser(encoding='utf-8', delimiter=b'\n')
        
        result = parser.parse(b"hello\n")
        self.assertEqual(result, "hello")
        
        result = parser.format("world")
        self.assertEqual(result, b"world\n")
        
        logger.info("✅ 文本解析器测试通过")
    
    def test_json_parser(self):
        """测试JSON解析器"""
        import json
        
        parser = JSONParser()
        
        data = {"name": "test", "value": 123}
        encoded = json.dumps(data).encode('utf-8')
        
        result = parser.parse(encoded)
        self.assertEqual(result, data)
        
        result = parser.format(data)
        self.assertEqual(result, encoded)
        
        logger.info("✅ JSON解析器测试通过")


class TestTCPClient(unittest.TestCase):
    """测试TCP客户端"""
    
    def test_tcp_client_creation(self):
        """测试TCP客户端创建"""
        from core.communication.tcp_client import TCPClient
        
        client = TCPClient()
        self.assertEqual(client.state, ConnectionState.DISCONNECTED)
        self.assertEqual(client.protocol_name, "TCPClient")
        
        logger.info("✅ TCP客户端创建测试通过")
    
    def test_tcp_client_connect_failure(self):
        """测试TCP客户端连接失败"""
        from core.communication.tcp_client import TCPClient
        
        client = TCPClient()
        client.register_callback("on_error", lambda msg: logger.debug(f"错误: {msg}"))
        
        result = client.connect({
            "host": "127.0.0.1",
            "port": 99999,
            "timeout": 0.5
        })
        
        self.assertFalse(result)
        self.assertEqual(client.state, ConnectionState.ERROR)
        
        logger.info("✅ TCP客户端连接失败测试通过")


class TestTCPServer(unittest.TestCase):
    """测试TCP服务端"""
    
    def test_tcp_server_creation(self):
        """测试TCP服务端创建"""
        from core.communication.tcp_server import TCPServer
        
        server = TCPServer()
        self.assertEqual(server.state, ConnectionState.DISCONNECTED)
        self.assertEqual(server.protocol_name, "TCPServer")
        
        logger.info("✅ TCP服务端创建测试通过")
    
    def test_tcp_server_listen(self):
        """测试TCP服务端监听"""
        from core.communication.tcp_server import TCPServer
        
        server = TCPServer()
        
        result = server.listen({
            "host": "127.0.0.1",
            "port": 19999,
            "backlog": 5
        })
        
        self.assertTrue(result)
        self.assertEqual(server.state, ConnectionState.CONNECTED)
        
        server.stop()
        
        logger.info("✅ TCP服务端监听测试通过")
    
    def test_tcp_server_broadcast(self):
        """测试TCP服务端广播"""
        from core.communication.tcp_server import TCPServer
        
        server = TCPServer()
        
        server.listen({"port": 19998})
        
        clients = server.get_connected_clients()
        self.assertEqual(clients, [])
        
        result = server.broadcast("test")
        self.assertEqual(result, 0)
        
        server.stop()
        
        logger.info("✅ TCP服务端广播测试通过")


class TestSerialPort(unittest.TestCase):
    """测试串口"""
    
    def test_serial_port_creation(self):
        """测试串口创建"""
        from core.communication.serial_port import SerialPort
        
        serial = SerialPort()
        self.assertEqual(serial.state, ConnectionState.DISCONNECTED)
        self.assertEqual(serial.protocol_name, "SerialPort")
        
        logger.info("✅ 串口创建测试通过")
    
    def test_serial_port_list(self):
        """测试串口列表"""
        from core.communication.serial_port import SerialPort
        
        ports = SerialPort.list_ports()
        self.assertIsInstance(ports, list)
        
        logger.info(f"可用串口: {[p['port'] for p in ports]}")
        logger.info("✅ 串口列表测试通过")
    
    def test_serial_port_connect_failure(self):
        """测试串口连接失败"""
        from core.communication.serial_port import SerialPort
        
        serial = SerialPort()
        
        result = serial.connect({
            "port": "COM999",
            "baudrate": 9600,
            "timeout": 0.5
        })
        
        self.assertFalse(result)
        
        logger.info("✅ 串口连接失败测试通过")


class TestHTTPClient(unittest.TestCase):
    """测试HTTP客户端"""
    
    def test_http_client_creation(self):
        """测试HTTP客户端创建"""
        from core.communication.http_client import HTTPClient
        
        http = HTTPClient()
        self.assertEqual(http.protocol_name, "HTTPClient")
        
        logger.info("✅ HTTP客户端创建测试通过")
    
    def test_http_client_connect(self):
        """测试HTTP客户端初始化"""
        from core.communication.http_client import HTTPClient
        
        http = HTTPClient()
        
        result = http.connect({
            "base_url": "https://httpbin.org",
            "timeout": 10
        })
        
        self.assertTrue(result)
        self.assertEqual(http.state, ConnectionState.CONNECTED)
        
        http.disconnect()
        
        logger.info("✅ HTTP客户端初始化测试通过")
    
    def test_http_client_get(self):
        """测试HTTP GET请求"""
        from core.communication.http_client import HTTPClient
        
        http = HTTPClient()
        http.connect({"base_url": "https://httpbin.org", "timeout": 10})
        
        response = http.get("/get", params={"key": "value"})
        
        self.assertTrue(response["success"])
        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["data"]["args"], {"key": "value"})
        
        http.disconnect()
        
        logger.info("✅ HTTP GET请求测试通过")
    
    def test_http_client_post(self):
        """测试HTTP POST请求"""
        from core.communication.http_client import HTTPClient
        
        http = HTTPClient()
        http.connect({"base_url": "https://httpbin.org", "timeout": 10})
        
        response = http.post("/post", json={"name": "test"})
        
        self.assertTrue(response["success"])
        self.assertEqual(response["status_code"], 200)
        
        http.disconnect()
        
        logger.info("✅ HTTP POST请求测试通过")


class TestProtocolManager(unittest.TestCase):
    """测试协议管理器"""
    
    def test_protocol_manager_creation(self):
        """测试协议管理器创建"""
        from core.communication.protocol_manager import ProtocolManager
        
        manager = ProtocolManager()
        
        protocols = manager.get_protocols()
        self.assertEqual(len(protocols), 0)
        
        logger.info("✅ 协议管理器创建测试通过")
    
    def test_protocol_manager_create(self):
        """测试协议管理器创建协议"""
        from core.communication.protocol_manager import ProtocolManager, ProtocolType
        
        manager = ProtocolManager()
        
        tcp = manager.create_protocol(ProtocolType.TCP_CLIENT, "test_tcp")
        self.assertIsNotNone(tcp)
        
        protocols = manager.get_protocols()
        self.assertEqual(len(protocols), 1)
        
        manager.remove_all()
        
        logger.info("✅ 协议管理器创建协议测试通过")
    
    def test_protocol_manager_stats(self):
        """测试协议管理器统计"""
        from core.communication.protocol_manager import ProtocolManager, ProtocolType
        
        manager = ProtocolManager()
        
        manager.create_protocol(ProtocolType.TCP_CLIENT, "tcp1")
        manager.create_protocol(ProtocolType.SERIAL, "serial1")
        
        stats = manager.get_connection_stats()
        
        self.assertEqual(len(stats), 2)
        self.assertIn("tcp1", stats)
        self.assertIn("serial1", stats)
        
        manager.remove_all()
        
        logger.info("✅ 协议管理器统计测试通过")
    
    def test_protocol_builder(self):
        """测试协议构建器"""
        from core.communication.protocol_manager import ProtocolBuilder, ProtocolManager
        
        manager = ProtocolManager()
        builder = ProtocolBuilder()
        
        tcp = (builder
               .tcp_client("builder_test")
               .host("127.0.0.1")
               .port(8080)
               .timeout(10)
               .build(manager))
        
        self.assertIsNotNone(tcp)
        
        manager.remove_all()
        
        logger.info("✅ 协议构建器测试通过")


def run_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始通讯模块测试")
    logger.info("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestProtocolBase))
    suite.addTests(loader.loadTestsFromTestCase(TestDataParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTCPClient))
    suite.addTests(loader.loadTestsFromTestCase(TestTCPServer))
    suite.addTests(loader.loadTestsFromTestCase(TestSerialPort))
    suite.addTests(loader.loadTestsFromTestCase(TestHTTPClient))
    suite.addTests(loader.loadTestsFromTestCase(TestProtocolManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info("=" * 60)
    if result.wasSuccessful():
        logger.info("所有测试通过!")
    else:
        logger.error(f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误")
    logger.info("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
