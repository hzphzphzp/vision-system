#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误管理模块

提供统一的错误信息管理和显示功能，包括：
- 错误消息的集中管理
- 错误分类和优先级
- 错误显示格式化
- 错误日志记录

Author: Vision System Team
Date: 2025-01-04
"""

from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
import logging


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"        # 信息性错误
    WARNING = "warning"  # 警告
    ERROR = "error"      # 错误
    CRITICAL = "critical"  # 严重错误


class ErrorCategory(Enum):
    """错误类别"""
    PARAMETER = "parameter"      # 参数错误
    IMAGE = "image"              # 图像错误
    CAMERA = "camera"            # 相机错误
    TOOL = "tool"                # 工具错误
    PROCEDURE = "procedure"      # 流程错误
    SOLUTION = "solution"        # 方案错误
    NETWORK = "network"          # 网络错误
    FILE = "file"                # 文件错误
    MODEL = "model"              # 模型错误
    SYSTEM = "system"            # 系统错误


@dataclass
class ErrorInfo:
    """错误信息类"""
    error_code: int
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    description: Optional[str] = None
    recommended_action: Optional[str] = None


class ErrorManager:
    """错误管理器"""
    
    def __init__(self):
        """初始化错误管理器"""
        self._error_catalog: Dict[int, ErrorInfo] = {}
        self._logger = logging.getLogger("ErrorManager")
        self._initialize_error_catalog()
    
    def _initialize_error_catalog(self):
        """初始化错误目录"""
        # 参数错误
        self.register_error(
            error_code=400,
            message="参数错误",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PARAMETER,
            description="输入参数无效或超出范围",
            recommended_action="检查参数值是否符合要求"
        )
        
        # 图像错误
        self.register_error(
            error_code=422,
            message="图像处理错误",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.IMAGE,
            description="图像数据无效或处理失败",
            recommended_action="检查图像源是否正确"
        )
        
        # 相机错误
        self.register_error(
            error_code=502,
            message="相机错误",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.CAMERA,
            description="相机连接或采集失败",
            recommended_action="检查相机连接和配置"
        )
        
        # 工具错误
        self.register_error(
            error_code=500,
            message="工具执行错误",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.TOOL,
            description="工具执行过程中发生错误",
            recommended_action="检查工具配置和输入数据"
        )
        
        # 网络错误
        self.register_error(
            error_code=503,
            message="网络错误",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
            description="网络连接或通信失败",
            recommended_action="检查网络连接和目标设备状态"
        )
        
        # 文件错误
        self.register_error(
            error_code=404,
            message="文件未找到",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.FILE,
            description="请求的文件不存在",
            recommended_action="检查文件路径是否正确"
        )
        
        # 系统错误
        self.register_error(
            error_code=501,
            message="系统错误",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            description="系统内部错误",
            recommended_action="检查系统日志和配置"
        )
    
    def register_error(self, error_code: int, message: str, 
                      severity: ErrorSeverity, category: ErrorCategory, 
                      description: Optional[str] = None, 
                      recommended_action: Optional[str] = None):
        """
        注册错误信息
        
        Args:
            error_code: 错误代码
            message: 错误消息
            severity: 错误严重程度
            category: 错误类别
            description: 详细描述
            recommended_action: 推荐操作
        """
        error_info = ErrorInfo(
            error_code=error_code,
            message=message,
            severity=severity,
            category=category,
            description=description,
            recommended_action=recommended_action
        )
        self._error_catalog[error_code] = error_info
        self._logger.debug(f"注册错误: {error_code} - {message}")
    
    def get_error_info(self, error_code: int) -> Optional[ErrorInfo]:
        """
        获取错误信息
        
        Args:
            error_code: 错误代码
            
        Returns:
            ErrorInfo对象，如果未找到返回None
        """
        return self._error_catalog.get(error_code)
    
    def format_error_message(self, error_code: int, 
                             details: Optional[str] = None) -> str:
        """
        格式化错误消息
        
        Args:
            error_code: 错误代码
            details: 详细错误信息
            
        Returns:
            格式化后的错误消息
        """
        error_info = self.get_error_info(error_code)
        if error_info:
            base_message = f"[{error_info.severity.value.upper()}] {error_info.message}"
            if details:
                base_message += f": {details}"
            return base_message
        return f"[ERROR] 未知错误 (代码: {error_code})"
    
    def get_error_recommendation(self, error_code: int) -> Optional[str]:
        """
        获取错误推荐操作
        
        Args:
            error_code: 错误代码
            
        Returns:
            推荐操作字符串，如果未找到返回None
        """
        error_info = self.get_error_info(error_code)
        if error_info:
            return error_info.recommended_action
        return None
    
    def log_error(self, error_code: int, details: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None):
        """
        记录错误日志
        
        Args:
            error_code: 错误代码
            details: 详细错误信息
            context: 错误上下文
        """
        error_info = self.get_error_info(error_code)
        if error_info:
            log_message = self.format_error_message(error_code, details)
            if context:
                log_message += f" - 上下文: {context}"
            
            # 根据严重程度记录日志
            if error_info.severity == ErrorSeverity.CRITICAL:
                self._logger.critical(log_message)
            elif error_info.severity == ErrorSeverity.ERROR:
                self._logger.error(log_message)
            elif error_info.severity == ErrorSeverity.WARNING:
                self._logger.warning(log_message)
            else:
                self._logger.info(log_message)
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """
        根据类别获取错误列表
        
        Args:
            category: 错误类别
            
        Returns:
            错误信息列表
        """
        return [info for info in self._error_catalog.values() 
                if info.category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """
        根据严重程度获取错误列表
        
        Args:
            severity: 错误严重程度
            
        Returns:
            错误信息列表
        """
        return [info for info in self._error_catalog.values() 
                if info.severity == severity]


# 创建全局错误管理器实例
error_manager = ErrorManager()


def get_error_message(error_code: int, details: Optional[str] = None) -> str:
    """
    获取格式化的错误消息
    
    Args:
        error_code: 错误代码
        details: 详细错误信息
        
    Returns:
        格式化后的错误消息
    """
    return error_manager.format_error_message(error_code, details)


def log_error(error_code: int, details: Optional[str] = None, 
              context: Optional[Dict[str, Any]] = None):
    """
    记录错误日志
    
    Args:
        error_code: 错误代码
        details: 详细错误信息
        context: 错误上下文
    """
    error_manager.log_error(error_code, details, context)


def get_error_recommendation(error_code: int) -> Optional[str]:
    """
    获取错误推荐操作
    
    Args:
        error_code: 错误代码
        
    Returns:
        推荐操作字符串
    """
    return error_manager.get_error_recommendation(error_code)
