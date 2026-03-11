#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手眼标定工具模块

提供手眼标定功能，支持两种模式：
1. Eye-in-Hand（眼在手上）：相机安装在机器人末端
2. Eye-to-Hand（眼在手外）：相机固定安装

标定原理：
- Eye-in-Hand: 求解 末端位姿 * 相机到末端 = 目标位姿 * 相机到目标
- Eye-to-Hand: 求解 基座位姿 * 相机到基座 = 末端位姿 * 相机到末端

Author: Vision System Team
Date: 2026-03-11
"""

import logging
import os
import sys
import json
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException

_logger = logging.getLogger("HandEyeCalibration")


def decompose_homography(H: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """从单应性矩阵分解出旋转矩阵和平移向量

    Args:
        H: 3x3 单应性矩阵

    Returns:
        R: 3x3 旋转矩阵
        t: 3x1 平移向量
    """
    H = H / H[2, 2]
    R1 = H[:, 0]
    R2 = H[:, 1]
    t = H[:, 2]

    R1 = R1 / np.linalg.norm(R1)
    R2 = R2 / np.linalg.norm(R2)

    R3 = np.cross(R1, R2)
    R = np.column_stack([R1, R2, R3])

    U, S, Vt = np.linalg.svd(R)
    R = U @ Vt

    return R, t


def compute_hand_eye_eye_in_hand(
    robot_poses: List[np.ndarray],
    marker_poses: List[np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """Eye-in-Hand 手眼标定算法

    求解: T_cam_to_end * T_marker_to_cam = T_end_to_base * T_marker_to_base
    其中 T_cam_to_end 是我们要标定的相机到末端的关系

    Args:
        robot_poses: 机器人末端位姿列表 (每个是4x4齐次变换矩阵)
        marker_poses: 标定板位姿列表 (每个是4x4齐次变换矩阵)

    Returns:
        T_cam_to_end: 相机到末端的变换矩阵 (4x4)
        T_marker_to_base: 标定板到基座的变换矩阵 (4x4)
    """
    if len(robot_poses) < 4:
        raise ValueError("Eye-in-Hand至少需要4组数据")

    A_list = []
    B_list = []

    for i in range(len(robot_poses)):
        R_base = robot_poses[i][:3, :3]
        t_base = robot_poses[i][:3, 3]

        R_marker = marker_poses[i][:3, :3]
        t_marker = marker_poses[i][:3, 3]

        A_list.append(np.hstack([R_marker, np.eye(3)]))
        B_list.append(R_base - np.eye(3))

    A = np.vstack(A_list)
    B = np.hstack(B_list)

    X = np.linalg.lstsq(B, A, rcond=None)[0]
    R_cam_to_end = X[:, :3]
    t_cam_to_end = X[:, 3]

    R_cam_to_end, _ = cv2.Rodrigues(R_cam_to_end)
    R_cam_to_end, _ = cv2.Rodrigues(R_cam_to_end)

    T_cam_to_end = np.eye(4)
    T_cam_to_end[:3, :3] = R_cam_to_end
    T_cam_to_end[:3, 3] = t_cam_to_end

    T_marker_to_base = np.eye(4)

    return T_cam_to_end, T_marker_to_base


def compute_hand_eye_eye_to_hand(
    robot_poses: List[np.ndarray],
    marker_poses: List[np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """Eye-to-Hand 手眼标定算法

    求解: T_cam_to_base = T_end_to_base * T_cam_to_end
    其中 T_cam_to_base 是我们要标定的相机到基座的关系

    Args:
        robot_poses: 机器人末端位姿列表 (每个是4x4齐次变换矩阵)
        marker_poses: 标定板位姿列表 (每个是4x4齐次变换矩阵)

    Returns:
        T_cam_to_base: 相机到基座的变换矩阵 (4x4)
        T_cam_to_end: 相机到末端的变换矩阵 (4x4)
    """
    if len(robot_poses) < 4:
        raise ValueError("Eye-to-Hand至少需要4组数据")

    A_list = []
    B_list = []

    for i in range(len(robot_poses)):
        R_end = robot_poses[i][:3, :3]
        t_end = robot_poses[i][:3, 3]

        R_marker = marker_poses[i][:3, :3]
        t_marker = marker_poses[i][:3, 3]

        A_list.append(np.hstack([np.eye(3), R_marker]))
        B_list.append(t_end - t_marker)

    A = np.vstack(A_list)
    B = np.hstack(B_list)

    X = np.linalg.lstsq(A, B, rcond=None)[0]

    R_cam_to_end = X[:3]
    t_cam_to_end = X[3:6]

    R_cam_to_end, _ = cv2.Rodrigues(R_cam_to_end)
    R_cam_to_end, _ = cv2.Rodrigues(R_cam_to_end)

    T_cam_to_end = np.eye(4)
    T_cam_to_end[:3, :3] = R_cam_to_end
    T_cam_to_end[:3, 3] = t_cam_to_end

    T_cam_to_base = np.eye(4)
    T_cam_to_base[:3, 3] = B.mean(axis=0)

    return T_cam_to_base, T_cam_to_end


def estimate_calibration_accuracy(
    robot_poses: List[np.ndarray],
    marker_poses: List[np.ndarray],
    T_cam_to_end: np.ndarray,
    T_marker_to_base: np.ndarray
) -> float:
    """估算标定精度（重投影误差）

    Args:
        robot_poses: 机器人末端位姿列表
        marker_poses: 标定板位姿列表
        T_cam_to_end: 相机到末端变换
        T_marker_to_base: 标定板到基座变换

    Returns:
        平均重投影误差（像素）
    """
    errors = []

    for i in range(len(robot_poses)):
        T_end_to_base = robot_poses[i]
        T_marker_to_marker = marker_poses[i]

        T_cam_calc = np.linalg.inv(T_end_to_base) @ T_marker_to_base @ T_marker_to_marker
        T_cam_true = T_cam_to_end

        diff = T_cam_calc - T_cam_true
        error = np.linalg.norm(diff[:3, 3])
        errors.append(error)

    return np.mean(errors)


@ToolRegistry.register
class HandEyeCalibrationTool(ToolBase):
    """
    手眼标定工具

    支持Eye-in-Hand（眼在手上）和Eye-to-Hand（眼在手外）两种标定模式。

    参数说明：
    - calibration_mode: 标定模式选择
    - pattern_type: 标定板类型
    - pattern_width: 棋盘格宽度（内角点数）
    - pattern_height: 棋盘格高度（内角点数）
    - square_size: 单个方格实际尺寸（mm）
    """

    tool_name = "手眼标定"
    tool_category = "Vision"
    tool_description = "机器人手眼标定，支持眼在手上和眼在手外两种模式"

    PARAM_DEFINITIONS = {
        "calibration_mode": ToolParameter(
            name="标定模式",
            param_type="enum",
            default="eye_in_hand",
            description="选择手眼标定模式",
            options=["eye_in_hand", "eye_to_hand"],
            option_labels={
                "eye_in_hand": "Eye-in-Hand (眼在手上)",
                "eye_to_hand": "Eye-to-Hand (眼在手外)",
            },
        ),
        "pattern_type": ToolParameter(
            name="标定板类型",
            param_type="enum",
            default="chessboard",
            description="选择标定板类型",
            options=["chessboard", "circles", "charuco"],
            option_labels={
                "chessboard": "Chessboard (棋盘格)",
                "circles": "Circles (圆点格)",
                "charuco": "Charuco (ArUco棋盘格)",
            },
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
            name="方格尺寸(mm)",
            param_type="float",
            default=10.0,
            description="单个方格的实际物理尺寸，单位毫米(mm)",
            min_value=0.1,
            max_value=1000.0,
        ),
    }

    OUTPUT_PORTS = [
        {"name": "OutputImage", "type": "image", "description": "标定结果图像"},
        {"name": "CalibrationMatrix", "type": "data", "description": "标定矩阵"},
    ]

    def __init__(self, name: str = None):
        super().__init__(name)
        self._calibration_data = []
        self._T_cam_to_end = np.eye(4)
        self._T_cam_to_base = np.eye(4)
        self._is_calibrated = False
        self._detected_corners = None
        self._detected_image = None

    def _init_params(self):
        """初始化参数"""
        mode = get_config("hand_eye.calibration_mode", "eye_in_hand")
        pattern = get_config("hand_eye.pattern_type", "chessboard")
        width = get_config("hand_eye.pattern_width", 9)
        height = get_config("hand_eye.pattern_height", 6)
        square = get_config("hand_eye.square_size", 10.0)

        self.set_param("calibration_mode", mode)
        self.set_param("pattern_type", pattern)
        self.set_param("pattern_width", width)
        self.set_param("pattern_height", height)
        self.set_param("square_size", square)

    def add_calibration_point(
        self,
        image: np.ndarray,
        robot_pose: np.ndarray
    ) -> bool:
        """添加一个标定点

        Args:
            image: 包含标定板的图像
            robot_pose: 机器人末端位姿 (4x4齐次变换矩阵)

        Returns:
            bool: 是否成功添加
        """
        pattern_type = self.get_param("pattern_type", "chessboard")
        pattern_width = self.get_param("pattern_width", 9)
        pattern_height = self.get_param("pattern_height", 6)
        square_size = self.get_param("square_size", 10.0)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        if pattern_type == "chessboard":
            ret, corners = cv2.findChessboardCorners(
                gray,
                (pattern_width, pattern_height),
                None
            )
            if ret:
                corners = cv2.cornerSubPix(
                    gray,
                    corners,
                    (11, 11),
                    (-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 0.001)
                )
        elif pattern_type == "circles":
            ret, corners = cv2.findCirclesGrid(
                gray,
                (pattern_width, pattern_height),
                None
            )
        else:
            self._logger.warning("Charuco标定板暂不支持")
            return False

        if ret:
            self._detected_corners = corners
            self._detected_image = image.copy()

            self._calibration_data.append({
                "corners": corners,
                "robot_pose": robot_pose.copy(),
                "image": image.copy(),
            })
            self._logger.info(f"成功添加标定点，当前共{len(self._calibration_data)}个")
            return True
        else:
            self._logger.warning("未检测到标定板角点")
            return False

    def clear_calibration_data(self):
        """清除所有标定数据"""
        self._calibration_data.clear()
        self._detected_corners = None
        self._detected_image = None
        self._is_calibrated = False
        self._T_cam_to_end = np.eye(4)
        self._T_cam_to_base = np.eye(4)
        self._logger.info("已清除所有标定数据")

    def calibrate(self) -> Dict[str, Any]:
        """执行手眼标定

        Returns:
            dict: 标定结果
        """
        if len(self._calibration_data) < 4:
            raise ToolException(f"标定数据不足，需要至少4组，当前{len(self._calibration_data)}组")

        calibration_mode = self.get_param("calibration_mode", "eye_in_hand")
        pattern_width = self.get_param("pattern_width", 9)
        pattern_height = self.get_param("pattern_height", 6)
        square_size = self.get_param("square_size", 10.0)

        object_points = []
        image_points = []
        robot_poses = []
        marker_poses = []

        world_points = np.zeros(
            (pattern_width * pattern_height, 3),
            dtype=np.float32
        )
        world_points[:, :2] = np.mgrid[0:pattern_width, 0:pattern_height].T.reshape(-1, 2)
        world_points *= square_size

        for data in self._calibration_data:
            object_points.append(world_points)
            image_points.append(data["corners"].reshape(-1, 2))
            robot_poses.append(data["robot_pose"])

            marker_pose = np.eye(4)
            marker_pose[:3, 3] = [0, 0, 0]
            marker_poses.append(marker_pose)

        try:
            if calibration_mode == "eye_in_hand":
                self._T_cam_to_end, T_marker_to_base = compute_hand_eye_eye_in_hand(
                    robot_poses, marker_poses
                )
                self._T_cam_to_base = np.eye(4)
                result_msg = "Eye-in-Hand标定完成"
            else:
                self._T_cam_to_base, self._T_cam_to_end = compute_hand_eye_eye_to_hand(
                    robot_poses, marker_poses
                )
                result_msg = "Eye-to-Hand标定完成"

            self._is_calibrated = True

            reproj_error = estimate_calibration_accuracy(
                robot_poses, marker_poses,
                self._T_cam_to_end, self._T_cam_to_base
            )

            self._logger.info(f"{result_msg}，重投影误差: {reproj_error:.4f}mm")

            return {
                "status": True,
                "message": result_msg,
                "calibration_mode": calibration_mode,
                "T_cam_to_end": self._T_cam_to_end.tolist(),
                "T_cam_to_base": self._T_cam_to_base.tolist(),
                "reprojection_error": reproj_error,
                "num_points": len(self._calibration_data),
            }

        except Exception as e:
            raise ToolException(f"标定失败: {str(e)}")

    def save_calibration(self, file_path: str) -> bool:
        """保存标定结果

        Args:
            file_path: 保存路径

        Returns:
            bool: 是否成功保存
        """
        if not self._is_calibrated:
            raise ToolException("尚未完成标定，无法保存")

        calibration_mode = self.get_param("calibration_mode", "eye_in_hand")

        data = {
            "calibration_mode": calibration_mode,
            "T_cam_to_end": self._T_cam_to_end.tolist(),
            "T_cam_to_base": self._T_cam_to_base.tolist(),
            "parameters": {
                "pattern_width": self.get_param("pattern_width", 9),
                "pattern_height": self.get_param("pattern_height", 6),
                "square_size": self.get_param("square_size", 10.0),
            }
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        self._logger.info(f"标定结果已保存到: {file_path}")
        return True

    def load_calibration(self, file_path: str) -> bool:
        """加载标定结果

        Args:
            file_path: 标定文件路径

        Returns:
            bool: 是否成功加载
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        self._T_cam_to_end = np.array(data["T_cam_to_end"])
        self._T_cam_to_base = np.array(data["T_cam_to_base"])
        self._is_calibrated = True

        self.set_param("calibration_mode", data.get("calibration_mode", "eye_in_hand"))
        if "parameters" in data:
            params = data["parameters"]
            self.set_param("pattern_width", params.get("pattern_width", 9))
            self.set_param("pattern_height", params.get("pattern_height", 6))
            self.set_param("square_size", params.get("square_size", 10.0))

        self._logger.info(f"标定结果已从: {file_path}")
        return True

    def transform_point_to_base(self, point_2d: Tuple[float, float]) -> Tuple[float, float]:
        """将2D像素坐标转换到机器人基座坐标系

        Args:
            point_2d: 像素坐标 (x, y)

        Returns:
            基座坐标系下的坐标 (x, y, z)
        """
        if not self._is_calibrated:
            raise ToolException("尚未完成标定")

        x, y = point_2d

        point_cam = np.array([x, y, 1.0])

        T = self._T_cam_to_base if self.get_param("calibration_mode") == "eye_to_hand" else self._T_cam_to_end

        point_base = T @ point_cam

        return (point_base[0], point_base[1])

    def get_calibration_data_count(self) -> int:
        """获取当前标定数据数量"""
        return len(self._calibration_data)

    def is_calibrated(self) -> bool:
        """是否已完成标定"""
        return self._is_calibrated

    def get_transform_matrix(self) -> np.ndarray:
        """获取变换矩阵"""
        calibration_mode = self.get_param("calibration_mode", "eye_in_hand")
        if calibration_mode == "eye_in_hand":
            return self._T_cam_to_end
        else:
            return self._T_cam_to_base

    def visualize_calibration(self, image: np.ndarray = None) -> np.ndarray:
        """可视化标定结果

        Args:
            image: 可选的输入图像

        Returns:
            可视化图像
        """
        if self._detected_image is not None and image is None:
            image = self._detected_image.copy()
        elif image is None:
            return np.zeros((480, 640, 3), dtype=np.uint8)

        vis_image = image.copy()

        if self._detected_corners is not None:
            cv2.drawChessboardCorners(
                vis_image,
                (self.get_param("pattern_width", 9), self.get_param("pattern_height", 6)),
                self._detected_corners,
                True
            )

        if self._is_calibrated:
            cv2.putText(
                vis_image,
                f"Calibrated: {self.get_param('calibration_mode')}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            cv2.putText(
                vis_image,
                f"Points: {len(self._calibration_data)}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        else:
            cv2.putText(
                vis_image,
                "Not Calibrated",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        return vis_image

    def _run_impl(self) -> Dict[str, Any]:
        """执行标定工具"""
        if not self.has_input():
            raise ToolException("无输入图像")

        input_image = self._input_data.data
        h, w = input_image.shape[:2]

        vis_image = self.visualize_calibration(input_image)

        result_data = ResultData()
        result_data.tool_name = self._name
        result_data.result_category = "calibration"

        if self._is_calibrated:
            T = self.get_transform_matrix()
            result_data.set_value("calibration_mode", self.get_param("calibration_mode"))
            result_data.set_value("T_matrix", T.tolist())
            result_data.set_value("calibrated", True)
        else:
            result_data.set_value("calibrated", False)

        self._result_data = result_data

        return {
            "OutputImage": ImageData(data=vis_image),
            "CalibrationMatrix": result_data,
        }


def get_config(key: str, default=None):
    """获取配置"""
    try:
        from config.config_manager import ConfigManager
        return ConfigManager.get_instance().get(key, default)
    except:
        return default
