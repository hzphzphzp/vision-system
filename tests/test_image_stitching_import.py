#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通过tools模块导入图像拼接工具
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.tool_base import ToolRegistry


# 测试通过导入tools模块来注册所有工具
def test_tools_import():
    print("=== 测试通过tools模块导入图像拼接工具 ===")

    # 导入tools模块
    print("\n1. 导入tools模块")
    try:
        import tools

        print("   ✓ 成功导入 tools 模块")
    except Exception as e:
        print(f"   ✗ 导入模块失败: {e}")
        return

    # 列出所有已注册的工具
    print("\n2. 列出所有已注册的工具")
    all_tools = ToolRegistry.get_all_tools()
    for key, tool_cls in all_tools.items():
        print(f"   {key}")

    print(f"\n   总共注册了 {len(all_tools)} 个工具")

    # 测试获取图像拼接工具
    print("\n3. 测试获取图像拼接工具")
    tool_class = ToolRegistry.get_tool_class("Vision", "图像拼接")

    if tool_class:
        print("   ✓ 成功获取图像拼接工具类")
        print(f"   工具类: {tool_class.__name__}")
        print(f"   工具名称: {tool_class.tool_name}")
        print(f"   工具类别: {tool_class.tool_category}")

        # 测试创建工具实例
        print("\n4. 测试创建工具实例")
        try:
            tool_instance = ToolRegistry.create_tool(
                "Vision", "图像拼接", "test_stitcher"
            )
            print("   ✓ 成功创建图像拼接工具实例")
            print(f"   实例: {tool_instance}")
        except Exception as e:
            print(f"   ✗ 创建工具实例失败: {e}")
    else:
        print("   ✗ 无法获取图像拼接工具类")


if __name__ == "__main__":
    test_tools_import()
