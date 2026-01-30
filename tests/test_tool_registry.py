#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具注册表测试

用于验证所有工具是否都被正确注册到ToolRegistry中。

Usage:
    python tests/test_tool_registry.py
    pytest tests/test_tool_registry.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools
from core.tool_base import ToolRegistry


def test_tool_registry():
    """测试工具注册表"""
    print("=" * 60)
    print("工具注册表测试")
    print("=" * 60)

    all_tools = ToolRegistry.get_all_tools()

    print(f"\n已注册的工具总数: {len(all_tools)}")
    print("=" * 60)

    categories = ToolRegistry.get_categories()
    print(f"工具类别数量: {len(categories)}")
    print(f"工具类别: {categories}")
    print("=" * 60)

    for category in sorted(categories):
        print(f"\n【{category}】")
        category_tools = ToolRegistry.get_tools_by_category(category)
        print(f"  类别工具数: {len(category_tools)}")

        for tool_key, tool_class in sorted(category_tools.items()):
            print(f"  - {tool_class.tool_name} ({tool_key})")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    print("\n验证工具创建:")
    print("=" * 60)

    test_tools = [
        ("ImageSource", "相机"),
        ("ImageFilter", "高斯滤波"),
        ("Vision", "灰度匹配"),
        ("Recognition", "二维码识别"),
    ]

    for category, name in test_tools:
        try:
            tool = ToolRegistry.create_tool(category, name, f"测试_{name}")
            print(f"✅ {category}.{name} - 创建成功")
            print(f"    工具实例: {tool}")
        except Exception as e:
            print(f"❌ {category}.{name} - 创建失败: {e}")

    print("\n" + "=" * 60)
    print("工具注册表测试完成")
    print("=" * 60)


def test_tool_categories():
    """测试工具类别获取"""
    categories = ToolRegistry.get_categories()
    assert len(categories) > 0, "应该有一些工具类别"
    print(f"✅ 工具类别测试通过: {categories}")


def test_tool_creation():
    """测试工具创建"""
    try:
        tool = ToolRegistry.create_tool("ImageSource", "相机", "测试相机")
        assert tool is not None
        print("✅ 工具创建测试通过")
    except Exception as e:
        print(f"❌ 工具创建测试失败: {e}")
        raise


if __name__ == "__main__":
    test_tool_registry()
