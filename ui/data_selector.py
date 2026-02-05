#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据选择器模块

提供"模块名称.结果字段"格式的数据选择功能：
- 支持搜索和筛选
- 树形结构显示模块和字段
- 中文字段名显示

Author: Vision System Team
Date: 2026-02-05
"""

import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

logger = logging.getLogger("DataSelector")


class DataSelectorDialog(QDialog):
    """数据选择对话框
    
    支持"模块名称.结果字段"格式的数据选择
    """
    
    data_selected = pyqtSignal(str, str)  # 模块名, 字段名
    
    def __init__(self, available_modules: Dict[str, Dict[str, Any]], parent=None):
        """
        初始化数据选择对话框
        
        Args:
            available_modules: {模块名: {字段名: 值}}
            parent: 父窗口
        """
        super().__init__(parent)
        self.available_modules = available_modules
        self.selected_module = ""
        self.selected_field = ""
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("选择数据")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("选择要发送的数据")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索模块或字段...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # 数据树
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["模块/字段", "值预览"])
        self.data_tree.setAlternatingRowColors(True)
        self.data_tree.itemClicked.connect(self._on_item_selected)
        self.data_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 设置列宽
        self.data_tree.setColumnWidth(0, 250)
        self.data_tree.setColumnWidth(1, 200)
        
        # 填充数据
        self._populate_tree()
        
        layout.addWidget(self.data_tree)
        
        # 当前选择显示
        self.selection_label = QLabel("当前选择: 无")
        self.selection_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        layout.addWidget(self.selection_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self._on_ok)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def _populate_tree(self):
        """填充数据树"""
        self.data_tree.clear()
        
        for module_name, fields in self.available_modules.items():
            # 创建模块节点
            module_item = QTreeWidgetItem([module_name, ""])
            module_item.setFont(0, QFont("Microsoft YaHei", 9, QFont.Bold))
            module_item.setData(0, Qt.UserRole, {"type": "module", "name": module_name})
            
            # 添加字段子节点
            for field_name, value in fields.items():
                # 翻译字段名
                display_name = self._translate_field_name(field_name)
                
                # 值预览（截断长文本）
                value_str = str(value)
                if len(value_str) > 30:
                    value_str = value_str[:27] + "..."
                
                field_item = QTreeWidgetItem([f"{display_name} ({field_name})", value_str])
                field_item.setData(0, Qt.UserRole, {
                    "type": "field",
                    "module": module_name,
                    "field": field_name
                })
                field_item.setToolTip(0, f"{module_name}.{field_name}")
                field_item.setToolTip(1, str(value))
                
                module_item.addChild(field_item)
            
            self.data_tree.addTopLevelItem(module_item)
            module_item.setExpanded(True)
            
    def _on_search(self, text: str):
        """搜索过滤"""
        text = text.lower()
        
        for i in range(self.data_tree.topLevelItemCount()):
            module_item = self.data_tree.topLevelItem(i)
            module_name = module_item.text(0).lower()
            module_match = text in module_name
            
            # 检查子节点
            has_visible_child = False
            for j in range(module_item.childCount()):
                field_item = module_item.child(j)
                field_text = field_item.text(0).lower()
                field_match = text in field_text
                
                field_item.setHidden(not field_match and not module_match)
                if field_match:
                    has_visible_child = True
            
            # 如果模块名匹配或有匹配的子节点，显示模块
            module_item.setHidden(not module_match and not has_visible_child)
            
    def _on_item_selected(self, item: QTreeWidgetItem):
        """节点选择"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
            
        if data.get("type") == "field":
            self.selected_module = data.get("module", "")
            self.selected_field = data.get("field", "")
            self.selection_label.setText(f"当前选择: {self.selected_module}.{self.selected_field}")
            self.ok_button.setEnabled(True)
        else:
            self.selection_label.setText("当前选择: 无（请选择具体字段）")
            self.ok_button.setEnabled(False)
            
    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        """节点双击"""
        data = item.data(0, Qt.UserRole)
        if data and data.get("type") == "field":
            self.selected_module = data.get("module", "")
            self.selected_field = data.get("field", "")
            self._on_ok()
            
    def _on_ok(self):
        """确定按钮"""
        if self.selected_module and self.selected_field:
            self.data_selected.emit(self.selected_module, self.selected_field)
            self.accept()
            
    def get_selection(self) -> tuple:
        """获取选择结果"""
        return self.selected_module, self.selected_field
        
    @staticmethod
    def _translate_field_name(field_name: str) -> str:
        """将字段名翻译为中文"""
        translations = {
            # 通用字段
            "status": "状态",
            "result": "结果",
            "message": "消息",
            "error": "错误",
            "confidence": "置信度",
            "score": "分数",
            "value": "数值",
            "count": "数量",
            "index": "索引",
            "id": "编号",
            "name": "名称",
            "type": "类型",
            "category": "类别",
            "label": "标签",
            "timestamp": "时间戳",
            
            # 图像相关
            "width": "width",
            "height": "height",
            "channels": "通道数",
            "format": "格式",
            "size": "大小",
            "resolution": "分辨率",
            
            # 位置相关
            "x": "X坐标",
            "y": "Y坐标",
            "z": "Z坐标",
            "position": "位置",
            "center": "中心点",
            "top": "顶部",
            "bottom": "底部",
            "left": "左侧",
            "right": "右侧",
            
            # 尺寸相关
            "radius": "半径",
            "diameter": "直径",
            "area": "面积",
            "perimeter": "周长",
            "length": "长度",
            "distance": "距离",
            "angle": "角度",
            "rotation": "旋转角度",
            "scale": "缩放比例",
            
            # 检测相关
            "detected": "检测结果",
            "found": "发现目标",
            "matched": "匹配结果",
            "recognized": "识别结果",
            "verified": "验证结果",
            "passed": "通过状态",
            "failed": "失败状态",
            
            # 码识别相关
            "code": "码值",
            "barcode": "条形码",
            "qrcode": "二维码",
            "content": "内容",
            "data": "数据",
            "text": "文本",
            
            # 匹配相关
            "template": "模板",
            "similarity": "相似度",
            "correlation": "相关性",
            "offset": "偏移量",
            "shift": "位移",
            
            # 测量相关
            "measurement": "测量值",
            "dimension": "尺寸",
            "thickness": "厚度",
            "width_mm": "宽度(mm)",
            "height_mm": "高度(mm)",
            "depth": "深度",
            "volume": "体积",
            
            # 颜色相关
            "color": "颜色",
            "gray": "灰度",
            "brightness": "亮度",
            "contrast": "对比度",
            "saturation": "饱和度",
            "hue": "色调",
            
            # 通信相关
            "device_id": "设备ID",
            "connection": "连接",
            "sent": "已发送",
            "received": "已接收",
            "send_count": "发送次数",
            "receive_count": "接收次数",
        }
        
        return translations.get(field_name, field_name)


class DataSelectorButton(QPushButton):
    """数据选择按钮
    
    点击后弹出数据选择对话框
    """
    
    data_selected = pyqtSignal(str, str)  # 模块名, 字段名
    
    def __init__(self, parent=None):
        super().__init__("选择数据...", parent)
        self.available_modules = {}
        self.selected_module = ""
        self.selected_field = ""
        self.clicked.connect(self._on_click)
        
    def set_available_modules(self, modules: Dict[str, Dict[str, Any]]):
        """设置可用模块"""
        self.available_modules = modules
        
    def _on_click(self):
        """点击事件"""
        if not self.available_modules:
            logger.warning("没有可用的数据模块")
            return
            
        dialog = DataSelectorDialog(self.available_modules, self)
        if dialog.exec_() == QDialog.Accepted:
            module, field = dialog.get_selection()
            if module and field:
                self.selected_module = module
                self.selected_field = field
                self.setText(f"{module}.{field}")
                self.data_selected.emit(module, field)
                
    def get_selection(self) -> tuple:
        """获取当前选择"""
        return self.selected_module, self.selected_field
