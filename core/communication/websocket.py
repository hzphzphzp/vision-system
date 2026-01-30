#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket通讯模块

实现WebSocket客户端功能，支持与WebSocket服务端进行实时双向通讯。

功能特性:
- WS/WSS加密支持
- 自动重连机制
- 心跳检测
- 二进制/文本数据

Usage:
    from core.communication import WebSocketClient

    ws = WebSocketClient()
    ws.register_callback("on_message", lambda data: print(f"收到: {data}"))

    if ws.connect({"url": "ws://localhost:8080/ws"}):
        ws.send("Hello")
        ws.disconnect()
"""

import logging
import os
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional, Union

import websocket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import ConnectionState, ProtocolBase

logger = logging.getLogger("WebSocketClient")


class WebSocketClient(ProtocolBase):
    """WebSocket客户端类

    提供WebSocket客户端功能，用于与WebSocket服务端进行实时双向通讯。
    """

    protocol_name = "WebSocketClient"

    def __init__(self):
        super().__init__()
        self._ws: Optional[websocket.WebSocket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._auto_reconnect = False
        self._reconnect_interval = 5.0
        self._heartbeat_interval = 30
        self._heartbeat_thread: Optional[threading.Thread] = None

    def connect(self, config: Dict[str, Any]) -> bool:
        """连接到WebSocket服务端

        Args:
            config: 连接配置
                - url: WebSocket地址（ws://或wss://）
                - header: 请求头字典
                - timeout: 连接超时（秒）
                - auto_reconnect: 是否自动重连
                - reconnect_interval: 重连间隔（秒）
                - heartbeat: 是否启用心跳
                - heartbeat_interval: 心跳间隔（秒）

        Returns:
            bool: 连接是否成功
        """
        if self._state == ConnectionState.CONNECTED:
            logger.warning("[WebSocketClient] 已连接")
            return True

        url = config.get("url", "ws://localhost:8080")
        header = config.get("header", {})
        timeout = config.get("timeout", 10)
        self._auto_reconnect = config.get("auto_reconnect", False)
        self._reconnect_interval = config.get("reconnect_interval", 5.0)
        heartbeat = config.get("heartbeat", False)
        self._heartbeat_interval = config.get("heartbeat_interval", 30)

        self._config = config
        self.set_state(ConnectionState.CONNECTING)

        try:
            self._ws = websocket.WebSocket(
                url, header=header, enable_multithread=True
            )

            self._ws.settimeout(timeout)
            result = self._ws.connect(url, header=header)

            self._running = True
            self._thread = threading.Thread(
                target=self._receive_loop, daemon=True
            )
            self._thread.start()

            if heartbeat:
                self._start_heartbeat()

            self.set_state(ConnectionState.CONNECTED)
            self._emit("on_connect")
            logger.info(f"[WebSocketClient] 成功连接到 {url}")
            return True

        except Exception as e:
            self.set_state(ConnectionState.ERROR)
            logger.error(f"[WebSocketClient] 连接失败: {e}")
            self._emit("on_error", str(e))
            return False

    def disconnect(self):
        """断开连接"""
        self._running = False
        self._auto_reconnect = False

        self._stop_heartbeat()

        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                logger.debug(f"[WebSocketClient] 关闭连接时发生异常: {e}")
            self._ws = None

        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_disconnect")
        logger.info("[WebSocketClient] 已断开连接")

    def send(self, data: Union[str, bytes]) -> bool:
        """发送数据

        Args:
            data: 要发送的数据（文本或二进制）

        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected() or not self._ws:
            logger.warning("[WebSocketClient] 未连接，无法发送")
            return False

        try:
            if isinstance(data, str):
                self._ws.send(data, websocket.ABNF.OPCODE_TEXT)
            else:
                self._ws.send(data, websocket.ABNF.OPCODE_BINARY)
            return True

        except Exception as e:
            logger.error(f"[WebSocketClient] 发送数据失败: {e}")
            self._emit("on_error", str(e))
            return False

    def send_json(self, data: Dict) -> bool:
        """发送JSON数据

        Args:
            data: 要发送的字典数据

        Returns:
            bool: 发送是否成功
        """
        import json

        return self.send(json.dumps(data, ensure_ascii=False))

    def receive(self, timeout: float = None) -> Any:
        """接收数据（阻塞模式）"""
        if not self.is_connected() or not self._ws:
            return None

        try:
            self._ws.settimeout(timeout)
            opcode, data = self._ws.recv_data()
            if opcode == websocket.ABNF.OPCODE_TEXT:
                return data.decode("utf-8")
            else:
                return data
        except Exception as e:
            logger.debug(f"[WebSocketClient] 接收数据失败: {e}")
            return None

    def ping(self, message: bytes = b"ping") -> bool:
        """发送ping"""
        if self._ws:
            try:
                self._ws.ping(message)
                return True
            except:
                pass
        return False

    def pong(self, message: bytes = b"pong") -> bool:
        """发送pong"""
        if self._ws:
            try:
                self._ws.pong(message)
                return True
            except:
                pass
        return False

    def _receive_loop(self):
        """接收数据循环"""
        while self._running:
            try:
                opcode, data = self._ws.recv_data()

                if not self._running:
                    break

                if opcode == websocket.ABNF.OPCODE_TEXT:
                    self._emit("on_message", data.decode("utf-8"))
                elif opcode == websocket.ABNF.OPCODE_BINARY:
                    self._emit("on_binary", data)
                elif opcode == websocket.ABNF.OPCODE_PING:
                    self._ws.pong()
                elif opcode == websocket.ABNF.OPCODE_PONG:
                    self._emit("on_pong")

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"[WebSocketClient] 接收异常: {e}")
                break

        if self._running and self._auto_reconnect:
            logger.info(
                f"[WebSocketClient] {self._reconnect_interval}秒后自动重连..."
            )
            time.sleep(self._reconnect_interval)
            self.connect(self._config)
        else:
            self.set_state(ConnectionState.DISCONNECTED)
            self._emit("on_disconnect")

    def _start_heartbeat(self):
        """启动心跳"""
        self._stop_heartbeat()

        def heartbeat_loop():
            while self._running:
                time.sleep(self._heartbeat_interval)
                if self._running and self.is_connected():
                    try:
                        self._ws.ping()
                    except:
                        break

        self._heartbeat_thread = threading.Thread(
            target=heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self):
        """停止心跳"""
        self._heartbeat_thread = None


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    ws = WebSocketClient()
    ws.register_callback("on_message", lambda data: print(f"收到: {data}"))
    ws.register_callback("on_connect", lambda: print("连接成功"))
    ws.register_callback("on_disconnect", lambda: print("连接断开"))

    config = {
        "url": "ws://localhost:8080",
        "auto_reconnect": False,
        "heartbeat": True,
        "heartbeat_interval": 30,
    }

    if ws.connect(config):
        ws.send("Hello WebSocket!")
        ws.send_json({"type": "test", "data": "Hello"})

        import time

        time.sleep(5)

        ws.disconnect()
