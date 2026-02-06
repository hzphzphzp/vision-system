#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像拼接重影问题诊断和测试脚本

用于测试和诊断实际图像的拼接效果
"""

import os
import sys
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool


def load_image(image_path):
    """加载图像文件"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法加载图像: {image_path}")
    h, w = img.shape[:2]
    return ImageData(data=img, width=w, height=h, channels=3)


def save_debug_image(image_data, filename):
    """保存调试图像"""
    if isinstance(image_data, ImageData):
        cv2.imwrite(filename, image_data.data)
    else:
        cv2.imwrite(filename, image_data)
    print(f"已保存: {filename}")


def test_stitching(img1_path, img2_path, output_prefix="test"):
    """测试图像拼接"""
    print(f"\n{'='*60}")
    print(f"测试拼接: {img1_path} + {img2_path}")
    print(f"{'='*60}")
    
    # 加载图像
    try:
        img1 = load_image(img1_path)
        img2 = load_image(img2_path)
        print(f"图像1尺寸: {img1.width}x{img1.height}")
        print(f"图像2尺寸: {img2.width}x{img2.height}")
    except Exception as e:
        print(f"加载图像失败: {e}")
        return None
    
    # 创建拼接工具
    stitcher = ImageStitchingTool()
    
    # 测试不同参数配置
    configs = [
        {
            "name": "当前默认配置",
            "params": {
                "feature_detector": "ORB",
                "matcher_type": "BFM",
                "min_match_count": 8,
                "ransac_reproj_threshold": 2.0,
                "blend_method": "feather",
                "blend_strength": 3,
            }
        },
        {
            "name": "高质量配置",
            "params": {
                "feature_detector": "SIFT",
                "matcher_type": "BFM",
                "min_match_count": 15,
                "ransac_reproj_threshold": 1.5,
                "blend_method": "feather",
                "blend_strength": 2,
            }
        },
        {
            "name": "严格RANSAC配置",
            "params": {
                "feature_detector": "ORB",
                "matcher_type": "BFM",
                "min_match_count": 12,
                "ransac_reproj_threshold": 1.0,  # 更严格
                "blend_method": "feather",
                "blend_strength": 2,
            }
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"\n--- 测试配置: {config['name']} ---")
        
        # 设置参数
        stitcher.set_parameters(config['params'])
        
        # 执行拼接
        result = stitcher.process([img1, img2])
        
        if result.status:
            print(f"✓ 拼接成功")
            print(f"  输出尺寸: {result.get_value('stitched_width')}x{result.get_value('stitched_height')}")
            print(f"  处理时间: {result.get_value('processing_time'):.2f}秒")
            
            # 保存结果
            stitched_img = result.get_image("stitched_image")
            output_file = f"{output_prefix}_{config['name'].replace(' ', '_')}.jpg"
            save_debug_image(stitched_img, output_file)
            results.append((config['name'], stitched_img, result))
        else:
            print(f"✗ 拼接失败: {result.message}")
    
    return results


def detect_ghosting_visual(image_data, output_prefix="ghost_analysis"):
    """可视化检测重影并保存分析图"""
    if isinstance(image_data, ImageData):
        img = image_data.data
    else:
        img = image_data
    
    h, w = img.shape[:2]
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. 边缘检测
    edges = cv2.Canny(gray, 50, 150)
    
    # 2. 局部方差（检测重影区域）
    kernel_size = 31
    local_mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
    local_var = cv2.blur((gray.astype(np.float32) - local_mean) ** 2, (kernel_size, kernel_size))
    
    # 归一化用于显示
    local_var_norm = cv2.normalize(local_var, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # 3. 高频成分
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude = np.log(np.abs(fshift) + 1)
    magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # 计算重影得分
    edge_density = np.sum(edges > 0) / (h * w)
    high_var_ratio = np.sum(local_var > np.percentile(local_var, 90)) / (h * w)
    
    ghost_score = (edge_density * 100 + high_var_ratio * 100) / 2
    has_ghosting = ghost_score > 50
    
    # 创建可视化结果
    fig = np.zeros((h*2, w*2, 3), dtype=np.uint8)
    
    # 原图
    fig[0:h, 0:w] = img
    cv2.putText(fig, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 边缘图
    fig[0:h, w:2*w] = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cv2.putText(fig, "Edges", (w+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 局部方差
    fig[h:2*h, 0:w] = cv2.cvtColor(local_var_norm, cv2.COLOR_GRAY2BGR)
    cv2.putText(fig, "Local Variance", (10, h+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 频谱
    fig[h:2*h, w:2*w] = cv2.cvtColor(magnitude, cv2.COLOR_GRAY2BGR)
    cv2.putText(fig, "Frequency", (w+10, h+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 添加得分信息
    info_text = f"Ghost Score: {ghost_score:.2f} | Has Ghosting: {has_ghosting}"
    cv2.putText(fig, info_text, (10, fig.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    output_file = f"{output_prefix}_analysis.jpg"
    cv2.imwrite(output_file, fig)
    print(f"重影分析图已保存: {output_file}")
    print(f"重影得分: {ghost_score:.2f}, 是否检测到重影: {has_ghosting}")
    
    return ghost_score, has_ghosting


def main():
    """主函数"""
    print("="*60)
    print("图像拼接重影问题诊断工具")
    print("="*60)
    
    # 测试原始拼接结果
    current_result_path = r"C:\Users\Administrator\Desktop\a.png"
    if os.path.exists(current_result_path):
        print(f"\n分析当前拼接结果: {current_result_path}")
        img = cv2.imread(current_result_path)
        if img is not None:
            detect_ghosting_visual(img, "current_result")
    
    # 测试不同顺序的拼接
    img1_path = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A1.jpg"
    img2_path = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A2.jpg"
    
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        print(f"\n警告: 找不到原始图像文件")
        print(f"  A1: {img1_path} - 存在: {os.path.exists(img1_path)}")
        print(f"  A2: {img2_path} - 存在: {os.path.exists(img2_path)}")
        return
    
    # 顺序1: A1 -> A2
    results1 = test_stitching(img1_path, img2_path, "stitch_A1_A2")
    
    # 顺序2: A2 -> A1 (交换位置)
    results2 = test_stitching(img2_path, img1_path, "stitch_A2_A1")
    
    # 分析所有结果
    print("\n" + "="*60)
    print("结果汇总")
    print("="*60)
    
    if results1:
        print("\n顺序 A1 -> A2:")
        for name, img, result in results1:
            score, has_ghost = detect_ghosting_visual(img, f"result_{name.replace(' ', '_')}")
    
    if results2:
        print("\n顺序 A2 -> A1:")
        for name, img, result in results2:
            score, has_ghost = detect_ghosting_visual(img, f"result_swapped_{name.replace(' ', '_')}")
    
    print("\n" + "="*60)
    print("诊断完成")
    print("="*60)


if __name__ == "__main__":
    main()
