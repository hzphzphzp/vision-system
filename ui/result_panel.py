#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果面板UI模块

实现VisionMaster风格的结果面板，包括：
- 运行结果显示
- 工具执行状态
- 详细错误信息
- 结果过滤和搜索
- 结果导出功能

Author: Vision System Team
Date: 2026-01-05
"""

import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

PYQT_VERSION = 5

try:
    from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QIcon, QTextCursor
    from PyQt6.QtWidgets import (
        QComboBox,
        QDockWidget,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QIcon, QTextCursor
    from PyQt5.QtWidgets import (
        QComboBox,
        QDockWidget,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )


class ResultType(Enum):
    """结果类型枚举"""

    INFO = "info"  # 信息
    SUCCESS = "success"  # 成功
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    DEBUG = "debug"  # 调试


class ResultItem:
    """结果项"""

    def __init__(
        self,
        result_type: ResultType,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
        timestamp: float = None,
    ):
        self.type = result_type
        self.message = message
        self.details = details or {}
        self.tool_name = tool_name
        self.timestamp = timestamp or time.time()
        self.datetime = datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "message": self.message,
            "details": self.details,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp,
            "datetime": self.datetime.isoformat(),
        }

    def __str__(self) -> str:
        """字符串表示"""
        time_str = self.datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{time_str}] [{self.type.value.upper()}] {self.message}"


class ResultPanelWidget(QWidget):
    """结果面板"""

    # 信号
    clear_results_signal = pyqtSignal()
    export_results_signal = pyqtSignal(str)  # 导出文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("ResultPanelWidget")
        self._results: List[ResultItem] = []
        self._filtered_results: List[ResultItem] = []
        self._result_limit = 1000  # 结果数量限制

        # 初始化UI
        self._init_ui()

    def _init_ui(self):
        """初始化UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 标题
        title_label = QLabel("结果")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(title_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # 控制栏
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 5)

        # 过滤下拉框
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("所有结果", None)
        self.filter_combo.addItem("成功", ResultType.SUCCESS)
        self.filter_combo.addItem("警告", ResultType.WARNING)
        self.filter_combo.addItem("错误", ResultType.ERROR)
        self.filter_combo.addItem("信息", ResultType.INFO)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        control_layout.addWidget(self.filter_combo)

        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索结果...")
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        control_layout.addWidget(self.search_edit)

        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self._on_clear_results)
        control_layout.addWidget(clear_btn)

        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self._on_export_results)
        control_layout.addWidget(export_btn)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # 结果显示区域
        self.result_tabs = QTabWidget()

        # 文本视图
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_view.setStyleSheet(
            """
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 10pt;
            }
        """
        )
        self.result_tabs.addTab(self.text_view, "文本视图")

        # 表格视图
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(4)
        self.table_view.setHorizontalHeaderLabels(
            ["时间", "类型", "工具", "消息"]
        )
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_view.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.result_tabs.addTab(self.table_view, "表格视图")

        # 树形视图
        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderLabels(["结果"])
        self.result_tabs.addTab(self.tree_view, "树形视图")

        main_layout.addWidget(self.result_tabs)

        # 状态栏
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 5, 0, 0)

        self.result_count_label = QLabel("0 条结果")
        status_layout.addWidget(self.result_count_label)

        self.filter_count_label = QLabel("0 条过滤结果")
        status_layout.addWidget(self.filter_count_label)

        status_layout.addStretch()
        main_layout.addLayout(status_layout)

    def add_result(
        self,
        result_type: ResultType,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加结果

        Args:
            result_type: 结果类型
            message: 结果消息
            details: 详细信息
            tool_name: 工具名称
        """
        # 创建结果项
        result_item = ResultItem(result_type, message, details, tool_name)

        # 添加到结果列表
        self._results.append(result_item)

        # 限制结果数量
        if len(self._results) > self._result_limit:
            self._results = self._results[-self._result_limit :]

        # 更新过滤结果
        self._update_filtered_results()

        # 更新显示
        self._update_display()

        # 记录日志
        self._logger.log(
            getattr(logging, result_type.value.upper(), logging.INFO),
            f"{tool_name}: {message}",
            extra=details,
        )

    def add_info(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加信息结果"""
        self.add_result(ResultType.INFO, message, details, tool_name)

    def add_success(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加成功结果"""
        self.add_result(ResultType.SUCCESS, message, details, tool_name)

    def add_warning(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加警告结果"""
        self.add_result(ResultType.WARNING, message, details, tool_name)

    def add_error(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加错误结果"""
        self.add_result(ResultType.ERROR, message, details, tool_name)

    def clear_results(self):
        """清空所有结果"""
        self._results.clear()
        self._filtered_results.clear()
        self._update_display()
        self._logger.info("已清空所有结果")

    def get_results(self) -> List[ResultItem]:
        """获取所有结果"""
        return self._results.copy()

    def get_filtered_results(self) -> List[ResultItem]:
        """获取过滤后的结果"""
        return self._filtered_results.copy()

    def _update_filtered_results(self):
        """更新过滤结果"""
        # 获取过滤条件
        filter_type = self.filter_combo.currentData()
        search_text = self.search_edit.text().lower()

        # 过滤结果
        self._filtered_results = []
        for result in self._results:
            # 类型过滤
            if filter_type is not None and result.type != filter_type:
                continue

            # 文本过滤
            if search_text:
                if search_text not in result.message.lower() and (
                    result.tool_name is None
                    or search_text not in result.tool_name.lower()
                ):
                    continue

            self._filtered_results.append(result)

    def _update_display(self):
        """更新结果显示"""
        # 更新状态栏
        self.result_count_label.setText(f"{len(self._results)} 条结果")
        self.filter_count_label.setText(
            f"{len(self._filtered_results)} 条过滤结果"
        )

        # 更新当前选中的视图
        current_index = self.result_tabs.currentIndex()
        if current_index == 0:  # 文本视图
            self._update_text_view()
        elif current_index == 1:  # 表格视图
            self._update_table_view()
        elif current_index == 2:  # 树形视图
            self._update_tree_view()

    def _update_text_view(self):
        """更新文本视图"""
        # 保存当前滚动位置
        scrollbar = self.text_view.verticalScrollBar()
        is_at_bottom = scrollbar.value() == scrollbar.maximum()

        # 清空文本
        self.text_view.clear()

        # 添加结果
        for result in self._filtered_results:
            # 设置文本颜色
            if result.type == ResultType.ERROR:
                color = QColor(255, 0, 0)  # 红色
            elif result.type == ResultType.WARNING:
                color = QColor(255, 165, 0)  # 橙色
            elif result.type == ResultType.SUCCESS:
                color = QColor(0, 128, 0)  # 绿色
            elif result.type == ResultType.INFO:
                color = QColor(0, 0, 255)  # 蓝色
            else:  # DEBUG
                color = QColor(128, 128, 128)  # 灰色

            # 添加结果行
            self.text_view.setTextColor(color)
            self.text_view.append(str(result))

        # 恢复滚动位置
        if is_at_bottom:
            self.text_view.moveCursor(QTextCursor.MoveOperation.End)

    def _update_table_view(self):
        """更新表格视图"""
        # 清空表格
        self.table_view.setRowCount(0)

        # 添加结果行
        for result in self._filtered_results:
            row = self.table_view.rowCount()
            self.table_view.insertRow(row)

            # 时间
            time_item = QTableWidgetItem(
                result.datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            )
            self.table_view.setItem(row, 0, time_item)

            # 类型
            type_item = QTableWidgetItem(result.type.value.upper())
            if result.type == ResultType.ERROR:
                type_item.setBackground(QColor(255, 200, 200))
            elif result.type == ResultType.WARNING:
                type_item.setBackground(QColor(255, 250, 200))
            elif result.type == ResultType.SUCCESS:
                type_item.setBackground(QColor(200, 255, 200))
            self.table_view.setItem(row, 1, type_item)

            # 工具名称
            tool_item = QTableWidgetItem(result.tool_name or "")
            self.table_view.setItem(row, 2, tool_item)

            # 消息
            message_item = QTableWidgetItem(result.message)
            self.table_view.setItem(row, 3, message_item)

    def _update_tree_view(self):
        """更新树形视图"""
        # 清空树形视图
        self.tree_view.clear()

        # 按工具分组
        tool_groups = {}
        for result in self._filtered_results:
            tool_name = result.tool_name or "全局"
            if tool_name not in tool_groups:
                tool_groups[tool_name] = []
            tool_groups[tool_name].append(result)

        # 添加到树形视图
        for tool_name, results in tool_groups.items():
            tool_item = QTreeWidgetItem([tool_name])

            for result in results:
                # 设置文本
                result_text = f"[{result.type.value.upper()}] {result.message}"
                result_item = QTreeWidgetItem([result_text])

                # 设置图标或颜色
                if result.type == ResultType.ERROR:
                    result_item.setForeground(0, QColor(255, 0, 0))
                elif result.type == ResultType.WARNING:
                    result_item.setForeground(0, QColor(255, 165, 0))
                elif result.type == ResultType.SUCCESS:
                    result_item.setForeground(0, QColor(0, 128, 0))

                # 添加详细信息
                if result.details:
                    for key, value in result.details.items():
                        detail_item = QTreeWidgetItem([f"{key}: {value}"])
                        result_item.addChild(detail_item)

                tool_item.addChild(result_item)

            self.tree_view.addTopLevelItem(tool_item)
            tool_item.setExpanded(True)

    def _on_filter_changed(self, index: int):
        """过滤条件变化事件"""
        self._update_filtered_results()
        self._update_display()

    def _on_search_text_changed(self, text: str):
        """搜索文本变化事件"""
        self._update_filtered_results()
        self._update_display()

    def _on_clear_results(self):
        """清空结果事件"""
        self.clear_results()
        self.clear_results_signal.emit()

    def _on_export_results(self):
        """导出结果事件"""
        # 这里只是示例，实际实现需要打开文件对话框
        file_path = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.export_results_signal.emit(file_path)

        # 导出结果
        self._export_results_to_file(file_path)

    def _export_results_to_file(self, file_path: str):
        """导出结果到文件"""
        try:
            # 转换结果为字典
            results_dict = [result.to_dict() for result in self._results]

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)

            self.add_success(f"结果已导出到 {file_path}")
            self._logger.info(f"结果已导出到 {file_path}")
        except Exception as e:
            self.add_error(f"导出结果失败: {str(e)}")
            self._logger.error(f"导出结果失败: {str(e)}")

    def _on_tab_changed(self, index: int):
        """标签页切换事件"""
        self._update_display()


class ResultDockWidget(QDockWidget):
    """结果面板停靠窗口"""

    # 信号
    clear_results = pyqtSignal()
    export_results = pyqtSignal(str)  # 导出文件路径

    def __init__(self, parent=None):
        super().__init__("结果", parent)
        self._logger = logging.getLogger("ResultDockWidget")

        # 创建结果面板
        self.result_panel = ResultPanelWidget()
        self.setWidget(self.result_panel)

        # 设置停靠位置
        self.setAllowedAreas(Qt.BottomDockWidgetArea)

        # 设置样式
        self.setStyleSheet(
            """
            QDockWidget {
                border: 1px solid #d0d0d0;
            }
            QDockWidget::title {
                background-color: #f5f5f5;
                padding: 5px;
                border-bottom: 1px solid #d0d0d0;
            }
        """
        )

        # 连接信号
        self.result_panel.clear_results_signal.connect(self.clear_results)
        self.result_panel.export_results_signal.connect(self.export_results)

    def add_result(
        self,
        result_type: ResultType,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加结果"""
        self.result_panel.add_result(result_type, message, details, tool_name)

    def add_info(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加信息结果"""
        self.result_panel.add_info(message, details, tool_name)

    def add_success(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加成功结果"""
        self.result_panel.add_success(message, details, tool_name)

    def add_warning(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加警告结果"""
        self.result_panel.add_warning(message, details, tool_name)

    def add_error(
        self,
        message: str,
        details: Dict[str, Any] = None,
        tool_name: str = None,
    ):
        """添加错误结果"""
        self.result_panel.add_error(message, details, tool_name)

    def clear_results(self):
        """清空所有结果"""
        self.result_panel.clear_results()

    def get_results(self) -> List[ResultItem]:
        """获取所有结果"""
        return self.result_panel.get_results()

    def get_filtered_results(self) -> List[ResultItem]:
        """获取过滤后的结果"""
        return self.result_panel.get_filtered_results()

    def get_result_panel(self) -> ResultPanelWidget:
        """获取结果面板实例"""
        return self.result_panel
