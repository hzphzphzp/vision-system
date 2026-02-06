#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图像拼接工具的数据流
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool

def test_data_flow():
    """测试数据流"""
    
    print("="*70)
    print("测试图像拼接工具数据流")
    print("="*70)
    
    # 创建工具实例
    stitcher = ImageStitchingTool()
    
    # 加载测试图像
    img1 = cv2.imread('A1.jpg')
    img2 = cv2.imread('A2.jpg')
    
    if img1 is None or img2 is None:
        print("错误: 找不到测试图像 A1.jpg 或 A2.jpg")
        return
    
    img1_data = ImageData(data=img1)
    img2_data = ImageData(data=img2)
    
    print(f"\n[步骤1] 模拟图像源工具执行并输出")
    print(f"  图像1: {img1_data.width}x{img1_data.height}")
    print(f"  图像2: {img2_data.width}x{img2_data.height}")
    
    print(f"\n[步骤2] 模拟数据传递到拼接工具")
    print(f"  调用 set_input(img1)")
    stitcher.set_input(img1_data, "InputImage")
    
    print(f"  调用 set_input(img2)")
    stitcher.set_input(img2_data, "InputImage")
    
    print(f"\n[步骤3] 检查输入数据状态")
    print(f"  _input_data: {stitcher._input_data is not None}")
    print(f"  _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    if hasattr(stitcher, '_input_data_list') and len(stitcher._input_data_list) >= 2:
        print(f"\n[步骤4] 执行拼接")
        result = stitcher._run_impl()
        
        if result and "OutputImage" in result:
            output = result["OutputImage"]
            print(f"  拼接成功! 输出尺寸: {output.width}x{output.height}")
        else:
            print(f"  拼接失败或无输出")
    else:
        print(f"\n[错误] 输入数据不足!")
        print(f"  期望: 至少2张图像")
        print(f"  实际: {len(stitcher._input_data_list) if hasattr(stitcher, '_input_data_list') else 0}张")
        print(f"\n  可能原因:")
        print(f"    1. set_input 没有被正确调用")
        print(f"    2. 连接线没有正确建立")
        print(f"    3. 上游工具没有输出数据")

if __name__ == "__main__":
    test_data_flow()
