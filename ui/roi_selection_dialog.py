#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI选择对话框

提供完整的ROI编辑功能：
- 绘制ROI（矩形、直线、圆）
- 拖拽ROI整体移动位置
- 拖拽ROI边界调整大小
- 拖拽ROI角点调整形状
- 键盘微调（方向键）
- Ctrl+Z撤销编辑

Author: Vision System Team
Date: 2025-01-13
"""

import logging
from typing import Any, Dict, Optional

import cv2
import numpy as np

from core.zoomable_image import ZoomableFrameMixin

try:
    from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
    from PyQt6.QtGui import (
        QColor,
        QCursor,
        QFont,
        QImage,
        QPainter,
        QPen,
        QPixmap,
    )
    from PyQt6.QtWidgets import (
        QButtonGroup,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QRadioButton,
        QSizePolicy,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
    from PyQt5.QtGui import (
        QColor,
        QCursor,
        QFont,
        QImage,
        QPainter,
        QPen,
        QPixmap,
    )
    from PyQt5.QtWidgets import (
        QButtonGroup,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QRadioButton,
        QSizePolicy,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 5


class ROIEditorCanvas(ZoomableFrameMixin, QFrame):
    """图像画布组件，支持显示图像和完整的ROI编辑功能"""

    roi_changed = pyqtSignal(dict)  # ROI变更信号（实时）
    roi_edited = pyqtSignal(dict)  # ROI编辑完成信号（松开鼠标/键盘）
    zoom_changed = pyqtSignal(float)  # 缩放变化信号（暴露给外部）

    DRAG_NONE = 0
    DRAG_MOVE = 1
    DRAG_RESIZE_LT = 2
    DRAG_RESIZE_RT = 3
    DRAG_RESIZE_LB = 4
    DRAG_RESIZE_RB = 5
    DRAG_RESIZE_L = 6
    DRAG_RESIZE_R = 7
    DRAG_RESIZE_T = 8
    DRAG_RESIZE_B = 9

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("ROIEditorCanvas")

        self.setStyleSheet(
            "border: 1px solid #CCCCCC; background-color: #333333;"
        )
        self.setMinimumSize(400, 300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._init_zoomable()  # 初始化缩放功能

        self._roi_type = "rect"
        self._roi_data = {}
        self._original_roi = {}

        self._is_drawing = False
        self._is_editing = False
        self._is_draw_mode = True  # True=绘制ROI模式, False=拖拽移动模式
        self._is_panning = False  # 拖拽移动状态
        self._pan_start = None  # 拖拽起始位置
        self._pan_offset_start = None  # 拖拽起始偏移
        self._start_point = None
        self._current_point = None

        self._drag_mode = self.DRAG_NONE
        self._drag_start_pos = None
        self._drag_start_roi = None

        self._roi_color = QColor(0, 255, 0)
        self._roi_width = 1
        self._handle_size = 5

        self._keyboard_step = 1

        # 图像偏移量（用于拖拽移动）
        self._offset_x = 0.0
        self._offset_y = 0.0

    def set_image(self, image):
        """设置显示的图像"""
        if image is None:
            self._image = None
            self.update()
            return

        if isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self._image = QImage(
                    image.data,
                    image.shape[1],
                    image.shape[0],
                    image.shape[1] * 3,
                    QImage.Format.Format_RGB888,
                )
            else:
                self._image = QImage(
                    image.data,
                    image.shape[1],
                    image.shape[0],
                    image.shape[1],
                    QImage.Format.Format_Grayscale8,
                )
        elif isinstance(image, QImage):
            self._image = image

        self._calculate_scale()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._calculate_scale()
        self.update()

    def set_roi_type(self, roi_type: str):
        """设置ROI类型"""
        self._roi_type = roi_type
        self._roi_data = {}
        self.update()

    def set_draw_mode(self, is_draw_mode: bool):
        """设置绘制模式
        
        Args:
            is_draw_mode: True=绘制ROI模式, False=拖拽移动模式
        """
        self._is_draw_mode = is_draw_mode
        if is_draw_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def set_roi_data(self, roi_data: dict):
        """设置ROI数据"""
        self._roi_data = roi_data.copy()
        self._original_roi = roi_data.copy()
        self._validate_roi_data()
        self.update()
        self.roi_changed.emit(self._roi_data)

    def _validate_roi_data(self):
        """验证ROI数据是否在图像范围内"""
        if not self._roi_data or not self._image:
            return

        img_width = self._image.width()
        img_height = self._image.height()

        if "x" in self._roi_data and "y" in self._roi_data:
            self._roi_data["x"] = max(
                0, min(self._roi_data["x"], img_width - 1)
            )
            self._roi_data["y"] = max(
                0, min(self._roi_data["y"], img_height - 1)
            )

        if "width" in self._roi_data:
            self._roi_data["width"] = max(
                1, min(self._roi_data["width"], img_width)
            )

        if "height" in self._roi_data:
            self._roi_data["height"] = max(
                1, min(self._roi_data["height"], img_height)
            )

        if "x1" in self._roi_data:
            self._roi_data["x1"] = max(
                0, min(self._roi_data["x1"], img_width - 1)
            )
        if "y1" in self._roi_data:
            self._roi_data["y1"] = max(
                0, min(self._roi_data["y1"], img_height - 1)
            )

        if "x2" in self._roi_data:
            self._roi_data["x2"] = max(
                0, min(self._roi_data["x2"], img_width - 1)
            )
        if "y2" in self._roi_data:
            self._roi_data["y2"] = max(
                0, min(self._roi_data["y2"], img_height - 1)
            )

        if "cx" in self._roi_data:
            self._roi_data["cx"] = max(
                0, min(self._roi_data["cx"], img_width - 1)
            )
        if "cy" in self._roi_data:
            self._roi_data["cy"] = max(
                0, min(self._roi_data["cy"], img_height - 1)
            )

        if "radius" in self._roi_data:
            self._roi_data["radius"] = max(
                1,
                min(self._roi_data["radius"], min(img_width, img_height) // 2),
            )

    def get_roi_data(self) -> dict:
        """获取ROI数据"""
        return self._roi_data.copy()

    def clear_roi(self):
        """清除ROI"""
        self._roi_data = {}
        self._original_roi = {}
        self.update()
        self.roi_changed.emit(self._roi_data)

    def undo_roi(self):
        """撤销ROI编辑"""
        if self._original_roi:
            self._roi_data = self._original_roi.copy()
            self.update()
            self.roi_changed.emit(self._roi_data)

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(50, 50, 50))

        if self._image is not None:
            x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
            y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y

            scaled_image = self._image.scaled(
                int(self._image.width() * self._scale),
                int(self._image.height() * self._scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            painter.drawImage(int(x), int(y), scaled_image)

            self._draw_roi(painter, x, y)

        if self._current_point and self._image and self._is_drawing:
            x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
            y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y
            img_width = self._image.width() * self._scale
            img_height = self._image.height() * self._scale

            if (
                x <= self._current_point.x() <= x + img_width
                and y <= self._current_point.y() <= y + img_height
            ):

                # 绘制十字线
                pen = QPen(QColor(255, 255, 255, 150), 1)
                painter.setPen(pen)
                px = int(self._current_point.x())
                py = int(self._current_point.y())
                painter.drawLine(px, int(y), px, int(y + img_height))
                painter.drawLine(int(x), py, int(x + img_width), py)

                # 实时显示绘制中的ROI矩形
                self._draw_preview_rect(painter, x, y)

    def _draw_preview_rect(self, painter: QPainter, offset_x: float, offset_y: float):
        """绘制预览矩形（绘制过程中实时显示）"""
        if not self._start_point or not self._current_point:
            return

        # 计算图像区域
        img_width = self._image.width() * self._scale
        img_height = self._image.height() * self._scale

        # 获取鼠标在图像上的坐标
        start_x = self._start_point.x()
        start_y = self._start_point.y()
        current_x = self._current_point.x()
        current_y = self._current_point.y()

        # 限制在图像范围内
        start_x = max(offset_x, min(start_x, offset_x + img_width))
        start_y = max(offset_y, min(start_y, offset_y + img_height))
        current_x = max(offset_x, min(current_x, offset_x + img_width))
        current_y = max(offset_y, min(current_y, offset_y + img_height))

        # 计算矩形
        left = min(start_x, current_x)
        top = min(start_y, current_y)
        width = abs(current_x - start_x)
        height = abs(current_y - start_y)

        # 转换为图像坐标
        img_left = int((left - offset_x) / self._scale)
        img_top = int((top - offset_y) / self._scale)
        img_width_px = int(width / self._scale)
        img_height_px = int(height / self._scale)

        # 绘制半透明填充
        fill_color = QColor(0, 255, 0, 50)
        painter.fillRect(int(left), int(top), int(width), int(height), fill_color)

        # 绘制边框
        pen = QPen(QColor(0, 255, 0, 200), 2)
        painter.setPen(pen)
        painter.drawRect(int(left), int(top), int(width), int(height))

        # 显示尺寸信息
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        size_text = f"{img_width_px} x {img_height_px}"
        painter.drawText(int(left), int(top) - 5, f"ROI: ({img_left}, {img_top}) {size_text}")

    def _draw_roi(self, painter: QPainter, offset_x: float, offset_y: float):
        """绘制ROI"""
        if not self._roi_data:
            return

        roi_type = self._roi_data.get("type", "rect")

        if roi_type == "rect" and all(
            k in self._roi_data for k in ["x", "y", "width", "height"]
        ):
            self._draw_rect_roi(painter, offset_x, offset_y)
        elif roi_type == "line" and all(
            k in self._roi_data for k in ["x1", "y1", "x2", "y2"]
        ):
            self._draw_line_roi(painter, offset_x, offset_y)
        elif roi_type == "circle" and all(
            k in self._roi_data for k in ["cx", "cy", "radius"]
        ):
            self._draw_circle_roi(painter, offset_x, offset_y)

    def _draw_rect_roi(
        self, painter: QPainter, offset_x: float, offset_y: float
    ):
        """绘制矩形ROI及控制点"""

        def to_canvas(x, y):
            return int(x * self._scale + offset_x), int(
                y * self._scale + offset_y
            )

        x1, y1 = to_canvas(self._roi_data["x"], self._roi_data["y"])
        x2, y2 = to_canvas(
            self._roi_data["x"] + self._roi_data["width"],
            self._roi_data["y"] + self._roi_data["height"],
        )

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        pen = QPen(self._roi_color, self._roi_width)
        painter.setPen(pen)
        painter.drawRect(left, top, width, height)

        self._draw_handles(painter, left, top, width, height)

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            left,
            top - 5,
            f"ROI: ({self._roi_data['x']}, {self._roi_data['y']}) {width}x{height}",
        )

    def _draw_line_roi(
        self, painter: QPainter, offset_x: float, offset_y: float
    ):
        """绘制直线ROI"""

        def to_canvas(x, y):
            return int(x * self._scale + offset_x), int(
                y * self._scale + offset_y
            )

        x1, y1 = to_canvas(self._roi_data["x1"], self._roi_data["y1"])
        x2, y2 = to_canvas(self._roi_data["x2"], self._roi_data["y2"])

        pen = QPen(self._roi_color, self._roi_width)
        painter.setPen(pen)
        painter.drawLine(x1, y1, x2, y2)

        painter.setBrush(QColor(0, 255, 0))
        painter.drawEllipse(
            QPoint(x1, y1), self._handle_size, self._handle_size
        )
        painter.drawEllipse(
            QPoint(x2, y2), self._handle_size, self._handle_size
        )

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            x1,
            y1 - 5,
            f"直线: ({self._roi_data['x1']}, {self._roi_data['y1']})",
        )

    def _draw_circle_roi(
        self, painter: QPainter, offset_x: float, offset_y: float
    ):
        """绘制圆形ROI"""

        def to_canvas(x, y):
            return int(x * self._scale + offset_x), int(
                y * self._scale + offset_y
            )

        cx, cy = to_canvas(self._roi_data["cx"], self._roi_data["cy"])
        radius = int(self._roi_data["radius"] * self._scale)

        pen = QPen(self._roi_color, self._roi_width)
        painter.setPen(pen)
        painter.drawEllipse(QPoint(cx, cy), radius, radius)

        painter.setBrush(QColor(0, 255, 0))
        painter.drawEllipse(
            QPoint(cx, cy), self._handle_size, self._handle_size
        )

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            cx + radius + 5, cy, f"圆: r={self._roi_data['radius']}"
        )

    def _draw_handles(
        self, painter: QPainter, x: int, y: int, width: int, height: int
    ):
        """绘制控制点"""
        painter.setBrush(QColor(0, 255, 0))

        handles = [
            (x, y),
            (x + width, y),
            (x, y + height),
            (x + width, y + height),
            (x + width // 2, y),
            (x + width // 2, y + height),
            (x, y + height // 2),
            (x + width, y + height // 2),
        ]

        for hx, hy in handles:
            painter.drawEllipse(
                QPoint(hx, hy), self._handle_size, self._handle_size
            )

    def _get_handle_at_position(
        self, pos: QPoint, offset_x: float, offset_y: float
    ) -> int:
        """获取指定位置的控制点"""
        if self._roi_type != "rect" or not self._roi_data:
            return self.DRAG_NONE

        def to_canvas(x, y):
            return int(x * self._scale + offset_x), int(
                y * self._scale + offset_y
            )

        x1, y1 = to_canvas(self._roi_data["x"], self._roi_data["y"])
        x2, y2 = to_canvas(
            self._roi_data["x"] + self._roi_data["width"],
            self._roi_data["y"] + self._roi_data["height"],
        )

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        handle_threshold = self._handle_size * 2

        px, py = pos.x(), pos.y()

        if (
            abs(px - left) < handle_threshold
            and abs(py - top) < handle_threshold
        ):
            return self.DRAG_RESIZE_LT
        elif (
            abs(px - (left + width)) < handle_threshold
            and abs(py - top) < handle_threshold
        ):
            return self.DRAG_RESIZE_RT
        elif (
            abs(px - left) < handle_threshold
            and abs(py - (top + height)) < handle_threshold
        ):
            return self.DRAG_RESIZE_LB
        elif (
            abs(px - (left + width)) < handle_threshold
            and abs(py - (top + height)) < handle_threshold
        ):
            return self.DRAG_RESIZE_RB
        elif abs(px - left) < handle_threshold:
            return self.DRAG_RESIZE_L
        elif abs(px - (left + width)) < handle_threshold:
            return self.DRAG_RESIZE_R
        elif abs(py - top) < handle_threshold:
            return self.DRAG_RESIZE_T
        elif abs(py - (top + height)) < handle_threshold:
            return self.DRAG_RESIZE_B
        elif left <= px <= left + width and top <= py <= top + height:
            return self.DRAG_MOVE

        return self.DRAG_NONE

    def _update_cursor(self, pos: QPoint, offset_x: float, offset_y: float):
        """根据位置更新鼠标光标"""
        if self._roi_type != "rect" or not self._roi_data:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return

        handle = self._get_handle_at_position(pos, offset_x, offset_y)

        cursors = {
            self.DRAG_MOVE: Qt.CursorShape.SizeAllCursor,
            self.DRAG_RESIZE_LT: Qt.CursorShape.SizeFDiagCursor,
            self.DRAG_RESIZE_RB: Qt.CursorShape.SizeFDiagCursor,
            self.DRAG_RESIZE_RT: Qt.CursorShape.SizeBDiagCursor,
            self.DRAG_RESIZE_LB: Qt.CursorShape.SizeBDiagCursor,
            self.DRAG_RESIZE_L: Qt.CursorShape.SizeHorCursor,
            self.DRAG_RESIZE_R: Qt.CursorShape.SizeHorCursor,
            self.DRAG_RESIZE_T: Qt.CursorShape.SizeVerCursor,
            self.DRAG_RESIZE_B: Qt.CursorShape.SizeVerCursor,
        }

        self.setCursor(
            cursors.get(handle, QCursor(Qt.CursorShape.ArrowCursor))
        )

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() != Qt.MouseButton.LeftButton or not self._image:
            return

        # 非绘制模式下，执行拖拽移动
        if not self._is_draw_mode:
            self._is_panning = True
            self._pan_start = event.pos()
            self._pan_offset_start = (self._offset_x, self._offset_y)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
        y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y

        if not (
            x <= event.pos().x() <= x + self._image.width() * self._scale
            and y <= event.pos().y() <= y + self._image.height() * self._scale
        ):
            return

        if self._roi_data and self._roi_type == "rect":
            handle = self._get_handle_at_position(event.pos(), x, y)
            if handle != self.DRAG_NONE:
                self._is_editing = True
                self._drag_mode = handle
                self._drag_start_pos = event.pos()
                self._drag_start_roi = self._roi_data.copy()
                return

        self._is_drawing = True
        self._start_point = event.pos()
        self._current_point = event.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self._image:
            return

        x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
        y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y

        # 拖拽移动模式
        if self._is_panning and self._pan_start:
            dx = event.pos().x() - self._pan_start.x()
            dy = event.pos().y() - self._pan_start.y()
            self._offset_x = self._pan_offset_start[0] + dx
            self._offset_y = self._pan_offset_start[1] + dy
            self.update()
            return

        if self._is_editing and self._drag_start_roi:
            self._apply_resize(event.pos(), x, y)
            self._current_point = event.pos()
            self.update()
            return

        if self._is_drawing:
            self._current_point = event.pos()
            self.update()
        else:
            self._update_cursor(event.pos(), x, y)

    def _apply_resize(self, pos: QPoint, offset_x: float, offset_y: float):
        """应用拖拽调整大小"""
        dx = int((pos.x() - self._drag_start_pos.x()) / self._scale)
        dy = int((pos.y() - self._drag_start_pos.y()) / self._scale)

        roi = self._drag_start_roi.copy()

        if self._drag_mode == self.DRAG_MOVE:
            roi["x"] = max(0, roi["x"] + dx)
            roi["y"] = max(0, roi["y"] + dy)

        elif self._drag_mode == self.DRAG_RESIZE_LT:
            roi["x"] = max(0, min(roi["x"] + dx, roi["x"] + roi["width"] - 1))
            roi["y"] = max(0, min(roi["y"] + dy, roi["y"] + roi["height"] - 1))
            roi["width"] = max(1, roi["width"] - dx)
            roi["height"] = max(1, roi["height"] - dy)

        elif self._drag_mode == self.DRAG_RESIZE_RB:
            roi["width"] = max(1, roi["width"] + dx)
            roi["height"] = max(1, roi["height"] + dy)

        elif self._drag_mode == self.DRAG_RESIZE_RT:
            roi["y"] = max(0, min(roi["y"] + dy, roi["y"] + roi["height"] - 1))
            roi["width"] = max(1, roi["width"] + dx)
            roi["height"] = max(1, roi["height"] - dy)

        elif self._drag_mode == self.DRAG_RESIZE_LB:
            roi["x"] = max(0, min(roi["x"] + dx, roi["x"] + roi["width"] - 1))
            roi["width"] = max(1, roi["width"] - dx)
            roi["height"] = max(1, roi["height"] + dy)

        elif self._drag_mode == self.DRAG_RESIZE_L:
            roi["x"] = max(0, min(roi["x"] + dx, roi["x"] + roi["width"] - 1))
            roi["width"] = max(1, roi["width"] - dx)

        elif self._drag_mode == self.DRAG_RESIZE_R:
            roi["width"] = max(1, roi["width"] + dx)

        elif self._drag_mode == self.DRAG_RESIZE_T:
            roi["y"] = max(0, min(roi["y"] + dy, roi["y"] + roi["height"] - 1))
            roi["height"] = max(1, roi["height"] - dy)

        elif self._drag_mode == self.DRAG_RESIZE_B:
            roi["height"] = max(1, roi["height"] + dy)

        self._roi_data = roi
        self.roi_changed.emit(self._roi_data)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        # 拖拽移动模式释放
        if self._is_panning:
            self._is_panning = False
            self._pan_start = None
            self._pan_offset_start = None
            # 恢复光标
            if not self._is_draw_mode:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            return

        if self._is_editing:
            self._is_editing = False
            self._drag_mode = self.DRAG_NONE
            self._drag_start_pos = None
            self._drag_start_roi = None
            self.roi_edited.emit(self._roi_data)
            return

        if not self._is_drawing or not self._start_point:
            return

        x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
        y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y

        img_x = int((event.pos().x() - x) / self._scale)
        img_y = int((event.pos().y() - y) / self._scale)
        start_img_x = int((self._start_point.x() - x) / self._scale)
        start_img_y = int((self._start_point.y() - y) / self._scale)

        img_x = max(0, min(img_x, self._image.width() - 1))
        img_y = max(0, min(img_y, self._image.height() - 1))
        start_img_x = max(0, min(start_img_x, self._image.width() - 1))
        start_img_y = max(0, min(start_img_y, self._image.height() - 1))

        if self._roi_type == "rect":
            self._roi_data = {
                "type": "rect",
                "x": min(start_img_x, img_x),
                "y": min(start_img_y, img_y),
                "width": abs(img_x - start_img_x) + 1,
                "height": abs(img_y - start_img_y) + 1,
            }
        elif self._roi_type == "line":
            self._roi_data = {
                "type": "line",
                "x1": start_img_x,
                "y1": start_img_y,
                "x2": img_x,
                "y2": img_y,
            }
        elif self._roi_type == "circle":
            center_x = (start_img_x + img_x) // 2
            center_y = (start_img_y + img_y) // 2
            radius = int(
                np.sqrt(
                    (img_x - start_img_x) ** 2 + (img_y - start_img_y) ** 2
                )
            )
            self._roi_data = {
                "type": "circle",
                "cx": center_x,
                "cy": center_y,
                "radius": max(1, radius),
            }

        self._is_drawing = False
        self._start_point = None
        self._current_point = None
        self.update()
        self.roi_changed.emit(self._roi_data)
        self.roi_edited.emit(self._roi_data)

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if not self._roi_data or self._roi_type != "rect":
            super().keyPressEvent(event)
            return

        dx, dy = 0, 0

        if event.key() == Qt.Key.Key_Left:
            dx = -self._keyboard_step
        elif event.key() == Qt.Key.Key_Right:
            dx = self._keyboard_step
        elif event.key() == Qt.Key.Key_Up:
            dy = -self._keyboard_step
        elif event.key() == Qt.Key.Key_Down:
            dy = self._keyboard_step
        elif (
            event.key() == Qt.Key.Key_Z
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.undo_roi()
            return
        else:
            super().keyPressEvent(event)
            return

        if dx != 0 or dy != 0:
            if "x" in self._roi_data:
                self._roi_data["x"] = max(0, self._roi_data["x"] + dx)
            if "y" in self._roi_data:
                self._roi_data["y"] = max(0, self._roi_data["y"] + dy)

            self.update()
            self.roi_changed.emit(self._roi_data)
            self.roi_edited.emit(self._roi_data)

    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放图像"""
        self._calculate_scale()  # 先更新_scale
        self._handle_wheel_zoom(event)  # 再处理滚轮缩放（会调用update）

    def _calculate_scale(self):
        """计算缩放比例（包含基础缩放和用户缩放）"""
        if self._image is None:
            return

        canvas_size = self.size()
        img_size = QSize(self._image.width(), self._image.height())

        if img_size.width() == 0:
            return

        self._base_scale = self._calculate_base_scale(canvas_size, img_size)
        self._scale = self._base_scale * self._zoom


