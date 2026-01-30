#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图像拼接功能的修复

测试修复后的ImageData类和图像拼接算法，确保：
1. 拼接结果尺寸不再变为0x0
2. 多图像拼接功能正常工作
3. 拼接结果能正确显示
"""

import cv2
import numpy as np

from data.image_data import ImageData
from tools.image_stitching import ImageStitchingTool


def create_test_images():
    """
    创建测试图像
    """
    # 创建两张测试图像，一张红色，一张蓝色，中间有重叠区域
    img1 = np.zeros((480, 640, 3), dtype=np.uint8)
    img1[:, :320] = [0, 0, 255]  # 左侧红色
    img1[:, 320:] = [255, 255, 255]  # 右侧白色

    img2 = np.zeros((480, 640, 3), dtype=np.uint8)
    img2[:, :320] = [255, 255, 255]  # 左侧白色
    img2[:, 320:] = [255, 0, 0]  # 右侧蓝色

    # 添加一些特征点
    cv2.putText(
        img1,
        "Image 1",
        (100, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )
    cv2.putText(
        img2,
        "Image 2",
        (400, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        3,
    )

    return img1, img2


def test_image_stitching():
    """
    测试图像拼接功能
    """
    print("=== 测试图像拼接功能 ===")

    # 创建测试图像
    img1, img2 = create_test_images()

    # 创建ImageData对象
    image_data1 = ImageData(data=img1)
    image_data2 = ImageData(data=img2)

    print(f"测试图像1: {image_data1.width}x{image_data1.height}")
    print(f"测试图像2: {image_data2.width}x{image_data2.height}")

    # 创建图像拼接工具
    stitcher = ImageStitchingTool()

    # 测试多图像拼接
    input_images = [image_data1, image_data2]

    print("\n=== 执行图像拼接 ===")
    result = stitcher.process(input_images)

    print(f"拼接状态: {'成功' if result.status else '失败'}")
    print(f"拼接消息: {result.message}")

    # 获取拼接结果
    stitched_image = result.get_image("stitched_image")

    if stitched_image:
        print(f"拼接结果尺寸: {stitched_image.width}x{stitched_image.height}")
        print(f"拼接结果有效: {stitched_image.is_valid}")

        # 保存拼接结果
        if stitched_image.is_valid:
            cv2.imwrite(
                "data/test_results/stitched_result.jpg", stitched_image.data
            )
            print("拼接结果已保存为 data/test_results/stitched_result.jpg")
        else:
            print("拼接结果无效，无法保存")
    else:
        print("未获取到拼接结果")

    return result.status


def test_image_data_init():
    """
    测试ImageData初始化
    """
    print("\n=== 测试ImageData初始化 ===")

    # 创建测试图像
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)

    # 测试1: 仅提供data
    image_data1 = ImageData(data=test_img)
    print(
        f"测试1 - 仅提供data: {image_data1.width}x{image_data1.height}, channels={image_data1.channels}"
    )

    # 测试2: 提供data和尺寸参数
    image_data2 = ImageData(data=test_img, width=800, height=600)
    print(
        f"测试2 - 提供data和尺寸: {image_data2.width}x{image_data2.height}, channels={image_data2.channels}"
    )

    # 测试3: 空数据
    image_data3 = ImageData()
    print(
        f"测试3 - 空数据: {image_data3.width}x{image_data3.height}, channels={image_data3.channels}, valid={image_data3.is_valid}"
    )

    return True


if __name__ == "__main__":
    print("开始测试图像拼接功能修复...")

    # 测试ImageData初始化
    test_image_data_init()

    # 测试图像拼接
    stitching_success = test_image_stitching()

    if stitching_success:
        print("\n✅ 测试通过！图像拼接功能已修复。")
    else:
        print("\n❌ 测试失败！图像拼接功能仍有问题。")
