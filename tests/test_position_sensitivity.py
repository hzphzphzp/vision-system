#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图像拼接算法的位置敏感性问题

验证优化后的增强型传统方法是否解决了位置敏感性问题，
测试不同输入顺序下的拼接效果。
"""

import time

import cv2
import numpy as np

from data.image_data import ImageData
from tools.image_stitching import ImageStitchingTool


def create_test_images():
    """
    创建测试图像

    返回两张有重叠区域的测试图像
    """
    # 创建第一张图像（左侧）
    img1 = np.zeros((480, 640, 3), dtype=np.uint8)
    img1[:, :400] = [0, 0, 255]  # 左侧红色
    img1[:, 400:] = [255, 255, 255]  # 右侧白色（重叠区域）

    # 添加特征点
    cv2.putText(
        img1,
        "Image 1",
        (100, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )
    cv2.rectangle(img1, (350, 100), (450, 200), (0, 255, 0), 3)

    # 创建第二张图像（右侧）
    img2 = np.zeros((480, 640, 3), dtype=np.uint8)
    img2[:, :240] = [255, 255, 255]  # 左侧白色（重叠区域）
    img2[:, 240:] = [255, 0, 0]  # 右侧蓝色

    # 添加特征点
    cv2.putText(
        img2,
        "Image 2",
        (400, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )
    cv2.circle(img2, (290, 150), 50, (0, 255, 255), 3)

    return img1, img2


def test_position_sensitivity():
    """
    测试位置敏感性问题
    """
    print("=== 测试图像拼接算法的位置敏感性 ===")

    # 创建测试图像
    img1, img2 = create_test_images()

    # 保存测试图像
    cv2.imwrite("data/images/test_image_1.jpg", img1)
    cv2.imwrite("data/images/test_image_2.jpg", img2)
    print(
        "测试图像已保存: data/images/test_image_1.jpg, data/images/test_image_2.jpg"
    )

    # 创建ImageData对象
    image_data1 = ImageData(data=img1)
    image_data2 = ImageData(data=img2)

    print(f"\n测试图像1: {image_data1.width}x{image_data1.height}")
    print(f"测试图像2: {image_data2.width}x{image_data2.height}")

    # 创建图像拼接工具
    stitcher = ImageStitchingTool()

    # 测试1: 顺序 [image1, image2]
    print("\n=== 测试1: 顺序 [image1, image2] ===")
    start_time = time.time()
    result1 = stitcher.process([image_data1, image_data2])
    time1 = time.time() - start_time

    print(f"拼接状态: {'成功' if result1.status else '失败'}")
    print(f"拼接消息: {result1.message}")
    print(f"处理时间: {time1:.2f}秒")

    if result1.status:
        stitched1 = result1.get_image("stitched_image")
        if stitched1:
            print(f"拼接结果尺寸: {stitched1.width}x{stitched1.height}")
            cv2.imwrite(
                "data/test_results/stitched_result_order1.jpg", stitched1.data
            )
            print(
                "拼接结果已保存: data/test_results/stitched_result_order1.jpg"
            )

    # 测试2: 顺序 [image2, image1]
    print("\n=== 测试2: 顺序 [image2, image1] ===")
    start_time = time.time()
    result2 = stitcher.process([image_data2, image_data1])
    time2 = time.time() - start_time

    print(f"拼接状态: {'成功' if result2.status else '失败'}")
    print(f"拼接消息: {result2.message}")
    print(f"处理时间: {time2:.2f}秒")

    if result2.status:
        stitched2 = result2.get_image("stitched_image")
        if stitched2:
            print(f"拼接结果尺寸: {stitched2.width}x{stitched2.height}")
            cv2.imwrite(
                "data/test_results/stitched_result_order2.jpg", stitched2.data
            )
            print(
                "拼接结果已保存: data/test_results/stitched_result_order2.jpg"
            )

    # 测试3: 三张图像的不同顺序
    print("\n=== 测试3: 三张图像的不同顺序 ===")

    # 创建第三张测试图像
    img3 = np.zeros((480, 640, 3), dtype=np.uint8)
    img3[:, :240] = [255, 0, 0]  # 左侧蓝色（与img2重叠）
    img3[:, 240:] = [0, 255, 0]  # 右侧绿色

    # 添加特征点
    cv2.putText(
        img3,
        "Image 3",
        (400, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )
    cv2.line(img3, (240, 100), (340, 300), (0, 255, 255), 3)

    image_data3 = ImageData(data=img3)
    cv2.imwrite("data/images/test_image_3.jpg", img3)
    print("测试图像3已保存: data/images/test_image_3.jpg")

    # 测试顺序1: [1, 2, 3]
    print("\n测试3.1: 顺序 [1, 2, 3]")
    start_time = time.time()
    result3_1 = stitcher.process([image_data1, image_data2, image_data3])
    time3_1 = time.time() - start_time

    print(f"拼接状态: {'成功' if result3_1.status else '失败'}")
    print(f"处理时间: {time3_1:.2f}秒")

    if result3_1.status:
        stitched3_1 = result3_1.get_image("stitched_image")
        if stitched3_1:
            print(f"拼接结果尺寸: {stitched3_1.width}x{stitched3_1.height}")
            cv2.imwrite(
                "data/test_results/stitched_result_order3_1.jpg",
                stitched3_1.data,
            )

    # 测试顺序2: [3, 2, 1]
    print("\n测试3.2: 顺序 [3, 2, 1]")
    start_time = time.time()
    result3_2 = stitcher.process([image_data3, image_data2, image_data1])
    time3_2 = time.time() - start_time

    print(f"拼接状态: {'成功' if result3_2.status else '失败'}")
    print(f"处理时间: {time3_2:.2f}秒")

    if result3_2.status:
        stitched3_2 = result3_2.get_image("stitched_image")
        if stitched3_2:
            print(f"拼接结果尺寸: {stitched3_2.width}x{stitched3_2.height}")
            cv2.imwrite(
                "data/test_results/stitched_result_order3_2.jpg",
                stitched3_2.data,
            )

    # 综合评估
    print("\n=== 综合评估 ===")
    print(f"测试1 (顺序1) 成功: {result1.status}")
    print(f"测试2 (顺序2) 成功: {result2.status}")
    print(f"测试3.1 (顺序3.1) 成功: {result3_1.status}")
    print(f"测试3.2 (顺序3.2) 成功: {result3_2.status}")

    # 计算成功率
    tests = [
        result1.status,
        result2.status,
        result3_1.status,
        result3_2.status,
    ]
    success_rate = sum(tests) / len(tests) * 100

    print(f"\n总成功率: {success_rate:.1f}%")

    if success_rate == 100:
        print("✅ 测试通过！位置敏感性问题已解决。")
    else:
        print("❌ 测试失败！位置敏感性问题仍存在。")

    return success_rate


if __name__ == "__main__":
    print("开始测试图像拼接算法的位置敏感性...")
    success_rate = test_position_sensitivity()
    print(f"测试完成，成功率: {success_rate:.1f}%")
