#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的图像拼接工具功能
"""

import sys
import os
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.tool_base import ToolRegistry
from data.image_data import ImageData

# 测试修复后的图像拼接工具
def test_image_stitching_fix():
    print("=== 测试修复后的图像拼接工具 ===")
    
    # 导入工具模块
    print("\n1. 导入工具模块")
    try:
        import tools.image_stitching
        print("   ✓ 成功导入 tools.image_stitching 模块")
    except Exception as e:
        print(f"   ✗ 导入模块失败: {e}")
        return
    
    # 创建工具实例
    print("\n2. 创建工具实例")
    try:
        stitcher = ToolRegistry.create_tool("Vision", "图像拼接", "test_stitcher")
        print(f"   ✓ 成功创建工具实例: {stitcher.name}")
    except Exception as e:
        print(f"   ✗ 创建工具实例失败: {e}")
        return
    
    # 测试参数设置和获取
    print("\n3. 测试参数设置和获取")
    
    # 获取默认参数
    default_params = stitcher.get_parameters()
    print("   默认参数:")
    for key, value in default_params.items():
        print(f"     {key}: {value}")
    
    # 测试设置参数
    test_params = {
        "feature_detector": "ORB",
        "min_match_count": 15,
        "blend_method": "feather"
    }
    
    stitcher.set_parameters(test_params)
    updated_params = stitcher.get_parameters()
    print("   更新后参数:")
    for key, value in test_params.items():
        if updated_params.get(key) == value:
            print(f"     ✓ {key}: {value}")
        else:
            print(f"     ✗ {key}: 期望 {value}, 实际 {updated_params.get(key)}")
    
    # 测试_run_impl方法
    print("\n4. 测试_run_impl方法")
    
    # 创建测试图像
    test_data = np.zeros((100, 100, 3), dtype=np.uint8)
    test_data[25:75, 25:75] = [0, 255, 0]  # 绿色方块
    test_image = ImageData(data=test_data)
    
    # 设置输入数据
    stitcher.set_input(test_image)
    
    # 执行_run_impl
    output = stitcher._run_impl()
    
    if output is not None:
        print("   ✓ _run_impl方法返回结果")
        if isinstance(output, dict) and "OutputImage" in output:
            print("   ✓ 返回包含OutputImage的字典")
            output_image = output["OutputImage"]
            if output_image.is_valid:
                print(f"   ✓ 输出图像有效: {output_image.width}x{output_image.height}")
            else:
                print("   ✗ 输出图像无效")
        else:
            print("   ✗ 返回格式不正确")
    else:
        print("   ✗ _run_impl方法返回None")
    
    # 测试参数定义
    print("\n5. 测试参数定义")
    if hasattr(stitcher, 'PARAM_DEFINITIONS'):
        print("   ✓ 工具包含PARAM_DEFINITIONS")
        print(f"   参数定义数量: {len(stitcher.PARAM_DEFINITIONS)}")
        for param_name, param_def in stitcher.PARAM_DEFINITIONS.items():
            if "name" in param_def and "description" in param_def:
                print(f"     ✓ {param_name}: {param_def['name']}")
            else:
                print(f"     ✗ {param_name}: 缺少名称或描述")
    else:
        print("   ✗ 工具缺少PARAM_DEFINITIONS")
    
    # 测试工具信息
    print("\n6. 测试工具信息")
    info = stitcher.get_info()
    print(f"   工具名称: {info.get('name')}")
    print(f"   工具描述: {info.get('description')}")
    print(f"   工具版本: {info.get('version')}")
    print(f"   输入类型: {info.get('input_types')}")
    print(f"   输出类型: {info.get('output_types')}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_image_stitching_fix()
