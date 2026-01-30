#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多个图像读取器组件的独立性
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入工具模块
import tools.image_source
from core.procedure import Procedure
from core.tool_base import ToolRegistry


# 测试多个图像读取器的独立性
def test_multiple_image_readers():
    print("=== 测试多个图像读取器组件的独立性 ===")

    # 创建流程
    procedure = Procedure("测试流程")

    # 创建第一个图像读取器
    print("\n1. 创建第一个图像读取器")
    reader1 = ToolRegistry.create_tool(
        "ImageSource", "图像读取器", "image_reader_1"
    )
    reader1.set_param("file_path", "data/images/test_image_1.jpg")
    procedure.add_tool(reader1)
    print(f"   创建成功: {reader1._name}")
    print(f"   文件路径: {reader1.get_param('file_path')}")

    # 创建第二个图像读取器
    print("\n2. 创建第二个图像读取器")
    reader2 = ToolRegistry.create_tool(
        "ImageSource", "图像读取器", "image_reader_2"
    )
    reader2.set_param("file_path", "data/images/test_image_2.jpg")
    procedure.add_tool(reader2)
    print(f"   创建成功: {reader2._name}")
    print(f"   文件路径: {reader2.get_param('file_path')}")

    # 验证两个读取器的参数是否独立
    print("\n3. 验证参数独立性")
    print(f"   读取器1文件路径: {reader1.get_param('file_path')}")
    print(f"   读取器2文件路径: {reader2.get_param('file_path')}")

    if reader1.get_param("file_path") != reader2.get_param("file_path"):
        print("   ✅ 测试通过: 两个图像读取器的参数是独立的")
    else:
        print("   ❌ 测试失败: 两个图像读取器的参数相同，存在共享问题")

    # 测试修改一个读取器的参数是否会影响另一个
    print("\n4. 测试参数修改的独立性")
    print("   修改读取器1的文件路径...")
    reader1.set_param("file_path", "modified_test_image_1.jpg")

    print(f"   读取器1文件路径: {reader1.get_param('file_path')}")
    print(f"   读取器2文件路径: {reader2.get_param('file_path')}")

    if reader1.get_param("file_path") != reader2.get_param("file_path"):
        print("   ✅ 测试通过: 修改一个读取器的参数不会影响另一个")
    else:
        print("   ❌ 测试失败: 修改一个读取器的参数影响了另一个")

    # 测试流程中的工具管理
    print("\n5. 测试流程中的工具管理")
    print(f"   流程中的工具数量: {procedure.tool_count}")
    print(
        f"   流程中的工具: {[tool._name for tool in procedure._tools.values()]}"
    )

    # 验证两个工具都在流程中
    if len(procedure._tools) == 2:
        print("   ✅ 测试通过: 两个图像读取器都成功添加到流程中")
    else:
        print("   ❌ 测试失败: 流程中的工具数量不正确")

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_multiple_image_readers()
