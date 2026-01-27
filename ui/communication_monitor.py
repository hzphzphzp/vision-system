#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通信状态监控面板

显示通信连接状态和数据收发统计。

Author: Vision System Team
Date: 2026-01-19
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QHeaderView, QLabel, QFrame,
                              QProgressBar, QGroupBox, QGridLayout, QPushButton,
                              QComboBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush


class CommunicationMonitorPanel(QWidget):
    """通信状态监控面板"""
    
    connection_selected = pyqtSignal(str)  # 选择连接
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._comm_manager = None
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_status)
        self._refresh_timer.start(1000)  # 每秒刷新
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 标题
        title = QLabel("📡 通信监控")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        layout.addWidget(title)
        
        # 连接状态表格
        self.connection_table = QTableWidget(0, 5)
        self.connection_table.setHorizontalHeaderLabels([
            "名称", "协议", "状态", "收发", "设备ID"
        ])
        self.connection_table.horizontalHeader().setStretchLastSection(True)
        self.connection_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        layout.addWidget(self.connection_table)
        
        # 统计信息
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QGridLayout(stats_group)
        
        self.total_sent_label = QLabel("发送: 0")
        self.total_received_label = QLabel("接收: 0")
        self.active_connections_label = QLabel("活跃: 0")
        self.error_count_label = QLabel("错误: 0")
        
        for i, label in enumerate([self.total_sent_label, self.total_received_label, 
                                   self.active_connections_label, self.error_count_label]):
            label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    padding: 3px;
                }
            """)
            stats_layout.addWidget(label, i // 2, i % 2)
        
        layout.addWidget(stats_group)
        
        # 快速连接区域
        quick_group = QGroupBox("🔌 快速连接")
        quick_layout = QHBoxLayout(quick_group)
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["TCP客户端", "TCP服务端", "串口", "WebSocket", "Modbus TCP"])
        quick_layout.addWidget(self.protocol_combo)
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("地址")
        self.host_input.setMaximumWidth(100)
        quick_layout.addWidget(self.host_input)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("端口")
        self.port_input.setMaximumWidth(60)
        quick_layout.addWidget(self.port_input)
        
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        quick_layout.addWidget(self.connect_btn)
        
        layout.addWidget(quick_group)
        
        # 设置固定高度
        self.setMinimumHeight(300)
        self.setMaximumHeight(400)
    
    def set_communication_manager(self, manager):
        """设置通信管理器"""
        self._comm_manager = manager
    
    def _refresh_status(self):
        """刷新状态"""
        if not self._comm_manager:
            return
        
        try:
            connections = self._comm_manager.get_available_connections()
            self.connection_table.setRowCount(len(connections))
            
            total_sent = 0
            total_received = 0
            active_count = 0
            error_count = 0
            
            for row, conn in enumerate(connections):
                # 名称
                name_item = QTableWidgetItem(conn.get("name", ""))
                self.connection_table.setItem(row, 0, name_item)
                
                # 协议
                protocol_item = QTableWidgetItem(conn.get("protocol_type", "").upper())
                self.connection_table.setItem(row, 1, protocol_item)
                
                # 状态
                status = "已连接" if conn.get("connected") else "断开"
                status_item = QTableWidgetItem(status)
                if conn.get("connected"):
                    status_item.setBackground(QBrush(QColor(46, 204, 113)))
                else:
                    status_item.setBackground(QBrush(QColor(231, 76, 60)))
                self.connection_table.setItem(row, 2, status_item)
                
                # 收发统计
                stats = f"↑0 ↓0"
                stats_item = QTableWidgetItem(stats)
                self.connection_table.setItem(row, 3, stats_item)
                
                # 设备ID
                dev_id = str(conn.get("device_id", ""))
                self.connection_table.setItem(row, 4, QTableWidgetItem(dev_id))
                
                if conn.get("connected"):
                    active_count += 1
            
            # 更新统计标签
            self.active_connections_label.setText(f"活跃: {active_count}")
            
        except Exception as e:
            pass
    
    def get_selected_connection(self) -> Optional[str]:
        """获取选中的连接"""
        current_row = self.connection_table.currentRow()
        if current_row >= 0:
            return self.connection_table.item(current_row, 0).text()
        return None


class CommunicationStatusWidget(QWidget):
    """通信状态指示器（用于状态栏）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(10)
        
        # TCP状态指示
        self.tcp_indicator = self._create_indicator("TCP", "#3498db")
        self._layout.addWidget(self.tcp_indicator)
        
        # 串口状态指示
        self.serial_indicator = self._create_indicator("Serial", "#9b59b6")
        self._layout.addWidget(self.serial_indicator)
        
        # Modbus状态指示
        self.modbus_indicator = self._create_indicator("Modbus", "#e67e22")
        self._layout.addWidget(self.modbus_indicator)
        
        self._layout.addStretch()
    
    def _create_indicator(self, name: str, color: str) -> QLabel:
        """创建状态指示器"""
        indicator = QLabel(f"● {name}")
        indicator.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        return indicator
    
    def update_status(self, protocol_type: str, connected: bool):
        """更新状态"""
        color = "#2ecc71" if connected else "#e74c3c"
        indicator_map = {
            "tcp": self.tcp_indicator,
            "serial": self.serial_indicator,
            "modbus": self.modbus_indicator
        }
        
        if protocol_type.lower() in indicator_map:
            indicator = indicator_map[protocol_type.lower()]
            indicator.setText(f"● {protocol_type.upper()}")
            indicator.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
