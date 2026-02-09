#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性面板UI模块

实现VisionMaster风格的属性面板，包括：
- 工具属性展示
- 参数编辑功能
- 属性分类
- 实时参数更新

Author: Vision System Team
Date: 2026-01-05
"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

PYQT_VERSION = 5

try:
    from PyQt6.QtCore import QObject, Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QPalette
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDockWidget,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSpinBox,
        QDoubleSpinBox,
        QCheckBox,
        QComboBox,
        QGroupBox,
        QScrollArea,
        QFormLayout,
        QFrame,
        QSplitter,
        QDockWidget,
        QTreeWidget,
        QTreeWidgetItem,
        QFileDialog,
    )
    from PyQt5.QtGui import QFont, QColor, QPalette
    from PyQt5.QtCore import Qt, pyqtSignal, QObject

from core.tool_base import (
    PARAM_CHINESE_NAMES,
    PARAM_TYPE_CHINESE_NAMES,
    TOOL_CATEGORY_CHINESE_NAMES,
    ToolBase,
)


class ParameterType(Enum):
    """参数类型枚举"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    IMAGE_FILE_PATH = "image_file_path"  # 专门用于选择图片文件
    FILE_LIST = "file_list"  # 多文件列表（用于多图像选择器）
    ROI_RECT = "roi_rect"  # 矩形ROI选择
    ROI_LINE = "roi_line"  # 直线ROI选择
    ROI_CIRCLE = "roi_circle"  # 圆形ROI选择
    BUTTON = "button"  # 按钮类型（用于触发操作）
    DATA_CONTENT = "data_content"  # 数据内容选择（用于发送数据工具）
    EXTRACTION_RULE = "extraction_rule"  # 数据提取规则（用于Modbus TCP等协议）


class FilePathSelector(QWidget):
    """文件路径选择器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("FilePathSelector")
        self._file_path = ""
        self._file_filter = "所有文件 (*.*)"

        # 初始化UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 文件路径编辑框
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择文件路径...")
        layout.addWidget(self.path_edit)

        # 浏览按钮
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMaximumWidth(60)
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)

    def set_file_filter(self, filter_str: str):
        """设置文件过滤器"""
        self._file_filter = filter_str

    def set_file_path(self, path: str):
        """设置文件路径"""
        self._file_path = path
        self.path_edit.setText(path)

    def get_file_path(self) -> str:
        """获取文件路径"""
        return self.path_edit.text()

    def _on_browse(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            self._file_path if self._file_path else ".",
            self._file_filter,
        )

        if file_path:
            self.set_file_path(file_path)
            self._logger.info(f"选择文件: {file_path}")


