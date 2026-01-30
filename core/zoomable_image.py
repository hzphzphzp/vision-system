#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可缩放图像组件

提供通用的图像缩放和平移功能，可被其他组件继承或嵌入使用。

功能:
- 鼠标滚轮缩放
- 拖拽平移
- 缩放范围限制
- 缩放变化信号

Usage:
# 方式1: 继承使用
class MyImageCanvas(ZoomableGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 自定义初始化

# 方式2: 嵌入使用
canvas = ZoomableGraphicsView(parent)
canvas.set_image(qpixmap)
"""

import logging
from typing import Optional

try:
    from PyQt6.QtCore import QPointF, QSize, Qt, pyqtSignal
    from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap
    from PyQt6.QtWidgets import (
        QGraphicsPixmapItem,
        QGraphicsScene,
        QGraphicsView,
        QWidget,
    )

    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtCore import QPointF, QSize, Qt, pyqtSignal
    from PyQt5.QtGui import QBrush, QColor, QImage, QPainter, QPixmap
    from PyQt5.QtWidgets import (
        QGraphicsPixmapItem,
        QGraphicsScene,
        QGraphicsView,
        QWidget,
    )

    PYQT_VERSION = 5


def _get_resize_anchor():
    """获取合适的ResizeAnchor枚举值"""
    if PYQT_VERSION == 6:
        return QGraphicsView.ViewportAnchor.CenterAnchor
    else:
        return QGraphicsView.ViewportAnchor.AnchorViewCenter


def _get_transformation_anchor():
    """获取合适的TransformationAnchor枚举值"""
    if PYQT_VERSION == 6:
        return QGraphicsView.ViewportAnchor.CenterAnchor
    else:
        return QGraphicsView.ViewportAnchor.AnchorViewCenter


def _get_smooth_transformation():
    """获取合适的平滑变换枚举值"""
    if PYQT_VERSION == 6:
        return Qt.TransformationMode.SmoothTransformation
    else:
        return Qt.SmoothTransformation


def _get_aspect_ratio_mode():
    """获取合适的宽高比模式枚举值"""
    if PYQT_VERSION == 6:
        return Qt.AspectRatioMode.KeepAspectRatio
    else:
        return Qt.KeepAspectRatio


class ZoomableGraphicsView(QGraphicsView):
    """可缩放图形视图组件"""

    zoom_changed = pyqtSignal(float)  # 缩放变化信号

    def __init__(self, scene: QGraphicsScene = None, parent: QWidget = None):
        super().__init__(scene, parent)
        self._logger = logging.getLogger("ZoomableGraphicsView")

        if scene is None:
            scene = QGraphicsScene()
        self.setScene(scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )  # 添加平滑像素变换
        self.setBackgroundBrush(QBrush(QColor(20, 20, 20)))
        self.setResizeAnchor(_get_resize_anchor())
        self.setTransformationAnchor(_get_transformation_anchor())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._zoom = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 10.0
        self._zoom_factor = 1.1

        self._pixmap_item = None
        self._original_pixmap = None  # 保存原始图像

        self._logger.info("[ZoomableGraphicsView] 初始化完成")

    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放图像"""
        delta = event.angleDelta().y()
        if delta == 0:
            return

        zoom_factor = (
            self._zoom_factor if delta > 0 else 1.0 / self._zoom_factor
        )
        self.set_zoom(self._zoom * zoom_factor)

    def set_zoom(self, zoom: float):
        """设置缩放比例"""
        new_zoom = max(self._zoom_min, min(self._zoom_max, zoom))

        if abs(new_zoom - self._zoom) > 0.001:
            self._zoom = new_zoom

            # 重置变换并应用新的缩放，确保基于原始图像缩放
            self.resetTransform()
            self.scale(self._zoom, self._zoom)

            self.zoom_changed.emit(self._zoom)
            self._logger.debug(
                f"[ZoomableGraphicsView] 缩放比例: {self._zoom:.2f}"
            )

    def get_zoom(self) -> float:
        """获取当前缩放比例"""
        return self._zoom

    def zoom_in(self):
        """放大"""
        self.set_zoom(self._zoom * self._zoom_factor)

    def zoom_out(self):
        """缩小"""
        self.set_zoom(self._zoom / self._zoom_factor)

    def reset_zoom(self):
        """重置缩放"""
        if self._zoom != 1.0:
            self.resetTransform()
            self._zoom = 1.0
            self.zoom_changed.emit(self._zoom)

    def update_zoom_from_transform(self):
        """从当前变换矩阵更新缩放值"""
        transform = self.transform()
        self._zoom = transform.m11()  # 假设均匀缩放
        self.zoom_changed.emit(self._zoom)
        self._logger.debug(
            f"[ZoomableGraphicsView] 从变换更新缩放: {self._zoom:.2f}"
        )

    def set_image_pixmap(self, pixmap: QPixmap):
        """设置图像（QPixmap格式）"""
        # 显式删除旧的pixmap_item - QGraphicsItem使用removeItem
        if self._pixmap_item:
            self.scene().removeItem(self._pixmap_item)
            self._pixmap_item = None

        if pixmap.isNull():
            self._logger.warning("[ZoomableGraphicsView] 无效的QPixmap")
            return

        # 保存原始图像
        self._original_pixmap = pixmap

        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._pixmap_item.setTransformationMode(_get_smooth_transformation())
        self.scene().addItem(self._pixmap_item)

        rect = self.scene().sceneRect()
        self._pixmap_item.setPos(
            rect.center() - self._pixmap_item.boundingRect().center()
        )

        # 重置缩放
        self.reset_zoom()

        self._logger.debug(
            f"[ZoomableGraphicsView] 设置图像: {pixmap.width()}x{pixmap.height()}"
        )

    def set_image_qimage(self, qimage: QImage):
        """设置图像（QImage格式）"""
        pixmap = QPixmap.fromImage(qimage)
        self.set_image_pixmap(pixmap)

    def set_zoom_range(self, min_zoom: float, max_zoom: float):
        """设置缩放范围"""
        self._zoom_min = max(0.01, min_zoom)
        self._zoom_max = max(self._zoom_min, max_zoom)

        if self._zoom < self._zoom_min:
            self.set_zoom(self._zoom_min)
        elif self._zoom > self._zoom_max:
            self.set_zoom(self._zoom_max)

    def set_zoom_factor(self, factor: float):
        """设置缩放因子（每次缩放的比例）"""
        self._zoom_factor = max(1.01, factor)

    def fit_to_window(self):
        """自适应窗口大小"""
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, _get_aspect_ratio_mode())
            self._zoom = 1.0
            self.zoom_changed.emit(self._zoom)


