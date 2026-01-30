#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP服务端模块（线程安全版本）

实现TCP服务端功能，支持多客户端连接管理。

Author: Vision System Team
Date: 2026-01-13
"""

import concurrent.futures
import logging
import os
import queue
import socket
import sys
import threading
import time
import uuid
from typing import Any, Dict, Optional, Tuple, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import (
    ConnectionState,
    DataParser,
    ProtocolBase,
)

logger = logging.getLogger("TCPServer")


class ClientInfo:
    """客户端信息类"""

    def __init__(self, client_id, client_socket, addr):
        self.client_id = client_id
        self.socket = client_socket
        self.addr = addr
        self.connected_time = time.time()
        self.last_activity = time.time()
        self.send_count = 0
        self.receive_count = 0
        self.error_count = 0
        self.buffer = b""
        self.status = "connected"  # connected, inactive, error
        self.thread = None
        self.queue = queue.Queue()


class TCPServer(ProtocolBase):
    """TCP服务端类"""

    protocol_name = "TCPServer"

    def __init__(self):
        super().__init__()
        self._server_socket: Optional[socket.socket] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._running = False
        self._clients: Dict[str, ClientInfo] = {}  # 客户端信息
        self._clients_lock = threading.Lock()
        self._parser: DataParser = DataParser()
        self._receive_queues: Dict[str, queue.Queue] = {}  # 接收队列
        self._thread_pool: Optional[concurrent.futures.ThreadPoolExecutor] = (
            None  # 线程池
        )
        self._config = {
            "max_connections": 1000,  # 最大连接数
            "thread_pool_size": 10,  # 线程池大小
            "receive_buffer_size": 4096,  # 接收缓冲区大小
            "heartbeat_interval": 30.0,  # 心跳间隔
            "connection_timeout": 60.0,  # 连接超时
            "queue_size": 1000,  # 队列大小
            "ipv6": False,  # 是否启用IPv6
            "backlog": 100,  # 连接队列大小
            "buffer_timeout": 5.0,  # 缓冲区超时
        }  # 配置
        self._statistics = {
            "total_connections": 0,  # 总连接数
            "current_connections": 0,  # 当前连接数
            "max_connections": 0,  # 最大连接数
            "total_received": 0,  # 总接收数据量
            "total_sent": 0,  # 总发送数据量
            "error_count": 0,  # 错误次数
            "start_time": time.time(),  # 启动时间
        }  # 统计信息
        self._heartbeat_timer: Optional[threading.Timer] = None  # 心跳定时器
        self._shutdown_event = threading.Event()  # 关闭事件

    def listen(self, config: Dict[str, Any]) -> bool:
        """开始监听

        Args:
            config: 监听配置
                - host: 监听地址（默认0.0.0.0）
                - port: 监听端口
                - backlog: 连接队列大小
                - parser: 数据解析器（可选）

        Returns:
            bool: 是否成功开始监听
        """
        host = config.get("host", "0.0.0.0")
        port = config.get("port", 8080)
        backlog = config.get("backlog", 5)
        self._parser = config.get("parser", DataParser())

        # 更新配置
        self._config.update(config)
        self._config["host"] = host
        self._config["port"] = port
        self._config["backlog"] = backlog

        self._config = config
        self.set_state(ConnectionState.CONNECTING)

        try:
            # 支持IPv6
            if self._config.get("ipv6", False):
                self._server_socket = socket.socket(
                    socket.AF_INET6, socket.SOCK_STREAM
                )
                self._server_socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0
                )
            else:
                self._server_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM
                )

            self._server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self._server_socket.bind((host, port))
            self._server_socket.listen(backlog)
            self._server_socket.settimeout(0.5)

            # 创建线程池
            self._thread_pool = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._config.get("thread_pool_size", 10)
            )

            self._running = True
            self._listen_thread = threading.Thread(
                target=self._accept_loop, daemon=True
            )
            self._listen_thread.start()

            # 启动心跳
            self._start_heartbeat()

            self.set_state(ConnectionState.CONNECTED)
            logger.info(f"[TCPServer] 开始监听 {host}:{port}")
            self._emit("on_listen")
            return True

        except Exception as e:
            self.set_state(ConnectionState.ERROR)
            logger.error(f"[TCPServer] 监听失败: {e}")
            self._emit("on_error", str(e))
            return False

    def stop(self):
        """停止监听"""
        with self._clients_lock:
            if not self._running:
                return

            self._running = False

        # 停止心跳
        self._stop_heartbeat()

        # 优雅关闭客户端连接
        for client_id in list(self._clients.keys()):
            self._remove_client(client_id, graceful=True)

        # 关闭线程池
        if self._thread_pool:
            self._thread_pool.shutdown(wait=False)

        # 关闭服务器 socket
        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass
            self._server_socket = None

        # 等待监听线程结束
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)

        # 清理资源
        self._receive_queues.clear()
        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_stop")
        logger.info("[TCPServer] 已停止监听")

    def disconnect(self):
        """断开连接（别名）"""
        self.stop()

    def broadcast(self, data: Union[str, bytes, dict]) -> int:
        """广播消息到所有客户端

        Args:
            data: 要发送的数据

        Returns:
            int: 成功发送的客户端数量
        """
        success = 0
        for client_id in list(self._clients.keys()):
            if self.send_to(client_id, data):
                success += 1
        return success

    def send_to(self, client_id: Any, data: Union[str, bytes, dict]) -> bool:
        """发送消息到指定客户端"""
        try:
            # 准备数据
            if isinstance(data, dict):
                data = self._parser.format(data)
            elif isinstance(data, str):
                data = data.encode("utf-8")

            with self._clients_lock:
                if client_id not in self._clients:
                    return False

                client_info = self._clients[client_id]
                client_socket = client_info.socket
                if not client_socket:
                    return False

                # 发送数据
                client_socket.sendall(data)

                # 更新客户端信息
                client_info.send_count += 1
                client_info.last_activity = time.time()

                # 更新统计信息
                self._statistics["total_sent"] += len(data)

                return True

        except Exception as e:
            logger.error(f"[TCPServer] 发送失败: {e}")
            self._remove_client(client_id)
            return False

    def receive(
        self, timeout: float = None
    ) -> Tuple[Optional[str], Optional[Any]]:
        """不支持此方法"""
        logger.warning("[TCPServer] 请使用receive_from获取指定客户端数据")
        return None, None

    def receive_from(
        self, client_id: str = None, timeout: float = 0.1
    ) -> Tuple[Optional[str], Optional[Any]]:
        """从指定客户端接收数据

        Args:
            client_id: 客户端ID，为None则从任意客户端接收
            timeout: 超时时间

        Returns:
            Tuple[客户端ID, 数据]
        """
        if client_id:
            if client_id in self._receive_queues:
                try:
                    data = self._receive_queues[client_id].get(timeout=timeout)
                    # 使用解析器解析数据
                    parsed_data = self._parser.parse(data)
                    return client_id, parsed_data
                except queue.Empty:
                    return None, None
            return None, None

        with self._clients_lock:
            client_ids = list(self._receive_queues.keys())

        for cid in client_ids:
            if cid in self._receive_queues:
                try:
                    data = self._receive_queues[cid].get(timeout=0.01)
                    # 使用解析器解析数据
                    parsed_data = self._parser.parse(data)
                    return cid, parsed_data
                except queue.Empty:
                    continue

        return None, None

    def get_connected_clients(self) -> list:
        """获取已连接的客户端列表"""
        with self._clients_lock:
            return list(self._clients.keys())

    def get_client_info(self, client_id: str) -> Optional[ClientInfo]:
        """获取客户端信息"""
        with self._clients_lock:
            return self._clients.get(client_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._clients_lock:
            stats = self._statistics.copy()
            stats["current_connections"] = len(self._clients)
            return stats

    def reset_statistics(self):
        """重置统计信息"""
        with self._clients_lock:
            self._statistics = {
                "total_connections": 0,
                "current_connections": len(self._clients),
                "max_connections": self._statistics["max_connections"],
                "total_received": 0,
                "total_sent": 0,
                "error_count": 0,
                "start_time": time.time(),
            }

    def set_max_connections(self, max_connections: int):
        """设置最大连接数"""
        self._config["max_connections"] = max_connections

    def set_thread_pool_size(self, size: int):
        """设置线程池大小"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=False)
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=size
        )
        self._config["thread_pool_size"] = size

    def _accept_loop(self):
        """接受连接循环"""
        while self._running:
            try:
                # 检查连接数是否超过限制
                with self._clients_lock:
                    if len(self._clients) >= self._config.get(
                        "max_connections", 1000
                    ):
                        time.sleep(0.1)
                        continue

                client_socket, addr = self._server_socket.accept()
                client_socket.settimeout(0.1)
                client_id = str(uuid.uuid4())[:8]

                # 创建客户端信息
                client_info = ClientInfo(client_id, client_socket, addr)

                # 创建接收队列
                self._receive_queues[client_id] = queue.Queue()

                # 添加客户端
                with self._clients_lock:
                    self._clients[client_id] = client_info
                    self._statistics["total_connections"] += 1
                    self._statistics["current_connections"] = len(
                        self._clients
                    )
                    if (
                        len(self._clients)
                        > self._statistics["max_connections"]
                    ):
                        self._statistics["max_connections"] = len(
                            self._clients
                        )

                # 使用线程池处理客户端
                if self._thread_pool:
                    self._thread_pool.submit(
                        self._client_handler, client_id, client_socket, addr
                    )
                else:
                    # 降级为线程处理
                    thread = threading.Thread(
                        target=self._client_handler,
                        args=(client_id, client_socket, addr),
                        daemon=True,
                    )
                    thread.start()

                # 触发事件
                self._emit("on_client_connect", client_id, addr)
                logger.info(f"[TCPServer] 客户端 {client_id} 已连接: {addr}")

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"[TCPServer] 接受连接异常: {e}")
                break

    def _client_handler(
        self,
        client_id: str,
        client_socket: socket.socket,
        addr: Tuple[str, int],
    ):
        """客户端处理线程"""
        buffer = b""
        last_activity = time.time()

        while self._running:
            try:
                # 检查连接超时
                current_time = time.time()
                if current_time - last_activity > self._config.get(
                    "connection_timeout", 60.0
                ):
                    logger.warning(f"[TCPServer] 客户端 {client_id} 连接超时")
                    break

                # 接收数据
                data = client_socket.recv(
                    self._config.get("receive_buffer_size", 4096)
                )
                if not data:
                    break

                # 更新活动时间
                last_activity = current_time

                # 更新客户端信息
                with self._clients_lock:
                    if client_id in self._clients:
                        client_info = self._clients[client_id]
                        client_info.receive_count += 1
                        client_info.last_activity = current_time
                        client_info.buffer += data

                # 更新统计信息
                self._statistics["total_received"] += len(data)

                # 处理数据
                if client_id in self._receive_queues:
                    try:
                        self._receive_queues[client_id].put_nowait(data)
                        # 触发事件
                        self._emit("on_client_data", client_id, data)
                    except Exception as e:
                        logger.error(f"[TCPServer] 队列满: {e}")
                        break

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(
                        f"[TCPServer] 客户端 {client_id} 接收异常: {e}"
                    )
                    self._statistics["error_count"] += 1
                break

        self._remove_client(client_id)

    def _remove_client(self, client_id: str, graceful: bool = False):
        """移除客户端"""
        with self._clients_lock:
            if client_id in self._clients:
                client_info = self._clients[client_id]
                client_socket = client_info.socket
                if client_socket:
                    try:
                        if graceful:
                            # 优雅关闭
                            try:
                                client_socket.sendall(b"Server shutting down")
                            except:
                                pass
                        client_socket.shutdown(socket.SHUT_RDWR)
                        client_socket.close()
                    except:
                        pass
                del self._clients[client_id]
                self._statistics["current_connections"] = len(self._clients)

        # 清理接收队列
        if client_id in self._receive_queues:
            del self._receive_queues[client_id]

        # 触发事件
        self._emit("on_client_disconnect", client_id)
        logger.info(f"[TCPServer] 客户端 {client_id} 已断开")

    def _start_heartbeat(self):
        """启动心跳"""
        self._stop_heartbeat()
        interval = self._config.get("heartbeat_interval", 30.0)
        self._heartbeat_timer = threading.Timer(interval, self._heartbeat)
        self._heartbeat_timer.daemon = True
        self._heartbeat_timer.start()

    def _stop_heartbeat(self):
        """停止心跳"""
        if self._heartbeat_timer:
            try:
                self._heartbeat_timer.cancel()
            except:
                pass
            self._heartbeat_timer = None

    def _heartbeat(self):
        """心跳检查"""
        if not self._running:
            return

        try:
            # 检查客户端连接状态
            current_time = time.time()
            timeout = self._config.get("connection_timeout", 60.0)

            clients_to_remove = []
            with self._clients_lock:
                for client_id, client_info in self._clients.items():
                    if current_time - client_info.last_activity > timeout:
                        clients_to_remove.append(client_id)

            # 移除超时的客户端
            for client_id in clients_to_remove:
                logger.warning(f"[TCPServer] 客户端 {client_id} 心跳超时")
                self._remove_client(client_id)

            # 触发事件
            self._emit("on_heartbeat")

        except Exception as e:
            logger.error(f"[TCPServer] 心跳检查失败: {e}")
        finally:
            # 重新启动心跳
            if self._running:
                self._start_heartbeat()

    def _cleanup_clients(self):
        """清理客户端"""
        current_time = time.time()
        timeout = self._config.get("connection_timeout", 60.0)

        clients_to_remove = []
        with self._clients_lock:
            for client_id, client_info in self._clients.items():
                if current_time - client_info.last_activity > timeout:
                    clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            self._remove_client(client_id)


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO)

    server = TCPServer()
    server.register_callback(
        "on_client_connect",
        lambda cid, addr: print(f"客户端 {cid} 已连接: {addr}"),
    )
    server.register_callback(
        "on_client_disconnect", lambda cid: print(f"客户端 {cid} 已断开")
    )

    if server.listen({"port": 8888, "backlog": 5}):
        print("服务端已启动，等待客户端连接...")

        try:
            while True:
                client_id, data = server.receive_from(timeout=0.5)
                if data:
                    print(f"收到 [客户端{client_id}]: {data}")
                    server.send_to(client_id, f"已收到: {data}")
        except KeyboardInterrupt:
            pass
        finally:
            server.stop()
