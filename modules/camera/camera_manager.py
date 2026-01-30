#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机管理模块 - 支持海康MVS SDK

完全参考用户提供的海康SDK示例实现。

Author: Vision System Team
Date: 2026-01-04
"""

import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2

from data.image_data import ImageData, PixelFormat
from utils.exceptions import (
    CameraCaptureException,
    CameraConnectionException,
    CameraException,
)


def _get_mv_import_path():
    """获取MVS SDK的MvImport路径"""
    mvimport_path = os.getenv("MVCAM_COMMON_RUNENV")
    if mvimport_path:
        full_path = mvimport_path + "/Samples/Python/MvImport"
        if os.path.exists(full_path):
            return full_path

    default_path = r"D:\MVS\MVS\Development\Samples\Python\MvImport"
    if os.path.exists(default_path):
        return default_path

    return None


def _import_mv_camera_control():
    """导入海康相机SDK模块"""
    mvimport_path = _get_mv_import_path()
    if mvimport_path and mvimport_path not in sys.path:
        sys.path.append(mvimport_path)

    try:
        from CameraParams_header import (
            MVCC_ENUMVALUE,
            MVCC_FLOATVALUE,
            MVCC_INTVALUE,
            MVCC_STRINGVALUE,
        )
        from MvCameraControl_class import (
            MV_CC_DEVICE_INFO,
            MV_CC_DEVICE_INFO_LIST,
            MV_FRAME_OUT,
            MV_GIGE_DEVICE,
            MV_USB_DEVICE,
            MvCamera,
        )
        from MvErrorDefine_const import MV_OK

        MvCamera.MV_CC_Initialize()

        return {
            "MvCamera": MvCamera,
            "MV_CC_DEVICE_INFO_LIST": MV_CC_DEVICE_INFO_LIST,
            "MV_CC_DEVICE_INFO": MV_CC_DEVICE_INFO,
            "MV_GIGE_DEVICE": MV_GIGE_DEVICE,
            "MV_USB_DEVICE": MV_USB_DEVICE,
            "MV_FRAME_OUT": MV_FRAME_OUT,
            "MVCC_INTVALUE": MVCC_INTVALUE,
            "MVCC_FLOATVALUE": MVCC_FLOATVALUE,
            "MVCC_ENUMVALUE": MVCC_ENUMVALUE,
            "MVCC_STRINGVALUE": MVCC_STRINGVALUE,
            "MV_OK": MV_OK,
            "available": True,
        }
    except ImportError:
        return {"available": False}


class CameraType(Enum):
    """相机类型"""

    HIKROBOT_MVS = "hikrobot_mvs"
    USB_CAMERA = "usb_camera"
    UNKNOWN = "unknown"


class CameraState(Enum):
    """相机状态"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"


class TriggerMode(Enum):
    """触发模式"""

    CONTINUOUS = "continuous"
    SOFTWARE = "software"
    HARDWARE = "hardware"


@dataclass
class CameraInfo:
    """相机信息"""

    id: str
    name: str
    model: Optional[str] = None
    type: CameraType = CameraType.UNKNOWN


