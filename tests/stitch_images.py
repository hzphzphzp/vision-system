#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接测试脚本 - 使用命令行参数指定图像路径
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool


def load_image(image_path):
    """加载图像"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"找不到文件: {image_path}")
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")
    h, w = img.shape[:2]
    print(f"  加载成功: {w}x{h}")
    return ImageData(data=img, width=w, height=h, channels=3)


def stitch_images(img1_path, img2_path, output_name="result"):
    """拼接两张图像"""
    print(f"\n正在拼接...")
    print(f"  图像1: {img1_path}")
    print(f"  图像2: {img2_path}")
    
    try:
        img1 = load_image(img1_path)
        img2 = load_image(img2_path)
    except Exception as e:
        print(f"加载图像失败: {e}")
        return False
    
    # 创建拼接工具并设置参数
    stitcher = ImageStitchingTool()
    
    # 使用针对您图像优化的参数
    stitcher.set_parameters({
        "feature_detector": "SIFT",
        "matcher_type": "BFM",
        "min_match_count": 15,
        "ransac_reproj_threshold": 1.0,  # 严格的几何约束
        "blend_method": "feather",
        "blend_strength": 1,             # 低融合强度，减少重影
    })
    
    # 执行拼接
    result = stitcher.process([img1, img2])
    
    if result.status:
        stitched = result.get_image("stitched_image")
        output_path = f"{output_name}.jpg"
        cv2.imwrite(output_path, stitched.data)
        print(f"  [OK] 成功! 保存到: {output_path}")
        print(f"  尺寸: {stitched.width}x{stitched.height}")
        return True
    else:
        print(f"  [FAIL] 失败: {result.message}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("图像拼接工具")
    print("="*60)
    
    # 检查命令行参数
    if len(sys.argv) >= 3:
        img1_path = sys.argv[1]
        img2_path = sys.argv[2]
    else:
        # 使用默认路径（请修改为您的实际路径）
        print("\n用法: python stitch_images.py <图像1路径> <图像2路径>")
        print("\n例如:")
        print(r'  python stitch_images.py "E:\images\A1.jpg" "E:\images\A2.jpg"')
        print("\n或者先复制图像到当前目录:")
        print(r'  copy "E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A1.jpg" .')
        print(r'  copy "E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A2.jpg" .')
        print("\n然后运行:")
        print("  python stitch_images.py A1.jpg A2.jpg")
        
        # 尝试在当前目录查找
        if os.path.exists("A1.jpg") and os.path.exists("A2.jpg"):
            print("\n找到当前目录的 A1.jpg 和 A2.jpg，使用这些文件...")
            img1_path = "A1.jpg"
            img2_path = "A2.jpg"
        else:
            return
    
    # 尝试两种顺序
    print("\n" + "="*60)
    print("顺序1: 图像1 -> 图像2")
    print("="*60)
    success1 = stitch_images(img1_path, img2_path, "result_1_2")
    
    print("\n" + "="*60)
    print("顺序2: 图像2 -> 图像1")
    print("="*60)
    success2 = stitch_images(img2_path, img1_path, "result_2_1")
    
    print("\n" + "="*60)
    print("完成!")
    print("="*60)
    if success1 or success2:
        print("结果文件:")
        if success1:
            print("  - result_1_2.jpg")
        if success2:
            print("  - result_2_1.jpg")
        print("\n请查看结果，选择最佳效果")
    else:
        print("拼接失败，请检查图像是否正确")


if __name__ == "__main__":
    main()
