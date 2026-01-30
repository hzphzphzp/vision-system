#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU优化模块使用示例

展示CPU优化模块的各种使用方式和最佳实践

Author: Vision System Team
Date: 2026-01-26
"""

import os
import sys
import time
import numpy as np
import cv2
from pathlib import Path

# 添加模块路径
_module_path = Path(__file__).parent
if str(_module_path) not in sys.path:
    sys.path.insert(0, str(_module_path))


def example_basic_usage():
    """基本使用示例"""
    print("\n" + "=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)

    from modules.cpu_optimization import YOLO26CPUDetector, CPUInferenceConfig

    # 创建检测器
    config = CPUInferenceConfig(num_threads=4, conf_threshold=0.25, nms_threshold=0.45)

    detector = YOLO26CPUDetector(config)

    # 检查模型是否存在
    model_path = "models/yolo26n.onnx"
    if os.path.exists(model_path):
        if detector.load_model(model_path):
            # 预热模型
            detector.warmup(5)

            # 创建测试图像
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

            # 检测
            start = time.time()
            result = detector.detect(test_image)
            elapsed = (time.time() - start) * 1000

            print(f"检测到 {len(result.boxes)} 个目标")
            print(f"总耗时: {elapsed:.2f}ms")
            print(f"  - 预处理: {result.preprocess_time_ms:.2f}ms")
            print(f"  - 推理: {result.inference_time_ms:.2f}ms")
            print(f"  - 后处理: {result.postprocess_time_ms:.2f}ms")

            # 性能统计
            stats = detector.get_performance_stats()
            print(f"平均FPS: {stats['avg_fps']:.1f}")

            detector.release()
        else:
            print(f"模型加载失败: {model_path}")
    else:
        print(f"模型文件不存在: {model_path}")
        print("请提供有效的ONNX模型文件进行测试")


def example_parallel_processing():
    """并行处理示例"""
    print("\n" + "=" * 60)
    print("示例2: 并行处理")
    print("=" * 60)

    from modules.cpu_optimization import (
        ParallelEngine,
        parallel_for_range,
        batch_process,
    )

    engine = ParallelEngine()
    print(f"CPU核心数: {engine.cpu_count}")
    print(f"工作线程数: {engine.get_worker_count()}")

    # 并行计算示例
    def process_item(x):
        time.sleep(0.1)  # 模拟处理
        return x**2

    # 并行for循环
    print("\n并行for循环测试:")
    start = time.time()
    results = parallel_for_range(0, 10, process_item, workers=4)
    elapsed = time.time() - start
    print(f"  结果: {results}")
    print(f"  耗时: {elapsed:.3f}秒")

    # 批量处理
    print("\n批量处理测试:")
    data = list(range(20))
    start = time.time()
    results = batch_process(
        data, process_func=process_item, batch_size=5, show_progress=True
    )
    elapsed = time.time() - start
    print(f"  处理数量: {len(results)}")
    print(f"  耗时: {elapsed:.3f}秒")


def example_memory_pool():
    """内存池示例"""
    print("\n" + "=" * 60)
    print("示例3: 内存池管理")
    print("=" * 60)

    from modules.cpu_optimization import MemoryPool, ImageMemoryPool, get_memory_pool

    # 使用全局内存池
    pool = get_memory_pool()

    # 创建自定义池
    pool.create_pool("test_pool", 1024, 100, dtype=np.float32)
    print("已创建测试内存池")

    # 获取和使用内存块
    block = pool.get("test_pool")
    if block is not None:
        print(f"获取内存块: shape={block.shape}, size={block.nbytes}")
        # 使用内存块
        block[:] = np.random.randn(*block.shape)
        # 释放回池
        pool.release("test_pool", block)
        print("内存块已释放")

    # 统计信息
    stats = pool.get_stats()
    print(f"\n内存池统计:")
    print(f"  总分配: {stats['total_allocated_mb']:.2f} MB")
    print(f"  命中率: {stats['hit_rate']}")

    # 图像处理内存池
    print("\n图像处理内存池:")
    img_pool = ImageMemoryPool()

    with img_pool.image_context(640, 480, 3) as img:
        print(f"  图像缓冲区: shape={img.shape}")
        img[:] = 128  # 填充


def example_simd_optimization():
    """SIMD优化示例"""
    print("\n" + "=" * 60)
    print("示例4: SIMD优化")
    print("=" * 60)

    from modules.cpu_optimization import get_simd_optimizer

    optimizer = get_simd_optimizer()
    caps = optimizer.capabilities

    print("SIMD能力:")
    print(f"  优化级别: {caps.optimization_level}")
    print(f"  SSE2: {caps.sse2}")
    print(f"  SSE3: {caps.sse3}")
    print(f"  SSE4.1: {caps.sse4_1}")
    print(f"  SSE4.2: {caps.sse4_2}")
    print(f"  AVX: {caps.avx}")
    print(f"  AVX2: {caps.avx2}")
    print(f"  AVX512: {caps.avx512f}")

    # 测试优化函数
    print("\n优化函数测试:")

    # ReLU
    data = np.random.randn(1000, 1000).astype(np.float32)
    result = optimizer._optimized_relu(data)
    print(f"  ReLU: output shape={result.shape}")

    # Softmax
    data = np.random.randn(100, 10).astype(np.float32)
    result = optimizer._optimized_softmax(data)
    print(f"  Softmax: output shape={result.shape}, sum={result.sum(axis=1)[0]:.4f}")

    # 量化
    data = np.random.randn(1000).astype(np.float32) * 10
    quantized, scale, zp = optimizer.quantize(data, 8)
    dequantized = optimizer.dequantize(quantized, scale, zp)
    error = np.abs(data - dequantized).mean()
    print(f"  量化: 原始范围=[{data.min():.2f}, {data.max():.2f}], 误差={error:.6f}")


def example_api_usage():
    """API接口示例"""
    print("\n" + "=" * 60)
    print("示例5: API接口使用")
    print("=" * 60)

    from modules.cpu_optimization import CPUDetectorAPI, APIConfig

    # 创建API
    config = APIConfig(num_threads=4, confidence_threshold=0.25)

    api = CPUDetectorAPI(config)

    # 获取配置
    print("当前配置:")
    current_config = api.get_config()
    for key, value in current_config.items():
        print(f"  {key}: {value}")

    # 动态调整配置
    api.set_config(confidence_threshold=0.3)
    print("\n已调整置信度阈值到 0.3")

    # 注册回调
    def on_detection_complete(data):
        print(f"  检测完成: {data['num_boxes']} 个目标")

    api.register_callback("on_detection_complete", on_detection_complete)

    # 检查状态
    print(f"\n当前状态: {api.get_state()}")


def example_performance_monitoring():
    """性能监控示例"""
    print("\n" + "=" * 60)
    print("示例6: 性能监控")
    print("=" * 60)

    from modules.cpu_optimization import PerformanceMonitor, PerformanceWidget

    # 创建监控器
    monitor = PerformanceMonitor(sample_interval=0.5)
    monitor.start()

    # 创建显示窗口
    widget = PerformanceWidget(monitor)
    widget.show()

    # 模拟推理过程
    print("\n模拟推理过程:")
    for i in range(5):
        time.sleep(0.3)
        inference_time = 30 + np.random.randn() * 10
        monitor.record_inference(inference_time)
        print(f"  推理 {i+1}: {inference_time:.2f}ms")

    # 获取统计信息
    print("\n性能统计:")
    stats = monitor.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    # 打印摘要
    monitor.print_summary()

    # 停止监控
    monitor.stop()


def example_batch_detection():
    """批量检测示例"""
    print("\n" + "=" * 60)
    print("示例7: 批量检测")
    print("=" * 60)

    from modules.cpu_optimization import create_yolo26_detector, CPUInferenceConfig

    # 创建检测器
    detector = create_yolo26_detector(
        "models/yolo26n.onnx", CPUInferenceConfig(num_threads=4)
    )

    if detector.is_loaded:
        # 创建测试图像列表
        images = [
            np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(5)
        ]

        print("批量检测测试:")
        start = time.time()

        # 逐个检测
        results = []
        for i, image in enumerate(images):
            result = detector.detect(image)
            results.append(result)
            print(
                f"  图像 {i+1}: {len(result.boxes)} 个目标, {result.inference_time_ms:.2f}ms"
            )

        elapsed = (time.time() - start) * 1000
        total_boxes = sum(len(r.boxes) for r in results)

        print(f"\n总耗时: {elapsed:.2f}ms")
        print(f"总检测数: {total_boxes}")
        print(f"平均每张: {elapsed/5:.2f}ms")

        detector.release()


def example_integration_with_cv2():
    """与OpenCV集成示例"""
    print("\n" + "=" * 60)
    print("示例8: 与OpenCV集成")
    print("=" * 60)

    from modules.cpu_optimization import create_yolo26_detector, CPUInferenceConfig

    # 创建检测器
    detector = create_yolo26_detector(
        "models/yolov8n.onnx", CPUInferenceConfig(num_threads=4)
    )

    if detector.is_loaded:
        # 读取图像
        image_path = "test.jpg"
        if os.path.exists(image_path):
            image = cv2.imread(image_path)

            # 检测
            result = detector.detect(image)

            # 绘制结果
            for box in result.boxes:
                x1 = int(box.x1 * image.shape[1])
                y1 = int(box.y1 * image.shape[0])
                x2 = int(box.x2 * image.shape[1])
                y2 = int(box.y2 * image.shape[0])

                # 随机颜色
                color = tuple(np.random.randint(0, 255, 3).tolist())

                # 绘制边界框
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                # 绘制标签
                label = f"{box.class_name}: {box.confidence:.2f}"
                cv2.putText(
                    image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
                )

            # 保存结果
            cv2.imwrite("detected_result.jpg", image)
            print(f"检测结果已保存到: detected_result.jpg")
            print(f"检测到 {len(result.boxes)} 个目标")

        detector.release()


def example_full_integration():
    """完整集成示例"""
    print("\n" + "=" * 60)
    print("示例9: 完整集成示例")
    print("=" * 60)

    from modules.cpu_optimization import (
        create_yolo26_detector,
        CPUInferenceConfig,
        get_performance_monitor,
        get_memory_pool,
    )

    # 初始化组件
    detector = create_yolo26_detector(
        "models/yolo26n.onnx", CPUInferenceConfig(num_threads=4, conf_threshold=0.25)
    )

    monitor = get_performance_monitor(0.5)
    monitor.start()

    pool = get_memory_pool()

    if detector.is_loaded:
        print("开始实时检测演示...")

        # 创建测试图像
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # 模拟实时处理
        for frame in range(10):
            # 检测
            result = detector.detect(test_image)

            # 记录性能
            monitor.record_inference(result.inference_time_ms)

            if frame % 5 == 0:
                # 打印性能摘要
                print(f"\n帧 {frame}:")
                metrics = monitor.get_current_metrics()
                print(f"  CPU: {metrics.cpu_percent:.1f}%")
                print(f"  内存: {metrics.memory_used_mb:.1f} MB")
                print(f"  FPS: {metrics.fps:.1f}")
                print(f"  推理时间: {result.inference_time_ms:.2f}ms")

        # 打印最终统计
        print("\n最终统计:")
        summary = monitor.get_summary()
        for section, items in summary.items():
            print(f"\n{section}:")
            for key, value in items.items():
                print(f"  {key}: {value}")

        # 清理
        detector.release()
        monitor.stop()


def main():
    """主函数"""
    print("=" * 60)
    print("  CPU优化模块使用示例")
    print("=" * 60)

    # 运行所有示例
    examples = [
        ("基本使用", example_basic_usage),
        ("并行处理", example_parallel_processing),
        ("内存池管理", example_memory_pool),
        ("SIMD优化", example_simd_optimization),
        ("API接口", example_api_usage),
        ("性能监控", example_performance_monitoring),
        ("批量检测", example_batch_detection),
        ("OpenCV集成", example_integration_with_cv2),
        ("完整集成", example_full_integration),
    ]

    for i, (name, func) in enumerate(examples):
        try:
            func()
        except Exception as e:
            print(f"\n示例 '{name}' 执行失败: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
