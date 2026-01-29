#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强结果面板模块

提供全面的结果展示功能：
- 多类型结果展示（码识别、匹配分析等）
- 数据类型选择器
- 多模块数据连接
- 结果可视化
- 数据导出

Author: Vision System Team
Date: 2026-01-14
"""

import sys
import os
import logging
import json
import time
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QComboBox, QLineEdit, QSplitter, QDockWidget, QFrame, QScrollArea,
    QGroupBox, QFormLayout, QHeaderView, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QTreeWidgetItemIterator,
    QMenu, QAction, QToolButton, QWidgetAction, QDoubleSpinBox, QSpinBox,
    QCheckBox, QStyledItemDelegate, QStyleOptionViewItem, QSizePolicy
)
from PyQt5.QtGui import (
    QFont, QColor, QIcon, QTextCursor, QPainter, QPen, QBrush, QPixmap,
    QPainterPath, QLinearGradient
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QModelIndex, QSize

from data.image_data import ResultData, DataType


class ResultCategory(Enum):
    """结果类别枚举"""
    BARCODE = "barcode"
    QRCODE = "qrcode"
    MATCH = "match"
    CALIPER = "caliper"
    BLOB = "blob"
    SHAPE = "shape"
    OCR = "ocr"
    CLASSIFICATION = "classification"
    DEFECT = "defect"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class ResultDetailWidget(QWidget):
    """结果详情组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result_data = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    
    def set_result(self, result_data: ResultData, category: str = ""):
        """设置结果数据"""
        self._result_data = result_data
        
        # 清空现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if result_data is None:
            return
        
        # 获取工具名称和类别
        tool_name = result_data.tool_name or "未知工具"
        category = result_data.result_category or category
        
        # 添加标题
        title_layout = QHBoxLayout()
        title_label = QLabel(f"📋 {tool_name}")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_layout.addWidget(title_label)
        
        # 状态标签
        if result_data.status:
            status_label = QLabel("✅ 成功")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_label = QLabel("❌ 失败")
            status_label.setStyleSheet("color: red; font-weight: bold;")
        title_layout.addWidget(status_label)
        title_layout.addStretch()
        
        title_widget = QWidget()
        title_widget.setLayout(title_layout)
        self.content_layout.addWidget(title_widget)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.content_layout.addWidget(separator)
        
        # 根据类别显示不同内容
        if category in ["barcode", "qrcode", "code"]:
            self._show_barcode_result(result_data)
        elif category == "detection":
            self._show_detection_result(result_data)
        elif category == "match":
            self._show_match_result(result_data)
        elif category in ["caliper", "measurement"]:
            self._show_caliper_result(result_data)
        elif category in ["blob", "shape"]:
            self._show_blob_result(result_data)
        elif category == "ocr":
            self._show_ocr_result(result_data)
        else:
            self._show_general_result(result_data)
        
        self.content_layout.addStretch()
    
    def _show_barcode_result(self, result_data: ResultData):
        """显示条码识别结果"""
        codes = result_data.get_value("codes", [])
        count = result_data.get_value("count", 0)
        
        if isinstance(codes, list) and codes:
            for i, code in enumerate(codes):
                self._add_result_group(f"码 {i+1}", [
                    ("内容", code.get("data", "")),
                    ("类型", code.get("type", "")),
                    ("位置", f"({code.get('rect', {}).get('x', 0)}, {code.get('rect', {}).get('y', 0)})"),
                    ("尺寸", f"{code.get('rect', {}).get('width', 0)} x {code.get('rect', {}).get('height', 0)}")
                ])
        else:
            self._add_info_label("未识别到码")
    
    def _show_match_result(self, result_data: ResultData):
        """显示匹配分析结果"""
        match_result = result_data.get_value("match_result", {})
        score = result_data.get_value("score", 0)
        center = result_data.get_value("center", {})
        matched = result_data.get_value("matched", False)
        
        self._add_result_group("匹配结果", [
            ("状态", "匹配成功 ✅" if matched else "匹配失败 ❌"),
            ("相似度", f"{score * 100:.2f}%" if isinstance(score, float) else str(score)),
            ("中心点", f"({center.get('x', center.get('cx', ''))}, {center.get('y', center.get('cy', ''))})"),
            ("角度", f"{result_data.get_value('angle', 0):.2f}°" if result_data.has_value('angle') else "N/A"),
            ("匹配分数", f"{result_data.get_value('match_score', 0):.4f}")
        ])
    
    def _show_caliper_result(self, result_data: ResultData):
        """显示卡尺测量结果"""
        measurements = result_data.get_value("measurements", {})
        
        for name, value in measurements.items():
            if isinstance(value, dict):
                self._add_result_group(name, [
                    (k, f"{v:.4f}" if isinstance(v, float) else str(v)) 
                    for k, v in value.items()
                ])
            else:
                self._add_result_group(name, [("值", f"{value:.4f}" if isinstance(value, float) else str(value))])
    
    def _show_blob_result(self, result_data: ResultData):
        """显示Blob分析结果"""
        blobs = result_data.get_value("blobs", [])
        
        if isinstance(blobs, list) and blobs:
            # 只显示前10个blob，避免UI卡顿
            display_blobs = blobs[:10]
            total_count = len(blobs)
            
            # 如果有更多blob，显示总数
            if total_count > 10:
                self._add_info_label(f"共检测到 {total_count} 个斑点，显示前10个")
            
            for i, blob in enumerate(display_blobs):
                self._add_result_group(f"Blob {i+1}", [
                    ("面积", f"{blob.get('area', 0):.2f}"),
                    ("中心", f"({blob.get('cx', blob.get('center_x', 'N/A'))}, {blob.get('cy', blob.get('center_y', 'N/A'))})"),
                    ("周长", f"{blob.get('perimeter', 0):.2f}" if blob.get('perimeter') else "N/A"),
                    ("圆度", f"{blob.get('circularity', 0):.4f}" if blob.get('circularity') else "N/A")
                ])
        else:
            self._add_info_label("未检测到Blob")
    
    def _show_ocr_result(self, result_data: ResultData):
        """显示OCR识别结果"""
        texts = result_data.get_value("texts", [])
        confidence = result_data.get_value("confidence", 0)
        
        if isinstance(texts, list) and texts:
            for i, item in enumerate(texts):
                if isinstance(item, dict):
                    self._add_result_group(f"文本 {i+1}", [
                        ("内容", item.get("text", "")),
                        ("置信度", f"{item.get('confidence', 0) * 100:.1f}%"),
                        ("区域", f"({item.get('x', 0)}, {item.get('y', 0)})")
                    ])
                else:
                    self._add_result_group(f"文本 {i+1}", [("内容", str(item))])
        else:
            self._add_info_label("未识别到文本")
    
    def _show_detection_result(self, result_data: ResultData):
        """显示目标检测结果（如YOLO26）"""
        # 尝试从不同的键获取检测结果
        detections = result_data.get_value("detections", [])
        detection_count = result_data.get_value("detection_count", len(detections))
        
        if isinstance(detections, list) and detections:
            # 显示总体统计
            self._add_result_group("检测统计", [
                ("检测数量", str(detection_count)),
                ("总检测时间", f"{result_data.get_value('inference_time_ms', 0):.2f} ms")
            ])
            
            # 显示每个检测结果
            for i, det in enumerate(detections[:20]):  # 最多显示20个结果
                class_name = det.get("class_name", det.get("name", "未知"))
                confidence = det.get("confidence", det.get("score", 0))
                bbox = det.get("bbox", {})
                
                # 处理不同格式的边界框
                if isinstance(bbox, dict):
                    x1 = bbox.get("x1", bbox.get("x", 0))
                    y1 = bbox.get("y1", bbox.get("y", 0))
                    x2 = bbox.get("x2", x1 + bbox.get("width", 0))
                    y2 = bbox.get("y2", y1 + bbox.get("height", 0))
                elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    x1, y1, x2, y2 = bbox
                else:
                    x1, y1, x2, y2 = 0, 0, 0, 0
                
                self._add_result_group(f"目标 {i+1} ({class_name})", [
                    ("类别", class_name),
                    ("置信度", f"{confidence * 100:.1f}%"),
                    ("边界框", f"({x1:.2f}, {y1:.2f}) - ({x2:.2f}, {y2:.2f})"),
                    ("宽度", f"{x2 - x1:.2f}"),
                    ("高度", f"{y2 - y1:.2f}")
                ])
        else:
            self._add_info_label("未检测到目标")
    
    def _show_general_result(self, result_data: ResultData):
        """显示通用结果"""
        values = result_data.get_values_with_types()
        
        for key, value, data_type in values:
            if key in ["message", "status", "count"]:
                continue
            
            type_name = {
                DataType.INT: "int",
                DataType.FLOAT: "float", 
                DataType.STRING: "string",
                DataType.BOOL: "bool",
                DataType.POINT: "点",
                DataType.RECT: "矩形",
                DataType.LINE: "线",
                DataType.CIRCLE: "圆",
                DataType.POLYGON: "多边形",
                DataType.IMAGE: "图像",
                DataType.ARRAY: "数组",
                DataType.DICT: "字典",
                DataType.UNKNOWN: "未知"
            }.get(data_type, "未知")
            
            display_value = value
            if isinstance(value, float):
                display_value = f"{value:.4f}"
            elif isinstance(value, dict):
                display_value = str(value)
            
            self._add_result_group(key, [("类型", type_name), ("值", str(display_value))])
    
    def _add_result_group(self, title: str, items: List[Tuple[str, str]]):
        """添加结果组"""
        group = QGroupBox(title)
        layout = QFormLayout(group)
        layout.setLabelAlignment(Qt.AlignRight)
        layout.setSpacing(5)
        
        for label, value in items:
            value_label = QLabel(str(value))
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addRow(label, value_label)
        
        self.content_layout.addWidget(group)
    
    def _add_info_label(self, text: str):
        """添加信息标签"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: gray; padding: 20px;")
        self.content_layout.addWidget(label)


class DataSelectorWidget(QWidget):
    """数据选择器组件
    
    提供+号按钮，点击后展开数据类型选择和模块数据选择
    """
    
    data_selected = pyqtSignal(str, str, DataType)  # 模块名, 键名, 数据类型
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._available_modules = {}  # {模块名: {键名: DataType}}
        self._current_selection = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # +号按钮
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(30)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                min-width: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_btn.clicked.connect(self._show_selection_dialog)
        layout.addWidget(self.add_btn)
        
        # 当前选择标签
        self.selection_label = QLabel("点击+选择数据")
        self.selection_label.setMinimumWidth(150)
        self.selection_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.selection_label)
        
        layout.addStretch()
    
    def set_available_modules(self, modules: Dict[str, Dict[str, DataType]]):
        """设置可用模块
        
        Args:
            modules: {模块名: {键名: DataType}}
        """
        self._available_modules = modules
    
    def _show_selection_dialog(self):
        """显示选择对话框"""
        if not self._available_modules:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择数据")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # 标题
        title = QLabel("选择要使用的数据")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # 模块列表
        self.module_tree = QTreeWidget()
        self.module_tree.setHeaderLabels(["模块/数据", "类型"])
        self.module_tree.setAlternatingRowColors(True)
        layout.addWidget(self.module_tree)
        
        for module_name, data_dict in self._available_modules.items():
            module_item = QTreeWidgetItem([module_name])
            module_item.setExpanded(True)
            
            for key, data_type in data_dict.items():
                type_name = {
                    DataType.INT: "int", DataType.FLOAT: "float",
                    DataType.STRING: "string", DataType.BOOL: "bool",
                    DataType.POINT: "点", DataType.RECT: "矩形",
                    DataType.LINE: "线", DataType.CIRCLE: "圆",
                    DataType.POLYGON: "多边形", DataType.IMAGE: "图像",
                    DataType.ARRAY: "数组", DataType.DICT: "字典",
                    DataType.UNKNOWN: "未知"
                }.get(data_type, "未知")
                
                data_item = QTreeWidgetItem([key, type_name])
                data_item.setData(0, Qt.UserRole, (module_name, key, data_type))
                module_item.addChild(data_item)
            
            self.module_tree.addTopLevelItem(module_item)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            item = self.module_tree.currentItem()
            if item and item.data(0, Qt.UserRole):
                module_name, key, data_type = item.data(0, Qt.UserRole)
                self._current_selection = (module_name, key, data_type)
                
                type_icon = {
                    DataType.INT: "🔢", DataType.FLOAT: "🔢",
                    DataType.STRING: "📝", DataType.BOOL: "☑",
                    DataType.POINT: "📍", DataType.RECT: "⬜",
                    DataType.LINE: "📏", DataType.CIRCLE: "⭕",
                    DataType.POLYGON: "🔷", DataType.IMAGE: "🖼",
                    DataType.ARRAY: "📋", DataType.DICT: "📦",
                    DataType.UNKNOWN: "❓"
                }.get(data_type, "📦")
                
                self.selection_label.setText(f"{type_icon} {module_name}.{key}")
                self.selection_label.setStyleSheet("color: #2196F3; font-weight: bold;")
                self.data_selected.emit(module_name, key, data_type)
    
    def get_selection(self) -> Tuple[str, str, DataType]:
        """获取选择"""
        return self._current_selection
    
    def clear_selection(self):
        """清除选择"""
        self._current_selection = None
        self.selection_label.setText("点击+选择数据")
        self.selection_label.setStyleSheet("color: #666; font-style: italic;")


class ResultVisualizationWidget(QWidget):
    """结果可视化组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result_data = None
        self.setMinimumSize(200, 200)
    
    def set_result(self, result_data: ResultData, category: str = ""):
        """设置结果数据进行可视化"""
        self._result_data = result_data
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 背景渐变
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(245, 245, 245))
        gradient.setColorAt(1, QColor(230, 230, 230))
        painter.fillRect(0, 0, w, h, gradient)
        
        if self._result_data is None:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(w//2 - 50, h//2, "无数据")
            return
        
        # 根据类别绘制不同内容
        category = self._result_data.result_category
        codes = self._result_data.get_value("codes", [])
        
        if codes and isinstance(codes, list):
            self._draw_codes(painter, codes, w, h)
        else:
            # 绘制通用信息
            painter.setPen(QColor(100, 100, 100))
            values = self._result_data.get_all_values()
            y = 30
            for key, value in list(values.items())[:5]:
                if key in ["message", "status"]:
                    continue
                text = f"{key}: {value}"
                if len(text) > 30:
                    text = text[:27] + "..."
                painter.drawText(20, y, text)
                y += 25
    
    def _draw_codes(self, painter: QPainter, codes: List[Dict], w: int, h: int):
        """绘制码的位置"""
        from PyQt5.QtCore import QRectF
        
        for i, code in enumerate(codes):
            rect_dict = code.get("rect", {})
            if not rect_dict:
                continue
            
            x = rect_dict.get("x", 0)
            y = rect_dict.get("y", 0)
            rw = rect_dict.get("width", 50)
            rh = rect_dict.get("height", 30)
            
            # 计算缩放以适应窗口
            scale = min(w / (rw + 40), h / (rh + 40)) * 0.8
            offset_x = (w - rw * scale) // 2
            offset_y = (h - rh * scale) // 2
            
            draw_x = offset_x + x * scale
            draw_y = offset_y + y * scale
            draw_w = rw * scale
            draw_h = rh * scale
            
            # 绘制矩形框
            painter.setPen(QPen(QColor(76, 175, 80), 2))
            painter.setBrush(QBrush(QColor(76, 175, 80, 30)))
            painter.drawRect(int(draw_x), int(draw_y), int(draw_w), int(draw_h))
            
            # 绘制标签
            code_type = code.get("type", "CODE")
            code_data = str(code.get("data", ""))[:10]
            label = f"{code_type}: {code_data}"
            painter.setPen(QColor(76, 175, 80))
            painter.drawText(int(draw_x), int(draw_y) - 5, label)


class EnhancedResultPanel(QWidget):
    """增强结果面板"""
    
    result_selected = pyqtSignal(ResultData, str)  # 结果数据, 类别
    data_connection_requested = pyqtSignal(str, str, DataType)  # 模块名, 键名, 类型
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("EnhancedResultPanel")
        self._results: List[Tuple[ResultData, str, float]] = []  # (数据, 类别, 时间戳)
        self._available_modules: Dict[str, Dict[str, DataType]] = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        title_label = QLabel("📊 结果面板")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 清除按钮
        clear_btn = QPushButton("🗑 清空")
        clear_btn.clicked.connect(self.clear_results)
        title_layout.addWidget(clear_btn)
        
        # 导出按钮
        export_btn = QPushButton("💾 导出")
        export_btn.clicked.connect(self._show_export_dialog)
        title_layout.addWidget(export_btn)
        
        layout.addLayout(title_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 搜索和过滤区域
        filter_layout = QHBoxLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部", "")
        self.category_combo.addItem("码识别", "code")
        self.category_combo.addItem("目标检测", "detection")
        self.category_combo.addItem("匹配分析", "match")
        self.category_combo.addItem("测量", "caliper")
        self.category_combo.addItem("Blob分析", "blob")
        self.category_combo.addItem("OCR", "ocr")
        self.category_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.category_combo)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索工具...")
        self.search_edit.textChanged.connect(self._on_filter_changed)
        self.search_edit.setMinimumWidth(150)
        filter_layout.addWidget(self.search_edit)
        
        layout.addLayout(filter_layout)
        
        # 结果列表 - 使用树形控件，可以展开显示详情
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderHidden(True)
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.result_tree.setMinimumHeight(150)
        layout.addWidget(self.result_tree)
        
        # 状态栏
        status_layout = QHBoxLayout()
        
        self.count_label = QLabel("0 条结果")
        status_layout.addWidget(self.count_label)
        
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
        # 初始化数据选择器列表
        self.data_selectors = []
    
    def add_result(self, result_data: ResultData, category: str = ""):
        """添加结果"""
        # 自动检测结果类别
        if not category:
            tool_name = result_data.tool_name or ""
            if "YOLO" in tool_name or "yolo" in tool_name:
                category = "detection"
            elif "条码" in tool_name or "二维码" in tool_name or "读码" in tool_name:
                category = "code"
            elif "匹配" in tool_name:
                category = "match"
            elif "测量" in tool_name or "卡尺" in tool_name:
                category = "caliper"
            elif "Blob" in tool_name or "blob" in tool_name:
                category = "blob"
            elif "OCR" in tool_name or "ocr" in tool_name:
                category = "ocr"
        
        result_data.result_category = category
        
        timestamp = time.time()
        self._results.append((result_data, category, timestamp))
        
        # 限制数量
        if len(self._results) > 500:
            self._results = self._results[-500:]
        
        self._update_result_list()
        self._update_available_modules()
        
        # 自动选择最新的结果
        if self.result_tree.topLevelItemCount() > 0:
            first_item = self.result_tree.topLevelItem(0)
            if first_item:
                self.result_tree.setCurrentItem(first_item)
    
    def _update_result_list(self):
        """更新结果列表"""
        filter_category = self.category_combo.currentData()
        search_text = self.search_edit.text().lower()
        
        self.result_tree.clear()
        
        for result_data, category, timestamp in reversed(self._results):
            # 过滤
            if filter_category and category != filter_category:
                continue
            
            tool_name = result_data.tool_name or "未知"
            if search_text and search_text not in tool_name.lower():
                continue
            
            # 创建树形项
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            
            icon = "✅" if result_data.status else "❌"
            category_icon = {
                "code": "📱", "detection": "🔍", "match": "🎯", "caliper": "📏",
                "blob": "🔵", "ocr": "📝", "": "📋"
            }.get(category, "📋")
            
            # 创建父项（工具名称）
            parent_text = f"{time_str} {icon} {category_icon} {tool_name}"
            parent_item = QTreeWidgetItem([parent_text])
            parent_item.setData(0, Qt.UserRole, (result_data, category))
            
            # 添加关键结果作为子项
            self._add_result_details(parent_item, result_data, category)
            
            self.result_tree.addTopLevelItem(parent_item)
        
        self.count_label.setText(f"{len(self._results)} 条结果")
    
    def _add_result_details(self, parent_item: QTreeWidgetItem, result_data: ResultData, category: str):
        """添加结果详情作为子项"""
        if category in ["barcode", "qrcode", "code"]:
            codes = result_data.get_value("codes", [])
            if isinstance(codes, list) and codes:
                for i, code in enumerate(codes[:5]):  # 最多显示5个
                    data = code.get("data", "")[:20]
                    child = QTreeWidgetItem([f"  码 {i+1}: {data}"])
                    parent_item.addChild(child)
        elif category == "detection":
            detections = result_data.get_value("detections", [])
            if isinstance(detections, list) and detections:
                for i, det in enumerate(detections[:5]):
                    name = det.get("class_name", det.get("name", "未知"))
                    conf = det.get("confidence", 0)
                    child = QTreeWidgetItem([f"  目标 {i+1}: {name} ({conf*100:.1f}%)"])
                    parent_item.addChild(child)
        elif category in ["blob", "shape"]:
            blobs = result_data.get_value("blobs", [])
            if isinstance(blobs, list) and blobs:
                for i, blob in enumerate(blobs[:5]):
                    area = blob.get("area", 0)
                    child = QTreeWidgetItem([f"  Blob {i+1}: 面积={area:.2f}"])
                    parent_item.addChild(child)
        elif category == "match":
            score = result_data.get_value("score", 0)
            matched = result_data.get_value("matched", False)
            child = QTreeWidgetItem([f"  匹配{'成功' if matched else '失败'}: 相似度={score*100:.2f}%"])
            parent_item.addChild(child)
        elif category == "ocr":
            texts = result_data.get_value("texts", [])
            if isinstance(texts, list) and texts:
                for i, item in enumerate(texts[:5]):
                    if isinstance(item, dict):
                        text = item.get("text", "")[:20]
                        child = QTreeWidgetItem([f"  文本 {i+1}: {text}"])
                        parent_item.addChild(child)
        else:
            # 通用结果显示
            values = result_data.get_all_values()
            for key, value in list(values.items())[:5]:
                if key not in ["message", "status"]:
                    display_value = str(value)[:30]
                    child = QTreeWidgetItem([f"  {key}: {display_value}"])
                    parent_item.addChild(child)
    
    def _update_available_modules(self):
        """更新可用模块列表"""
        self._available_modules = {}
        
        for result_data, category, _ in self._results:
            module_name = result_data.tool_name or "未知模块"
            
            if module_name not in self._available_modules:
                self._available_modules[module_name] = {}
            
            for key, data_type in result_data.get_all_value_types().items():
                if key not in ["message", "status"]:
                    self._available_modules[module_name][key] = data_type
        
        # 更新选择器
        for selector in self.data_selectors:
            selector.set_available_modules(self._available_modules)
    
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """树形项点击事件"""
        # 获取父项的数据（如果是子项，获取其父项）
        parent_item = item.parent() if item.parent() else item
        data = parent_item.data(0, Qt.UserRole)
        
        if data:
            result_data, category = data
            self.result_selected.emit(result_data, category)
            
            # 切换展开/折叠状态
            if item.childCount() > 0:
                item.setExpanded(not item.isExpanded())
    
    def _on_filter_changed(self):
        """过滤条件变化"""
        self._update_result_list()
    
    def _on_data_selected(self, module_name: str, key: str, data_type: DataType):
        """数据选择事件"""
        self.data_connection_requested.emit(module_name, key, data_type)
    
    def _show_data_selector(self):
        """显示数据选择器对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("选择数据")
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        
        title = QLabel("选择要使用的数据")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        if not self._available_modules:
            info_label = QLabel("暂无可用的模块数据\n\n请先运行工具以生成结果数据")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            layout.addWidget(info_label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec_()
            return
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["模块/数据", "类型"])
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QTreeWidget.SingleSelection)
        
        # 自动展开并选择第一个有数据的子节点
        for module_name, data_dict in self._available_modules.items():
            if data_dict:
                for i in range(tree.topLevelItemCount()):
                    item = tree.topLevelItem(i)
                    if item.text(0) == module_name and item.childCount() > 0:
                        item.setExpanded(True)
                        first_child = item.child(0)
                        if first_child:
                            tree.setCurrentItem(first_child)
                        break
        
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        layout.addWidget(tree)
        
        for module_name, data_dict in self._available_modules.items():
            module_item = QTreeWidgetItem([module_name])
            module_item.setExpanded(True)
            
            for key, data_type in data_dict.items():
                type_name = {
                    DataType.INT: "int", DataType.FLOAT: "float",
                    DataType.STRING: "string", DataType.BOOL: "bool",
                    DataType.POINT: "点", DataType.RECT: "矩形",
                    DataType.LINE: "线", DataType.CIRCLE: "圆",
                    DataType.POLYGON: "多边形", DataType.IMAGE: "图像",
                    DataType.ARRAY: "数组", DataType.DICT: "字典",
                    DataType.UNKNOWN: "未知"
                }.get(data_type, "未知")
                
                data_item = QTreeWidgetItem([key, type_name])
                data_item.setData(0, Qt.UserRole, (module_name, key, data_type))
                module_item.addChild(data_item)
            
            tree.addTopLevelItem(module_item)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setText("确定")
        ok_btn.setEnabled(False)
        
        def on_item_clicked(item):
            ok_btn.setEnabled(True)
        
        tree.itemClicked.connect(on_item_clicked)
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            item = tree.currentItem()
            
            if item is None:
                return
            
            user_data = item.data(0, Qt.UserRole)
            
            if user_data is None and item.childCount() > 0:
                item = item.child(0)
                user_data = item.data(0, Qt.UserRole)
            
            if item and user_data:
                module_name, key, data_type = user_data
                
                type_icon = {
                    DataType.INT: "🔢", DataType.FLOAT: "🔢",
                    DataType.STRING: "📝", DataType.BOOL: "☑",
                    DataType.POINT: "📍", DataType.RECT: "⬜",
                    DataType.LINE: "📏", DataType.CIRCLE: "⭕",
                    DataType.POLYGON: "🔷", DataType.IMAGE: "🖼",
                    DataType.ARRAY: "📋", DataType.DICT: "📦",
                    DataType.UNKNOWN: "❓"
                }.get(data_type, "📦")
                
                self.data_connection_requested.emit(module_name, key, data_type)
    
    def _show_export_dialog(self):
        """显示导出对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("导出结果")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        
        # 导出选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout()
        
        self.export_json = QCheckBox("JSON格式")
        self.export_json.setChecked(True)
        options_layout.addWidget(self.export_json)
        
        self.export_csv = QCheckBox("CSV格式")
        options_layout.addWidget(self.export_csv)
        
        self.export_details = QCheckBox("包含详细信息")
        self.export_details.setChecked(True)
        options_layout.addWidget(self.export_details)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            formats = []
            if self.export_json.isChecked():
                formats.append("json")
            if self.export_csv.isChecked():
                formats.append("csv")
            
            if formats:
                self._export_results(formats, self.export_details.isChecked())
    
    def _export_results(self, formats: List[str], include_details: bool):
        """导出结果"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_data = []
        for result_data, category, ts in self._results:
            result_dict = {
                "timestamp": ts,
                "datetime": datetime.fromtimestamp(ts).isoformat(),
                "category": category,
                "tool_name": result_data.tool_name,
                "status": result_data.status,
                "message": result_data.message,
                "values": {}
            }
            
            if include_details:
                for key, value in result_data.get_all_values().items():
                    if key not in ["message", "status"]:
                        result_dict["values"][key] = {
                            "value": str(value) if not isinstance(value, (int, float, bool, list, dict)) else value,
                            "type": result_data.get_value_type(key).value
                        }
            
            results_data.append(result_dict)
        
        for fmt in formats:
            if fmt == "json":
                filename = f"results_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, ensure_ascii=False, indent=2)
                self._logger.info(f"结果已导出到 {filename}")
            
            elif fmt == "csv":
                filename = f"results_{timestamp}.csv"
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["时间", "类别", "工具", "状态", "消息"])
                    for r in results_data:
                        writer.writerow([
                            r["datetime"], r["category"], r["tool_name"],
                            "成功" if r["status"] else "失败", r["message"]
                        ])
                self._logger.info(f"结果已导出到 {filename}")
    
    def clear_results(self):
        """清空结果"""
        self._results.clear()
        self._update_result_list()
    
    def set_available_modules(self, modules: Dict[str, Dict[str, DataType]]):
        """设置可用模块数据
        
        Args:
            modules: {模块名: {键名: DataType}}
        """
        self._available_modules = modules
    
    def get_results(self) -> List[Tuple[ResultData, str, float]]:
        """获取所有结果"""
        return self._results.copy()


class ResultPanelDockWidget(QDockWidget):
    """结果面板停靠窗口"""
    
    def __init__(self, parent=None):
        super().__init__("结果面板", parent)
        self.setObjectName("ResultPanel")
        
        self.widget = EnhancedResultPanel()
        self.setWidget(self.widget)
        
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(300)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    panel = EnhancedResultPanel()
    panel.show()
    
    # 测试添加结果
    from data.image_data import ResultData, DataType
    
    test_result = ResultData()
    test_result.tool_name = "条码识别"
    test_result.status = True
    test_result.message = "识别成功"
    test_result.set_value("count", 2)
    test_result.set_value("codes", [
        {"data": "123456789", "type": "QRCODE", "rect": {"x": 100, "y": 100, "width": 50, "height": 50}},
        {"data": "987654321", "type": "CODE128", "rect": {"x": 200, "y": 200, "width": 100, "height": 30}}
    ])
    test_result.set_value("confidence", 0.95)
    
    panel.add_result(test_result, "code")
    
    sys.exit(app.exec_())
