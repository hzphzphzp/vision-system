#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯配置管理模块 - 修复版

修复：所有协议创建改为异步，避免阻塞AI
"""

import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.communication import ProtocolBase
from core.communication.tcp_client import TCPClient
from core.communication.tcp_server import TCPServer
from core.tool_base import ToolBase, ToolRegistry


@dataclass
class ProtocolConnection:
    """协议连接数据类"""

    id: str
    name: str
    protocol_type: str
    config: Dict[str, Any]
    is_connected: bool = False
    status: str = "未连接"
    protocol_instance: Optional[ProtocolBase] = None
    send_count: int = 0
    receive_count: int = 0
    error_count: int = 0


class ConnectionStorage:
    """连接存储类 - 支持文件持久化"""

    def __init__(self):
        self._connections: Dict[str, Dict] = {}
        # 配置文件路径
        self._config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        self._config_file = os.path.join(self._config_dir, "communication_config.json")
        # 确保配置目录存在
        os.makedirs(self._config_dir, exist_ok=True)

    def save_connections(self, connections: List[ProtocolConnection]) -> bool:
        """保存连接配置到内存和文件"""
        try:
            for conn in connections:
                self._connections[conn.id] = {
                    "id": conn.id,
                    "name": conn.name,
                    "protocol_type": conn.protocol_type,
                    "config": conn.config,
                    "is_connected": False,  # 保存时不保存连接状态
                    "status": "未连接",  # 重置状态
                }
            # 同时保存到文件
            self._save_to_file()
            return True
        except Exception as e:
            logger.error(f"保存连接失败: {e}")
            return False

    def load_connections(self) -> List[Dict]:
        """从内存加载连接配置，如果内存为空则从文件加载"""
        if not self._connections:
            self._load_from_file()
        return list(self._connections.values())

    def _save_to_file(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._connections, f, ensure_ascii=False, indent=2)
            logger.info(f"通讯配置已保存到文件: {self._config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置到文件失败: {e}")
            return False

    def _load_from_file(self) -> bool:
        """从文件加载配置"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._connections = json.load(f)
                logger.info(f"已从文件加载通讯配置: {self._config_file}")
                return True
            else:
                logger.info("通讯配置文件不存在，使用空配置")
                return False
        except Exception as e:
            logger.error(f"从文件加载配置失败: {e}")
            return False


