#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具库UI模块

实现VisionMaster风格的工具库，包括：
- 工具分类展示
- 工具拖拽功能
- 工具搜索功能

Author: Vision System Team
Date: 2026-01-05
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

PYQT_VERSION = 5

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QAbstractItemView, QLabel, QLineEdit, QSplitter, QDockWidget,
        QTreeWidget, QTreeWidgetItem, QFrame
    )
    from PyQt6.QtGui import QIcon, QDrag, QCursor, QFont, QPixmap, QPainter, QColor, QPoint
    from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
        QAbstractItemView, QLabel, QLineEdit, QSplitter, QDockWidget,
        QTreeWidget, QTreeWidgetItem, QFrame
    )
    from PyQt5.QtGui import QIcon, QDrag, QCursor, QFont, QPixmap, QPainter, QColor
    from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QPoint

from core.tool_base import ToolRegistry


@dataclass
class ToolItemData:
    """工具项数据"""
    category: str           # 工具类别
    name: str               # 工具名称
    display_name: str       # 显示名称
    icon: str = "📦"         # 图标
    description: str = ""    # 描述


class ToolLibraryItem(QListWidgetItem):
    """工具库列表项"""
    
    def __init__(self, tool_data: ToolItemData):
        super().__init__(f"{tool_data.icon}  {tool_data.display_name}")
        self.tool_data = tool_data
        self.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | 
                     Qt.ItemFlag.ItemIsDragEnabled)
        self._drag_start_pos = None
    
    def get_tool_class(self):
        """获取工具类"""
        return ToolRegistry.get_tool_class(self.tool_data.category, self.tool_data.name)
    
    def mousePressEvent(self, event):
        """记录鼠标按下位置作为拖拽起始位置"""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def startDrag(self, supportedActions):
        """重写拖拽方法，使用自定义格式"""
        # 委托给列表控件处理
        if self.listWidget() and hasattr(self.listWidget(), 'startDrag'):
            self.listWidget().startDrag(supportedActions)
        else:
            self._logger.warning("[LIBRARY] listWidget 没有 startDrag 方法")


