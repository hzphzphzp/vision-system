#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据内容选择器组件

为发送数据工具提供数据选择功能：
- 文本输入框 + 选择按钮的组合
- 点击选择按钮弹出数据选择对话框
- 支持"模块名称.结果字段"格式

Author: Vision System Team
Date: 2026-02-05
"""

import logging
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from ui.data_selector import DataSelectorDialog

logger = logging.getLogger("DataContentSelector")


class DataContentSelector(QWidget):
    """数据内容选择器
    
    组合控件：文本输入框 + 选择按钮
    用于发送数据工具的"数据内容"参数
    """
    
    data_selected = pyqtSignal(str)  # 选中的数据内容（格式：模块名称.结果字段）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._available_modules: Dict[str, Dict[str, Any]] = {}
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 文本输入框
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("点击右侧按钮选择数据...")
        self.text_edit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: white;
                color: #2c3e50;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """
        )
        layout.addWidget(self.text_edit)
        
        # 选择按钮
        self.select_btn = QPushButton("选择...")
        self.select_btn.setMaximumWidth(60)
        self.select_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        )
        self.select_btn.clicked.connect(self._on_select_clicked)
        layout.addWidget(self.select_btn)
        
    def set_available_modules(self, modules: Dict[str, Dict[str, Any]]):
        """设置可用模块数据
        
        Args:
            modules: {模块名: {字段名: 值}}
        """
        self._available_modules = modules
        
    def set_text(self, text: str):
        """设置文本内容"""
        self.text_edit.setText(text)
        
    def get_text(self) -> str:
        """获取文本内容"""
        return self.text_edit.text()
        
    def _on_select_clicked(self):
        """选择按钮点击事件"""
        logger.debug(f"点击选择按钮，可用模块数量: {len(self._available_modules)}")
        logger.debug(f"可用模块: {list(self._available_modules.keys())}")
        
        if not self._available_modules:
            logger.warning("没有可用的数据模块")
            # 显示提示信息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "提示",
                "当前没有可用的数据模块。\n请先添加并执行上游模块。"
            )
            return
            
        # 显示数据选择对话框
        dialog = DataSelectorDialog(self._available_modules, self)
        if dialog.exec_() == DataSelectorDialog.Accepted:
            module_name, field_name = dialog.get_selection()
            if module_name and field_name:
                # 格式：模块名称.结果字段
                selected_data = f"{module_name}.{field_name}"
                self.text_edit.setText(selected_data)
                self.data_selected.emit(selected_data)
                logger.info(f"选择数据: {selected_data}")


class DataContentSelectorFactory:
    """数据内容选择器工厂"""
    
    @staticmethod
    def create_selector(available_modules: Dict[str, Dict[str, Any]] = None) -> DataContentSelector:
        """创建数据内容选择器
        
        Args:
            available_modules: 可用模块数据
            
        Returns:
            数据内容选择器实例
        """
        selector = DataContentSelector()
        if available_modules:
            selector.set_available_modules(available_modules)
        return selector
