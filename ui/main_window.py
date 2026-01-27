#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口UI模块

实现VisionMaster风格的主界面，包括：
- 菜单栏和工具栏
- 项目浏览器
- 工具库
- 图像显示区域
- 算法编辑器
- 属性面板
- 结果面板

Author: Vision System Team
Date: 2025-01-04
"""

import sys
import os
import math
import logging
logging.basicConfig(level=logging.INFO)

# 设置protobuf兼容模式（解决paddlepaddle兼容性问题）
os.environ.setdefault('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', 'python')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List
from enum import Enum

PYQT_VERSION = 5

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
        QTabWidget, QToolBar, QAction, QStatusBar, QDockWidget,
        QTreeWidget, QTreeWidgetItem, QMenuBar, QListWidget, QListWidgetItem,
        QAbstractItemView, QGraphicsView, QGraphicsScene, QGraphicsItem,
        QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
        QPushButton, QFileDialog, QComboBox, QDialog, QFormLayout,
        QSpinBox, QDoubleSpinBox, QCheckBox, QDialogButtonBox, QLabel,
        QFrame, QScrollArea, QGroupBox, QGridLayout, QSplitterHandle,
        QMessageBox
    )
    from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QPainter, QPen, QBrush, QColor, QImage, QDrag, QCursor, QLineF, QFont, QPainterPath
    from PyQt6.QtCore import Qt, QSize, QPointF, QRectF, QMimeData, pyqtSignal, QObject, QTimer
    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
        QTabWidget, QToolBar, QAction, QStatusBar, QDockWidget,
        QTreeWidget, QTreeWidgetItem, QMenuBar, QListWidget, QListWidgetItem,
        QAbstractItemView, QGraphicsView, QGraphicsScene, QGraphicsItem,
        QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
        QGraphicsPixmapItem, QPushButton, QFileDialog, QComboBox, QDialog, QFormLayout,
        QSpinBox, QDoubleSpinBox, QCheckBox, QDialogButtonBox, QLabel,
        QFrame, QScrollArea, QGroupBox, QGridLayout, QSplitterHandle,
        QMessageBox
    )
    from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QPainter, QPen, QBrush, QColor, QImage, QDrag, QCursor, QFont, QPainterPath
    from PyQt5.QtCore import Qt, QSize, QPointF, QRectF, QMimeData, pyqtSignal, QObject, QLineF, QEvent, QTimer
    PYQT_VERSION = 5

import cv2
import numpy as np
from pathlib import Path

from core.solution import Solution
from core.procedure import Procedure
from core.tool_base import ToolRegistry, ToolBase
from data.image_data import ImageData
from modules.camera_manager import CameraManager, HikCamera, CameraInfo, CameraState
from core.solution_file_manager import SolutionFileManager, CodeGenerator, DocumentationGenerator
from ui.tool_library import ToolLibraryDockWidget
from ui.property_panel import PropertyDockWidget
from ui.result_panel import ResultDockWidget, ResultType
from ui.enhanced_result_dock import EnhancedResultDockWidget
from ui.project_browser import ProjectBrowserDockWidget
# from ui.communication_dialog import CommunicationConfigDialog, CommunicationMonitorWidget
# from ui.communication_monitor import CommunicationMonitorPanel, CommunicationStatusWidget
from ui.communication_config import get_communication_config_widget
from ui.cpu_optimization_dialog import CPUOptimizationDialog, PerformanceMonitorWidget
from ui.theme import get_style, apply_theme

# 导入所有工具模块，确保它们被注册到ToolRegistry
import tools





class ConnectionLine(QGraphicsLineItem):
    """连接线图形项，连接两个端口
    
    Attributes:
        start_port: 起始端口
        end_port: 结束端口
        line_color: 连线颜色
        line_width: 连线宽度
    """
    
    def __init__(self, start_port: 'PortItem', end_port: 'PortItem', parent=None):
        """初始化连接线
        
        Args:
            start_port: 起始端口
            end_port: 结束端口
            parent: 父图形项
        """
        # 计算初始连线位置
        start_pos = start_port.sceneBoundingRect().center()
        end_pos = end_port.sceneBoundingRect().center()
        
        super().__init__(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y(), parent)
        
        self.start_port = start_port
        self.end_port = end_port
        self._logger = logging.getLogger("ConnectionLine")
        
        # 设置连线样式
        self.line_color = QColor(50, 100, 200)
        self.line_width = 3
        self.setPen(QPen(self.line_color, self.line_width))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)
        
        # 设置Z值，使其在工具框上方
        self.setZValue(-1)
        
        # 连接端口的连接状态变化信号
        start_port.is_connected = True
        end_port.is_connected = True
        
        self._logger.info(f"[LINE] 创建连接线: {start_port.parent_item.tool.tool_name}:{start_port.port_type} -> {end_port.parent_item.tool.tool_name}:{end_port.port_type}")
    
    def update_position(self):
        """更新连线位置（当端口移动时调用）"""
        if self.start_port and self.end_port:
            start_pos = self.start_port.sceneBoundingRect().center()
            end_pos = self.end_port.sceneBoundingRect().center()
            self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
    
    def get_connected_tools(self) -> tuple:
        """获取连接的两个工具
        
        Returns:
            (start_tool, end_tool) 元组
        """
        return (self.start_port.parent_item, self.end_port.parent_item)
    
    def delete(self):
        """删除连线"""
        self._logger.info(f"[LINE] 删除连接线: {self.start_port.parent_item.tool.tool_name} -> {self.end_port.parent_item.tool.tool_name}")
        
        # 重置端口连接状态
        self.start_port.is_connected = False
        self.end_port.is_connected = False
        
        # 从场景中移除
        if self.scene():
            self.scene().removeItem(self)
    
    def paint(self, painter, option, widget=None):
        """重写绘制方法，绘制箭头"""
        # 绘制主线
        painter.setPen(QPen(self.line_color, self.line_width))
        painter.drawLine(self.line())
        
        # 绘制箭头（在终点绘制）
        line = self.line()
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = 10
        
        # 计算箭头位置（在终点处）
        end_point = line.p2()
        
        # 绘制简单的箭头
        painter.setPen(QPen(self.line_color, self.line_width))
        painter.setBrush(QBrush(self.line_color))
        
        # 箭头路径
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        
        # 箭头两侧的点
        p1 = end_point - QPointF(math.cos(angle - math.pi/6) * arrow_size, 
                                 math.sin(angle - math.pi/6) * arrow_size)
        p2 = end_point - QPointF(math.cos(angle + math.pi/6) * arrow_size, 
                                 math.sin(angle + math.pi/6) * arrow_size)
        
        arrow_path.lineTo(p1)
        arrow_path.lineTo(p2)
        arrow_path.lineTo(end_point)
        arrow_path.closeSubpath()
        
        painter.drawPath(arrow_path)


class PortItem(QGraphicsEllipseItem):
    """端口图形项，支持点击和拖拽连线"""
    
    def __init__(self, port_type: str, parent_item: 'GraphicsToolItem', parent=None):
        """初始化端口
        
        Args:
            port_type: 端口类型 ('input' 或 'output')
            parent_item: 父工具图形项
            parent: 父图形项
        """
        port_size = 14
        super().__init__(0, 0, port_size, port_size, parent)
        
        self.port_type = port_type
        self.parent_item = parent_item
        self._logger = logging.getLogger("PortItem")
        
        # 设置端口样式
        if port_type == 'input':
            self.setBrush(QBrush(QColor(255, 100, 100)))
            self.setPen(QPen(QColor(200, 50, 50), 2))
        else:
            self.setBrush(QBrush(QColor(100, 255, 100)))
            self.setPen(QPen(QColor(50, 200, 50), 2))
        
        # 设置可接受悬停和点击
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # 连接状态
        self.is_connected = False
        
        # 临时连线（用于拖拽时显示）
        self.temp_line = None
    
    def sceneBoundingRect(self) -> QRectF:
        """获取场景坐标系下的边界矩形"""
        return self.mapToScene(self.boundingRect()).boundingRect()
    
    def center(self) -> QPointF:
        """获取端口中心在场景坐标系下的位置"""
        return self.sceneBoundingRect().center()
    
    def hoverEnterEvent(self, event):
        """鼠标悬停事件"""
        if self.port_type == 'input':
            self.setPen(QPen(QColor(255, 150, 150), 3))
        else:
            self.setPen(QPen(QColor(150, 255, 150), 3))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """鼠标离开事件"""
        if self.port_type == 'input':
            self.setPen(QPen(QColor(200, 50, 50), 2))
        else:
            self.setPen(QPen(QColor(50, 200, 50), 2))
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始创建连线"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._logger.info(f"[PORT] 点击端口: {self.port_type}")
            
            # 获取场景
            scene = self.scene()
            if scene and hasattr(scene, 'start_connection'):
                # 通知场景开始连线
                scene.start_connection(self)
            
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 更新临时连线"""
        if self.temp_line:
            # 更新临时连线的终点
            scene_pos = self.mapToScene(event.pos())
            line = self.temp_line.line()
            line.setP2(scene_pos)
            self.temp_line.setLine(line)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 完成连线"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 获取场景
            scene = self.scene()
            if scene and hasattr(scene, 'finish_connection'):
                # 检测鼠标释放位置下是否有其他端口
                scene_pos = event.scenePos()
                items_at_pos = scene.items(scene_pos)
                
                # 查找鼠标位置下的端口
                target_port = None
                for item in items_at_pos:
                    if isinstance(item, PortItem) and item != self:
                        target_port = item
                        break
                
                # 如果找到了目标端口，则完成连线
                if target_port:
                    scene.finish_connection(target_port, scene_pos)
                else:
                    # 否则取消连线
                    scene.finish_connection(self, scene_pos)
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)


from core.zoomable_image import ZoomableGraphicsView


class ImageView(ZoomableGraphicsView):
    """图像显示视图，支持缩放和平移"""
    
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self._logger = logging.getLogger("ImageView")
        self._logger.info("[VIEW] ImageView 初始化完成")


