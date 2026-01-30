#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具连接功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入所有工具模块
import tools
from core.procedure import Procedure
from core.tool_base import ToolRegistry


# 测试工具连接功能
def test_tool_connection():
    print("=== 测试工具连接功能 ===")

    # 创建流程
    procedure = Procedure("测试流程")

    # 创建两个工具实例
    print("\n1. 创建工具实例")

    # 创建图像读取器
    reader = ToolRegistry.create_tool(
        "ImageSource", "图像读取器", "image_reader_123"
    )
    reader.set_param("file_path", "test_image.jpg")
    procedure.add_tool(reader)
    print(f"   创建图像读取器: {reader.name}")

    # 创建图像拼接工具
    stitcher = ToolRegistry.create_tool("Vision", "图像拼接", "stitcher_456")
    procedure.add_tool(stitcher)
    print(f"   创建图像拼接工具: {stitcher.name}")

    # 测试连接工具
    print("\n2. 测试连接工具")
    success = procedure.connect(reader.name, stitcher.name)

    if success:
        print(f"   ✅ 连接成功: {reader.name} -> {stitcher.name}")
    else:
        print(f"   ❌ 连接失败: {reader.name} -> {stitcher.name}")

    # 测试获取连接
    print("\n3. 测试获取连接")
    connections = procedure.get_connections_from(reader.name)
    print(f"   从 {reader.name} 出发的连接数: {len(connections)}")

    for conn in connections:
        print(f"   连接: {conn.from_tool} -> {conn.to_tool}")

    # 测试断开连接
    print("\n4. 测试断开连接")
    success = procedure.disconnect(reader.name, stitcher.name)

    if success:
        print(f"   ✅ 断开成功: {reader.name} -> {stitcher.name}")
    else:
        print(f"   ❌ 断开失败: {reader.name} -> {stitcher.name}")

    # 测试获取连接（断开后）
    connections = procedure.get_connections_from(reader.name)
    print(f"   断开后，从 {reader.name} 出发的连接数: {len(connections)}")


if __name__ == "__main__":
    test_tool_connection()
