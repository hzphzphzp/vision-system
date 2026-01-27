#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强结果面板停靠窗口

Author: Vision System Team
Date: 2026-01-14
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QDockWidget, QTabWidget, QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal

from ui.enhanced_result_panel import EnhancedResultPanel, ResultDetailWidget, DataType
from ui.result_panel import ResultPanelWidget
from ui.theme import apply_theme

logger = logging.getLogger("EnhancedResultDockWidget")


class EnhancedResultDockWidget(QDockWidget):
    """增强结果面板停靠窗口"""
    
    clear_results = pyqtSignal()
    export_results = pyqtSignal(str)
    data_connection_requested = pyqtSignal(str, str, DataType)
    
    def __init__(self, parent=None):
        super().__init__("📊 结果", parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setObjectName("EnhancedResultPanel")
        
        apply_theme(self, "light")
        
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.enhanced_panel = EnhancedResultPanel()
        self.enhanced_panel.data_connection_requested.connect(
            lambda m, k, t: self.data_connection_requested.emit(m, k, t)
        )
        self.tabs.addTab(self.enhanced_panel, "📊 结果")
        
        self.traditional_panel = ResultPanelWidget()
        self.tabs.addTab(self.traditional_panel, "📋 日志")
        
        layout.addWidget(self.tabs)
        
        self.setWidget(self.main_widget)
        
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        self.setMinimumWidth(280)
        self.setMinimumHeight(200)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def add_result(self, result_data, category=""):
        """添加结果到增强面板"""
        self.enhanced_panel.add_result(result_data, category)
        self.tabs.setCurrentIndex(0)
    
    def add_info(self, message, details=None, tool_name=None):
        """添加信息（兼容旧接口）"""
        self.traditional_panel.add_info(message, details, tool_name)
        self.tabs.setCurrentIndex(1)
    
    def add_success(self, message, details=None, tool_name=None):
        """添加成功结果（兼容旧接口）"""
        self.traditional_panel.add_success(message, details, tool_name)
        self.tabs.setCurrentIndex(1)
    
    def add_warning(self, message, details=None, tool_name=None):
        """添加警告结果（兼容旧接口）"""
        self.traditional_panel.add_warning(message, details, tool_name)
        self.tabs.setCurrentIndex(1)
    
    def add_error(self, message, details=None, tool_name=None):
        """添加错误结果（兼容旧接口）"""
        self.traditional_panel.add_error(message, details, tool_name)
        self.tabs.setCurrentIndex(1)
    
    def get_panel(self):
        """获取增强面板"""
        return self.enhanced_panel
    
    def clear_all(self):
        """清空所有结果"""
        self.enhanced_panel.clear_results()
        self.traditional_panel.clear_results()
        self.clear_results.emit()
    
    def show_detail(self, result_data, category=""):
        """显示结果详情"""
        self.enhanced_panel.detail_widget.set_result(result_data, category)
    
    def set_available_modules(self, modules):
        """设置可用模块"""
        self.enhanced_panel.set_available_modules(modules)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dock = EnhancedResultDockWidget()
    dock.show()
    
    sys.exit(app.exec_())
