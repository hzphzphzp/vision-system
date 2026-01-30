#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO26功能测试 - 使用新模块
"""

import os
import sys
import time

import cv2
import numpy as np

print("=" * 60)
print("YOLO26 功能测试 - 新模块")
print("=" * 60)

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.cpu_optimization.models.yolo26_cpu import YOLO26CPUDetector

# 测试图片路径
image_path = "D:/ultralytics-main/tools/cat/train/images/42.jpg"

# 检查图片
if os.path.exists(image_path):
    print(f"✓ 图片存在: {image_path}")
else:
    print(f"✗ 图片不存在: {image_path}")
    exit(1)

# 创建检测器
detector = YOLO26CPUDetector(conf_threshold=0.25, nms_threshold=0.45)

# 尝试加载模型
model_loaded = False

# 1. 检查E盘模型
model_paths = [
    "E:/yolo26n.pt",
    "D:/ultralytics-main/runs/detect/train/weights/best.pt",
    "data/models/yolo26n.pt",
]

for model_path in model_paths:
    if os.path.exists(model_path):
        print(f"\n尝试加载模型: {model_path}")
        if detector.load_model(model_path):
            print(f"✓ 模型加载成功!")
            model_loaded = True
            break
        else:
            print(f"✗ 模型加载失败")

if not model_loaded:
    print("\n✗ 没有找到可用的模型文件")
    exit(1)

# 执行检测
print(f"\n执行检测...")
image = cv2.imread(image_path)
if image is None:
    print(f"✗ 无法读取图片: {image_path}")
    exit(1)

print(f"✓ 图片加载成功: {image.shape}")

# 检测
start_time = time.time()
result = detector.detect(image)
inference_time = (time.time() - start_time) * 1000

print(f"\n检测完成，耗时: {inference_time:.2f}ms")

# 解析结果
if "error" in result:
    print(f"✗ 检测失败: {result['error']}")
else:
    print(f"✓ 发现 {result['detection_count']} 个目标")

    # 显示检测结果
    for i, det in enumerate(result["detections"][:10]):
        print(
            f"  目标{i+1}: {det['class_name']}, 置信度: {det['confidence']:.2f}"
        )
        bbox = det["bbox"]
        print(
            f"         位置: ({bbox['x1']:.2f}, {bbox['y1']:.2f}) - ({bbox['x2']:.2f}, {bbox['y2']:.2f})"
        )

    # 在图片上绘制检测框
    output_image = image.copy()
    for det in result["detections"]:
        bbox = det["bbox"]
        x1 = int(bbox["x1"] * output_image.shape[1])
        y1 = int(bbox["y1"] * output_image.shape[0])
        x2 = int(bbox["x2"] * output_image.shape[1])
        y2 = int(bbox["y2"] * output_image.shape[0])

        # 随机颜色
        color = tuple(np.random.randint(0, 255, 3).tolist())

        # 绘制边界框
        cv2.rectangle(output_image, (x1, y1), (x2, y2), color, 2)

        # 绘制标签
        label = f"{det['class_name']}: {det['confidence']:.2f}"
        cv2.putText(
            output_image,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # 保存结果
    output_path = "runs/detect/predict/test_result.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, output_image)
    print(f"\n✓ 结果已保存到: {output_path}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
