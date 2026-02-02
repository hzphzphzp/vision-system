#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt Compatibility Layer

统一PyQt5/PyQt6/PySide6的差异，提供一致的API接口

使用方式:
    from ui.qt_compat import Qt, Signal, Slot, QApplication, ...

支持:
    - PySide6 (推荐)
    - PyQt6
    - PyQt5 (向后兼容)

Author: Vision System Team
Date: 2026-02-02
"""

import sys
from typing import Any, Optional, Dict, List, Tuple, Callable
from enum import Enum

# 优先级: PySide6 > PyQt6 > PyQt5
_QT_BACKEND = None


def _get_qt_backend():
    """检测并返回可用的Qt后端"""
    global _QT_BACKEND
    
    if _QT_BACKEND is not None:
        return _QT_BACKEND
    
    # 尝试导入顺序
    backends = [
        ('PySide6', 'PySide6'),
        ('PyQt6', 'PyQt6'),  
        ('PyQt5', 'PyQt5'),
    ]
    
    for backend_name, module_prefix in backends:
        try:
            if backend_name == 'PySide6':
                from PySide6 import QtCore, QtGui, QtWidgets
                _QT_BACKEND = {
                    'name': 'PySide6',
                    'QtCore': QtCore,
                    'QtGui': QtGui, 
                    'QtWidgets': QtWidgets,
                    'version': QtCore.qVersion() if hasattr(QtCore, 'qVersion') else '6.x',
                }
                print(f'[Qt Compat] Using PySide6')
                return _QT_BACKEND
            elif backend_name == 'PyQt6':
                from PyQt6 import QtCore, QtGui, QtWidgets
                _QT_BACKEND = {
                    'name': 'PyQt6',
                    'QtCore': QtCore,
                    'QtGui': QtGui,
                    'QtWidgets': QtWidgets,
                    'version': QtCore.qVersion() if hasattr(QtCore, 'qVersion') else '6.x',
                }
                print(f'[Qt Compat] Using PyQt6')
                return _QT_BACKEND
            else:  # PyQt5
                from PyQt5 import QtCore, QtGui, QtWidgets
                _QT_BACKEND = {
                    'name': 'PyQt5',
                    'QtCore': QtCore,
                    'QtGui': QtGui,
                    'QtWidgets': QtWidgets,
                    'version': QtCore.qVersion() if hasattr(QtCore, 'qVersion') else '5.x',
                }
                print(f'[Qt Compat] Using PyQt5')
                return _QT_BACKEND
        except ImportError:
            continue
    
    raise ImportError('No Qt backend available (PySide6/PyQt6/PyQt5)')


# 获取Qt后端
_QT = _get_qt_backend()
_QtCore = _QT['QtCore']
_QtGui = _QT['QtGui']
_QtWidgets = _QT['QtWidgets']


# ============ 核心类型统一 ============

# 版本信息
QT_VERSION = _QT['name']
QT_VERSION_STR = _QT['version']

# PySide6特殊处理：某些类在不同模块中
if QT_VERSION == 'PySide6':
    _QAction = _QtGui.QAction
    _QActionGroup = _QtGui.QActionGroup
    _QShortcut = _QtGui.QShortcut
else:
    _QAction = _QtWidgets.QAction
    _QActionGroup = _QtWidgets.QActionGroup
    _QShortcut = _QtWidgets.QShortcut

# 基础类
QApplication = _QtWidgets.QApplication
QWidget = _QtWidgets.QWidget
QFrame = _QtWidgets.QFrame
QDialog = _QtWidgets.QDialog
QMainWindow = _QtWidgets.QMainWindow
QMenu = _QtWidgets.QMenu
QMenuBar = _QtWidgets.QMenuBar
QToolBar = _QtWidgets.QToolBar
QDockWidget = _QtWidgets.QDockWidget
QSplitter = _QtWidgets.QSplitter
QScrollArea = _QtWidgets.QScrollArea
QStackedWidget = _QtWidgets.QStackedWidget
QTabWidget = _QtWidgets.QTabWidget
QMdiArea = _QtWidgets.QMdiArea
QMdiSubWindow = _QtWidgets.QMdiSubWindow

# 按钮和输入
QPushButton = _QtWidgets.QPushButton
QToolButton = _QtWidgets.QToolButton
QRadioButton = _QtWidgets.QRadioButton
QCheckBox = _QtWidgets.QCheckBox
QComboBox = _QtWidgets.QComboBox
QSpinBox = _QtWidgets.QSpinBox
QDoubleSpinBox = _QtWidgets.QDoubleSpinBox
QSlider = _QtWidgets.QSlider
QProgressBar = _QtWidgets.QProgressBar

# 显示组件
QLabel = _QtWidgets.QLabel
QLineEdit = _QtWidgets.QLineEdit
QTextEdit = _QtWidgets.QTextEdit
QPlainTextEdit = _QtWidgets.QPlainTextEdit
QGroupBox = _QtWidgets.QGroupBox
QStackedWidget = _QtWidgets.QStackedWidget

# 布局
QVBoxLayout = _QtWidgets.QVBoxLayout
QHBoxLayout = _QtWidgets.QHBoxLayout
QGridLayout = _QtWidgets.QGridLayout
QFormLayout = _QtWidgets.QFormLayout

# 列表和树
QListWidget = _QtWidgets.QListWidget
QTreeWidget = _QtWidgets.QTreeWidget
QTableWidget = _QtWidgets.QTableWidget
QListWidgetItem = _QtWidgets.QListWidgetItem
QTreeWidgetItem = _QtWidgets.QTreeWidgetItem
QTableWidgetItem = _QtWidgets.QTableWidgetItem

# 图形视图
QGraphicsView = _QtWidgets.QGraphicsView
QGraphicsScene = _QtWidgets.QGraphicsScene
QGraphicsItem = _QtWidgets.QGraphicsItem
QGraphicsRectItem = _QtWidgets.QGraphicsRectItem
QGraphicsEllipseItem = _QtWidgets.QGraphicsEllipseItem
QGraphicsLineItem = _QtWidgets.QGraphicsLineItem
QGraphicsTextItem = _QtWidgets.QGraphicsTextItem
QGraphicsProxyWidget = _QtWidgets.QGraphicsProxyWidget
QGraphicsPathItem = _QtWidgets.QGraphicsPathItem

# 对话框
QFileDialog = _QtWidgets.QFileDialog
QColorDialog = _QtWidgets.QColorDialog
QFontDialog = _QtWidgets.QFontDialog
QInputDialog = _QtWidgets.QInputDialog
QMessageBox = _QtWidgets.QMessageBox

# 其他部件
QAction = _QAction
QActionGroup = _QActionGroup
QShortcut = _QShortcut
QTimer = _QtCore.QTimer
QThread = _QtCore.QThread
QMetaObject = _QtCore.QMetaObject
QEvent = _QtCore.QEvent
QObject = _QtCore.QObject
QEventLoop = _QtCore.QEventLoop

# 图形
QPainter = _QtGui.QPainter
QPen = _QtGui.QPen
QBrush = _QtGui.QBrush
QColor = _QtGui.QColor
QFont = _QtGui.QFont
QIcon = _QtGui.QIcon
QPixmap = _QtGui.QPixmap
QImage = _QtGui.QImage
QBitmap = _QtGui.QBitmap
QCursor = _QtGui.QCursor
QPalette = _QtGui.QPalette
QFontMetrics = _QtGui.QFontMetrics
QPainterPath = _QtGui.QPainterPath
QRegion = _QtGui.QRegion
QTransform = _QtGui.QTransform
QMatrix = None  # PySide6中已移除，使用QTransform替代

# 核心类型
QPoint = _QtCore.QPoint
QPointF = _QtCore.QPointF
QRect = _QtCore.QRect
QRectF = _QtCore.QRectF
QSize = _QtCore.QSize
QSizeF = _QtCore.QSizeF
QLine = _QtCore.QLine
QLineF = _QtCore.QLineF
QVariant = None  # PySide6中已移除，使用Python类型替代

# 日期时间
QDate = _QtCore.QDate
QTime = _QtCore.QTime
QDateTime = _QtCore.QDateTime

# 信号槽
if QT_VERSION == 'PySide6':
    Signal = _QtCore.Signal
    Slot = _QtCore.Slot
    Property = _QtCore.Property
else:
    Signal = _QtCore.pyqtSignal
    Slot = _QtCore.pyqtSlot
    Property = _QtCore.pyqtProperty

# 枚举统一
class AlignmentFlag(Enum):
    """对齐标志统一枚举"""
    AlignLeft = 0x1
    AlignRight = 0x2
    AlignHCenter = 0x4
    AlignJustify = 0x8
    AlignTop = 0x20
    AlignBottom = 0x40
    AlignVCenter = 0x80
    AlignCenter = AlignHCenter | AlignVCenter
    AlignAbsolute = 0x10
    
    @classmethod
    def from_qt(cls, value):
        """从Qt对齐值转换"""
        return cls(value)
    
    def to_qt(self):
        """转换为Qt对齐值"""
        return self.value


class Orientation(Enum):
    """方向枚举"""
    Horizontal = 0x1
    Vertical = 0x2
    
    @classmethod
    def from_qt(cls, value):
        return cls(value)
    
    def to_qt(self):
        return self.value


class SizePolicy(Enum):
    """尺寸策略枚举"""
    Fixed = 0x1
    Minimum = 0x2
    Maximum = 0x4
    Preferred = 0x5
    Expanding = 0x3
    MinimumExpanding = 0x6
    Ignored = 0x7
    
    @classmethod
    def from_qt(cls, value):
        return cls(value)
    
    def to_qt(self):
        return self.value


# PenStyle统一
class PenStyle(Enum):
    NoPen = 0x0
    SolidPen = 0x1
    DashPen = 0x2
    DotPen = 0x3
    DashDotPen = 0x4
    DashDotDotPen = 0x5
    CustomDashPen = 0x6
    
    @classmethod
    def from_qt(cls, value):
        return cls(value)
    
    def to_qt(self):
        return self.value


# BrushStyle统一
class BrushStyle(Enum):
    NoBrush = 0x0
    SolidPattern = 1
    Dense1Pattern = 2
    Dense2Pattern = 3
    Dense3Pattern = 4
    Dense4Pattern = 5
    Dense5Pattern = 6
    Dense6Pattern = 7
    Dense7Pattern = 8
    HorPattern = 9
    VerPattern = 10
    CrossPattern = 11
    BDiagPattern = 12
    FDiagPattern = 13
    DiagCrossPattern = 14
    
    @classmethod
    def from_qt(cls, value):
        return cls(value)
    
    def to_qt(self):
        return self.value


# 工具函数
def create_icon(icon_name: str):
    """创建图标，兼容不同Qt后端"""
    return QIcon(f'icons/{icon_name}.png')


def connect_signal(signal, callback: Callable):
    """安全连接信号槽"""
    try:
        signal.connect(callback)
        return True
    except Exception as e:
        print(f'[Qt Compat] Signal connection failed: {e}')
        return False


def set_widget_parent(widget, parent=None):
    """设置父组件，兼容不同Qt后端"""
    if parent is not None:
        widget.setParent(parent)
    return widget


def get_application_instance():
    """获取QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def qtimer_single_shot(interval: int, callback: Callable, *args, **kwargs):
    """单次定时器，兼容不同Qt后端"""
    if QT_VERSION == 'PySide6':
        QTimer.singleShot(interval, lambda: callback(*args, **kwargs))
    else:
        QTimer.singleShot(interval, callback)


