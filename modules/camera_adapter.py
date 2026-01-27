#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机适配器基类

定义统一的相机接口，支持多种相机SDK。

Author: Vision System Team
Date: 2026-01-19
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

from data.image_data import ImageData, PixelFormat


class CameraType(Enum):
    """相机类型"""
    HIKROBOT_MVS = "hikrobot_mvs"
    BASLER_PYLON = "basler_pylon"
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
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None


class CameraAdapter(ABC):
    """相机适配器基类
    
    所有相机SDK适配器必须继承此类并实现所有抽象方法。
    
    使用示例:
        class MyCameraAdapter(CameraAdapter):
            def connect(self) -> bool:
                # 实现连接逻辑
                pass
    """
    
    def __init__(self, camera_id: str):
        self._camera_id = camera_id
        self._logger = logging.getLogger(f"CameraAdapter.{camera_id}")
        self._is_connected = False
        self._is_grabbing = False
        self._camera_info: Optional[CameraInfo] = None
    
    @property
    def camera_id(self) -> str:
        """获取相机ID"""
        return self._camera_id
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected
    
    @property
    def is_grabbing(self) -> bool:
        """检查是否正在取流"""
        return self._is_grabbing
    
    @property
    def camera_info(self) -> Optional[CameraInfo]:
        """获取相机信息"""
        return self._camera_info
    
    @abstractmethod
    def connect(self) -> bool:
        """连接到相机
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开相机连接"""
        pass
    
    @abstractmethod
    def start_grabbing(self, callback: Callable[[ImageData], None] = None) -> bool:
        """开始取流
        
        Args:
            callback: 帧数据回调函数
            
        Returns:
            bool: 是否成功开始取流
        """
        pass
    
    @abstractmethod
    def stop_grabbing(self) -> bool:
        """停止取流
        
        Returns:
            bool: 是否成功停止取流
        """
        pass
    
    @abstractmethod
    def capture_frame(self, timeout_ms: int = 1000) -> Optional[ImageData]:
        """采集一帧图像
        
        Args:
            timeout_ms: 超时时间（毫秒）
            
        Returns:
            ImageData: 采集的图像数据，失败返回None
        """
        pass
    
    @abstractmethod
    def set_parameter(self, name: str, value: Any) -> bool:
        """设置相机参数
        
        Args:
            name: 参数名称
            value: 参数值
            
        Returns:
            bool: 是否设置成功
        """
        pass
    
    @abstractmethod
    def get_parameter(self, name: str) -> Any:
        """获取相机参数
        
        Args:
            name: 参数名称
            
        Returns:
            参数值
        """
        pass
    
    @abstractmethod
    def set_trigger_mode(self, mode: str) -> bool:
        """设置触发模式
        
        Args:
            mode: 触发模式 (continuous/software/hardware)
            
        Returns:
            bool: 是否设置成功
        """
        pass
    
    @abstractmethod
    def trigger_software(self) -> bool:
        """软件触发一次
        
        Returns:
            bool: 是否触发成功
        """
        pass


class CameraAdapterFactory:
    """相机适配器工厂
    
    根据相机类型创建相应的适配器。
    """
    
    _adapters: Dict[CameraType, type] = {}
    
    @classmethod
    def register(cls, camera_type: CameraType, adapter_class: type):
        """注册相机适配器"""
        cls._adapters[camera_type] = adapter_class
    
    @classmethod
    def create(cls, camera_type: CameraType, camera_id: str) -> Optional[CameraAdapter]:
        """创建相机适配器
        
        Args:
            camera_type: 相机类型
            camera_id: 相机ID
            
        Returns:
            相机适配器实例，失败返回None
        """
        if camera_type not in cls._adapters:
            cls._logger.error(f"不支持的相机类型: {camera_type}")
            return None
        
        return cls._adapters[camera_type](camera_id)
    
    @classmethod
    def get_supported_types(cls) -> List[CameraType]:
        """获取支持的相机类型"""
        return list(cls._adapters.keys())


def create_camera_adapter(camera_type: str, camera_id: str) -> Optional[CameraAdapter]:
    """创建相机适配器的便捷函数
    
    Args:
        camera_type: 相机类型字符串
        camera_id: 相机ID
        
    Returns:
        相机适配器实例
    """
    type_map = {
        "hikrobot_mvs": CameraType.HIKROBOT_MVS,
        "basler_pylon": CameraType.BASLER_PYLON,
        "usb_camera": CameraType.USB_CAMERA,
    }
    
    enum_type = type_map.get(camera_type.lower(), CameraType.UNKNOWN)
    return CameraAdapterFactory.create(enum_type, camera_id)
