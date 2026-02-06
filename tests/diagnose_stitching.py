#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断拼接问题 - 找出重影的根本原因
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool


def diagnose_stitching(img1_path, img2_path):
    """深度诊断拼接问题"""
    
    print("="*70)
    print("深度诊断：分析拼接失败的根本原因")
    print("="*70)
    
    # 1. 加载图像
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    if img1 is None or img2 is None:
        print("错误：无法加载图像")
        return
    
    print(f"\n[1] 图像信息:")
    print(f"    图像1: {img1.shape[1]}x{img1.shape[0]}")
    print(f"    图像2: {img2.shape[1]}x{img2.shape[0]}")
    
    # 2. 手动检测特征点和匹配
    print(f"\n[2] 特征点检测:")
    
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 使用SIFT检测特征点
    sift = cv2.SIFT_create(nfeatures=2000)
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)
    
    print(f"    图像1特征点: {len(kp1)}")
    print(f"    图像2特征点: {len(kp2)}")
    
    # 3. 特征匹配
    print(f"\n[3] 特征匹配:")
    
    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)
    
    # 应用比率测试
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    
    print(f"    初始匹配: {len(matches)}")
    print(f"    优质匹配: {len(good_matches)}")
    
    if len(good_matches) < 10:
        print(f"    [!] 警告：匹配点太少，可能无法正确对齐！")
    
    # 4. 计算单应性矩阵
    print(f"\n[4] 几何变换:")
    
    if len(good_matches) >= 4:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
        
        if H is not None and mask is not None:
            inliers = np.sum(mask)
            inlier_ratio = inliers / len(mask)
            print(f"    单应性矩阵内点: {inliers}/{len(mask)} ({inlier_ratio:.1%})")
            
            if inlier_ratio < 0.5:
                print(f"    [!] 警告：内点率太低，变换可能不准确！")
            
            # 显示变换矩阵
            print(f"    变换矩阵:")
            for row in H:
                print(f"      [{row[0]:8.3f} {row[1]:8.3f} {row[2]:8.3f}]")
        else:
            print(f"    [FAIL] 错误：无法计算单应性矩阵")
    
    # 5. 可视化匹配结果
    print(f"\n[5] 生成诊断图像...")
    
    # 绘制匹配线
    match_img = cv2.drawMatches(img1, kp1, img2, kp2, good_matches[:20], None, 
                                 flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    cv2.imwrite("diagnosis_matches.jpg", match_img)
    print(f"    已保存: diagnosis_matches.jpg (显示特征匹配)")
    
    # 6. 尝试使用OpenCV内置的Stitcher作为对比
    print(f"\n[6] 使用OpenCV内置拼接器对比:")
    
    try:
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, stitched = stitcher.stitch([img1, img2])
        
        if status == cv2.Stitcher_OK:
            cv2.imwrite("diagnosis_opencv_stitcher.jpg", stitched)
            print(f"    [OK] OpenCV内置拼接器成功!")
            print(f"    已保存: diagnosis_opencv_stitcher.jpg")
            print(f"    这说明我们的算法需要改进")
        else:
            print(f"    [FAIL] OpenCV内置拼接器也失败了 (状态码: {status})")
    except Exception as e:
        print(f"    [FAIL] OpenCV内置拼接器错误: {e}")
    
    # 7. 分析问题
    print(f"\n[7] 问题分析:")
    
    if len(good_matches) < 10:
        print(f"    [X] 问题1: 特征匹配不足")
        print(f"       - 可能原因：两张图像重叠区域太少或纹理不足")
    
    if inlier_ratio < 0.5:
        print(f"    [X] 问题2: 几何变换不准确")
        print(f"       - 可能原因：误匹配太多，RANSAC无法正确过滤")
    
    print(f"\n    💡 建议解决方案:")
    print(f"       1. 使用更严格的特征匹配筛选")
    print(f"       2. 增加预处理（CLAHE增强对比度）")
    print(f"       3. 使用多频段融合代替简单的羽化融合")
    print(f"       4. 或者参考OpenCV Stitcher的实现")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        img1_path = sys.argv[1]
        img2_path = sys.argv[2]
    else:
        img1_path = "A1.jpg"
        img2_path = "A2.jpg"
    
    if os.path.exists(img1_path) and os.path.exists(img2_path):
        diagnose_stitching(img1_path, img2_path)
    else:
        print(f"找不到图像文件")
        print(f"  A1: {os.path.exists(img1_path)}")
        print(f"  A2: {os.path.exists(img2_path)}")
