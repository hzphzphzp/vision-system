"""
图像拼接算法优化测试脚本
用于验证优化效果和性能提升
"""

import sys
import os
import time
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.vision.image_stitching import ImageStitchingTool
from data.image_data import ImageData


def create_test_images():
    """创建测试图像（模拟重叠图像）"""
    # 创建一个基础图像
    base_width, base_height = 800, 600
    
    # 创建第一个图像
    img1 = np.random.randint(0, 255, (base_height, base_width, 3), dtype=np.uint8)
    # 添加一些特征
    cv2.rectangle(img1, (100, 100), (200, 200), (255, 0, 0), -1)
    cv2.circle(img1, (400, 300), 50, (0, 255, 0), -1)
    cv2.line(img1, (50, 50), (750, 550), (0, 0, 255), 3)
    
    # 创建第二个图像（与第一个有30%重叠）
    img2 = np.zeros((base_height, base_width, 3), dtype=np.uint8)
    # 复制重叠区域
    overlap_width = int(base_width * 0.3)
    img2[:, :overlap_width] = img1[:, -overlap_width:]
    # 添加新内容
    cv2.rectangle(img2, (overlap_width + 100, 150), (overlap_width + 250, 350), (255, 255, 0), -1)
    cv2.circle(img2, (overlap_width + 400, 400), 80, (255, 0, 255), -1)
    
    return img1, img2


def test_performance_mode(mode="balanced"):
    """测试不同性能模式"""
    print(f"\n{'='*60}")
    print(f"测试性能模式: {mode}")
    print(f"{'='*60}")
    
    # 创建工具实例
    tool = ImageStitchingTool()
    tool.set_parameters({
        "performance_mode": mode,
        "feature_detector": "ORB" if mode != "quality" else "SIFT",
        "fast_mode": mode == "fast"
    })
    
    # 创建测试图像
    img1, img2 = create_test_images()
    
    # 转换为ImageData
    image_data1 = ImageData(img1)
    image_data2 = ImageData(img2)
    
    # 执行拼接
    start_time = time.time()
    result = tool.process([image_data1, image_data2])
    total_time = time.time() - start_time
    
    print(f"总处理时间: {total_time:.2f}秒")
    print(f"结果状态: {'成功' if result.status else '失败'}")
    print(f"结果消息: {result.message}")
    
    if result.status:
        stitched_img = result.get_image("stitched_image")
        if stitched_img:
            print(f"输出图像尺寸: {stitched_img.width}x{stitched_img.height}")
    
    return result.status, total_time


def test_feature_detectors():
    """测试不同特征检测器"""
    print(f"\n{'='*60}")
    print("测试不同特征检测器")
    print(f"{'='*60}")
    
    detectors = ["ORB", "SIFT", "AKAZE"]
    results = {}
    
    img1, img2 = create_test_images()
    image_data1 = ImageData(img1)
    image_data2 = ImageData(img2)
    
    for detector in detectors:
        print(f"\n测试检测器: {detector}")
        
        tool = ImageStitchingTool()
        tool.set_parameters({
            "feature_detector": detector,
            "performance_mode": "balanced"
        })
        
        start_time = time.time()
        result = tool.process([image_data1, image_data2])
        total_time = time.time() - start_time
        
        results[detector] = {
            "time": total_time,
            "success": result.status
        }
        
        print(f"  处理时间: {total_time:.2f}秒")
        print(f"  结果: {'成功' if result.status else '失败'}")
    
    return results


def test_ghosting_reduction():
    """测试重影减少效果"""
    print(f"\n{'='*60}")
    print("测试重影减少效果")
    print(f"{'='*60}")
    
    # 创建有明显边缘的测试图像
    img1 = np.ones((600, 800, 3), dtype=np.uint8) * 200
    cv2.rectangle(img1, (100, 100), (300, 400), (0, 0, 0), -1)
    cv2.rectangle(img1, (350, 150), (550, 450), (255, 255, 255), -1)
    
    # 创建第二个图像（有重叠）
    img2 = np.ones((600, 800, 3), dtype=np.uint8) * 200
    overlap = 240
    img2[:, :overlap] = img1[:, -overlap:]
    cv2.rectangle(img2, (overlap + 50, 100), (overlap + 250, 400), (0, 255, 0), -1)
    
    tool = ImageStitchingTool()
    tool.set_parameters({
        "feature_detector": "ORB",
        "performance_mode": "balanced",
        "blend_strength": 3,
        "ransac_reproj_threshold": 3.0
    })
    
    image_data1 = ImageData(img1)
    image_data2 = ImageData(img2)
    
    start_time = time.time()
    result = tool.process([image_data1, image_data2])
    total_time = time.time() - start_time
    
    print(f"处理时间: {total_time:.2f}秒")
    print(f"结果状态: {'成功' if result.status else '失败'}")
    
    if result.status:
        stitched_img = result.get_image("stitched_image")
        if stitched_img:
            # 保存结果以便目视检查
            output_path = "test_stitching_result.jpg"
            cv2.imwrite(output_path, stitched_img.data)
            print(f"结果已保存到: {output_path}")
            print(f"输出尺寸: {stitched_img.width}x{stitched_img.height}")
    
    return result.status


def compare_before_after():
    """对比优化前后的性能"""
    print(f"\n{'='*60}")
    print("性能对比测试")
    print(f"{'='*60}")
    
    img1, img2 = create_test_images()
    image_data1 = ImageData(img1)
    image_data2 = ImageData(img2)
    
    # 测试配置
    configs = [
        {
            "name": "优化配置（ORB + Fast模式）",
            "params": {
                "feature_detector": "ORB",
                "performance_mode": "fast",
                "fast_mode": True,
                "blend_strength": 3
            }
        },
        {
            "name": "平衡配置（ORB + Balanced模式）",
            "params": {
                "feature_detector": "ORB",
                "performance_mode": "balanced",
                "fast_mode": True,
                "blend_strength": 3
            }
        },
        {
            "name": "高质量配置（SIFT + Quality模式）",
            "params": {
                "feature_detector": "SIFT",
                "performance_mode": "quality",
                "fast_mode": False,
                "blend_strength": 5
            }
        }
    ]
    
    results = []
    for config in configs:
        print(f"\n测试: {config['name']}")
        
        times = []
        for i in range(3):  # 运行3次取平均
            tool = ImageStitchingTool()
            tool.set_parameters(config["params"])
            
            start_time = time.time()
            result = tool.process([image_data1, image_data2])
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        results.append({
            "name": config["name"],
            "avg_time": avg_time,
            "success": result.status
        })
        
        print(f"  平均时间: {avg_time:.2f}秒 (3次运行)")
        print(f"  成功率: {'成功' if result.status else '失败'}")
    
    # 打印对比结果
    print(f"\n{'='*60}")
    print("性能对比总结")
    print(f"{'='*60}")
    for r in results:
        print(f"{r['name']}: {r['avg_time']:.2f}秒")
    
    return results


if __name__ == "__main__":
    print("图像拼接算法优化测试")
    print("=" * 60)
    
    try:
        # 1. 测试不同性能模式
        print("\n1. 测试不同性能模式")
        for mode in ["fast", "balanced", "quality"]:
            success, time_taken = test_performance_mode(mode)
        
        # 2. 测试不同特征检测器
        print("\n2. 测试不同特征检测器")
        detector_results = test_feature_detectors()
        
        # 3. 测试重影减少
        print("\n3. 测试重影减少效果")
        ghosting_result = test_ghosting_reduction()
        
        # 4. 性能对比
        print("\n4. 性能对比测试")
        comparison_results = compare_before_after()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
