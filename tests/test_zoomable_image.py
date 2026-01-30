#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZoomableImage组件测试用例

测试缩放图像组件的PyQt版本兼容性和功能正确性。

Run: python tests/test_zoomable_image.py
"""

import sys
import os
import logging
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestZoomableImage")

PYQT_VERSION = None

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QFrame,
        QVBoxLayout,
        QGraphicsView,
        QGraphicsScene,
        QGraphicsPixmapItem,
        QLabel,
        QPushButton,
        QHBoxLayout,
    )
    from PyQt6.QtGui import QPainter, QBrush, QColor, QPixmap, QImage
    from PyQt6.QtCore import Qt, QSize

    PYQT_VERSION = 6
    logger.info("[TEST] 使用 PyQt6")
except Exception as e:
    logger.info(f"[TEST] PyQt6导入失败，尝试PyQt5: {e}")
    try:
        from PyQt5.QtWidgets import (
            QApplication,
            QMainWindow,
            QWidget,
            QFrame,
            QVBoxLayout,
            QGraphicsView,
            QGraphicsScene,
            QGraphicsPixmapItem,
            QLabel,
            QPushButton,
            QHBoxLayout,
        )
        from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap, QImage
        from PyQt5.QtCore import Qt, QSize

        PYQT_VERSION = 5
        logger.info("[TEST] 使用 PyQt5")
    except Exception as e:
        logger.error(f"[TEST] PyQt5也导入失败: {e}")
        sys.exit(1)

from core.zoomable_image import (
    ZoomableGraphicsView,
    ZoomableFrameMixin,
    _get_resize_anchor,
    _get_transformation_anchor,
    _get_smooth_transformation,
    _get_aspect_ratio_mode,
)


class TestZoomableImage(unittest.TestCase):
    """测试ZoomableImage组件"""

    @classmethod
    def setUpClass(cls):
        """创建QApplication（所有测试只创建一次）"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_version_detection(self):
        """测试PyQt版本检测"""
        self.assertIn(PYQT_VERSION, [5, 6])
        logger.info(f"[TEST] PyQt版本: {PYQT_VERSION}")

    def test_enum_compat_functions(self):
        """测试枚举兼容函数"""
        resize_anchor = _get_resize_anchor()
        transformation_anchor = _get_transformation_anchor()
        smooth_transform = _get_smooth_transformation()
        aspect_ratio = _get_aspect_ratio_mode()

        self.assertIsNotNone(resize_anchor)
        self.assertIsNotNone(transformation_anchor)
        self.assertIsNotNone(smooth_transform)
        self.assertIsNotNone(aspect_ratio)

        logger.info(f"[TEST] ResizeAnchor: {resize_anchor}")
        logger.info(f"[TEST] TransformationAnchor: {transformation_anchor}")
        logger.info(f"[TEST] SmoothTransformation: {smooth_transform}")
        logger.info(f"[TEST] KeepAspectRatio: {aspect_ratio}")

    def test_zoomable_graphics_view_init(self):
        """测试ZoomableGraphicsView初始化"""
        scene = QGraphicsScene()
        view = ZoomableGraphicsView(scene)

        self.assertIsNotNone(view)
        self.assertEqual(view.get_zoom(), 1.0)

        logger.info("[TEST] ZoomableGraphicsView初始化成功")

    def test_zoomable_frame_mixin_init(self):
        """测试ZoomableFrameMixin初始化"""

        class TestCanvas(ZoomableFrameMixin, QFrame):
            def __init__(self, parent=None):
                super().__init__(parent)
                self._init_zoomable()

        canvas = TestCanvas()
        self.assertIsNotNone(canvas)
        self.assertEqual(canvas.get_zoom(), 1.0)

        logger.info("[TEST] ZoomableFrameMixin初始化成功")

    def test_zoom_range(self):
        """测试缩放范围设置"""
        scene = QGraphicsScene()
        view = ZoomableGraphicsView(scene)

        view.set_zoom_range(0.5, 5.0)

        self.assertEqual(view._zoom_min, 0.5)
        self.assertEqual(view._zoom_max, 5.0)

        logger.info("[TEST] 缩放范围设置成功")

    def test_zoom_in_out(self):
        """测试放大缩小功能"""
        scene = QGraphicsScene()
        view = ZoomableGraphicsView(scene)

        initial_zoom = view.get_zoom()

        view.zoom_in()
        self.assertGreater(view.get_zoom(), initial_zoom)

        view.zoom_out()
        self.assertEqual(view.get_zoom(), initial_zoom)

        logger.info("[TEST] 放大缩小功能正常")

    def test_reset_zoom(self):
        """测试重置缩放"""
        scene = QGraphicsScene()
        view = ZoomableGraphicsView(scene)

        view.zoom_in()
        view.zoom_in()
        self.assertNotEqual(view.get_zoom(), 1.0)

        view.reset_zoom()
        self.assertEqual(view.get_zoom(), 1.0)

        logger.info("[TEST] 重置缩放功能正常")


