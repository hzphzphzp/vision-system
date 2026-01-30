#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机参数设置模块

基于海康SDK的相机参数设置工具，实现相机参数的配置、修改和验证功能。

Author: Vision System Team
Date: 2026-01-28
"""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.tool_base import ToolBase, ToolParameter, ToolPort, ToolRegistry
from data.image_data import ImageData
from modules.camera.camera_manager import CameraInfo, CameraManager, HikCamera
from utils.exceptions import CameraException, ParameterException


@dataclass
class CameraParamRange:
    """相机参数范围"""

    min_value: float
    max_value: float
    step: float
    default: float


class CameraParameterSettingTool(ToolBase):
    """
    相机参数设置工具

    用于设置和管理相机的各项参数，包括：
    - 曝光时间
    - 增益
    - 伽马值
    - 分辨率（宽度、高度）
    - 帧率
    - 触发模式
    """

    tool_name = "相机参数设置"
    tool_category = "ImageSource"
    tool_description = "设置和管理相机的各项参数"

    INPUT_PORTS = []

    OUTPUT_PORTS = [
        ToolPort("Status", "output", "string", "相机状态"),
        ToolPort("Parameters", "output", "value", "相机参数"),
    ]

    PARAM_DEFINITIONS = {
        "camera_id": ToolParameter(
            name="相机ID",
            param_type="string",
            default="",
            description="要控制的相机ID",
        ),
        "exposure": ToolParameter(
            name="曝光时间",
            param_type="float",
            default=10000.0,
            description="相机曝光时间（微秒）",
            min_value=1.0,
            max_value=1000000.0,
            unit="μs",
        ),
        "gain": ToolParameter(
            name="增益",
            param_type="float",
            default=0.0,
            description="相机增益",
            min_value=0.0,
            max_value=48.0,
            unit="dB",
        ),
        "gamma": ToolParameter(
            name="伽马值",
            param_type="float",
            default=1.0,
            description="相机伽马值",
            min_value=0.1,
            max_value=5.0,
        ),
        "width": ToolParameter(
            name="宽度",
            param_type="integer",
            default=1920,
            description="图像宽度",
            min_value=1,
            max_value=5000,
        ),
        "height": ToolParameter(
            name="高度",
            param_type="integer",
            default=1080,
            description="图像高度",
            min_value=1,
            max_value=5000,
        ),
        "fps": ToolParameter(
            name="帧率",
            param_type="float",
            default=30.0,
            description="相机帧率",
            min_value=1.0,
            max_value=200.0,
            unit="fps",
        ),
        "trigger_mode": ToolParameter(
            name="触发模式",
            param_type="enum",
            default="continuous",
            description="相机触发模式",
            options=["continuous", "software", "hardware"],
            option_labels={
                "continuous": "连续取流",
                "software": "软件触发",
                "hardware": "硬件触发",
            },
        ),
        "auto_exposure": ToolParameter(
            name="自动曝光",
            param_type="boolean",
            default=True,
            description="是否启用自动曝光",
        ),
        "auto_gain": ToolParameter(
            name="自动增益",
            param_type="boolean",
            default=True,
            description="是否启用自动增益",
        ),
    }

    def __init__(self, name: str = None):
        super().__init__(name)
        self._camera_manager = CameraManager()
        self._connected_camera: Optional[HikCamera] = None
        self._param_ranges: Dict[str, CameraParamRange] = {
            "exposure": CameraParamRange(1.0, 1000000.0, 100.0, 10000.0),
            "gain": CameraParamRange(0.0, 48.0, 0.1, 0.0),
            "gamma": CameraParamRange(0.1, 5.0, 0.1, 1.0),
            "fps": CameraParamRange(1.0, 200.0, 1.0, 30.0),
        }

    def _check_input(self) -> bool:
        """参数设置工具不需要输入"""
        return True

    def _run_impl(self):
        """执行相机参数设置"""
        try:
            camera_id = self.get_param("camera_id")

            if not camera_id:
                return {"Status": "未选择相机", "Parameters": {}}

            # 确保相机ID格式正确
            final_camera_id = camera_id
            if not final_camera_id.startswith("hik_"):
                final_camera_id = f"hik_{final_camera_id}"

            # 连接相机
            camera = self._connect_camera(final_camera_id)
            if not camera:
                return {"Status": "相机连接失败", "Parameters": {}}

            # 更新参数
            self._update_camera_parameters(camera)

            # 获取更新后的参数
            updated_params = camera.get_all_parameter_info()

            return {"Status": "参数设置成功", "Parameters": updated_params}

        except Exception as e:
            self._logger.error(f"执行相机参数设置失败: {e}")
            return {"Status": f"执行失败: {str(e)}", "Parameters": {}}

    def _connect_camera(self, camera_id: str) -> Optional[HikCamera]:
        """连接相机"""
        try:
            # 首先尝试获取已连接的相机
            existing_camera = self._camera_manager.get_camera(camera_id)
            if existing_camera and existing_camera.is_connected:
                self._connected_camera = existing_camera
                self._logger.info(f"使用已连接的相机: {camera_id}")
                return existing_camera

            # 如果相机未连接，尝试连接
            camera = self._camera_manager.connect(camera_id)
            if camera:
                self._connected_camera = camera
                self._logger.info(f"成功连接相机: {camera_id}")
            return camera
        except Exception as e:
            self._logger.error(f"连接相机失败: {e}")
            raise CameraException(f"连接相机失败: {str(e)}")

    def _update_camera_parameters(self, camera: HikCamera):
        """更新相机参数"""
        try:
            # 设置曝光时间
            exposure = self.get_param("exposure")
            auto_exposure = self.get_param("auto_exposure")
            if not auto_exposure:
                if not self._set_camera_parameter(
                    camera, "ExposureTime", exposure
                ):
                    self._logger.warning(f"设置曝光时间失败: {exposure}")

            # 设置增益
            gain = self.get_param("gain")
            auto_gain = self.get_param("auto_gain")
            if not auto_gain:
                if not self._set_camera_parameter(camera, "Gain", gain):
                    self._logger.warning(f"设置增益失败: {gain}")

            # 设置伽马值
            gamma = self.get_param("gamma")
            if not self._set_camera_parameter(camera, "Gamma", gamma):
                self._logger.warning(f"设置伽马值失败: {gamma}")

            # 设置分辨率
            width = self.get_param("width")
            height = self.get_param("height")
            if not self._set_camera_parameter(camera, "Width", width):
                self._logger.warning(f"设置宽度失败: {width}")
            if not self._set_camera_parameter(camera, "Height", height):
                self._logger.warning(f"设置高度失败: {height}")

            # 设置帧率
            fps = self.get_param("fps")
            if not self._set_camera_parameter(
                camera, "AcquisitionFrameRate", fps
            ):
                self._logger.warning(f"设置帧率失败: {fps}")

            # 设置触发模式
            trigger_mode = self.get_param("trigger_mode")
            if not camera.set_trigger_mode(trigger_mode):
                self._logger.warning(f"设置触发模式失败: {trigger_mode}")

        except Exception as e:
            self._logger.error(f"更新相机参数失败: {e}")
            raise ParameterException(f"更新相机参数失败: {str(e)}")

    def _set_camera_parameter(
        self, camera: HikCamera, param_name: str, value: Any
    ):
        """设置相机参数"""
        try:
            from ctypes import byref, memset, sizeof

            sdk = self._import_mv_camera_control()
            if not sdk.get("available", False):
                raise Exception("MVS SDK未安装或不可用")

            # 参数类型验证
            if value is None:
                self._logger.error(f"参数 {param_name} 值为None")
                return False

            # 根据参数类型设置值
            if param_name in [
                "ExposureTime",
                "Gain",
                "Gamma",
                "AcquisitionFrameRate",
            ]:
                # 浮点参数
                try:
                    float_value = float(value)
                except (ValueError, TypeError) as e:
                    self._logger.error(f"参数 {param_name} 类型转换失败: {e}")
                    return False

                stParam = sdk["MVCC_FLOATVALUE"]()
                memset(byref(stParam), 0, sizeof(sdk["MVCC_FLOATVALUE"]))
                stParam.fCurValue = float_value
                ret = camera._camera.MV_CC_SetFloatValue(
                    param_name.encode("utf-8"), stParam
                )
            elif param_name in ["Width", "Height"]:
                # 整数参数
                try:
                    int_value = int(value)
                except (ValueError, TypeError) as e:
                    self._logger.error(f"参数 {param_name} 类型转换失败: {e}")
                    return False

                stParam = sdk["MVCC_INTVALUE"]()
                memset(byref(stParam), 0, sizeof(sdk["MVCC_INTVALUE"]))
                stParam.nCurValue = int_value
                ret = camera._camera.MV_CC_SetIntValue(
                    param_name.encode("utf-8"), stParam
                )
            else:
                # 其他参数
                self._logger.warning(f"不支持的参数类型: {param_name}")
                return False

            if ret != sdk["MV_OK"]:
                error_msg = f"设置参数 {param_name} 失败! ret[0x{ret:x}]"
                self._logger.error(error_msg)
                return False

            self._logger.info(f"成功设置参数 {param_name} = {value}")
            return True

        except Exception as e:
            self._logger.error(f"设置参数 {param_name} 失败: {e}")
            import traceback

            self._logger.error(f"详细错误: {traceback.format_exc()}")
            return False

    def _import_mv_camera_control(self):
        """导入海康相机SDK模块"""
        from modules.camera.camera_manager import _import_mv_camera_control

        return _import_mv_camera_control()

    def show_parameter_dialog(self, parent=None):
        """显示参数设置对话框"""
        dialog = CameraParameterDialog(self, parent)
        return dialog.exec_()

    def get_available_cameras(self) -> List[CameraInfo]:
        """获取可用相机列表"""
        try:
            return self._camera_manager.discover_devices()
        except Exception as e:
            self._logger.error(f"获取可用相机列表失败: {e}")
            return []

    def get_camera_parameters(self, camera_id: str) -> Dict[str, Any]:
        """获取相机当前参数"""
        try:
            # 确保相机ID格式正确
            final_camera_id = camera_id
            if not final_camera_id.startswith("hik_"):
                final_camera_id = f"hik_{final_camera_id}"

            camera = self._connect_camera(final_camera_id)
            if camera:
                return camera.get_all_parameter_info()
            return {}
        except Exception as e:
            self._logger.error(f"获取相机参数失败: {e}")
            return {}

    def get_connected_camera(self) -> Optional[HikCamera]:
        """获取当前连接的相机"""
        return self._connected_camera

    def set_connected_camera(self, camera: Optional[HikCamera]):
        """设置当前连接的相机"""
        self._connected_camera = camera


class CameraParameterDialog(QDialog):
    """相机参数设置对话框"""

    def __init__(self, tool: CameraParameterSettingTool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("相机参数设置")
        self.setMinimumSize(600, 600)
        self.tool = tool
        self.camera_manager = tool._camera_manager
        self.connected_camera = tool._connected_camera
        self._logger = tool._logger

        self.init_ui()
        self.discover_cameras()

        # 检查是否有已连接的相机
        if self.connected_camera:
            self.connect_button.setText("关闭相机")
            self.status_label.setText("状态: 相机已连接")
            self.status_label.setStyleSheet("color: green")
            # 加载当前参数
            self.load_parameters()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 相机选择区域
        camera_group = QGroupBox("相机选择")
        camera_layout = QFormLayout()

        self.camera_combo = QComboBox()
        self.refresh_button = QPushButton("刷新")
        self.connect_button = QPushButton("连接相机")
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: red")

        camera_layout.addRow("可用相机:", self.camera_combo)
        camera_layout.addRow(self.refresh_button)
        camera_layout.addRow(self.connect_button)
        camera_layout.addRow("相机状态:", self.status_label)

        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)

        # 图像参数区域
        image_group = QGroupBox("图像参数")
        image_layout = QGridLayout()

        # 曝光时间
        self.exposure_label = QLabel("曝光时间 (μs):")
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(1.0, 1000000.0)
        self.exposure_spin.setSingleStep(100.0)
        self.exposure_spin.setValue(10000.0)
        self.auto_exposure_check = QCheckBox("自动曝光")
        self.auto_exposure_check.setChecked(True)

        # 增益
        self.gain_label = QLabel("增益:")
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0.0, 48.0)
        self.gain_spin.setSingleStep(0.1)
        self.gain_spin.setValue(0.0)
        self.auto_gain_check = QCheckBox("自动增益")
        self.auto_gain_check.setChecked(True)

        # 伽马值
        self.gamma_label = QLabel("伽马值:")
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.1, 5.0)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.setValue(1.0)

        image_layout.addWidget(self.exposure_label, 0, 0)
        image_layout.addWidget(self.exposure_spin, 0, 1)
        image_layout.addWidget(self.auto_exposure_check, 0, 2)

        image_layout.addWidget(self.gain_label, 1, 0)
        image_layout.addWidget(self.gain_spin, 1, 1)
        image_layout.addWidget(self.auto_gain_check, 1, 2)

        image_layout.addWidget(self.gamma_label, 2, 0)
        image_layout.addWidget(self.gamma_spin, 2, 1)

        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # 分辨率参数区域
        resolution_group = QGroupBox("分辨率参数")
        resolution_layout = QFormLayout()

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 5000)
        self.width_spin.setValue(1920)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 5000)
        self.height_spin.setValue(1080)

        resolution_layout.addRow("宽度:", self.width_spin)
        resolution_layout.addRow("高度:", self.height_spin)

        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)

        # 采集参数区域
        acquisition_group = QGroupBox("采集参数")
        acquisition_layout = QFormLayout()

        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setRange(1.0, 200.0)
        self.fps_spin.setSingleStep(1.0)
        self.fps_spin.setValue(30.0)

        acquisition_layout.addRow("帧率 (fps):", self.fps_spin)

        acquisition_group.setLayout(acquisition_layout)
        layout.addWidget(acquisition_group)

        # 触发控制区域
        trigger_group = QGroupBox("触发控制")
        trigger_layout = QFormLayout()

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["连续取流", "软件触发", "硬件触发"])

        trigger_layout.addRow("触发模式:", self.trigger_combo)

        trigger_group.setLayout(trigger_layout)
        layout.addWidget(trigger_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.apply_button = QPushButton("应用参数")
        self.load_button = QPushButton("加载当前参数")
        self.reset_button = QPushButton("重置")
        self.close_button = QPushButton("关闭")

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 信号连接
        self.refresh_button.clicked.connect(self.discover_cameras)
        self.connect_button.clicked.connect(self.connect_camera)
        self.apply_button.clicked.connect(self.apply_parameters)
        self.load_button.clicked.connect(self.load_parameters)
        self.reset_button.clicked.connect(self.reset_parameters)
        self.close_button.clicked.connect(self.reject)

        self.auto_exposure_check.stateChanged.connect(
            self.update_exposure_enabled
        )
        self.auto_gain_check.stateChanged.connect(self.update_gain_enabled)

    def discover_cameras(self):
        """发现可用相机"""
        try:
            self.status_label.setText("状态: 正在搜索相机...")
            self.status_label.setStyleSheet("color: orange")

            cameras = self.camera_manager.discover_devices()

            self.camera_combo.clear()
            for camera in cameras:
                self.camera_combo.addItem(camera.name, camera.id)

            if cameras:
                self.status_label.setText(f"状态: 发现 {len(cameras)} 个相机")
                self.status_label.setStyleSheet("color: blue")
            else:
                self.status_label.setText("状态: 未发现相机")
                self.status_label.setStyleSheet("color: red")

        except Exception as e:
            self.status_label.setText(f"状态: 搜索失败: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            self._logger.error(f"发现相机失败: {e}")

    def connect_camera(self):
        """连接/断开相机"""
        try:
            if self.connected_camera:
                # 断开相机
                self.status_label.setText("状态: 正在断开相机...")
                self.status_label.setStyleSheet("color: orange")

                # 获取当前选中的相机ID
                camera_id = self.camera_combo.itemData(
                    self.camera_combo.currentIndex()
                )
                if not camera_id:
                    # 如果没有选中，尝试从相机信息获取
                    camera_id = "hik_0"

                # 确保相机ID格式正确
                final_camera_id = camera_id
                if not final_camera_id.startswith("hik_"):
                    final_camera_id = f"hik_{final_camera_id}"

                # 断开CameraManager中的连接
                try:
                    self._logger.info(
                        f"尝试断开CameraManager中的相机: {final_camera_id}"
                    )
                    self.camera_manager.disconnect(final_camera_id)
                    self._logger.info(
                        f"CameraManager中的相机已断开: {final_camera_id}"
                    )
                except Exception as e:
                    self._logger.warning(f"CameraManager断开失败: {e}")

                # 断开相机连接
                try:
                    self.connected_camera.disconnect()
                except Exception as e:
                    self._logger.error(f"断开相机失败: {e}")

                self.connected_camera = None
                self.tool._connected_camera = None
                self.connect_button.setText("连接相机")
                self.status_label.setText("状态: 相机已断开")
                self.status_label.setStyleSheet("color: red")

                # 设置CameraSource中的用户断开标志
                if hasattr(self.tool, "_user_disconnected"):
                    self.tool._user_disconnected = True
                    self._logger.info("已设置CameraSource的用户断开标志")
            else:
                # 连接相机
                index = self.camera_combo.currentIndex()
                if index == -1:
                    QMessageBox.warning(self, "警告", "请先选择一个相机")
                    return

                camera_id = self.camera_combo.itemData(index)

                self.status_label.setText("状态: 正在连接相机...")
                self.status_label.setStyleSheet("color: orange")

                # 确保相机ID格式正确
                final_camera_id = camera_id
                if not final_camera_id.startswith("hik_"):
                    final_camera_id = f"hik_{final_camera_id}"

                # 尝试连接相机
                camera = self.camera_manager.connect(final_camera_id)
                if camera:
                    self.connected_camera = camera
                    self.tool._connected_camera = camera
                    self.connect_button.setText("关闭相机")
                    self.status_label.setText("状态: 相机连接成功")
                    self.status_label.setStyleSheet("color: green")

                    # 加载当前参数
                    self.load_parameters()

                    # 重置CameraSource中的用户断开标志
                    if hasattr(self.tool, "_user_disconnected"):
                        self.tool._user_disconnected = False
                        self._logger.info("已重置CameraSource的用户断开标志")

                else:
                    self.status_label.setText("状态: 相机连接失败")
                    self.status_label.setStyleSheet("color: red")

        except Exception as e:
            self.status_label.setText(f"状态: 操作失败: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            self._logger.error(f"相机操作失败: {e}")

    def apply_parameters(self):
        """应用参数"""
        try:
            if not self.connected_camera:
                QMessageBox.warning(self, "警告", "请先连接相机")
                return

            # 获取参数
            camera_id = self.camera_combo.itemData(
                self.camera_combo.currentIndex()
            )
            exposure = self.exposure_spin.value()
            gain = self.gain_spin.value()
            gamma = self.gamma_spin.value()
            width = self.width_spin.value()
            height = self.height_spin.value()
            fps = self.fps_spin.value()
            trigger_mode = self.trigger_combo.currentIndex()

            # 映射触发模式
            trigger_mode_map = ["continuous", "software", "hardware"]
            trigger_mode_str = trigger_mode_map[trigger_mode]

            # 更新工具参数
            self.tool.set_param("camera_id", camera_id)
            self.tool.set_param("exposure", exposure)
            self.tool.set_param("gain", gain)
            self.tool.set_param("gamma", gamma)
            self.tool.set_param("width", width)
            self.tool.set_param("height", height)
            self.tool.set_param("fps", fps)
            self.tool.set_param("trigger_mode", trigger_mode_str)
            self.tool.set_param(
                "auto_exposure", self.auto_exposure_check.isChecked()
            )
            self.tool.set_param("auto_gain", self.auto_gain_check.isChecked())

            # 执行工具
            result = self.tool.run()

            if isinstance(result, dict) and result.get(
                "Status", ""
            ).startswith("参数设置成功"):
                QMessageBox.information(self, "成功", "相机参数设置成功")
            else:
                if isinstance(result, dict):
                    error_msg = result.get("Status", "未知错误")
                else:
                    error_msg = str(result)
                QMessageBox.warning(self, "警告", f"参数设置失败: {error_msg}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用参数失败: {str(e)}")
            self._logger.error(f"应用相机参数失败: {e}")

    def load_parameters(self):
        """加载当前参数"""
        try:
            if not self.connected_camera:
                QMessageBox.warning(self, "警告", "请先连接相机")
                return

            params = self.connected_camera.get_all_parameter_info()

            # 更新UI
            if "exposure" in params:
                self.exposure_spin.setValue(params["exposure"])
            if "gain" in params:
                self.gain_spin.setValue(params["gain"])
            if "fps" in params:
                self.fps_spin.setValue(params["fps"])
            if "width" in params:
                self.width_spin.setValue(params["width"])
            if "height" in params:
                self.height_spin.setValue(params["height"])

            QMessageBox.information(self, "成功", "已加载相机当前参数")

        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载参数失败: {str(e)}")
            self._logger.error(f"加载相机参数失败: {e}")

    def reset_parameters(self):
        """重置参数"""
        self.exposure_spin.setValue(10000.0)
        self.gain_spin.setValue(0.0)
        self.gamma_spin.setValue(1.0)
        self.width_spin.setValue(1920)
        self.height_spin.setValue(1080)
        self.fps_spin.setValue(30.0)
        self.trigger_combo.setCurrentIndex(0)
        self.auto_exposure_check.setChecked(True)
        self.auto_gain_check.setChecked(True)

        self.update_exposure_enabled()
        self.update_gain_enabled()

    def update_exposure_enabled(self):
        """更新曝光控件状态"""
        enabled = not self.auto_exposure_check.isChecked()
        self.exposure_spin.setEnabled(enabled)
        self.exposure_label.setEnabled(enabled)

    def update_gain_enabled(self):
        """更新增益控件状态"""
        enabled = not self.auto_gain_check.isChecked()
        self.gain_spin.setEnabled(enabled)
        self.gain_label.setEnabled(enabled)


# 注册工具
ToolRegistry.register(CameraParameterSettingTool)


if __name__ == "__main__":
    # 测试代码
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    tool = CameraParameterSettingTool()
    dialog = CameraParameterDialog(tool)
    dialog.exec_()

    sys.exit(app.exec_())
