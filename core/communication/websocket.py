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
        self._reconnect_timer: Optional[threading.Timer] = None  # 重连定时器

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
        logger.info("[WebSocketClient] 开始断开连接...")
        
        self._running = False
        self._auto_reconnect = False
        logger.info("[WebSocketClient] 设置_running=False")

        # 停止重连定时器
        if self._reconnect_timer:
            try:
                self._reconnect_timer.cancel()
            except Exception:
                pass
            self._reconnect_timer = None
            logger.info("[WebSocketClient] 重连定时器已停止")

        self._stop_heartbeat()
        logger.info("[WebSocketClient] 心跳已停止")

        if self._ws:
            logger.info("[WebSocketClient] 关闭WebSocket连接...")
            try:
                self._ws.close()
            except Exception as e:
                logger.debug(f"[WebSocketClient] 关闭连接时发生异常: {e}")
            self._ws = None
            logger.info("[WebSocketClient] WebSocket连接已关闭")

        if self._thread and self._thread.is_alive():
            logger.info("[WebSocketClient] 等待接收线程结束...")
            self._thread.join(timeout=1.0)
            self._thread = None
            logger.info("[WebSocketClient] 接收线程已清理")

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            logger.info("[WebSocketClient] 等待心跳线程结束...")
            self._heartbeat_thread.join(timeout=1.0)
            self._heartbeat_thread = None
            logger.info("[WebSocketClient] 心跳线程已清理")

        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_disconnect")
        self._emit = lambda *args, **kwargs: None  # 断开回调引用
        self.clear_callbacks()
        logger.info("[WebSocketClient] 回调已清除")
        logger.info("[WebSocketClient] 断开连接完成")

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
            logger.error(f"[WebSocketClient] 发送失败: {e}")
            return False

    def receive(self, timeout: float = None) -> Any:
        """接收数据

        Args:
            timeout: 超时时间（秒）

        Returns:
            接收到的数据
        """
        # WebSocket使用回调方式接收数据，此方法返回None
        return None

    def _receive_loop(self):
        """接收数据循环"""
        while self._running:
            try:
                if not self._ws:
                    break

                # 接收数据
                opcode, data = self._ws.recv_data()

                if opcode == websocket.ABNF.OPCODE_TEXT:
                    self._emit("on_message", data.decode("utf-8"))
                elif opcode == websocket.ABNF.OPCODE_BINARY:
                    self._emit("on_message", data)
                elif opcode == websocket.ABNF.OPCODE_PING:
                    self._ws.pong(data)
                elif opcode == websocket.ABNF.OPCODE_CLOSE:
                    break

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"[WebSocketClient] 接收异常: {e}")
                break

        # 使用定时器进行异步重连，避免在接收线程中阻塞
        if self._running and self._auto_reconnect:
            logger.info(
                f"[WebSocketClient] {self._reconnect_interval}秒后自动重连..."
            )
            self._reconnect_timer = threading.Timer(
                self._reconnect_interval, 
                self._do_reconnect
            )
            self._reconnect_timer.daemon = True
            self._reconnect_timer.start()
        else:
            self.set_state(ConnectionState.DISCONNECTED)
            self._emit("on_disconnect")

    def _do_reconnect(self):
        """执行重连（在独立线程中）"""
        if self._running and self._auto_reconnect:
            logger.info("[WebSocketClient] 开始自动重连...")
            try:
                self.connect(self._config)
            except Exception as e:
                logger.error(f"[WebSocketClient] 自动重连失败: {e}")

    def _start_heartbeat(self):
        """启动心跳"""
        self._stop_heartbeat()

        def heartbeat_loop():
            while self._running:
                try:
                    time.sleep(self._heartbeat_interval)
                    if self._running and self.is_connected() and self._ws:
                        try:
                            self._ws.ping()
                        except Exception as e:
                            logger.warning(f"[WebSocketClient] 心跳发送失败: {e}")
                            break
                except Exception as e:
                    logger.error(f"[WebSocketClient] 心跳循环异常: {e}")
                    break

        self._heartbeat_thread = threading.Thread(
            target=heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _stop_heartbeat(self):
        """停止心跳"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            # 等待心跳线程结束
            self._heartbeat_thread.join(timeout=1.0)
            self._heartbeat_thread = None


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO)

    ws = WebSocketClient()
    ws.register_callback(
        "on_message", lambda data: print(f"收到消息: {data}")
    )
    ws.register_callback("on_connect", lambda: print("已连接"))
    ws.register_callback("on_disconnect", lambda: print("已断开"))

    if ws.connect({"url": "ws://echo.websocket.org/"}):
        print("连接成功，发送测试消息...")
        ws.send("Hello WebSocket!")

        try:
            time.sleep(5)
        except KeyboardInterrupt:
            pass
        finally:
            ws.disconnect()
