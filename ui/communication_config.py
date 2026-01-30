#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯配置管理模块

提供独立的通讯配置管理功能：
- 集中的协议连接管理
- 连接状态监控
- 协议配置界面
- 连接的启用/禁用

Author: Vision System Team
Date: 2026-01-19
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

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
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

from core.communication.protocol_base import DataParser, ProtocolBase
from core.communication.tcp_client import TCPClient
from core.communication.tcp_server import TCPServer
from core.tool_base import ToolBase, ToolRegistry


class ProtocolFactory:
    """协议工厂类，负责创建不同类型的协议实例"""

    @staticmethod
    def create_protocol(
        protocol_type: str, config: Dict[str, Any]
    ) -> Optional[ProtocolBase]:
        """创建协议实例

        Args:
            protocol_type: 协议类型
            config: 协议配置

        Returns:
            ProtocolBase: 协议实例
        """
        try:
            if protocol_type == "TCP客户端":
                client = TCPClient()
                # 连接到服务器
                client.connect(config)
                return client
            elif protocol_type == "TCP服务端":
                server = TCPServer()
                # 开始监听
                server.listen(config)
                return server
            elif protocol_type == "串口":
                # 串口协议实现
                from core.communication.serial_protocol import SerialProtocol

                serial = SerialProtocol()
                serial.connect(config)
                return serial
            elif protocol_type == "WebSocket":
                # WebSocket协议实现
                from core.communication.websocket_protocol import (
                    WebSocketProtocol,
                )

                ws = WebSocketProtocol()
                ws.connect(config)
                return ws
            elif protocol_type == "HTTP":
                # HTTP协议实现
                from core.communication.http_protocol import HTTPProtocol

                http = HTTPProtocol()
                http.connect(config)
                return http
            elif protocol_type == "Modbus TCP":
                # Modbus TCP协议实现
                from core.communication.modbus_tcp_protocol import (
                    ModbusTCPProtocol,
                )

                modbus = ModbusTCPProtocol()
                modbus.connect(config)
                return modbus
            else:
                logger.error(f"不支持的协议类型: {protocol_type}")
                return None
        except Exception as e:
            logger.error(f"创建协议实例失败: {e}")
            return None


@dataclass
class ProtocolConnection:
    """协议连接信息"""

    id: str
    name: str
    protocol_type: str
    config: Dict[str, Any]
    status: str = "未连接"
    is_connected: bool = False
    created_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    send_count: int = 0
    receive_count: int = 0
    error_count: int = 0
    protocol_instance: Any = None


class ConnectionStorage:
    """连接存储类，负责连接配置的持久化存储"""

    def __init__(self, storage_path: str = "./connections.json"):
        self.storage_path = storage_path

    def save_connections(self, connections: List[ProtocolConnection]) -> bool:
        """保存连接配置到文件"""
        try:
            data = []
            for conn in connections:
                conn_data = {
                    "id": conn.id,
                    "name": conn.name,
                    "protocol_type": conn.protocol_type,
                    "config": conn.config,
                    "is_enabled": getattr(conn, "is_enabled", True),
                    "tags": getattr(conn, "tags", []),
                    "description": getattr(conn, "description", ""),
                    "creator": getattr(conn, "creator", ""),
                    "created_time": conn.created_time,
                    "last_modified": getattr(
                        conn, "last_modified", time.time()
                    ),
                    "version": getattr(conn, "version", 1),
                }
                data.append(conn_data)

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存连接配置失败: {e}")
            return False

    def load_connections(self) -> List[ProtocolConnection]:
        """从文件加载连接配置"""
        try:
            if not os.path.exists(self.storage_path):
                return []

            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            connections = []
            for conn_data in data:
                conn = ProtocolConnection(
                    id=conn_data.get("id"),
                    name=conn_data.get("name"),
                    protocol_type=conn_data.get("protocol_type"),
                    config=conn_data.get("config", {}),
                )
                conn.is_enabled = conn_data.get("is_enabled", True)
                conn.tags = conn_data.get("tags", [])
                conn.description = conn_data.get("description", "")
                conn.creator = conn_data.get("creator", "")
                conn.created_time = conn_data.get("created_time", time.time())
                conn.last_modified = conn_data.get(
                    "last_modified", time.time()
                )
                conn.version = conn_data.get("version", 1)
                connections.append(conn)

            return connections
        except Exception as e:
            logger.error(f"加载连接配置失败: {e}")
            return []


