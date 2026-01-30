#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口通讯模块

实现串口通讯功能，支持RS232/RS485等串口设备通信。

功能特性:
- 自动检测可用串口
- 常用波特率支持
- 数据位/停止位/校验位配置
- 十六进制收发

Usage:
    from core.communication import SerialPort

    serial = SerialPort()
    serial.register_callback("on_receive", lambda data: print(f"收到: {data}"))

    if serial.connect({"port": "COM3", "baudrate": 9600}):
        serial.send("Hello")
        serial.disconnect()
"""

import logging
import os
import sys
import threading
from typing import Any, Callable, Dict, Optional, Union

import serial
import serial.tools.list_ports

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import (
    ConnectionState,
    DataParser,
    ProtocolBase,
    TextParser,
)

logger = logging.getLogger("SerialPort")


class SerialPort(ProtocolBase):
    """串口通讯类

    提供串口通讯功能，用于与RS232/RS485等串口设备通信。
    """

    protocol_name = "SerialPort"

    SUPPORTED_BAUDRATES = [
        9600,
        19200,
        38400,
        57600,
        115200,
        230400,
        460800,
        921600,
    ]

    SUPPORTED_BYTESIZES = [5, 6, 7, 8]
    SUPPORTED_STOPBITS = [
        serial.STOPBITS_ONE,
        serial.STOPBITS_ONE_POINT_FIVE,
        serial.STOPBITS_TWO,
    ]
    SUPPORTED_PARITIES = [
        serial.PARITY_NONE,
        serial.PARITY_EVEN,
        serial.PARITY_ODD,
        serial.PARITY_MARK,
        serial.PARITY_SPACE,
    ]

    def __init__(self):
        super().__init__()
        self._serial: Optional[serial.Serial] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False
        self._parser: TextParser = TextParser()

    @staticmethod
    def list_ports() -> list:
        """列出所有可用串口

        Returns:
            list: 可用串口列表，每个元素为(port, description, hardware_id)
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(
                {
                    "port": port.device,
                    "description": port.description,
                    "hardware_id": port.hwid,
                }
            )
        return ports

    def connect(self, config: Dict[str, Any]) -> bool:
        """打开串口

        Args:
            config: 串口配置
                - port: 串口名称（如COM1或/dev/ttyUSB0）
                - baudrate: 波特率（默认115200）
                - bytesize: 数据位（默认8）
                - stopbits: 停止位（默认1）
                - parity: 校验位（默认无）
                - timeout: 读取超时（秒）
                - parser: 数据解析器（可选）

        Returns:
            bool: 是否成功打开
        """
        if self._state == ConnectionState.CONNECTED:
            logger.warning("[SerialPort] 串口已打开")
            return True

        port = config.get("port", "COM1")
        baudrate = config.get("baudrate", 115200)
        bytesize = config.get("bytesize", 8)
        stopbits = config.get("stopbits", serial.STOPBITS_ONE)
        parity = config.get("parity", serial.PARITY_NONE)
        timeout = config.get("timeout", 1.0)
        self._parser = config.get("parser", TextParser())

        self._config = config
        self.set_state(ConnectionState.CONNECTING)

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                stopbits=stopbits,
                parity=parity,
                timeout=timeout,
            )

            if self._serial.is_open:
                self._running = True
                self._receive_thread = threading.Thread(
                    target=self._receive_loop, daemon=True
                )
                self._receive_thread.start()

                self.set_state(ConnectionState.CONNECTED)
                self._emit("on_connect")
                logger.info(f"[SerialPort] 成功打开串口 {port}: {baudrate}bps")
                return True
            else:
                self.set_state(ConnectionState.ERROR)
                logger.error(f"[SerialPort] 无法打开串口 {port}")
                return False

        except serial.SerialException as e:
            self.set_state(ConnectionState.ERROR)
            logger.error(f"[SerialPort] 打开串口失败: {e}")
            self._emit("on_error", str(e))
            return False

    def disconnect(self):
        """关闭串口"""
        self._running = False

        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
                self._serial = None
            except Exception as e:
                logger.debug(f"[SerialPort] 关闭串口时发生异常: {e}")

        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_disconnect")
        logger.info("[SerialPort] 已关闭串口")

    def send(self, data: Union[str, bytes, dict]) -> bool:
        """发送数据

        Args:
            data: 要发送的数据

        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected():
            logger.warning("[SerialPort] 串口未打开，无法发送")
            return False

        try:
            if isinstance(data, dict):
                data = self._parser.format(data)
            elif isinstance(data, str):
                data = data.encode("utf-8")

            self._serial.write(data)
            return True

        except Exception as e:
            logger.error(f"[SerialPort] 发送数据失败: {e}")
            self._emit("on_error", str(e))
            return False

    def send_hex(self, hex_data: str) -> bool:
        """发送十六进制数据

        Args:
            hex_data: 十六进制字符串，如 "FF AA 01"

        Returns:
            bool: 发送是否成功
        """
        try:
            data = bytes.fromhex(hex_data.replace(" ", ""))
            return self.send(data)
        except ValueError as e:
            logger.error(f"[SerialPort] 十六进制数据格式错误: {e}")
            return False

    def receive(self, timeout: float = None) -> Any:
        """接收数据（阻塞模式）"""
        if not self.is_connected() or not self._serial:
            return None

        try:
            if timeout:
                self._serial.timeout = timeout

            data = self._serial.readline()
            if data:
                return self._parser.parse(data)
            return None

        except Exception as e:
            logger.error(f"[SerialPort] 接收数据失败: {e}")
            return None

    def _receive_loop(self):
        """接收数据循环"""
        buffer = b""

        while self._running and self._serial:
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    if data:
                        buffer += data
                        parsed = self._parser.parse(buffer)
                        if parsed:
                            buffer = b""
                            self._emit("on_receive", parsed)

            except Exception as e:
                if self._running:
                    logger.error(f"[SerialPort] 接收异常: {e}")
                break

    def purge(self):
        """清空接收缓冲区"""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            logger.debug("[SerialPort] 已清空接收缓冲区")

    def get_port_info(self) -> Dict[str, Any]:
        """获取串口信息"""
        if not self._serial:
            return {}

        return {
            "port": self._serial.port,
            "baudrate": self._serial.baudrate,
            "bytesize": self._serial.bytesize,
            "stopbits": self._serial.stopbits,
            "parity": self._serial.parity,
            "in_waiting": self._serial.in_waiting,
            "out_waiting": self._serial.out_waiting,
        }


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)

    print("可用串口:")
    for port in SerialPort.list_ports():
        print(f"  {port['port']} - {port['description']}")

    serial_port = SerialPort()
    serial_port.register_callback(
        "on_receive", lambda data: print(f"收到: {data}")
    )
    serial_port.register_callback("on_connect", lambda: print("串口已打开"))
    serial_port.register_callback("on_disconnect", lambda: print("串口已关闭"))

    config = {"port": "COM1", "baudrate": 9600, "timeout": 1.0}

    if serial_port.connect(config):
        serial_port.send("AT\r\n")

        import time

        time.sleep(2)

        serial_port.disconnect()