class ZoomableImageGUITestWindow(QMainWindow):
    """可视化测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ZoomableImage组件测试 - PyQt{PYQT_VERSION}")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setStyleSheet("border: 2px solid #3498db;")
        layout.addWidget(self.view)

        button_layout = QHBoxLayout()

        btn_zoom_in = QPushButton("放大")
        btn_zoom_in.clicked.connect(self.view.zoom_in)
        button_layout.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("缩小")
        btn_zoom_out.clicked.connect(self.view.zoom_out)
        button_layout.addWidget(btn_zoom_out)

        btn_reset = QPushButton("重置")
        btn_reset.clicked.connect(self.view.reset_zoom)
        button_layout.addWidget(btn_reset)

        self.zoom_label = QLabel("100%")
        button_layout.addWidget(self.zoom_label)

        layout.addLayout(button_layout)

        self.view.zoom_changed.connect(self._on_zoom_changed)

        self._create_test_image()

    def _create_test_image(self):
        """创建测试图像"""
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor(50, 50, 50))

        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 255, 0))
        painter.setBrush(QBrush(QColor(0, 100, 0)))
        painter.drawRect(100, 75, 200, 150)
        painter.drawText(150, 150, "测试图像")
        painter.end()

        self.view.set_image_pixmap(pixmap)

    def _on_zoom_changed(self, zoom):
        self.zoom_label.setText(f"{int(zoom * 100)}%")


def run_tests():
    """运行单元测试"""
    logger.info("=" * 50)
    logger.info("开始ZoomableImage组件测试")
    logger.info("=" * 50)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestZoomableImage)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    logger.info("=" * 50)
    if result.wasSuccessful():
        logger.info("所有测试通过!")
    else:
        logger.error(
            f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误"
        )
    logger.info("=" * 50)

    return result.wasSuccessful()


def run_gui_test():
    """运行GUI可视化测试"""
    logger.info("启动可视化测试窗口...")

    window = ZoomableImageGUITestWindow()
    window.show()

    return window


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ZoomableImage组件测试")
    parser.add_argument("--gui", action="store_true", help="启动GUI可视化测试")
    parser.add_argument("--test", action="store_true", help="运行单元测试")
    args = parser.parse_args()

    if args.gui:
        app = QApplication(sys.argv)
        window = run_gui_test()
        sys.exit(app.exec())
    elif args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        print("用法:")
        print("  python test_zoomable_image.py --test   # 运行单元测试")
        print("  python test_zoomable_image.py --gui    # 启动GUI可视化测试")
        print()
        print("默认运行单元测试...")
        success = run_tests()

        if success:
            print("\n启动GUI可视化测试...")
            app = QApplication(sys.argv)
            window = run_gui_test()
            sys.exit(app.exec())
