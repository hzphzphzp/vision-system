#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO26功能测试脚本
"""

import os

from PIL import Image
from ultralytics import YOLO

print("=" * 60)
print("YOLO26 功能测试")
print("=" * 60)

# 测试图片路径
image_path = "D:/ultralytics-main/tools/cat/train/images/42.jpg"

# 检查图片
if os.path.exists(image_path):
    print(f"✓ 图片存在: {image_path}")
else:
    print(f"✗ 图片不存在: {image_path}")
    exit(1)

# 尝试加载模型
model = None

# 1. 检查自定义模型
custom_model = "D:/ultralytics-main/runs/detect/train/weights/best.pt"
if os.path.exists(custom_model):
    print(f"✓ 找到自定义模型: {custom_model}")
    model = YOLO(custom_model)
else:
    print(f"✗ 未找到自定义模型: {custom_model}")

# 2. 检查E盘模型
if model is None:
    e_model = "E:/yolo26n.pt"
    if os.path.exists(e_model):
        print(f"✓ 找到E盘模型: {e_model}")
        model = YOLO(e_model)
    else:
        print(f"✗ 未找到E盘模型: {e_model}")

# 3. 检查models目录
if model is None:
    models_dir = "data/models"
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            if f.endswith(".pt"):
                model_path = os.path.join(models_dir, f)
                print(f"✓ 找到模型: {model_path}")
                model = YOLO(model_path)
                break

if model is None:
    print("\n✗ 没有找到任何模型文件")
    print("\n请确保以下任一位置有模型文件:")
    print(f"  1. {custom_model}")
    print(f"  2. E:/yolo26n.pt")
    print(f"  3. data/models/目录")
    exit(1)

print(f"\n✓ 模型加载成功")

# 执行检测
print("\n执行检测...")
im1 = Image.open(image_path)
results = model.predict(source=im1, save=True, save_txt=True)

# 解析结果
if len(results) > 0:
    boxes = results[0].boxes
    if boxes is not None:
        num_detections = len(boxes)
        print(f"\n✓ 检测完成，发现 {num_detections} 个目标")

        # 显示检测结果
        for i, box in enumerate(boxes[:10]):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            cls = int(box.cls[0].cpu().numpy())
            name = results[0].names.get(cls, f"class_{cls}")
            print(
                f"  目标{i+1}: {name}, 置信度: {conf:.2f}, 位置: ({x1:.0f}, {y1:.0f}) - ({x2:.0f}, {y2:.0f})"
            )
    else:
        print("\n✓ 检测完成，未发现目标")
else:
    print("\n✓ 检测完成，无结果")

# 检查保存的图片
save_path = "runs/detect/predict"
if os.path.exists(save_path):
    saved_files = os.listdir(save_path)
    print(f"\n✓ 结果已保存到: {save_path}")
    for f in saved_files[:5]:
        print(f"  - {f}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