class ZoomableFrameMixin:
    """可缩放帧混入类

    为QFrame子类添加缩放和平移功能。
    适用于需要自定义绘制的场景。

    Usage:
        class MyCanvas(ZoomableFrameMixin, QFrame):
            def __init__(self, parent=None):
                super().__init__(parent)
                self._init_zoomable()
                self._image = None
                self._scale = 1.0
                self._base_scale = 1.0  # 基础缩放（适应窗口）

    """

    def _init_zoomable(self):
        """初始化缩放功能（子类应在__init__中调用）"""
        self._zoom = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 10.0
        self._zoom_factor = 1.1
        self._base_scale = 1.0
        self._image = None
        self._original_image = None  # 保存原始图像

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def _calculate_base_scale(self, canvas_size, img_size):
        """计算基础缩放比例（适应窗口）"""
        if img_size.width() == 0:
            return 1.0
        width_ratio = canvas_size.width() / img_size.width()
        height_ratio = canvas_size.height() / img_size.height()
        return min(width_ratio, height_ratio) * 0.95

    def _get_total_scale(self) -> float:
        """获取总缩放比例"""
        return self._base_scale * self._zoom

    def _handle_wheel_zoom(self, event) -> bool:
        """处理滚轮缩放事件

        Returns:
            True: 事件已处理
            False: 未处理（可能没有图像）
        """
        if self._image is None:
            return False

        delta = event.angleDelta().y()
        if delta == 0:
            return True

        zoom_factor = (
            self._zoom_factor if delta > 0 else 1.0 / self._zoom_factor
        )
        new_zoom = self._zoom * zoom_factor
        new_zoom = max(self._zoom_min, min(self._zoom_max, new_zoom))

        if abs(new_zoom - self._zoom) > 0.001:
            self._zoom = new_zoom
            self.update()
            self._emit_zoom_changed()

        return True

    def _emit_zoom_changed(self):
        """发射缩放变化信号"""
        if hasattr(self, "zoom_changed"):
            self.zoom_changed.emit(self._zoom)

    def set_zoom(self, zoom: float):
        """设置缩放比例"""
        new_zoom = max(self._zoom_min, min(self._zoom_max, zoom))
        if abs(new_zoom - self._zoom) > 0.001:
            self._zoom = new_zoom
            self.update()
            self._emit_zoom_changed()

    def get_zoom(self) -> float:
        """获取当前缩放比例"""
        return self._zoom

    def zoom_in(self):
        """放大"""
        self.set_zoom(self._zoom * self._zoom_factor)

    def zoom_out(self):
        """缩小"""
        self.set_zoom(self._zoom / self._zoom_factor)

    def reset_zoom(self):
        """重置缩放"""
        if self._zoom != 1.0:
            self._zoom = 1.0
            self.update()
            self._emit_zoom_changed()

    def set_image(self, image):
        """设置图像（子类应重写此方法）"""
        # 保存原始图像
        self._original_image = image
        self._image = image
        self._calculate_scale()
        # 重置缩放
        self.reset_zoom()
        self.update()

    def _calculate_scale(self):
        """计算缩放比例（子类可重写）"""
        pass

    def set_zoom_range(self, min_zoom: float, max_zoom: float):
        """设置缩放范围"""
        self._zoom_min = max(0.01, min_zoom)
        self._zoom_max = max(self._zoom_min, max_zoom)

        if self._zoom < self._zoom_min:
            self.set_zoom(self._zoom_min)
        elif self._zoom > self._zoom_max:
            self.set_zoom(self._zoom_max)

    def set_zoom_factor(self, factor: float):
        """设置缩放因子"""
        self._zoom_factor = max(1.01, factor)