class ImageFilePathSelector(FilePathSelector):
    """图片文件路径选择器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_file_filter(
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*.*)"
        )


class MultiImageSelectorWidget(QWidget):
    """多图像选择器控件 - 支持加载多张图片、切换和自动运行"""

    images_changed = pyqtSignal(list)
    current_index_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("MultiImageSelectorWidget")
        self._image_paths = []
        self._current_index = 0
        self._tool_instance = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        file_layout = QHBoxLayout()
        file_layout.setSpacing(5)

        self.select_btn = QPushButton("选择图片...")
        self.select_btn.setToolTip("选择多张图片文件")
        self.select_btn.clicked.connect(self._select_images)
        file_layout.addWidget(self.select_btn)

        self.add_btn = QPushButton("+")
        self.add_btn.setToolTip("添加更多图片")
        self.add_btn.setMaximumWidth(30)
        self.add_btn.clicked.connect(self._add_images)
        file_layout.addWidget(self.add_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setToolTip("清空所有图片")
        self.clear_btn.setMaximumWidth(50)
        self.clear_btn.clicked.connect(self._clear_images)
        file_layout.addWidget(self.clear_btn)

        file_layout.addStretch()
        layout.addLayout(file_layout)

        self.list_label = QLabel("未加载图片")
        self.list_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                min-height: 40px;
            }
        """)
        self.list_label.setWordWrap(True)
        layout.addWidget(self.list_label)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)

        self.prev_btn = QPushButton("◀ 上一张")
        self.prev_btn.setToolTip("切换到上一张图片")
        self.prev_btn.clicked.connect(self._previous_image)
        nav_layout.addWidget(self.prev_btn)

        self.info_label = QLabel("0 / 0")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; min-width: 80px;")
        nav_layout.addWidget(self.info_label)

        self.next_btn = QPushButton("下一张 ▶")
        self.next_btn.setToolTip("切换到下一张图片")
        self.next_btn.clicked.connect(self._next_image)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        jump_layout = QHBoxLayout()
        jump_layout.setSpacing(5)

        jump_layout.addWidget(QLabel("跳转到:"))
        self.jump_spin = QSpinBox()
        self.jump_spin.setMinimum(1)
        self.jump_spin.setMaximum(9999)
        self.jump_spin.setValue(1)
        self.jump_spin.setToolTip("输入图片序号快速跳转")
        jump_layout.addWidget(self.jump_spin)

        self.jump_btn = QPushButton("跳转")
        self.jump_btn.clicked.connect(self._jump_to_image)
        jump_layout.addWidget(self.jump_btn)

        jump_layout.addStretch()
        layout.addLayout(jump_layout)

        self.auto_run_checkbox = QCheckBox("切换图片后自动运行流程")
        self.auto_run_checkbox.setChecked(True)
        self.auto_run_checkbox.stateChanged.connect(self._on_auto_run_changed)
        layout.addWidget(self.auto_run_checkbox)

        self.loop_checkbox = QCheckBox("循环模式")
        self.loop_checkbox.setChecked(True)
        self.loop_checkbox.setToolTip("到最后一张后回到第一张")
        self.loop_checkbox.stateChanged.connect(self._on_loop_changed)
        layout.addWidget(self.loop_checkbox)

        self._update_ui()

    def set_tool_instance(self, tool):
        self._tool_instance = tool
        if tool:
            try:
                image_files = tool.get_param("图像文件列表", [])
                current_index = tool.get_param("当前图像索引", 0)
                auto_run = tool.get_param("自动运行", True)
                loop_mode = tool.get_param("循环模式", True)

                self._image_paths = image_files if image_files else []
                self._current_index = current_index
                self.auto_run_checkbox.setChecked(auto_run)
                self.loop_checkbox.setChecked(loop_mode)

                self._update_ui()
            except Exception as e:
                self._logger.error(f"同步工具数据失败: {e}")

    def _select_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            ".",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*.*)"
        )

        if file_paths:
            self._image_paths = file_paths
            self._current_index = 0
            self._update_ui()
            self._sync_to_tool()
            self.images_changed.emit(self._image_paths)
            self._logger.info(f"选择了 {len(file_paths)} 张图片")

    def _add_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "添加图片文件",
            ".",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*.*)"
        )

        if file_paths:
            self._image_paths.extend(file_paths)
            self._update_ui()
            self._sync_to_tool()
            self.images_changed.emit(self._image_paths)
            self._logger.info(f"添加了 {len(file_paths)} 张图片，总共 {len(self._image_paths)} 张")

    def _clear_images(self):
        self._image_paths = []
        self._current_index = 0
        self._update_ui()
        self._sync_to_tool()
        self.images_changed.emit(self._image_paths)
        self._logger.info("清空图片列表")

    def _previous_image(self):
        if not self._image_paths:
            return

        loop_mode = self.loop_checkbox.isChecked()

        if self._current_index > 0:
            self._current_index -= 1
        elif loop_mode:
            self._current_index = len(self._image_paths) - 1
        else:
            return

        self._update_ui()
        self._sync_to_tool()
        self.current_index_changed.emit(self._current_index)

        if self._tool_instance:
            try:
                self._tool_instance.previous_image()
            except Exception as e:
                self._logger.error(f"调用工具previous_image失败: {e}")

    def _next_image(self):
        if not self._image_paths:
            return

        loop_mode = self.loop_checkbox.isChecked()

        if self._current_index < len(self._image_paths) - 1:
            self._current_index += 1
        elif loop_mode:
            self._current_index = 0
        else:
            return

        self._update_ui()
        self._sync_to_tool()
        self.current_index_changed.emit(self._current_index)

        if self._tool_instance:
            try:
                self._tool_instance.next_image()
            except Exception as e:
                self._logger.error(f"调用工具next_image失败: {e}")

    def _jump_to_image(self):
        if not self._image_paths:
            return

        target_index = self.jump_spin.value() - 1

        if 0 <= target_index < len(self._image_paths):
            self._current_index = target_index
            self._update_ui()
            self._sync_to_tool()
            self.current_index_changed.emit(self._current_index)

            if self._tool_instance:
                try:
                    self._tool_instance.goto_image(target_index)
                except Exception as e:
                    self._logger.error(f"调用工具goto_image失败: {e}")

    def _on_auto_run_changed(self, state):
        if self._tool_instance:
            try:
                self._tool_instance.set_param("自动运行", bool(state))
            except Exception as e:
                self._logger.error(f"设置自动运行参数失败: {e}")

    def _on_loop_changed(self, state):
        if self._tool_instance:
            try:
                self._tool_instance.set_param("循环模式", bool(state))
            except Exception as e:
                self._logger.error(f"设置循环模式参数失败: {e}")

    def _sync_to_tool(self):
        if self._tool_instance:
            try:
                self._tool_instance.set_param("图像文件列表", self._image_paths)
                self._tool_instance.set_param("当前图像索引", self._current_index)
                self._logger.debug(f"同步到工具: index={self._current_index}, total={len(self._image_paths)}")
            except Exception as e:
                self._logger.error(f"同步到工具失败: {e}")

    def _update_ui(self):
        total = len(self._image_paths)

        if total == 0:
            self.list_label.setText("未加载图片")
            self.info_label.setText("0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.jump_btn.setEnabled(False)
            self.jump_spin.setMaximum(1)
        else:
            display_text = f"已加载 {total} 张图片:\n"
            for i, path in enumerate(self._image_paths):
                marker = "▶ " if i == self._current_index else "   "
                filename = os.path.basename(path)
                display_text += f"{marker}[{i+1}] {filename}\n"
            self.list_label.setText(display_text)

            self.info_label.setText(f"{self._current_index + 1} / {total}")

            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.jump_btn.setEnabled(True)
            self.jump_spin.setMaximum(total)
            self.jump_spin.setValue(self._current_index + 1)

    def get_value(self):
        return {
            "图像文件列表": self._image_paths,
            "当前图像索引": self._current_index,
            "自动运行": self.auto_run_checkbox.isChecked(),
            "循环模式": self.loop_checkbox.isChecked(),
        }


class ROISelectButton(QWidget):
    """ROI选择按钮组件"""

    roi_clicked = pyqtSignal(str)  # ROI点击信号，参数为参数名
    roi_changed = pyqtSignal(dict)  # ROI数据变更信号

    def __init__(self, param_name: str = "roi", parent=None):
        super().__init__(parent)
        self._param_name = param_name
        self._roi_data = {}
        self._logger = logging.getLogger("ROISelectButton")

        # 初始化UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # ROI信息显示标签
        self.info_label = QLabel("未设置")
        self.info_label.setStyleSheet("color: #888888; min-width: 150px;")
        layout.addWidget(self.info_label)

        # 选择ROI按钮
        self.select_btn = QPushButton("选择ROI...")
        self.select_btn.setMaximumWidth(100)
        layout.addWidget(self.select_btn)

        # 清除ROI按钮
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setMaximumWidth(50)
        self.clear_btn.setEnabled(False)
        layout.addWidget(self.clear_btn)

        # 连接信号
        self.select_btn.clicked.connect(self._on_select_roi)
        self.clear_btn.clicked.connect(self._on_clear_roi)

    def set_roi_data(self, roi_data: dict):
        """设置ROI数据"""
        self._roi_data = roi_data.copy()
        self._update_info_display()

    def get_roi_data(self) -> dict:
        """获取ROI数据"""
        return self._roi_data.copy()

    def _update_info_display(self):
        """更新信息显示"""
        if not self._roi_data:
            self.info_label.setText("未设置")
            self.info_label.setStyleSheet("color: #888888;")
            self.clear_btn.setEnabled(False)
        else:
            roi_type = self._roi_data.get("type", "unknown")
            if roi_type == "rect":
                text = f"矩形: {self._roi_data.get('width', 0)}x{self._roi_data.get('height', 0)}"
            elif roi_type == "line":
                text = f"直线: ({self._roi_data.get('x1', 0)}, {self._roi_data.get('y1', 0)})"
            elif roi_type == "circle":
                text = f"圆形: r={self._roi_data.get('radius', 0)}"
            else:
                text = "已设置"

            self.info_label.setText(text)
            self.info_label.setStyleSheet("color: #00FF00;")
            self.clear_btn.setEnabled(True)

    def _on_select_roi(self):
        """选择ROI"""
        self.roi_clicked.emit(self._param_name)

    def _on_clear_roi(self):
        """清除ROI"""
        self._roi_data = {}
        self._update_info_display()
        self.roi_changed.emit(self._roi_data)


class ParameterWidgetFactory:
    """参数编辑器工厂类"""

    @staticmethod
    def create_parameter_widget(
        param_type: ParameterType, value: Any = None, **kwargs
    ) -> Tuple[QWidget, QWidget]:
        """创建参数编辑器

        Args:
            param_type: 参数类型
            value: 参数初始值
            **kwargs: 额外参数
                - min_value: 最小值（用于数值类型）
                - max_value: 最大值（用于数值类型）
                - step: 步长（用于数值类型）
                - options: 选项列表（用于枚举类型）
                - tooltip: 提示信息
                - placeholder: 占位符文本

        Returns:
            标签和编辑器控件
        """
        label = QLabel(kwargs.get("label", "参数"))
        widget = None

        if param_type == ParameterType.STRING:
            widget = QLineEdit()
            if value is not None:
                widget.setText(str(value))
            if "placeholder" in kwargs:
                widget.setPlaceholderText(kwargs["placeholder"])
            widget.setStyleSheet(
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

        elif param_type == ParameterType.INTEGER:
            widget = QSpinBox()
            widget.setRange(
                kwargs.get("min_value", -2147483648),
                kwargs.get("max_value", 2147483647),
            )
            widget.setSingleStep(kwargs.get("step", 1))
            if value is not None:
                widget.setValue(int(value))
            widget.setStyleSheet(
                """
                QSpinBox {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px 5px;
                    background-color: white;
                    color: #2c3e50;
                    font-size: 11px;
                }
                QSpinBox:focus {
                    border-color: #3498db;
                    outline: none;
                }
                QSpinBox::up-button,
                QSpinBox::down-button {
                    width: 20px;
                    background-color: #ecf0f1;
                    border-left: 1px solid #bdc3c7;
                }
                QSpinBox::up-button:hover,
                QSpinBox::down-button:hover {
                    background-color: #bdc3c7;
                }
            """
            )

        elif param_type == ParameterType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(
                kwargs.get("min_value", -1e308), kwargs.get("max_value", 1e308)
            )
            widget.setSingleStep(kwargs.get("step", 0.1))
            widget.setDecimals(kwargs.get("decimals", 2))
            if value is not None:
                widget.setValue(float(value))
            widget.setStyleSheet(
                """
                QDoubleSpinBox {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px 5px;
                    background-color: white;
                    color: #2c3e50;
                    font-size: 11px;
                }
                QDoubleSpinBox:focus {
                    border-color: #3498db;
                    outline: none;
                }
                QDoubleSpinBox::up-button,
                QDoubleSpinBox::down-button {
                    width: 20px;
                    background-color: #ecf0f1;
                    border-left: 1px solid #bdc3c7;
                }
                QDoubleSpinBox::up-button:hover,
                QDoubleSpinBox::down-button:hover {
                    background-color: #bdc3c7;
                }
            """
            )

        elif param_type == ParameterType.BOOLEAN:
            widget = QCheckBox()
            if value is not None:
                widget.setChecked(bool(value))
            widget.setStyleSheet(
                """
                QCheckBox {
                    color: #2c3e50;
                    font-size: 11px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #3498db;
                    border-color: #2980b9;
                }
            """
            )

        elif param_type == ParameterType.ENUM:
            widget = QComboBox()
            options = kwargs.get("options", [])
            option_labels = kwargs.get("option_labels", {}) or {}
            
            # 使用print代替logger，因为静态方法中没有self
            print(f"【属性面板】创建ENUM控件: param_name={kwargs.get('param_name', 'unknown')}, value='{value}', options数量={len(options)}")
            print(f"【属性面板】ENUM选项: {options}")

            if options:
                # 使用 option_labels 显示中文名称，如果没有则使用原始值
                for option in options:
                    display_text = option_labels.get(option, option)
                    widget.addItem(display_text, option)
                    print(f"【属性面板】添加选项: display_text='{display_text}', option='{option}'")
            else:
                # 默认选项
                widget.addItems(["选项1", "选项2"])

            # 设置当前选中项（根据实际值）
            if value is not None and str(value).strip():
                print(f"【属性面板】设置当前值: '{value}'")
                # 查找匹配的值
                current_index = widget.findData(value)
                print(f"【属性面板】findData结果: index={current_index}")
                if current_index >= 0:
                    widget.setCurrentIndex(current_index)
                    print(f"【属性面板】已设置当前索引: {current_index}")
                else:
                    # 如果找不到精确匹配，尝试字符串比较
                    print(f"【属性面板】使用setCurrentText: '{str(value)}'")
                    widget.setCurrentText(str(value))
            else:
                print(f"【属性面板】值为空，不设置当前选中项")
            widget.setStyleSheet(
                """
                QComboBox {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px 8px;
                    background-color: white;
                    color: #2c3e50;
                    font-size: 11px;
                    min-width: 120px;
                }
                QComboBox:focus {
                    border-color: #3498db;
                    outline: none;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: url(:/icons/down_arrow.png);
                    width: 8px;
                    height: 8px;
                }
            """
            )

        elif param_type == ParameterType.IMAGE_FILE_PATH:
            widget = ImageFilePathSelector()
            if value is not None:
                widget.set_file_path(str(value))

        elif param_type == ParameterType.FILE_LIST:
            widget = MultiImageSelectorWidget()

        elif param_type == ParameterType.FILE_PATH:
            widget = FilePathSelector()
            if value is not None:
                widget.set_file_path(str(value))

        elif param_type == ParameterType.ROI_RECT:
            widget = ROISelectButton(
                param_name=kwargs.get("param_name", kwargs.get("label", "roi"))
            )
            if value is not None:
                widget.set_roi_data(value if isinstance(value, dict) else {})

        elif param_type == ParameterType.ROI_LINE:
            widget = ROISelectButton(
                param_name=kwargs.get(
                    "param_name", kwargs.get("label", "line_roi")
                )
            )
            if value is not None:
                widget.set_roi_data(value if isinstance(value, dict) else {})

        elif param_type == ParameterType.ROI_CIRCLE:
            widget = ROISelectButton(
                param_name=kwargs.get(
                    "param_name", kwargs.get("label", "circle_roi")
                )
            )
            if value is not None:
                widget.set_roi_data(value if isinstance(value, dict) else {})

        elif param_type == ParameterType.BUTTON:
            widget = QPushButton(kwargs.get("button_text", "点击操作"))
            button_callback = kwargs.get("button_callback")
            if button_callback and callable(button_callback):
                widget.clicked.connect(button_callback)
            widget.setStyleSheet(
                """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f618d;
                }
            """
            )

        elif param_type == ParameterType.DATA_CONTENT:
            # 导入数据内容选择器
            from ui.data_content_selector import DataContentSelector
            
            widget = DataContentSelector()
            if value is not None:
                widget.set_text(str(value))
            
            # 设置可用模块数据
            available_modules = kwargs.get("available_modules", {})
            if available_modules:
                widget.set_available_modules(available_modules)

        elif param_type == ParameterType.EXTRACTION_RULE:
            # 导入数据提取规则控件
            from ui.widgets.extraction_rule_widget import ExtractionRuleWidget
            
            widget = ExtractionRuleWidget()
            if value is not None:
                widget.set_rule(value)

        # 设置提示信息
        if "tooltip" in kwargs:
            label.setToolTip(kwargs["tooltip"])
            if widget is not None:
                widget.setToolTip(kwargs["tooltip"])

        return label, widget


class PropertyPanelWidget(QWidget):
    """属性面板"""

    # 信号
    property_changed = pyqtSignal(
        str, str, object
    )  # tool_name, property_name, new_value
    roi_select_requested = pyqtSignal(
        str, str, object
    )  # tool_name, param_name, current_image

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("PropertyPanelWidget")
        self._current_tool: Optional[ToolBase] = None
        self._parameter_widgets: Dict[str, QWidget] = {}
        self._current_image = None
        self._available_modules: Dict[str, Dict[str, Any]] = {}  # 可用模块数据

        # 初始化UI
        self._init_ui()
    
    def set_available_modules(self, modules: Dict[str, Dict[str, Any]]):
        """设置可用模块数据
        
        Args:
            modules: {模块名: {字段名: 值}}
        """
        self._available_modules = modules
        self._logger.info(f"设置可用模块数据: {list(modules.keys())}, 控件数量: {len(self._parameter_widgets)}")
        
        # 更新已创建的数据内容选择器控件
        updated_count = 0
        for param_name, widget in self._parameter_widgets.items():
            if hasattr(widget, 'set_available_modules'):
                widget.set_available_modules(modules)
                self._logger.debug(f"更新控件 {param_name} 的可用模块数据")
                updated_count += 1
        
        if updated_count > 0:
            self._logger.info(f"已更新 {updated_count} 个数据内容选择器控件")

    def _init_ui(self):
        """初始化UI组件"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # 标题栏
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)

        title_icon = QLabel("⚙️")
        title_icon.setStyleSheet("font-size: 14px;")
        title_layout.addWidget(title_icon)

        title_label = QLabel("属性面板")
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(title_label)

        main_layout.addWidget(title_container)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(
            "border: none; border-bottom: 1px solid #e0e0e0; margin: 2px 0;"
        )
        main_layout.addWidget(separator)

        # 工具信息区域
        self.tool_info_widget = QGroupBox("工具信息")
        self.tool_info_widget.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        info_layout = QFormLayout(self.tool_info_widget)
        info_layout.setContentsMargins(10, 15, 10, 10)
        info_layout.setSpacing(8)
        info_layout.setVerticalSpacing(8)

        # 工具名称
        self.tool_name_edit = QLineEdit()
        self.tool_name_edit.setReadOnly(True)
        self.tool_name_edit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 4px 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
            }
        """
        )
        info_layout.addRow("名称:", self.tool_name_edit)

        # 工具类型
        self.tool_type_label = QLabel("未选择工具")
        self.tool_type_label.setStyleSheet(
            """
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 4px 0;
            }
        """
        )
        info_layout.addRow("类型:", self.tool_type_label)

        main_layout.addWidget(self.tool_info_widget)

        # 参数配置区域
        params_container = QWidget()
        params_layout = QVBoxLayout(params_container)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(4)

        params_header = QLabel("参数配置")
        params_header.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        params_header.setStyleSheet("color: #2c3e50; margin-top: 6px;")
        params_layout.addWidget(params_header)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QScrollArea::viewport {
                background-color: white;
            }
        """
        )

        # 属性内容
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_layout.setContentsMargins(6, 6, 6, 6)
        self.properties_layout.setSpacing(6)

        # 空状态
        self.empty_label = QLabel("选择工具查看属性")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            """
            QLabel {
                color: #95a5a6;
                font-style: italic;
                padding: 30px 10px;
                font-size: 12px;
            }
        """
        )
        self.properties_layout.addWidget(self.empty_label)

        scroll_area.setWidget(self.properties_widget)
        params_layout.addWidget(scroll_area, 1)

        main_layout.addWidget(params_container, 1)

        # 底部按钮区域
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 4, 0, 0)
        button_layout.setSpacing(8)

        reset_btn = QPushButton("重置参数")
        reset_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """
        )
        reset_btn.clicked.connect(self._on_reset_params)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()
        main_layout.addWidget(button_container)

    def show_tool_properties(self, tool: ToolBase):
        """显示工具属性

        Args:
            tool: 工具实例
        """
        self._current_tool = tool

        # 更新工具信息
        self.tool_name_edit.setText(tool.name)
        self.tool_type_label.setText(f"{tool.tool_category}.{tool.tool_name}")

        # 清空现有属性
        self._clear_properties()
        self._parameter_widgets.clear()  # 清空控件引用

        # 隐藏空状态
        self.empty_label.hide()

        # 显示工具参数
        self._display_parameters(tool)

    def clear_properties(self):
        """清空属性显示"""
        self._logger.info("清空属性显示")
        self._current_tool = None

        # 重置工具信息
        self.tool_name_edit.setText("")
        self.tool_type_label.setText("未选择工具")

        # 清空现有属性
        self._clear_properties()
        self._parameter_widgets.clear()

        # 显示空状态
        self.empty_label.show()

    def _clear_properties(self):
        """清空现有属性控件"""
        # 删除所有子控件
        for i in reversed(range(self.properties_layout.count())):
            widget = self.properties_layout.itemAt(i).widget()
            if widget and widget != self.empty_label:
                widget.setParent(None)

    def _display_parameters(self, tool: ToolBase):
        """显示工具参数

        Args:
            tool: 工具实例
        """
        # 使用新的方法获取参数详细信息
        params = tool.get_param_with_details()

        if not params:
            # 没有参数，显示提示
            no_params_label = QLabel("该工具没有可编辑的参数")
            no_params_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_params_label.setStyleSheet(
                """
                QLabel {
                    color: #95a5a6;
                    font-style: italic;
                    margin: 20px 0;
                    font-size: 12px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }
            """
            )
            self.properties_layout.addWidget(no_params_label)
            return

        # 创建参数组
        param_group = QGroupBox("参数配置")
        param_group.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: white;
            }
        """
        )
        param_layout = QFormLayout(param_group)
        param_layout.setContentsMargins(12, 20, 12, 12)
        param_layout.setSpacing(10)
        param_layout.setVerticalSpacing(10)

        # 检查是否为相机工具
        is_camera_tool = (
            hasattr(tool, "tool_name") and tool.tool_name == "相机"
        )

        # 如果是相机工具，只显示相机设置按钮，不显示具体参数
        if is_camera_tool:
            # 为相机工具添加设置按钮
            self._add_camera_settings_button(tool, param_layout)
        else:
            # 非相机工具，正常显示所有参数
            # 遍历参数并创建编辑器
            for param_name, param_info in params.items():
                # 使用中文显示名称
                display_name = param_info["display_name"]
                param_value = param_info["value"]
                param_type = param_info.get(
                    "type", "string"
                )  # 获取参数类型信息
                description = param_info["description"]
                unit = param_info.get("unit", "")
                options = param_info.get("options")  # 获取枚举选项
                option_labels = param_info.get(
                    "option_labels"
                )  # 获取选项标签映射

                # 确定参数类型（优先使用参数指定的类型）
                qt_param_type = self._get_parameter_type(
                    param_value, param_type
                )

                # 准备创建编辑器的参数
                widget_kwargs = {
                    "label": display_name,
                    "param_name": param_name,
                    "tooltip": description,
                    "options": options,
                    "option_labels": option_labels,
                }
                
                # 如果是数据内容选择器类型，传递可用模块数据
                if qt_param_type == ParameterType.DATA_CONTENT:
                    widget_kwargs["available_modules"] = self._available_modules
                    self._logger.debug(f"创建数据内容选择器，可用模块: {list(self._available_modules.keys())}")

                # 创建编辑器
                label, editor = ParameterWidgetFactory.create_parameter_widget(
                    qt_param_type,
                    param_value,
                    **widget_kwargs
                )

                # 设置标签样式
                label.setStyleSheet(
                    """
                    QLabel {
                        color: #2c3e50;
                        font-size: 11px;
                        min-width: 80px;
                        padding: 2px 0;
                    }
                """
                )

                # 如果有单位，添加到标签
                if unit:
                    label.setText(f"{display_name} ({unit})")
                    label.setStyleSheet(
                        """
                        QLabel {
                            color: #7f8c8d;
                            font-size: 10px;
                            min-width: 80px;
                            padding: 2px 0;
                            font-style: italic;
                        }
                    """
                    )

                # 连接信号
                self._connect_parameter_signal(editor, param_name)

                # 添加到布局
                param_layout.addRow(label, editor)

                # 保存编辑器引用
                self._parameter_widgets[param_name] = editor

        # 初始设置模型路径可见性（仅YOLO26-CPU工具）
        if hasattr(tool, "tool_name") and tool.tool_name == "YOLO26-CPU":
            model_type = tool.get_param("model_type", "custom")
            model_path_widget = self._parameter_widgets.get("model_path")
            if model_path_widget:
                model_path_widget.setVisible(model_type == "custom")

        if hasattr(tool, "tool_name") and tool.tool_name == "多图像选择器":
            image_files_widget = self._parameter_widgets.get("图像文件列表")
            if image_files_widget and hasattr(image_files_widget, 'set_tool_instance'):
                image_files_widget.set_tool_instance(tool)
                self._logger.info("多图像选择器控件已设置工具实例")

        self.properties_layout.addWidget(param_group)

    def _add_camera_settings_button(self, tool, param_layout):
        """为相机工具添加设置按钮

        Args:
            tool: 相机工具实例
            param_layout: 表单布局
        """
        button_layout = QHBoxLayout()

        settings_btn = QPushButton("相机设置")
        settings_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        settings_btn.clicked.connect(
            lambda: self._on_camera_settings_clicked(tool)
        )
        button_layout.addWidget(settings_btn)

        button_layout.addStretch()

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        param_layout.addRow("", button_widget)

    def _on_camera_settings_clicked(self, tool):
        """相机设置按钮点击事件"""
        self._logger.info("点击相机设置按钮")
        if hasattr(tool, "show_settings_dialog"):
            parent = self.window() if hasattr(self, "window") else None
            tool.show_settings_dialog(parent)

    def _get_parameter_type(
        self, value: Any, param_type: str = None
    ) -> ParameterType:
        """获取参数类型

        Args:
            value: 参数值
            param_type: 参数类型信息（可选）

        Returns:
            参数类型
        """
        # 优先使用参数指定的类型
        if param_type:
            param_type_lower = param_type.lower()
            if param_type_lower == "image_file_path":
                return ParameterType.IMAGE_FILE_PATH
            elif param_type_lower == "file_list":
                return ParameterType.FILE_LIST
            elif param_type_lower == "file_path":
                return ParameterType.FILE_PATH
            elif param_type_lower == "directory_path":
                return ParameterType.DIRECTORY_PATH
            elif param_type_lower == "boolean":
                return ParameterType.BOOLEAN
            elif param_type_lower == "integer":
                return ParameterType.INTEGER
            elif param_type_lower == "float":
                return ParameterType.FLOAT
            elif param_type_lower == "enum":
                return ParameterType.ENUM
            elif param_type_lower == "roi_rect":
                return ParameterType.ROI_RECT
            elif param_type_lower == "roi_line":
                return ParameterType.ROI_LINE
            elif param_type_lower == "roi_circle":
                return ParameterType.ROI_CIRCLE
            elif param_type_lower == "data_content":
                return ParameterType.DATA_CONTENT
            elif param_type_lower == "extraction_rule":
                return ParameterType.EXTRACTION_RULE

        # 根据值类型猜测
        if isinstance(value, bool):
            return ParameterType.BOOLEAN
        elif isinstance(value, int):
            return ParameterType.INTEGER
        elif isinstance(value, float):
            return ParameterType.FLOAT
        elif isinstance(value, (list, tuple)):
            return ParameterType.ENUM
        elif isinstance(value, dict):
            # 如果是字典且包含ROI相关键，可能是ROI类型
            if "type" in value:
                roi_type = value.get("type")
                if roi_type == "rect":
                    return ParameterType.ROI_RECT
                elif roi_type == "line":
                    return ParameterType.ROI_LINE
                elif roi_type == "circle":
                    return ParameterType.ROI_CIRCLE
            return ParameterType.STRING
        elif isinstance(value, str):
            return ParameterType.STRING
        else:
            return ParameterType.STRING

    def _connect_parameter_signal(self, widget: QWidget, param_name: str):
        """连接参数编辑器信号

        Args:
            widget: 参数编辑器控件
            param_name: 参数名称
        """
        # 使用functools.partial避免lambda导致的引用循环
        from functools import partial

        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(
                partial(self._on_parameter_changed, param_name)
            )
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(
                partial(self._on_parameter_changed, param_name)
            )
        elif isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(
                partial(self._on_parameter_changed, param_name)
            )
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(
                partial(self._on_checkbox_changed, param_name)
            )
        elif isinstance(widget, QComboBox):
            # 使用lambda获取当前选中的userData而不是显示文本
            widget.currentIndexChanged.connect(
                lambda index, w=widget, p=param_name: self._on_combobox_changed(p, w)
            )
            # 备用信号：当用户手动选择时触发
            widget.activated.connect(
                lambda index, w=widget, p=param_name: self._on_combobox_activated(p, w)
            )
        elif isinstance(widget, FilePathSelector):
            # 文件路径选择器连接信号
            widget.path_edit.textChanged.connect(
                partial(self._on_parameter_changed, param_name)
            )
        elif isinstance(widget, ROISelectButton):
            # ROI选择器连接信号
            widget.roi_changed.connect(
                partial(self._on_parameter_changed, param_name)
            )
            # ROI点击信号需要外部处理，连接到主窗口
            widget.roi_clicked.connect(
                partial(self._on_roi_select_clicked, param_name)
            )
        else:
            # 检查是否是 DataContentSelector（使用 duck typing）
            if hasattr(widget, 'data_selected') and hasattr(widget, 'text_edit'):
                # 数据内容选择器连接信号
                widget.data_selected.connect(
                    partial(self._on_parameter_changed, param_name)
                )
                # 同时连接文本框的 textChanged 信号作为备用
                widget.text_edit.textChanged.connect(
                    partial(self._on_parameter_changed, param_name)
                )
                self._logger.info(f"【属性面板】已连接 DataContentSelector 信号: {param_name}")
            
            # 检查是否是 ExtractionRuleWidget（使用 duck typing）
            elif hasattr(widget, 'rule_changed') and hasattr(widget, 'get_rule_dict'):
                # 数据提取规则控件连接信号
                widget.rule_changed.connect(
                    partial(self._on_parameter_changed, param_name)
                )
                self._logger.info(f"【属性面板】已连接 ExtractionRuleWidget 信号: {param_name}")

    def _on_checkbox_changed(self, param_name: str, state: int):
        """复选框状态变更处理"""
        self._on_parameter_changed(param_name, bool(state))

    def _on_combobox_changed(self, param_name: str, combobox: QComboBox):
        """下拉框选项变更处理（currentIndexChanged信号）
        
        Args:
            param_name: 参数名称
            combobox: QComboBox控件
        """
        # 获取当前选中的userData（实际值）而不是显示文本
        current_data = combobox.currentData()
        current_text = combobox.currentText()
        current_index = combobox.currentIndex()
        self._logger.info(f"【属性面板】下拉框变更(currentIndexChanged): {param_name}, index={current_index}, currentText='{current_text}', currentData='{current_data}'")
        
        # 使用userData作为参数值（如果存在），否则使用显示文本
        value = current_data if current_data is not None else current_text
        self._on_parameter_changed(param_name, value)
    
    def _on_combobox_activated(self, param_name: str, combobox: QComboBox):
        """下拉框选项激活处理（activated信号）- 当用户手动选择时触发
        
        Args:
            param_name: 参数名称
            combobox: QComboBox控件
        """
        # 获取当前选中的userData（实际值）而不是显示文本
        current_data = combobox.currentData()
        current_text = combobox.currentText()
        current_index = combobox.currentIndex()
        self._logger.info(f"【属性面板】下拉框激活(activated): {param_name}, index={current_index}, currentText='{current_text}', currentData='{current_data}'")
        
        # 使用userData作为参数值（如果存在），否则使用显示文本
        value = current_data if current_data is not None else current_text
        self._on_parameter_changed(param_name, value)

    def _on_parameter_changed(self, param_name: str, value: Any):
        """参数变更事件

        Args:
            param_name: 参数名称
            value: 新的参数值
        """
        if self._current_tool:
            self._logger.info(f"【属性面板】参数变更: {param_name} = '{value}' (类型: {type(value).__name__})")
            
            # 记录变更前的值
            old_value = self._current_tool.get_param(param_name, "<未设置>")
            self._logger.info(f"【属性面板】参数旧值: {param_name} = '{old_value}'")
            
            # 设置新值
            self._current_tool.set_param(param_name, value)
            
            # 验证新值是否已保存
            saved_value = self._current_tool.get_param(param_name, "<未设置>")
            self._logger.info(f"【属性面板】参数新值验证: {param_name} = '{saved_value}'")

            # 调用initialize方法应用参数变更
            if hasattr(self._current_tool, "initialize") and callable(
                self._current_tool.initialize
            ):
                try:
                    params = self._current_tool.get_all_params()
                    self._current_tool.initialize(params)
                    self._logger.debug(
                        f"工具已重新初始化: {self._current_tool.name}"
                    )
                except Exception as e:
                    self._logger.warning(f"工具重新初始化失败: {e}")

            self.property_changed.emit(
                self._current_tool.name, param_name, value
            )

        # 特殊处理YOLO26-CPU工具的模型路径显示
        if (
            param_name == "model_type"
            and self._current_tool
            and hasattr(self._current_tool, "tool_name")
            and self._current_tool.tool_name == "YOLO26-CPU"
        ):
            model_path_widget = self._parameter_widgets.get("model_path")
            if model_path_widget:
                model_path_widget.setVisible(value == "custom")

    def _on_roi_select_clicked(self, param_name: str):
        """ROI选择按钮点击事件

        Args:
            param_name: 参数名称
        """
        self._logger.error(f"ROI选择按钮点击: param_name={param_name}")
        # 发送信号给主窗口处理
        self.roi_select_requested.emit(
            self._current_tool.name if self._current_tool else "",
            param_name,
            self._current_image,
        )

    def _on_reset_params(self):
        """重置参数"""
        if self._current_tool:
            self._logger.info(f"重置工具参数: {self._current_tool.name}")
            self._current_tool.reset_params()
            # 重新显示属性
            self.show_tool_properties(self._current_tool)

    def update_parameter(self, param_name: str, value: Any):
        """更新参数值

        Args:
            param_name: 参数名称
            value: 新的参数值
        """
        if param_name in self._parameter_widgets:
            widget = self._parameter_widgets[param_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                if str(value) in [
                    widget.itemText(i) for i in range(widget.count())
                ]:
                    widget.setCurrentText(str(value))

    def get_current_tool(self) -> Optional[ToolBase]:
        """获取当前显示属性的工具

        Returns:
            当前工具实例
        """
        return self._current_tool


class PropertyDockWidget(QDockWidget):
    """属性面板停靠窗口"""

    # 信号
    property_changed = pyqtSignal(
        str, str, Any
    )  # tool_name, property_name, new_value
    roi_select_requested = pyqtSignal(
        str, str, object
    )  # tool_name, param_name, current_image

    def __init__(self, parent=None):
        super().__init__("属性", parent)
        self._logger = logging.getLogger("PropertyDockWidget")

        # 创建属性面板
        self.property_panel = PropertyPanelWidget()
        self.setWidget(self.property_panel)

        # 设置停靠位置
        self.setAllowedAreas(Qt.RightDockWidgetArea)

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
        self.property_panel.property_changed.connect(self.property_changed)
        self.property_panel.roi_select_requested.connect(
            self.roi_select_requested
        )

    def widget(self) -> PropertyPanelWidget:
        """获取属性面板控件"""
        return self.property_panel

    def show_tool_properties(self, tool: ToolBase):
        """显示工具属性

        Args:
            tool: 要显示属性的工具
        """
        self.property_panel.show_tool_properties(tool)

    def clear_properties(self):
        """清空属性显示"""
        self.property_panel.clear_properties()

    def update_parameter(self, param_name: str, value: Any):
        """更新参数值

        Args:
            param_name: 参数名称
            value: 新的参数值
        """
        self.property_panel.update_parameter(param_name, value)

    def get_property_panel(self) -> PropertyPanelWidget:
        """获取属性面板实例

        Returns:
            属性面板实例
        """
        return self.property_panel
