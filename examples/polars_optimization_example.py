#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Polars优化示例

展示如何使用Polars库进行高性能数据处理

Author: Vision System Team
Date: 2026-01-27
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.performance_optimization import (
    DataProcessor,
    benchmark_data_processing,
)


def test_polars_optimization():
    """
    测试Polars优化性能
    """
    print("测试Polars优化性能...")

    # 运行基准测试
    results = benchmark_data_processing()

    if "polars" in results:
        print("\n性能测试结果:")
        print(f"Python原生处理: {results['python']:.4f}秒")
        print(f"Polars处理: {results['polars']:.4f}秒")
        speedup = results["python"] / results["polars"]
        print(f"性能提升: {speedup:.2f}x")
    else:
        print("\nPolars未安装，无法进行性能测试")


def test_data_processing():
    """
    测试数据处理功能
    """
    print("\n测试数据处理功能...")

    # 生成测试数据
    test_results = [
        {
            "class": "person",
            "confidence": 0.95,
            "x": 100,
            "y": 200,
            "width": 50,
            "height": 100,
        },
        {
            "class": "person",
            "confidence": 0.85,
            "x": 300,
            "y": 150,
            "width": 45,
            "height": 90,
        },
        {
            "class": "car",
            "confidence": 0.90,
            "x": 50,
            "y": 300,
            "width": 100,
            "height": 60,
        },
        {
            "class": "car",
            "confidence": 0.75,
            "x": 200,
            "y": 350,
            "width": 90,
            "height": 55,
        },
        {
            "class": "dog",
            "confidence": 0.65,
            "x": 400,
            "y": 250,
            "width": 30,
            "height": 40,
        },
    ]

    # 处理结果
    df = DataProcessor.process_detection_results(test_results)

    if df is not None:
        print("原始检测结果:")
        print(df)

        # 过滤低置信度
        filtered_df = DataProcessor.filter_by_confidence(df, 0.8)
        print("\n过滤后结果（置信度>=0.8）:")
        print(filtered_df)

        # 按类别分组
        grouped_df = DataProcessor.group_by_class(df)
        print("\n按类别分组统计:")
        print(grouped_df)

        # 计算统计信息
        stats = DataProcessor.compute_statistics(df)
        print("\n统计信息:")
        print(stats)
    else:
        print("Polars未安装，无法测试数据处理功能")


if __name__ == "__main__":
    print("=== Polars优化示例 ===")
    test_data_processing()
    test_polars_optimization()
    print("\n示例完成！")
