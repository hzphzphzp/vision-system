#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试算法工具位置偏移问题

验证不同数量工具下的位置稳定性，测试场景需覆盖1-20个工具的极端情况。
"""

import os
import sys
import time

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QApplication

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_filter import BoxFilter
from tools.image_source import ImageSource
from tools.image_stitching import ImageStitchingTool
from ui.main_window import MainWindow

# 测试工具类型
TEST_TOOLS = ["图像源", "图像滤波", "图像拼接", "灰度匹配", "形状匹配"]

# 测试工具数量范围
MIN_TOOLS = 1
MAX_TOOLS = 20


def setup_test_environment():
    """设置测试环境"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    return app


def test_tool_position_stability():
    """测试工具位置稳定性"""
    print("=== 开始测试工具位置稳定性 ===")

    # 设置测试环境
    app = setup_test_environment()

    try:
        # 创建主窗口实例
        main_window = MainWindow()

        # 隐藏窗口
        main_window.hide()

        # 测试不同数量的工具
        for tool_count in range(MIN_TOOLS, MAX_TOOLS + 1):
            print(f"\n=== 测试工具数量: {tool_count} ===")

            # 清空现有工具
            main_window.tool_items.clear()
            main_window.algorithm_scene.clear()

            # 记录所有工具的位置
            tool_positions = []

            # 添加工具
            for i in range(tool_count):
                # 选择工具类型
                tool_type = TEST_TOOLS[i % len(TEST_TOOLS)]

                # 计算工具位置
                x = 100 + (i % 5) * 200
                y = 100 + (i // 5) * 200
                position = QPointF(x, y)

                print(
                    f"  添加工具 {i+1}/{tool_count}: {tool_type} 到位置 ({x}, {y})"
                )

                # 添加工具到编辑器
                main_window._create_tool_on_editor(tool_type, position)

                # 记录位置
                tool_positions.append((tool_type, position))

            # 验证工具位置
            verify_tool_positions(main_window, tool_positions)

            # 测试删除工具
            if tool_count > 1:
                test_tool_deletion(main_window, tool_count)

        print("\n=== 测试完成 ===")

    finally:
        # 清理资源
        app.quit()


def verify_tool_positions(main_window, expected_positions):
    """验证工具位置"""
    print(f"  验证 {len(expected_positions)} 个工具的位置...")

    # 获取实际工具位置
    actual_positions = []
    for tool_name, tool_item in main_window.tool_items.items():
        actual_pos = tool_item.pos()
        actual_positions.append((tool_name, actual_pos))

    print(f"  预期工具数: {len(expected_positions)}")
    print(f"  实际工具数: {len(actual_positions)}")

    # 检查工具数量是否正确
    if len(expected_positions) != len(actual_positions):
        print(f"  ❌ 工具数量不一致")
        return

    # 检查位置偏移
    max_offset = 0
    for i, (expected_tool, expected_pos) in enumerate(expected_positions):
        if i < len(actual_positions):
            actual_tool, actual_pos = actual_positions[i]

            # 计算偏移量
            offset_x = abs(actual_pos.x() - expected_pos.x())
            offset_y = abs(actual_pos.y() - expected_pos.y())
            total_offset = (offset_x**2 + offset_y**2) ** 0.5

            if total_offset > max_offset:
                max_offset = total_offset

            print(
                f"  工具 {i+1}: 预期位置 ({expected_pos.x():.1f}, {expected_pos.y():.1f}), 实际位置 ({actual_pos.x():.1f}, {actual_pos.y():.1f}), 偏移量: {total_offset:.2f} 像素"
            )

    # 验证偏移量是否在可接受范围内
    if max_offset <= 1:
        print(f"  ✅ 所有工具位置偏移量均在可接受范围内 (≤1像素)")
    else:
        print(
            f"  ❌ 工具位置偏移量超出可接受范围 (最大偏移: {max_offset:.2f} 像素)"
        )


def test_tool_deletion(main_window, tool_count):
    """测试工具删除"""
    print(f"  测试删除工具...")

    # 记录删除前的工具数量
    before_count = len(main_window.tool_items)

    # 删除第一个工具
    if main_window.tool_items:
        first_tool_name = list(main_window.tool_items.keys())[0]
        first_tool_item = main_window.tool_items[first_tool_name]

        print(f"  删除工具: {first_tool_name}")

        # 删除工具
        main_window.algorithm_scene.remove_tool(first_tool_item)

        # 记录删除后的工具数量
        after_count = len(main_window.tool_items)

        print(f"  删除前工具数: {before_count}")
        print(f"  删除后工具数: {after_count}")

        if after_count == before_count - 1:
            print(f"  ✅ 工具删除成功")
        else:
            print(f"  ❌ 工具删除失败")


if __name__ == "__main__":
    try:
        test_tool_position_stability()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
