#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块

提供统一的异常类定义，方便错误处理和日志记录。

Author: Vision System Team
Date: 2025-01-04
"""


class VisionMasterException(Exception):
    """视觉检测异常基类"""
    
    def __init__(self, message: str, error_code: int = None, details: dict = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 详细错误信息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code})"


class CameraException(VisionMasterException):
    """相机异常"""
    pass


class CameraConnectionException(CameraException):
    """相机连接异常"""
    pass


class CameraCaptureException(CameraException):
    """相机采集异常"""
    pass


class ToolException(VisionMasterException):
    """工具异常"""
    pass


class ToolExecutionException(ToolException):
    """工具执行异常"""
    pass


class ToolNotFoundException(ToolException):
    """工具未找到异常"""
    pass


class ParameterException(VisionMasterException):
    """参数异常"""
    pass


class InvalidParameterException(ParameterException):
    """无效参数异常"""
    pass


class ProcedureException(VisionMasterException):
    """流程异常"""
    pass


class ProcedureExecutionException(ProcedureException):
    """流程执行异常"""
    pass


class SolutionException(VisionMasterException):
    """方案异常"""
    pass


class SolutionExecutionException(SolutionException):
    """方案执行异常"""
    pass


class ImageException(VisionMasterException):
    """图像异常"""
    pass


class ImageLoadException(ImageException):
    """图像加载异常"""
    pass


class ImageSaveException(ImageException):
    """图像保存异常"""
    pass


class ImageProcessException(ImageException):
    """图像处理异常"""
    pass


class ROIException(VisionMasterException):
    """ROI异常"""
    pass


class InvalidROIException(ROIException):
    """无效ROI异常"""
    pass


class ConfigException(VisionMasterException):
    """配置异常"""
    pass


class ConfigLoadException(ConfigException):
    """配置加载异常"""
    pass


class ConfigSaveException(ConfigException):
    """配置保存异常"""
    pass


class CommunicationException(VisionMasterException):
    """通信异常"""
    pass


class NetworkException(CommunicationException):
    """网络异常"""
    pass


class SerialException(CommunicationException):
    """串口异常"""
    pass


class TimeoutException(VisionMasterException):
    """超时异常"""
    pass


class PermissionException(VisionMasterException):
    """权限异常"""
    pass


class FileException(VisionMasterException):
    """文件异常"""
    pass


class FileNotFoundException(FileException):
    """文件未找到异常"""
    pass


class FileAccessException(FileException):
    """文件访问异常"""
    pass


class LicenseException(VisionMasterException):
    """许可证异常"""
    pass


class ModelException(VisionMasterException):
    """模型异常"""
    pass


class ModelLoadException(ModelException):
    """模型加载异常"""
    pass


class ModelInferenceException(ModelException):
    """模型推理异常"""
    pass


def get_exception_category(exception: Exception) -> str:
    """
    获取异常类别
    
    Args:
        exception: 异常实例
        
    Returns:
        异常类别名称
    """
    exception_type = type(exception)
    
    # 检查继承链
    for cls in exception_type.__mro__:
        if cls.__name__ in EXCEPTION_CATEGORIES:
            return EXCEPTION_CATEGORIES[cls.__name__]
    
    return "Unknown"


EXCEPTION_CATEGORIES = {
    "VisionMasterException": "系统",
    "CameraException": "相机",
    "ToolException": "工具",
    "ParameterException": "参数",
    "ProcedureException": "流程",
    "SolutionException": "方案",
    "ImageException": "图像",
    "ROIException": "ROI",
    "ConfigException": "配置",
    "CommunicationException": "通信",
    "FileException": "文件",
    "ModelException": "模型",
}
