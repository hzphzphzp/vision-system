#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试上下方向图像拼接
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from data.image_data import ImageData

def test_vertical_stitching():
    """测试垂直方向拼接"""
    
    print("="*70)
    print("测试垂直方向图像拼接")
    print("="*70)
    
    # 尝试加载 C1 和 D1
    c1_path = "C1.jpg"
    d1_path = "D1.jpg"
    
    # 如果找不到，尝试其他路径
    if not os.path.exists(c1_path):
        c1_path = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\C1.bmp"
        d1_path = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\D1.bmp"
    
    print(f"\n加载图像:")
    print(f"  C1: {c1_path} - 存在: {os.path.exists(c1_path)}")
    print(f"  D1: {d1_path} - 存在: {os.path.exists(d1_path)}")
    
    if not os.path.exists(c1_path) or not os.path.exists(d1_path):
        print("\n找不到 C1/D1 图像，请确认路径")
        return
    
    img1 = cv2.imread(c1_path)
    img2 = cv2.imread(d1_path)
    
    print(f"\n图像尺寸:")
    print(f"  C1: {img1.shape[1]}x{img1.shape[0]}")
    print(f"  D1: {img2.shape[1]}x{img2.shape[0]}")
    
    # 方法1: 直接水平拼接（默认）
    print(f"\n[方法1] OpenCV Stitcher 默认模式")
    stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
    status, result1 = stitcher.stitch([img1, img2])
    
    if status == cv2.Stitcher_OK:
        print(f"  成功! 尺寸: {result1.shape[1]}x{result1.shape[0]}")
        cv2.imwrite("test_vertical_default.jpg", result1)
        
        # 检查黑线
        gray = cv2.cvtColor(result1, cv2.COLOR_BGR2GRAY)
        mid_y = result1.shape[0] // 2
        mid_region = gray[mid_y-20:mid_y+20, :]
        dark_ratio = np.sum(mid_region < 50) / mid_region.size
        print(f"  中间区域黑线比例: {dark_ratio:.2%}")
    else:
        print(f"  失败: {status}")
    
    # 方法2: 旋转90度后拼接，再转回来
    print(f"\n[方法2] 旋转90度后拼接")
    # 顺时针旋转90度
    img1_rot = cv2.rotate(img1, cv2.ROTATE_90_CLOCKWISE)
    img2_rot = cv2.rotate(img2, cv2.ROTATE_90_CLOCKWISE)
    
    status, result_rot = stitcher.stitch([img1_rot, img2_rot])
    
    if status == cv2.Stitcher_OK:
        # 逆时针旋转90度转回来
        result2 = cv2.rotate(result_rot, cv2.ROTATE_90_COUNTERCLOCKWISE)
        print(f"  成功! 尺寸: {result2.shape[1]}x{result2.shape[0]}")
        cv2.imwrite("test_vertical_rotated.jpg", result2)
        
        # 检查黑线
        gray = cv2.cvtColor(result2, cv2.COLOR_BGR2GRAY)
        mid_y = result2.shape[0] // 2
        mid_region = gray[mid_y-20:mid_y+20, :]
        dark_ratio = np.sum(mid_region < 50) / mid_region.size
        print(f"  中间区域黑线比例: {dark_ratio:.2%}")
    else:
        print(f"  失败: {status}")
    
    # 方法3: 尝试垂直扫描模式
    print(f"\n[方法3] SCANS 模式（垂直扫描）")
    try:
        stitcher_scan = cv2.Stitcher.create(cv2.Stitcher_SCANS)
        status, result3 = stitcher_scan.stitch([img1, img2])
        
        if status == cv2.Stitcher_OK:
            print(f"  成功! 尺寸: {result3.shape[1]}x{result3.shape[0]}")
            cv2.imwrite("test_vertical_scans.jpg", result3)
            
            # 检查黑线
            gray = cv2.cvtColor(result3, cv2.COLOR_BGR2GRAY)
            mid_y = result3.shape[0] // 2
            mid_region = gray[mid_y-20:mid_y+20, :]
            dark_ratio = np.sum(mid_region < 50) / mid_region.size
            print(f"  中间区域黑线比例: {dark_ratio:.2%}")
        else:
            print(f"  失败: {status}")
    except Exception as e:
        print(f"  不支持SCANS模式: {e}")
    
    print(f"\n" + "="*70)
    print("测试结果已保存到:")
    print("  - test_vertical_default.jpg (默认模式)")
    print("  - test_vertical_rotated.jpg (旋转模式)")
    print("  - test_vertical_scans.jpg (扫描模式)")
    print("="*70)

if __name__ == "__main__":
    test_vertical_stitching()
