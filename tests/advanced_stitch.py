#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级图像拼接 - 使用多频段融合实现完美无缝拼接
参考OpenCV Stitcher的实现原理
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from data.image_data import ImageData


def load_image(image_path):
    """加载图像"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法加载: {image_path}")
    h, w = img.shape[:2]
    return ImageData(data=img, width=w, height=h, channels=3)


def compute_homography(img1, img2):
    """计算单应性矩阵"""
    gray1 = cv2.cvtColor(img1.data, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2.data, cv2.COLOR_BGR2GRAY)
    
    # 检测特征点
    sift = cv2.SIFT_create(nfeatures=2000)
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)
    
    # 特征匹配
    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)
    
    # 比率测试
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    
    if len(good_matches) < 8:
        raise ValueError(f"匹配点不足: {len(good_matches)}")
    
    # 计算单应性矩阵
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 3.0)
    
    if H is None:
        raise ValueError("无法计算单应性矩阵")
    
    inlier_ratio = np.sum(mask) / len(mask)
    print(f"单应性矩阵内点率: {inlier_ratio:.1%}")
    
    return H


def exposure_compensation(img1, img2, overlap_mask):
    """曝光补偿 - 统一两张图像的亮度"""
    # 计算重叠区域的平均亮度
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    mean1 = np.mean(gray1[overlap_mask > 0])
    mean2 = np.mean(gray2[overlap_mask > 0])
    
    if mean2 > 0:
        # 调整img2的亮度匹配img1
        ratio = mean1 / mean2
        img2_corrected = np.clip(img2.astype(np.float32) * ratio, 0, 255).astype(np.uint8)
        print(f"曝光补偿: 调整比例={ratio:.3f}")
        return img1, img2_corrected
    
    return img1, img2


def create_laplacian_pyramid(img, levels=6):
    """创建拉普拉斯金字塔"""
    gp = [img.astype(np.float32)]
    
    # 高斯金字塔
    for i in range(levels):
        img = cv2.pyrDown(img)
        gp.append(img)
    
    # 拉普拉斯金字塔
    lp = [gp[levels-1]]
    for i in range(levels-1, 0, -1):
        size = (gp[i-1].shape[1], gp[i-1].shape[0])
        GE = cv2.pyrUp(gp[i], dstsize=size)
        L = gp[i-1] - GE
        lp.append(L)
    
    return lp[::-1]  # 反转，从低到高


def blend_pyramids(lp1, lp2, gp_mask):
    """融合拉普拉斯金字塔"""
    blended = []
    
    for l1, l2, mask in zip(lp1, lp2, gp_mask):
        # 扩展mask到3通道
        mask_3d = np.stack([mask] * 3, axis=-1)
        # 融合
        blended_level = l1 * mask_3d + l2 * (1 - mask_3d)
        blended.append(blended_level)
    
    return blended


def reconstruct_from_pyramid(lp):
    """从拉普拉斯金字塔重建图像"""
    img = lp[-1]
    
    for i in range(len(lp)-2, -1, -1):
        size = (lp[i].shape[1], lp[i].shape[0])
        img = cv2.pyrUp(img, dstsize=size)
        img = img + lp[i]
    
    return np.clip(img, 0, 255).astype(np.uint8)


def multi_band_blending(img1, img2, mask1, mask2, num_bands=6):
    """
    多频段融合 - OpenCV Stitcher使用的核心算法
    
    原理：
    1. 创建拉普拉斯金字塔（高频细节）
    2. 创建高斯金字塔（权重掩码）
    3. 在不同频段分别融合
    4. 重建图像
    """
    print(f"执行多频段融合 (bands={num_bands})...")
    
    # 创建拉普拉斯金字塔
    lp1 = create_laplacian_pyramid(img1, num_bands)
    lp2 = create_laplacian_pyramid(img2, num_bands)
    
    # 为mask创建高斯金字塔
    # 归一化mask
    mask1_norm = mask1.astype(np.float32) / 255.0
    mask2_norm = mask2.astype(np.float32) / 255.0
    
    # 创建权重图（距离变换）
    dist1 = cv2.distanceTransform(mask1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(mask2, cv2.DIST_L2, 5)
    
    total_dist = dist1 + dist2 + 1e-6
    weight1 = dist1 / total_dist
    
    # 创建权重金字塔
    gp_mask = [weight1]
    curr_mask = weight1.copy()
    for i in range(num_bands-1):
        curr_mask = cv2.pyrDown(curr_mask)
        gp_mask.append(curr_mask)
    
    # 融合金字塔
    blended_pyramid = blend_pyramids(lp1, lp2, gp_mask)
    
    # 重建图像
    result = reconstruct_from_pyramid(blended_pyramid)
    
    return result


def advanced_stitch(img1_path, img2_path, output_path="advanced_stitch.jpg"):
    """高级拼接 - 使用多频段融合"""
    
    print("="*60)
    print("高级图像拼接 (多频段融合)")
    print("="*60)
    
    # 1. 加载图像
    print("\n[1] 加载图像...")
    img1_data = load_image(img1_path)
    img2_data = load_image(img2_path)
    img1 = img1_data.data
    img2 = img2_data.data
    
    print(f"  图像1: {img1.shape[1]}x{img1.shape[0]}")
    print(f"  图像2: {img2.shape[1]}x{img2.shape[0]}")
    
    # 2. 计算单应性矩阵
    print("\n[2] 计算几何变换...")
    H = compute_homography(img1_data, img2_data)
    
    # 3. 计算输出尺寸和变换
    print("\n[3] 图像变换...")
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
    # 计算边界
    corners = np.float32([[0, 0], [0, h2], [w2, h2], [w2, 0]]).reshape(-1, 1, 2)
    transformed_corners = cv2.perspectiveTransform(corners, H)
    
    all_corners = np.concatenate([
        transformed_corners,
        np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1, 1, 2)
    ])
    
    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel()) - 10
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel()) + 10
    
    x_min = min(0, x_min)
    y_min = min(0, y_min)
    
    canvas_w = x_max - x_min
    canvas_h = y_max - y_min
    
    print(f"  画布尺寸: {canvas_w}x{canvas_h}")
    
    # 4. 创建平移矩阵
    H_translate = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
    H_combined = H_translate @ H
    
    # 5. 变换图像
    img2_warped = cv2.warpPerspective(img2, H_combined, (canvas_w, canvas_h))
    
    # 放置图像1
    img1_canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    y_start = -y_min
    x_start = -x_min
    img1_canvas[y_start:y_start+h1, x_start:x_start+w1] = img1
    
    # 6. 创建掩码
    mask1 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    mask1[y_start:y_start+h1, x_start:x_start+w1] = 255
    
    mask2 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    mask2[img2_warped.sum(axis=2) > 0] = 255
    
    # 7. 曝光补偿
    print("\n[4] 曝光补偿...")
    overlap = cv2.bitwise_and(mask1, mask2)
    if np.sum(overlap) > 0:
        img1_canvas, img2_warped = exposure_compensation(img1_canvas, img2_warped, overlap)
    
    # 8. 多频段融合
    print("\n[5] 多频段融合...")
    result = multi_band_blending(img1_canvas, img2_warped, mask1, mask2, num_bands=6)
    
    # 9. 裁剪黑边
    print("\n[6] 裁剪优化...")
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        result = result[y:y+h, x:x+w]
    
    # 10. 保存结果
    cv2.imwrite(output_path, result)
    print(f"\n[OK] 完成! 保存到: {output_path}")
    print(f"    最终尺寸: {result.shape[1]}x{result.shape[0]}")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        img1 = sys.argv[1]
        img2 = sys.argv[2]
    else:
        img1 = "A1.jpg"
        img2 = "A2.jpg"
    
    if os.path.exists(img1) and os.path.exists(img2):
        try:
            result = advanced_stitch(img1, img2, "perfect_stitch.jpg")
            
            # 也尝试交换顺序
            print("\n" + "="*60)
            result2 = advanced_stitch(img2, img1, "perfect_stitch_swapped.jpg")
            
            print("\n" + "="*60)
            print("完成! 生成文件:")
            print("  - perfect_stitch.jpg")
            print("  - perfect_stitch_swapped.jpg")
            print("="*60)
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"找不到图像文件: {img1} 或 {img2}")
