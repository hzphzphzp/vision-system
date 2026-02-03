#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯配置对话框 - 无回调测试版

测试：完全移除回调机制，使用轮询检查状态
目的：确认问题是否在回调/QTimer
"""

import datetime
import logging

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger("CommunicationUI")


class ConnectWorker(QThread):
    """后台连接工作线程"""
    
    finished = pyqtSignal(bool, object)  # success, client
    
    def __init__(self, config):
        super().__init__()
        self._config = config
        
    def run(self):
        """在后台线程执行连接"""
        from core.communication import TCPClient
        
        logger.info("[ConnectWorker] 后台线程开始连接...")
        client = TCPClient()
        
        try:
            success = client.connect(self._config)
            logger.info(f"[ConnectWorker] 连接结果: {success}")
            self.finished.emit(success, client)
        except Exception as e:
            logger.error(f"[ConnectWorker] 连接异常: {e}")
            self.finished.emit(False, None)


class CommunicationConfigDialog(QDialog):
    """通讯配置对话框 - 无回调测试版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("通讯配置 - 无回调测试版")
        self.setMinimumSize(700, 550)
        
        self._protocol_instances = {}
        self._connections = {}
        self._connect_buttons = {}
        self._send_test_buttons = {}
        
        self._setup_ui()
        
        # 轮询定时器，替代回调
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_connection_status)
        self._poll_timer.start(500)  # 每500ms检查一次

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 警告标签
        warning = QLabel("⚠️ 无回调测试版：使用轮询替代回调")
        warning.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning)

        # TCP客户端选项卡
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self._tcp_client_tab()
        
        # 日志
        self._setup_log_area(layout)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)  # 直接接受，不清理
        layout.addWidget(button_box)

    def _tcp_client_tab(self):
        """TCP客户端选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("TCP客户端")
        grid = QGridLayout(group)

        grid.addWidget(QLabel("地址:"), 0, 0)
        self.tcp_host = QLineEdit("127.0.0.1")
        grid.addWidget(self.tcp_host, 0, 1)

        grid.addWidget(QLabel("端口:"), 1, 0)
        self.tcp_port = QSpinBox()
        self.tcp_port.setRange(1, 65535)
        self.tcp_port.setValue(8080)
        grid.addWidget(self.tcp_port, 1, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._connect_buttons["TCP客户端"] = QPushButton("连接")
        self._connect_buttons["TCP客户端"].clicked.connect(self._connect_tcp_client_simple)
        btn_layout.addWidget(self._connect_buttons["TCP客户端"])

        self._send_test_buttons["TCP客户端"] = QPushButton("发送测试")
        self._send_test_buttons["TCP客户端"].clicked.connect(self._send_tcp_test)
        self._send_test_buttons["TCP客户端"].setEnabled(False)
        btn_layout.addWidget(self._send_test_buttons["TCP客户端"])

        grid.addLayout(btn_layout, 2, 0, 1, 2)
        layout.addWidget(group)
        
        self.tabs.addTab(tab, "TCP客户端")

    def _connect_tcp_client_simple(self):
        """简化版连接 - 无回调"""
        from core.communication import TCPClient

        if "TCP客户端" in self._connections and self._connections["TCP客户端"]:
            # 断开连接
            self._add_log("断开连接...", "INFO")
            if "TCP客户端" in self._protocol_instances:
                try:
                    self._protocol_instances["TCP客户端"].disconnect()
                except:
                    pass
            self._connections["TCP客户端"] = False
            self._protocol_instances.pop("TCP客户端", None)
            self._update_button_state("TCP客户端", False)
            self._add_log("已断开", "INFO")
            return

        # 连接
        config = {
            "host": self.tcp_host.text(),
            "port": self.tcp_port.value(),
            "timeout": 2.0,
        }

        self._add_log(f"连接 {config['host']}:{config['port']}...", "INFO")
        
        # 在后台线程执行连接，避免阻塞UI
        self._connect_worker = ConnectWorker(config)
        self._connect_worker.finished.connect(self._on_connect_finished)
        self._connect_worker.start()
        
        self._add_log("连接中...", "INFO")
    
    def _on_connect_finished(self, success, client):
        """连接完成回调"""
        self._connect_worker = None
        
        if success and client:
            self._protocol_instances["TCP客户端"] = client
            self._connections["TCP客户端"] = True
            self._update_button_state("TCP客户端", True)
            self._add_log("连接成功!", "SUCCESS")
        else:
            self._add_log("连接失败", "ERROR")

    def _poll_connection_status(self):
        """轮询连接状态 - 替代回调"""
        # 检查TCP客户端状态
        if "TCP客户端" in self._protocol_instances:
            client = self._protocol_instances["TCP客户端"]
            if client and not client.is_connected():
                # 连接已断开
                self._connections["TCP客户端"] = False
                self._update_button_state("TCP客户端", False)
                self._add_log("检测到连接断开", "WARNING")

    def _send_tcp_test(self):
        """发送测试数据"""
        if "TCP客户端" not in self._protocol_instances:
            self._add_log("未连接", "ERROR")
            return

        test_data = '{"test": "hello"}'
        try:
            client = self._protocol_instances["TCP客户端"]
            if client.send(test_data):
                self._add_log(f"发送: {test_data}", "SEND")
            else:
                self._add_log("发送失败", "ERROR")
        except Exception as e:
            self._add_log(f"发送异常: {e}", "ERROR")

    def _update_button_state(self, protocol, connected):
        """更新按钮状态"""
        if protocol not in self._connect_buttons:
            return

        btn = self._connect_buttons[protocol]
        if connected:
            btn.setText("断开")
            btn.setStyleSheet("background-color: #f44336; color: white;")
            if protocol in self._send_test_buttons:
                self._send_test_buttons[protocol].setEnabled(True)
        else:
            btn.setText("连接")
            btn.setStyleSheet("background-color: #4CAF50; color: white;")
            if protocol in self._send_test_buttons:
                self._send_test_buttons[protocol].setEnabled(False)

    def _setup_log_area(self, layout):
        """设置日志区域"""
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(100)
        log_layout.addWidget(self.log_text)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_btn)

        layout.addWidget(log_group)

    def _add_log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        colors = {
            "INFO": "#2196F3",
            "SUCCESS": "#4CAF50",
            "ERROR": "#f44336",
            "SEND": "#9C27B0",
        }
        color = colors.get(level, "#d4d4d4")

        try:
            self.log_text.append(f'<span style="color: {color};">{log_entry}</span>')
        except:
            pass

    def closeEvent(self, event):
        """关闭事件 - 直接接受"""
        logger.info("[NoCallbackTest] closeEvent - 直接接受")
        # 停止轮询
        self._poll_timer.stop()
        event.accept()


# 保留CommunicationMonitorWidget供导入
class CommunicationMonitorWidget(QWidget):
    """通讯监控面板 - 占位符"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("通讯监控 - 无回调测试模式"))


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)
    dialog = CommunicationConfigDialog()
    dialog.show()
    sys.exit(app.exec_())
