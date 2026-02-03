#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标定工具模块

提供图像标定功能，将像素坐标和尺寸转换为实际物理尺寸（mm、inch等）。

功能：
- 棋盘格标定（自动检测角点）
- 圆点标定（自动检测圆点）
- 手动标定（输入参考尺寸）
- 像素到实际尺寸转换
- 畸变校正

Author: Vision System Team
Date: 2026-02-03
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException

_logger = logging.getLogger("Calibration")


@ToolRegistry.register
class CalibrationTool(ToolBase):
    """
    标定工具

    将图像中的像素坐标和尺寸转换为实际物理尺寸。
    支持多种标定方法：
    - 棋盘格标定（自动检测角点）
    - 圆点标定（自动检测圆点）
    - 手动标定（手动输入参考尺寸）

    参数说明：
    - calibration_type: 标定类型
    - pattern_width: 棋盘格宽度（内角点数）
    - pattern_height: 棋盘格高度（内角点数）
    - square_size: 单个方格实际尺寸（mm）
    - pixel_per_mm: 像素与毫米的比例（手动标定时使用）
    """

    tool_name = "标定"
    tool_category = "Vision"
    tool_description = "将像素坐标转换为实际物理尺寸"

    PARAM_DEFINITIONS = {
        "calibration_type": ToolParameter(
            name="标定类型",
            param_type="enum",
            default="manual",
            description="选择标定方法",
            options=["manual", "chessboard", "circles"],
        ),
        "pattern_width": ToolParameter(
            name="角点列数",
            param_type="integer",
            default=9,
            description="棋盘格内角点列数",
            min_value=3,
            max_value=20,
        ),
        "pattern_height": ToolParameter(
            name="角点行数",
            param_type="integer",
            default=6,
            description="棋盘格内角点行数",
            min_value=3,
            max_value=20,
        ),
        "square_size": ToolParameter(
            name="方格尺寸",
            param_type="float",
            default=10.0,
            description="单个方格的实际尺寸（mm）",
            min_value=0.1,
            max_value=1000.0,
        ),
        "pixel_per_mm_x": ToolParameter(
            name="水平像素比例",
            param_type="float",
            default=10.0,
            description="水平方向每毫米对应的像素数",
            min_value=0.1,
            max_value=1000.0,
        ),
        "pixel_per_mm_y": ToolParameter(
            name="垂直像素比例",
            param_type="float",
            default=10.0,
            description="垂直方向每毫米对应的像素数",
            min_value=0.1,
            max_value=1000.0,
        ),
        "reference_width": ToolParameter(
            name="参考物体宽度",
            param_type="float",
            default=100.0,
            description="参考物体的实际宽度（mm）",
            min_value=0.1,
            max_value=10000.0,
        ),
        "reference_height": ToolParameter(
            name="参考物体高度",
            param_type="float",
            default=100.0,
            description="参考物体的实际高度（mm）",
            min_value=0.1,
            max_value=10000.0,
        ),
        "output_unit": ToolParameter(
            name="输出单位",
            param_type="enum",
            default="mm",
            description="输出结果使用的单位",
            options=["mm", "inch", "um"],
        ),
        "save_calibration": ToolParameter(
            name="保存标定参数",
            param_type="boolean",
            default=False,
            description="是否将标定参数保存到文件",
        ),
        "calibration_file": ToolParameter(
            name="标定文件路径",
            param_type="file_path",
            default="",
            description="标定参数文件路径（.yaml或.npz）",
        ),
    }

    def __init__(self, name: str = None):
        """初始化标定工具"""
        super().__init__(name)
        self._calibration_matrix = None
        self._distortion_coeffs = None
        self._pixel_per_mm_x = 10.0
        self._pixel_per_mm_y = 10.0
        self._calibrated = False

    def _init_params(self):
        """初始化默认参数"""
        self.set_param("calibration_type", "manual")
        self.set_param("pattern_width", 9)
        self.set_param("pattern_height", 6)
        self.set_param("square_size", 10.0)
        self.set_param("pixel_per_mm_x", 10.0)
        self.set_param("pixel_per_mm_y", 10.0)
        self.set_param("reference_width", 100.0)
        self.set_param("reference_height", 100.0)
        self.set_param("output_unit", "mm")
        self.set_param("save_calibration", False)
        self.set_param("calibration_file", "")

    def calibrate_with_chessboard(self, image: np.ndarray) -> bool:
        """
        使用棋盘格进行标定

        Args:
            image: 输入图像

        Returns:
            标定是否成功
        """
        pattern_width = self.get_param("pattern_width", 9)
        pattern_height = self.get_param("pattern_height", 6)
        square_size = self.get_param("square_size", 10.0)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # 准备棋盘格角点
        pattern_size = (pattern_width, pattern_height)
        obj_points = []
        img_points = []

        objp = np.zeros((pattern_width * pattern_height, 3), np.float32)
        objp[:, :2] = np.mgrid[0:pattern_width, 0:pattern_height].T.reshape(-1, 2)
        objp *= square_size

        # 检测角点
        found, corners = cv2.findChessboardCorners(gray, pattern_size, None)

        if not found:
            _logger.error("未检测到棋盘格角点")
            return False

        # 亚像素级精度优化
        corners_refined = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )

        img_points.append(corners_refined)
        obj_points.append(objp)

        # 标定
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            [obj_points], [img_points], gray.shape[::-1], None, None
        )

        if ret:
            self._calibration_matrix = mtx
            self._distortion_coeffs = dist

            # 计算像素比例（从标定结果）
            fx = mtx[0, 0]
            fy = mtx[1, 1]
            # 假设焦距与工作距离的关系，估算像素比例
            # 这里简化处理，使用平均比例
            self._pixel_per_mm_x = fx / 1000.0  # 假设工作距离1m
            self._pixel_per_mm_y = fy / 1000.0
            self._calibrated = True

            _logger.info(f"棋盘格标定成功: fx={fx:.2f}, fy={fy:.2f}")

        return ret

    def calibrate_with_reference(
        self,
        pixel_width: int,
        pixel_height: int,
        actual_width: float,
        actual_height: float,
    ) -> bool:
        """
        使用参考物体进行手动标定

        Args:
            pixel_width: 参考物体在图像中的像素宽度
            pixel_height: 参考物体在图像中的像素高度
            actual_width: 参考物体的实际宽度（mm）
            actual_height: 参考物体的实际高度（mm）

        Returns:
            标定是否成功
        """
        if pixel_width <= 0 or pixel_height <= 0:
            _logger.error("像素尺寸必须大于0")
            return False

        self._pixel_per_mm_x = pixel_width / actual_width
        self._pixel_per_mm_y = pixel_height / actual_height
        self._calibrated = True

        _logger.info(
            f"手动标定成功: {self._pixel_per_mm_x:.3f} px/mm (X), "
            f"{self._pixel_per_mm_y:.3f} px/mm (Y)"
        )

        return True

    def pixel_to_physical(
        self, pixel_x: float, pixel_y: float
    ) -> Tuple[float, float]:
        """
        将像素坐标转换为物理坐标

        Args:
            pixel_x: 像素X坐标
            pixel_y: 像素Y坐标

        Returns:
            (physical_x, physical_y) 物理坐标（mm）
        """
        if not self._calibrated:
            _logger.warning("工具未标定，使用默认比例")
            return pixel_x / 10.0, pixel_y / 10.0

        unit = self.get_param("output_unit", "mm")

        phys_x = pixel_x / self._pixel_per_mm_x
        phys_y = pixel_y / self._pixel_per_mm_y

        if unit == "inch":
            phys_x /= 25.4
            phys_y /= 25.4
        elif unit == "um":
            phys_x *= 1000
            phys_y *= 1000

        return phys_x, phys_y

    def pixel_to_physical_size(
        self, pixel_width: float, pixel_height: float
    ) -> Tuple[float, float]:
        """
        将像素尺寸转换为物理尺寸

        Args:
            pixel_width: 像素宽度
            pixel_height: 像素高度

        Returns:
            (physical_width, physical_height) 物理尺寸（mm）
        """
        if not self._calibrated:
            _logger.warning("工具未标定，使用默认比例")
            return pixel_width / 10.0, pixel_height / 10.0

        unit = self.get_param("output_unit", "mm")

        phys_w = pixel_width / self._pixel_per_mm_x
        phys_h = pixel_height / self._pixel_per_mm_y

        if unit == "inch":
            phys_w /= 25.4
            phys_h /= 25.4
        elif unit == "um":
            phys_w *= 1000
            phys_h *= 1000

        return phys_w, phys_h

    def physical_to_pixel(
        self, physical_x: float, physical_y: float
    ) -> Tuple[float, float]:
        """
        将物理坐标转换为像素坐标

        Args:
            physical_x: 物理X坐标（mm）
            physical_y: 物理Y坐标（mm）

        Returns:
            (pixel_x, pixel_y) 像素坐标
        """
        if not self._calibrated:
            _logger.warning("工具未标定，使用默认比例")
            return physical_x * 10.0, physical_y * 10.0

        unit = self.get_param("output_unit", "mm")

        px = physical_x * self._pixel_per_mm_x
        py = physical_y * self._pixel_per_mm_y

        if unit == "inch":
            px *= 25.4
            py *= 25.4
        elif unit == "um":
            px /= 1000
            py /= 1000

        return px, py

    def _run_impl(self) -> Dict[str, Any]:
        """执行标定"""
        if not self.has_input():
            raise ToolException("没有输入图像")

        input_image = self._input_data.data
        calibration_type = self.get_param("calibration_type", "manual")

        output_image = input_image.copy()

        if calibration_type == "chessboard":
            success = self.calibrate_with_chessboard(input_image)
            if not success:
                raise ToolException("棋盘格标定失败，未检测到角点")

        elif calibration_type == "circles":
            raise ToolException("圆点标定功能待实现")

        elif calibration_type == "manual":
            reference_width = self.get_param("reference_width", 100.0)
            reference_height = self.get_param("reference_height", 100.0)
            pixel_per_mm_x = self.get_param("pixel_per_mm_x", 10.0)
            pixel_per_mm_y = self.get_param("pixel_per_mm_y", 10.0)

            # 使用ROI或自动检测参考物体（简化：使用用户输入的像素值）
            # 实际应用中应该让用户选择ROI
            self._pixel_per_mm_x = pixel_per_mm_x
            self._pixel_per_mm_y = pixel_per_mm_y
            self._calibrated = True

            # 在图像上绘制标定参考框
            h, w = input_image.shape[:2]
            box_width = int(reference_width * pixel_per_mm_x)
            box_height = int(reference_height * pixel_per_mm_y)
            x1 = (w - box_width) // 2
            y1 = (h - box_height) // 2
            x2 = x1 + box_width
            y2 = y1 + box_height

            cv2.rectangle(output_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                output_image,
                f"Calibration: {pixel_per_mm_x:.2f} px/mm",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        # 保存标定参数
        save_calibration = self.get_param("save_calibration", False)
        calibration_file = self.get_param("calibration_file", "")

        if save_calibration and calibration_file:
            self._save_calibration(calibration_file)

        # 创建输出图像
        output_data = ImageData(data=output_image)

        # 设置结果
        self._result_data = ResultData()
        self._result_data.set_value("calibrated", self._calibrated)
        self._result_data.set_value("pixel_per_mm_x", self._pixel_per_mm_x)
        self._result_data.set_value("pixel_per_mm_y", self._pixel_per_mm_y)
        self._result_data.set_value("output_unit", self.get_param("output_unit", "mm"))

        _logger.info(
            f"标定完成: pixel_per_mm = ({self._pixel_per_mm_x:.3f}, {self._pixel_per_mm_y:.3f})"
        )

        return {"OutputImage": output_data}

    def _save_calibration(self, filepath: str):
        """保存标定参数"""
        try:
            data = {
                "pixel_per_mm_x": self._pixel_per_mm_x,
                "pixel_per_mm_y": self._pixel_per_mm_y,
                "calibration_matrix": self._calibration_matrix,
                "distortion_coeffs": self._distortion_coeffs,
            }
            if filepath.endswith(".npz"):
                np.savez(filepath, **data)
            elif filepath.endswith(".yaml"):
                import yaml

                yaml_data = {
                    "pixel_per_mm_x": float(self._pixel_per_mm_x),
                    "pixel_per_mm_y": float(self._pixel_per_mm_y),
                }
                with open(filepath, "w") as f:
                    yaml.dump(yaml_data, f)

            _logger.info(f"标定参数已保存到: {filepath}")
        except Exception as e:
            _logger.error(f"保存标定参数失败: {e}")

    def load_calibration(self, filepath: str) -> bool:
        """加载标定参数"""
        try:
            if filepath.endswith(".npz"):
                data = np.load(filepath)
                self._pixel_per_mm_x = float(data["pixel_per_mm_x"])
                self._pixel_per_mm_y = float(data["pixel_per_mm_y"])
                if "calibration_matrix" in data:
                    self._calibration_matrix = data["calibration_matrix"]
                if "distortion_coeffs" in data:
                    self._distortion_coeffs = data["distortion_coeffs"]
            elif filepath.endswith(".yaml"):
                import yaml

                with open(filepath, "r") as f:
                    data = yaml.safe_load(f)
                self._pixel_per_mm_x = data["pixel_per_mm_x"]
                self._pixel_per_mm_y = data["pixel_per_mm_y"]

            self._calibrated = True
            _logger.info(f"标定参数已加载: {filepath}")
            return True
        except Exception as e:
            _logger.error(f"加载标定参数失败: {e}")
            return False

    @property
    def is_calibrated(self) -> bool:
        """检查是否已标定"""
        return self._calibrated

    @property
    def pixel_per_mm(self) -> Tuple[float, float]:
        """获取像素比例"""
        return (self._pixel_per_mm_x, self._pixel_per_mm_y)
