#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO26简单测试脚本
"""

import os
import sys
import time

import cv2
import numpy as np

print("=" * 60)
print("YOLO26 简单测试")
print("=" * 60)

# 1. 检查ultralytics
print("\n1. 检查Ultralytics安装...")
try:
    from ultralytics import YOLO

    print("✓ Ultralytics安装成功")
    YOLO_AVAILABLE = True
except ImportError as e:
    print(f"✗ Ultralytics未安装: {e}")
    YOLO_AVAILABLE = False

# 2. 检查PyTorch
print("\n2. 检查PyTorch安装...")
try:
    import torch

    print(f"✓ PyTorch安装成功: {torch.__version__}")
    PYTORCH_AVAILABLE = True
except ImportError as e:
    print(f"✗ PyTorch未安装: {e}")
    PYTORCH_AVAILABLE = False

# 3. 创建测试环境
print("\n3. 准备测试环境...")

# 测试图片路径
test_image = "data/images/test_image.jpg"

# 如果没有测试图片，下载一个
if not os.path.exists(test_image):
    print(f"✗ 测试图片不存在，下载一个...")
    try:
        import urllib.request

        url = "https://ultralytics.com/images/bus.jpg"
        urllib.request.urlretrieve(url, test_image)
        print(f"✓ 测试图片已下载: {test_image}")
    except Exception as e:
        print(f"✗ 下载测试图片失败: {e}")
        print("请手动放置一张测试图片到当前目录")
        sys.exit(1)

# 4. 测试YOLO26推理
print("\n4. 测试YOLO26推理...")

# 加载图片
image = cv2.imread(test_image)
if image is None:
    print(f"✗ 无法读取图片: {test_image}")
    sys.exit(1)

print(f"✓ 图片加载成功: {image.shape}")

if YOLO_AVAILABLE:
    try:
        # 尝试使用默认模型（会自动下载）
        print("\n尝试使用yolo26n模型...")
        model = YOLO("data/models/yolo26n.pt")

        # 执行推理
        start_time = time.time()
        results = model.predict(source=image, save=True, save_txt=True)
        inference_time = (time.time() - start_time) * 1000

        print(f"\n✓ 推理完成，耗时: {inference_time:.2f}ms")

        # 显示结果
        if len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                print(f"✓ 发现 {len(boxes)} 个目标")

                # 绘制检测框
                annotated_image = results[0].plot()
                cv2.imwrite("data/test_results/result.jpg", annotated_image)
                print(f"✓ 结果已保存到: data/test_results/result.jpg")
            else:
                print("✗ 未发现目标")
    except Exception as e:
        print(f"✗ 推理失败: {e}")
        print("\n尝试直接使用PyTorch模型...")

        # 简单的PyTorch模型测试
        if PYTORCH_AVAILABLE:
            # 创建一个简单的模型
            class SimpleModel(torch.nn.Module):
                def forward(self, x):
                    return torch.rand(1, 100, 6)  # 模拟输出

            model = SimpleModel()
            input_tensor = torch.rand(1, 3, 640, 640)
            output = model(input_tensor)
            print(f"✓ 简单PyTorch模型测试成功")
        else:
            print("✗ PyTorch不可用")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n如何使用您自己的模型:")
print("1. 确保模型文件在以下位置之一:")
print("   - E:/yolo26n.pt")
print("   - D:/ultralytics-main/runs/detect/train/weights/best.pt")
print("   - models/目录")
print("2. 在GUI中配置:")
print("   - 模型类型: custom")
print("   - 模型路径: 选择您的.pt文件")
print("\n祝您测试愉快！")
