#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动参数优化脚本 - 针对您的具体图像进行优化
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
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法加载: {image_path}")
    h, w = img.shape[:2]
    return ImageData(data=img, width=w, height=h, channels=3)


def auto_stitch(img1_path, img2_path, output_path="result.jpg"):
    """
    自动拼接 - 智能选择最佳参数
    """
    print(f"正在自动拼接...")
    print(f"  图像1: {img1_path}")
    print(f"  图像2: {img2_path}")
    
    # 加载图像
    img1 = load_image(img1_path)
    img2 = load_image(img2_path)
    
    # 尝试多种参数组合
    configs = [
        {
            "name": "保守配置",
            "params": {
                "feature_detector": "SIFT",
                "matcher_type": "BFM", 
                "min_match_count": 20,
                "ransac_reproj_threshold": 0.8,
                "blend_method": "feather",
                "blend_strength": 1,
            }
        },
        {
            "name": "平衡配置",
            "params": {
                "feature_detector": "SIFT",
                "matcher_type": "BFM",
                "min_match_count": 15,
                "ransac_reproj_threshold": 1.0,
                "blend_method": "feather",
                "blend_strength": 2,
            }
        },
        {
            "name": "快速配置",
            "params": {
                "feature_detector": "ORB",
                "matcher_type": "BFM",
                "min_match_count": 12,
                "ransac_reproj_threshold": 1.5,
                "blend_method": "feather",
                "blend_strength": 2,
            }
        }
    ]
    
    best_result = None
    best_score = float('inf')
    
    stitcher = ImageStitchingTool()
    
    for config in configs:
        print(f"\n尝试: {config['name']}")
        stitcher.set_parameters(config['params'])
        
        result = stitcher.process([img1, img2])
        
        if result.status:
            stitched = result.get_image("stitched_image")
            
            # 评估质量
            score = evaluate_quality(stitched.data)
            print(f"  质量得分: {score:.2f} (越低越好)")
            
            if score < best_score:
                best_score = score
                best_result = stitched
                print(f"  ✓ 当前最佳")
    
    if best_result:
        # 保存最佳结果
        cv2.imwrite(output_path, best_result.data)
        print(f"\n最佳结果已保存: {output_path}")
        print(f"最终质量得分: {best_score:.2f}")
        return best_result
    else:
        print("所有配置都失败了")
        return None


def evaluate_quality(image):
    """
    评估拼接质量
    检测边缘密度和亮度一致性
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # 1. 检测中间区域的边缘密度
    mid_start = w // 3
    mid_end = 2 * w // 3
    mid_region = gray[:, mid_start:mid_end]
    
    edges = cv2.Canny(mid_region, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # 2. 检测亮度均匀性
    left_half = gray[:, :w//2]
    right_half = gray[:, w//2:]
    brightness_diff = abs(np.mean(left_half) - np.mean(right_half))
    
    # 综合得分（越低越好）
    score = edge_density * 100 + brightness_diff * 0.1
    
    return score


if __name__ == "__main__":
    # 使用您的图像路径
    img1 = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A1.jpg"
    img2 = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A2.jpg"
    
    # 检查文件是否存在
    if not os.path.exists(img1) or not os.path.exists(img2):
        print("文件路径不存在，请确认路径正确")
        print(f"  A1: {os.path.exists(img1)}")
        print(f"  A2: {os.path.exists(img2)}")
    else:
        # 尝试两种顺序
        print("="*60)
        print("顺序1: A1 -> A2")
        print("="*60)
        result1 = auto_stitch(img1, img2, "result_A1_A2.jpg")
        
        print("\n" + "="*60)
        print("顺序2: A2 -> A1")
        print("="*60)
        result2 = auto_stitch(img2, img1, "result_A2_A1.jpg")
        
        print("\n" + "="*60)
        print("拼接完成！")
        print("="*60)
        print("请查看生成的结果文件，选择最佳效果")
