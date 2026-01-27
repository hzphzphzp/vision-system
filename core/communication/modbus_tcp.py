#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus TCP客户端模块（修正版）

实现Modbus TCP协议客户端，支持连接Modbus TCP服务器进行数据读写。

Author: Vision System Team
Date: 2026-01-13
"""

import socket
import struct
import threading
import queue
import logging
from typing import Optional, Dict, Any, List, Tuple
from enum import IntEnum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.protocol_base import ProtocolBase, ConnectionState

logger = logging.getLogger("ModbusTCP")


class ModbusFunctionCode(IntEnum):
    """Modbus功能码"""
    READ_COIL = 0x01
    READ_DISCRETE_INPUT = 0x02
    READ_HOLDING_REG = 0x03
    READ_INPUT_REG = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REG = 0x06
    WRITE_MULTIPLE_COIL = 0x0F
    WRITE_MULTIPLE_REG = 0x10


class ModbusExceptionCode(IntEnum):
    """Modbus异常码"""
    ILLEGAL_FUNCTION = 0x01
    ILLEGAL_DATA_ADDRESS = 0x02
    ILLEGAL_DATA_VALUE = 0x03
    SLAVE_DEVICE_FAILURE = 0x04
    ACKNOWLEDGE = 0x05
    SLAVE_DEVICE_BUSY = 0x06
    MEMORY_PARITY_ERROR = 0x08
    GATEWAY_PATH_UNAVAILABLE = 0x0A
    GATEWAY_TARGET_FAILED = 0x0B


class ModbusTCPClient(ProtocolBase):
    """Modbus TCP客户端类"""
    
    protocol_name = "ModbusTCP"
    
    def __init__(self):
        super().__init__()
        self._socket: Optional[socket.socket] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False
        self._transaction_id = 0
        self._transaction_lock = threading.Lock()
        self._unit_id = 1
        self._response_queues: Dict[int, queue.Queue] = {}
        self._lock = threading.Lock()
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接到Modbus TCP服务器"""
        if self._state == ConnectionState.CONNECTED:
            return True
        
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 502)
        timeout = config.get("timeout", 5.0)
        self._unit_id = config.get("unit_id", 1)
        
        self._config = config
        self.set_state(ConnectionState.CONNECTING)
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((host, port))
            self._socket.settimeout(0.2)
            
            self._running = True
            self._transaction_id = 0
            self._response_queues.clear()
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            self.set_state(ConnectionState.CONNECTED)
            self._emit("on_connect")
            logger.info(f"[ModbusTCP] 成功连接到 {host}:{port}")
            return True
            
        except Exception as e:
            self.set_state(ConnectionState.ERROR)
            logger.error(f"[ModbusTCP] 连接失败: {e}")
            self._emit("on_error", str(e))
            return False
    
    def disconnect(self):
        """断开连接"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
        
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        
        self._response_queues.clear()
        
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=2.0)
        
        self.set_state(ConnectionState.DISCONNECTED)
        self._emit("on_disconnect")
        logger.info("[ModbusTCP] 已断开连接")
    
    def read_coils(self, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取线圈状态"""
        return self._read_bits(ModbusFunctionCode.READ_COIL, address, count)
    
    def read_discrete_inputs(self, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取离散输入"""
        return self._read_bits(ModbusFunctionCode.READ_DISCRETE_INPUT, address, count)
    
    def read_holding_registers(self, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取保持寄存器"""
        return self._read_words(ModbusFunctionCode.READ_HOLDING_REG, address, count)
    
    def read_input_registers(self, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取输入寄存器"""
        return self._read_words(ModbusFunctionCode.READ_INPUT_REG, address, count)
    
    def write_single_coil(self, address: int, value: int) -> Tuple[bool, int]:
        """写入单个线圈"""
        coil_value = 0xFF00 if value else 0x0000
        pdu = struct.pack(">BBHH", ModbusFunctionCode.WRITE_SINGLE_COIL, 
                        (address >> 8) & 0xFF, address & 0xFF, coil_value)
        
        response = self._transaction(pdu)
        
        if response and len(response) >= 6:
            addr = struct.unpack(">H", response[2:4])[0]
            val = struct.unpack(">H", response[4:6])[0]
            return True, addr
        
        return False, 0
    
    def write_single_register(self, address: int, value: int) -> Tuple[bool, int]:
        """写入单个寄存器"""
        pdu = struct.pack(">BBHH", ModbusFunctionCode.WRITE_SINGLE_REG,
                        (address >> 8) & 0xFF, address & 0xFF, value)
        
        response = self._transaction(pdu)
        
        if response and len(response) >= 6:
            addr = struct.unpack(">H", response[2:4])[0]
            return True, addr
        
        return False, 0
    
    def write_multiple_coils(self, address: int, values: List[int]) -> Tuple[bool, int]:
        """写入多个线圈"""
        byte_count = (len(values) + 7) // 8
        coil_data = bytearray()
        for i in range(byte_count):
            byte_val = 0
            for j in range(8):
                idx = i * 8 + j
                if idx < len(values) and values[idx]:
                    byte_val |= (1 << j)
            coil_data.append(byte_val)
        
        pdu = struct.pack(">BBH", ModbusFunctionCode.WRITE_MULTIPLE_COIL,
                        (address >> 8) & 0xFF, address & 0xFF)
        pdu += struct.pack(">B", len(coil_data))
        pdu += bytes(coil_data)
        
        response = self._transaction(pdu)
        
        if response and len(response) >= 6:
            addr = struct.unpack(">H", response[2:4])[0]
            count = struct.unpack(">H", response[4:6])[0]
            return True, count
        
        return False, 0
    
    def write_multiple_registers(self, address: int, values: List[int]) -> Tuple[bool, int]:
        """写入多个寄存器"""
        byte_count = len(values) * 2
        
        pdu = struct.pack(">BBH", ModbusFunctionCode.WRITE_MULTIPLE_REG,
                        (address >> 8) & 0xFF, address & 0xFF)
        pdu += struct.pack(">B", byte_count)
        
        for value in values:
            pdu += struct.pack(">H", value)
        
        response = self._transaction(pdu)
        
        if response and len(response) >= 6:
            addr = struct.unpack(">H", response[2:4])[0]
            count = struct.unpack(">H", response[4:6])[0]
            return True, count
        
        return False, 0
    
    def _read_bits(self, func_code: int, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取位数据"""
        pdu = struct.pack(">BBHH", func_code, 
                         (address >> 8) & 0xFF, 
                         address & 0xFF, 
                         count)
        
        response = self._transaction(pdu)
        
        if not response:
            return False, []
        
        if response[1] & 0x80:
            self._handle_exception(response[2])
            return False, []
        
        byte_count = response[2]
        result = []
        for i in range(byte_count):
            for j in range(8):
                if len(result) < count:
                    result.append((response[3 + i] >> j) & 1)
        
        return True, result
    
    def _read_words(self, func_code: int, address: int, count: int) -> Tuple[bool, List[int]]:
        """读取字数据"""
        pdu = struct.pack(">BBHH", func_code, 
                         (address >> 8) & 0xFF, 
                         address & 0xFF, 
                         count)
        
        response = self._transaction(pdu)
        
        if not response:
            return False, []
        
        if response[1] & 0x80:
            self._handle_exception(response[2])
            return False, []
        
        byte_count = response[2]
        result = []
        for i in range(byte_count // 2):
            value = struct.unpack(">H", response[3 + i * 2:3 + i * 2 + 2])[0]
            result.append(value)
        
        return True, result
    
    def _transaction(self, pdu: bytes) -> Optional[bytes]:
        """执行Modbus事务"""
        if not self._socket:
            return None
        
        with self._transaction_lock:
            transaction_id = self._transaction_id
            self._transaction_id = (self._transaction_id + 1) & 0xFFFF
        
        try:
            mbap = struct.pack(">HHBB", transaction_id, len(pdu) + 1, self._unit_id, 0)
            request = mbap + pdu
            
            self._socket.sendall(request)
            
            q = queue.Queue()
            self._response_queues[transaction_id] = q
            
            response = q.get(timeout=5.0)
            
            if transaction_id in self._response_queues:
                del self._response_queues[transaction_id]
            
            return response
            
        except queue.Empty:
            logger.error(f"[ModbusTCP] 响应超时: transaction_id={transaction_id}")
            if transaction_id in self._response_queues:
                del self._response_queues[transaction_id]
            return None
        except Exception as e:
            logger.error(f"[ModbusTCP] 事务失败: {e}")
            if transaction_id in self._response_queues:
                del self._response_queues[transaction_id]
            return None
    
    def _receive_loop(self):
        """接收数据循环"""
        buffer = b""
        
        while self._running:
            try:
                data = self._socket.recv(4096)
                if not data:
                    if self._running:
                        logger.warning("[ModbusTCP] 服务器关闭连接")
                    break
                
                buffer += data
                
                while len(buffer) >= 7:
                    trans_id = struct.unpack(">H", buffer[0:2])[0]
                    length = struct.unpack(">H", buffer[2:4])[0]
                    unit_id = buffer[4]
                    func_code = buffer[5]
                    
                    total_len = 6 + length - 2
                    if len(buffer) < total_len:
                        break
                    
                    pdu = buffer[6:total_len]
                    buffer = buffer[total_len:]
                    
                    expected_unit_id = getattr(self, '_last_unit_id', 1)
                    
                    if trans_id in self._response_queues:
                        try:
                            self._response_queues[trans_id].put_nowait(pdu)
                        except:
                            pass
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.debug(f"[ModbusTCP] 接收异常: {e}")
                break
    
    def _handle_exception(self, exception_code: int):
        """处理Modbus异常"""
        exceptions = {
            ModbusExceptionCode.ILLEGAL_FUNCTION: "非法功能",
            ModbusExceptionCode.ILLEGAL_DATA_ADDRESS: "非法数据地址",
            ModbusExceptionCode.ILLEGAL_DATA_VALUE: "非法数据值",
            ModbusExceptionCode.SLAVE_DEVICE_FAILURE: "从站设备故障",
            ModbusExceptionCode.SLAVE_DEVICE_BUSY: "从站设备忙",
            ModbusExceptionCode.MEMORY_PARITY_ERROR: "内存奇偶校验错误",
            ModbusExceptionCode.GATEWAY_PATH_UNAVAILABLE: "网关路径不可用",
            ModbusExceptionCode.GATEWAY_TARGET_FAILED: "网关目标失败",
        }
        
        msg = exceptions.get(exception_code, f"未知异常({exception_code})")
        logger.error(f"[ModbusTCP] Modbus异常: {msg}")
        self._emit("on_error", msg)


if __name__ == "__main__":
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    client = ModbusTCPClient()
    
    print("连接Modbus TCP服务器...")
    if client.connect({"host": "127.0.0.1", "port": 502, "timeout": 5.0}):
        print("连接成功!")
        
        time.sleep(0.5)
        
        print("读取保持寄存器...")
        success, values = client.read_holding_registers(0, 10)
        if success:
            print(f"寄存器值: {values}")
        else:
            print("读取失败")
        
        client.disconnect()
    else:
        print("连接失败")
