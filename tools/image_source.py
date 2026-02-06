#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像源工具模块 - 简化版本用于避免语法问题

Author: Vision System Team
Date: 2026-01-22
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import (
    ImageData,
    ImageSourceToolBase,
    ToolParameter,
    ToolRegistry,
)


@ToolRegistry.register
class ImageSource(ImageSourceToolBase):
    """图像读取器工具"""

    tool_name = "图像读取器"
    tool_category = "ImageSource"
    tool_description = "从文件或相机获取图像"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._file_path = None
        self._camera = None
        self._is_connected = False
        self._last_frame_time = 0

    def _init_params(self):
        """初始化默认参数"""
        self.set_param(
            "file_path",
            "",
            param_type="image_file_path",
            description="本地图片文件路径",
        )

    def _run_impl(self):
        """执行图像采集"""
        file_path = self.get_param("file_path", "")

        if not file_path:
            raise Exception("未指定图像文件路径")

        try:
            image_data = np.fromfile(file_path, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        except:
            image = cv2.imread(file_path)

        if image is None:
            raise Exception(f"无法读取图像: {file_path}")

        height, width, channels = image.shape
        image_data = ImageData(image, width, height, channels)

        return {
            "OutputImage": image_data,
            "Width": width,
            "Height": height,
            "Channels": channels,
        }


@ToolRegistry.register
class CameraSource(ImageSourceToolBase):
    """相机图像源工具"""

    tool_name = "相机"
    tool_category = "ImageSource"
    tool_description = "从相机采集图像"

    _shared_camera_manager = None  # 共享的相机管理器

    def __init__(self, name: str = None):
        super().__init__(name)
        # 初始化相机相关属性
        self._camera = None
        self._camera_manager = None
        self._is_initialized = False
        self._user_disconnected = False  # 标记用户是否主动关闭了相机

    @classmethod
    def _get_shared_camera_manager(cls):
        """获取共享的相机管理器"""
        if cls._shared_camera_manager is None:
            from modules.camera.camera_manager import CameraManager

            cls._shared_camera_manager = CameraManager()
        return cls._shared_camera_manager

    def _init_params(self):
        """初始化默认参数"""
        self.set_param(
            "camera_id", "0", param_type="string", description="相机ID"
        )
        self.set_param(
            "trigger_mode",
            "software",
            param_type="enum",
            description="触发模式",
            options=["software", "continuous", "hardware"],
        )
        self.set_param("fps", 30, param_type="integer", description="帧率")
        self.set_param(
            "exposure",
            10000,
            param_type="integer",
            description="曝光时间（微秒）",
        )
        self.set_param("gain", 0, param_type="float", description="增益")
        self.set_param(
            "width", 640, param_type="integer", description="图像宽度"
        )
        self.set_param(
            "height", 480, param_type="integer", description="图像高度"
        )
        self.set_param(
            "auto_exposure", True, param_type="boolean", description="自动曝光"
        )
        self.set_param(
            "auto_gain", True, param_type="boolean", description="自动增益"
        )

    def _initialize_camera(self, final_camera_id=None):
        """初始化相机连接"""
        if self._is_initialized and self._camera:
            return True

        try:
            trigger_mode = self.get_param("trigger_mode", "continuous")

            # 使用共享的相机管理器
            self._camera_manager = self._get_shared_camera_manager()

            # 使用传入的final_camera_id或从参数获取
            camera_id = final_camera_id or self.get_param("camera_id", "0")

            # 连接相机
            self._logger.info(f"初始化相机连接: {camera_id}")

            # 尝试直接连接
            self._camera = self._camera_manager.get_camera(camera_id)

            # 如果相机不存在或未连接，尝试连接
            if not self._camera or not self._camera.is_connected:
                self._camera = self._camera_manager.connect(camera_id)

            if not self._camera:
                raise Exception(f"无法连接相机: {camera_id}")

            # 设置触发模式
            self._camera.set_trigger_mode(trigger_mode)

            # 开始取流
            if not self._camera.is_grabbing:
                self._camera.start_grabbing()

            self._is_initialized = True
            self._logger.info(f"相机初始化成功: {camera_id}")
            return True

        except Exception as e:
            self._logger.error(f"相机初始化失败: {e}")
            self._is_initialized = False
            return False

    def _run_impl(self):
        """执行图像采集 - 优先使用已连接相机"""
        try:
            # 获取相机参数
            camera_id = self.get_param("camera_id", "0")
            trigger_mode = self.get_param("trigger_mode", "software")
            fps = self.get_param("fps", 30)
            exposure = self.get_param("exposure", 10000)
            gain = self.get_param("gain", 0)
            width = self.get_param("width", 640)
            height = self.get_param("height", 480)
            auto_exposure = self.get_param("auto_exposure", True)
            auto_gain = self.get_param("auto_gain", True)

            # 确保相机ID格式正确
            final_camera_id = camera_id
            if not final_camera_id.startswith("hik_"):
                final_camera_id = f"hik_{final_camera_id}"

            self._logger.info(
                f"开始采集图像: camera_id={final_camera_id}, trigger_mode={trigger_mode}"
            )

            # 使用共享的相机管理器
            self._camera_manager = self._get_shared_camera_manager()

            # 优先使用已连接的相机
            self._camera = self._camera_manager.get_camera(final_camera_id)

            if self._camera and self._camera.is_connected:
                self._logger.info(f"使用已连接的相机: {final_camera_id}")
                # 重置用户断开标志
                self._user_disconnected = False
            elif self._user_disconnected:
                # 用户主动关闭了相机，不允许自动连接
                raise Exception("相机已关闭，请先在相机设置对话框中连接相机")
            else:
                # 相机未连接，不自动连接，直接报错
                raise Exception("相机未连接，请先在相机设置对话框中连接相机")

            # 确保相机已连接且正在取流
            if not self._camera.is_grabbing:
                if not self._camera.start_grabbing():
                    raise Exception("无法开始取流，请检查相机连接状态")

            # 如果是软件触发模式，发送触发信号
            if trigger_mode == "software":
                self._logger.info("发送软件触发信号...")
                # 添加重试机制，最多尝试3次
                max_retries = 3
                retry_count = 0
                trigger_success = False
                
                while retry_count < max_retries and not trigger_success:
                    trigger_success = self._camera.trigger_software()
                    if trigger_success:
                        self._logger.info(f"软件触发成功 (尝试 {retry_count + 1}/{max_retries})")
                        break
                    else:
                        retry_count += 1
                        self._logger.warning(f"软件触发失败，正在重试 ({retry_count}/{max_retries})...")
                        # 添加短暂延迟，确保相机有时间准备
                        time.sleep(0.1)
                
                if not trigger_success:
                    # 尝试重新设置触发模式
                    self._logger.info("尝试重新设置触发模式...")
                    if self._camera.set_trigger_mode("software"):
                        self._logger.info("重新设置触发模式成功，再次尝试软触发...")
                        # 再次尝试软触发
                        if self._camera.trigger_software():
                            self._logger.info("重新触发成功")
                            trigger_success = True
                        else:
                            self._logger.error("重新触发失败")
                    else:
                        self._logger.error("重新设置触发模式失败")
                
                if not trigger_success:
                    raise Exception("软触发失败，请检查相机连接状态和触发模式设置")

            # 采集一帧图像
            self._logger.info("采集一帧图像")
            image_data = self._camera.capture_frame(timeout_ms=3000)

            if not image_data:
                raise Exception("无法获取相机图像，请检查相机连接状态")

            self._logger.info(
                f"成功采集图像: {image_data.width}x{image_data.height}"
            )

            # 返回结果
            return {
                "OutputImage": image_data,
                "Width": image_data.width,
                "Height": image_data.height,
                "Channels": image_data.channels,
                "camera_id": final_camera_id,
                "trigger_mode": trigger_mode,
                "fps": fps,
                "exposure": exposure,
                "gain": gain,
                "resolution": f"{image_data.width}x{image_data.height}",
            }

        except Exception as e:
            self._logger.error(f"相机采集失败: {e}")
            # 清除相机引用，避免使用已关闭的相机
            self._camera = None
            raise Exception(f"相机采集失败: {str(e)}")

    def reset(self):
        """重置工具状态"""
        super().reset()
        # 重置相机相关状态
        self._camera = None
        self._is_initialized = False
        self._user_connected = False
        self._logger.info("相机工具已重置")

    def show_settings_dialog(self, parent=None, camera_settings_tool=None):
        """显示相机设置对话框"""
        from tools.camera_parameter_setting import CameraParameterSettingTool

        # 使用传入的相机参数设置工具实例，或创建新实例
        if camera_settings_tool:
            self._camera_settings_tool = camera_settings_tool
        elif not hasattr(self, "_camera_settings_tool"):
            self._camera_settings_tool = CameraParameterSettingTool(
                "camera_settings"
            )

        # 同步当前CameraSource的参数到相机参数设置工具
        self._camera_settings_tool.set_param(
            "camera_id", self.get_param("camera_id", "0")
        )
        self._camera_settings_tool.set_param(
            "exposure", self.get_param("exposure", 10000)
        )
        self._camera_settings_tool.set_param("gain", self.get_param("gain", 0))
        self._camera_settings_tool.set_param(
            "width", self.get_param("width", 640)
        )
        self._camera_settings_tool.set_param(
            "height", self.get_param("height", 480)
        )
        self._camera_settings_tool.set_param("fps", self.get_param("fps", 30))
        self._camera_settings_tool.set_param(
            "trigger_mode", self.get_param("trigger_mode", "continuous")
        )
        self._camera_settings_tool.set_param(
            "auto_exposure", self.get_param("auto_exposure", True)
        )
        self._camera_settings_tool.set_param(
            "auto_gain", self.get_param("auto_gain", True)
        )

        # 显示参数设置对话框
        result = self._camera_settings_tool.show_parameter_dialog(parent)

        if result == 1:  # QDialog.Accepted
            # 从相机参数设置工具获取参数并更新当前CameraSource的参数
            camera_id = self._camera_settings_tool.get_param("camera_id", "0")
            exposure = self._camera_settings_tool.get_param("exposure", 10000)
            gain = self._camera_settings_tool.get_param("gain", 0)
            gamma = self._camera_settings_tool.get_param("gamma", 1.0)
            width = self._camera_settings_tool.get_param("width", 640)
            height = self._camera_settings_tool.get_param("height", 480)
            fps = self._camera_settings_tool.get_param("fps", 30)
            trigger_mode = self._camera_settings_tool.get_param(
                "trigger_mode", "continuous"
            )
            auto_exposure = self._camera_settings_tool.get_param(
                "auto_exposure", True
            )
            auto_gain = self._camera_settings_tool.get_param("auto_gain", True)

            # 更新当前CameraSource的参数
            self.set_param("camera_id", camera_id)
            self.set_param("exposure", exposure)
            self.set_param("gain", gain)
            self.set_param("width", width)
            self.set_param("height", height)
            self.set_param("fps", fps)
            self.set_param("trigger_mode", trigger_mode)
            self.set_param("auto_exposure", auto_exposure)
            self.set_param("auto_gain", auto_gain)

            # 标记用户已连接相机
            self._user_connected = True

            # 重置相机初始化状态，确保下次运行时使用新参数
            self._is_initialized = False
            self._camera = None

            self._logger.info(
                f"更新相机参数: camera_id={camera_id}, width={width}, height={height}, fps={fps}, trigger_mode={trigger_mode}"
            )

        return result
