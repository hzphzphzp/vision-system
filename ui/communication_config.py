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
    """连接存储类（简化版，不使用文件）"""

    def __init__(self):
        self._connections: Dict[str, Dict] = {}

    def save_connections(self, connections: List[ProtocolConnection]) -> bool:
        """保存连接配置到内存"""
        try:
            for conn in connections:
                self._connections[conn.id] = {
                    "id": conn.id,
                    "name": conn.name,
                    "protocol_type": conn.protocol_type,
                    "config": conn.config,
                    "is_connected": conn.is_connected,
                    "status": conn.status,
                }
            return True
        except Exception as e:
            logger.error(f"保存连接失败: {e}")
            return False

    def load_connections(self) -> List[Dict]:
        """从内存加载连接配置"""
        return list(self._connections.values())


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
        self._connections: Dict[str, ProtocolConnection] = {}
        self._lock = threading.Lock()
        self._status_callback: Optional[Callable] = None
        self._storage = ConnectionStorage()
        self._pending_workers: Dict[str, ProtocolCreateWorker] = {}

    def set_status_callback(self, callback: Callable):
        """设置状态回调"""
        self._status_callback = callback

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
                del self._connections[connection_id]

        # 异步清理协议实例（不在锁内执行）
        if protocol_to_cleanup:
            def cleanup():
                try:
                    # 设置停止标志
                    if hasattr(protocol_to_cleanup, '_running'):
                        protocol_to_cleanup._running = False
                except Exception:
                    pass
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()

        # 异步保存配置
        self._save_connections_async()

        return conn_to_remove is not None

    def _save_connections_async(self):
        """异步保存连接配置"""
        def do_save():
            try:
                connections = self.get_all_connections()
                self._storage.save_connections(connections)
            except Exception as e:
                logger.error(f"保存连接失败: {e}")

        save_thread = threading.Thread(target=do_save, daemon=True)
        save_thread.start()

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
        """保存连接配置"""
        connections = self.get_all_connections()
        self._storage.save_connections(connections)


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

    def load_connection(self, connection_id: str):
        """加载连接配置"""
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
        self.connection_manager = ConnectionManager()
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

            # 异步添加连接
            if self.connection_manager.add_connection(connection):
                self.refresh_connections()
                QMessageBox.information(self, "提示", "连接已添加，正在后台建立连接...")
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
                self.refresh_connections()
                QMessageBox.information(self, "提示", "连接已更新，正在重新建立连接...")
            else:
                QMessageBox.warning(self, "警告", "更新连接失败")

    def delete_connection(self):
        """删除连接"""
        current_row = self.connection_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的连接")
            return

        connection_id = self.connection_table.item(current_row, 0).data(Qt.UserRole)

        reply = QMessageBox.question(
            self, "确认", "确定要删除这个连接吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 直接移除连接，不等待线程结束（避免UI阻塞）
            if self.connection_manager.remove_connection(connection_id):
                self.refresh_connections()
            else:
                QMessageBox.warning(self, "警告", "删除连接失败")

    def refresh_connections(self):
        """刷新连接列表"""
        connections = self.connection_manager.get_all_connections()
        self.connection_table.setRowCount(len(connections))

        for i, conn in enumerate(connections):
            name_item = QTableWidgetItem(conn.name)
            name_item.setData(Qt.UserRole, conn.id)
            self.connection_table.setItem(i, 0, name_item)
            self.connection_table.setItem(i, 1, QTableWidgetItem(conn.protocol_type))
            
            status_item = QTableWidgetItem(conn.status)
            if conn.is_connected:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.red)
            self.connection_table.setItem(i, 2, status_item)
            
            self.connection_table.setItem(i, 3, QTableWidgetItem(str(conn.send_count)))
            self.connection_table.setItem(i, 4, QTableWidgetItem(str(conn.receive_count)))
            self.connection_table.setItem(i, 5, QTableWidgetItem(str(conn.error_count)))

    def on_selection_changed(self):
        """选择变化时"""
        current_row = self.connection_table.currentRow()
        if current_row >= 0:
            connection_id = self.connection_table.item(current_row, 0).data(Qt.UserRole)
            connection = self.connection_manager.get_connection(connection_id)
            if connection:
                self.status_label.setText(f"选中: {connection.name} ({connection.status})")
        else:
            self.status_label.setText("就绪")

    def on_connection_status_changed(self, connection):
        """连接状态变化回调"""
        self.refresh_connections()


# 全局实例
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器实例"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_communication_config_widget(parent=None) -> CommunicationConfigWidget:
    """获取通讯配置组件"""
    return CommunicationConfigWidget(parent)
