#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP客户端模块（线程安全版本）

实现TCP客户端功能，支持连接到TCP服务端进行数据收发。

Author: Vision System Team
Date: 2026-01-13
"""

import logging
import os
import queue
import select
import socket
import sys
import threading
import time
import uuid
import zlib
from typing import Any, Dict, Optional, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import (
    ConnectionState,
    DataParser,
    ProtocolBase,
)

logger = logging.getLogger("TCPClient")


class SendRequest:
    """发送请求类"""

    def __init__(self, data, callback=None, timeout=None, max_retry=None):
        self.data = data
        self.callback = callback
        self.timeout = timeout
        self.max_retry = max_retry
        self.id = str(uuid.uuid4())
        self.start_time = time.time()
        self.end_time = None
        self.status = "pending"  # pending, sending, success, failed
        self.retry_count = 0
        self.error = None


class TCPClient(ProtocolBase):
    """TCP客户端类"""

    protocol_name = "TCPClient"

    def __init__(self):
        super().__init__()
        self._socket: Optional[socket.socket] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._send_thread: Optional[threading.Thread] = None  # 新增发送线程
        self._running = False
        self._auto_reconnect = False
        self._reconnect_interval = 5.0
        self._parser: DataParser = DataParser()
        self._lock = threading.Lock()
        self._receive_queue = queue.Queue()
        self._send_queue = queue.Queue()  # 新增发送队列
        self._statistics = {
            "send_count": 0,
            "send_success": 0,
            "send_failure": 0,
            "send_retry": 0,
            "send_bytes": 0,
            "send_time": 0,
            "last_send_time": 0,
            "avg_send_time": 0,
        }  # 新增统计信息
        self._config = {
            "max_retry": 3,  # 最大重试次数
            "retry_interval": 0.5,  # 重试间隔
            "send_buffer_size": 8192,  # 发送缓冲区大小
            "send_timeout": 5.0,  # 发送超时
            "queue_size": 1000,  # 队列大小
            "compression": False,  # 是否启用压缩
            "encryption": False,  # 是否启用加密
            "health_check_interval": 30.0,  # 健康检查间隔
        }  # 新增配置
        self._health_check_timer: Optional[threading.Timer] = (
            None  # 新增健康检查定时器
        )
        self._last_health_check = 0  # 上次健康检查时间

    def connect(self, config: Dict[str, Any]) -> bool:
        """连接到TCP服务端"""
        logger.info(f"[TCPClient] 开始连接... config={config}")
        
        if self._state == ConnectionState.CONNECTED:
            logger.info("[TCPClient] 已经是连接状态")
            return True

        host = config.get("host", "127.0.0.1")
        port = config.get("port", 8080)
        timeout = config.get("timeout", 10.0)
        self._auto_reconnect = config.get("auto_reconnect", False)
        self._reconnect_interval = config.get("reconnect_interval", 5.0)
        self._parser = config.get("parser", DataParser())

        # 更新配置
        self._config.update(config)
        self._config["host"] = host
        self._config["port"] = port
        self._config["timeout"] = timeout

        self._config = config
        self.set_state(ConnectionState.CONNECTING)
        logger.info(f"[TCPClient] 状态设为CONNECTING")

        try:
            logger.info(f"[TCPClient] 创建socket...")
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)

            # 启用TCP保活
            if self._config.get("keep_alive", True):
                self._socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1
                )
                if hasattr(socket, "TCP_KEEPIDLE"):
                    self._socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60
                    )
                    self._socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10
                    )
                    self._socket.setsockopt(
                        socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3
                    )

            # 启用TCP_NODELAY
            if self._config.get("tcp_nodelay", True):
                self._socket.setsockopt(
                    socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
                )

            logger.info(f"[TCPClient] 正在连接到 {host}:{port}...")
            
            # 使用非阻塞连接避免阻塞主线程
            self._socket.setblocking(False)
            try:
                self._socket.connect((host, port))
            except BlockingIOError:
                # 非阻塞连接会立即返回，需要等待连接完成
                logger.info(f"[TCPClient] 非阻塞连接进行中，等待连接完成...")
                ready = select.select([], [self._socket], [], timeout)
                if ready[1]:
                    # 检查连接是否成功
                    err = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if err != 0:
                        raise OSError(err, f"连接失败: {os.strerror(err)}")
                    logger.info(f"[TCPClient] 非阻塞连接成功")
                else:
                    raise TimeoutError(f"连接超时 ({timeout}秒)")
            
            logger.info(f"[TCPClient] 连接成功，设置非阻塞模式")
            self._socket.settimeout(0.1)

            self._running = True
            logger.info("[TCPClient] 启动接收线程...")
            self._receive_thread = threading.Thread(
                target=self._receive_loop, daemon=True
            )
            self._receive_thread.start()

            # 启动发送线程
            logger.info("[TCPClient] 启动发送线程...")
            self._send_thread = threading.Thread(
                target=self._send_loop, daemon=True
            )
            self._send_thread.start()

            # 启动健康检查
            logger.info("[TCPClient] 启动健康检查...")
            self._start_health_check()

            self.set_state(ConnectionState.CONNECTED)
            self._emit("on_connect")
            logger.info(f"[TCPClient] 连接完成，成功连接到 {host}:{port}")
            return True

        except Exception as e:
            logger.error(f"[TCPClient] 连接失败: {e}")
            self.set_state(ConnectionState.ERROR)
            self._emit("on_error", str(e))
            return False

    def disconnect(self):
        """断开连接（非阻塞版本）"""
        logger.info("[TCPClient] 开始断开连接...")

        with self._lock:
            if not self._running:
                logger.info("[TCPClient] 已经在断开状态")
                return

            self._running = False
            logger.info("[TCPClient] 设置_running=False")

            sock = self._socket
            self._socket = None
            logger.info("[TCPClient] 已清除socket引用")

        # 停止健康检查
        self._stop_health_check()
        logger.info("[TCPClient] 已停止健康检查")

        # 关闭socket（在锁外执行，避免阻塞）
        if sock:
            try:
                logger.info("[TCPClient] 关闭socket...")
                # 先设置非阻塞模式，避免shutdown阻塞
                sock.setblocking(False)
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
            logger.info("[TCPClient] socket已关闭")

        # 向发送队列放入一个None信号，唤醒发送线程
        try:
            self._send_queue.put_nowait(None)
        except queue.Full:
            pass

        # 清理队列（不阻塞）
        self._clear_queues()

        # 异步等待线程结束（不阻塞主线程）
        self._cleanup_threads_async()

        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_disconnect")
        self._emit = lambda *args, **kwargs: None  # 断开回调引用
        self.clear_callbacks()
        logger.info("[TCPClient] 断开连接完成")

    def _clear_queues(self):
        """清空队列（非阻塞）"""
        # 清理发送队列
        send_queue_size = self._send_queue.qsize()
        cleared_send = 0
        while not self._send_queue.empty():
            try:
                self._send_queue.get_nowait()
                cleared_send += 1
            except queue.Empty:
                break
        if cleared_send > 0:
            logger.info(f"[TCPClient] 已清空发送队列 ({cleared_send}项)")

        # 清理接收队列
        recv_queue_size = self._receive_queue.qsize()
        cleared_recv = 0
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
                cleared_recv += 1
            except queue.Empty:
                break
        if cleared_recv > 0:
            logger.info(f"[TCPClient] 已清空接收队列 ({cleared_recv}项)")

    def _cleanup_threads_async(self):
        """异步清理线程（不阻塞）"""
        def cleanup():
            # 等待接收线程结束
            if self._receive_thread and self._receive_thread.is_alive():
                self._receive_thread.join(timeout=0.5)
                if self._receive_thread.is_alive():
                    logger.warning("[TCPClient] 接收线程未能及时结束")
                self._receive_thread = None

            # 等待发送线程结束
            if self._send_thread and self._send_thread.is_alive():
                self._send_thread.join(timeout=0.5)
                if self._send_thread.is_alive():
                    logger.warning("[TCPClient] 发送线程未能及时结束")
                self._send_thread = None

            logger.info("[TCPClient] 线程清理完成")

        # 启动后台线程进行清理
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()

    def send(self, data: Union[str, bytes, dict]) -> bool:
        """发送数据"""
        if not self.is_connected():
            return False

        request = SendRequest(data)
        try:
            self._send_queue.put(request, timeout=1.0)
            return True
        except queue.Full:
            logger.error("[TCPClient] 发送队列已满")
            return False

    def send_with_callback(
        self,
        data: Union[str, bytes, dict],
        callback=None,
        timeout=None,
        max_retry=None,
    ) -> str:
        """发送数据并设置回调"""
        if not self.is_connected():
            if callback:
                callback(None, "Not connected")
            return None

        request = SendRequest(data, callback, timeout, max_retry)
        try:
            self._send_queue.put(request, timeout=1.0)
            return request.id
        except queue.Full:
            logger.error("[TCPClient] 发送队列已满")
            if callback:
                callback(None, "Send queue full")
            return None

    def receive(self, timeout: float = None) -> Any:
        """从队列中接收数据"""
        try:
            return self._receive_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _send_loop(self):
        """发送数据循环"""
        while self._running:
            try:
                request = self._send_queue.get(timeout=0.05)  # 减少超时时间，更快响应
                
                # 检查退出信号
                if request is None:
                    logger.debug("[TCPClient] 发送线程收到退出信号")
                    break
                
                if not self._running:
                    break

                self._process_send_request(request)

            except queue.Empty:
                # 队列为空，继续循环检查_running状态
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"[TCPClient] 发送循环异常: {e}")
                break
        logger.debug("[TCPClient] 发送线程已退出")

    def _process_send_request(self, request: SendRequest):
        """处理发送请求"""
        if not self.is_connected() or not self._socket:
            request.status = "failed"
            request.error = "Not connected"
            if request.callback:
                request.callback(None, "Not connected")
            return

        request.status = "sending"
        max_retry = request.max_retry or self._config.get("max_retry", 3)
        retry_interval = self._config.get("retry_interval", 0.5)

        while request.retry_count <= max_retry:
            try:
                # 准备数据
                data = request.data
                if isinstance(data, dict):
                    data = self._parser.format(data)
                elif isinstance(data, str):
                    data = data.encode("utf-8")

                # 压缩数据
                if self._config.get("compression", False) and len(data) > 1024:
                    compressed_data = zlib.compress(data)
                    if len(compressed_data) < len(data):
                        data = compressed_data

                # 记录发送开始时间
                start_time = time.time()

                # 发送数据
                with self._lock:
                    if not self.is_connected() or not self._socket:
                        request.status = "failed"
                        request.error = "Not connected"
                        if request.callback:
                            request.callback(None, "Not connected")
                        return

                    self._socket.settimeout(
                        self._config.get("send_timeout", 5.0)
                    )
                    self._socket.sendall(data)

                # 记录发送结束时间
                end_time = time.time()
                time_used = end_time - start_time

                # 更新统计信息
                with self._lock:
                    self._statistics["send_count"] += 1
                    self._statistics["send_success"] += 1
                    self._statistics["send_bytes"] += len(data)
                    self._statistics["send_time"] += time_used
                    self._statistics["last_send_time"] = end_time
                    self._statistics["avg_send_time"] = (
                        self._statistics["send_time"]
                        / self._statistics["send_count"]
                    )

                # 更新请求状态
                request.status = "success"
                request.end_time = end_time

                # 触发回调
                if request.callback:
                    request.callback(request.id, None)

                # 触发事件
                self._emit("on_send_success", request.id, len(data), time_used)

                break

            except Exception as e:
                request.retry_count += 1
                with self._lock:
                    self._statistics["send_retry"] += 1

                if request.retry_count > max_retry:
                    request.status = "failed"
                    request.error = str(e)
                    with self._lock:
                        self._statistics["send_failure"] += 1

                    if request.callback:
                        request.callback(None, str(e))

                    # 触发事件
                    self._emit("on_send_failure", request.id, str(e))

                    logger.error(f"[TCPClient] 发送数据失败: {e}")
                    break

                # 重试间隔
                time.sleep(retry_interval)

    def _receive_loop(self):
        """接收数据循环 - 使用select避免阻塞"""
        while self._running:
            try:
                # 检查socket是否存在
                if self._socket is None:
                    break
                
                # 使用select检查socket是否可读，设置较短的超时时间
                ready, _, _ = select.select([self._socket], [], [], 0.05)
                if not ready:
                    # 没有数据可读，继续循环检查_running状态
                    continue
                
                # 现在安全地recv，因为select已经确认有数据
                try:
                    data = self._socket.recv(4096)
                except (socket.error, OSError):
                    # socket可能已关闭
                    break
                    
                if not data:
                    # 连接已关闭
                    break

                if self._running:
                    try:
                        self._receive_queue.put_nowait(data)
                        # 触发事件
                        self._emit("on_receive", data)
                    except queue.Full:
                        logger.warning("[TCPClient] 接收队列已满，丢弃数据")

            except socket.timeout:
                continue
            except OSError:
                # socket已关闭
                break
            except Exception as e:
                if self._running:
                    logger.debug(f"[TCPClient] 接收异常: {e}")
                break
        
        logger.debug("[TCPClient] 接收线程已退出")
        
        # 只有在正常运行状态下才触发重连
        if self._running and self._auto_reconnect:
            threading.Timer(self._reconnect_interval, self._reconnect).start()

    def _reconnect(self):
        """自动重连"""
        if self._auto_reconnect and self._config:
            logger.info("[TCPClient] 尝试重连...")
            self.connect(self._config)

    def _start_health_check(self):
        """启动健康检查"""
        self._stop_health_check()
        interval = self._config.get("health_check_interval", 30.0)
        self._health_check_timer = threading.Timer(
            interval, self._health_check
        )
        self._health_check_timer.daemon = True
        self._health_check_timer.start()

    def _stop_health_check(self):
        """停止健康检查"""
        if self._health_check_timer:
            try:
                self._health_check_timer.cancel()
            except Exception:
                pass
            self._health_check_timer = None

    def _health_check(self):
        """健康检查"""
        if not self._running:
            return

        try:
            # 发送心跳包
            if self.is_connected() and self._socket:
                # 发送一个空包进行心跳检测
                with self._lock:
                    if self.is_connected() and self._socket:
                        try:
                            self._socket.send(b"")
                        except Exception as e:
                            logger.warning(f"[TCPClient] 健康检查发送失败: {e}")
                            # 连接可能已断开，不再继续健康检查
                            return

            self._last_health_check = time.time()
            self._emit("on_health_check")

        except Exception as e:
            logger.error(f"[TCPClient] 健康检查失败: {e}")
        finally:
            # 重新启动健康检查
            if self._running:
                self._start_health_check()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return self._statistics.copy()

    def reset_statistics(self):
        """重置统计信息"""
        with self._lock:
            self._statistics = {
                "send_count": 0,
                "send_success": 0,
                "send_failure": 0,
                "send_retry": 0,
                "send_bytes": 0,
                "send_time": 0,
                "last_send_time": 0,
                "avg_send_time": 0,
            }

    def get_queue_size(self) -> int:
        """获取发送队列大小"""
        return self._send_queue.qsize()

    def clear_queue(self):
        """清空发送队列"""
        cleared = 0
        while not self._send_queue.empty():
            try:
                self._send_queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        if cleared > 0:
            logger.info(f"[TCPClient] 已清空发送队列 ({cleared}项)")


if __name__ == "__main__":
    import json
    import time

    logging.basicConfig(level=logging.INFO)

    client = TCPClient()

    config = {"host": "127.0.0.1", "port": 8888, "timeout": 5.0}

    if client.connect(config):
        client.send("Hello TCP Server!")

        for i in range(5):
            data = client.receive(timeout=1.0)
            if data:
                logger.info(f"收到: {data}")
            else:
                logger.info("等待数据...")

        client.disconnect()
