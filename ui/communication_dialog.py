#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯配置对话框

提供通讯协议的配置和管理界面。

Author: Vision System Team
Date: 2026-01-13
"""

import datetime
import logging
import threading

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("CommunicationUI")


class CommunicationConfigDialog(QDialog):
    """通讯配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通讯配置")
        self.setMinimumSize(700, 550)
        self._connections = {}
        self._protocol_instances = {}
        self._logs = []
        self._current_protocol = "TCP客户端"
        self._connect_buttons = {}
        self._send_test_buttons = {}
        self._is_closed = False
        self._receive_timer = None
        self._setup_ui()
        self._start_receive_timer()

    def _start_receive_timer(self):
        """启动接收数据定时器"""
        self._receive_timer = QTimer(self)
        self._receive_timer.timeout.connect(self._check_received_data)
        self._receive_timer.start(100)  # 每100ms检查一次

    def _check_received_data(self):
        """检查收到的数据"""
        if self._is_closed:
            return

        for protocol_name, protocol in list(self._protocol_instances.items()):
            if (
                protocol_name not in self._connections
                or not self._connections[protocol_name]
            ):
                continue

            try:
                if protocol_name == "TCP客户端":
                    data = protocol.receive(timeout=0)
                    if data:
                        self._display_received_data(protocol_name, data)

                elif protocol_name == "TCP服务端":
                    client_id, data = protocol.receive_from(timeout=0.01)
                    if data:
                        self._display_received_data(
                            f"TCP服务端 [客户端{client_id}]", data
                        )

            except Exception as e:
                logger.debug(f"检查{protocol_name}数据时出错: {e}")

    def _display_received_data(self, protocol_name, data):
        """显示收到的数据"""
        try:
            if isinstance(data, bytes):
                text = data.decode("utf-8", errors="replace")
            else:
                text = str(data)
            self._add_log(f"接收 [{protocol_name}]: {text}", "RECV")
        except Exception as e:
            self._add_log(f"接收 [{protocol_name}]: 数据解析错误", "ERROR")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._tcp_client_tab()
        self._tcp_server_tab()
        self._serial_tab()
        self._websocket_tab()
        self._http_tab()
        self._modbus_tab()

        self._setup_log_area(layout)
        self._setup_status_bar(layout)

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        """切换选项卡"""
        self._current_protocol = self.tabs.tabText(index)
        if (
            not self._is_closed
            and hasattr(self, "status_label")
            and self.status_label is not None
        ):
            try:
                self.status_label.setText(
                    f"当前: {self._current_protocol} - 就绪"
                )
            except:
                pass

    def _is_valid(self):
        """检查对话框是否仍然有效"""
        return not self._is_closed and self.parent() is not None

    def _tcp_client_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._create_tcp_client_widgets()
        layout.addRow(self.tcp_client_group)

        self.tabs.addTab(tab, "TCP客户端")

    def _tcp_server_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._create_tcp_server_widgets()
        layout.addRow(self.tcp_server_group)

        self.tabs.addTab(tab, "TCP服务端")

    def _serial_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._create_serial_widgets()
        layout.addRow(self.serial_group)

        self.tabs.addTab(tab, "串口")

    def _websocket_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._create_websocket_widgets()
        layout.addRow(self.websocket_group)

        self.tabs.addTab(tab, "WebSocket")

    def _http_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._create_http_widgets()
        layout.addRow(self.http_group)

        self.tabs.addTab(tab, "HTTP")

    def _modbus_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._create_modbus_widgets()
        layout.addWidget(self.modbus_group)

        self._create_modbus_operation_widgets()
        layout.addWidget(self.modbus_operation_group)

        layout.addStretch()
        self.tabs.addTab(tab, "Modbus")

    def _create_tcp_client_widgets(self):
        """创建TCP客户端配置控件"""
        group = QGroupBox("TCP客户端")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("地址:"), 0, 0)
        self.tcp_host = QLineEdit("127.0.0.1")
        layout.addWidget(self.tcp_host, 0, 1)

        layout.addWidget(QLabel("端口:"), 1, 0)
        self.tcp_port = QSpinBox()
        self.tcp_port.setRange(1, 65535)
        self.tcp_port.setValue(8080)
        layout.addWidget(self.tcp_port, 1, 1)

        layout.addWidget(QLabel("超时(秒):"), 2, 0)
        self.tcp_timeout = QSpinBox()
        self.tcp_timeout.setRange(1, 300)
        self.tcp_timeout.setValue(10)
        layout.addWidget(self.tcp_timeout, 2, 1)

        layout.addWidget(QLabel("自动重连:"), 3, 0)
        self.tcp_auto_reconnect = QCheckBox()
        self.tcp_auto_reconnect.setChecked(True)
        layout.addWidget(self.tcp_auto_reconnect, 3, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["TCP客户端"] = QPushButton("连接")
        self._connect_buttons["TCP客户端"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["TCP客户端"].clicked.connect(
            self._toggle_tcp_client
        )
        btn_layout.addWidget(self._connect_buttons["TCP客户端"])

        self._send_test_buttons["TCP客户端"] = QPushButton("发送测试")
        self._send_test_buttons["TCP客户端"].setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        self._send_test_buttons["TCP客户端"].clicked.connect(
            self._send_tcp_test
        )
        self._send_test_buttons["TCP客户端"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["TCP客户端"])

        layout.addLayout(btn_layout, 4, 0, 1, 2)

        self.tcp_client_group = group

    def _create_tcp_server_widgets(self):
        """创建TCP服务端配置控件"""
        group = QGroupBox("TCP服务端")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("监听端口:"), 0, 0)
        self.tcp_server_port = QSpinBox()
        self.tcp_server_port.setRange(1, 65535)
        self.tcp_server_port.setValue(8080)
        layout.addWidget(self.tcp_server_port, 0, 1)

        layout.addWidget(QLabel(" backlog:"), 1, 0)
        self.tcp_server_backlog = QSpinBox()
        self.tcp_server_backlog.setRange(1, 100)
        self.tcp_server_backlog.setValue(5)
        layout.addWidget(self.tcp_server_backlog, 1, 1)

        layout.addWidget(QLabel("自动重连:"), 2, 0)
        self.tcp_server_auto_reconnect = QCheckBox()
        self.tcp_server_auto_reconnect.setChecked(True)
        layout.addWidget(self.tcp_server_auto_reconnect, 2, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["TCP服务端"] = QPushButton("监听")
        self._connect_buttons["TCP服务端"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["TCP服务端"].clicked.connect(
            self._toggle_tcp_server
        )
        btn_layout.addWidget(self._connect_buttons["TCP服务端"])

        self._send_test_buttons["TCP服务端"] = QPushButton("发送测试")
        self._send_test_buttons["TCP服务端"].setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
        """
        )
        self._send_test_buttons["TCP服务端"].clicked.connect(
            self._send_tcp_server_test
        )
        self._send_test_buttons["TCP服务端"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["TCP服务端"])

        layout.addLayout(btn_layout, 3, 0, 1, 2)

        self.tcp_server_group = group

    def _create_serial_widgets(self):
        """创建串口配置控件"""
        group = QGroupBox("串口")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("端口:"), 0, 0)
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.addItems(
            ["COM1", "COM2", "COM3", "COM4", "COM5"]
        )
        layout.addWidget(self.serial_port_combo, 0, 1)

        layout.addWidget(QLabel("波特率:"), 1, 0)
        self.serial_baudrate = QComboBox()
        self.serial_baudrate.addItems(
            ["9600", "19200", "38400", "57600", "115200", "230400", "460800"]
        )
        self.serial_baudrate.setCurrentText("115200")
        layout.addWidget(self.serial_baudrate, 1, 1)

        layout.addWidget(QLabel("自动重连:"), 2, 0)
        self.serial_auto_reconnect = QCheckBox()
        self.serial_auto_reconnect.setChecked(True)
        layout.addWidget(self.serial_auto_reconnect, 2, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["串口"] = QPushButton("连接")
        self._connect_buttons["串口"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["串口"].clicked.connect(self._toggle_serial)
        btn_layout.addWidget(self._connect_buttons["串口"])

        self._send_test_buttons["串口"] = QPushButton("发送测试")
        self._send_test_buttons["串口"].setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
        """
        )
        self._send_test_buttons["串口"].clicked.connect(self._send_serial_test)
        self._send_test_buttons["串口"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["串口"])

        layout.addLayout(btn_layout, 3, 0, 1, 2)

        self.serial_group = group

    def _create_websocket_widgets(self):
        """创建WebSocket配置控件"""
        group = QGroupBox("WebSocket")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("URL:"), 0, 0)
        self.ws_url = QLineEdit("ws://localhost:8080/ws")
        layout.addWidget(self.ws_url, 0, 1)

        layout.addWidget(QLabel("心跳:"), 1, 0)
        self.ws_heartbeat = QCheckBox()
        self.ws_heartbeat.setChecked(True)
        layout.addWidget(self.ws_heartbeat, 1, 1)

        layout.addWidget(QLabel("自动重连:"), 2, 0)
        self.ws_auto_reconnect = QCheckBox()
        self.ws_auto_reconnect.setChecked(True)
        layout.addWidget(self.ws_auto_reconnect, 2, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["WebSocket"] = QPushButton("连接")
        self._connect_buttons["WebSocket"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["WebSocket"].clicked.connect(
            self._toggle_websocket
        )
        btn_layout.addWidget(self._connect_buttons["WebSocket"])

        self._send_test_buttons["WebSocket"] = QPushButton("发送测试")
        self._send_test_buttons["WebSocket"].setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
        """
        )
        self._send_test_buttons["WebSocket"].clicked.connect(
            self._send_ws_test
        )
        self._send_test_buttons["WebSocket"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["WebSocket"])

        layout.addLayout(btn_layout, 3, 0, 1, 2)

        self.websocket_group = group

    def _create_http_widgets(self):
        """创建HTTP配置控件"""
        group = QGroupBox("HTTP")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("基础URL:"), 0, 0)
        self.http_base_url = QLineEdit("https://httpbin.org")
        layout.addWidget(self.http_base_url, 0, 1)

        layout.addWidget(QLabel("超时(秒):"), 1, 0)
        self.http_timeout = QSpinBox()
        self.http_timeout.setRange(1, 300)
        self.http_timeout.setValue(30)
        layout.addWidget(self.http_timeout, 1, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["HTTP"] = QPushButton("测试连接")
        self._connect_buttons["HTTP"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["HTTP"].clicked.connect(self._toggle_http)
        btn_layout.addWidget(self._connect_buttons["HTTP"])

        layout.addLayout(btn_layout, 2, 0, 1, 2)

        self.http_group = group

    def _create_modbus_widgets(self):
        """创建Modbus TCP配置控件"""
        group = QGroupBox("Modbus TCP配置")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("服务器地址:"), 0, 0)
        self.modbus_host = QLineEdit("127.0.0.1")
        layout.addWidget(self.modbus_host, 0, 1)

        layout.addWidget(QLabel("端口:"), 1, 0)
        self.modbus_port = QSpinBox()
        self.modbus_port.setRange(1, 65535)
        self.modbus_port.setValue(502)
        layout.addWidget(self.modbus_port, 1, 1)

        layout.addWidget(QLabel("单元ID:"), 2, 0)
        self.modbus_unit_id = QSpinBox()
        self.modbus_unit_id.setRange(1, 247)
        self.modbus_unit_id.setValue(1)
        layout.addWidget(self.modbus_unit_id, 2, 1)

        layout.addWidget(QLabel("超时(秒):"), 3, 0)
        self.modbus_timeout = QSpinBox()
        self.modbus_timeout.setRange(1, 60)
        self.modbus_timeout.setValue(5)
        layout.addWidget(self.modbus_timeout, 3, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["Modbus"] = QPushButton("连接")
        self._connect_buttons["Modbus"].setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self._connect_buttons["Modbus"].clicked.connect(self._toggle_modbus)
        btn_layout.addWidget(self._connect_buttons["Modbus"])

        self._connect_buttons["Modbus断开"] = QPushButton("断开")
        self._connect_buttons["Modbus断开"].setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
        """
        )
        self._connect_buttons["Modbus断开"].clicked.connect(
            self._disconnect_modbus
        )
        self._connect_buttons["Modbus断开"].setEnabled(False)
        btn_layout.addWidget(self._connect_buttons["Modbus断开"])

        layout.addLayout(btn_layout, 4, 0, 1, 2)

        self.modbus_group = group

    def _create_modbus_operation_widgets(self):
        """创建Modbus操作控件"""
        group = QGroupBox("Modbus操作")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(QLabel("功能:"), 0, 0)
        self.modbus_function = QComboBox()
        self.modbus_function.addItems(
            [
                "读线圈 (0x01)",
                "读离散输入 (0x02)",
                "读保持寄存器 (0x03)",
                "读输入寄存器 (0x04)",
                "写单个线圈 (0x05)",
                "写单个寄存器 (0x06)",
                "写多个线圈 (0x0F)",
                "写多个寄存器 (0x10)",
            ]
        )
        layout.addWidget(self.modbus_function, 0, 1)

        layout.addWidget(QLabel("起始地址:"), 1, 0)
        self.modbus_address = QSpinBox()
        self.modbus_address.setRange(0, 65535)
        self.modbus_address.setValue(0)
        layout.addWidget(self.modbus_address, 1, 1)

        layout.addWidget(QLabel("数量/值:"), 2, 0)
        self.modbus_count = QSpinBox()
        self.modbus_count.setRange(1, 2000)
        self.modbus_count.setValue(1)
        layout.addWidget(self.modbus_count, 2, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._send_test_buttons["Modbus"] = QPushButton("执行操作")
        self._send_test_buttons["Modbus"].setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        self._send_test_buttons["Modbus"].clicked.connect(
            self._execute_modbus_operation
        )
        self._send_test_buttons["Modbus"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["Modbus"])

        layout.addLayout(btn_layout, 3, 0, 1, 2)

        self.modbus_operation_group = group

    def _setup_log_area(self, parent_layout):
        """日志区域"""
        log_group = QGroupBox("通讯日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 15, 5, 5)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 11px;
                border: 1px solid #3c3c3c;
            }
        """
        )
        log_layout.addWidget(self.log_text)

        parent_layout.addWidget(log_group)

    def _setup_status_bar(self, parent_layout):
        """状态栏"""
        status_group = QGroupBox("连接状态")
        layout = QHBoxLayout(status_group)
        layout.setContentsMargins(10, 15, 10, 10)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()

        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self._clear_log)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """
        )
        close_btn.clicked.connect(self._on_close)
        btn_layout.addWidget(close_btn)

        parent_layout.addLayout(btn_layout)

    def _on_close(self):
        """关闭对话框（隐藏而不是销毁）"""
        self._is_closed = True
        if self._receive_timer:
            self._receive_timer.stop()
        self._disconnect_all()
        self.hide()

    def _disconnect_all(self):
        """断开所有连接"""
        for protocol_name in list(self._protocol_instances.keys()):
            try:
                if protocol_name == "TCP服务端":
                    self._protocol_instances[protocol_name].stop()
                else:
                    self._protocol_instances[protocol_name].disconnect()
            except Exception as e:
                logger.debug(f"断开 {protocol_name} 时出错: {e}")
        self._protocol_instances.clear()
        self._connections.clear()

    def _update_button_state(self, protocol, connected):
        """更新按钮状态"""
        if protocol not in self._connect_buttons:
            return

        btn = self._connect_buttons[protocol]
        if btn is None or btn.parent() is None:
            return

        try:
            if connected:
                btn.setText("断开")
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 4px;
                        font-weight: bold;
                        min-width: 100px;
                    }
                """
                )
            else:
                if protocol == "TCP服务端":
                    btn.setText("监听")
                else:
                    btn.setText("连接")
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 4px;
                        font-weight: bold;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """
                )

            if protocol in self._send_test_buttons:
                btn2 = self._send_test_buttons[protocol]
                if btn2 and btn2.parent():
                    btn2.setEnabled(connected)
        except:
            pass

    def _update_status(self, message):
        """更新状态栏"""
        if (
            not self._is_closed
            and hasattr(self, "status_label")
            and self.status_label is not None
        ):
            try:
                self.status_label.setText(message)
            except:
                pass

    def _toggle_tcp_client(self):
        """切换TCP客户端连接"""
        if "TCP客户端" in self._connections and self._connections["TCP客户端"]:
            self._disconnect_tcp_client()
        else:
            self._connect_tcp_client()

    def _connect_tcp_client(self):
        """连接TCP客户端"""
        from core.communication import TCPClient

        config = {
            "host": self.tcp_host.text(),
            "port": self.tcp_port.value(),
            "timeout": self.tcp_timeout.value(),
            "auto_reconnect": self.tcp_auto_reconnect.isChecked(),
        }

        self._add_log(
            f"正在连接TCP客户端: {config['host']}:{config['port']}...", "INFO"
        )

        client = TCPClient()

        def on_connected():
            self._connections["TCP客户端"] = True
            QTimer.singleShot(
                0, lambda: self._update_button_state("TCP客户端", True)
            )
            QTimer.singleShot(
                0, lambda: self._update_status("TCP客户端已连接")
            )
            QTimer.singleShot(
                0, lambda: self._add_log("TCP客户端连接成功!", "SUCCESS")
            )

        def on_disconnected():
            self._connections["TCP客户端"] = False
            QTimer.singleShot(
                0, lambda: self._update_button_state("TCP客户端", False)
            )
            QTimer.singleShot(
                0, lambda: self._update_status("TCP客户端已断开")
            )
            QTimer.singleShot(
                0, lambda: self._add_log("TCP客户端已断开连接", "WARNING")
            )

        def on_error(msg):
            QTimer.singleShot(
                0, lambda: self._add_log(f"错误 [TCP客户端]: {msg}", "ERROR")
            )

        client.register_callback("on_connect", on_connected)
        client.register_callback("on_disconnect", on_disconnected)
        client.register_callback("on_error", on_error)

        if client.connect(config):
            self._protocol_instances["TCP客户端"] = client
            self._connections["TCP客户端"] = True
            self._update_button_state("TCP客户端", True)
            self._update_status("TCP客户端已连接")
            self._add_log("TCP客户端连接成功!", "SUCCESS")
        else:
            self._add_log("连接失败，请检查地址和端口是否正确", "ERROR")

    def _disconnect_tcp_client(self):
        """断开TCP客户端"""
        if "TCP客户端" in self._protocol_instances:
            try:
                self._protocol_instances["TCP客户端"].disconnect()
            except Exception as e:
                logger.debug(f"断开TCP客户端时出错: {e}")
        self._connections["TCP客户端"] = False
        self._update_button_state("TCP客户端", False)
        self._update_status("TCP客户端已断开")
        self._add_log("TCP客户端已断开", "INFO")

    def _toggle_tcp_server(self):
        """切换TCP服务端连接"""
        from core.communication import TCPServer

        if "TCP服务端" in self._connections and self._connections["TCP服务端"]:
            self._stop_tcp_server()
        else:
            self._start_tcp_server()

    def _start_tcp_server(self):
        """启动TCP服务端"""
        from core.communication import TCPServer

        config = {
            "host": "0.0.0.0",
            "port": self.tcp_server_port.value(),
            "backlog": self.tcp_server_backlog.value(),
        }

        self._add_log(
            f"正在启动TCP服务端监听: 0.0.0.0:{config['port']}...", "INFO"
        )

        server = TCPServer()

        def on_client_connect(cid, addr):
            QTimer.singleShot(
                0,
                lambda: self._add_log(f"客户端 {cid} 已连接: {addr}", "INFO"),
            )

        def on_client_disconnect(cid):
            QTimer.singleShot(
                0, lambda: self._add_log(f"客户端 {cid} 已断开", "INFO")
            )

        def on_receive(cid, data):
            QTimer.singleShot(
                0,
                lambda: self._add_log(
                    f"接收 [TCP服务端]: [客户端{cid}]: {data}", "RECV"
                ),
            )

        def on_error(msg):
            QTimer.singleShot(
                0, lambda: self._add_log(f"错误 [TCP服务端]: {msg}", "ERROR")
            )

        server.register_callback("on_client_connect", on_client_connect)
        server.register_callback("on_client_disconnect", on_client_disconnect)
        server.register_callback("on_receive", on_receive)
        server.register_callback("on_error", on_error)

        if server.listen(config):
            self._protocol_instances["TCP服务端"] = server
            self._connections["TCP服务端"] = True
            self._update_button_state("TCP服务端", True)
            self._update_status("TCP服务端正在监听")
            self._add_log("TCP服务端启动成功!", "SUCCESS")
        else:
            self._add_log("启动监听失败", "ERROR")

    def _stop_tcp_server(self):
        """停止TCP服务端"""
        if "TCP服务端" in self._protocol_instances:
            try:
                self._protocol_instances["TCP服务端"].stop()
            except Exception as e:
                logger.debug(f"停止TCP服务端时出错: {e}")
        self._connections["TCP服务端"] = False
        self._update_button_state("TCP服务端", False)
        self._update_status("TCP服务端已停止监听")
        self._add_log("TCP服务端已停止监听", "INFO")

    def _toggle_serial(self):
        """切换串口连接"""
        from core.communication import SerialPort

        if "串口" in self._connections and self._connections["串口"]:
            self._close_serial()
        else:
            self._open_serial()

    def _open_serial(self):
        """打开串口"""
        from core.communication import SerialPort

        config = {
            "port": self.serial_port_combo.currentText(),
            "baudrate": int(self.serial_baudrate.currentText()),
            "timeout": 1.0,
            "auto_reconnect": self.serial_auto_reconnect.isChecked(),
        }

        self._add_log(
            f"正在打开串口: {config['port']} @ {config['baudrate']}bps", "INFO"
        )

        serial = SerialPort()

        def on_connected():
            self._connections["串口"] = True
            QTimer.singleShot(
                0, lambda: self._update_button_state("串口", True)
            )
            QTimer.singleShot(0, lambda: self._update_status("串口已打开"))
            QTimer.singleShot(
                0, lambda: self._add_log("串口打开成功!", "SUCCESS")
            )

        def on_disconnected():
            self._connections["串口"] = False
            QTimer.singleShot(
                0, lambda: self._update_button_state("串口", False)
            )
            QTimer.singleShot(0, lambda: self._update_status("串口已断开"))
            QTimer.singleShot(
                0, lambda: self._add_log("串口已断开", "WARNING")
            )

        def on_error(msg):
            QTimer.singleShot(
                0, lambda: self._add_log(f"错误 [串口]: {msg}", "ERROR")
            )

        serial.register_callback("on_connect", on_connected)
        serial.register_callback("on_disconnect", on_disconnected)
        serial.register_callback("on_error", on_error)

        if serial.connect(config):
            self._protocol_instances["串口"] = serial
            self._connections["串口"] = True
            self._update_button_state("串口", True)
            self._update_status("串口已打开")
            self._add_log("串口打开成功!", "SUCCESS")
        else:
            self._add_log("打开串口失败，请检查端口是否被占用", "ERROR")

    def _close_serial(self):
        """关闭串口"""
        if "串口" in self._protocol_instances:
            try:
                self._protocol_instances["串口"].disconnect()
            except Exception as e:
                logger.debug(f"关闭串口时出错: {e}")
        self._connections["串口"] = False
        self._update_button_state("串口", False)
        self._update_status("串口已断开")
        self._add_log("串口已断开", "INFO")

    def _toggle_websocket(self):
        """切换WebSocket连接"""
        from core.communication import WebSocketClient

        if "WebSocket" in self._connections and self._connections["WebSocket"]:
            self._disconnect_websocket()
        else:
            self._connect_websocket()

    def _connect_websocket(self):
        """连接WebSocket"""
        from core.communication import WebSocketClient

        config = {
            "url": self.ws_url.text(),
            "heartbeat": self.ws_heartbeat.isChecked(),
            "auto_reconnect": self.ws_auto_reconnect.isChecked(),
        }

        self._add_log(f"正在连接WebSocket: {config['url']}", "INFO")

        ws = WebSocketClient()

        def on_connected():
            self._connections["WebSocket"] = True
            QTimer.singleShot(
                0, lambda: self._update_button_state("WebSocket", True)
            )
            QTimer.singleShot(
                0, lambda: self._update_status("WebSocket已连接")
            )
            QTimer.singleShot(
                0, lambda: self._add_log("WebSocket连接成功!", "SUCCESS")
            )

        def on_disconnected():
            self._connections["WebSocket"] = False
            QTimer.singleShot(
                0, lambda: self._update_button_state("WebSocket", False)
            )
            QTimer.singleShot(
                0, lambda: self._update_status("WebSocket已断开")
            )
            QTimer.singleShot(
                0, lambda: self._add_log("WebSocket已断开连接", "WARNING")
            )

        def on_message(data):
            QTimer.singleShot(
                0, lambda: self._add_log(f"接收 [WebSocket]: {data}", "RECV")
            )

        def on_error(msg):
            QTimer.singleShot(
                0, lambda: self._add_log(f"错误 [WebSocket]: {msg}", "ERROR")
            )

        ws.register_callback("on_connect", on_connected)
        ws.register_callback("on_disconnect", on_disconnected)
        ws.register_callback("on_message", on_message)
        ws.register_callback("on_error", on_error)

        if ws.connect(config):
            self._protocol_instances["WebSocket"] = ws
            self._connections["WebSocket"] = True
            self._update_button_state("WebSocket", True)
            self._update_status("WebSocket已连接")
            self._add_log("WebSocket连接成功!", "SUCCESS")
        else:
            self._add_log("WebSocket连接失败", "ERROR")

    def _disconnect_websocket(self):
        """断开WebSocket"""
        if "WebSocket" in self._protocol_instances:
            try:
                self._protocol_instances["WebSocket"].disconnect()
            except Exception as e:
                logger.debug(f"断开WebSocket时出错: {e}")
        self._connections["WebSocket"] = False
        self._update_button_state("WebSocket", False)
        self._update_status("WebSocket已断开")
        self._add_log("WebSocket已断开", "INFO")

    def _toggle_http(self):
        """HTTP连接测试"""
        from core.communication import HTTPClient

        config = {
            "base_url": self.http_base_url.text(),
            "timeout": self.http_timeout.value(),
        }

        self._add_log(f"正在测试HTTP连接: {config['base_url']}", "INFO")

        http = HTTPClient()
        if http.connect(config):
            response = http.get("/get")
            if response["success"]:
                self._add_log(
                    f"HTTP连接成功，状态码: {response['status_code']}",
                    "SUCCESS",
                )
            else:
                self._add_log(
                    f"HTTP请求失败: {response.get('error', '未知错误')}",
                    "ERROR",
                )
            http.disconnect()
        else:
            self._add_log("HTTP连接失败", "ERROR")

    def _toggle_modbus(self):
        """切换Modbus连接"""
        if "Modbus" in self._connections and self._connections["Modbus"]:
            self._disconnect_modbus()
        else:
            self._connect_modbus()

    def _connect_modbus(self):
        """连接Modbus TCP服务器"""
        from core.communication import ModbusTCPClient

        config = {
            "host": self.modbus_host.text(),
            "port": self.modbus_port.value(),
            "timeout": self.modbus_timeout.value(),
            "unit_id": self.modbus_unit_id.value(),
        }

        self._add_log(
            f"正在连接Modbus TCP: {config['host']}:{config['port']}...", "INFO"
        )

        client = ModbusTCPClient()

        def on_connected():
            self._connections["Modbus"] = True
            QTimer.singleShot(
                0, lambda: self._update_button_state("Modbus", True)
            )
            QTimer.singleShot(0, lambda: self._update_status("Modbus已连接"))
            QTimer.singleShot(
                0, lambda: self._add_log("Modbus TCP连接成功!", "SUCCESS")
            )

        def on_disconnected():
            self._connections["Modbus"] = False
            QTimer.singleShot(
                0, lambda: self._update_button_state("Modbus", False)
            )
            QTimer.singleShot(0, lambda: self._update_status("Modbus已断开"))
            QTimer.singleShot(
                0, lambda: self._add_log("Modbus TCP已断开", "WARNING")
            )

        def on_error(msg):
            QTimer.singleShot(
                0, lambda: self._add_log(f"错误 [Modbus]: {msg}", "ERROR")
            )

        client.register_callback("on_connect", on_connected)
        client.register_callback("on_disconnect", on_disconnected)
        client.register_callback("on_error", on_error)

        if client.connect(config):
            self._protocol_instances["Modbus"] = client
            self._connections["Modbus"] = True
            self._update_button_state("Modbus", True)
            self._update_status("Modbus已连接")
            self._add_log("Modbus TCP连接成功!", "SUCCESS")
            self._connect_buttons["Modbus断开"].setEnabled(True)
            self._send_test_buttons["Modbus"].setEnabled(True)
        else:
            self._add_log("连接失败，请检查地址和端口", "ERROR")

    def _disconnect_modbus(self):
        """断开Modbus连接"""
        if "Modbus" in self._protocol_instances:
            try:
                self._protocol_instances["Modbus"].disconnect()
            except Exception as e:
                logger.debug(f"断开Modbus时出错: {e}")
        self._connections["Modbus"] = False
        self._update_button_state("Modbus", False)
        self._update_status("Modbus已断开")
        self._add_log("Modbus TCP已断开", "INFO")
        self._connect_buttons["Modbus断开"].setEnabled(False)
        self._send_test_buttons["Modbus"].setEnabled(False)

    def _execute_modbus_operation(self):
        """执行Modbus操作"""
        if "Modbus" not in self._protocol_instances:
            self._add_log("错误: 请先点击'连接'按钮连接Modbus服务器", "ERROR")
            return

        client = self._protocol_instances["Modbus"]

        if not hasattr(client, "_socket") or client._socket is None:
            self._add_log("错误: Modbus未连接，请重新连接", "ERROR")
            return

        address = self.modbus_address.value()
        count = self.modbus_count.value()
        func_idx = self.modbus_function.currentIndex()

        func_names = [
            "读线圈 (0x01)",
            "读离散输入 (0x02)",
            "读保持寄存器 (0x03)",
            "读输入寄存器 (0x04)",
            "写单个线圈 (0x05)",
            "写单个寄存器 (0x06)",
            "写多个线圈 (0x0F)",
            "写多个寄存器 (0x10)",
        ]

        self._add_log(
            f"执行: {func_names[func_idx]} 地址={address}, 数量={count}",
            "INFO",
        )

        try:
            if func_idx == 0:
                success, values = client.read_coils(address, count)
                if success:
                    self._add_log(f"读线圈 [{address}]: {values}", "SUCCESS")
                else:
                    self._add_log("读线圈失败: 无响应或超时", "ERROR")

            elif func_idx == 1:
                success, values = client.read_discrete_inputs(address, count)
                if success:
                    self._add_log(
                        f"读离散输入 [{address}]: {values}", "SUCCESS"
                    )
                else:
                    self._add_log("读离散输入失败: 无响应或超时", "ERROR")

            elif func_idx == 2:
                success, values = client.read_holding_registers(address, count)
                if success:
                    self._add_log(
                        f"读保持寄存器 [{address}]: {values}", "SUCCESS"
                    )
                else:
                    self._add_log("读保持寄存器失败: 无响应或超时", "ERROR")

            elif func_idx == 3:
                success, values = client.read_input_registers(address, count)
                if success:
                    self._add_log(
                        f"读输入寄存器 [{address}]: {values}", "SUCCESS"
                    )
                else:
                    self._add_log("读输入寄存器失败: 无响应或超时", "ERROR")

            elif func_idx == 4:
                value = count % 2
                success, addr = client.write_single_coil(address, value)
                if success:
                    self._add_log(f"写线圈 [{addr}] = {value}", "SUCCESS")
                else:
                    self._add_log("写线圈失败: 无响应或超时", "ERROR")

            elif func_idx == 5:
                success, addr = client.write_single_register(address, count)
                if success:
                    self._add_log(f"写寄存器 [{addr}] = {count}", "SUCCESS")
                else:
                    self._add_log("写寄存器失败: 无响应或超时", "ERROR")

            elif func_idx == 6:
                values = [1 if i % 2 == 0 else 0 for i in range(count)]
                success, num = client.write_multiple_coils(address, values)
                if success:
                    self._add_log(f"写多线圈 [{address}]: {num}个", "SUCCESS")
                else:
                    self._add_log("写多线圈失败: 无响应或超时", "ERROR")

            elif func_idx == 7:
                values = [i % 65536 for i in range(count)]
                success, num = client.write_multiple_registers(address, values)
                if success:
                    self._add_log(
                        f"写多寄存器 [{address}]: {num}个", "SUCCESS"
                    )
                else:
                    self._add_log("写多寄存器失败: 无响应或超时", "ERROR")

        except Exception as e:
            self._add_log(f"操作异常: {str(e)}", "ERROR")

    def _send_tcp_test(self):
        """发送TCP测试消息"""
        if "TCP客户端" in self._protocol_instances:
            msg = "Hello from Vision System!"
            try:
                if self._protocol_instances["TCP客户端"].send(msg):
                    self._add_log(f"发送: {msg}", "SEND")
            except Exception as e:
                self._add_log(f"发送失败: {e}", "ERROR")

    def _send_tcp_server_test(self):
        """发送TCP服务端测试消息"""
        if "TCP服务端" in self._protocol_instances:
            msg = "Broadcast message from Vision System!"
            try:
                count = self._protocol_instances["TCP服务端"].broadcast(msg)
                self._add_log(f"广播到 {count} 个客户端: {msg}", "SEND")
            except Exception as e:
                self._add_log(f"发送失败: {e}", "ERROR")

    def _send_serial_test(self):
        """发送串口测试消息"""
        if "串口" in self._protocol_instances:
            msg = "Hello Serial!\n"
            try:
                if self._protocol_instances["串口"].send(msg):
                    self._add_log(f"发送: Hello Serial!", "SEND")
            except Exception as e:
                self._add_log(f"发送失败: {e}", "ERROR")

    def _send_ws_test(self):
        """发送WebSocket测试消息"""
        if "WebSocket" in self._protocol_instances:
            msg = "Hello WebSocket!"
            try:
                if self._protocol_instances["WebSocket"].send(msg):
                    self._add_log(f"发送: {msg}", "SEND")
            except Exception as e:
                self._add_log(f"发送失败: {e}", "ERROR")

    def _add_log(self, message, level="INFO"):
        """添加日志"""
        if self._is_closed:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_entry)

        if len(self._logs) > 100:
            self._logs.pop(0)

        color_map = {
            "INFO": "#d4d4d4",
            "SUCCESS": "#4CAF50",
            "ERROR": "#f44336",
            "WARNING": "#ff9800",
            "RECV": "#2196F3",
            "SEND": "#9C27B0",
        }

        color = color_map.get(level, "#d4d4d4")

        if (
            not self._is_closed
            and hasattr(self, "log_text")
            and self.log_text is not None
        ):
            try:
                self.log_text.append(
                    f'<span style="color: {color};">{log_entry}</span>'
                )
                scroll_bar = self.log_text.verticalScrollBar()
                if scroll_bar:
                    scroll_bar.setValue(scroll_bar.maximum())
            except:
                pass

    def _clear_log(self):
        """清空日志"""
        self._logs.clear()
        if hasattr(self, "log_text") and self.log_text is not None:
            try:
                self.log_text.clear()
            except:
                pass
        self._add_log("日志已清空", "INFO")

    def closeEvent(self, event):
        """关闭事件"""
        self._is_closed = True
        if self._receive_timer:
            self._receive_timer.stop()
        self._disconnect_all()
        super().closeEvent(event)


class CommunicationMonitorWidget(QWidget):
    """通讯监控面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connections = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        toolbar = QHBoxLayout()

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(
            ["TCP客户端", "TCP服务端", "串口", "WebSocket", "HTTP"]
        )
        toolbar.addWidget(QLabel("协议:"))
        toolbar.addWidget(self.protocol_combo)

        self.connect_btn = QPushButton("连接")
        self.connect_btn.setStyleSheet(
            "background-color: #4CAF50; color: white;"
        )
        toolbar.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("断开")
        self.disconnect_btn.setStyleSheet(
            "background-color: #f44336; color: white;"
        )
        toolbar.addWidget(self.disconnect_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.log_frame = QFrame()
        self.log_frame.setFrameStyle(QFrame.StyledPanel)
        self.log_frame.setMinimumHeight(200)

        log_layout = QVBoxLayout(self.log_frame)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """
        )
        log_layout.addWidget(self.log_text)
        layout.addWidget(self.log_frame)

        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入要发送的消息...")
        input_layout.addWidget(self.message_input)

        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white;")
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] [{level}] {message}")

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = CommunicationConfigDialog()
    dialog.show()

    sys.exit(app.exec_())
