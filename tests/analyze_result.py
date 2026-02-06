#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析用户提供的拼接结果并给出改进建议
"""

import cv2
import numpy as np

def analyze_stitching_result(image_path):
    """分析拼接结果中的问题"""
    
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取图像: {image_path}")
        return
    
    h, w = img.shape[:2]
    print(f"图像尺寸: {w}x{h}")
    print(f"="*60)
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. 检测明显的拼接线/重影区域
    # 在水平方向检测异常
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # 检测垂直拼接线（可能在中间区域）
    mid_region = w // 3  # 检测中间1/3区域
    vertical_profile = np.mean(gradient_magnitude[:, mid_region:2*mid_region], axis=0)
    
    # 找到梯度最大的位置（可能是拼接线）
    max_grad_pos = np.argmax(vertical_profile) + mid_region
    print(f"检测到可能的拼接线位置: x={max_grad_pos}")
    
    # 2. 检测重影（通过分析重叠区域的高频成分）
    # 在拼接线附近创建分析窗口
    window_size = 100
    if max_grad_pos - window_size > 0 and max_grad_pos + window_size < w:
        left_region = gray[:, max_grad_pos-window_size:max_grad_pos]
        right_region = gray[:, max_grad_pos:max_grad_pos+window_size]
        
        # 计算两个区域的相关性
        left_mean = np.mean(left_region)
        right_mean = np.mean(right_region)
        
        print(f"左侧区域平均亮度: {left_mean:.2f}")
        print(f"右侧区域平均亮度: {right_mean:.2f}")
        print(f"亮度差异: {abs(left_mean - right_mean):.2f}")
        
        # 如果亮度差异大，说明曝光不一致
        if abs(left_mean - right_mean) > 20:
            print("⚠️ 警告: 左右区域亮度差异较大，可能需要曝光补偿")
    
    # 3. 边缘分析
    edges = cv2.Canny(gray, 50, 150)
    
    # 在拼接线附近的边缘密度
    if max_grad_pos - 50 > 0 and max_grad_pos + 50 < w:
        seam_edges = edges[:, max_grad_pos-50:max_grad_pos+50]
        edge_density = np.sum(seam_edges > 0) / seam_edges.size
        print(f"拼接线附近边缘密度: {edge_density:.4f}")
        
        if edge_density > 0.1:
            print("[!] 警告: 拼接线附近边缘密度高，可能存在重影")
    
    # 4. 生成可视化分析图
    analysis_img = img.copy()
    
    # 标记检测到的拼接线
    cv2.line(analysis_img, (max_grad_pos, 0), (max_grad_pos, h), (0, 0, 255), 2)
    
    # 添加分析区域标记
    if max_grad_pos - 100 > 0:
        cv2.rectangle(analysis_img, (max_grad_pos-100, 0), (max_grad_pos, h), (255, 0, 0), 2)
        cv2.putText(analysis_img, "Left Image", (max_grad_pos-90, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    if max_grad_pos + 100 < w:
        cv2.rectangle(analysis_img, (max_grad_pos, 0), (max_grad_pos+100, h), (0, 255, 0), 2)
        cv2.putText(analysis_img, "Right Image", (max_grad_pos+10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # 保存分析结果
    output_path = image_path.replace('.png', '_analysis.png')
    cv2.imwrite(output_path, analysis_img)
    print(f"\n分析图已保存: {output_path}")
    
    print(f"\n" + "="*60)
    print("改进建议:")
    print("="*60)
    print("1. 调整融合参数:")
    print("   - blend_strength: 从 3 降低到 2 或 1")
    print("   - ransac_reproj_threshold: 从 2.0 降低到 1.0")
    print()
    print("2. 如果亮度不一致:")
    print("   - 在拼接前对两张图像进行曝光补偿")
    print("   - 或使用 _balance_brightness 方法")
    print()
    print("3. 如果仍有问题，尝试:")
    print("   - 使用 SIFT 特征检测器（更精确但较慢）")
    print("   - 增加 min_match_count 到 15-20")


if __name__ == "__main__":
    analyze_stitching_result(r"C:\Users\Administrator\Desktop\a.png")