class AlgorithmView(QGraphicsView):
    """算法编辑器视图，支持拖拽功能"""
    
    def __init__(self, scene: 'AlgorithmScene', parent=None):
        super().__init__(scene, parent)
        self._logger = logging.getLogger("AlgorithmView")
        self.setScene(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        if self.horizontalScrollBar():
            self.horizontalScrollBar().setRange(0, 10000)
            self.horizontalScrollBar().setValue(0)
        if self.verticalScrollBar():
            self.verticalScrollBar().setRange(0, 10000)
            self.verticalScrollBar().setValue(0)
        
        self.centerOn(0, 0)
        
        self._logger.info("[VIEW] AlgorithmView 初始化完成，接受拖拽: True")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        mime_data = event.mimeData()
        self._logger.info(f"[VIEW] dragEnterEvent - mimeData formats: {mime_data.formats()}")
        
        if mime_data.hasFormat("application/vision-tool"):
            event.accept()
            self._logger.info("[VIEW] ✓ 接受拖拽进入 - application/vision-tool")
        elif mime_data.hasText():
            self._logger.info(f"[VIEW] ✗ 拒绝拖拽 - 文本格式: {mime_data.text()}")
            event.ignore()
        else:
            self._logger.info(f"[VIEW] ✗ 拒绝拖拽 - 未知格式")
            for format in mime_data.formats():
                self._logger.info(f"  可用格式: {format}")
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        mime_data = event.mimeData()
        
        if mime_data.hasFormat("application/vision-tool"):
            event.accept()
            # 只在第一次时记录，避免日志过多
            if not hasattr(self, '_drag_move_logged'):
                self._logger.info("[VIEW] 拖拽移动中...")
                self._drag_move_logged = True
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self._logger.info("[VIEW] 拖拽离开算法编辑器")
        self._drag_move_logged = False  # 重置标志
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        """拖拽释放事件"""
        mime_data = event.mimeData()
        self._logger.info(f"[VIEW] dropEvent - mimeData formats: {mime_data.formats()}")
        
        if mime_data.hasFormat("application/vision-tool"):
            try:
                # 获取工具数据
                tool_data = mime_data.data("application/vision-tool").data().decode('utf-8')
                parts = tool_data.split('|')
                
                self._logger.info(f"[VIEW] 解析工具数据: {tool_data}")
                self._logger.info(f"[VIEW] 分割结果: {parts}")
                
                if len(parts) >= 3:
                    category, name, display_name = parts[0], parts[1], parts[2]
                    self._logger.info(f"[VIEW] ✓ 拖拽释放工具成功:")
                    self._logger.info(f"  - category: {category}")
                    self._logger.info(f"  - name: {name}")
                    self._logger.info(f"  - display_name: {display_name}")
                    
                    # 获取视口信息用于调试
                    viewport_rect = self.viewport().rect()
                    self._logger.info(f"[VIEW] 视口大小: {viewport_rect.width()}x{viewport_rect.height()}")
                    self._logger.info(f"[VIEW] 视口位置: ({viewport_rect.x()}, {viewport_rect.y()})")
                    self._logger.info(f"[VIEW] 事件位置: ({event.pos().x()}, {event.pos().y()})")
                    self._logger.info(f"[VIEW] 场景矩形: {self.scene().sceneRect()}")
                    
                    # 调试视图变换和滚动位置
                    transform = self.transform()
                    self._logger.info(f"[VIEW] 视图变换: scale=({transform.m11():.2f}, {transform.m22():.2f}), "
                                     f"translate=({transform.dx():.1f}, {transform.dy():.1f})")
                    
                    # 获取滚动条位置
                    h_scroll = self.horizontalScrollBar().value() if self.horizontalScrollBar() else 0
                    v_scroll = self.verticalScrollBar().value() if self.verticalScrollBar() else 0
                    self._logger.info(f"[VIEW] 滚动条位置: horizontal={h_scroll}, vertical={v_scroll}")
                    
                    # 调用场景的回调函数
                    if self.scene().tool_dropped_callback:
                        # 将视口坐标转换为场景坐标
                        view_pos = event.pos()
                        scene_pos = self.mapToScene(view_pos)
                        self._logger.info(f"[VIEW] 视口坐标: ({view_pos.x():.1f}, {view_pos.y():.1f}) -> 场景坐标: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
                        self.scene().tool_dropped_callback(display_name, scene_pos)
                    else:
                        self._logger.warning("[VIEW] ✗ 未设置 tool_dropped_callback")
                    
                    event.accept()
                else:
                    self._logger.warning(f"[VIEW] ✗ 工具数据格式错误，parts数量: {len(parts)}")
                    event.ignore()
            except Exception as e:
                self._logger.error(f"[VIEW] ✗ 处理拖拽数据异常: {e}")
                event.ignore()
        else:
            self._logger.warning("[VIEW] ✗ 拒绝释放 - 非 application/vision-tool 格式")
            event.ignore()
        
        # 重置标志
        self._drag_move_logged = False


class AlgorithmScene(QGraphicsScene):
    """算法编辑器场景，支持端口连线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("AlgorithmScene")
        
        # 设置场景矩形（从(0,0)开始，避免滚动条默认位置为负）
        self.setSceneRect(0, 0, 2000, 2000)
        
        # 连线状态
        self.connecting_port = None
        self.temp_line = None
        self.connection_callback = None
        self.tool_clicked_callback = None
        self.tool_dropped_callback = None
    
    def set_connection_callback(self, callback):
        """设置连线回调函数
        
        Args:
            callback: 回调函数，接收参数 (from_port, to_port)
        """
        self.connection_callback = callback
    
    def set_tool_clicked_callback(self, callback):
        """设置工具点击回调函数
        
        Args:
            callback: 回调函数，接收参数 (tool_item: GraphicsToolItem)
        """
        self.tool_clicked_callback = callback
    
    def set_tool_dropped_callback(self, callback):
        """设置工具拖拽释放回调函数
        
        Args:
            callback: 回调函数，接收参数 (tool_name: str, position: QPointF)
        """
        self.tool_dropped_callback = callback
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/vision-tool"):
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/vision-tool"):
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽释放事件"""
        if event.mimeData().hasFormat("application/vision-tool"):
            event.accept()
            
            # 获取工具数据
            mime_data = event.mimeData()
            tool_data = mime_data.data("application/vision-tool").data().decode()
            parts = tool_data.split('|')
            
            if len(parts) >= 3:
                category, name, display_name = parts[0], parts[1], parts[2]
                self._logger.info(f"[SCENE] 拖拽释放工具: {display_name} (category={category}, name={name})")
                
                # 调用回调函数
                if self.tool_dropped_callback:
                    scene_pos = event.scenePos()
                    self.tool_dropped_callback(display_name, scene_pos)
        else:
            event.ignore()
    
    def _dispatch_tool_clicked(self, tool_item: 'GraphicsToolItem'):
        """分发工具点击事件"""
        self._logger.info(f"[SCENE] 工具被点击: {tool_item.tool.tool_name}")
        
        if self.tool_clicked_callback:
            self.tool_clicked_callback(tool_item)
    
    def start_connection(self, port: PortItem):
        """开始创建连线
        
        Args:
            port: 起始端口
        """
        self._logger.info(f"[SCENE] 开始连线，起始端口: {port.port_type}")
        
        # 如果已经有正在进行的连线，先取消
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
        
        self.connecting_port = port
        
        # 创建临时连线
        port_center = port.mapToScene(port.boundingRect().center())
        self.temp_line = QGraphicsLineItem(QLineF(port_center, port_center))
        self.temp_line.setPen(QPen(QColor(100, 150, 250), 2, Qt.PenStyle.DashLine))
        self.addItem(self.temp_line)
        
        # 设置端口引用，用于更新临时连线
        port.temp_line = self.temp_line
    
    def finish_connection(self, port: PortItem, scene_pos: QPointF):
        """完成连线
        
        Args:
            port: 结束端口（如果为None，表示取消连线）
            scene_pos: 鼠标释放位置
        """
        # 移除临时连线
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
        
        if self.connecting_port and self.connecting_port.temp_line:
            self.connecting_port.temp_line = None
        
        # 如果没有有效的目标端口，取消连线
        if not port or port == self.connecting_port:
            self._logger.info("[SCENE] 取消连线")
            self.connecting_port = None
            return
        
        self._logger.info(f"[SCENE] 完成连线，起始端口: {self.connecting_port.port_type}, 结束端口: {port.port_type}")
        
        # 检查是否可以创建连线
        if self.connecting_port:
            # 检查端口类型是否匹配（输出端口连接到输入端口）
            if self.connecting_port.port_type == 'output' and port.port_type == 'input':
                # 检查是否属于不同的工具
                if self.connecting_port.parent_item != port.parent_item:
                    self._logger.info(f"[SCENE] 创建连线: {self.connecting_port.parent_item.tool.tool_name} -> {port.parent_item.tool.tool_name}")
                    
                    # 调用回调函数创建连线
                    if self.connection_callback:
                        self.connection_callback(self.connecting_port, port)
                else:
                    self._logger.warning("[SCENE] 不能连接同一个工具的端口")
            else:
                self._logger.warning(f"[SCENE] 端口类型不匹配: {self.connecting_port.port_type} -> {port.port_type}")
        
        # 重置连线状态
        self.connecting_port = None
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 取消连线"""
        # 如果点击空白区域，取消正在进行的连线
        if event.button() == Qt.MouseButton.LeftButton and self.temp_line:
            self._logger.info("[SCENE] 点击空白区域，取消连线")
            self.removeItem(self.temp_line)
            self.temp_line = None
            if self.connecting_port and self.connecting_port.temp_line:
                self.connecting_port.temp_line = None
            self.connecting_port = None
        
        super().mousePressEvent(event)


class ConnectionItem(QGraphicsLineItem):
    """连接线条图形项"""
    
    def __init__(self, from_item: 'GraphicsToolItem', to_item: 'GraphicsToolItem', parent=None):
        """初始化连接线条
        
        Args:
            from_item: 源工具图形项
            to_item: 目标工具图形项
            parent: 父图形项
        """
        super().__init__(parent)
        self.from_item = from_item
        self.to_item = to_item
        
        # 初始化日志记录器
        self._logger = logging.getLogger("ConnectionItem")
        
        # 设置线条样式
        self.setPen(QPen(QColor(50, 150, 250), 3))
        self.setZValue(0)  # 线条在工具下方，但在场景背景上方
        
        # 更新线条位置
        self.update_position()
        
        self._logger.info(f"[CONNECTION] 创建连接线: {from_item.tool.tool_name} -> {to_item.tool.tool_name}")
    
    def update_position(self):
        """更新线条位置"""
        # 获取源工具输出端口的世界坐标
        from_pos = self.from_item.get_output_port_world_pos()
        # 获取目标工具输入端口的世界坐标
        to_pos = self.to_item.get_input_port_world_pos()
        
        if from_pos and to_pos:
            line = QLineF(from_pos, to_pos)
            self.setLine(line)
            
            # 调试输出 - 使用 INFO 级别确保可见
            self._logger.info(f"[CONNECTION] 更新连接线: {self.from_item.tool.tool_name} -> {self.to_item.tool.tool_name}")
            self._logger.info(f"[CONNECTION] 起点: ({from_pos.x():.1f}, {from_pos.y():.1f})")
            self._logger.info(f"[CONNECTION] 终点: ({to_pos.x():.1f}, {to_pos.y():.1f})")
            self._logger.info(f"[CONNECTION] 线条长度: {line.length():.1f}")
        else:
            self._logger.error(f"[CONNECTION] 无法更新连接线 - from_pos={from_pos}, to_pos={to_pos}")


class GraphicsToolItem(QGraphicsRectItem):
    """算法编辑器中的工具图形项"""
    
    def __init__(self, tool: ToolBase, position: QPointF, parent: QGraphicsItem = None):
        # 工具框的尺寸
        width = 160
        height = 70
        
        # 调整位置，使工具框的中心对齐鼠标释放位置
        x = position.x() - width / 2
        y = position.y() - height / 2
        
        super().__init__(x, y, width, height, parent)
        
        self.tool = tool
        self.tool_data = None
        self._logger = logging.getLogger("GraphicsToolItem")
        
        self._logger.info(f"[TOOL] 创建工具框 '{tool.tool_name}'")
        self._logger.info(f"[TOOL] 原始位置: ({position.x():.1f}, {position.y():.1f})")
        self._logger.info(f"[TOOL] 最终位置: ({x:.1f}, {y:.1f})")
        self._logger.info(f"[TOOL] 工具框尺寸: {width}x{height}")
        
        # 工具颜色 - 更加专业的配色方案
        self.colors = {
            "ImageSource": QColor(66, 133, 244),  # Google Blue
            "ImageFilter": QColor(52, 168, 83),   # Google Green
            "Vision": QColor(234, 67, 53),        # Google Red
            "Measurement": QColor(251, 188, 5),   # Google Yellow
            "Recognition": QColor(103, 58, 183),  # Google Purple
            "Communication": QColor(0, 188, 212), # Google Teal
            "Default": QColor(158, 158, 158)      # Google Grey
        }
        
        color = self.colors.get(tool.tool_category, self.colors["Default"])
        self.setBrush(QBrush(color.lighter(120)))
        self.setPen(QPen(QColor(50, 50, 50), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # 工具名称
        # 使用工具类的tool_name而不是实例名称
        self.text_item = QGraphicsTextItem(tool.tool_name, self)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.text_item.setZValue(100)
        
        # 端口
        self._create_ports()
        
        # 初始化文本和端口位置
        self._update_text_position()
        self._update_port_positions()
    
    def itemChange(self, change, value):
        """监听位置变化，更新连线"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # 位置将要变化
            self._logger.debug(f"[TOOL] 工具 '{self.tool.tool_name}' 位置将要变化: ({value.x():.1f}, {value.y():.1f})")
            
            # 更新所有相关的连线
            self._update_related_connections()
        
        return super().itemChange(change, value)
    
    def _update_related_connections(self):
        """更新所有相关的连线"""
        scene = self.scene()
        if not scene:
            return
        
        # 遍历场景中所有的连线
        for item in scene.items():
            if isinstance(item, ConnectionLine):
                # 检查是否与当前工具有关
                connected_tools = item.get_connected_tools()
                if self in connected_tools:
                    item.update_position()
                    self._logger.debug(f"[TOOL] 更新连线: {item.start_port.parent_item.tool.tool_name} -> {item.end_port.parent_item.tool.tool_name}")
    
    def delete_related_connections(self):
        """删除所有与当前工具相关的连线"""
        scene = self.scene()
        if not scene:
            return
        
        connections_to_delete = []
        
        # 查找所有相关的连线
        for item in scene.items():
            if isinstance(item, ConnectionLine):
                connected_tools = item.get_connected_tools()
                if self in connected_tools:
                    connections_to_delete.append(item)
        
        # 删除所有相关的连线
        for connection in connections_to_delete:
            connection.delete()
        
        if connections_to_delete:
            self._logger.info(f"[TOOL] 删除工具 '{self.tool.tool_name}' 的 {len(connections_to_delete)} 条连线")
    
    def mouseDoubleClickEvent(self, event):
        """双击编辑工具属性"""
        # 简单实现：打印工具信息
        print(f"双击工具: {self.tool.tool_name}")
        params = self.tool.get_param_with_details()
        print("工具参数:")
        for name, info in params.items():
            print(f"  {name}: {info['value']} ({info['description']})")
    
    def _create_ports(self):
        """创建输入输出端口"""
        # 输入端口（顶部中间）
        self.input_port = PortItem('input', self, self)
        # 输出端口（底部中间）
        self.output_port = PortItem('output', self, self)
        
        # 初始化端口位置
        self._update_port_positions()
    
    def _update_text_position(self):
        """更新文本位置"""
        # 文本居中显示
        text_rect = self.text_item.boundingRect()
        center = self.boundingRect().center()
        self.text_item.setPos(
            center.x() - text_rect.width() / 2,
            center.y() - text_rect.height() / 2
        )
    
    def _update_port_positions(self):
        """更新端口位置（端口完全在工具框内部，紧贴顶部和底部边缘）"""
        rect = self.boundingRect()
        
        # 端口尺寸
        port_size = 14
        
        # 输入端口：在工具框内部，紧贴顶部边缘
        # 端口顶部距离工具框顶部边缘有2像素间隙
        # 端口顶部 = rect.top() + 2
        # 端口中心 = rect.top() + 2 + port_size/2
        input_center_y = rect.top() + 2 + port_size / 2
        input_center = QPointF(rect.center().x(), input_center_y)
        self.input_port.setPos(
            input_center.x() - port_size / 2,
            input_center.y() - port_size / 2
        )
        
        # 输出端口：在工具框内部，紧贴底部边缘
        # 端口底部距离工具框底部边缘有2像素间隙
        # 端口底部 = rect.bottom() - 2
        # 端口中心 = rect.bottom() - 2 - port_size/2
        output_center_y = rect.bottom() - 2 - port_size / 2
        output_center = QPointF(rect.center().x(), output_center_y)
        self.output_port.setPos(
            output_center.x() - port_size / 2,
            output_center.y() - port_size / 2
        )
        
        self._logger.info(f"[TOOL] 端口位置已更新:")
        self._logger.info(f"  工具框顶部y: {rect.top():.1f}, 底部y: {rect.bottom():.1f}")
        self._logger.info(f"  端口尺寸: {port_size}x{port_size}")
        self._logger.info(f"  输入端口中心计算: {rect.top():.1f} + 2 + {port_size}/2 = {rect.top() + 2 + port_size / 2:.1f}")
        self._logger.info(f"  输入端口中心: ({input_center.x():.1f}, {input_center.y():.1f})")
        self._logger.info(f"  输出端口中心计算: {rect.bottom():.1f} - 2 - {port_size}/2 = {rect.bottom() - 2 - port_size / 2:.1f}")
        self._logger.info(f"  输出端口中心: ({output_center.x():.1f}, {output_center.y():.1f})")
        self._logger.info(f"  端口完全在工具框内部，顶部间隙=2px, 底部间隙=2px")
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 显示工具属性到属性面板"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._logger.info(f"[TOOL] 点击工具框: {self.tool.tool_name}")
            
            # 清除场景中其他项目的选择
            scene = self.scene()
            if scene:
                scene.clearSelection()
            
            # 选当前工具项
            self.setSelected(True)
            
            # 在属性面板中显示工具属性
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'property_dock'):
                main_window.property_dock.show_tool_properties(self.tool)
                self._logger.info(f"[TOOL] 已在属性面板中显示: {self.tool.tool_name}")
            
            # 通知场景工具被点击（用于显示图像）
            if scene and hasattr(scene, '_dispatch_tool_clicked'):
                scene._dispatch_tool_clicked(self)
            
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def _get_main_window(self):
        """获取主窗口实例"""
        # 方法1：通过场景的父窗口查找
        scene = self.scene()
        if scene:
            # 场景的views应该能提供主窗口
            views = scene.views()
            if views:
                viewport = views[0]
                # 查找包含这个view的窗口
                window = viewport.window()
                if window and hasattr(window, 'property_dock'):
                    return window
        
        # 方法2：备用方法（保留原有逻辑）
        parent = self.parentItem()
        while parent:
            if hasattr(parent, 'windowTitle') and 'Vision' in parent.windowTitle():
                return parent
            parent = parent.parentItem()
        
        return None
    
    def mouseDoubleClickEvent(self, event):
        """双击编辑工具属性"""
        # 双击也显示属性
        self.mousePressEvent(event)
        super().mouseDoubleClickEvent(event)
    
    def get_input_port_world_pos(self) -> Optional[QPointF]:
        """获取输入端口的世界坐标"""
        if hasattr(self, 'input_port') and self.input_port:
            return self.input_port.mapToScene(self.input_port.boundingRect().center())
        return None
    
    def get_output_port_world_pos(self) -> Optional[QPointF]:
        """获取输出端口的世界坐标"""
        if hasattr(self, 'output_port') and self.output_port:
            return self.output_port.mapToScene(self.output_port.boundingRect().center())
        return None
    
    def get_corner_positions(self) -> Dict[str, QPointF]:
        """获取工具框四个角点的精确坐标
        
        Returns:
            包含四个角点坐标的字典:
            - 'top_left': 左上角
            - 'top_right': 右上角
            - 'bottom_left': 左下角
            - 'bottom_right': 右下角
        """
        rect = self.boundingRect()
        
        corners = {
            'top_left': QPointF(rect.left(), rect.top()),
            'top_right': QPointF(rect.right(), rect.top()),
            'bottom_left': QPointF(rect.left(), rect.bottom()),
            'bottom_right': QPointF(rect.right(), rect.bottom())
        }
        
        # 记录详细的位置信息
        self._logger.info(f"[TOOL] 工具框 '{self.tool.tool_name}' 角点坐标:")
        self._logger.info(f"  矩形区域: x={rect.x():.1f}, y={rect.y():.1f}, width={rect.width():.1f}, height={rect.height():.1f}")
        self._logger.info(f"  左上角: ({corners['top_left'].x():.1f}, {corners['top_left'].y():.1f})")
        self._logger.info(f"  右上角: ({corners['top_right'].x():.1f}, {corners['top_right'].y():.1f})")
        self._logger.info(f"  左下角: ({corners['bottom_left'].x():.1f}, {corners['bottom_left'].y():.1f})")
        self._logger.info(f"  右下角: ({corners['bottom_right'].x():.1f}, {corners['bottom_right'].y():.1f})")
        
        return corners
    
    def get_port_positions(self) -> Dict[str, QPointF]:
        """获取输入输出端口的精确位置点
        
        Returns:
            包含端口位置点的字典:
            - 'input': 输入端口位置（顶部边缘中心）
            - 'output': 输出端口位置（底部边缘中心）
        """
        rect = self.boundingRect()
        
        # 获取端口尺寸
        input_port_rect = self.input_port.boundingRect() if hasattr(self, 'input_port') and self.input_port else QRectF(0, 0, 14, 14)
        output_port_rect = self.output_port.boundingRect() if hasattr(self, 'output_port') and self.output_port else QRectF(0, 0, 14, 14)
        
        # 计算输入端口位置：紧贴工具框顶部边缘
        # 端口底部紧贴工具框顶部，端口中心x与工具框中心x对齐
        input_center = QPointF(rect.center().x(), rect.top())
        
        # 计算输出端口位置：紧贴工具框底部边缘
        # 端口顶部紧贴工具框底部，端口中心x与工具框中心x对齐
        output_center = QPointF(rect.center().x(), rect.bottom())
        
        # 记录详细的位置信息
        self._logger.info(f"[TOOL] 工具框 '{self.tool.tool_name}' 端口位置:")
        self._logger.info(f"  工具框: x={rect.x():.1f}, y={rect.y():.1f}, width={rect.width():.1f}, height={rect.height():.1f}")
        self._logger.info(f"  输入端口中心: ({input_center.x():.1f}, {input_center.y():.1f})")
        self._logger.info(f"  输出端口中心: ({output_center.x():.1f}, {output_center.y():.1f})")
        self._logger.info(f"  输入端口底部应紧贴工具框顶部y={rect.top():.1f}")
        self._logger.info(f"  输出端口顶部应紧贴工具框底部y={rect.bottom():.1f}")
        
        return {
            'input': input_center,
            'output': output_center
        }
    
    def get_all_positions(self) -> Dict[str, Any]:
        """获取工具框的所有位置信息
        
        Returns:
            包含所有位置信息的字典:
            - 'rect': 矩形区域
            - 'center': 中心点
            - 'corners': 四个角点
            - 'ports': 输入输出端口位置
        """
        rect = self.boundingRect()
        corners = self.get_corner_positions()
        ports = self.get_port_positions()
        
        return {
            'rect': rect,
            'center': rect.center(),
            'corners': corners,
            'ports': ports
        }


class MainWindow(QMainWindow):
    """主窗口类 - VisionMaster风格的视觉检测系统界面"""
    
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("MainWindow")
        
        # 初始化方案
        self.solution = Solution("新方案")
        
        # 初始化文件管理器
        self.file_manager = SolutionFileManager()
        self.code_generator = CodeGenerator()
        self.doc_generator = DocumentationGenerator()
        
        # 初始化流程
        self.current_procedure = Procedure("流程1")
        self.solution.add_procedure(self.current_procedure)
        
        # 初始化相机管理器
        self.camera_manager = CameraManager()
        self.camera = None
        self._camera_config = {}
        self._camera_param_widgets = {}
        
        # 图像相关
        self.current_image = None
        self.current_display_image = None
        self.current_display_tool_name = None
        
        # 图像缓存（避免重复处理）
        self._image_cache = {}  # {tool_name: (image_data_hash, qimage, qpixmap)}
        
        # 图像视图状态管理
        self._view_scale = 1.0  # 视图缩放比例
        self._view_offset = QPointF(0, 0)  # 视图偏移量
        self._show_metadata = False  # 是否显示图像元数据
        self._show_roi = False  # 是否显示ROI区域
        
        # 工具和连接
        self.tool_items = {}
        self.connection_items = {}
        
        # 运行状态
        self._is_running = False
        
        # 当前工具标签（用于状态栏显示）
        self.current_tool_label = "当前模块: 无"
        
        # 初始化UI
        self._init_ui()
        self._create_status_bar()
        
        self._logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面 - VisionMaster风格布局"""
        self.setWindowTitle("Vision System - 专业视觉检测系统")
        self.resize(1600, 900)
        
        # 应用现代化主题
        apply_theme(self, "light")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # 创建主分割器（水平分割）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 1. 左侧 - 项目浏览器
        self.project_dock = ProjectBrowserDockWidget(self)
        self.project_dock.set_solution(self.solution)
        self.project_dock.setMinimumWidth(220)
        self.project_dock.setMaximumWidth(300)
        main_splitter.addWidget(self.project_dock)
        
        # 2. 中间面板 - 画幅 + 算法编辑器（上下排列）
        middle_container = QWidget()
        middle_layout = QVBoxLayout(middle_container)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(4)
        
        # 中间垂直分割器
        middle_splitter = QSplitter(Qt.Orientation.Vertical)
        middle_layout.addWidget(middle_splitter)
        
        # 2.1 上半部分 - 画幅（图像显示）
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(2)
        
        # 画幅标题标签 - 更专业的设计
        self.image_label = QLabel("📷 画幅区域")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 10px;
                border-radius: 3px 3px 0 0;
                border: none;
            }
        """)
        image_layout.addWidget(self.image_label)
        
        # 画幅视图
        self.image_scene = QGraphicsScene()
        self.image_view = ImageView(self.image_scene)
        self.image_view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #34495e;
                background-color: #1a1a1a;
                border-radius: 0 0 3px 3px;
            }
            QGraphicsView:hover {
                border-color: #3498db;
            }
        """)
        image_layout.addWidget(self.image_view)
        
        image_container.setMinimumHeight(280)
        middle_splitter.addWidget(image_container)
        
        # 2.2 下半部分 - 算法编辑器
        algorithm_container = QWidget()
        algorithm_layout = QVBoxLayout(algorithm_container)
        algorithm_layout.setContentsMargins(0, 0, 0, 0)
        algorithm_layout.setSpacing(2)
        
        algorithm_label = QLabel("🔧 算法编辑器")
        algorithm_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 10px;
                border-radius: 3px 3px 0 0;
                border: none;
            }
        """)
        algorithm_layout.addWidget(algorithm_label)
        
        self.algorithm_scene = AlgorithmScene(self)
        self.algorithm_view = AlgorithmView(self.algorithm_scene)
        self.algorithm_view.setAcceptDrops(True)
        self.algorithm_view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #34495e;
                background-color: #ecf0f1;
                border-radius: 0 0 3px 3px;
            }
            QGraphicsView:hover {
                border-color: #e74c3c;
            }
        """)
        algorithm_layout.addWidget(self.algorithm_view)
        
        algorithm_container.setMinimumHeight(180)
        middle_splitter.addWidget(algorithm_container)
        
        # 设置中间分割器比例（画幅:算法编辑器 = 3:5）
        middle_splitter.setStretchFactor(0, 3)
        middle_splitter.setStretchFactor(1, 5)
        middle_splitter.setSizes([300, 500])
        
        middle_container.setMinimumWidth(400)
        main_splitter.addWidget(middle_container)
        
        # 3. 右侧面板组（垂直分割器：工具库、属性面板、结果）
        right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(4)
        
        # 创建右侧垂直分割器
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 3.1 工具库
        self.tool_library_dock = ToolLibraryDockWidget(self)
        self.tool_library_dock.setMinimumWidth(220)
        right_splitter.addWidget(self.tool_library_dock)
        
        # 3.2 属性面板
        self.property_dock = PropertyDockWidget(self)
        self.property_dock.setMinimumWidth(220)
        right_splitter.addWidget(self.property_dock)
        
        # 3.3 结果面板
        self.result_dock = EnhancedResultDockWidget(self)
        self.result_dock.setMinimumWidth(220)
        self.result_dock.setMinimumHeight(120)
        right_splitter.addWidget(self.result_dock)
        
        # 监听数据连接请求
        self.result_dock.data_connection_requested.connect(self._on_data_connection_requested)
        
        # 设置右侧分割器比例（工具库:属性:结果 = 2:2:1）
        right_splitter.setStretchFactor(0, 2)
        right_splitter.setStretchFactor(1, 2)
        right_splitter.setStretchFactor(2, 1)
        right_splitter.setSizes([250, 250, 125])
        
        right_panel_layout.addWidget(right_splitter)
        
        right_panel_container.setMinimumWidth(220)
        main_splitter.addWidget(right_panel_container)
        
        # 设置主分割器比例（项目浏览器:中间:右侧 = 1:4:2）
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)
        main_splitter.setStretchFactor(2, 2)
        main_splitter.setSizes([220, 800, 330])
        
        # 添加样式优化
        main_splitter.setStyleSheet("""
            QSplitter {
                background-color: #f5f5f5;
                border: none;
            }
            QSplitter::handle {
                background-color: #e0e0e0;
                border: none;
            }
            QSplitter::handle:hover {
                background-color: #bdc3c7;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """)
        middle_splitter.setStyleSheet(main_splitter.styleSheet())
        right_splitter.setStyleSheet(main_splitter.styleSheet())
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 连接信号
        self._connect_signals()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_solution)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_solution)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_solution)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_solution_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 导入菜单（新增）
        import_menu = file_menu.addMenu("导入")
        
        import_package_action = QAction("导入方案包", self)
        import_package_action.triggered.connect(self.import_solution_package)
        import_menu.addAction(import_package_action)
        
        file_menu.addSeparator()
        
        # 导出菜单
        export_menu = file_menu.addMenu("导出")
        
        export_package_action = QAction("导出方案包", self)
        export_package_action.triggered.connect(self.export_solution_package)
        export_menu.addAction(export_package_action)
        
        export_code_action = QAction("导出代码", self)
        export_code_action.triggered.connect(self.export_solution_code)
        export_menu.addAction(export_code_action)
        
        export_docs_action = QAction("导出文档", self)
        export_docs_action.triggered.connect(self.export_solution_docs)
        export_menu.addAction(export_docs_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 运行菜单
        run_menu = menubar.addMenu("运行")
        
        run_once_action = QAction("单次运行", self)
        run_once_action.setShortcut(QKeySequence("F5"))
        run_once_action.triggered.connect(self.run_once)
        run_menu.addAction(run_once_action)
        
        run_continuous_action = QAction("连续运行", self)
        run_continuous_action.setShortcut(QKeySequence("F6"))
        run_continuous_action.triggered.connect(self.run_continuous)
        run_menu.addAction(run_continuous_action)
        
        stop_run_action = QAction("停止运行", self)
        stop_run_action.setShortcut(QKeySequence("F7"))
        stop_run_action.triggered.connect(self.stop_run)
        run_menu.addAction(stop_run_action)
        
        # 通讯菜单
        comm_menu = menubar.addMenu("通讯")
        
        comm_config_action = QAction("通讯配置", self)
        comm_config_action.setShortcut(QKeySequence("F8"))
        comm_config_action.triggered.connect(self.show_communication_config)
        comm_menu.addAction(comm_config_action)
        
        comm_monitor_action = QAction("通讯监控", self)
        comm_monitor_action.triggered.connect(self.show_communication_monitor)
        comm_menu.addAction(comm_monitor_action)
        
    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        # 工具栏样式
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                spacing: 8px;
                padding: 4px 8px;
            }
            QToolBar::separator {
                background-color: #e0e0e0;
                width: 1px;
                height: 20px;
                margin: 0 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 10px;
                color: #2c3e50;
                font-size: 12px;
                font-weight: 500;
            }
            QToolButton:hover {
                background-color: #e3f2fd;
                border-color: #bbdefb;
            }
            QToolButton:pressed {
                background-color: #bbdefb;
            }
            QToolButton:checked {
                background-color: #bbdefb;
                border-color: #2196f3;
            }
        """)
        
        # 新建
        new_action = QAction("📋 新建", self)
        new_action.setToolTip("新建方案")
        new_action.triggered.connect(self.new_solution)
        toolbar.addAction(new_action)
        
        # 打开
        open_action = QAction("📂 打开", self)
        open_action.setToolTip("打开方案")
        open_action.triggered.connect(self.open_solution)
        toolbar.addAction(open_action)
        
        # 保存
        save_action = QAction("💾 保存", self)
        save_action.setToolTip("保存方案")
        save_action.triggered.connect(self.save_solution)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 单次运行
        run_once_action = QAction("▶️ 单次运行", self)
        run_once_action.setToolTip("单次运行 (F5)")
        run_once_action.triggered.connect(self.run_once)
        toolbar.addAction(run_once_action)
        
        # 连续运行
        run_continuous_action = QAction("🔄 连续运行", self)
        run_continuous_action.setToolTip("连续运行 (F6)")
        run_continuous_action.triggered.connect(self.run_continuous)
        toolbar.addAction(run_continuous_action)
        
        # 停止运行
        stop_run_action = QAction("⏹️ 停止运行", self)
        stop_run_action.setToolTip("停止运行 (F7)")
        stop_run_action.triggered.connect(self.stop_run)
        toolbar.addAction(stop_run_action)
        
        toolbar.addSeparator()
        
        # 放大
        zoom_in_action = QAction("🔍+ 放大", self)
        zoom_in_action.setToolTip("放大图像 (滚轮向上)")
        zoom_in_action.triggered.connect(self.image_view.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        # 缩小
        zoom_out_action = QAction("🔍- 缩小", self)
        zoom_out_action.setToolTip("缩小图像 (滚轮向下)")
        zoom_out_action.triggered.connect(self.image_view.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        # 重置缩放
        reset_zoom_action = QAction("🔄 重置", self)
        reset_zoom_action.setToolTip("重置缩放")
        reset_zoom_action.triggered.connect(self.image_view.reset_zoom)
        toolbar.addAction(reset_zoom_action)
        
        # 缩放比例显示
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #e8f4f8;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                border: 1px solid #bbdefb;
                min-width: 60px;
                text-align: center;
            }
        """)
        toolbar.addWidget(self.zoom_label)
        
        toolbar.addSeparator()
        
        # 通讯配置
        comm_config_action = QAction("📡 通讯配置", self)
        comm_config_action.setToolTip("打开通讯配置对话框 (F8)")
        comm_config_action.triggered.connect(self.show_communication_config)
        toolbar.addAction(comm_config_action)
        
        # CPU优化配置
        cpu_optimize_action = QAction("⚡ CPU优化", self)
        cpu_optimize_action.setToolTip("配置CPU优化参数")
        cpu_optimize_action.triggered.connect(self._show_cpu_optimization_dialog)
        toolbar.addAction(cpu_optimize_action)
        
        # 性能监控
        perf_monitor_action = QAction("📊 性能监控", self)
        perf_monitor_action.setToolTip("打开性能监控面板")
        perf_monitor_action.triggered.connect(self._show_performance_monitor)
        toolbar.addAction(perf_monitor_action)
        
        # 连接缩放变化信号
        self.image_view.zoom_changed.connect(self._on_zoom_changed)
    
    def _create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 状态栏样式
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #e0e0e0;
                color: #2c3e50;
                font-size: 12px;
                padding: 4px 8px;
            }
            QStatusBar QLabel {
                margin-right: 15px;
            }
        """)
        
        # 状态标签
        self.status_label = QLabel("🟢 就绪 - 请从左侧工具库拖拽工具到算法编辑器")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding-right: 15px;
            }
        """)
        status_bar.addWidget(self.status_label)
        
        # 分割线
        separator = QLabel("|")
        separator.setStyleSheet("""
            QLabel {
                color: #bdbdbd;
                margin: 0 5px;
            }
        """)
        status_bar.addWidget(separator)
        
        # 当前模块标签
        self.current_tool_status = QLabel("🔧 当前模块: 无")
        self.current_tool_status.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-weight: bold;
                padding-left: 5px;
                min-width: 180px;
            }
        """)
        status_bar.addWidget(self.current_tool_status)
        
        # 分割线
        separator2 = QLabel("|")
        separator2.setStyleSheet("""
            QLabel {
                color: #bdbdbd;
                margin: 0 5px;
            }
        """)
        status_bar.addWidget(separator2)
        
        # 流程状态标签
        self.procedure_status = QLabel("📋 流程: 新方案 - 流程1")
        self.procedure_status.setStyleSheet("""
            QLabel {
                color: #4caf50;
                min-width: 200px;
            }
        """)
        status_bar.addWidget(self.procedure_status)
        
        # 分割线
        separator3 = QLabel("|")
        separator3.setStyleSheet("""
            QLabel {
                color: #bdbdbd;
                margin: 0 5px;
            }
        """)
        status_bar.addWidget(separator3)
        
        # 运行状态标签
        self.run_status = QLabel("⏹️ 停止")
        self.run_status.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-weight: bold;
                min-width: 100px;
            }
        """)
        status_bar.addWidget(self.run_status)
    
    def _on_zoom_changed(self, zoom: float):
        """缩放变化回调"""
        self.zoom_label.setText(f"{int(zoom * 100)}%")
    
    def _connect_signals(self):
        """连接信号"""
        # 工具库工具拖拽信号
        self.tool_library_dock.get_tool_library().tool_drag_started.connect(self._on_tool_drag_started)
        
        # 工具库工具点击信号
        self.tool_library_dock.get_tool_library().tool_clicked.connect(self._on_tool_library_clicked)
        
        # 项目浏览器信号
        self.project_dock.item_double_clicked.connect(self._on_project_item_double_clicked)
        self.project_dock.item_selected.connect(self._on_project_item_selected)
        self.project_dock.item_deleted.connect(self._on_project_item_deleted)
        self.project_dock.procedure_created.connect(self._on_procedure_created)
        
        # 算法场景信号
        self.algorithm_scene.set_connection_callback(self._on_port_connection)
        self.algorithm_scene.set_tool_clicked_callback(self._on_tool_clicked)
        self.algorithm_scene.set_tool_dropped_callback(self._on_tool_dropped)
        
        # 属性面板ROI选择信号
        self.property_dock.widget().roi_select_requested.connect(self._on_roi_select_requested)
        
        # 属性变更信号连接
        self.property_dock.widget().property_changed.connect(self._on_tool_property_changed)
    
    def _on_selection_changed(self):
        try:
            # 检查scene是否还存在
            if self.algorithm_scene is None:
                return
            
            selected_items = self.algorithm_scene.selectedItems()
            
            if selected_items:
                # 只处理第一个选中的工具项
                selected_item = selected_items[0]
                if isinstance(selected_item, GraphicsToolItem):
                    # 显示工具属性
                    self._logger.info(f"选择了工具: {selected_item.tool.name} ({selected_item.tool.tool_name})")
                    self.property_dock.show_tool_properties(selected_item.tool)
                    return
            
            # 没有选择工具或选择的不是工具项，清空属性面板
            self.property_dock.clear_properties()
            
        except (RuntimeError, AttributeError) as e:
            # 处理场景已删除的情况
            self._logger.debug(f"选择变化事件异常（可能是场景已删除）: {e}")
    
    def _on_tool_drag_started(self, category: str, name: str, display_name: str):
        """工具拖拽开始事件"""
        self._logger.info(f"收到工具拖拽信号: category={category}, name={name}, display_name={display_name}")
        
        # 使用显示名称作为工具名称
        tool_display_name = display_name
        
        self._logger.info(f"处理工具: {tool_display_name}")
    
    def _on_tool_library_clicked(self, category: str, name: str, display_name: str):
        """工具库工具点击事件 - 显示工具参数"""
        self._logger.info(f"工具库点击工具: {display_name} ({category}.{name})")
        
        # 获取工具类
        from core.tool_base import ToolRegistry
        tool_class = ToolRegistry.get_tool_class(category, name)
        
        if tool_class:
            # 创建临时工具实例（用于显示参数）
            temp_tool = tool_class(name)
            self._logger.info(f"创建临时工具实例: {name}")
            
            # 在属性面板中显示参数
            self.property_dock.show_tool_properties(temp_tool)
            self._logger.info(f"已在属性面板中显示: {display_name}")
        else:
            self._logger.warning(f"未找到工具类: {category}.{name}")
        
        # 注意：实际的工具创建会在算法编辑器的drop事件中处理
        # 这里只是记录拖拽开始事件
    
    def _on_tool_property_changed(self, tool_name: str, param_name: str, new_value: Any):
        """工具属性变更事件"""
        self._logger.info(f"属性变更: tool_name={tool_name}, param_name={param_name}, value={new_value}")
        
        # 查找流程中的工具并更新参数
        if self.current_procedure and hasattr(self.current_procedure, '_tools'):
            for tool in self.current_procedure._tools.values():
                # 匹配工具名称
                if tool_name in tool._name or tool._name in tool_name:
                    tool.set_param(param_name, new_value)
                    self._logger.info(f"已更新工具参数: {tool._name}.{param_name} = {new_value}")
                    
                    # 调用initialize方法应用参数变更
                    if hasattr(tool, 'initialize') and callable(tool.initialize):
                        try:
                            params = tool.get_all_params()
                            tool.initialize(params)
                            self._logger.debug(f"工具已重新初始化: {tool.name}")
                        except Exception as e:
                            self._logger.warning(f"工具重新初始化失败: {e}")
                    break
    
    def _on_roi_select_requested(self, tool_name: str, param_name: str, current_image):
        """ROI选择请求事件"""
        self._logger.info(f"收到ROI选择请求: tool_name={tool_name}, param_name={param_name}")
        
        # 获取当前工具 - 使用当前流程
        tool = None
        
        # 使用 self.current_procedure 访问当前流程
        procedure = self.current_procedure
        if not procedure:
            self._logger.warning("当前没有活动的流程")
            return
        
        self._logger.info(f"检查当前流程: {procedure.name if hasattr(procedure, 'name') else 'unknown'}")
        
        # 调试：打印所有工具名称
        if hasattr(procedure, '_tools'):
            self._logger.info(f"流程中的工具: {list(procedure._tools.keys())}")
            for t in procedure._tools.values():
                self._logger.info(f"  - _name={t._name}, name={t.name}, tool_name={t.tool_name}")
                
                # 匹配逻辑：优先使用 _name (完整名称)，然后是 tool_name (显示名称)
                if tool_name in t._name or t._name in tool_name:
                    tool = t
                    self._logger.info(f"通过 _name 找到工具: {t._name}")
                    break
                elif t.tool_name == tool_name:
                    tool = t
                    self._logger.info(f"通过 tool_name 找到工具: {t.tool_name}")
                    break
        else:
            self._logger.warning(f"当前流程没有 _tools 属性")
        
        if tool is None:
            self._logger.warning(f"未找到工具: {tool_name}")
            return
        
        self._logger.info(f"成功找到工具: {tool._name}, 显示名称: {tool.tool_name}")
        
        # 获取输入图像
        input_image = None
        
        # 方法1: 直接从工具的输入数据获取
        if tool.has_input() and tool._input_data:
            input_image = tool._input_data.data
            self._logger.info("从工具输入数据获取图像")
        
        # 方法2: 如果没有输入数据，尝试从上游工具获取
        if input_image is None:
            self._logger.info("尝试从上游工具获取图像...")
            # 遍历流程中的工具，找到连接到当前工具的上游工具
            for proc_tool in procedure._tools.values():
                if proc_tool == tool:
                    continue
                # 检查是否有连接到当前工具的输出
                if hasattr(proc_tool, '_output_data') and proc_tool._output_data is not None:
                    output_data = proc_tool._output_data.data
                    output_image = getattr(output_data, 'image', None)
                    if output_data is not None and isinstance(output_image, np.ndarray):
                        input_image = output_image
                        self._logger.info(f"从上游工具 '{proc_tool.tool_name}' 获取图像")
                        break
        
        # 方法3: 如果还是没有图像，先运行流程获取
        if input_image is None:
            self._logger.info("没有输入图像，将先运行流程获取图像...")
            # 运行流程
            self._run_procedure_sync()
            
            # 再次尝试获取输入图像
            if tool.has_input() and tool._input_data and tool._input_data.data is not None:
                input_image = tool._input_data.data
                self._logger.info("运行流程后从工具输入数据获取图像")
            else:
                # 尝试从上游工具获取
                for proc_tool in procedure._tools.values():
                    if proc_tool == tool:
                        continue
                    if hasattr(proc_tool, '_output_data') and proc_tool._output_data is not None:
                        output_data = proc_tool._output_data.data
                        output_image = getattr(output_data, 'image', None)
                        if output_data is not None and isinstance(output_image, np.ndarray):
                            input_image = output_image
                            self._logger.info(f"运行流程后从上游工具 '{proc_tool.tool_name}' 获取图像")
                            break
        
        if input_image is None:
            self._logger.warning("工具没有输入图像，无法进行ROI选择")
            QMessageBox.warning(self, "警告", "请先配置好流程，确保工具有效输入图像")
            return
        
        # 打开ROI选择对话框（使用增强版ROI编辑器，支持拖拽编辑）
        from ui.roi_selection_dialog import ROISelectionDialog
        dialog = ROISelectionDialog(self, "选择ROI区域 - " + tool.tool_name, roi_type="rect")
        dialog.set_image(input_image)
        
        # 设置已有的ROI数据
        roi_data = tool.get_param(param_name, {})
        if roi_data:
            dialog.set_roi_data(roi_data)
        
        # 连接ROI选择完成信号
        def on_roi_selected(data):
            self._logger.info(f"ROI编辑完成: {data}")
            
            # 直接使用ROI数据（新编辑器已输出标准格式）
            tool.set_param(param_name, data)
            
            self._logger.info(f"ROI已设置: {data}")
            # 更新属性面板
            self.property_dock.show_tool_properties(tool)
            # 提示用户需要重新运行
            QMessageBox.information(self, "提示", "ROI已设置，请点击运行按钮使用新ROI进行匹配")
        
        dialog.roi_edited.connect(on_roi_selected)
        
        # 显示对话框
        self._logger.info("打开ROI选择对话框")
        dialog.exec()
    
    def _run_procedure_sync(self):
        """同步运行当前流程（用于获取数据）"""
        self._logger.info("同步运行流程以获取ROI选择所需的图像数据...")
        
        # 保存UI状态
        was_running = self._is_running
        self._is_running = True
        
        try:
            # 清除之前的结果
            # 清空结果面板
            if hasattr(self.result_dock.widget(), 'clear_results'):
                self.result_dock.widget().clear_results()
            
            # 运行所有流程
            if self.solution.procedures:
                for procedure in self.solution.procedures:
                    if procedure is None:
                        continue
                    
                    # 重置所有工具
                    for tool in procedure.tools:
                        if hasattr(tool, '_output_data'):
                            tool._output_data = None
                    
                    # 运行工具
                    for tool in procedure.tools:
                        if tool is None:
                            continue
                        try:
                            self._run_single_tool_sync(procedure, tool)
                        except Exception as e:
                            self._logger.error(f"运行工具失败: {tool.tool_name}, 错误: {e}")
                            import traceback
                            traceback.print_exc()
            
            self._logger.info("流程运行完成")
            
            # 收集所有工具的输出数据
            self._collect_tool_outputs()
            
        except Exception as e:
            self._logger.error(f"运行流程失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_running = was_running
    
    def _collect_tool_outputs(self):
        """收集所有工具的输出数据并传递给结果面板"""
        try:
            from ui.enhanced_result_panel import DataType
            
            available_modules = {}
            
            if self.solution.procedures:
                for procedure in self.solution.procedures:
                    if procedure is None:
                        continue
                    
                    for tool in procedure.tools:
                        if tool is None:
                            continue
                        
                        tool_name = getattr(tool, 'tool_name', 'Unknown')
                        tool_instance = getattr(tool, 'name', '') or ''
                        module_name = f"{tool_name}_{tool_instance}" if tool_instance else tool_name
                        
                        # 检查 _result_data
                        if hasattr(tool, '_result_data'):
                            if tool._result_data is not None:
                                result_data = tool._result_data
                                
                                if module_name not in available_modules:
                                    available_modules[module_name] = {}
                                
                                # 分析 _result_data 的属性
                                if hasattr(result_data, '_values'):
                                    values = result_data._values
                                    for key, value in values.items():
                                        display_key = self._get_chinese_key_name(key)
                                        data_type = self._get_data_type(value)
                                        available_modules[module_name][display_key] = data_type
                        
                        # 检查 _output_data
                        if hasattr(tool, '_output_data'):
                            if tool._output_data is not None:
                                output_data = tool._output_data
                                if hasattr(output_data, 'data') and output_data.data is not None:
                                    if module_name not in available_modules:
                                        available_modules[module_name] = {}
                                    if 'output_image' not in available_modules[module_name]:
                                        available_modules[module_name]['输出图像'] = DataType.IMAGE
            
            # 传递给结果面板
            if available_modules:
                self.result_dock.set_available_modules(available_modules)
                
        except Exception as e:
            self._logger.error(f"收集工具输出数据失败: {e}")
    
    def _get_data_type(self, value):
        """根据值获取数据类型"""
        from ui.enhanced_result_panel import DataType
        
        if value is None:
            return DataType.UNKNOWN
        elif isinstance(value, bool):
            return DataType.BOOL
        elif isinstance(value, int):
            return DataType.INT
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, str):
            return DataType.STRING
        elif hasattr(value, 'shape') or hasattr(value, 'dtype'):
            return DataType.IMAGE
        elif isinstance(value, (list, tuple)):
            return DataType.ARRAY
        elif isinstance(value, dict):
            return DataType.DICT
        elif hasattr(value, 'x') and hasattr(value, 'y'):
            return DataType.POINT
        elif hasattr(value, 'width') and hasattr(value, 'height'):
            return DataType.RECT
        else:
            return DataType.UNKNOWN
    
    def _get_chinese_key_name(self, key: str) -> str:
        """将英文键名转换为中文"""
        key_name_map = {
            # 通用
            "count": "数量",
            "status": "状态",
            "message": "消息",
            "confidence": "置信度",
            "result": "结果",
            "image": "图像",
            "image_size": "图像尺寸",
            "width": "宽度",
            "height": "高度",
            "x": "X坐标",
            "y": "Y坐标",
            
            # 条码相关
            "barcode_type": "条码类型",
            "barcode_data": "条码数据",
            "barcodes": "条码列表",
            "content": "内容",
            "points": "角点",
            "rect": "矩形区域",
            
            # 斑点分析
            "blob_count": "blob个数",
            "blobs": "blob列表",
            "blob_area": "blob面积",
            "blob_centroid": "blob中心",
            
            # 几何测量
            "angle": "角度",
            "length": "长度",
            "area": "面积",
            "perimeter": "周长",
            "center": "中心点",
            "radius": "半径",
            "diameter": "直径",
            
            # 模板匹配
            "match_score": "匹配分数",
            "match_position": "匹配位置",
            "match_angle": "匹配角度",
            
            # OCR
            "text": "文本",
            "rotated_rect": "旋转矩形",
            "corners": "角点",
        }
        return key_name_map.get(key, key)
    
    def _on_data_connection_requested(self, module_name: str, key: str, data_type):
        """处理数据连接请求
        
        当用户在结果面板选择数据时调用，根据模块名和键名获取实际数据，
        并传递给结果详情和可视化组件。
        """
        display_key = self._get_chinese_key_name(key)
        
        try:
            target_tool = None
            
            for procedure in self.solution.procedures:
                if procedure is None:
                    continue
                for tool in procedure.tools:
                    if tool is None:
                        continue
                    
                    tool_name = getattr(tool, 'tool_name', 'Unknown')
                    tool_instance = getattr(tool, 'name', '') or ''
                    full_name = f"{tool_name}_{tool_instance}" if tool_instance else tool_name
                    
                    if full_name == module_name:
                        target_tool = tool
                        break
                if target_tool:
                    break
            
            if not target_tool:
                return
            
            if hasattr(target_tool, '_result_data') and target_tool._result_data:
                result_data = target_tool._result_data
                
                actual_value = None
                if hasattr(result_data, '_values') and key in result_data._values:
                    actual_value = result_data._values[key]
                elif hasattr(result_data, 'get_value'):
                    actual_value = result_data.get_value(key)
                else:
                    return
                
                from data.image_data import ResultData
                display_result = ResultData()
                display_result.set_value(display_key, actual_value)
                display_result.set_value("原始键名", key)
                display_result.set_value("来源模块", module_name)
                display_result._status = True
                display_result._message = f"从 {module_name} 获取的数据"
                
                enhanced_panel = self.result_dock.get_panel()
                enhanced_panel.detail_widget.set_result(display_result, "connection")
                enhanced_panel.viz_widget.set_result(display_result, "connection")
                
        except Exception:
            pass
    
    def _run_single_tool_sync(self, procedure, tool):
        """同步运行单个工具"""
        # 设置输入数据
        if tool.has_input():
            # 从连接的工具获取输入
            for connection in procedure.connections:
                if connection.to_tool == tool.name:
                    from_tool = procedure.get_tool(connection.from_tool)
                    if from_tool and hasattr(from_tool, '_output_data') and from_tool._output_data:
                        tool.set_input(from_tool._output_data)
                        self._logger.debug(f"设置工具输入: {tool.tool_name} <- {from_tool.tool_name}")
                        break
        
        # 执行工具
        try:
            result = tool.run()
            self._logger.debug(f"工具执行完成: {tool.tool_name}, 结果: {result}")
            
            # 将结果添加到结果面板
            if hasattr(tool, '_result_data') and tool._result_data:
                self.result_dock.add_result(tool._result_data)
                self._logger.debug(f"结果已添加到结果面板: {tool.tool_name}")
        except Exception as e:
            self._logger.error(f"工具执行失败: {tool.tool_name}, 错误: {e}")
            raise
    
    def _on_tool_dropped(self, tool_name: str, position: QPointF):
        """工具拖拽释放事件"""
        self._logger.info(f"收到工具拖拽释放信号: tool_name={tool_name}, position=({position.x()}, {position.y()})")
        
        # 检查视图是否已经初始化
        if self.algorithm_view is None or self.algorithm_view.viewport() is None:
            self._logger.warning("algorithm_view 未初始化，使用默认位置")
            adjusted_position = QPointF(100, 100)
            self._create_tool_on_editor(tool_name, adjusted_position)
            return
        
        # 计算场景的可见区域边界
        viewport_rect = self.algorithm_view.viewport().rect()
        
        # 检查viewport是否有效
        if viewport_rect.width() <= 0 or viewport_rect.height() <= 0:
            self._logger.warning(f"viewport尺寸无效: {viewport_rect.width()}x{viewport_rect.height()}，使用默认位置")
            adjusted_position = QPointF(100, 100)
            self._create_tool_on_editor(tool_name, adjusted_position)
            return
        
        self._logger.info(f"视口大小: {viewport_rect.width()}x{viewport_rect.height()}")
        self._logger.info(f"原始位置（视口坐标）: ({position.x():.1f}, {position.y():.1f})")
        
        # 检查位置是否在视口内
        is_in_viewport = (
            0 <= position.x() <= viewport_rect.width() and
            0 <= position.y() <= viewport_rect.height()
        )
        
        # 在视图中心附近添加偏移，避免重叠
        offset = len(self.tool_items) * 60
        
        # 使用视口中心位置 + 偏移
        center_x = viewport_rect.width() / 2
        center_y = viewport_rect.height() / 2
        
        if is_in_viewport:
            # 位置在视口内，使用原始位置 + 偏移
            adjusted_position = QPointF(position.x() + offset, position.y() + offset)
            self._logger.info(f"位置在视口内，使用原始位置偏移: ({adjusted_position.x():.1f}, {adjusted_position.y():.1f})")
        else:
            # 位置不在视口内，使用视口中心位置 + 偏移
            adjusted_position = QPointF(center_x + offset, center_y + offset)
            self._logger.info(f"位置不在视口内，使用视口中心偏移位置: ({adjusted_position.x():.1f}, {adjusted_position.y():.1f})")
        
        # 在编辑器中创建工具
        self._create_tool_on_editor(tool_name, adjusted_position)
    
    def _create_tool_on_editor(self, tool_name: str, position: QPointF):
        """在编辑器中创建工具"""
        self._logger.info(f"创建工具: {tool_name}，位置: {position}")
        
        # 查找工具数据
        tool_data = None
        self._logger.debug(f"查找工具数据，工具名称: {tool_name}")
        
        # 从新的工具库获取工具数据
        tool_data = self.tool_library_dock.get_tool_library().get_tool_data(tool_name)
        
        if tool_data is None:
            self._logger.error(f"未找到工具数据: {tool_name}")
            return
        
        # 创建工具实例
        self._logger.info(f"创建工具实例: {tool_data.category}.{tool_data.name}")
        tool = ToolRegistry.create_tool(tool_data.category, tool_data.name, tool_name)
        
        if tool is None:
            self._logger.error(f"创建工具实例失败: {tool_data.category}.{tool_data.name}")
            return
        
        # 调用initialize方法初始化工具（应用默认参数）
        if hasattr(tool, 'initialize') and callable(tool.initialize):
            params = tool.get_all_params()
            tool.initialize(params)
            self._logger.info(f"工具已初始化: {tool_name}")
        
        # 创建图形项
        self._logger.debug(f"创建图形项，位置: {position}")
        graphics_item = GraphicsToolItem(tool, position)
        # 保存工具数据到图形项
        graphics_item.tool_data = tool_data
        self.algorithm_scene.addItem(graphics_item)
        
        # 保存
        self.tool_items[tool_name] = graphics_item
        self._logger.debug(f"保存工具图形项: {tool_name}")
        
        # 添加到流程
        if self.current_procedure:
            self.current_procedure.add_tool(tool)
            self._logger.debug(f"添加到流程: {self.current_procedure.name}, 当前流程工具数: {self.current_procedure.tool_count}")
        else:
            self._logger.warning(f"current_procedure 为空，无法添加工具到流程")
        
        # 更新项目树
        self._update_project_tree()
        self._logger.debug("更新项目树")
        
        self.update_status(f"已添加工具: {tool_name}")
        self._logger.info(f"工具创建完成: {tool_name}")
    
    def _on_port_connection(self, from_port: PortItem, to_port: PortItem):
        """端口连线回调函数
        
        Args:
            from_port: 源端口（输出端口）
            to_port: 目标端口（输入端口）
        """
        # 获取工具名称
        from_tool_name = from_port.parent_item.tool.tool_name
        to_tool_name = to_port.parent_item.tool.tool_name
        
        self._logger.info(f"[MAIN] 端口连线: {from_tool_name} -> {to_tool_name}")
        
        # 调用连接工具方法
        success = self.connect_tools(from_tool_name, to_tool_name)
        
        if success:
            self.update_status(f"已连接: {from_tool_name} -> {to_tool_name}")
        else:
            self.update_status(f"连接失败: {from_tool_name} -> {to_tool_name}")
    
    def _on_tool_clicked(self, tool_item: 'GraphicsToolItem'):
        """工具点击事件 - 显示该工具的输出图像
        
        Args:
            tool_item: 被点击的工具图形项
        """
        tool = tool_item.tool
        self._logger.info(f"[MAIN] 点击工具: {tool.tool_name}")
        
        # 更新状态栏显示当前模块
        self.current_tool_status.setText(f"当前模块: {tool.tool_name}")
        self.current_tool_status.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                padding-left: 20px;
                border-left: 2px solid #ddd;
                min-width: 150px;
            }
        """)
        
        # 优先显示输出图像
        output_data = tool.get_output("OutputImage")
        
        if output_data is not None and output_data.is_valid:
            self._logger.info(f"[MAIN] 显示 {tool.tool_name} 的输出图像")
            self._display_image(output_data, tool.tool_name)
            return
        
        # 如果没有输出图像，从上游工具获取输入图像
        from_tool = self._get_upstream_tool(tool)
        if from_tool:
            upstream_output = from_tool.get_output("OutputImage")
            if upstream_output and upstream_output.is_valid:
                self._logger.info(f"[MAIN] {tool.tool_name} 尚未运行，显示上游 {from_tool.tool_name} 的图像")
                self._display_image(upstream_output, f"{tool.tool_name} (输入)")
                return
        
        # 尝试显示工具自身的输入数据
        input_data = tool.get_input()
        if input_data is not None and input_data.is_valid:
            self._logger.info(f"[MAIN] {tool.tool_name} 显示输入图像")
            self._display_image(input_data, f"{tool.tool_name} (输入)")
            return
        
        # 都没有图像，显示提示
        self._logger.warning(f"[MAIN] {tool.tool_name} 没有有效的图像数据")
        self.current_display_image = None
        self.current_display_tool_name = None
        
        # 清除场景中的图像
        self.image_scene.clear()
        
        # 显示提示
        text_item = QGraphicsTextItem(f"{tool.tool_name}\n暂无图像数据\n（请先运行流程）")
        text_item.setDefaultTextColor(QColor(150, 150, 150))
        text_item.setFont(QFont("Arial", 14))
        text_rect = text_item.boundingRect()
        text_item.setPos(QPointF(200 - text_rect.width() / 2, 150 - text_rect.height() / 2))
        self.image_scene.addItem(text_item)
    
    def _display_image(self, image_data: ImageData, tool_name: str):
        """在图像视图中显示图像
        
        Args:
            image_data: 图像数据
            tool_name: 工具名称（用于显示）
        """
        # 保存当前显示信息
        self.current_display_image = image_data
        self.current_display_tool_name = tool_name
        
        # 清除场景
        self.image_scene.clear()
        
        # 获取图像数据
        if image_data.is_valid:
            image = image_data.data
            
            # 转换为RGB格式用于显示
            if len(image.shape) == 2:
                # 灰度图像
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                # BGR图像（OpenCV默认格式）
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 创建QImage
            h, w, c = image_rgb.shape
            bytes_per_line = c * w
            
            # 根据PyQt版本选择正确的Format
            if PYQT_VERSION == 6:
                qimage_format = QImage.Format.Format_RGB888
            else:
                qimage_format = QImage.Format_RGB888
            
            qimage = QImage(image_rgb.data, w, h, bytes_per_line, qimage_format)
            
            # 创建QPixmap
            pixmap = QPixmap.fromImage(qimage)
            
            # 设置场景背景为专业的深灰色网格
            self.image_scene.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
            
            # 创建图像容器，添加专业的边框和阴影效果
            container = QGraphicsRectItem()
            container.setBrush(QBrush(QColor(60, 60, 60)))
            container.setPen(QPen(QColor(100, 100, 100), 1))
            container.setZValue(-2)
            
            # 添加到场景
            self.image_scene.addItem(container)
            
            # 创建图像项
            pixmap_item = QGraphicsPixmapItem(pixmap)
            pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            pixmap_item.setZValue(-1)
            
            # 计算合适的显示尺寸（保持原图比例，最大适应视图的90%）
            view_size = self.image_view.viewport().size()
            max_display_width = int(view_size.width() * 0.9)
            max_display_height = int(view_size.height() * 0.9)
            
            display_size = pixmap.size()
            display_size.scale(
                max_display_width,
                max_display_height,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            
            # 调整图像大小
            scaled_pixmap = pixmap.scaled(
                display_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            pixmap_item.setPixmap(scaled_pixmap)
            
            # 添加到场景并居中
            self.image_scene.addItem(pixmap_item)
            
            # 调整容器大小以适应图像
            container_rect = QRectF(pixmap_item.boundingRect())
            container_rect.adjust(-10, -10, 10, 10)  # 添加10px边距
            container.setRect(container_rect)
            
            # 计算居中位置
            scene_rect = self.image_scene.sceneRect()
            container_center = scene_rect.center()
            container_offset = QPointF(
                container_center.x() - container_rect.width() / 2,
                container_center.y() - container_rect.height() / 2
            )
            
            # 移动容器和图像
            container.setPos(container_offset)
            pixmap_item.setPos(container_offset.x() + 10, container_offset.y() + 10)
            
            # 添加图像信息文本
            info_text = f"{tool_name} | {w}×{h} | {c}通道"
            text_item = QGraphicsTextItem(info_text)
            text_item.setDefaultTextColor(QColor(200, 200, 200))
            text_item.setFont(QFont("Microsoft YaHei", 10))
            
            # 计算文本位置（图像下方居中）
            text_rect = text_item.boundingRect()
            text_pos = QPointF(
                container_offset.x() + container_rect.width() / 2 - text_rect.width() / 2,
                container_offset.y() + container_rect.height() + 5
            )
            text_item.setPos(text_pos)
            text_item.setZValue(1)
            self.image_scene.addItem(text_item)
            
            self._logger.info(f"[MAIN] 显示图像: {tool_name}, 分辨率: {w}x{h}")
        else:
            # 显示无效图像占位符
            self.image_scene.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
            
            # 创建占位符文本
            placeholder_text = QGraphicsTextItem("无效图像数据")
            placeholder_text.setDefaultTextColor(QColor(150, 150, 150))
            placeholder_text.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            
            # 居中显示
            text_rect = placeholder_text.boundingRect()
            scene_rect = self.image_scene.sceneRect()
            text_pos = QPointF(
                scene_rect.center().x() - text_rect.width() / 2,
                scene_rect.center().y() - text_rect.height() / 2
            )
            placeholder_text.setPos(text_pos)
            self.image_scene.addItem(placeholder_text)
            
            self._logger.warning(f"[MAIN] 无效的图像数据: {tool_name}")
    
    def _on_project_item_double_clicked(self, item_type: str, item_object: Any):
        """项目树节点双击事件"""
        self._logger.info(f"双击项目节点: {item_type}, {item_object}")
        
        if item_type == "tool":
            # 显示工具属性
            self.property_dock.show_tool_properties(item_object)
        elif item_type == "procedure":
            # 切换到指定流程
            self.current_procedure = item_object
        elif item_type == "solution":
            # 处理方案双击事件
            pass
    
    def _on_project_item_selected(self, item_type: str, item_object: Any):
        """项目树节点选择事件"""
        self._logger.info(f"选择项目节点: {item_type}, {item_object}")
        
        if item_type == "tool":
            # 显示工具属性（先检查property_dock是否存在）
            if hasattr(self, 'property_dock') and self.property_dock:
                self.property_dock.show_tool_properties(item_object)
            else:
                self._logger.warning("property_dock 尚未初始化")
            
            # 在算法场景中选中对应的工具项
            for name, tool_item in self.tool_items.items():
                if tool_item.tool == item_object:
                    # 清除其他选择
                    self.algorithm_scene.clearSelection()
                    # 选中该工具项
                    tool_item.setSelected(True)
                    self._logger.info(f"已选中工具: {name}")
                    break
        elif item_type == "procedure":
            # 切换当前流程
            self.current_procedure = item_object
            # 显示流程属性
            if hasattr(self, 'property_dock') and self.property_dock:
                self.property_dock.clear_properties()
        elif item_type == "solution":
            # 显示方案属性
            if hasattr(self, 'property_dock') and self.property_dock:
                self.property_dock.clear_properties()
    
    def _on_procedure_created(self, procedure):
        """新建流程事件"""
        self._logger.info(f"新建流程: {procedure.name}")
        # 切换到新创建的流程
        self.current_procedure = procedure
        # 切换到新的流程（触发流程选择事件）
        self._on_project_item_selected("procedure", procedure)
    
    def _on_project_item_deleted(self, item_type: str, item_object: Any):
        """项目树节点删除事件"""
        self._logger.info(f"删除项目节点: {item_type}, {item_object}")
        
        if item_type == "tool":
            # 找到对应的工具图形项
            tool_item = None
            tool_name = None
            for name, item in list(self.tool_items.items()):
                if item.tool == item_object:
                    tool_item = item
                    tool_name = name
                    break
            
            if tool_item:
                # 删除工具相关的所有连线（使用工具的方法）
                tool_item.delete_related_connections()
                
                # 从流程中移除工具
                if self.current_procedure:
                    self.current_procedure.remove_tool(tool_item.tool.name)
                
                # 从场景中移除工具项
                self.algorithm_scene.removeItem(tool_item)
                
                # 从工具项字典中移除
                if tool_name in self.tool_items:
                    del self.tool_items[tool_name]
                
                # 清理 connection_items 中相关的连线
                connections_to_remove = []
                for key, conn_item in self.connection_items.items():
                    if conn_item in self.algorithm_scene.items():
                        continue  # 连线已经被删除
                    connections_to_remove.append(key)
                
                for key in connections_to_remove:
                    if key in self.connection_items:
                        del self.connection_items[key]
        
        elif item_type == "procedure":
            # 清空算法编辑器
            self.algorithm_scene.clear()
            self.tool_items.clear()
            self.connection_items.clear()
            
            # 先从Solution中移除流程
            if item_object in self.solution.procedures:
                self.solution.procedures.remove(item_object)
            
            # 更新当前流程
            if self.solution.procedures:
                self.current_procedure = self.solution.procedures[0]
                # 切换到新的流程（触发流程选择事件）
                self._on_project_item_selected("procedure", self.current_procedure)
            else:
                self.current_procedure = None
            
            # 延迟刷新项目树（避免与项目浏览器的删除操作冲突）
            QTimer.singleShot(100, self.project_dock.refresh)
    
    def _update_project_tree(self):
        """更新项目树（使用项目浏览器刷新）"""
        QTimer.singleShot(50, self.project_dock.refresh)
    
    def connect_tools(self, from_tool_name: str, to_tool_name: str):
        """连接两个工具
        
        Args:
            from_tool_name: 源工具名称
            to_tool_name: 目标工具名称
        
        Returns:
            bool: 连接成功返回True，否则返回False
        """
        # 检查工具是否存在
        if from_tool_name not in self.tool_items or to_tool_name not in self.tool_items:
            self._logger.error(f"连接工具失败：工具不存在 - from_tool={from_tool_name}, to_tool={to_tool_name}")
            return False
        
        # 检查连接是否已存在
        connection_key = (from_tool_name, to_tool_name)
        if connection_key in self.connection_items:
            self._logger.warning(f"连接已存在：{from_tool_name} -> {to_tool_name}")
            return False
        
        # 获取工具图形项
        from_item = self.tool_items[from_tool_name]
        to_item = self.tool_items[to_tool_name]
        
        # 在流程中连接工具
        if self.current_procedure:
            if not self.current_procedure.connect(from_tool_name, to_tool_name):
                self._logger.error(f"在流程中连接工具失败：{from_tool_name} -> {to_tool_name}")
                return False
        
        # 创建连接线（使用新的 ConnectionLine 类）
        from_port = from_item.output_port
        to_port = to_item.input_port
        connection_line = ConnectionLine(from_port, to_port)
        self.algorithm_scene.addItem(connection_line)
        
        # 保存连接项
        self.connection_items[connection_key] = connection_line
        
        self._logger.info(f"连接工具成功：{from_tool_name} -> {to_tool_name}")
        return True
    
    def disconnect_tools(self, from_tool_name: str, to_tool_name: str):
        """断开两个工具的连接
        
        Args:
            from_tool_name: 源工具名称
            to_tool_name: 目标工具名称
        
        Returns:
            bool: 断开成功返回True，否则返回False
        """
        # 检查连接是否存在
        connection_key = (from_tool_name, to_tool_name)
        if connection_key not in self.connection_items:
            self._logger.warning(f"连接不存在：{from_tool_name} -> {to_tool_name}")
            return False
        
        # 从流程中断开工具
        if self.current_procedure:
            self.current_procedure.disconnect(from_tool_name, to_tool_name)
        
        # 移除连接线（使用新的 delete 方法）
        connection_item = self.connection_items.pop(connection_key)
        connection_item.delete()
        
        self._logger.info(f"断开工具连接成功：{from_tool_name} -> {to_tool_name}")
        return True
    
    def update_all_connections(self):
        """更新所有连接线条的位置
        
        Returns:
            None
        """
        self._logger.debug("更新所有连接线条位置")
        for connection_item in self.connection_items.values():
            connection_item.update_position()
    
    def _on_tool_connected(self, from_tool: ToolBase, to_tool: ToolBase):
        """处理工具连接事件
        
        Args:
            from_tool: 源工具
            to_tool: 目标工具
        
        Returns:
            None
        """
        self._logger.info(f"工具连接事件：{from_tool.name} -> {to_tool.name}")
        self.connect_tools(from_tool.name, to_tool.name)
    
    def _on_tool_disconnected(self, from_tool: ToolBase, to_tool: ToolBase):
        """处理工具断开事件
        
        Args:
            from_tool: 源工具
            to_tool: 目标工具
        
        Returns:
            None
        """
        self._logger.info(f"工具断开事件：{from_tool.name} -> {to_tool.name}")
        self.disconnect_tools(from_tool.name, to_tool.name)
    
    # 文件操作
    def new_solution(self):
        """新建方案"""
        self.solution.clear()
        self.algorithm_scene.clear()
        self.tool_items.clear()
        
        # 创建默认流程
        self.current_procedure = Procedure("流程1")
        self.solution.add_procedure(self.current_procedure)
        
        # 更新项目浏览器
        self.project_dock.set_solution(self.solution)
        self.update_status("新建方案")
    
    def _show_camera_settings(self):
        """显示相机设置"""
        from tools.image_source import CameraSettingsDialog
        
        dialog = CameraSettingsDialog(self)
        dialog.show()
        dialog.shutdown()
    
    def open_solution(self):
        """打开方案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开方案", "", "方案文件 (*.vmsol);;所有文件 (*.*)"
        )
        
        if file_path:
            if self.solution.load(file_path):
                # 更新项目浏览器
                self.project_dock.set_solution(self.solution)
                self.update_status(f"已打开: {Path(file_path).name}")
    
    def save_solution(self):
        """保存方案"""
        if self.solution.solution_path:
            self.solution.save()
            self.update_status(f"已保存: {Path(self.solution.solution_path).name}")
        else:
            self.save_solution_as()
    
    def save_solution_as(self):
        """另存为方案"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存方案", "", "方案文件 (*.vmsol);;所有文件 (*.*)"
        )
        
        if file_path:
            self.solution.save(file_path)
            self._update_project_tree()
            self.update_status(f"已保存: {Path(file_path).name}")
    
    # 图像操作
    def load_image(self):
        """加载图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载图像", "", "图像文件 (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)"
        )
        
        if file_path:
            # 使用支持中文路径的方式加载
            try:
                data = np.fromfile(file_path, dtype=np.uint8)
                image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            except:
                image = cv2.imread(file_path)
            
            if image is not None:
                self.current_image = ImageData(data=image)
                self._display_image(self.current_image)
                self.update_status(f"已加载: {Path(file_path).name}")
            else:
                self.update_status("加载图像失败")
    
    def save_image(self):
        """保存图像"""
        if self.current_image is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图像", "", "JPEG (*.jpg);;PNG (*.png);;BMP (*.bmp)"
        )
        
        if file_path:
            try:
                cv2.imencode('.jpg', self.current_image.data)[1].tofile(file_path)
                self.update_status(f"已保存: {Path(file_path).name}")
            except:
                self.update_status("保存图像失败")
    
    # 运行操作
    def run_once(self):
        """单次运行 - 按模块连接关系传递图像数据"""
        if not self.solution.procedures:
            self.update_status("没有可执行的流程")
            return
        
        if not self.current_procedure:
            self.update_status("请先选择一个流程")
            return
        
        self.update_status("运行中...")
        
        try:
            # 按依赖关系执行工具
            execution_order = self._get_execution_order()
            
            for tool in execution_order:
                self._logger.info(f"[RUN] 执行工具: {tool.tool_name}")
                
                # 对于非图像源工具，从上游工具获取输入
                if tool.tool_category != "ImageSource":
                    # 查找连接到该工具的输出端口的工具
                    from_tool = self._get_upstream_tool(tool)
                    if from_tool and from_tool.has_output():
                        input_data = from_tool.get_output("OutputImage")
                        if input_data and input_data.is_valid:
                            tool.set_input(input_data, "InputImage")
                            self._logger.info(f"[RUN] 从 {from_tool.tool_name} 获取输入图像")
                
                # 执行工具
                tool.run()
                
                # 将结果添加到结果面板
                if hasattr(tool, '_result_data') and tool._result_data:
                    self.result_dock.add_result(tool._result_data)
                    self._logger.debug(f"结果已添加到结果面板: {tool.tool_name}")
                
                self._logger.info(f"[RUN] {tool.tool_name} 执行完成")
            
            # 显示结果
            results = {self.current_procedure.name: {}}
            for tool in execution_order:
                if tool.has_output():
                    results[self.current_procedure.name][tool.tool_name] = {
                        "output": tool.get_output(),
                        "result": tool.get_result()
                    }
            
            self._show_results(results)
            
            # 自动显示最后一个工具的输出图像
            if execution_order:
                last_tool = execution_order[-1]
                output = last_tool.get_output("OutputImage")
                if output and output.is_valid:
                    self._logger.info(f"[RUN] 自动显示 {last_tool.tool_name} 的输出图像")
                    self._display_image(output, last_tool.tool_name)
                    # 更新当前显示的工具名称
                    self.current_display_tool_name = last_tool.tool_name
                    self.current_tool_status.setText(f"当前模块: {last_tool.tool_name}")
                    self.current_tool_status.setStyleSheet("""
                        QLabel {
                            color: #4CAF50;
                            font-weight: bold;
                            padding-left: 20px;
                            border-left: 2px solid #ddd;
                            min-width: 150px;
                        }
                    """)
                else:
                    # 如果最后一个工具没有输出，尝试找第一个有输出的工具
                    for tool in execution_order:
                        output = tool.get_output("OutputImage")
                        if output and output.is_valid:
                            self._logger.info(f"[RUN] 自动显示 {tool.tool_name} 的输出图像")
                            self._display_image(output, tool.tool_name)
                            self.current_display_tool_name = tool.tool_name
                            self.current_tool_status.setText(f"当前模块: {tool.tool_name}")
                            break
            
            self.update_status("运行完成")
            
            # 收集工具输出数据
            self._collect_tool_outputs()
            
        except Exception as e:
            self.update_status(f"运行失败: {str(e)}")
            self._logger.error(f"运行失败: {e}")
            
            # 即使执行失败，也尝试显示图像
            if execution_order:
                # 优先显示最后一个工具的上游工具的输出
                last_tool = execution_order[-1]
                upstream_tool = self._get_upstream_tool(last_tool)
                if upstream_tool:
                    upstream_output = upstream_tool.get_output("OutputImage")
                    if upstream_output and upstream_output.is_valid:
                        self._logger.info(f"[RUN] 执行失败但显示上游 {upstream_tool.tool_name} 的图像")
                        self._display_image(upstream_output, f"{last_tool.tool_name} (输入)")
                        return
                
                # 如果没有上游工具，尝试从后往前找有输出的工具
                for tool in reversed(execution_order):
                    output = tool.get_output("OutputImage")
                    if output and output.is_valid:
                        self._logger.info(f"[RUN] 执行失败但显示 {tool.tool_name} 的输出图像")
                        self._display_image(output, tool.tool_name)
                        return
    
    def _get_execution_order(self) -> List[ToolBase]:
        """获取工具执行顺序（按依赖关系排序）
        
        优先执行图像源工具，然后按连接关系执行后续工具
        """
        if not self.current_procedure:
            return []
        
        tools = self.current_procedure.tools
        
        # 创建工具名称到工具的映射
        tool_name_map = {tool.tool_name: tool for tool in tools}
        
        # 获取连接关系
        connections = self.current_procedure.connections
        
        # 拓扑排序
        executed = set()
        order = []
        
        def execute_tool(tool):
            if tool in executed:
                return
            
            executed.add(tool)
            
            # 先执行依赖的工具
            for conn in connections:
                if conn.to_tool == tool.tool_name:
                    from_tool_name = conn.from_tool
                    if from_tool_name in tool_name_map:
                        from_tool = tool_name_map[from_tool_name]
                        execute_tool(from_tool)
            
            order.append(tool)
        
        # 先执行所有图像源工具
        for tool in tools:
            if tool.tool_category == "ImageSource":
                execute_tool(tool)
        
        # 再执行其他工具
        for tool in tools:
            if tool.tool_category != "ImageSource":
                execute_tool(tool)
        
        return order
    
    def _get_upstream_tool(self, tool: ToolBase) -> Optional[ToolBase]:
        """获取连接到指定工具输入端口的上游工具
        
        Args:
            tool: 目标工具
            
        Returns:
            上游工具，如果没有则返回None
        """
        if not self.current_procedure:
            return None
        
        connections = self.current_procedure.connections
        
        for conn in connections:
            # 使用tool._name（实例名称）进行比较，而不是tool.tool_name（类型名称）
            if conn.to_tool == tool._name:
                from_tool_name = conn.from_tool
                tools = self.current_procedure.tools
                tool_name_map = {t._name: t for t in tools}
                if from_tool_name in tool_name_map:
                    return tool_name_map[from_tool_name]
        
        return None
    
    def run_continuous(self):
        """连续运行"""
        self.solution.run_interval = 1000
        self.solution.runing()
        self.update_status("连续运行中...")
    
    def stop_run(self):
        """停止运行"""
        self.solution.stop_run()
        self.update_status("已停止")
    
    def _show_results(self, results: dict):
        """显示结果"""
        # 清空之前的结果
        # self.result_dock.clear_results()
        
        for proc_name, proc_results in results.items():
            self.result_dock.add_info(f"流程: {proc_name}")
            if isinstance(proc_results, dict):
                for tool_name, tool_result in proc_results.items():
                    if isinstance(tool_result, dict):
                        output = tool_result.get("output")
                        result = tool_result.get("result")
                        if result:
                            self.result_dock.add_success(
                                f"工具: {tool_name}",
                                details=result.get_all_values(),
                                tool_name=tool_name
                            )
                    elif "error" in tool_result:
                        self.result_dock.add_error(
                            f"工具: {tool_name} 执行失败",
                            details={"error": tool_result["error"]},
                            tool_name=tool_name
                        )
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.setText(message)
        # 同时将状态信息添加到结果面板
        self.result_dock.add_info(message)
    
    def show_communication_config(self):
        """显示通讯配置停靠窗口"""
        if not hasattr(self, '_comm_config_widget') or self._comm_config_widget is None:
            # 创建通讯配置组件
            self._comm_config_widget = get_communication_config_widget()
            
            # 创建停靠窗口
            self._comm_config_dock = QDockWidget("通讯配置", self)
            self._comm_config_dock.setWidget(self._comm_config_widget)
            self._comm_config_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
            
            # 如果通讯监控已存在，将它们放在同一标签页
            if hasattr(self, '_comm_monitor_dock') and self._comm_monitor_dock is not None:
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._comm_config_dock)
                self.tabifyDockWidget(self._comm_config_dock, self._comm_monitor_dock)
            else:
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._comm_config_dock)
        
        self._comm_config_dock.show()
        self._comm_config_dock.raise_()
        self._comm_config_dock.activateWindow()
    
    def show_communication_monitor(self):
        """显示通讯监控面板"""
        if not hasattr(self, '_comm_monitor_widget') or self._comm_monitor_widget is None:
            self._comm_monitor_widget = CommunicationMonitorWidget(self)
            self._comm_monitor_dock = QDockWidget("通讯监控", self)
            self._comm_monitor_dock.setWidget(self._comm_monitor_widget)
            self._comm_monitor_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._comm_monitor_dock)
        
        self._comm_monitor_dock.show()
        self._comm_monitor_dock.raise_()
    
    def _show_cpu_optimization_dialog(self):
        """显示CPU优化配置对话框"""
        try:
            if not hasattr(self, '_cpu_optimize_dialog') or self._cpu_optimize_dialog is None:
                self._cpu_optimize_dialog = CPUOptimizationDialog(self)
            
            self._cpu_optimize_dialog.show()
            self._cpu_optimize_dialog.raise_()
            self._cpu_optimize_dialog.activateWindow()
            
        except ImportError as e:
            QMessageBox.warning(self, "警告", f"CPU优化模块不可用: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开CPU优化配置失败:\n{str(e)}")
    
    def _show_performance_monitor(self):
        """显示性能监控面板"""
        try:
            if not hasattr(self, '_perf_monitor_widget') or self._perf_monitor_widget is None:
                self._perf_monitor_widget = PerformanceMonitorWidget(self)
                
                self._perf_monitor_dock = QDockWidget("性能监控", self)
                self._perf_monitor_dock.setWidget(self._perf_monitor_widget)
                self._perf_monitor_dock.setAllowedAreas(
                    Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea
                )
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._perf_monitor_dock)
            
            self._perf_monitor_dock.show()
            self._perf_monitor_dock.raise_()
            self._perf_monitor_dock.activateWindow()
            
        except ImportError as e:
            QMessageBox.warning(self, "警告", f"性能监控模块不可用: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开性能监控失败:\n{str(e)}")
    
    def import_solution_package(self):
        """导入方案包"""
        try:
            # 选择文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入方案包", "", 
                "VisionMaster方案包 (*.vmsol);;JSON方案 (*.json);;YAML方案 (*.yaml);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 使用SolutionFileManager导入方案包
            file_manager = SolutionFileManager()
            data = file_manager.import_solution_package(file_path)
            
            if data:
                QMessageBox.information(self, "成功", f"方案包已导入:\n{file_path}")
                self.update_status(f"方案包导入成功: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "导入方案包失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入方案包时发生错误:\n{str(e)}")
    
    def export_solution_package(self):
        """导出方案包"""
        try:
            if not self.solution:
                QMessageBox.warning(self, "警告", "没有可导出的方案")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出方案包", f"{self.solution.name}.vmsol", 
                "VisionMaster方案包 (*.vmsol);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 使用SolutionFileManager导出方案包
            file_manager = SolutionFileManager()
            success = file_manager.save_solution(self.solution, file_path, format='vmsol', include_code=True, include_docs=True)
            
            if success:
                QMessageBox.information(self, "成功", f"方案包已导出到:\n{file_path}")
                self.update_status(f"方案包导出成功: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "导出方案包失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出方案包时发生错误:\n{str(e)}")
    
    def export_solution_code(self):
        """导出方案代码"""
        try:
            if not self.solution:
                QMessageBox.warning(self, "警告", "没有可导出的方案")
                return
            
            # 选择保存路径
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择代码保存目录", ""
            )
            
            if not dir_path:
                return
            
            # 使用CodeGenerator导出代码
            code_gen = CodeGenerator()
            success = code_gen.generate_solution_code(self.solution, dir_path)
            
            if success:
                QMessageBox.information(self, "成功", f"方案代码已导出到:\n{dir_path}")
                self.update_status(f"方案代码导出成功")
            else:
                QMessageBox.critical(self, "错误", "导出方案代码失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出方案代码时发生错误:\n{str(e)}")
    
    def export_solution_docs(self):
        """导出方案文档"""
        try:
            if not self.solution:
                QMessageBox.warning(self, "警告", "没有可导出的方案")
                return
            
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出方案文档", f"{self.solution.name}_文档.md", 
                "Markdown文档 (*.md);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
            
            # 使用DocumentationGenerator导出文档
            doc_gen = DocumentationGenerator()
            success = doc_gen.generate_solution_docs(self.solution, file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"方案文档已导出到:\n{file_path}")
                self.update_status(f"方案文档导出成功: {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "错误", "导出方案文档失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出方案文档时发生错误:\n{str(e)}")
    
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        event.accept()


def main():
    """主函数"""
    if PYQT_VERSION == 6:
        from PyQt6.QtWidgets import QApplication
    else:
        from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    if PYQT_VERSION == 6:
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