class ConnectionValidator:
    """连接验证器"""

    @staticmethod
    def validate_config(protocol_type: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证连接配置"""
        try:
            if protocol_type in ["TCP客户端", "TCP服务端", "WebSocket", "HTTP", "Modbus TCP"]:
                host = config.get("host")
                port = config.get("port")

                if not host:
                    return False, "目标地址不能为空"
                if not port:
                    return False, "目标端口不能为空"
                if not isinstance(port, int) or port < 1 or port > 65535:
                    return False, "目标端口必须是1-65535之间的整数"
            elif protocol_type == "串口":
                port = config.get("port")
                baudrate = config.get("baudrate")
                
                if not port:
                    return False, "串口不能为空"
                if not baudrate:
                    return False, "波特率不能为空"

            return True, ""
        except Exception as e:
            return False, f"配置验证失败: {e}"


class ProtocolCreateWorker(QThread):
    """后台协议创建线程"""
    
    finished = pyqtSignal(str, bool, object)  # connection_id, success, instance
    
    def __init__(self, connection_id: str, protocol_type: str, config: Dict):
        super().__init__()
        self.connection_id = connection_id
        self.protocol_type = protocol_type
        self.config = config
    
    def run(self):
        """在后台线程创建协议实例"""
        try:
            logger.info(f"[ProtocolCreateWorker] 创建协议: {self.protocol_type}")
            
            if self.protocol_type == "TCP客户端":
                client = TCPClient()
                if client.connect(self.config):
                    logger.info(f"[ProtocolCreateWorker] TCP客户端创建成功")
                    self.finished.emit(self.connection_id, True, client)
                else:
                    logger.error(f"[ProtocolCreateWorker] TCP客户端连接失败")
                    self.finished.emit(self.connection_id, False, None)
            elif self.protocol_type == "TCP服务端":
                server = TCPServer()
                if server.listen(self.config):
                    logger.info(f"[ProtocolCreateWorker] TCP服务端创建成功")
                    self.finished.emit(self.connection_id, True, server)
                else:
                    logger.error(f"[ProtocolCreateWorker] TCP服务端监听失败")
                    self.finished.emit(self.connection_id, False, None)
            elif self.protocol_type == "串口":
                from core.communication.serial_port import SerialPort
                serial = SerialPort()
                if serial.connect(self.config):
                    logger.info(f"[ProtocolCreateWorker] 串口创建成功")
                    self.finished.emit(self.connection_id, True, serial)
                else:
                    logger.error(f"[ProtocolCreateWorker] 串口连接失败")
                    self.finished.emit(self.connection_id, False, None)
            elif self.protocol_type == "WebSocket":
                from core.communication.websocket import WebSocketClient
                ws = WebSocketClient()
                if ws.connect(self.config):
                    logger.info(f"[ProtocolCreateWorker] WebSocket创建成功")
                    self.finished.emit(self.connection_id, True, ws)
                else:
                    logger.error(f"[ProtocolCreateWorker] WebSocket连接失败")
                    self.finished.emit(self.connection_id, False, None)
            elif self.protocol_type == "HTTP":
                from core.communication.http_client import HTTPClient
                http = HTTPClient()
                if http.connect(self.config):
                    logger.info(f"[ProtocolCreateWorker] HTTP创建成功")
                    self.finished.emit(self.connection_id, True, http)
                else:
                    logger.error(f"[ProtocolCreateWorker] HTTP连接失败")
                    self.finished.emit(self.connection_id, False, None)
            elif self.protocol_type == "Modbus TCP":
                from core.communication.modbus_tcp import ModbusTCPClient
                modbus = ModbusTCPClient()
                if modbus.connect(self.config):
                    logger.info(f"[ProtocolCreateWorker] Modbus TCP创建成功")
                    self.finished.emit(self.connection_id, True, modbus)
                else:
                    logger.error(f"[ProtocolCreateWorker] Modbus TCP连接失败")
                    self.finished.emit(self.connection_id, False, None)
            else:
                logger.error(f"[ProtocolCreateWorker] 不支持的协议: {self.protocol_type}")
                self.finished.emit(self.connection_id, False, None)
                
        except Exception as e:
            logger.error(f"[ProtocolCreateWorker] 创建异常: {e}")
            self.finished.emit(self.connection_id, False, None)


class ConnectionManager:
    """连接管理器（全局单例）"""

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 只在第一次初始化时创建属性，避免单例重复初始化清空数据
        if not hasattr(self, '_initialized'):
            self._connections: Dict[str, ProtocolConnection] = {}
            self._lock = threading.Lock()
            self._status_callback: Optional[Callable] = None
            self._storage = ConnectionStorage()
            self._pending_workers: Dict[str, ProtocolCreateWorker] = {}
            # 注意：不再自动加载全局配置，配置由方案驱动
            # 当加载方案时，方案会调用相应方法加载通讯配置
            self._initialized = True

    def load_from_solution(self, communication_config: List[Dict]):
        """从方案加载连接配置
        
        Args:
            communication_config: 方案中的通讯配置列表
        """
        try:
            # 清空现有连接
            with self._lock:
                self._connections.clear()
            
            # 加载方案中的连接
            for conn_data in communication_config:
                connection = ProtocolConnection(
                    id=conn_data["id"],
                    name=conn_data["name"],
                    protocol_type=conn_data["protocol_type"],
                    config=conn_data["config"],
                    is_connected=False,  # 加载时重置为未连接
                    status="未连接",
                )
                self._connections[connection.id] = connection
            logger.info(f"[ConnectionManager] 从方案加载了 {len(communication_config)} 个连接配置")
            
            # 加载后自动连接所有
            self._auto_connect_all()
            
        except Exception as e:
            logger.error(f"[ConnectionManager] 从方案加载连接配置失败: {e}")
    
    def _auto_connect_all(self):
        """自动连接所有配置为自动连接的通讯项"""
        if not self._connections:
            return
        
        logger.info("[ConnectionManager] 开始自动连接...")
        
        for conn_id, connection in list(self._connections.items()):
            # 检查是否为自动连接模式
            auto_connect = connection.config.get("auto_connect", True)
            
            if auto_connect:
                logger.info(f"[ConnectionManager] 自动连接: {connection.name}")
                # 异步创建并连接
                self._create_and_connect_async(connection)
            else:
                logger.info(f"[ConnectionManager] 跳过非自动连接: {connection.name}")
    
    def clear_all_connections(self):
        """清空所有连接配置"""
        try:
            with self._lock:
                # 断开所有连接
                for conn in self._connections.values():
                    if conn.protocol_instance and hasattr(conn.protocol_instance, 'disconnect'):
                        try:
                            conn.protocol_instance.disconnect()
                        except Exception:
                            pass
                self._connections.clear()
            logger.info("[ConnectionManager] 已清空所有连接配置")
        except Exception as e:
            logger.error(f"[ConnectionManager] 清空连接配置失败: {e}")

    def set_status_callback(self, callback: Callable):
        """设置状态回调"""
        self._status_callback = callback

    def generate_connection_name(self, protocol_type: str) -> str:
        """自动生成连接名称
        
        命名规则：
        - 第一个TCP客户端连接：TCP客户端_1
        - 第一个TCP服务端连接：TCP服务端_1
        - 后续同类型连接依次递增编号
        
        Args:
            protocol_type: 协议类型（如"TCP客户端"、"TCP服务端"等）
            
        Returns:
            str: 自动生成的连接名称
        """
        with self._lock:
            # 获取当前该协议类型的所有连接
            existing_names = []
            for conn in self._connections.values():
                if conn.protocol_type == protocol_type:
                    existing_names.append(conn.name)
            
            # 查找最大编号
            max_number = 0
            prefix = f"{protocol_type}_"
            
            for name in existing_names:
                if name.startswith(prefix):
                    try:
                        number = int(name[len(prefix):])
                        max_number = max(max_number, number)
                    except ValueError:
                        # 名称格式不符合，跳过
                        pass
            
            # 生成新名称
            new_number = max_number + 1
            new_name = f"{prefix}{new_number}"
            
            logger.info(f"[ConnectionManager] 自动生成连接名称: {new_name}")
            return new_name

    def add_connection(self, connection: ProtocolConnection) -> bool:
        """添加连接 - 异步创建协议实例"""
        # 验证配置
        valid, error_msg = ConnectionValidator.validate_config(
            connection.protocol_type, connection.config
        )
        if not valid:
            logger.error(f"添加连接失败: {error_msg}")
            return False

        # 先添加连接（不创建协议实例）
        connection.protocol_instance = None
        connection.status = "连接中..."
        connection.is_connected = False
        
        with self._lock:
            self._connections[connection.id] = connection
        
        # 保存配置
        self._save_connections()
        
        # 在后台线程创建协议实例
        worker = ProtocolCreateWorker(
            connection.id, connection.protocol_type, connection.config
        )
        worker.finished.connect(self._on_protocol_created)
        self._pending_workers[connection.id] = worker
        worker.start()
        
        logger.info(f"[ConnectionManager] 启动后台创建: {connection.id}")
        return True
    
    def _create_and_connect_async(self, connection: ProtocolConnection):
        """异步创建并连接协议实例"""
        if connection.id in self._pending_workers:
            logger.warning(f"[ConnectionManager] 连接正在创建中: {connection.id}")
            return
        
        connection.status = "连接中..."
        
        worker = ProtocolCreateWorker(
            connection.id, connection.protocol_type, connection.config
        )
        worker.finished.connect(self._on_protocol_created)
        self._pending_workers[connection.id] = worker
        worker.start()
        
        logger.info(f"[ConnectionManager] 启动自动连接: {connection.id}")
    
    def _on_protocol_created(self, connection_id: str, success: bool, instance):
        """协议实例创建完成回调"""
        # 清理worker
        if connection_id in self._pending_workers:
            del self._pending_workers[connection_id]
        
        with self._lock:
            if connection_id in self._connections:
                conn = self._connections[connection_id]
                if success and instance:
                    conn.protocol_instance = instance
                    conn.is_connected = True
                    conn.status = "已连接"
                    logger.info(f"[ConnectionManager] 连接成功: {connection_id}")
                else:
                    conn.is_connected = False
                    conn.status = "连接失败"
                    logger.error(f"[ConnectionManager] 连接失败: {connection_id}")
                
                # 通知状态变化
                if self._status_callback:
                    self._status_callback(conn)

    def remove_connection(self, connection_id: str) -> bool:
        """移除连接（异步，不阻塞UI）"""
        # 先在锁外收集需要的数据，避免在锁内进行复杂操作
        conn_to_remove = None
        protocol_to_cleanup = None

        with self._lock:
            if connection_id in self._connections:
                conn = self._connections[connection_id]
                conn_to_remove = {
                    'id': conn.id,
                    'name': conn.name,
                }
                protocol_to_cleanup = conn.protocol_instance
                # 立即从字典中移除，避免其他线程访问
                del self._connections[connection_id]

        # 异步清理协议实例（不在锁内执行，避免阻塞UI）
        if protocol_to_cleanup:
            def cleanup():
                try:
                    # 调用正式的disconnect方法，确保资源正确释放
                    if hasattr(protocol_to_cleanup, 'disconnect'):
                        protocol_to_cleanup.disconnect()
                    # 清除回调，防止内存泄漏
                    if hasattr(protocol_to_cleanup, 'clear_callbacks'):
                        protocol_to_cleanup.clear_callbacks()
                except Exception as e:
                    logger.error(f"[ConnectionManager] 清理协议实例失败: {e}")
            
            # 启动后台线程进行清理
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()

        # 异步保存配置
        self._save_connections_async()

        return conn_to_remove is not None

    def _save_connections_async(self):
        """异步保存连接配置（方案驱动，不保存到文件）
        
        注意：通讯配置现在由方案驱动，会在保存方案时一起保存。
        此方法不再执行实际的文件保存操作。
        """
        # 方案驱动模式下，配置不保存到全局文件
        # 只在内存中维护，由方案保存时统一持久化
        pass

    def force_remove_connection(self, connection_id: str) -> bool:
        """强制移除连接（已废弃，使用remove_connection）"""
        return self.remove_connection(connection_id)

    def get_connection(self, connection_id: str) -> Optional[ProtocolConnection]:
        """获取连接"""
        with self._lock:
            return self._connections.get(connection_id)

    def get_all_connections(self) -> List[ProtocolConnection]:
        """获取所有连接"""
        with self._lock:
            return list(self._connections.values())

    def get_available_connections(self) -> List[Dict[str, Any]]:
        """获取可用的连接列表（供工具使用）"""
        result = []
        with self._lock:
            for conn_id, conn in self._connections.items():
                if conn.is_connected:
                    config = conn.config if hasattr(conn, 'config') else {}
                    host = config.get("host", config.get("url", ""))
                    port = config.get("port", "")
                    result.append({
                        "name": conn.name,
                        "device_id": conn_id,
                        "protocol_type": conn.protocol_type,
                        "display_name": f"[{conn_id}] {conn.protocol_type.upper()} - {conn.name} ({host}:{port})",
                        "connected": True,
                    })
        return result

    def _save_connections(self):
        """保存连接配置到内存（方案驱动，不保存到文件）
        
        注意：通讯配置现在由方案驱动，会在保存方案时一起保存。
        此方法仅用于内部状态管理，不再保存到全局文件。
        """
        # 方案驱动模式下，配置不保存到全局文件
        # 只在内存中维护，由方案保存时统一持久化
        pass


class ConnectionConfigDialog(QDialog):
    """连接配置对话框 - 支持所有协议"""

    def __init__(self, parent=None, connection_id: str = None):
        super().__init__(parent)
        self.connection_id = connection_id
        self.setWindowTitle("连接配置")
        self.setModal(True)
        self.resize(500, 400)

        self.connection_manager = get_connection_manager()
        self.setup_ui()

        if connection_id:
            self.load_connection(connection_id)
        else:
            # 新建连接时，自动生成默认名称
            self._generate_default_name()

    def setup_ui(self):
        """设置UI - 支持所有协议"""
        layout = QVBoxLayout()

        # 连接信息组
        info_group = QGroupBox("连接信息")
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("连接名称:"), 0, 0)
        self.name_edit = QLineEdit()
        info_layout.addWidget(self.name_edit, 0, 1)

        info_layout.addWidget(QLabel("协议类型:"), 1, 0)
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems([
            "TCP客户端", 
            "TCP服务端", 
            "串口",
            "WebSocket",
            "HTTP",
            "Modbus TCP"
        ])
        self.protocol_combo.currentTextChanged.connect(self.on_protocol_changed)
        info_layout.addWidget(self.protocol_combo, 1, 1)

        # 自动连接选项
        info_layout.addWidget(QLabel("自动连接:"), 2, 0)
        self.auto_connect_check = QCheckBox("程序启动时自动建立连接")
        self.auto_connect_check.setChecked(True)
        info_layout.addWidget(self.auto_connect_check, 2, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 协议配置组 - TCP/WebSocket/HTTP/Modbus
        self.tcp_config_group = QGroupBox("网络配置")
        tcp_config_layout = QGridLayout()

        tcp_config_layout.addWidget(QLabel("目标地址:"), 0, 0)
        self.host_edit = QLineEdit("127.0.0.1")
        tcp_config_layout.addWidget(self.host_edit, 0, 1)

        tcp_config_layout.addWidget(QLabel("目标端口:"), 1, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(8080)
        tcp_config_layout.addWidget(self.port_spin, 1, 1)

        self.tcp_config_group.setLayout(tcp_config_layout)
        layout.addWidget(self.tcp_config_group)

        # 协议配置组 - 串口
        self.serial_config_group = QGroupBox("串口配置")
        serial_config_layout = QGridLayout()

        serial_config_layout.addWidget(QLabel("串口号:"), 0, 0)
        self.serial_combo = QComboBox()
        self.serial_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"])
        serial_config_layout.addWidget(self.serial_combo, 0, 1)

        serial_config_layout.addWidget(QLabel("波特率:"), 1, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        serial_config_layout.addWidget(self.baud_combo, 1, 1)

        self.serial_config_group.setLayout(serial_config_layout)
        layout.addWidget(self.serial_config_group)

        # 默认显示TCP配置，隐藏串口配置
        self.serial_config_group.hide()

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_protocol_changed(self, protocol_type: str):
        """协议类型变化时更新UI"""
        if protocol_type == "串口":
            self.tcp_config_group.hide()
            self.serial_config_group.show()
        else:
            self.tcp_config_group.show()
            self.serial_config_group.hide()
        
        # 如果名称是自动生成的，根据新协议类型重新生成
        current_name = self.name_edit.text()
        if not current_name or "_" in current_name:
            # 检查是否是自动生成的名称格式
            parts = current_name.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                # 是自动生成的名称，重新生成
                new_name = self.connection_manager.generate_connection_name(protocol_type)
                self.name_edit.setText(new_name)

    def _generate_default_name(self):
        """生成默认连接名称
        
        根据当前选择的协议类型自动生成名称
        """
        protocol_type = self.protocol_combo.currentText()
        default_name = self.connection_manager.generate_connection_name(protocol_type)
        self.name_edit.setText(default_name)
        logger.info(f"[ConnectionConfigDialog] 生成默认连接名称: {default_name}")

    def load_connection(self, connection_id: str):
        """加载连接配置"""
        # 保存连接ID，确保编辑时保持相同的ID
        self.connection_id = connection_id
        
        conn = self.connection_manager.get_connection(connection_id)
        if conn:
            self.name_edit.setText(conn.name)
            self.protocol_combo.setCurrentText(conn.protocol_type)
            config = conn.config

            if conn.protocol_type == "串口":
                if "port" in config:
                    self.serial_combo.setCurrentText(config["port"])
                if "baudrate" in config:
                    self.baud_combo.setCurrentText(str(config["baudrate"]))
            else:
                if "host" in config:
                    self.host_edit.setText(config["host"])
                if "port" in config:
                    self.port_spin.setValue(config["port"])

            # 加载自动连接设置
            auto_connect = config.get("auto_connect", True)
            self.auto_connect_check.setChecked(auto_connect)

    def get_connection_config(self) -> Dict[str, Any]:
        """获取连接配置"""
        protocol_type = self.protocol_combo.currentText()
        config = {}

        if protocol_type == "串口":
            config["port"] = self.serial_combo.currentText()
            config["baudrate"] = int(self.baud_combo.currentText())
        else:
            config["host"] = self.host_edit.text()
            config["port"] = self.port_spin.value()

        # 添加自动连接配置
        config["auto_connect"] = self.auto_connect_check.isChecked()

        # 添加数据映射配置
        if hasattr(self, '_current_mapping') and self._current_mapping:
            try:
                mapping_data = json.loads(self._current_mapping)
                if mapping_data:
                    config["data_mapping"] = self._current_mapping
            except json.JSONDecodeError:
                pass

        return config

    def get_connection_data(self) -> Dict[str, Any]:
        """获取连接数据"""
        return {
            "id": self.connection_id or f"conn_{int(time.time())}",
            "name": self.name_edit.text(),
            "protocol_type": self.protocol_combo.currentText(),
            "config": self.get_connection_config(),
        }

    def accept(self):
        """接受对话框"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入连接名称")
            return
        super().accept()


