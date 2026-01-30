#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试YOLO26支持
"""

import os
import sys
import time

import cv2

print("=" * 60)
print("测试YOLO26支持")
print("=" * 60)

# 1. 检查Ultralytics版本
print("1. 检查Ultralytics版本...")
try:
    import ultralytics
    from ultralytics import YOLO

    print(f"✓ Ultralytics版本: {ultralytics.__version__}")
    print(f"✓ YOLO类可用: {YOLO is not None}")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 2. 检查模型文件
print("\n2. 检查模型文件...")

model_dir = "modules/cpu_optimization/models"
model_files = []

if os.path.exists(model_dir):
    print(f"✓ 模型目录: {model_dir}")
    for f in os.listdir(model_dir):
        if f.endswith(".pt"):
            model_files.append(f)

    print(f"✓ 发现 {len(model_files)} 个模型:")
    for f in model_files:
        size_mb = os.path.getsize(os.path.join(model_dir, f)) / (1024 * 1024)
        print(f"   - {f} ({size_mb:.1f} MB)")
else:
    print(f"✗ 模型目录不存在: {model_dir}")
    sys.exit(1)

# 3. 测试模型加载
print("\n3. 测试模型加载...")

for model_file in model_files:
    model_path = os.path.join(model_dir, model_file)
    print(f"\n测试模型: {model_file}")

    try:
        model = YOLO(model_path)
        print(f"✓ 模型加载成功!")

        # 4. 测试推理
        print("4. 测试推理...")

        # 准备测试图片
        test_image = "D:/ultralytics-main/tools/cat/train/images/42.jpg"
        if not os.path.exists(test_image):
            test_image = "test_image.jpg"
            if not os.path.exists(test_image):
                import urllib.request

                url = "https://ultralytics.com/images/bus.jpg"
                urllib.request.urlretrieve(url, test_image)

        # 加载图片
        image = cv2.imread(test_image)
        if image is None:
            print(f"✗ 无法读取图片: {test_image}")
            continue

        print(f"✓ 图片加载成功: {image.shape}")

        # 执行推理
        start_time = time.time()
        results = model.predict(source=image, save=True, save_txt=True)
        inference_time = (time.time() - start_time) * 1000

        print(f"✓ 推理完成! 耗时: {inference_time:.2f}ms")

        # 解析结果
        if len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                print(f"✓ 发现 {len(boxes)} 个目标")

                # 显示前5个目标
                for i, box in enumerate(boxes[:5]):
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    name = results[0].names[cls]
                    print(f"   {i+1}. {name}: {conf:.2f}")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
