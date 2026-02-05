#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯配置对话框 - 重构版

架构改进：
- 对话框关闭只隐藏UI，不自动断开连接
- 协议实例由 CommunicationManager 长期维护
- 提供"断开所有"按钮让用户主动控制
- 重新打开对话框时恢复现有连接状态

Author: Vision System Team
Date: 2026-02-03
"""

import datetime
import logging

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
    """通讯配置对话框 - 重构版
    
    改进点：
    1. 关闭对话框只隐藏UI，不自动断开连接
    2. 协议实例长期维护，可重新关联
    3. 提供"断开所有"按钮主动控制
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通讯配置")
        self.setMinimumSize(700, 550)
        
        # 协议实例 - 长期维护，不因对话框关闭而清除
        self._protocol_instances = {}
        self._connections = {}  # 连接状态
        
        self._current_protocol = "TCP客户端"
        self._connect_buttons = {}
        self._send_test_buttons = {}
        self._is_closed = False
        self._receive_timer = None
        
        self._setup_ui()
        self._start_receive_timer()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 工具栏 - 添加断开所有按钮
        toolbar = QHBoxLayout()
        
        self._disconnect_all_btn = QPushButton("断开所有连接")
        self._disconnect_all_btn.setStyleSheet(
            "background-color: #f44336; color: white; padding: 8px 15px;"
        )
        self._disconnect_all_btn.clicked.connect(self._disconnect_all_async)
        toolbar.addWidget(self._disconnect_all_btn)
        
        toolbar.addStretch()
        
        # 状态标签
        self._status_label = QLabel("就绪")
        toolbar.addWidget(self._status_label)
        
        layout.addLayout(toolbar)

        # 选项卡
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._tcp_client_tab()
        self._tcp_server_tab()
        self._serial_tab()
        self._websocket_tab()
        self._http_tab()
        self._modbus_tab()

        # 日志区域
        self._setup_log_area(layout)

        # 按钮区域 - 只保留关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self._on_close_clicked)
        layout.addWidget(button_box)

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_close_clicked(self):
        """点击关闭按钮 - 只隐藏对话框"""
        logger.info("[CommunicationDialog] 用户点击关闭，隐藏对话框")
        self.hide()

    def closeEvent(self, event):
        """关闭事件 - 只隐藏，不断开连接"""
        logger.info("[CommunicationDialog] closeEvent - 隐藏对话框，保持连接")
        
        # 停止定时器
        if self._receive_timer:
            self._receive_timer.stop()
            self._receive_timer = None
        
        # 只隐藏，不接受关闭事件
        self.hide()
        event.ignore()

    def _disconnect_all_async(self):
        """异步断开所有连接 - 不阻塞UI"""
        logger.info("[CommunicationDialog] 用户请求断开所有连接")
        
        # 使用 QTimer 将断开操作延迟到事件循环，避免阻塞
        QTimer.singleShot(0, self._do_disconnect_all)

    def _do_disconnect_all(self):
        """实际执行断开操作"""
        logger.info(f"[CommunicationDialog] 开始断开 {len(self._protocol_instances)} 个连接")
        
        for protocol_name in list(self._protocol_instances.keys()):
            try:
                protocol = self._protocol_instances[protocol_name]
                if protocol:
                    logger.info(f"[CommunicationDialog] 断开 {protocol_name}...")
                    
                    # 清除回调
                    if hasattr(protocol, 'clear_callbacks'):
                        try:
                            protocol.clear_callbacks()
                        except:
                            pass
                    
                    # 断开连接 - 使用极短超时
                    if protocol_name == "TCP服务端":
                        try:
                            protocol.stop()
                        except:
                            pass
                    else:
                        try:
                            protocol.disconnect()
                        except:
                            pass
                    
                    logger.info(f"[CommunicationDialog] {protocol_name} 已断开")
            except Exception as e:
                logger.error(f"[CommunicationDialog] 断开 {protocol_name} 失败: {e}")
        
        # 清理字典
        self._protocol_instances.clear()
        self._connections.clear()
        
        # 更新UI
        self._update_all_button_states()
        self._add_log("所有连接已断开", "INFO")
        logger.info("[CommunicationDialog] 所有连接已断开")

    def _update_all_button_states(self):
        """更新所有按钮状态"""
        for protocol in ["TCP客户端", "TCP服务端", "串口", "WebSocket", "Modbus"]:
            connected = self._connections.get(protocol, False)
            self._update_button_state(protocol, connected)

    # ========== TCP客户端选项卡 ==========
    def _tcp_client_tab(self):
        """TCP客户端选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._create_tcp_client_widgets()
        layout.addWidget(self.tcp_client_group)

        self.tabs.addTab(tab, "TCP客户端")

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

    def _toggle_tcp_client(self):
        """切换TCP客户端连接"""
        if "TCP客户端" in self._connections and self._connections["TCP客户端"]:
            self._disconnect_tcp_client()
        else:
            self._connect_tcp_client()

    def _connect_tcp_client(self):
        """连接TCP客户端 - 非阻塞"""
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

        # 创建客户端
        client = TCPClient()
        
        # 使用 QTimer 延迟连接，避免阻塞UI
        QTimer.singleShot(0, lambda: self._do_tcp_connect(client, config))

    def _do_tcp_connect(self, client, config):
        """实际执行连接（在事件循环中）"""
        def on_connected():
            self._connections["TCP客户端"] = True
            QTimer.singleShot(0, lambda: self._update_button_state("TCP客户端", True))
            QTimer.singleShot(0, lambda: self._update_status("TCP客户端已连接"))
            QTimer.singleShot(0, lambda: self._add_log("TCP客户端连接成功!", "SUCCESS"))

        def on_disconnected():
            self._connections["TCP客户端"] = False
            QTimer.singleShot(0, lambda: self._update_button_state("TCP客户端", False))
            QTimer.singleShot(0, lambda: self._update_status("TCP客户端已断开"))
            QTimer.singleShot(0, lambda: self._add_log("TCP客户端已断开连接", "WARNING"))

        def on_error(msg):
            QTimer.singleShot(0, lambda: self._add_log(f"错误 [TCP客户端]: {msg}", "ERROR"))

        client.register_callback("on_connect", on_connected)
        client.register_callback("on_disconnect", on_disconnected)
        client.register_callback("on_error", on_error)

        # 连接（非阻塞）
        try:
            if client.connect(config):
                self._protocol_instances["TCP客户端"] = client
                self._connections["TCP客户端"] = True
                self._update_button_state("TCP客户端", True)
                self._update_status("TCP客户端已连接")
                self._add_log("TCP客户端连接成功!", "SUCCESS")
            else:
                self._add_log("连接失败，请检查地址和端口是否正确", "ERROR")
        except Exception as e:
            self._add_log(f"连接异常: {e}", "ERROR")

    def _disconnect_tcp_client(self):
        """断开TCP客户端 - 异步"""
        logger.info("[CommunicationDialog] 异步断开TCP客户端")
        QTimer.singleShot(0, self._do_disconnect_tcp_client)

    def _do_disconnect_tcp_client(self):
        """实际执行断开"""
        if "TCP客户端" in self._protocol_instances:
            try:
                protocol = self._protocol_instances["TCP客户端"]
                if hasattr(protocol, 'clear_callbacks'):
                    protocol.clear_callbacks()
                protocol.disconnect()
            except Exception as e:
                logger.debug(f"断开TCP客户端时出错: {e}")
        
        self._connections["TCP客户端"] = False
        self._update_button_state("TCP客户端", False)
        self._update_status("TCP客户端已断开")
        self._add_log("TCP客户端已断开", "INFO")

    def _send_tcp_test(self):
        """发送TCP测试数据"""
        if "TCP客户端" not in self._protocol_instances:
            self._add_log("TCP客户端未连接", "ERROR")
            return

        test_data = '{"test": "hello", "timestamp": "' + str(datetime.datetime.now()) + '"}'
        
        try:
            client = self._protocol_instances["TCP客户端"]
            if client.send(test_data):
                self._add_log(f"发送测试数据: {test_data}", "SEND")
            else:
                self._add_log("发送失败", "ERROR")
        except Exception as e:
            self._add_log(f"发送异常: {e}", "ERROR")

    # ========== 其他协议选项卡（简化版） ==========
    def _tcp_server_tab(self):
        """TCP服务端选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("TCP服务端配置 - 简化版"))
        
        btn = QPushButton("启动监听")
        btn.clicked.connect(lambda: self._add_log("TCP服务端功能待实现", "INFO"))
        layout.addWidget(btn)
        
        self.tabs.addTab(tab, "TCP服务端")

    def _serial_tab(self):
        """串口选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("串口配置 - 简化版"))
        
        btn = QPushButton("打开串口")
        btn.clicked.connect(lambda: self._add_log("串口功能待实现", "INFO"))
        layout.addWidget(btn)
        
        self.tabs.addTab(tab, "串口")

    def _websocket_tab(self):
        """WebSocket选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("WebSocket配置 - 简化版"))
        
        btn = QPushButton("连接WebSocket")
        btn.clicked.connect(lambda: self._add_log("WebSocket功能待实现", "INFO"))
        layout.addWidget(btn)
        
        self.tabs.addTab(tab, "WebSocket")

    def _http_tab(self):
        """HTTP选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("HTTP配置 - 简化版"))
        
        btn = QPushButton("测试HTTP")
        btn.clicked.connect(lambda: self._add_log("HTTP功能待实现", "INFO"))
        layout.addWidget(btn)
        
        self.tabs.addTab(tab, "HTTP")

    def _modbus_tab(self):
        """Modbus选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Modbus配置 - 简化版"))
        
        btn = QPushButton("连接Modbus")
        btn.clicked.connect(lambda: self._add_log("Modbus功能待实现", "INFO"))
        layout.addWidget(btn)
        
        self.tabs.addTab(tab, "Modbus")

    # ========== UI更新方法 ==========
    def _update_button_state(self, protocol, connected):
        """更新按钮状态"""
        if protocol not in self._connect_buttons:
            return

        btn = self._connect_buttons[protocol]
        if btn is None:
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
                if protocol in self._send_test_buttons:
                    self._send_test_buttons[protocol].setEnabled(True)
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
                    self._send_test_buttons[protocol].setEnabled(False)
        except Exception as e:
            logger.debug(f"更新按钮状态时出错: {e}")

    def _update_status(self, message):
        """更新状态栏"""
        try:
            self._status_label.setText(message)
        except:
            pass

    def _on_tab_changed(self, index):
        """切换选项卡"""
        self._current_protocol = self.tabs.tabText(index)
        self._update_status(f"当前: {self._current_protocol} - 就绪")

    # ========== 日志区域 ==========
    def _setup_log_area(self, layout):
        """设置日志区域"""
        log_group = QGroupBox("通讯日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)
        log_layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self._clear_log)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        log_layout.addLayout(btn_layout)

        layout.addWidget(log_group)

    def _add_log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        color_map = {
            "INFO": "#2196F3",
            "SUCCESS": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#f44336",
            "SEND": "#9C27B0",
            "RECV": "#00BCD4",
        }
        color = color_map.get(level, "#d4d4d4")

        try:
            self.log_text.append(
                f'<span style="color: {color};">{log_entry}</span>'
            )
        except:
            pass

    def _clear_log(self):
        """清空日志"""
        try:
            self.log_text.clear()
        except:
            pass
        self._add_log("日志已清空", "INFO")

    # ========== 接收数据检查 ==========
    def _start_receive_timer(self):
        """启动接收数据定时器"""
        self._receive_timer = QTimer(self)
        self._receive_timer.timeout.connect(self._check_received_data)
        self._receive_timer.start(100)

    def _check_received_data(self):
        """检查收到的数据 - 简化版"""
        if self._is_closed:
            return

        # 检查TCP客户端数据
        if "TCP客户端" in self._protocol_instances:
            try:
                client = self._protocol_instances["TCP客户端"]
                if client:
                    data = client.receive(timeout=0)
                    if data:
                        self._add_log(f"接收: {data}", "RECV")
            except:
                pass


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    dialog = CommunicationConfigDialog()
    dialog.show()
    sys.exit(app.exec_())
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
