#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI布局测试脚本

测试VisionMaster风格UI布局是否正确

Author: Vision System Team
Date: 2026-01-29
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.theme import get_style


def test_ui_layout():
    """测试UI布局"""
    print("=" * 60)
    print("VisionMaster风格UI布局测试")
    print("=" * 60)
    
    # 创建应用
    app = QApplication(sys.argv)
    
    try:
        # 创建主窗口
        print("\n1. 创建主窗口...")
        window = MainWindow()
        print("   ✓ 主窗口创建成功")
        
        # 检查主题样式
        print("\n2. 检查主题样式...")
        style = get_style("vision_master")
        if "background-color: #ffffff" in style:
            print("   ✓ 白色背景设置正确")
        else:
            print("   ✗ 白色背景设置不正确")
            
        if "color: #000000" in style:
            print("   ✓ 黑色字体设置正确")
        else:
            print("   ✗ 黑色字体设置不正确")
        
        # 检查窗口大小
        print("\n3. 检查窗口布局...")
        print(f"   窗口大小: {window.width()} x {window.height()}")
        
        # 检查关键组件是否存在
        print("\n4. 检查关键组件...")
        
        # 检查工具库
        if hasattr(window, 'tool_library_dock'):
            print("   ✓ 工具库组件存在")
        else:
            print("   ✗ 工具库组件缺失")
        
        # 检查算法视图
        if hasattr(window, 'algorithm_view'):
            print("   ✓ 算法编辑器存在")
        else:
            print("   ✗ 算法编辑器缺失")
        
        # 检查图像视图
        if hasattr(window, 'image_view'):
            print("   ✓ 图像显示区域存在")
        else:
            print("   ✗ 图像显示区域缺失")
        
        # 检查菜单栏
        menubar = window.menuBar()
        if menubar:
            print("   ✓ 菜单栏存在")
            # 检查菜单项
            menus = [menu.title() for menu in menubar.actions() if menu.menu()]
            print(f"   菜单项: {menus}")
        else:
            print("   ✗ 菜单栏缺失")
        
        # 检查工具栏
        toolbars = window.findChildren(type(window.toolBar()))
        if toolbars:
            print("   ✓ 工具栏存在")
        else:
            print("   ✗ 工具栏缺失")
        
        # 检查状态栏
        statusbar = window.statusBar()
        if statusbar:
            print("   ✓ 状态栏存在")
        else:
            print("   ✗ 状态栏缺失")
        
        print("\n5. 显示窗口...")
        window.show()
        print("   ✓ 窗口显示成功")
        
        print("\n" + "=" * 60)
        print("UI布局测试完成!")
        print("=" * 60)
        print("\n提示: 窗口已显示，请检查:")
        print("  1. 左侧工具库是否正确显示")
        print("  2. 中间算法编辑器区域是否正确")
        print("  3. 右侧图像显示和结果面板是否正确")
        print("  4. 背景是否为白色，字体是否为黑色")
        print("  5. 菜单栏和工具栏是否正常")
        print("\n按 Ctrl+C 或关闭窗口退出测试")
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    test_ui_layout()