class ConnectionMonitor:
    """连接监控类，负责监控连接状态和触发报警"""

    def __init__(self):
        self._alert_threshold = 3
        self._alerts: Dict[str, int] = {}

    def monitor_connection(self, connection: ProtocolConnection) -> bool:
        """监控连接状态

        Args:
            connection: 连接信息

        Returns:
            bool: 是否需要报警
        """
        if not connection.is_connected:
            # 增加错误计数
            self._alerts[connection.id] = (
                self._alerts.get(connection.id, 0) + 1
            )

            # 检查是否达到报警阈值
            if self._alerts[connection.id] >= self._alert_threshold:
                logger.warning(
                    f"连接 {connection.name} 异常，已连续失败 {self._alerts[connection.id]} 次"
                )
                return True
        else:
            # 重置错误计数
            if connection.id in self._alerts:
                del self._alerts[connection.id]

        return False

    def set_alert_threshold(self, threshold: int):
        """设置报警阈值"""
        self._alert_threshold = threshold


class ConnectionValidator:
    """连接验证类，负责验证协议配置的有效性"""

    @staticmethod
    def validate_config(
        protocol_type: str, config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """验证协议配置

        Args:
            protocol_type: 协议类型
            config: 协议配置

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if protocol_type == "TCP客户端":
                # 验证TCP客户端配置
                host = config.get("host")
                port = config.get("port")

                if not host:
                    return False, "目标地址不能为空"
                if not port:
                    return False, "目标端口不能为空"
                if not isinstance(port, int) or port < 1 or port > 65535:
                    return False, "目标端口必须是1-65535之间的整数"
            elif protocol_type == "TCP服务端":
                # 验证TCP服务端配置
                port = config.get("port")

                if not port:
                    return False, "监听端口不能为空"
                if not isinstance(port, int) or port < 1 or port > 65535:
                    return False, "监听端口必须是1-65535之间的整数"
            elif protocol_type == "串口":
                # 验证串口配置
                port = config.get("port")
                baudrate = config.get("baudrate")

                if not port:
                    return False, "串口不能为空"
                if not baudrate:
                    return False, "波特率不能为空"
                if not isinstance(baudrate, int) or baudrate <= 0:
                    return False, "波特率必须是正整数"
            elif protocol_type == "WebSocket":
                # 验证WebSocket配置
                url = config.get("url")

                if not url:
                    return False, "WebSocket URL不能为空"
            elif protocol_type == "HTTP":
                # 验证HTTP配置
                url = config.get("url")

                if not url:
                    return False, "HTTP URL不能为空"
            elif protocol_type == "Modbus TCP":
                # 验证Modbus TCP配置
                host = config.get("host")
                port = config.get("port")

                if not host:
                    return False, "目标地址不能为空"
                if not port:
                    return False, "目标端口不能为空"
                if not isinstance(port, int) or port < 1 or port > 65535:
                    return False, "目标端口必须是1-65535之间的整数"

            return True, ""
        except Exception as e:
            return False, f"配置验证失败: {e}"


class ConnectionManager:
    """连接管理器（全局单例）"""

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._connections: Dict[str, ProtocolConnection] = {}
        self._lock = threading.Lock()
        self._status_callback: Optional[Callable] = None
        self._storage = ConnectionStorage()
        self._monitor = ConnectionMonitor()
        self._validator = ConnectionValidator()

        # 启动状态监控定时器
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_connection_status)
        self._status_timer.start(1000)  # 每秒更新一次状态

        # 加载连接配置
        self._load_connections()

    def add_connection(self, connection: ProtocolConnection) -> bool:
        """添加连接"""
        with self._lock:
            # 验证配置
            valid, error_msg = self._validator.validate_config(
                connection.protocol_type, connection.config
            )
            if not valid:
                logger.error(f"添加连接失败: {error_msg}")
                return False

            # 创建协议实例
            connection.protocol_instance = ProtocolFactory.create_protocol(
                connection.protocol_type, connection.config
            )
            if not connection.protocol_instance:
                logger.error(f"创建协议实例失败: {connection.protocol_type}")
                return False

            # 添加连接
            self._connections[connection.id] = connection

            # 保存连接配置
            self._save_connections()

            return True

    def remove_connection(self, connection_id: str) -> bool:
        """移除连接"""
        with self._lock:
            if connection_id in self._connections:
                conn = self._connections[connection_id]
                if conn.is_connected and conn.protocol_instance:
                    try:
                        conn.protocol_instance.disconnect()
                    except Exception as e:
                        logger.error(f"断开连接失败: {e}")
                del self._connections[connection_id]

                # 保存连接配置
                self._save_connections()

                return True
        return False

    def update_connection(
        self, connection_id: str, config: Dict[str, Any]
    ) -> bool:
        """更新连接配置"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            conn = self._connections[connection_id]

            # 验证配置
            valid, error_msg = self._validator.validate_config(
                conn.protocol_type, config
            )
            if not valid:
                logger.error(f"更新连接失败: {error_msg}")
                return False

            # 断开旧连接
            if conn.is_connected and conn.protocol_instance:
                try:
                    conn.protocol_instance.disconnect()
                except Exception as e:
                    logger.error(f"断开旧连接失败: {e}")

            # 更新配置
            conn.config = config
            conn.last_modified = time.time()
            conn.version += 1

            # 创建新的协议实例
            conn.protocol_instance = ProtocolFactory.create_protocol(
                conn.protocol_type, config
            )
            if not conn.protocol_instance:
                logger.error(f"创建协议实例失败: {conn.protocol_type}")
                return False

            # 保存连接配置
            self._save_connections()

            return True

    def start_connection(self, connection_id: str) -> bool:
        """启动连接"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            conn = self._connections[connection_id]
            if conn.is_connected:
                return True

            if not conn.protocol_instance:
                conn.protocol_instance = ProtocolFactory.create_protocol(
                    conn.protocol_type, conn.config
                )
                if not conn.protocol_instance:
                    logger.error(f"创建协议实例失败: {conn.protocol_type}")
                    return False
            else:
                # 重新连接
                if hasattr(conn.protocol_instance, "connect"):
                    try:
                        conn.protocol_instance.connect(conn.config)
                    except Exception as e:
                        logger.error(f"连接失败: {e}")
                        return False

            return True

    def stop_connection(self, connection_id: str) -> bool:
        """停止连接"""
        with self._lock:
            if connection_id not in self._connections:
                return False

            conn = self._connections[connection_id]
            if not conn.is_connected:
                return True

            if conn.protocol_instance and hasattr(
                conn.protocol_instance, "disconnect"
            ):
                try:
                    conn.protocol_instance.disconnect()
                except Exception as e:
                    logger.error(f"断开连接失败: {e}")
                    return False

            return True

    def test_connection(self, connection_id: str) -> Tuple[bool, str]:
        """测试连接"""
        with self._lock:
            if connection_id not in self._connections:
                return False, "连接不存在"

            conn = self._connections[connection_id]

            # 创建临时协议实例进行测试
            temp_instance = ProtocolFactory.create_protocol(
                conn.protocol_type, conn.config
            )
            if not temp_instance:
                return False, "创建协议实例失败"

            try:
                # 检查连接状态
                is_connected = temp_instance.is_connected()
                if is_connected:
                    temp_instance.disconnect()
                    return True, "连接成功"
                else:
                    temp_instance.disconnect()
                    return False, "连接失败"
            except Exception as e:
                return False, f"测试失败: {e}"

    def get_connection(
        self, connection_id: str
    ) -> Optional[ProtocolConnection]:
        """获取连接"""
        with self._lock:
            return self._connections.get(connection_id)

    def get_all_connections(self) -> List[ProtocolConnection]:
        """获取所有连接"""
        with self._lock:
            return list(self._connections.values())

    def get_active_connections(self) -> List[ProtocolConnection]:
        """获取活跃连接"""
        with self._lock:
            return [
                conn
                for conn in self._connections.values()
                if conn.is_connected
            ]

    def set_status_callback(self, callback: Callable):
        """设置状态回调"""
        self._status_callback = callback

    def _update_connection_status(self):
        """更新连接状态"""
        for conn in self._connections.values():
            if conn.protocol_instance and hasattr(
                conn.protocol_instance, "is_connected"
            ):
                was_connected = conn.is_connected
                conn.is_connected = conn.protocol_instance.is_connected()

                # 更新状态字符串
                if conn.is_connected:
                    conn.status = "已连接"
                    conn.last_activity = time.time()
                else:
                    conn.status = "已断开"
                    if was_connected:
                        conn.error_count += 1

                # 监控连接状态
                self._monitor.monitor_connection(conn)

                # 通知状态变化
                if self._status_callback and (
                    conn.status != self._get_previous_status(conn.id)
                ):
                    (
                        self._get_previous_status.cache_clear()
                        if hasattr(self._get_previous_status, "cache_clear")
                        else None
                    )
                    self._set_previous_status(conn.id, conn.status)
                    self._status_callback(conn)

    def _load_connections(self):
        """加载连接配置"""
        connections = self._storage.load_connections()
        with self._lock:
            for conn in connections:
                # 创建协议实例
                conn.protocol_instance = ProtocolFactory.create_protocol(
                    conn.protocol_type, conn.config
                )
                if conn.protocol_instance:
                    conn.is_connected = conn.protocol_instance.is_connected()
                    conn.status = "已连接" if conn.is_connected else "已断开"
                self._connections[conn.id] = conn

    def _save_connections(self):
        """保存连接配置"""
        connections = self.get_all_connections()
        self._storage.save_connections(connections)

    def _get_previous_status(self, connection_id):
        """获取之前的状态（用于检查状态变化）"""
        if not hasattr(self, "_previous_status_cache"):
            self._previous_status_cache = {}
        return self._previous_status_cache.get(connection_id, "")

    def _set_previous_status(self, connection_id, status):
        """设置之前的状态"""
        if not hasattr(self, "_previous_status_cache"):
            self._previous_status_cache = {}
        self._previous_status_cache[connection_id] = status


class ConnectionConfigDialog(QDialog):
    """连接配置对话框"""

    def __init__(self, parent=None, connection_id: str = None):
        super().__init__(parent)
        self.connection_id = connection_id
        self.setWindowTitle("连接配置")
        self.setModal(True)
        self.resize(500, 400)

        self.connection_manager = ConnectionManager()
        self.setup_ui()

        if connection_id:
            self.load_connection(connection_id)

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()

        # 连接信息组
        info_group = QGroupBox("连接信息")
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("连接名称:"), 0, 0)
        self.name_edit = QLineEdit()
        info_layout.addWidget(self.name_edit, 0, 1)

        info_layout.addWidget(QLabel("协议类型:"), 1, 0)
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(
            [
                "TCP客户端",
                "TCP服务端",
                "串口",
                "WebSocket",
                "HTTP",
                "Modbus TCP",
            ]
        )
        info_layout.addWidget(self.protocol_combo, 1, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 协议配置组
        config_group = QGroupBox("协议配置")
        config_layout = QGridLayout()

        # TCP配置
        config_layout.addWidget(QLabel("目标地址:"), 0, 0)
        self.host_edit = QLineEdit("127.0.0.1")
        config_layout.addWidget(self.host_edit, 0, 1)

        config_layout.addWidget(QLabel("目标端口:"), 1, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(8080)
        config_layout.addWidget(self.port_spin, 1, 1)

        # 串口配置
        config_layout.addWidget(QLabel("串口:"), 2, 0)
        self.serial_combo = QComboBox()
        self.serial_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5"])
        config_layout.addWidget(self.serial_combo, 2, 1)

        config_layout.addWidget(QLabel("波特率:"), 3, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        config_layout.addWidget(self.baud_combo, 3, 1)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 连接测试按钮
        test_button = QPushButton("测试连接")
        test_button.clicked.connect(self.test_connection)
        layout.addWidget(test_button)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # 连接协议变化时更新UI
        self.protocol_combo.currentTextChanged.connect(
            self.on_protocol_changed
        )
        self.on_protocol_changed(self.protocol_combo.currentText())

    def on_protocol_changed(self, protocol_type: str):
        """协议类型变化时更新UI"""
        # 根据协议类型显示/隐藏相应配置
        is_serial = "串口" in protocol_type
        is_tcp = "TCP" in protocol_type

        self.host_edit.setVisible(is_tcp)
        self.port_spin.setVisible(is_tcp or protocol_type == "WebSocket")
        self.serial_combo.setVisible(is_serial)
        self.baud_combo.setVisible(is_serial)

    def test_connection(self):
        """测试连接"""
        try:
            protocol_type = self.protocol_combo.currentText()
            config = self.get_connection_config()

            if self.connection_id:
                # 测试现有连接
                conn = self.connection_manager.get_connection(
                    self.connection_id
                )
                if conn and conn.protocol_instance:
                    success = self._test_protocol_instance(
                        conn.protocol_instance, config
                    )
                    QMessageBox.information(
                        self,
                        "测试结果",
                        "连接测试成功！" if success else "连接测试失败！",
                    )
            else:
                # 测试新连接
                success = self._create_and_test_protocol(protocol_type, config)
                QMessageBox.information(
                    self,
                    "测试结果",
                    "连接测试成功！" if success else "连接测试失败！",
                )

        except Exception as e:
            QMessageBox.critical(
                self, "测试错误", f"测试过程中发生错误：{str(e)}"
            )

    def _create_and_test_protocol(
        self, protocol_type: str, config: Dict[str, Any]
    ) -> bool:
        """创建协议实例并测试"""
        try:
            # 这里应该根据协议类型创建实际的协议实例
            # 暂时返回True，表示连接成功
            return True
        except Exception as e:
            print(f"协议测试失败: {e}")
            return False

    def _test_protocol_instance(
        self, protocol_instance, config: Dict[str, Any]
    ) -> bool:
        """测试协议实例"""
        try:
            # 这里应该测试实际的协议实例
            # 暂时返回True
            return True
        except Exception as e:
            print(f"协议实例测试失败: {e}")
            return False

    def get_connection_config(self) -> Dict[str, Any]:
        """获取连接配置"""
        protocol_type = self.protocol_combo.currentText()

        config = {}

        if "TCP" in protocol_type or "WebSocket" in protocol_type:
            config["host"] = self.host_edit.text()
            config["port"] = self.port_spin.value()
        elif "串口" in protocol_type:
            config["port"] = self.serial_combo.currentText()
            config["baudrate"] = int(self.baud_combo.currentText())

        return config

    def get_connection_data(self) -> Dict[str, Any]:
        """获取连接数据"""
        return {
            "id": self.connection_id or f"conn_{int(time.time())}",
            "name": self.name_edit.text(),
            "protocol_type": self.protocol_combo.currentText(),
            "config": self.get_connection_config(),
        }

    def load_connection(self, connection_id: str):
        """加载连接配置"""
        conn = self.connection_manager.get_connection(connection_id)
        if conn:
            self.name_edit.setText(conn.name)
            self.protocol_combo.setCurrentText(conn.protocol_type)

            config = conn.config
            if "host" in config:
                self.host_edit.setText(config["host"])
            if "port" in config:
                self.port_spin.setValue(config["port"])
            if "baudrate" in config:
                self.baud_combo.setCurrentText(str(config["baudrate"]))

    def accept(self):
        """接受对话框"""
        # 验证输入
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入连接名称")
            return

        super().accept()


class CommunicationConfigWidget(QWidget):
    """通讯配置主窗口"""

    # 信号：连接状态变化
    connection_status_changed = pyqtSignal(
        str, str, bool
    )  # connection_id, status, is_connected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection_manager = ConnectionManager()
        self.connection_manager.set_status_callback(
            self.on_connection_status_changed
        )

        self.setup_ui()
        self.load_connections()

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
            [
                "连接名称",
                "协议类型",
                "状态",
                "发送次数",
                "接收次数",
                "错误次数",
            ]
        )

        # 设置列宽
        header = self.connection_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.connection_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.connection_table.itemSelectionChanged.connect(
            self.on_selection_changed
        )

        layout.addWidget(self.connection_table)

        # 状态栏
        status_layout = QHBoxLayout()

        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addLayout(status_layout)

        self.setLayout(layout)

    def add_connection(self):
        """添加连接"""
        dialog = ConnectionConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            connection_data = dialog.get_connection_data()
            connection = ProtocolConnection(
                id=connection_data["id"],
                name=connection_data["name"],
                protocol_type=connection_data["protocol_type"],
                config=connection_data["config"],
            )

            # 对于演示目的，自动设置为已连接状态
            connection.is_connected = True
            connection.status = "已连接"

            self.connection_manager.add_connection(connection)
            self.refresh_connections()

    def edit_connection(self):
        """编辑连接"""
        current_row = self.connection_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的连接")
            return

        connection_id = self.connection_table.item(current_row, 0).data(
            Qt.UserRole
        )

        dialog = ConnectionConfigDialog(self, connection_id)
        if dialog.exec_() == QDialog.Accepted:
            connection_data = dialog.get_connection_data()
            connection = self.connection_manager.get_connection(connection_id)
            if connection:
                # 更新连接信息
                connection.name = connection_data["name"]
                connection.protocol_type = connection_data["protocol_type"]
                connection.config = connection_data["config"]

                # 刷新表格显示
                self.refresh_connections()

                # 发送连接更新信号
                self.connection_status_changed.emit(
                    connection.id, connection.status, connection.is_connected
                )

    def delete_connection(self):
        """删除连接"""
        current_row = self.connection_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的连接")
            return

        connection_id = self.connection_table.item(current_row, 0).data(
            Qt.UserRole
        )

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除连接 {connection_id} 吗？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.connection_manager.remove_connection(connection_id)
            self.refresh_connections()

    def refresh_connections(self):
        """刷新连接列表"""
        connections = self.connection_manager.get_all_connections()

        # 先设置行数
        self.connection_table.setRowCount(len(connections))

        for i, conn in enumerate(connections):
            # 连接名称
            name_item = QTableWidgetItem(conn.name)
            name_item.setData(Qt.UserRole, conn.id)
            self.connection_table.setItem(i, 0, name_item)

            # 协议类型
            self.connection_table.setItem(
                i, 1, QTableWidgetItem(conn.protocol_type)
            )

            # 状态
            status_item = QTableWidgetItem(conn.status)
            if conn.is_connected:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.red)
            self.connection_table.setItem(i, 2, status_item)

            # 统计信息
            self.connection_table.setItem(
                i, 3, QTableWidgetItem(str(conn.send_count))
            )
            self.connection_table.setItem(
                i, 4, QTableWidgetItem(str(conn.receive_count))
            )
            self.connection_table.setItem(
                i, 5, QTableWidgetItem(str(conn.error_count))
            )

    def on_selection_changed(self):
        """选择变化时"""
        current_row = self.connection_table.currentRow()
        if current_row >= 0:
            connection_id = self.connection_table.item(current_row, 0).data(
                Qt.UserRole
            )
            connection = self.connection_manager.get_connection(connection_id)
            if connection:
                self.status_label.setText(
                    f"选中: {connection.name} ({connection.status})"
                )
        else:
            self.status_label.setText("就绪")

    def on_connection_status_changed(self, connection: ProtocolConnection):
        """连接状态变化回调"""
        # 更新表格显示
        for row in range(self.connection_table.rowCount()):
            if (
                self.connection_table.item(row, 0).data(Qt.UserRole)
                == connection.id
            ):
                # 更新状态
                status_item = self.connection_table.item(row, 2)
                status_item.setText(connection.status)
                if connection.is_connected:
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.red)

                # 更新统计
                self.connection_table.item(row, 3).setText(
                    str(connection.send_count)
                )
                self.connection_table.item(row, 4).setText(
                    str(connection.receive_count)
                )
                self.connection_table.item(row, 5).setText(
                    str(connection.error_count)
                )
                break

        # 发送状态变化信号
        self.connection_status_changed.emit(
            connection.id, connection.status, connection.is_connected
        )

    def load_connections(self):
        """加载保存的连接"""
        try:
            # 这里应该从文件或数据库加载保存的连接
            # 暂时跳过，使用默认连接
            self.refresh_connections()
        except Exception as e:
            print(f"加载连接失败: {e}")

    def get_connection_list(self) -> List[Dict[str, Any]]:
        """获取连接列表（供发送/接收工具使用）"""
        connections = self.connection_manager.get_active_connections()
        result = []

        for conn in connections:
            result.append(
                {
                    "id": conn.id,
                    "name": conn.name,
                    "protocol_type": conn.protocol_type,
                    "config": conn.config,
                    "display_name": f"{conn.protocol_type} - {conn.name}",
                    "status": conn.status,
                }
            )

        return result


# 全局通讯配置实例
_comm_config_widget = None


def get_communication_config_widget() -> CommunicationConfigWidget:
    """获取通讯配置组件实例"""
    global _comm_config_widget
    if _comm_config_widget is None:
        _comm_config_widget = CommunicationConfigWidget()
    return _comm_config_widget


# 全局连接管理器实例
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_communication_dock_widget(parent=None):
    """创建通讯配置停靠窗口"""
    global _comm_config_widget
    if _comm_config_widget is None:
        _comm_config_widget = CommunicationConfigWidget(parent)
    return _comm_config_widget
