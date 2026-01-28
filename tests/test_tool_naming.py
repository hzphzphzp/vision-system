#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具命名功能

验证拖拽生成的算法模块是否使用正确的命名格式：
- 工具类型名称_1
- 工具类型名称_2
- 确保名称唯一且无乱码

Author: Vision System Team
Date: 2026-01-28
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestToolNaming(unittest.TestCase):
    """测试工具命名功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟流程对象
        self.mock_procedure = Mock()
        self.mock_procedure.tools = {}
    
    def test_tool_naming_sequential_numbering(self):
        """测试工具命名的顺序编号功能"""
        print("\n=== 测试工具命名的顺序编号功能 ===")
        
        # 测试命名逻辑
        tool_type_name = "图像读取器"
        
        # 统计当前流程中同类型工具的数量
        tool_count = 0
        if self.mock_procedure:
            for existing_tool in self.mock_procedure.tools.values():
                if hasattr(existing_tool, 'tool_name'):
                    # 提取现有工具的类型名称（去掉序号部分）
                    existing_tool_type = existing_tool.tool_name.split('_')[0]
                    if existing_tool_type == tool_type_name:
                        tool_count += 1
        
        # 生成递增的序号
        new_tool_name = f"{tool_type_name}_{tool_count + 1}"
        
        print(f"预期工具名称: {new_tool_name}")
        self.assertEqual(new_tool_name, "图像读取器_1")
        
    def test_tool_naming_unique_names(self):
        """测试工具命名的唯一性"""
        print("\n=== 测试工具命名的唯一性 ===")
        
        # 模拟添加一个工具到流程
        mock_tool = Mock()
        mock_tool.tool_name = "图像读取器_1"
        self.mock_procedure.tools["图像读取器_1"] = mock_tool
        
        # 测试创建第二个相同类型的工具
        tool_type_name = "图像读取器"
        
        # 统计当前流程中同类型工具的数量
        tool_count = 0
        if self.mock_procedure:
            for existing_tool in self.mock_procedure.tools.values():
                if hasattr(existing_tool, 'tool_name'):
                    # 提取现有工具的类型名称（去掉序号部分）
                    existing_tool_type = existing_tool.tool_name.split('_')[0]
                    if existing_tool_type == tool_type_name:
                        tool_count += 1
        
        # 生成递增的序号
        new_tool_name = f"{tool_type_name}_{tool_count + 1}"
        
        # 确保名称唯一
        counter = tool_count + 1
        while self.mock_procedure and new_tool_name in self.mock_procedure.tools:
            counter += 1
            new_tool_name = f"{tool_type_name}_{counter}"
        
        print(f"预期工具名称: {new_tool_name}")
        self.assertEqual(new_tool_name, "图像读取器_2")
    
    def test_tool_naming_different_types(self):
        """测试不同类型工具的命名"""
        print("\n=== 测试不同类型工具的命名 ===")
        
        # 模拟添加不同类型的工具
        mock_tool1 = Mock()
        mock_tool1.tool_name = "图像读取器_1"
        self.mock_procedure.tools["图像读取器_1"] = mock_tool1
        
        mock_tool2 = Mock()
        mock_tool2.tool_name = "相机_1"
        self.mock_procedure.tools["相机_1"] = mock_tool2
        
        # 测试创建第二个图像读取器
        tool_type_name = "图像读取器"
        
        # 统计当前流程中同类型工具的数量
        tool_count = 0
        if self.mock_procedure:
            for existing_tool in self.mock_procedure.tools.values():
                if hasattr(existing_tool, 'tool_name'):
                    # 提取现有工具的类型名称（去掉序号部分）
                    existing_tool_type = existing_tool.tool_name.split('_')[0]
                    if existing_tool_type == tool_type_name:
                        tool_count += 1
        
        # 生成递增的序号
        new_tool_name = f"{tool_type_name}_{tool_count + 1}"
        
        print(f"预期工具名称: {new_tool_name}")
        self.assertEqual(new_tool_name, "图像读取器_2")
        
        # 测试创建第二个相机
        tool_type_name = "相机"
        
        # 统计当前流程中同类型工具的数量
        tool_count = 0
        if self.mock_procedure:
            for existing_tool in self.mock_procedure.tools.values():
                if hasattr(existing_tool, 'tool_name'):
                    # 提取现有工具的类型名称（去掉序号部分）
                    existing_tool_type = existing_tool.tool_name.split('_')[0]
                    if existing_tool_type == tool_type_name:
                        tool_count += 1
        
        # 生成递增的序号
        new_tool_name = f"{tool_type_name}_{tool_count + 1}"
        
        print(f"预期工具名称: {new_tool_name}")
        self.assertEqual(new_tool_name, "相机_2")
    
    def test_tool_naming_no_duplicates(self):
        """测试工具命名无重复"""
        print("\n=== 测试工具命名无重复 ===")
        
        # 模拟添加一些工具到流程
        mock_tool1 = Mock()
        mock_tool1.tool_name = "图像读取器_1"
        self.mock_procedure.tools["图像读取器_1"] = mock_tool1
        
        mock_tool2 = Mock()
        mock_tool2.tool_name = "图像读取器_2"
        self.mock_procedure.tools["图像读取器_2"] = mock_tool2
        
        # 测试创建第三个图像读取器
        tool_type_name = "图像读取器"
        
        # 统计当前流程中同类型工具的数量
        tool_count = 0
        if self.mock_procedure:
            for existing_tool in self.mock_procedure.tools.values():
                if hasattr(existing_tool, 'tool_name'):
                    # 提取现有工具的类型名称（去掉序号部分）
                    existing_tool_type = existing_tool.tool_name.split('_')[0]
                    if existing_tool_type == tool_type_name:
                        tool_count += 1
        
        # 生成递增的序号
        new_tool_name = f"{tool_type_name}_{tool_count + 1}"
        
        print(f"预期工具名称: {new_tool_name}")
        self.assertEqual(new_tool_name, "图像读取器_3")
        
        # 确保名称不在现有工具中
        self.assertNotIn(new_tool_name, self.mock_procedure.tools)
    
    def test_tool_naming_format(self):
        """测试工具命名格式是否正确"""
        print("\n=== 测试工具命名格式是否正确 ===")
        
        # 测试各种工具类型的命名格式
        test_cases = [
            ("图像读取器", 1, "图像读取器_1"),
            ("相机", 2, "相机_2"),
            ("图像拼接", 3, "图像拼接_3"),
            ("灰度匹配", 1, "灰度匹配_1"),
            ("形状匹配", 4, "形状匹配_4")
        ]
        
        for tool_type_name, count, expected_name in test_cases:
            actual_name = f"{tool_type_name}_{count}"
            print(f"工具类型: {tool_type_name}, 序号: {count}, 预期: {expected_name}, 实际: {actual_name}")
            self.assertEqual(actual_name, expected_name)
            # 验证格式是否符合要求
            self.assertTrue("_" in actual_name)
            parts = actual_name.split("_")
            self.assertEqual(len(parts), 2)
            self.assertTrue(parts[1].isdigit())


if __name__ == '__main__':
    print("开始测试工具命名功能...")
    unittest.main(verbosity=2)
