#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化主题样式表

提供统一、美观、现代的UI样式

Author: Vision System Team
Date: 2026-01-14
"""

MODERN_STYLE = """
/* ========== 全局样式 ========== */
QMainWindow, QWidget {
    background-color: #f0f2f5;
    color: #202124;
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ========== 分割器 ========== */
QSplitter::handle {
    background-color: #d1d5db;
    width: 4px;
    height: 4px;
}

QSplitter::handle:horizontal {
    width: 4px;
}

QSplitter::handle:vertical {
    height: 4px;
}

QSplitter::handle:hover {
    background-color: #3b82f6;
}

/* ========== 停靠窗口 ========== */
QDockWidget {
    border: 1px solid #dadce0;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    border-radius: 4px;
}

QDockWidget::title {
    background-color: #ffffff;
    padding: 9px 14px;
    border-bottom: 1px solid #dadce0;
    font-weight: 600;
    color: #1a73e8;
    font-size: 14px;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    icon-size: 14px;
    min-width: 20px;
    max-width: 20px;
    min-height: 20px;
    max-height: 20px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #e5e7eb;
    border-radius: 4px;
}

/* ========== 标签页 ========== */
QTabWidget::pane {
    border: 1px solid #e5e7eb;
    background-color: #ffffff;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #f3f4f6;
    color: #6b7280;
    padding: 8px 16px;
    border: 1px solid #e5e7eb;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #3b82f6;
    border-bottom: 2px solid #3b82f6;
}

QTabBar::tab:hover:selected {
    background-color: #ffffff;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #2563eb;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #d1d5db;
    color: #9ca3af;
}

/* ========== 列表 ========== */
QListWidget, QListView {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px;
    alternate-background-color: #f9fafb;
}

QListWidget::item, QListView::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px 4px;
}

QListWidget::item:selected, QListView::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

/* ========== 树形控件 ========== */
QTreeWidget, QTreeView {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px;
    alternate-background-color: #f9fafb;
}

QTreeWidget::item, QTreeView::item {
    padding: 6px 12px;
    border-radius: 4px;
    margin: 1px 2px;
}

QTreeWidget::item:selected, QTreeView::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
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
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    gridline-color: #f3f4f6;
}

QTableWidget::item, QTableView::item {
    padding: 8px 12px;
    border-radius: 4px;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

QHeaderView::section {
    background-color: #f3f4f6;
    color: #374151;
    padding: 10px 12px;
    font-weight: 600;
    border-bottom: 1px solid #e5e7eb;
}

/* ========== 输入控件 ========== */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #bfdbfe;
    color: #374151;
}

QLineEdit:focus {
    border-color: #3b82f6;
    outline: none;
}

QLineEdit:hover {
    border-color: #9ca3af;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #9ca3af;
}

QComboBox:focus {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

/* ========== Spin控件 ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3b82f6;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 8px;
    color: #374151;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #d1d5db;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

QCheckBox::indicator:hover {
    border-color: #3b82f6;
}

/* ========== 组框 ========== */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #374151;
    font-weight: 600;
}

/* ========== 滚动区域 ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    width: 10px;
    background-color: #f3f4f6;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #d1d5db;
    border-radius: 4px;
    min-height: 30px;
    margin: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9ca3af;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 10px;
    background-color: #f3f4f6;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #d1d5db;
    border-radius: 4px;
    min-width: 30px;
    margin: 4px;
}

/* ========== 菜单 ========== */
QMenuBar {
    background-color: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #dbeafe;
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item:selected {
    background-color: #dbeafe;
    border-radius: 4px;
}

/* ========== 工具栏 ========== */
QToolBar {
    background-color: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
}

QToolBar QToolButton:hover {
    background-color: #e5e7eb;
}

QToolBar QToolButton:pressed {
    background-color: #d1d5db;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #f9fafb;
    border-top: 1px solid #e5e7eb;
    padding: 4px 8px;
}

/* ========== 标签 ========== */
QLabel {
    color: #374151;
}

QLabel[header="true"] {
    font-weight: 600;
    color: #111827;
}

QLabel[status="true"] {
    color: #6b7280;
    font-size: 12px;
}

/* ========== 帧 ========== */
QFrame[frameStyle="panel"] {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

QFrame[frameStyle="styled"] {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
"""

DARK_STYLE = """
/* 深色主题 */
QMainWindow, QWidget {
    background-color: #1f2937;
    color: #f3f4f6;
}

QDockWidget::title {
    background-color: #374151;
    color: #f3f4f6;
    border-bottom: 1px solid #4b5563;
}

QTabBar::tab {
    background-color: #374151;
    color: #9ca3af;
}

QTabBar::tab:selected {
    background-color: #1f2937;
    color: #60a5fa;
}

QPushButton {
    background-color: #3b82f6;
}

QPushButton:hover {
    background-color: #2563eb;
}

QListWidget, QTreeWidget, QTableWidget {
    background-color: #374151;
    border: 1px solid #4b5563;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #1d4ed8;
    color: white;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #374151;
    border: 1px solid #4b5563;
    color: #f3f4f6;
}

QGroupBox {
    background-color: #374151;
    border: 1px solid #4b5563;
}
"""


def get_style(theme: str = "light") -> str:
    """获取样式表
    
    Args:
        theme: 主题，可选 'light' 或 'dark'
    
    Returns:
        样式表字符串
    """
    if theme == "dark":
        return MODERN_STYLE + DARK_STYLE
    return MODERN_STYLE


def apply_theme(widget, theme: str = "light"):
    """应用主题到窗口
    
    Args:
        widget: 要应用样式的小部件
        theme: 主题名称
    """
    widget.setStyleSheet(get_style(theme))


if __name__ == "__main__":
    print("可用主题:")
    print("  - light: 浅色主题（默认）")
    print("  - dark: 深色主题")