class ToolLibraryListWidget(QListWidget):
    """工具库自定义列表控件"""
    
    # 信号：工具被点击
    tool_clicked = pyqtSignal(str, str, str)  # category, name, display_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setSpacing(2)
        self.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: none;
                padding: 4px;
            }
            QListWidget::item {
                background-color: #ffffff;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 8px 10px;
                margin: 1px;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #e3e3e3;
                color: #000000;
                border-color: #d4d4d4;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
                border-color: #d4d4d4;
            }
            QListWidget::item:selected:hover {
                background-color: #d4d4d4;
                border-color: #c0c0c0;
            }
        """)
        
        self.itemClicked.connect(self._on_item_clicked)
    
    def _on_item_clicked(self, item):
        """处理列表项点击事件"""
        if isinstance(item, ToolLibraryItem):
            self.tool_clicked.emit(
                item.tool_data.category,
                item.tool_data.name,
                item.tool_data.display_name
            )
    
    def startDrag(self, supportedActions):
        """重写拖拽开始方法，确保使用自定义格式"""
        current_item = self.currentItem()
        if not isinstance(current_item, ToolLibraryItem):
            super().startDrag(supportedActions)
            return
        
        tool_item = current_item
        
        self.tool_clicked.emit(
            tool_item.tool_data.category,
            tool_item.tool_data.name,
            tool_item.tool_data.display_name
        )
        
        # 通知父组件拖拽开始
        if self.parent() and hasattr(self.parent(), 'tool_drag_started'):
            self.parent().tool_drag_started.emit(
                tool_item.tool_data.category,
                tool_item.tool_data.name,
                tool_item.tool_data.display_name
            )
        
        drag = QDrag(self)
        mime_data = QMimeData()
        tool_info = f"{tool_item.tool_data.category}|{tool_item.tool_data.name}|{tool_item.tool_data.display_name}"
        mime_data.setData("application/vision-tool", tool_info.encode('utf-8'))
        mime_data.setText(tool_item.tool_data.display_name)
        drag.setMimeData(mime_data)
        
        rect = self.visualItemRect(tool_item)
        pixmap = QPixmap(rect.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor(100, 150, 250))
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(rect.adjusted(5, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, f"{tool_item.tool_data.icon} {tool_item.tool_data.display_name}")
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(10, rect.height() // 2))
        
        # PyQt5使用exec_()而不是exec()
        try:
            drag.exec_(supportedActions)
        except AttributeError:
            # PyQt6使用exec()
            drag.exec(supportedActions)


class ToolLibraryWidget(QWidget):
    """工具库面板"""
    
    # 信号
    tool_drag_started = pyqtSignal(str, str, str)  # category, name, display_name
    tool_clicked = pyqtSignal(str, str, str)  # category, name, display_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tool_items: Dict[str, List[ToolLibraryItem]] = {}
        self._tool_data_list: List[ToolItemData] = []
        
        # 初始化UI
        self._init_ui()
        self._load_tools()
        self._update_tool_list()
    
    def _init_ui(self):
        """初始化UI组件 - VisionMaster风格"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 搜索框
        search_container = QWidget()
        search_container.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #d4d4d4;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.setSpacing(6)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 11px; color: #606060;")
        search_layout.addWidget(search_icon)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索工具...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d4d4d4;
                border-radius: 3px;
                padding: 4px 8px;
                background-color: #ffffff;
                font-size: 11px;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #ff6a00;
            }
            QLineEdit::placeholder {
                color: #909090;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_edit)
        
        main_layout.addWidget(search_container)
        
        # 工具分类树和工具列表
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 分类树 - VisionMaster风格
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabels(["分类"])
        self.category_tree.setColumnWidth(0, 100)
        self.category_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: #ffffff;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px 8px;
                border-radius: 2px;
                margin: 1px 0;
                color: #000000;
            }
            QTreeWidget::item:selected {
                background-color: #e3e3e3;
                color: #000000;
            }
            QTreeWidget::item:hover {
                background-color: #f5f5f5;
            }
            QTreeWidget::branch:closed:has-children {
                image: none;
            }
            QTreeWidget::branch:open:has-children {
                image: none;
            }
        """)
        self.category_tree.itemClicked.connect(self._on_category_clicked)
        content_splitter.addWidget(self.category_tree)
        
        # 工具列表
        self.tool_list = ToolLibraryListWidget()
        content_splitter.addWidget(self.tool_list)
        
        content_splitter.setSizes([90, 180])
        main_layout.addWidget(content_splitter, 1)
        
        # 工具描述区域 - VisionMaster风格
        desc_container = QWidget()
        desc_container.setStyleSheet("background-color: #ffffff; border-top: 1px solid #d4d4d4;")
        desc_layout = QVBoxLayout(desc_container)
        desc_layout.setContentsMargins(8, 8, 8, 8)
        desc_layout.setSpacing(6)
        
        desc_header = QLabel("工具信息")
        desc_header.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        desc_header.setStyleSheet("color: #000000;")
        desc_layout.addWidget(desc_header)
        
        self.description_label = QLabel("选择工具查看详细信息")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #d4d4d4;
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
                color: #000000;
                min-height: 40px;
            }
        """)
        desc_layout.addWidget(self.description_label)
        
        main_layout.addWidget(desc_container)
        
        # 连接工具列表的点击信号
        self.tool_list.tool_clicked.connect(self._on_tool_clicked)
    
    def _on_tool_clicked(self, category: str, name: str, display_name: str):
        """处理工具点击事件"""
        # 转发信号
        self.tool_clicked.emit(category, name, display_name)
        
        # 更新描述标签 - VisionMaster风格
        tool_data = self.get_tool_data(display_name)
        if tool_data:
            self.description_label.setText(f"📝 {tool_data.description}")
            self.description_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    border: 1px solid #ff6a00;
                    border-radius: 3px;
                    padding: 10px;
                    font-size: 11px;
                    color: #000000;
                }
            """)
    
    def _load_tools(self):
        """加载所有工具"""
        self._tool_data_list = [
            ToolItemData("ImageSource", "图像读取器", "图像读取器", "📷", "从本地文件读取图像"),
            ToolItemData("ImageSource", "相机", "相机", "📷", "从相机获取图像"),
            
            ToolItemData("ImageFilter", "方框滤波", "方框滤波", "🌀", "使用方框滤波平滑图像"),
            ToolItemData("ImageFilter", "均值滤波", "均值滤波", "🌀", "使用均值滤波平滑图像"),
            ToolItemData("ImageFilter", "高斯滤波", "高斯滤波", "🌀", "使用高斯滤波平滑图像"),
            ToolItemData("ImageFilter", "中值滤波", "中值滤波", "🌀", "使用中值滤波去除噪声"),
            ToolItemData("ImageFilter", "双边滤波", "双边滤波", "🌀", "使用双边滤波保留边缘"),
            ToolItemData("ImageFilter", "形态学处理", "形态学处理", "🌀", "形态学腐蚀、膨胀等操作"),
            ToolItemData("ImageFilter", "图像缩放", "图像缩放", "🌀", "调整图像大小"),
            
            ToolItemData("Vision", "灰度匹配", "灰度匹配", "🎯", "基于灰度模板匹配目标"),
            ToolItemData("Vision", "形状匹配", "形状匹配", "🎯", "基于形状特征匹配目标"),
            ToolItemData("Vision", "直线查找", "直线查找", "📏", "在图像中查找直线"),
            ToolItemData("Vision", "圆查找", "圆查找", "⭕", "在图像中查找圆形"),
            
            ToolItemData("Recognition", "读码", "读码", "📱", "通用条码二维码识别"),
            ToolItemData("Recognition", "条码识别", "条码识别", "📊", "一维条码识别"),
            ToolItemData("Recognition", "二维码识别", "二维码识别", "🔳", "二维条码识别"),
            ToolItemData("Recognition", "OCR识别", "OCR识别", "📝", "图像文字识别（中英文）"),
            ToolItemData("Recognition", "英文OCR", "英文OCR", "🔤", "英文字符识别"),
            
            ToolItemData("Analysis", "斑点分析", "斑点分析", "⚪", "分析图像中的斑点"),
            ToolItemData("Analysis", "像素计数", "像素计数", "🔢", "统计图像中的像素"),
            ToolItemData("Analysis", "直方图", "直方图", "📊", "生成图像直方图"),
            ToolItemData("Analysis", "卡尺测量", "卡尺测量", "📏", "使用卡尺进行测量"),
            
            ToolItemData("Communication", "发送数据", "发送数据", "📤", "将检测结果发送到外部设备"),
            ToolItemData("Communication", "接收数据", "接收数据", "📥", "从外部设备接收数据"),
            
            ToolItemData("Vision", "YOLO26-CPU", "YOLO26-CPU", "🤖", "使用YOLO26模型进行CPU目标检测，支持YOLO26系列模型"),
            ToolItemData("Vision", "图像拼接", "图像拼接", "🔄", "高性能图像拼接融合算法，支持多张图像自动拼接"),
        ]
        
        # 按类别分组
        self._tool_items = {}
        for tool_data in self._tool_data_list:
            if tool_data.category not in self._tool_items:
                self._tool_items[tool_data.category] = []
            self._tool_items[tool_data.category].append(tool_data)
    
    def _update_tool_list(self):
        """更新工具列表"""
        # 清空分类树
        self.category_tree.clear()
        
        # 添加分类
        self._category_items = {}
        for category in self._tool_items.keys():
            category_item = QTreeWidgetItem([category])
            self.category_tree.addTopLevelItem(category_item)
            self._category_items[category] = category_item
        
        # 展开所有分类
        self.category_tree.expandAll()
        
        # 默认显示所有工具
        self._show_tools_by_category(None)
    
    def _on_category_clicked(self, item, column):
        """分类点击事件"""
        category_name = item.text(0)
        self._show_tools_by_category(category_name)
    
    def _show_tools_by_category(self, category: Optional[str]):
        """按分类显示工具"""
        self.tool_list.clear()
        
        # 收集要显示的工具
        tools_to_show = []
        if category is None:
            # 显示所有工具
            for category_tools in self._tool_items.values():
                tools_to_show.extend(category_tools)
        else:
            # 显示指定分类的工具
            if category in self._tool_items:
                tools_to_show = self._tool_items[category]
        
        # 添加工具到列表
        for tool_data in tools_to_show:
            item = ToolLibraryItem(tool_data)
            self.tool_list.addItem(item)
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化事件"""
        self.tool_list.clear()
        
        # 过滤工具
        search_text = text.lower()
        for category_tools in self._tool_items.values():
            for tool_data in category_tools:
                if (search_text in tool_data.display_name.lower() or 
                   search_text in tool_data.description.lower()):
                    item = ToolLibraryItem(tool_data)
                    self.tool_list.addItem(item)
    
    def get_tool_data(self, display_name: str) -> Optional[ToolItemData]:
        """根据显示名称获取工具数据"""
        for tool_data in self._tool_data_list:
            if tool_data.display_name == display_name:
                return tool_data
        return None
    
    def get_all_tools(self) -> List[ToolItemData]:
        """获取所有工具数据"""
        return self._tool_data_list.copy()
    
    def refresh(self):
        """刷新工具库"""
        # 重新加载工具
        self._load_tools()
        # 更新工具列表显示
        self._update_tool_list()
        # 刷新分类树
        self._setup_category_tree()


class ToolLibraryDockWidget(QDockWidget):
    """工具库停靠窗口"""
    
    def __init__(self, parent=None):
        super().__init__("工具库", parent)
        
        # 创建工具库面板
        self.tool_library = ToolLibraryWidget()
        self.setWidget(self.tool_library)
        
        # 设置停靠位置
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # 设置样式
        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #d0d0d0;
            }
            QDockWidget::title {
                background-color: #f5f5f5;
                padding: 5px;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
    
    def get_tool_library(self) -> ToolLibraryWidget:
        """获取工具库面板"""
        return self.tool_library
