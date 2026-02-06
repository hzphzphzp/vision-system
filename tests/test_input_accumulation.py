#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控图像拼接工具的输入数据累积问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import cv2
from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool

# 设置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_stitching_accumulation():
    """测试输入数据累积问题"""
    
    print("="*70)
    print("测试图像拼接工具的输入数据累积")
    print("="*70)
    
    # 创建工具实例
    stitcher = ImageStitchingTool()
    
    # 加载测试图像
    img1 = ImageData(data=cv2.imread('A1.jpg'))
    img2 = ImageData(data=cv2.imread('A2.jpg'))
    
    print(f"\n[测试1] 模拟连接2个输入端口的情况")
    print("-"*70)
    
    # 模拟第一次运行 - 连接第一个端口
    print("\n1. 调用 set_input(img1, 'InputImage') - 第一个端口")
    stitcher.set_input(img1, "InputImage")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    # 模拟第一次运行 - 连接第二个端口
    print("\n2. 调用 set_input(img2, 'InputImage') - 第二个端口")
    stitcher.set_input(img2, "InputImage")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    # 模拟运行
    print("\n3. 执行 process()")
    result = stitcher.process(stitcher._input_data_list)
    print(f"   输入图像数量: {len(stitcher._input_data_list)}")
    print(f"   处理结果: {'成功' if result.status else '失败'}")
    
    print(f"\n[测试2] 模拟第二次运行（问题复现）")
    print("-"*70)
    
    # 问题：如果不清理 _input_data_list，第二次运行会累积
    print("\n4. 再次调用 set_input(img1, 'InputImage') - 第一次运行后未清理")
    stitcher.set_input(img1, "InputImage")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    print("\n5. 再次调用 set_input(img2, 'InputImage')")
    stitcher.set_input(img2, "InputImage")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    print("\n6. 再次执行 process()")
    result = stitcher.process(stitcher._input_data_list)
    print(f"   输入图像数量: {len(stitcher._input_data_list)}")
    print(f"   处理结果: {'成功' if result.status else '失败'}")
    
    print(f"\n[问题分析]")
    print("-"*70)
    print(f"期望: 每次运行应该处理2张图像")
    print(f"实际: 第二次运行处理了 {len(stitcher._input_data_list)} 张图像")
    print(f"\n原因: _input_data_list 在每次运行后没有被清空")
    print(f"解决: 需要在 process() 成功后清空 _input_data_list")
    
    print(f"\n[测试3] 修复后的行为")
    print("-"*70)
    
    # 手动清空列表（修复方法）
    stitcher._input_data_list.clear()
    print("\n7. 清空 _input_data_list")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    stitcher.set_input(img1, "InputImage")
    stitcher.set_input(img2, "InputImage")
    print(f"\n8. 重新输入2张图像")
    print(f"   _input_data_list 长度: {len(stitcher._input_data_list)}")
    
    result = stitcher.process(stitcher._input_data_list)
    print(f"\n9. 执行 process()")
    print(f"   输入图像数量: {len(stitcher._input_data_list)}")
    print(f"   处理结果: {'成功' if result.status else '失败'}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_stitching_accumulation()