class CommunicationConfigWidget(QWidget):
    """通讯配置主窗口"""

    connection_status_changed = pyqtSignal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用单例获取ConnectionManager，确保与方案加载使用的是同一个实例
        self.connection_manager = get_connection_manager()
        self.connection_manager.set_status_callback(self.on_connection_status_changed)
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar_layout = QHBoxLayout()

        add_button = QPushButton("添加连接")
        add_button.clicked.connect(self.add_connection)
        toolbar_layout.addWidget(add_button)

        edit_button = QPushButton("编辑连接")
        edit_button.clicked.connect(self.edit_connection)
        toolbar_layout.addWidget(edit_button)

        delete_button = QPushButton("删除连接")
        delete_button.clicked.connect(self.delete_connection)
        toolbar_layout.addWidget(delete_button)

        toolbar_layout.addStretch()

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_connections)
        toolbar_layout.addWidget(refresh_button)

        layout.addLayout(toolbar_layout)

        # 连接列表
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(6)
        self.connection_table.setHorizontalHeaderLabels(
            ["连接名称", "协议类型", "状态", "发送次数", "接收次数", "错误次数"]
        )
        layout.addWidget(self.connection_table)

        # 状态栏
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.connection_table.itemSelectionChanged.connect(self.on_selection_changed)

        # 注意：不再自动加载全局配置，配置由方案驱动
        # 当加载方案时，会调用refresh_connections()刷新显示

    def add_connection(self):
        """添加连接（非阻塞版本）"""
        dialog = ConnectionConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            connection_data = dialog.get_connection_data()
            connection = ProtocolConnection(
                id=connection_data["id"],
                name=connection_data["name"],
                protocol_type=connection_data["protocol_type"],
                config=connection_data["config"],
            )

            # 异步添加连接
            if self.connection_manager.add_connection(connection):
                # 立即刷新显示，不显示阻塞的对话框
                self.refresh_connections()
                # 更新状态栏显示连接状态
                self.status_label.setText(f"连接 '{connection.name}' 正在建立中...")
            else:
                QMessageBox.warning(self, "警告", "添加连接失败")

    def edit_connection(self):
        """编辑连接"""
        current_row = self.connection_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的连接")
            return

        connection_id = self.connection_table.item(current_row, 0).data(Qt.UserRole)

        # 打开编辑对话框
        dialog = ConnectionConfigDialog(self, connection_id)
        if dialog.exec_() == QDialog.Accepted:
            connection_data = dialog.get_connection_data()

            # 先删除旧连接
            self.connection_manager.remove_connection(connection_id)

            # 创建新连接
            new_connection = ProtocolConnection(
                id=connection_data["id"],
                name=connection_data["name"],
                protocol_type=connection_data["protocol_type"],
                config=connection_data["config"],
            )

            # 异步添加新连接
            if self.connection_manager.add_connection(new_connection):
                # 立即刷新显示，不显示阻塞的对话框
                self.refresh_connections()
                # 更新状态栏显示连接状态
                self.status_label.setText(f"连接 '{new_connection.name}' 正在重新建立中...")
            else:
                QMessageBox.warning(self, "警告", "更新连接失败")

    def delete_connection(self):
        """删除连接（修复版）
        
        修复内容:
        1. 添加空指针检查，防止item为None时崩溃
        2. 删除后清除选择状态，避免指向不存在的行
        3. 添加详细的错误信息和日志记录
        4. 添加异常处理，防止删除过程中崩溃
        """
        try:
            current_row = self.connection_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "警告", "请先选择要删除的连接")
                return

            # 获取当前行的连接项，添加空指针检查
            item = self.connection_table.item(current_row, 0)
            if item is None:
                QMessageBox.warning(self, "警告", "无法获取选中的连接信息")
                logger.warning(f"[CommunicationConfigWidget] 第{current_row}行的item为None")
                return

            connection_id = item.data(Qt.UserRole)
            if not connection_id:
                QMessageBox.warning(self, "警告", "连接ID无效")
                logger.warning(f"[CommunicationConfigWidget] 第{current_row}行的connection_id为空")
                return

            # 获取连接名称用于显示
            connection_name = item.text() or connection_id

            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除连接 '{connection_name}' 吗？\n\n注意：删除后将断开与该设备的通信。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # 默认选择No，防止误操作
            )

            if reply == QMessageBox.Yes:
                logger.info(f"[CommunicationConfigWidget] 开始删除连接: {connection_id}")
                
                # 先清除选择，避免删除后指向不存在的行
                self.connection_table.clearSelection()
                self.status_label.setText("正在删除...")
                
                # 执行删除操作
                success = self.connection_manager.remove_connection(connection_id)
                
                if success:
                    logger.info(f"[CommunicationConfigWidget] 连接删除成功: {connection_id}")
                    self.refresh_connections()
                    self.status_label.setText(f"连接 '{connection_name}' 已删除")
                    
                    # 如果还有其他连接，选择第一行
                    if self.connection_table.rowCount() > 0:
                        self.connection_table.selectRow(0)
                else:
                    error_msg = f"删除连接 '{connection_name}' 失败。\n可能原因：\n1. 连接不存在\n2. 连接正在使用中\n3. 系统资源不足"
                    logger.error(f"[CommunicationConfigWidget] 删除连接失败: {connection_id}")
                    QMessageBox.warning(self, "删除失败", error_msg)
                    self.status_label.setText("删除失败")
                    
                    # 恢复选择状态
                    if current_row < self.connection_table.rowCount():
                        self.connection_table.selectRow(current_row)
                    
        except Exception as e:
            error_msg = f"删除连接时发生错误: {str(e)}"
            logger.error(f"[CommunicationConfigWidget] {error_msg}", exc_info=True)
            QMessageBox.critical(self, "错误", error_msg)
            self.status_label.setText("删除出错")

    def refresh_connections(self):
        """刷新连接列表（增强版）
        
        改进内容:
        1. 添加异常处理，防止刷新过程中崩溃
        2. 保存当前选择状态，刷新后恢复
        3. 添加日志记录，便于调试
        """
        try:
            # 保存当前选中的连接ID
            selected_connection_id = None
            current_row = self.connection_table.currentRow()
            if current_row >= 0:
                item = self.connection_table.item(current_row, 0)
                if item:
                    selected_connection_id = item.data(Qt.UserRole)
            
            # 获取连接列表
            connections = self.connection_manager.get_all_connections()
            logger.debug(f"[CommunicationConfigWidget] 刷新连接列表: {len(connections)}个连接")
            
            # 设置表格行数
            self.connection_table.setRowCount(len(connections))
            
            # 填充数据
            new_selected_row = -1
            for i, conn in enumerate(connections):
                # 名称列
                name_item = QTableWidgetItem(conn.name)
                name_item.setData(Qt.UserRole, conn.id)
                self.connection_table.setItem(i, 0, name_item)
                
                # 协议类型列
                self.connection_table.setItem(i, 1, QTableWidgetItem(conn.protocol_type))
                
                # 状态列
                status_item = QTableWidgetItem(conn.status)
                if conn.is_connected:
                    status_item.setBackground(QBrush(QColor(46, 204, 113)))  # 绿色
                    status_item.setForeground(QBrush(QColor(255, 255, 255)))  # 白色文字
                else:
                    status_item.setBackground(QBrush(QColor(231, 76, 60)))  # 红色
                    status_item.setForeground(QBrush(QColor(255, 255, 255)))  # 白色文字
                self.connection_table.setItem(i, 2, status_item)
                
                # 统计列
                self.connection_table.setItem(i, 3, QTableWidgetItem(str(conn.send_count)))
                self.connection_table.setItem(i, 4, QTableWidgetItem(str(conn.receive_count)))
                self.connection_table.setItem(i, 5, QTableWidgetItem(str(conn.error_count)))
                
                # 检查是否是之前选中的连接
                if conn.id == selected_connection_id:
                    new_selected_row = i
            
            # 恢复选择状态
            if new_selected_row >= 0:
                self.connection_table.selectRow(new_selected_row)
            elif self.connection_table.rowCount() > 0:
                # 如果之前选中的连接不在了，选择第一行
                self.connection_table.selectRow(0)
            
            # 更新状态栏
            connected_count = sum(1 for c in connections if c.is_connected)
            self.status_label.setText(f"共{len(connections)}个连接，{connected_count}个已连接")
            
        except Exception as e:
            logger.error(f"[CommunicationConfigWidget] 刷新连接列表失败: {e}", exc_info=True)
            self.status_label.setText("刷新失败")

    def on_selection_changed(self):
        """选择变化时（增强版）"""
        try:
            current_row = self.connection_table.currentRow()
            if current_row >= 0:
                item = self.connection_table.item(current_row, 0)
                if item:
                    connection_id = item.data(Qt.UserRole)
                    connection = self.connection_manager.get_connection(connection_id)
                    if connection:
                        self.status_label.setText(f"选中: {connection.name} ({connection.status})")
                    else:
                        self.status_label.setText(f"选中: {item.text()} (连接已断开)")
                else:
                    self.status_label.setText("就绪")
            else:
                self.status_label.setText("就绪")
        except Exception as e:
            logger.debug(f"[CommunicationConfigWidget] 选择变化处理异常: {e}")
            self.status_label.setText("就绪")

    def on_connection_status_changed(self, connection):
        """连接状态变化回调（使用延迟刷新避免频繁更新）"""
        # 使用单次定时器延迟刷新，避免频繁更新UI导致卡顿
        if not hasattr(self, '_refresh_timer'):
            self._refresh_timer = QTimer(self)
            self._refresh_timer.setSingleShot(True)
            self._refresh_timer.timeout.connect(self.refresh_connections)
        
        # 如果定时器已经在运行，停止并重新启动
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()
        
        # 延迟100ms刷新，合并多次状态变化
        self._refresh_timer.start(100)


# 全局实例
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器实例（单例）
    
    使用ConnectionManager的__new__方法确保单例，
    此函数提供统一的获取入口。
    """
    # 直接创建实例，__new__方法会确保返回单例
    return ConnectionManager()


def get_communication_config_widget(parent=None) -> CommunicationConfigWidget:
    """获取通讯配置组件"""
    return CommunicationConfigWidget(parent)
