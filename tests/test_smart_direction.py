#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能方向检测拼接 - 自动识别水平和垂直方向
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from data.image_data import ImageData
from tools.vision.image_stitching import ImageStitchingTool


def detect_stitch_direction(img1, img2):
    """
    检测应该使用水平拼接还是垂直拼接
    
    通过比较特征点在水平和垂直方向的分布来判断
    """
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 使用ORB检测特征点
    orb = cv2.ORB_create(nfeatures=500)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)
    
    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return "horizontal"  # 默认水平
    
    # 匹配特征点
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    if len(matches) < 8:
        return "horizontal"  # 默认水平
    
    # 分析匹配点的位置差异
    horizontal_diffs = []
    vertical_diffs = []
    
    for match in matches:
        pt1 = kp1[match.queryIdx].pt
        pt2 = kp2[match.trainIdx].pt
        
        horizontal_diffs.append(abs(pt1[0] - pt2[0]))
        vertical_diffs.append(abs(pt1[1] - pt2[1]))
    
    # 计算平均差异
    avg_h_diff = np.mean(horizontal_diffs)
    avg_v_diff = np.mean(vertical_diffs)
    
    # 如果垂直差异明显大于水平差异，说明是垂直拼接
    if avg_v_diff > avg_h_diff * 1.5:
        return "vertical"
    else:
        return "horizontal"


def smart_stitch(img1, img2):
    """
    智能拼接 - 自动检测方向并处理
    """
    # 检测拼接方向
    direction = detect_stitch_direction(img1, img2)
    print(f"检测到拼接方向: {direction}")
    
    if direction == "vertical":
        # 垂直拼接：先旋转90度，水平拼接，再转回来
        print("使用垂直拼接模式（旋转90度）")
        img1_rot = cv2.rotate(img1, cv2.ROTATE_90_CLOCKWISE)
        img2_rot = cv2.rotate(img2, cv2.ROTATE_90_CLOCKWISE)
        
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, result_rot = stitcher.stitch([img1_rot, img2_rot])
        
        if status == cv2.Stitcher_OK:
            result = cv2.rotate(result_rot, cv2.ROTATE_90_COUNTERCLOCKWISE)
            return result, direction
    else:
        # 水平拼接：直接使用
        print("使用水平拼接模式")
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, result = stitcher.stitch([img1, img2])
        
        if status == cv2.Stitcher_OK:
            return result, direction
    
    return None, direction


def main():
    print("="*70)
    print("智能方向检测拼接测试")
    print("="*70)
    
    # 测试水平拼接（A1, A2）
    print("\n[测试1] 水平方向拼接 (A1 + A2)")
    img1 = cv2.imread('A1.jpg')
    img2 = cv2.imread('A2.jpg')
    
    if img1 is not None and img2 is not None:
        result, direction = smart_stitch(img1, img2)
        if result is not None:
            cv2.imwrite("smart_horizontal.jpg", result)
            print(f"  成功! 方向: {direction}, 尺寸: {result.shape[1]}x{result.shape[0]}")
        else:
            print("  失败")
    
    # 测试垂直拼接（模拟：将A1, A2旋转90度作为垂直测试）
    print("\n[测试2] 垂直方向拼接 (模拟)")
    img1_v = cv2.rotate(img1, cv2.ROTATE_90_CLOCKWISE)
    img2_v = cv2.rotate(img2, cv2.ROTATE_90_CLOCKWISE)
    
    result, direction = smart_stitch(img1_v, img2_v)
    if result is not None:
        cv2.imwrite("smart_vertical.jpg", result)
        print(f"  成功! 方向: {direction}, 尺寸: {result.shape[1]}x{result.shape[0]}")
    else:
        print("  失败")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