class HikCamera:
    """
    海康相机类

    封装海康MVS SDK的常用操作，完全参考官方示例实现。
    """

    def __init__(self, device_info):
        self._logger = logging.getLogger("HikCamera")
        self._device_info = device_info
        self._camera = None
        self._is_connected = False
        self._is_grabbing = False
        self._model_name = None
        self._trigger_mode = TriggerMode.CONTINUOUS

        self._payload_size = 0
        self._data_buffer = None
        self._frame_info = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_grabbing(self) -> bool:
        return self._is_grabbing

    @property
    def model_name(self) -> str:
        return self._model_name or "Unknown"

    @property
    def trigger_mode(self) -> str:
        return self._trigger_mode.value

    def connect(self) -> bool:
        """连接相机"""
        if self._is_connected:
            return True

        self._logger.info("正在连接海康相机...")

        try:
            from ctypes import byref, c_ubyte, cast, memset, sizeof

            sdk = _import_mv_camera_control()
            if not sdk.get("available", False):
                raise Exception("MVS SDK未安装或不可用")

            self._camera = sdk["MvCamera"]()
            ret = self._camera.MV_CC_CreateHandle(self._device_info)
            if ret != sdk["MV_OK"]:
                error_msg = f"创建相机句柄失败! ret[0x{ret:x}]"
                self._logger.error(error_msg)
                raise CameraConnectionException(error_msg, error_code=ret)

            ret = self._camera.MV_CC_OpenDevice(0x00000001, 0)
            if ret != sdk["MV_OK"]:
                error_msg = f"打开设备失败! ret[0x{ret:x}]"
                self._logger.error(error_msg)
                raise CameraConnectionException(error_msg, error_code=ret)

            self._get_device_info(sdk)

            stParam = sdk["MVCC_INTVALUE"]()
            memset(byref(stParam), 0, sizeof(sdk["MVCC_INTVALUE"]))
            ret = self._camera.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != sdk["MV_OK"]:
                error_msg = f"获取PayloadSize失败! ret[0x{ret:x}]"
                self._logger.error(error_msg)
                raise CameraConnectionException(error_msg, error_code=ret)

            self._payload_size = stParam.nCurValue
            self._data_buffer = (c_ubyte * self._payload_size)()

            self._is_connected = True
            self._trigger_mode = TriggerMode.CONTINUOUS
            self._logger.info(f"海康相机连接成功: {self._model_name}")
            return True

        except Exception as e:
            self._logger.error(f"相机连接失败: {e}")
            self.disconnect()
            raise

    def _get_device_info(self, sdk):
        """获取设备信息"""
        try:
            from ctypes import byref, sizeof

            stDeviceName = sdk["MVCC_STRINGVALUE"]()
            ret = self._camera.MV_CC_GetStringValue(
                "DeviceModelName", stDeviceName
            )
            if ret == sdk["MV_OK"]:
                model_name = "".join(
                    [chr(c) for c in stDeviceName.chCurValue if c != 0]
                )
                self._model_name = model_name
                self._logger.info(f"相机型号: {model_name}")

        except Exception as e:
            self._logger.debug(f"获取设备信息失败: {e}")

    def disconnect(self):
        """断开相机连接"""
        if self._is_grabbing:
            self.stop_grabbing()

        if self._is_connected and self._camera is not None:
            try:
                ret = self._camera.MV_CC_CloseDevice()
                if ret != 0:
                    self._logger.warning(f"关闭设备失败: 0x{ret:x}")

                self._camera.MV_CC_DestroyHandle()
                self._logger.info("相机已断开")
            except Exception as e:
                self._logger.error(f"断开相机时发生错误: {e}")

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

        try:
            ret = self._camera.MV_CC_StartGrabbing()
            if ret != 0:
                error_msg = f"开始取流失败! ret[0x{ret:x}]"
                self._logger.error(error_msg)
                raise CameraCaptureException(error_msg, error_code=ret)

            self._is_grabbing = True
            self._logger.info("开始取流")
            return True

        except Exception as e:
            self._logger.error(f"开始取流失败: {e}")
            return False

    def stop_grabbing(self) -> bool:
        """停止取流"""
        if not self._is_grabbing:
            return True

        try:
            ret = self._camera.MV_CC_StopGrabbing()
            if ret != 0:
                self._logger.warning(f"停止取流失败: 0x{ret:x}")
                return False

            self._is_grabbing = False
            self._logger.info("停止取流")
            return True

        except Exception as e:
            self._logger.error(f"停止取流时发生错误: {e}")
            return False

    def set_trigger_mode(self, mode: str) -> bool:
        """设置触发模式"""
        if not self._is_connected:
            self._logger.warning("相机未连接")
            return False

        try:
            if mode == "continuous":
                ret = self._camera.MV_CC_SetEnumValue("TriggerMode", 0)
                if ret != 0:
                    self._logger.warning(f"设置触发模式为Off失败: 0x{ret:x}")
                    return False
                self._trigger_mode = TriggerMode.CONTINUOUS
                self._logger.info("触发模式设置为连续取流")
            elif mode == "software":
                # 先停止取流
                if self._is_grabbing:
                    self.stop_grabbing()
                    self._logger.info("已停止取流，准备设置触发模式")

                # 设置触发模式为On
                ret = self._camera.MV_CC_SetEnumValue("TriggerMode", 1)
                if ret != 0:
                    self._logger.warning(f"设置触发模式为On失败: 0x{ret:x}")
                    return False

                # 设置触发源为Software
                ret = self._camera.MV_CC_SetEnumValue("TriggerSource", 7)
                if ret != 0:
                    self._logger.warning(
                        f"设置触发源为Software失败: 0x{ret:x}"
                    )
                    return False

                # 重新开始取流
                if not self._is_grabbing:
                    self.start_grabbing()
                    self._logger.info("已重新开始取流")

                self._trigger_mode = TriggerMode.SOFTWARE
                self._logger.info("触发模式设置为软件触发")
            elif mode == "hardware":
                # 先停止取流
                if self._is_grabbing:
                    self.stop_grabbing()
                    self._logger.info("已停止取流，准备设置触发模式")

                # 设置触发模式为On
                ret = self._camera.MV_CC_SetEnumValue("TriggerMode", 1)
                if ret != 0:
                    self._logger.warning(f"设置触发模式为On失败: 0x{ret:x}")
                    return False

                # 设置触发源为Line0
                ret = self._camera.MV_CC_SetEnumValue("TriggerSource", 0)
                if ret != 0:
                    self._logger.warning(f"设置触发源为Line0失败: 0x{ret:x}")
                    return False

                # 重新开始取流
                if not self._is_grabbing:
                    self.start_grabbing()
                    self._logger.info("已重新开始取流")

                self._trigger_mode = TriggerMode.HARDWARE
                self._logger.info("触发模式设置为硬件触发")
            else:
                self._logger.warning(f"不支持的触发模式: {mode}")
                return False

            return True

        except Exception as e:
            self._logger.error(f"设置触发模式失败: {e}")
            return False

    def trigger_software(self) -> bool:
        """软件触发一次"""
        if not self._is_connected:
            self._logger.warning("相机未连接")
            return False

        try:
            ret = self._camera.MV_CC_SetCommandValue("TriggerSoftware")
            if ret != 0:
                self._logger.warning(f"软件触发失败: 0x{ret:x}")
                return False

            self._logger.debug("软件触发一次")
            return True

        except Exception as e:
            self._logger.error(f"软件触发失败: {e}")
            return False

    def get_one_frame(self, timeout_ms: int = 1000) -> Optional[np.ndarray]:
        """获取一帧图像"""
        if not self._is_connected:
            self._logger.error("相机未连接")
            return None

        try:
            from ctypes import POINTER, byref, c_ubyte, cast, memset, sizeof

            sdk = _import_mv_camera_control()

            stOutFrame = sdk["MV_FRAME_OUT"]()
            memset(byref(stOutFrame), 0, sizeof(sdk["MV_FRAME_OUT"]))

            ret = self._camera.MV_CC_GetImageBuffer(stOutFrame, timeout_ms)
            if ret != 0:
                self._logger.warning(f"获取图像超时或失败，错误码: 0x{ret:x}")
                return None

            self._frame_info = stOutFrame.stFrameInfo

            width = self._frame_info.nWidth
            height = self._frame_info.nHeight
            frame_len = self._frame_info.nFrameLen

            pData = cast(stOutFrame.pBufAddr, POINTER(c_ubyte))

            # 创建numpy数组的副本，避免原始缓冲区被释放后访问无效内存
            temp = np.ctypeslib.as_array(pData, shape=(frame_len,)).copy()
            image = temp.reshape((height, width))

            self._camera.MV_CC_FreeImageBuffer(stOutFrame)

            return image

        except Exception as e:
            self._logger.error(f"获取图像失败: {e}")
            return None

    def capture_frame(self, timeout_ms: int = 1000) -> Optional[ImageData]:
        """采集一帧图像"""
        if not self._is_connected:
            self._logger.error("相机未连接")
            return None

        if not self._is_grabbing:
            if not self.start_grabbing():
                return None

        frame = self.get_one_frame(timeout_ms)

        if frame is None:
            self._logger.error("无法获取图像帧")
            return None

        self._logger.debug(f"采集图像: {frame.shape}")

        return ImageData(
            data=frame,
            width=frame.shape[1],
            height=frame.shape[0],
            camera_id=str(self._device_info),
            pixel_format=PixelFormat.MONO8,
        )

    def get_all_parameter_info(self) -> Dict[str, Any]:
        """获取所有参数信息"""
        params = {}

        if not self._is_connected:
            return params

        try:
            from ctypes import byref, memset, sizeof

            sdk = _import_mv_camera_control()

            stFloatParam = sdk["MVCC_FLOATVALUE"]()
            memset(byref(stFloatParam), 0, sizeof(sdk["MVCC_FLOATVALUE"]))
            ret = self._camera.MV_CC_GetFloatValue(
                "ExposureTime", stFloatParam
            )
            if ret == sdk["MV_OK"]:
                params["exposure"] = stFloatParam.fCurValue

            stGain = sdk["MVCC_FLOATVALUE"]()
            memset(byref(stGain), 0, sizeof(sdk["MVCC_FLOATVALUE"]))
            ret = self._camera.MV_CC_GetFloatValue("Gain", stGain)
            if ret == sdk["MV_OK"]:
                params["gain"] = stGain.fCurValue

            stFps = sdk["MVCC_FLOATVALUE"]()
            memset(byref(stFps), 0, sizeof(sdk["MVCC_FLOATVALUE"]))
            ret = self._camera.MV_CC_GetFloatValue(
                "AcquisitionFrameRate", stFps
            )
            if ret == sdk["MV_OK"]:
                params["fps"] = stFps.fCurValue

            stWidth = sdk["MVCC_INTVALUE"]()
            memset(byref(stWidth), 0, sizeof(sdk["MVCC_INTVALUE"]))
            ret = self._camera.MV_CC_GetIntValue("Width", stWidth)
            if ret == sdk["MV_OK"]:
                params["width"] = stWidth.nCurValue

            stHeight = sdk["MVCC_INTVALUE"]()
            memset(byref(stHeight), 0, sizeof(sdk["MVCC_INTVALUE"]))
            ret = self._camera.MV_CC_GetIntValue("Height", stHeight)
            if ret == sdk["MV_OK"]:
                params["height"] = stHeight.nCurValue

        except Exception as e:
            self._logger.warning(f"获取参数信息失败: {e}")

        return params

    def __del__(self):
        """析构函数"""
        try:
            self.disconnect()
        except:
            pass


