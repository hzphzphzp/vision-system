#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionMaster风格主题样式表

提供白色背景、黑色字体的专业UI样式

Author: Vision System Team
Date: 2026-01-29
"""

VISION_MASTER_STYLE = """
/* ========== 全局样式 ========== */
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #000000;
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}

/* ========== 菜单栏 ========== */
QMenuBar {
    background-color: #f5f5f5;
    border-bottom: 1px solid #d4d4d4;
    padding: 2px 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    color: #000000;
}

QMenuBar::item:selected {
    background-color: #e3e3e3;
    border-radius: 3px;
}

QMenuBar::item:pressed {
    background-color: #d4d4d4;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    color: #000000;
}

QMenu::item:selected {
    background-color: #e3e3e3;
}

QMenu::separator {
    height: 1px;
    background-color: #d4d4d4;
    margin: 4px 8px;
}

/* ========== 工具栏 ========== */
QToolBar {
    background-color: #f5f5f5;
    border-bottom: 1px solid #d4d4d4;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 3px;
    padding: 4px 8px;
    color: #000000;
}

QToolBar QToolButton:hover {
    background-color: #e3e3e3;
}

QToolBar QToolButton:pressed {
    background-color: #d4d4d4;
}

/* ========== 分割器 ========== */
QSplitter::handle {
    background-color: #d4d4d4;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #a0a0a0;
}

/* ========== 停靠窗口 ========== */
QDockWidget {
    border: 1px solid #d4d4d4;
    background-color: #ffffff;
}

QDockWidget::title {
    background-color: #f5f5f5;
    padding: 6px 10px;
    border-bottom: 1px solid #d4d4d4;
    font-weight: bold;
    color: #000000;
    font-size: 12px;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    icon-size: 12px;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #e3e3e3;
    border-radius: 2px;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    border: 1px solid #d4d4d4;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #f5f5f5;
    color: #000000;
    padding: 6px 12px;
    border: 1px solid #d4d4d4;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #000000;
    border-bottom: 2px solid #ff6a00;
}

QTabBar::tab:hover:!selected {
    background-color: #e8e8e8;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #f5f5f5;
    color: #000000;
    border: 1px solid #d4d4d4;
    border-radius: 3px;
    padding: 6px 12px;
    font-weight: normal;
}

QPushButton:hover {
    background-color: #e3e3e3;
}

QPushButton:pressed {
    background-color: #d4d4d4;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #a0a0a0;
    border-color: #e0e0e0;
}

QPushButton[primary="true"] {
    background-color: #ff6a00;
    color: #ffffff;
    border: none;
}

QPushButton[primary="true"]:hover {
    background-color: #e55f00;
}

QPushButton[primary="true"]:pressed {
    background-color: #cc5500;
}

/* ========== 列表 ========== */
QListWidget, QListView {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    padding: 2px;
    color: #000000;
}

QListWidget::item, QListView::item {
    padding: 6px 10px;
    border-radius: 2px;
    margin: 1px;
    color: #000000;
}

QListWidget::item:selected, QListView::item:selected {
    background-color: #e3e3e3;
    color: #000000;
}

QListWidget::item:hover:!selected, QListView::item:hover:!selected {
    background-color: #f0f0f0;
}

/* ========== 树形控件 ========== */
QTreeWidget, QTreeView {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    padding: 2px;
    color: #000000;
}

QTreeWidget::item, QTreeView::item {
    padding: 5px 10px;
    border-radius: 2px;
    margin: 1px;
    color: #000000;
}

QTreeWidget::item:selected, QTreeView::item:selected {
    background-color: #e3e3e3;
    color: #000000;
}

QTreeWidget::item:hover:!selected, QTreeView::item:hover:!selected {
    background-color: #f0f0f0;
}

QTreeWidget::branch:has-children:closed {
    image: url(resource:branch-closed.png);
}

QTreeWidget::branch:has-children:open {
    image: url(resource:branch-open.png);
}

/* ========== 表格 ========== */
QTableWidget, QTableView {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    gridline-color: #e0e0e0;
    color: #000000;
}

QTableWidget::item, QTableView::item {
    padding: 6px 10px;
    color: #000000;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #e3e3e3;
    color: #000000;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #000000;
    padding: 6px 10px;
    font-weight: bold;
    border-bottom: 1px solid #d4d4d4;
    border-right: 1px solid #d4d4d4;
}

/* ========== 输入控件 ========== */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 3px;
    padding: 6px 10px;
    selection-background-color: #ff6a00;
    selection-color: #ffffff;
    color: #000000;
}

QLineEdit:focus {
    border-color: #ff6a00;
}

QLineEdit:hover {
    border-color: #a0a0a0;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 3px;
    padding: 6px 10px;
    min-width: 80px;
    color: #000000;
}

QComboBox:hover {
    border-color: #a0a0a0;
}

QComboBox:focus {
    border-color: #ff6a00;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    color: #000000;
    selection-background-color: #e3e3e3;
}

/* ========== Spin控件 ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 3px;
    padding: 6px 10px;
    color: #000000;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #ff6a00;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 6px;
    color: #000000;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d4d4d4;
    border-radius: 2px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #ff6a00;
    border-color: #ff6a00;
}

QCheckBox::indicator:hover {
    border-color: #a0a0a0;
}

/* ========== 单选框 ========== */
QRadioButton {
    spacing: 6px;
    color: #000000;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d4d4d4;
    border-radius: 8px;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    background-color: #ff6a00;
    border-color: #ff6a00;
}

/* ========== 组框 ========== */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 10px;
    margin-top: 8px;
    color: #000000;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #000000;
    font-weight: bold;
}

/* ========== 滚动区域 ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    width: 12px;
    background-color: #f5f5f5;
    border-radius: 0;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 12px;
    background-color: #f5f5f5;
    border-radius: 0;
}

QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a0a0a0;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #f5f5f5;
    border-top: 1px solid #d4d4d4;
    padding: 4px 8px;
    color: #000000;
}

QStatusBar::item {
    border: none;
}

/* ========== 标签 ========== */
QLabel {
    color: #000000;
}

QLabel[header="true"] {
    font-weight: bold;
    color: #000000;
}

QLabel[status="true"] {
    color: #606060;
    font-size: 11px;
}

/* ========== 帧 ========== */
QFrame[frameStyle="panel"] {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 4px;
}

QFrame[frameStyle="styled"] {
    background-color: #f5f5f5;
    border: 1px solid #d4d4d4;
    border-radius: 4px;
}

/* ========== 图形视图 ========== */
QGraphicsView {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
}

/* ========== 工具提示 ========== */
QToolTip {
    background-color: #ffffff;
    border: 1px solid #d4d4d4;
    color: #000000;
    padding: 4px 8px;
}
"""


def get_style(theme: str = "vision_master") -> str:
    """获取样式表

    Args:
        theme: 主题，可选 'vision_master'

    Returns:
        样式表字符串
    """
    return VISION_MASTER_STYLE


def apply_theme(widget, theme: str = "vision_master"):
    """应用主题到窗口

    Args:
        widget: 要应用样式的小部件
        theme: 主题名称
    """
    widget.setStyleSheet(get_style(theme))


if __name__ == "__main__":
    print("VisionMaster风格主题")
    print("  - 白色背景")
    print("  - 黑色字体")
    print("  - 橙色强调色")
