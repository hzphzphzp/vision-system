#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试已有模型
"""

import os
import sys
import time

import cv2
import numpy as np

print("=" * 60)
print("YOLO26 已有模型测试")
print("=" * 60)

# 1. 检查模型文件
print("\n1. 检查模型文件...")

# 模型目录
model_dir = "modules/cpu_optimization/models"
model_files = []

if os.path.exists(model_dir):
    print(f"✓ 模型目录存在: {model_dir}")
    for f in os.listdir(model_dir):
        if f.endswith(".pt"):
            model_files.append(f)

    print(f"✓ 发现 {len(model_files)} 个模型文件:")
    for f in model_files:
        full_path = os.path.join(model_dir, f)
        size_mb = os.path.getsize(full_path) / (1024 * 1024)
        print(f"   - {f} ({size_mb:.1f} MB)")
else:
    print(f"✗ 模型目录不存在: {model_dir}")
    sys.exit(1)

# 2. 检查ultralytics
print("\n2. 检查Ultralytics安装...")
try:
    from ultralytics import YOLO

    print("✓ Ultralytics安装成功")
    YOLO_AVAILABLE = True
except ImportError as e:
    print(f"✗ Ultralytics未安装: {e}")
    YOLO_AVAILABLE = False

# 3. 准备测试图片
print("\n3. 准备测试图片...")

test_image = "D:/ultralytics-main/tools/cat/train/images/42.jpg"

if os.path.exists(test_image):
    print(f"✓ 测试图片存在: {test_image}")
else:
    print(f"✗ 测试图片不存在: {test_image}")
    print("下载默认测试图片...")
    test_image = "test_image.jpg"
    if not os.path.exists(test_image):
        try:
            import urllib.request

            url = "https://ultralytics.com/images/bus.jpg"
            urllib.request.urlretrieve(url, test_image)
            print(f"✓ 已下载测试图片: {test_image}")
        except Exception as e:
            print(f"✗ 下载测试图片失败: {e}")
            sys.exit(1)

# 4. 加载图片
image = cv2.imread(test_image)
if image is None:
    print(f"✗ 无法读取图片: {test_image}")
    sys.exit(1)

print(f"✓ 图片加载成功: {image.shape}")

# 5. 测试模型
print("\n5. 测试模型推理...")

for model_file in model_files:
    model_path = os.path.join(model_dir, model_file)
    print(f"\n=== 测试模型: {model_file} ===")

    if YOLO_AVAILABLE:
        try:
            # 加载模型
            model = YOLO(model_path)
            print(f"✓ 模型加载成功: {model_file}")

            # 执行推理
            start_time = time.time()
            results = model.predict(source=image, save=True, save_txt=True)
            inference_time = (time.time() - start_time) * 1000

            print(f"✓ 推理完成，耗时: {inference_time:.2f}ms")

            # 显示结果
            if len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None:
                    print(f"✓ 发现 {len(boxes)} 个目标")

                    # 绘制检测框
                    annotated_image = results[0].plot()
                    result_file = f"result_{model_file[:-3]}.jpg"
                    cv2.imwrite(result_file, annotated_image)
                    print(f"✓ 结果已保存到: {result_file}")
                else:
                    print("✗ 未发现目标")
        except Exception as e:
            print(f"✗ 模型测试失败: {e}")
            import traceback

            traceback.print_exc()

# 6. 测试YOLO26CPUDetector
print("\n6. 测试YOLO26CPUDetector...")

try:
    from modules.cpu_optimization.models.yolo26_cpu import YOLO26CPUDetector

    # 创建检测器
    detector = YOLO26CPUDetector()

    # 测试第一个模型
    first_model = model_files[0]
    model_path = os.path.join(model_dir, first_model)

    print(f"\n测试 {first_model}...")
    if detector.load_model(model_path):
        print(f"✓ 检测器加载模型成功")

        # 检测
        result = detector.detect(image)

        if "error" in result:
            print(f"✗ 检测失败: {result['error']}")
        else:
            print(f"✓ 检测完成，发现 {result['detection_count']} 个目标")
    else:
        print(f"✗ 检测器加载模型失败")
except Exception as e:
    print(f"✗ YOLO26CPUDetector测试失败: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n如何在GUI中使用:")
print("1. 配置YOLO26-CPU工具:")
print("   - 模型类型: yolo26n (或您想要使用的模型)")
print("   - 或选择 custom 并浏览选择模型文件")
print(f"   - 模型文件位置: {model_dir}")
print("2. 运行测试:")
print("   - 按 F5 执行")
print("\n祝您测试愉快！")