def qthread_sleep(seconds: float):
    """线程休眠"""
    import time
    end_time = time.time() + seconds
    while time.time() < end_time:
        QApplication.processEvents()


# 导出常用类型
__all__ = [
    # 版本信息
    'QT_VERSION',
    'QT_VERSION_STR',
    
    # 应用程序
    'QApplication',
    'get_application_instance',
    
    # 窗口部件
    'QWidget',
    'QFrame',
    'QDialog',
    'QMainWindow',
    'QMenu',
    'QMenuBar',
    'QToolBar',
    'QDockWidget',
    'QSplitter',
    'QScrollArea',
    'QStackedWidget',
    'QTabWidget',
    'QMdiArea',
    
    # 按钮
    'QPushButton',
    'QToolButton',
    'QRadioButton',
    'QCheckBox',
    'QComboBox',
    'QSpinBox',
    'QDoubleSpinBox',
    'QSlider',
    'QProgressBar',
    
    # 显示
    'QLabel',
    'QLineEdit',
    'QTextEdit',
    'QPlainTextEdit',
    'QGroupBox',
    
    # 布局
    'QVBoxLayout',
    'QHBoxLayout',
    'QGridLayout',
    'QFormLayout',
    
    # 列表
    'QListWidget',
    'QTreeWidget', 
    'QTableWidget',
    'QListWidgetItem',
    'QTreeWidgetItem',
    'QTableWidgetItem',
    
    # 图形视图
    'QGraphicsView',
    'QGraphicsScene',
    'QGraphicsItem',
    'QGraphicsRectItem',
    'QGraphicsEllipseItem',
    'QGraphicsLineItem',
    'QGraphicsTextItem',
    'QGraphicsProxyWidget',
    
    # 对话框
    'QFileDialog',
    'QColorDialog',
    'QFontDialog',
    'QInputDialog',
    'QMessageBox',
    
    # 其他部件
    'QAction',
    'QActionGroup',
    'QShortcut',
    'QTimer',
    'QThread',
    'QMetaObject',
    'QEvent',
    'QObject',
    'QEventLoop',
    
    # 图形
    'QPainter',
    'QPen',
    'QBrush',
    'QColor',
    'QFont',
    'QIcon',
    'QPixmap',
    'QImage',
    'QBitmap',
    'QCursor',
    'QPalette',
    'QFontMetrics',
    'QPainterPath',
    'QRegion',
    'QTransform',
    
    # 核心类型
    'QPoint',
    'QPointF',
    'QRect',
    'QRectF',
    'QSize',
    'QSizeF',
    'QLine',
    'QLineF',
    
    # 日期时间
    'QDate',
    'QTime',
    'QDateTime',
    
    # 信号槽
    'Signal',
    'Slot',
    'Property',
    'connect_signal',
    
    # 统一枚举
    'AlignmentFlag',
    'Orientation',
    'SizePolicy',
    'PenStyle',
    'BrushStyle',
    
    # 工具函数
    'create_icon',
    'set_widget_parent',
    'qtimer_single_shot',
    'qthread_sleep',
]


if __name__ == '__main__':
    print(f'Qt Compatibility Layer - Using {QT_VERSION}')
    print(f'Qt Version: {QT_VERSION_STR}')
    print('\nAvailable classes:')
    for name in sorted(__all__):
        print(f'  - {name}')