class ROISelectionDialog(QDialog):
    """ROI选择对话框（支持绘制和编辑）"""

    roi_edited = pyqtSignal(dict)  # ROI编辑完成信号（暴露给外部使用）

    def __init__(
        self, parent=None, title: str = "选择ROI区域", roi_type: str = "rect"
    ):
        super().__init__(parent)
        self._logger = logging.getLogger("ROISelectionDialog")

        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)

        self._roi_type = roi_type
        self._roi_data = {}

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 工具栏 - 模式切换
        toolbar_layout = QHBoxLayout()
        
        # 模式切换按钮组
        self._mode_group = QButtonGroup(self)
        
        self._btn_draw_mode = QRadioButton("绘制ROI模式")
        self._btn_draw_mode.setChecked(True)
        self._btn_draw_mode.setToolTip("点击后使用鼠标左键绘制ROI区域")
        self._mode_group.addButton(self._btn_draw_mode)
        toolbar_layout.addWidget(self._btn_draw_mode)
        
        self._btn_pan_mode = QRadioButton("拖拽移动模式")
        self._btn_pan_mode.setToolTip("点击后使用鼠标左键拖拽移动图像")
        self._mode_group.addButton(self._btn_pan_mode)
        toolbar_layout.addWidget(self._btn_pan_mode)
        
        toolbar_layout.addStretch()
        
        # 清除和撤销按钮
        self._btn_clear = QPushButton("清除ROI")
        toolbar_layout.addWidget(self._btn_clear)

        self._btn_undo = QPushButton("撤销编辑 (Ctrl+Z)")
        toolbar_layout.addWidget(self._btn_undo)
        
        layout.addLayout(toolbar_layout)

        # 画布
        self._canvas = ROIEditorCanvas(self)
        layout.addWidget(self._canvas)

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        self._btn_cancel = QPushButton("取消")
        button_layout.addWidget(self._btn_cancel)

        self._btn_confirm = QPushButton("确认")
        button_layout.addWidget(self._btn_confirm)

        layout.addLayout(button_layout)

        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("操作提示:"))
        info_layout.addWidget(
            QLabel(
                "先选择模式 | 绘制模式:拖拽绘制ROI | 移动模式:拖拽移动图像 | 拖拽边角调整大小 | 方向键微调 | Ctrl+Z撤销 | 滚轮缩放"
            )
        )
        info_layout.addStretch()

        self._zoom_label = QLabel("缩放: 100%")
        info_layout.addWidget(self._zoom_label)

        layout.addLayout(info_layout)

    def _connect_signals(self):
        """连接信号"""
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_undo.clicked.connect(self._on_undo)
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_confirm.clicked.connect(self.accept)

        # 模式切换
        self._btn_draw_mode.toggled.connect(self._on_mode_changed)
        self._btn_pan_mode.toggled.connect(self._on_mode_changed)

        self._canvas.roi_changed.connect(self._on_roi_changed)
        self._canvas.roi_edited.connect(self.roi_edited)  # 暴露给外部
        self._canvas.zoom_changed.connect(self._on_zoom_changed)  # 缩放变化

    def _on_mode_changed(self):
        """模式切换处理"""
        if self._btn_draw_mode.isChecked():
            self._canvas.set_draw_mode(True)
        else:
            self._canvas.set_draw_mode(False)

    def set_image(self, image):
        """设置显示的图像"""
        self._canvas.set_image(image)

    def set_roi_type(self, roi_type: str):
        """设置ROI类型"""
        self._roi_type = roi_type
        self._canvas.set_roi_type(roi_type)

    def set_roi_data(self, roi_data: dict):
        """设置ROI数据"""
        self._canvas.set_roi_data(roi_data)

    def get_roi_data(self) -> dict:
        """获取ROI数据"""
        return self._canvas.get_roi_data()

    def _on_roi_changed(self, roi_data: dict):
        """ROI变更回调"""
        self._roi_data = roi_data
        self._logger.info(f"ROI已更新: {roi_data}")

    def _on_clear(self):
        """清除ROI"""
        self._canvas.clear_roi()

    def _on_undo(self):
        """撤销编辑"""
        self._canvas.undo_roi()

    def _on_zoom_changed(self, zoom: float):
        """缩放变化回调"""
        self._zoom_label.setText(f"缩放: {int(zoom * 100)}%")


def show_roi_editor(
    parent,
    image,
    title: str = "选择ROI区域",
    roi_type: str = "rect",
    roi_data: dict = None,
) -> dict:
    """显示ROI编辑对话框

    Args:
        parent: 父窗口
        image: 图像数据
        title: 对话框标题
        roi_type: ROI类型 ("rect", "line", "circle")
        roi_data: 初始ROI数据（可选）

    Returns:
        dict: ROI数据，格式取决于roi_type，None表示用户取消
    """
    dialog = ROISelectionDialog(parent, title, roi_type)
    dialog.set_image(image)
    if roi_data:
        dialog.set_roi_data(roi_data)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_roi_data()
    return None
