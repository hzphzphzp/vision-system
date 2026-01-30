#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图像拼接功能的一致性

对同一组测试图片和参数执行至少10次程序关闭重启循环，验证拼接结果的一致性。
测试图片顺序需要不停调换，看看生成的图片是否一致。
"""

import os
import shutil
import time

import cv2
import numpy as np

from data.image_data import ImageData
from tools.image_stitching import ImageStitchingTool

# 测试图片路径
TEST_IMAGE1 = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A1.jpg"
TEST_IMAGE2 = r"E:\工作资料\VM流程文件\python脚本实现拼接算法(免标定板)\A2.jpg"

# 测试结果保存目录
TEST_RESULT_DIR = os.path.join(
    os.path.dirname(__file__), "stitching_consistency_test"
)

# 测试次数
TEST_COUNT = 10


def setup_test_environment():
    """设置测试环境"""
    # 创建测试结果目录
    if not os.path.exists(TEST_RESULT_DIR):
        os.makedirs(TEST_RESULT_DIR)
    else:
        # 清空目录
        for file in os.listdir(TEST_RESULT_DIR):
            file_path = os.path.join(TEST_RESULT_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    print(f"测试环境已设置，结果将保存到: {TEST_RESULT_DIR}")


def load_test_images():
    """加载测试图片"""
    print(f"加载测试图片:")
    print(f"  图片1: {TEST_IMAGE1}")
    print(f"  图片2: {TEST_IMAGE2}")

    # 检查图片是否存在
    if not os.path.exists(TEST_IMAGE1):
        raise FileNotFoundError(f"测试图片不存在: {TEST_IMAGE1}")
    if not os.path.exists(TEST_IMAGE2):
        raise FileNotFoundError(f"测试图片不存在: {TEST_IMAGE2}")

    # 加载图片
    img1 = cv2.imread(TEST_IMAGE1)
    img2 = cv2.imread(TEST_IMAGE2)

    if img1 is None:
        raise Exception(f"无法加载图片: {TEST_IMAGE1}")
    if img2 is None:
        raise Exception(f"无法加载图片: {TEST_IMAGE2}")

    print(f"图片加载成功:")
    print(f"  图片1尺寸: {img1.shape[1]}x{img1.shape[0]}")
    print(f"  图片2尺寸: {img2.shape[1]}x{img2.shape[0]}")

    # 创建ImageData对象
    image_data1 = ImageData(data=img1)
    image_data2 = ImageData(data=img2)

    return image_data1, image_data2


def test_stitching_consistency():
    """测试图像拼接的一致性"""
    print("=== 开始测试图像拼接一致性 ===")

    # 设置测试环境
    setup_test_environment()

    # 加载测试图片
    img1, img2 = load_test_images()

    # 保存原始图片
    cv2.imwrite(os.path.join(TEST_RESULT_DIR, "original_A1.jpg"), img1.data)
    cv2.imwrite(os.path.join(TEST_RESULT_DIR, "original_A2.jpg"), img2.data)

    # 存储所有测试结果
    all_results = []
    all_times = []

    for i in range(TEST_COUNT):
        print(f"\n=== 测试 {i+1}/{TEST_COUNT} ===")

        # 随机调换图片顺序
        if i % 2 == 0:
            input_images = [img1, img2]
            order = "A1_A2"
        else:
            input_images = [img2, img1]
            order = "A2_A1"

        print(f"  图片顺序: {order}")

        # 每次测试都创建新的拼接工具实例（模拟程序重启）
        stitcher = ImageStitchingTool()

        # 设置参数
        stitcher.set_parameters(
            {
                "feature_detector": "SIFT",
                "matcher_type": "FLANN",
                "min_match_count": 10,
                "ransac_reproj_threshold": 4.0,
                "blend_method": "multi_band",
                "blend_strength": 5,
                "parallel_processing": False,  # 禁用并行处理，确保结果一致
            }
        )

        # 执行拼接
        start_time = time.time()
        result = stitcher.process(input_images)
        processing_time = time.time() - start_time

        # 记录处理时间
        all_times.append(processing_time)

        print(f"  处理时间: {processing_time:.2f}秒")
        print(f"  拼接状态: {'成功' if result.status else '失败'}")
        print(f"  拼接消息: {result.message}")

        if result.status:
            # 获取拼接结果
            stitched_image = result.get_image("stitched_image")
            if stitched_image:
                print(
                    f"  拼接结果尺寸: {stitched_image.width}x{stitched_image.height}"
                )

                # 保存拼接结果
                result_path = os.path.join(
                    TEST_RESULT_DIR, f"stitched_result_{i+1}_{order}.jpg"
                )
                cv2.imwrite(result_path, stitched_image.data)
                print(f"  拼接结果已保存: {result_path}")

                # 存储结果
                all_results.append(
                    {
                        "test_id": i + 1,
                        "order": order,
                        "status": result.status,
                        "message": result.message,
                        "width": stitched_image.width,
                        "height": stitched_image.height,
                        "processing_time": processing_time,
                        "image_data": stitched_image.data,
                    }
                )
        else:
            print(f"  拼接失败: {result.message}")
            all_results.append(
                {
                    "test_id": i + 1,
                    "order": order,
                    "status": result.status,
                    "message": result.message,
                    "width": 0,
                    "height": 0,
                    "processing_time": processing_time,
                    "image_data": None,
                }
            )

    # 验证结果一致性
    validate_results(all_results)

    # 生成测试报告
    generate_test_report(all_results, all_times)


def validate_results(all_results):
    """验证拼接结果的一致性"""
    print("\n=== 验证拼接结果一致性 ===")

    # 过滤成功的结果
    successful_results = [
        r for r in all_results if r["status"] and r["image_data"] is not None
    ]

    if not successful_results:
        print("  没有成功的拼接结果，无法验证一致性")
        return

    print(
        f"  成功的拼接结果数量: {len(successful_results)}/{len(all_results)}"
    )

    # 检查所有成功结果的尺寸是否一致
    widths = [r["width"] for r in successful_results]
    heights = [r["height"] for r in successful_results]

    width_consistent = len(set(widths)) == 1
    height_consistent = len(set(heights)) == 1

    print(
        f"  宽度一致: {'是' if width_consistent else '否'} (值: {set(widths)})"
    )
    print(
        f"  高度一致: {'是' if height_consistent else '否'} (值: {set(heights)})"
    )

    # 检查所有成功结果的图像数据是否一致
    if len(successful_results) > 1:
        first_image = successful_results[0]["image_data"]
        all_same = True

        for i, result in enumerate(successful_results[1:], 2):
            current_image = result["image_data"]

            # 检查尺寸是否相同
            if first_image.shape != current_image.shape:
                print(
                    f"  结果 {i} 与结果 1 尺寸不同: {first_image.shape} vs {current_image.shape}"
                )
                all_same = False
                continue

            # 检查像素值是否相同
            diff = cv2.absdiff(first_image, current_image)
            mean_diff = np.mean(diff)
            max_diff = np.max(diff)

            print(
                f"  结果 {i} 与结果 1 像素差异: 均值={mean_diff:.2f}, 最大值={max_diff}"
            )

            if mean_diff > 1 or max_diff > 10:
                all_same = False

        if all_same:
            print("  ✅ 所有拼接结果一致!")
        else:
            print("  ❌ 拼接结果不一致!")

    # 检查不同顺序的结果是否一致
    order_a1_a2 = [r for r in successful_results if r["order"] == "A1_A2"]
    order_a2_a1 = [r for r in successful_results if r["order"] == "A2_A1"]

    if order_a1_a2 and order_a2_a1:
        print(f"\n  不同顺序的结果比较:")
        print(f"    A1_A2 顺序结果数: {len(order_a1_a2)}")
        print(f"    A2_A1 顺序结果数: {len(order_a2_a1)}")

        # 比较两种顺序的结果
        a1_a2_result = order_a1_a2[0]
        a2_a1_result = order_a2_a1[0]

        print(
            f"    A1_A2 尺寸: {a1_a2_result['width']}x{a1_a2_result['height']}"
        )
        print(
            f"    A2_A1 尺寸: {a2_a1_result['width']}x{a2_a1_result['height']}"
        )

        if (
            a1_a2_result["width"] == a2_a1_result["width"]
            and a1_a2_result["height"] == a2_a1_result["height"]
        ):
            print("    ✅ 不同顺序的结果尺寸一致")
        else:
            print("    ❌ 不同顺序的结果尺寸不一致")


def generate_test_report(all_results, all_times):
    """生成测试报告"""
    print("\n=== 测试报告 ===")
    print(f"测试次数: {TEST_COUNT}")
    print(f"平均处理时间: {np.mean(all_times):.2f}秒")
    print(f"最长处理时间: {np.max(all_times):.2f}秒")
    print(f"最短处理时间: {np.min(all_times):.2f}秒")

    # 统计成功和失败的次数
    success_count = sum(1 for r in all_results if r["status"])
    failure_count = sum(1 for r in all_results if not r["status"])

    print(f"成功次数: {success_count}")
    print(f"失败次数: {failure_count}")
    print(f"成功率: {success_count/TEST_COUNT*100:.1f}%")

    # 生成详细报告文件
    report_path = os.path.join(TEST_RESULT_DIR, "test_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== 图像拼接一致性测试报告 ===\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试次数: {TEST_COUNT}\n")
        f.write(f"测试图片1: {TEST_IMAGE1}\n")
        f.write(f"测试图片2: {TEST_IMAGE2}\n")
        f.write(f"平均处理时间: {np.mean(all_times):.2f}秒\n")
        f.write(f"最长处理时间: {np.max(all_times):.2f}秒\n")
        f.write(f"最短处理时间: {np.min(all_times):.2f}秒\n")
        f.write(f"成功次数: {success_count}\n")
        f.write(f"失败次数: {failure_count}\n")
        f.write(f"成功率: {success_count/TEST_COUNT*100:.1f}%\n\n")

        f.write("=== 详细测试结果 ===\n")
        for i, result in enumerate(all_results, 1):
            f.write(f"测试 {i}:\n")
            f.write(f"  图片顺序: {result['order']}\n")
            f.write(f"  状态: {'成功' if result['status'] else '失败'}\n")
            f.write(f"  消息: {result['message']}\n")
            if result["status"]:
                f.write(f"  尺寸: {result['width']}x{result['height']}\n")
            f.write(f"  处理时间: {result['processing_time']:.2f}秒\n\n")

    print(f"\n详细测试报告已保存: {report_path}")


if __name__ == "__main__":
    try:
        test_stitching_consistency()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
