#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试缩放优化

验证图像缩放时是否还会出现越来越模糊的问题

Author: Vision System Team
Date: 2026-01-27
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtGui import QImage, QPixmap
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtGui import QImage, QPixmap
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT_VERSION = 5

from core.zoomable_image import ZoomableGraphicsView


class TestZoomWindow(QMainWindow):
    """
    测试缩放窗口
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试缩放优化")
        self.setGeometry(100, 100, 800, 600)

        # 创建主窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)

        # 创建可缩放图像视图
        self.zoom_view = ZoomableGraphicsView()
        layout.addWidget(self.zoom_view)

        # 创建按钮
        reset_button = QPushButton("重置缩放")
        reset_button.clicked.connect(self.zoom_view.reset_zoom)
        layout.addWidget(reset_button)

        # 加载测试图像
        self.load_test_image()

    def load_test_image(self):
        """
        加载测试图像
        """
        # 尝试加载测试图像
        test_image_path = "test_image.jpg"

        if os.path.exists(test_image_path):
            pixmap = QPixmap(test_image_path)
            if not pixmap.isNull():
                self.zoom_view.set_image_pixmap(pixmap)
                print(f"加载测试图像: {test_image_path}")
                return

        # 如果没有测试图像，创建一个简单的测试图像
        print("创建测试图像...")

        # 创建一个带有文字和图形的测试图像
        if PYQT_VERSION == 6:
            from PyQt6.QtCore import QSize
            from PyQt6.QtGui import QColor, QFont, QPainter
        else:
            from PyQt5.QtCore import QSize
            from PyQt5.QtGui import QColor, QFont, QPainter

        # 创建QImage
        image = QImage(QSize(640, 480), QImage.Format.Format_RGB32)
        image.fill(QColor(255, 255, 255))

        # 绘制内容
        painter = QPainter(image)
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 20))
        painter.drawText(100, 100, "测试缩放优化")
        painter.drawText(100, 140, "请使用鼠标滚轮缩放图像")
        painter.drawText(100, 180, "检查图像是否会越来越模糊")

        # 绘制一些几何图形
        painter.setPen(QColor(255, 0, 0))
        painter.drawRect(100, 200, 200, 100)

        painter.setPen(QColor(0, 255, 0))
        painter.drawEllipse(400, 200, 150, 150)

        painter.setPen(QColor(0, 0, 255))
        painter.drawLine(100, 350, 500, 350)

        painter.end()

        # 转换为QPixmap并设置
        pixmap = QPixmap.fromImage(image)
        self.zoom_view.set_image_pixmap(pixmap)

        # 保存测试图像
        image.save(test_image_path)
        print(f"保存测试图像到: {test_image_path}")


def main():
    """
    主函数
    """
    app = QApplication(sys.argv)
    window = TestZoomWindow()
    window.show()
    print("测试窗口已打开，请使用鼠标滚轮缩放图像，检查是否会越来越模糊")
    print("如果图像保持清晰，说明缩放优化成功")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
