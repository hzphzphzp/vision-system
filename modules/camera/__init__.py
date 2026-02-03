#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机模块包

包含相机管理、适配器和工具。

注意：使用延迟导入以避免循环导入问题
"""


def __getattr__(name):
    """延迟导入相机相关模块"""
    if name == 'CameraManager':
        from .camera_manager import CameraManager
        return CameraManager
    if name == 'CameraAdapter':
        from .camera_adapter import CameraAdapter
        return CameraAdapter
    if name == 'BaslerCameraAdapter':
        from .basler_camera import BaslerCameraAdapter
        return BaslerCameraAdapter
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    'CameraManager',
    'CameraAdapter',
    'BaslerCameraAdapter'
]
