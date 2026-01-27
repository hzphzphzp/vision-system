#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理测试脚本

测试错误处理和异常管理的改进

Author: Vision System Team
Date: 2025-01-04
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tool_base import ToolBase
from data.image_data import ImageData, ResultData
from utils.exceptions import ParameterException, ImageException, CameraException
from utils.error_management import get_error_message, log_error
from utils.error_recovery import recover_from_error, RecoveryStatus


class TestTool(ToolBase):
    """测试工具类"""
    tool_name = "TestTool"
    tool_category = "Test"
    
    def _run_impl(self):
        """实际执行逻辑"""
        # 这里可以根据需要抛出不同类型的异常
        # raise ParameterException("测试参数错误")
        # raise ImageException("测试图像错误")
        # raise CameraException("测试相机错误")
        # raise Exception("测试系统错误")
        
        # 正常执行
        return {"result": "success"}


def test_error_handling():
    """测试错误处理"""
    print("=== 测试错误处理 ===")
    
    # 创建测试工具
    tool = TestTool("test_tool")
    
    # 测试1: 正常执行
    print("\n1. 测试正常执行:")
    try:
        success = tool.run()
        print(f"   执行结果: {success}")
        print(f"   最后错误: {tool.last_error}")
    except Exception as e:
        print(f"   异常: {e}")
    
    # 测试2: 参数错误
    print("\n2. 测试参数错误:")
    tool2 = TestTool("test_tool_2")
    def raise_param_error():
        raise ParameterException("测试参数错误")
    tool2._run_impl = raise_param_error
    try:
        success = tool2.run()
        print(f"   执行结果: {success}")
    except Exception as e:
        print(f"   异常: {e}")
        print(f"   最后错误: {tool2.last_error}")
    
    # 测试3: 图像错误
    print("\n3. 测试图像错误:")
    tool3 = TestTool("test_tool_3")
    def raise_image_error():
        raise ImageException("测试图像错误")
    tool3._run_impl = raise_image_error
    try:
        success = tool3.run()
        print(f"   执行结果: {success}")
    except Exception as e:
        print(f"   异常: {e}")
        print(f"   最后错误: {tool3.last_error}")
    
    # 测试4: 相机错误
    print("\n4. 测试相机错误:")
    tool4 = TestTool("test_tool_4")
    def raise_camera_error():
        raise CameraException("测试相机错误")
    tool4._run_impl = raise_camera_error
    try:
        success = tool4.run()
        print(f"   执行结果: {success}")
    except Exception as e:
        print(f"   异常: {e}")
        print(f"   最后错误: {tool4.last_error}")
    
    # 测试5: 系统错误
    print("\n5. 测试系统错误:")
    tool5 = TestTool("test_tool_5")
    def raise_system_error():
        raise Exception("测试系统错误")
    tool5._run_impl = raise_system_error
    try:
        success = tool5.run()
        print(f"   执行结果: {success}")
    except Exception as e:
        print(f"   异常: {e}")
        print(f"   最后错误: {tool5.last_error}")


def test_error_management():
    """测试错误管理模块"""
    print("\n=== 测试错误管理模块 ===")
    
    # 测试错误消息格式化
    error_message = get_error_message(400, "参数值无效")
    print(f"\n1. 错误消息格式化:")
    print(f"   错误消息: {error_message}")
    
    # 测试错误日志记录
    print("\n2. 测试错误日志记录:")
    log_error(400, "参数值无效", {"tool": "test_tool", "param": "threshold"})
    print("   错误日志已记录")


def test_error_recovery():
    """测试错误恢复模块"""
    print("\n=== 测试错误恢复模块 ===")
    
    # 测试参数错误恢复
    print("\n1. 测试参数错误恢复:")
    status = recover_from_error(
        error_type="ParameterError",
        error_code=400,
        error_message="参数值无效",
        component="test_tool",
        details={"tool": "test_tool", "param": "threshold"}
    )
    print(f"   恢复状态: {status.value}")
    
    # 测试图像错误恢复
    print("\n2. 测试图像错误恢复:")
    status = recover_from_error(
        error_type="ImageError",
        error_code=422,
        error_message="图像处理失败",
        component="test_tool"
    )
    print(f"   恢复状态: {status.value}")
    
    # 测试相机错误恢复
    print("\n3. 测试相机错误恢复:")
    status = recover_from_error(
        error_type="CameraError",
        error_code=502,
        error_message="相机连接失败",
        component="test_tool"
    )
    print(f"   恢复状态: {status.value}")
    
    # 测试系统错误恢复
    print("\n4. 测试系统错误恢复:")
    status = recover_from_error(
        error_type="InternalError",
        error_code=500,
        error_message="系统内部错误",
        component="test_tool"
    )
    print(f"   恢复状态: {status.value}")


if __name__ == "__main__":
    # 修复lambda函数中的raise语法
    import types
    def raise_exception(exc):
        def func():
            raise exc
        return func
    
    # 重新定义测试工具的_run_impl方法
    TestTool._run_impl = lambda self: {"result": "success"}
    
    # 运行测试
    test_error_handling()
    test_error_management()
    test_error_recovery()
    
    print("\n=== 测试完成 ===")