class CameraManager:
    """相机管理器 - 单例模式"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraManager, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化"""
        self._logger = logging.getLogger("CameraManager")
        self._cameras = {}
        self._camera_list = []
        self._lock = threading.RLock()

    def discover_devices(self) -> List[CameraInfo]:
        """发现可用的相机设备"""
        self._logger.info("开始发现相机设备...")
        self._camera_list = []

        try:
            from ctypes import POINTER, byref, cast, sizeof

            sdk = _import_mv_camera_control()
            if not sdk.get("available", False):
                self._logger.warning("MVS SDK未安装，无法发现海康相机")
                return []

            device_list = sdk["MV_CC_DEVICE_INFO_LIST"]()
            ret = sdk["MvCamera"].MV_CC_EnumDevices(
                sdk["MV_GIGE_DEVICE"] | sdk["MV_USB_DEVICE"], device_list
            )

            if ret != sdk["MV_OK"]:
                self._logger.warning(f"枚举设备失败: 0x{ret:x}")
                return []

            if device_list.nDeviceNum == 0:
                self._logger.warning("未发现任何相机设备")
                return []

            self._logger.info(f"发现 {device_list.nDeviceNum} 个相机设备")

            for i in range(device_list.nDeviceNum):
                mvcc_dev_info = cast(
                    device_list.pDeviceInfo[i],
                    POINTER(sdk["MV_CC_DEVICE_INFO"]),
                ).contents

                if mvcc_dev_info.nTLayerType == sdk["MV_GIGE_DEVICE"]:
                    camera_id = f"hik_{i}"
                    model_name = "".join(
                        [
                            chr(c)
                            for c in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName
                            if c != 0
                        ]
                    )
                    nip = mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp
                    ip_str = f"{(nip >> 24) & 0xFF}.{(nip >> 16) & 0xFF}.{(nip >> 8) & 0xFF}.{nip & 0xFF}"
                    display_name = f"海康GigE [{i}]: {model_name} @ {ip_str}"
                    self._camera_list.append(
                        CameraInfo(
                            id=camera_id,
                            name=display_name,
                            model=model_name,
                            type=CameraType.HIKROBOT_MVS,
                        )
                    )
                    self._logger.info(f"发现海康相机: {display_name}")
                elif mvcc_dev_info.nTLayerType == sdk["MV_USB_DEVICE"]:
                    camera_id = f"hik_{i}"
                    model_name = "".join(
                        [
                            chr(c)
                            for c in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName
                            if c != 0
                        ]
                    )
                    display_name = f"海康USB [{i}]: {model_name}"
                    self._camera_list.append(
                        CameraInfo(
                            id=camera_id,
                            name=display_name,
                            model=model_name,
                            type=CameraType.HIKROBOT_MVS,
                        )
                    )
                    self._logger.info(f"发现海康USB相机: {display_name}")

            return self._camera_list

        except ImportError:
            self._logger.warning("MVS SDK未安装，无法发现海康相机")
            return []
        except Exception as e:
            import traceback

            self._logger.error(f"发现相机设备失败: {e}")
            self._logger.error(f"详细错误: {traceback.format_exc()}")
            return []

    def connect(self, camera_id: str) -> Optional[HikCamera]:
        """连接相机"""
        # 确保相机ID格式正确
        final_camera_id = camera_id
        if not final_camera_id.startswith("hik_"):
            final_camera_id = f"hik_{final_camera_id}"
            self._logger.info(f"使用hik_前缀格式相机ID: {final_camera_id}")

        self._logger.info(f"正在连接相机: {final_camera_id}")

        try:
            from ctypes import POINTER, byref, cast, sizeof

            sdk = _import_mv_camera_control()
            if not sdk.get("available", False):
                self._logger.warning("MVS SDK未安装")
                return None

            with self._lock:
                # 检查是否已有该相机的实例
                if final_camera_id in self._cameras:
                    camera = self._cameras[final_camera_id]
                    if camera.is_connected:
                        self._logger.info(
                            f"使用已连接的相机实例: {final_camera_id}"
                        )
                        return camera
                    else:
                        # 如果相机已断开，移除旧实例
                        del self._cameras[final_camera_id]
                        self._logger.info(
                            f"移除已断开的相机实例: {final_camera_id}"
                        )

                # 如果相机已连接，直接返回
                if (
                    final_camera_id in self._cameras
                    and self._cameras[final_camera_id].is_connected
                ):
                    return self._cameras[final_camera_id]

            device_list = sdk["MV_CC_DEVICE_INFO_LIST"]()
            ret = sdk["MvCamera"].MV_CC_EnumDevices(
                sdk["MV_GIGE_DEVICE"] | sdk["MV_USB_DEVICE"], device_list
            )

            if ret != sdk["MV_OK"]:
                self._logger.error(f"枚举设备失败: 0x{ret:x}")
                return None

            idx = int(final_camera_id.split("_")[-1])

            if idx < 0 or idx >= device_list.nDeviceNum:
                self._logger.error(f"无效的相机索引: {idx}")
                return None

            device_info = device_list.pDeviceInfo[idx]
            stDeviceInfo = cast(
                device_info, POINTER(sdk["MV_CC_DEVICE_INFO"])
            ).contents

            camera = HikCamera(stDeviceInfo)
            camera.connect()

            with self._lock:
                self._cameras[final_camera_id] = camera

            self._logger.info(f"相机连接成功: {final_camera_id}")

            return camera

        except ImportError:
            self._logger.warning("MVS SDK未安装")
            return None
        except Exception as e:
            import traceback

            self._logger.error(f"连接相机失败: {e}")
            self._logger.error(f"详细错误: {traceback.format_exc()}")
            return None

    def disconnect(self, camera_id: str) -> bool:
        """断开相机连接"""
        # 确保相机ID格式正确
        final_camera_id = camera_id
        if not final_camera_id.startswith("hik_"):
            final_camera_id = f"hik_{final_camera_id}"

        with self._lock:
            if final_camera_id in self._cameras:
                camera = self._cameras[final_camera_id]
                try:
                    camera.disconnect()
                except Exception as e:
                    self._logger.error(f"断开相机时发生错误: {e}")
                del self._cameras[final_camera_id]
                self._logger.info(f"相机已断开: {final_camera_id}")
                return True
            else:
                self._logger.warning(f"相机未连接: {final_camera_id}")
                return False

    def shutdown(self):
        """关闭管理器"""
        self._logger.info("相机管理器正在关闭...")

        with self._lock:
            for camera_id, camera in list(self._cameras.items()):
                try:
                    camera.disconnect()
                except Exception as e:
                    self._logger.error(f"断开相机 {camera_id} 时发生错误: {e}")

            self._cameras.clear()

        self._logger.info("相机管理器已关闭")

    def get_camera(self, camera_id: str) -> Optional[HikCamera]:
        """获取已连接的相机"""
        # 确保相机ID格式正确
        final_camera_id = camera_id
        if not final_camera_id.startswith("hik_"):
            final_camera_id = f"hik_{final_camera_id}"

        with self._lock:
            camera = self._cameras.get(final_camera_id)
            if camera and not camera.is_connected:
                # 如果相机已断开，移除实例
                del self._cameras[final_camera_id]
                self._logger.info(f"移除已断开的相机实例: {final_camera_id}")
                return None
            return camera

    def get_connected_cameras(self) -> List[str]:
        """获取所有已连接相机的ID列表"""
        with self._lock:
            connected_cameras = []
            for camera_id, camera in list(self._cameras.items()):
                if camera.is_connected:
                    connected_cameras.append(camera_id)
                else:
                    # 清理已断开的相机实例
                    del self._cameras[camera_id]
            return connected_cameras

    def is_camera_connected(self, camera_id: str) -> bool:
        """检查相机是否已连接"""
        # 确保相机ID格式正确
        final_camera_id = camera_id
        if not final_camera_id.startswith("hik_"):
            final_camera_id = f"hik_{final_camera_id}"

        camera = self.get_camera(final_camera_id)
        return camera is not None and camera.is_connected
