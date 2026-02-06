#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完美图像拼接 - 使用最佳接缝和羽化融合
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
    
    sift = cv2.SIFT_create(nfeatures=2000)
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)
    
    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)
    
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    
    if len(good_matches) < 8:
        raise ValueError(f"匹配点不足: {len(good_matches)}")
    
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 3.0)
    
    if H is None:
        raise ValueError("无法计算单应性矩阵")
    
    return H, good_matches, kp1, kp2


def smooth_blend(img1, img2, mask1, mask2):
    """
    平滑融合 - 使用距离变换权重（无黑线版本）
    """
    # 计算距离变换
    dist1 = cv2.distanceTransform(mask1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(mask2, cv2.DIST_L2, 5)
    
    # 计算权重
    total_dist = dist1 + dist2 + 1e-6
    weight1 = dist1 / total_dist
    weight2 = dist2 / total_dist
    
    # 扩展权重到3通道
    w1 = np.stack([weight1] * 3, axis=-1)
    w2 = np.stack([weight2] * 3, axis=-1)
    
    # 加权融合
    blended = img1.astype(np.float32) * w1 + img2.astype(np.float32) * w2
    result = np.clip(blended, 0, 255).astype(np.uint8)
    
    return result


def seamless_blend_v2(img1, img2, mask1, mask2):
    """
    改进的无缝融合 - 避免黑线
    在重叠区域使用平滑过渡，非重叠区域保留原图
    """
    h, w = img1.shape[:2]
    result = np.zeros_like(img1)
    
    # 创建平滑的权重图
    # 对于每个像素，计算它应该使用img1还是img2
    overlap = cv2.bitwise_and(mask1, mask2)
    
    # 使用高斯模糊平滑权重，避免硬边
    dist1 = cv2.distanceTransform(mask1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(mask2, cv2.DIST_L2, 5)
    
    # 创建权重图
    weight = np.zeros((h, w), dtype=np.float32)
    
    # 非重叠区域
    only_mask1 = cv2.bitwise_and(mask1, cv2.bitwise_not(mask2))
    only_mask2 = cv2.bitwise_and(mask2, cv2.bitwise_not(mask1))
    
    weight[only_mask1 > 0] = 0.0  # 完全使用img1
    weight[only_mask2 > 0] = 1.0  # 完全使用img2
    
    # 重叠区域：基于距离平滑过渡
    overlap_coords = np.where(overlap > 0)
    if len(overlap_coords[0]) > 0:
        d1 = dist1[overlap_coords]
        d2 = dist2[overlap_coords]
        total = d1 + d2 + 1e-6
        # weight = 0 表示img1, weight = 1 表示img2
        w = d2 / total  # 距离img2越远，越偏向img1
        weight[overlap_coords] = w
    
    # 应用高斯模糊使过渡更平滑（关键：避免硬边和黑线）
    weight = cv2.GaussianBlur(weight, (21, 21), 5)
    
    # 扩展权重到3通道
    weight_3d = np.stack([weight] * 3, axis=-1)
    
    # 融合
    result = img1.astype(np.float32) * (1 - weight_3d) + img2.astype(np.float32) * weight_3d
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return result


def perfect_stitch(img1_path, img2_path, output_path="perfect_result.jpg"):
    """完美拼接"""
    
    print("="*60)
    print("完美图像拼接")
    print("="*60)
    
    # 1. 加载
    print("\n[1] 加载图像...")
    img1_data = load_image(img1_path)
    img2_data = load_image(img2_path)
    img1 = img1_data.data
    img2 = img2_data.data
    
    print(f"  图像1: {img1.shape[1]}x{img1.shape[0]}")
    print(f"  图像2: {img2.shape[1]}x{img2.shape[0]}")
    
    # 2. 计算变换
    print("\n[2] 计算几何变换...")
    H, matches, kp1, kp2 = compute_homography(img1_data, img2_data)
    print(f"  优质匹配点: {len(matches)}")
    
    # 3. 计算画布
    print("\n[3] 图像变换...")
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
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
    
    print(f"  画布: {canvas_w}x{canvas_h}")
    
    # 4. 变换图像
    H_translate = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]])
    H_combined = H_translate @ H
    
    img2_warped = cv2.warpPerspective(img2, H_combined, (canvas_w, canvas_h))
    
    # 放置图像1
    img1_canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    y_start = -y_min
    x_start = -x_min
    img1_canvas[y_start:y_start+h1, x_start:x_start+w1] = img1
    
    # 5. 创建掩码
    mask1 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    mask1[y_start:y_start+h1, x_start:x_start+w1] = 255
    
    mask2 = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    mask2[img2_warped.sum(axis=2) > 0] = 255
    
    # 6. 无缝融合（使用改进的算法，避免黑线）
    print("\n[4] 无缝融合...")
    result = seamless_blend_v2(img1_canvas, img2_warped, mask1, mask2)
    
    # 8. 裁剪
    print("\n[6] 裁剪...")
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        result = result[y:y+h, x:x+w]
    
    # 9. 保存
    cv2.imwrite(output_path, result)
    print(f"\n[OK] 完成: {output_path}")
    print(f"    尺寸: {result.shape[1]}x{result.shape[0]}")
    
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
            result = perfect_stitch(img1, img2, "final_result.jpg")
            
            print("\n" + "="*60)
            result2 = perfect_stitch(img2, img1, "final_result_swapped.jpg")
            
            print("\n" + "="*60)
            print("完成!")
            print("  - final_result.jpg")
            print("  - final_result_swapped.jpg")
            
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"找不到图像: {img1} 或 {img2}")
