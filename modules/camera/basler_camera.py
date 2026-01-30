#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basler相机适配器

使用pypylon SDK实现Basler相机支持。

Requirements:
    pip install pypylon

Author: Vision System Team
Date: 2026-01-19
"""

import logging
import os
import sys
import threading
from typing import Any, Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from data.image_data import ImageData, PixelFormat
from .camera_adapter import (
    CameraAdapter,
    CameraInfo,
    CameraState,
    CameraType,
    TriggerMode,
)


class BaslerCameraAdapter(CameraAdapter):
    """Basler相机适配器

    使用pypylon SDK实现Basler相机支持。
    """

    def __init__(self, camera_id: str):
        super().__init__(camera_id)
        self._camera = None
        self._grab_thread = None
        self._stop_event = threading.Event()
        self._frame_callback = None
        self._payload_size = 0

    def connect(self) -> bool:
        """连接Basler相机"""
        if self._is_connected:
            return True

        self._logger.info("正在连接Basler相机...")

        try:
            from pypylon import pylon

            # 創建相機實例
            tl_factory = pylon.TlFactory.GetInstance()
            devices = tl_factory.EnumerateDevices()

            if not devices:
                self._logger.warning("未发现Basler相机设备")
                return False

            # 查找指定相机
            camera = None
            for i, device in enumerate(devices):
                device_id = f"basler_{i}"
                if device_id == self._camera_id:
                    camera = pylon.TlFactory.GetInstance().CreateDevice(device)
                    break

            # 如果找不到指定相机，使用第一个
            if camera is None:
                if self._camera_id.startswith("basler_"):
                    idx = int(self._camera_id.split("_")[-1])
                    if idx < len(devices):
                        camera = pylon.TlFactory.GetInstance().CreateDevice(
                            devices[idx]
                        )
                    else:
                        camera = pylon.TlFactory.GetInstance().CreateDevice(
                            devices[0]
                        )
                else:
                    camera = pylon.TlFactory.GetInstance().CreateDevice(
                        devices[0]
                    )

            # 打开相机
            camera.Open()

            # 获取相机信息
            model_name = camera.GetDeviceInfo().GetModelName()
            serial_number = camera.GetDeviceInfo().GetSerialNumber()

            self._camera_info = CameraInfo(
                id=self._camera_id,
                name=f"Basler {model_name}",
                model=model_name,
                type=CameraType.BASLER_PYLON,
                serial_number=serial_number,
            )

            # 获取有效载荷大小
            self._payload_size = camera.PayloadSize.GetValue()

            self._camera = camera
            self._is_connected = True

            self._logger.info(
                f"Basler相机连接成功: {model_name} (SN: {serial_number})"
            )
            return True

        except ImportError:
            self._logger.warning("pypylon未安装，无法连接Basler相机")
            return False
        except Exception as e:
            self._logger.error(f"连接Basler相机失败: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """断开Basler相机连接"""
        self.stop_grabbing()

        if self._camera is not None and self._is_connected:
            try:
                self._camera.Close()
                self._logger.info("Basler相机已断开")
            except Exception as e:
                self._logger.error(f"断开Basler相机时发生错误: {e}")

        self._camera = None
        self._is_connected = False
        self._is_grabbing = False

    def start_grabbing(
        self, callback: Callable[[ImageData], None] = None
    ) -> bool:
        """开始取流"""
        if not self._is_connected:
            self._logger.error("相机未连接，无法开始取流")
            return False

        if self._is_grabbing:
            return True

        self._frame_callback = callback
        self._stop_event.clear()

        try:
            self._camera.StartGrabbing(self.pylon.GrabStrategy_LatestImageOnly)
            self._is_grabbing = True

            # 启动取帧线程
            self._grab_thread = threading.Thread(
                target=self._grab_loop, daemon=True
            )
            self._grab_thread.start()

            self._logger.info("开始取流")
            return True

        except Exception as e:
            self._logger.error(f"开始取流失败: {e}")
            return False

    def stop_grabbing(self) -> bool:
        """停止取流"""
        if not self._is_grabbing:
            return True

        self._stop_event.set()

        if self._camera is not None:
            try:
                self._camera.StopGrabbing()
            except Exception as e:
                self._logger.warning(f"停止取流时发生错误: {e}")

        if self._grab_thread is not None:
            self._grab_thread.join(timeout=5.0)
            self._grab_thread = None

        self._is_grabbing = False
        self._logger.info("停止取流")
        return True

    def _grab_loop(self):
        """取帧循环"""
        from pypylon import pylon

        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_Mono8
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        while not self._stop_event.is_set() and self._is_grabbing:
            try:
                grab_result = self._camera.RetrieveResult(
                    1000, pylon.TimeoutHandling_ThrowException
                )

                if grab_result.IsValid():
                    # 转换图像格式
                    image = converter.Convert(grab_result).GetArray()

                    # 创建ImageData
                    image_data = ImageData(
                        data=image,
                        width=image.shape[1],
                        height=image.shape[0],
                        camera_id=self._camera_id,
                        pixel_format=PixelFormat.MONO8,
                    )

                    # 调用回调
                    if self._frame_callback:
                        self._frame_callback(image_data)

                    grab_result.Release()

            except Exception as e:
                if not self._stop_event.is_set():
                    self._logger.debug(f"取帧时发生错误: {e}")

    def capture_frame(self, timeout_ms: int = 1000) -> Optional[ImageData]:
        """采集一帧图像"""
        if not self._is_connected:
            self._logger.error("相机未连接")
            return None

        try:
            from pypylon import pylon

            # 如果正在取流，使用回调方式获取
            if self._is_grabbing:
                frame = None
                event = threading.Event()

                def callback(image_data):
                    nonlocal frame
                    frame = image_data
                    event.set()

                self._frame_callback = callback
                event.wait(timeout=1000)
                return frame

            # 单次采集模式
            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_Mono8
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

            self._camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            grab_result = self._camera.RetrieveResult(
                timeout_ms, pylon.TimeoutHandling_ThrowException
            )

            if grab_result.IsValid():
                image = converter.Convert(grab_result).GetArray()
                grab_result.Release()

                self._camera.StopGrabbing()

                return ImageData(
                    data=image,
                    width=image.shape[1],
                    height=image.shape[0],
                    camera_id=self._camera_id,
                    pixel_format=PixelFormat.MONO8,
                )

            self._camera.StopGrabbing()
            return None

        except Exception as e:
            self._logger.error(f"采集图像失败: {e}")
            return None

    def set_parameter(self, name: str, value: Any) -> bool:
        """设置相机参数"""
        if not self._is_connected or self._camera is None:
            return False

        try:
            if name == "exposure":
                self._camera.ExposureTime.SetValue(float(value))
            elif name == "gain":
                self._camera.Gain.SetValue(float(value))
            elif name == "width":
                self._camera.Width.SetValue(int(value))
            elif name == "height":
                self._camera.Height.SetValue(int(value))
            elif name == "fps":
                self._camera.AcquisitionFrameRate.SetValue(float(value))
            else:
                self._logger.warning(f"不支持的参数: {name}")
                return False

            return True

        except Exception as e:
            self._logger.error(f"设置参数失败: {name}={value}, {e}")
            return False

    def get_parameter(self, name: str) -> Any:
        """获取相机参数"""
        if not self._is_connected or self._camera is None:
            return None

        try:
            if name == "exposure":
                return self._camera.ExposureTime.GetValue()
            elif name == "gain":
                return self._camera.Gain.GetValue()
            elif name == "width":
                return self._camera.Width.GetValue()
            elif name == "height":
                return self._camera.Height.GetValue()
            elif name == "fps":
                return self._camera.AcquisitionFrameRate.GetValue()
            elif name == "payload_size":
                return self._camera.PayloadSize.GetValue()
            else:
                self._logger.warning(f"不支持的参数: {name}")
                return None

        except Exception as e:
            self._logger.error(f"获取参数失败: {name}, {e}")
            return None

    def set_trigger_mode(self, mode: str) -> bool:
        """设置触发模式"""
        if not self._is_connected or self._camera is None:
            return False

        try:
            from pypylon import pylon

            if mode == "continuous":
                self._camera.TriggerMode.SetValue(pylon.TriggerMode_Off)
                self._trigger_mode = TriggerMode.CONTINUOUS
            elif mode == "software":
                self._camera.TriggerMode.SetValue(pylon.TriggerMode_On)
                self._camera.TriggerSource.SetValue(
                    pylon.TriggerSource_Software
                )
                self._trigger_mode = TriggerMode.SOFTWARE
            elif mode == "hardware":
                self._camera.TriggerMode.SetValue(pylon.TriggerMode_On)
                self._camera.TriggerSource.SetValue(pylon.TriggerSource_Line1)
                self._trigger_mode = TriggerMode.HARDWARE
            else:
                self._logger.warning(f"不支持的触发模式: {mode}")
                return False

            self._logger.info(f"触发模式设置为: {mode}")
            return True

        except Exception as e:
            self._logger.error(f"设置触发模式失败: {e}")
            return False

    def trigger_software(self) -> bool:
        """软件触发一次"""
        if not self._is_connected or self._camera is None:
            return False

        try:
            self._camera.ExecuteSoftwareTrigger()
            return True
        except Exception as e:
            self._logger.error(f"软件触发失败: {e}")
            return False


# 注册Basler适配器
from .camera_adapter import CameraAdapterFactory, CameraType

CameraAdapterFactory.register(CameraType.BASLER_PYLON, BaslerCameraAdapter)
