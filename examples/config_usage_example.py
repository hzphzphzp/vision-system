#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置使用示例

展示如何使用配置管理器加载、修改和保存配置

Author: Vision System Team
Date: 2026-01-27
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import (
    get_config,
    get_full_config,
    reload_config,
    save_config,
    set_config,
    update_config,
    validate_config,
)


def test_basic_config_operations():
    """
    测试基本配置操作
    """
    print("测试基本配置操作...")

    # 获取配置
    print("\n1. 获取配置:")
    system_name = get_config("system.name")
    camera_id = get_config("camera.default_id")
    threshold = get_config("image_processing.default_threshold")

    print(f"系统名称: {system_name}")
    print(f"相机默认ID: {camera_id}")
    print(f"默认阈值: {threshold}")

    # 设置配置
    print("\n2. 设置配置:")
    set_config("system.debug", True)
    set_config("camera.default_id", 1)
    set_config("image_processing.default_threshold", 150)

    # 获取更新后的配置
    print("\n3. 获取更新后的配置:")
    debug_mode = get_config("system.debug")
    updated_camera_id = get_config("camera.default_id")
    updated_threshold = get_config("image_processing.default_threshold")

    print(f"调试模式: {debug_mode}")
    print(f"更新后相机默认ID: {updated_camera_id}")
    print(f"更新后默认阈值: {updated_threshold}")

    # 保存配置
    print("\n4. 保存配置:")
    save_config()

    # 验证配置
    print("\n5. 验证配置:")
    validate_config()


def test_nested_config():
    """
    测试嵌套配置
    """
    print("\n\n测试嵌套配置...")

    # 获取嵌套配置
    print("\n1. 获取嵌套配置:")
    ocr_language = get_config("ocr.language")
    ocr_confidence = get_config("ocr.min_confidence")

    print(f"OCR语言: {ocr_language}")
    print(f"OCR最小置信度: {ocr_confidence}")

    # 设置嵌套配置
    print("\n2. 设置嵌套配置:")
    set_config("ocr.language", "ch_sim+en")
    set_config("ocr.min_confidence", 0.6)

    # 获取更新后的嵌套配置
    print("\n3. 获取更新后的嵌套配置:")
    updated_ocr_language = get_config("ocr.language")
    updated_ocr_confidence = get_config("ocr.min_confidence")

    print(f"更新后OCR语言: {updated_ocr_language}")
    print(f"更新后OCR最小置信度: {updated_ocr_confidence}")


def test_config_update():
    """
    测试配置更新
    """
    print("\n\n测试配置更新...")

    # 准备更新配置
    update_data = {
        "system": {"log_level": "DEBUG", "max_concurrent_tools": 15},
        "performance": {"enable_gpu": True, "batch_size": 4},
    }

    # 更新配置
    print("\n1. 更新配置:")
    update_config(update_data)

    # 获取更新后的配置
    print("\n2. 获取更新后的配置:")
    log_level = get_config("system.log_level")
    max_tools = get_config("system.max_concurrent_tools")
    enable_gpu = get_config("performance.enable_gpu")
    batch_size = get_config("performance.batch_size")

    print(f"日志级别: {log_level}")
    print(f"最大并发工具数: {max_tools}")
    print(f"启用GPU: {enable_gpu}")
    print(f"批量大小: {batch_size}")


def test_full_config():
    """
    测试获取完整配置
    """
    print("\n\n测试获取完整配置...")

    # 获取完整配置
    full_config = get_full_config()
    print(f"完整配置包含 {len(full_config)} 个部分:")
    for section in full_config:
        print(f"- {section}")


def test_reload_config():
    """
    测试重新加载配置
    """
    print("\n\n测试重新加载配置...")

    # 修改配置
    set_config("system.debug", False)
    print(f"修改前调试模式: {get_config('system.debug')}")

    # 保存配置
    save_config()

    # 再次修改配置
    set_config("system.debug", True)
    print(f"修改后调试模式: {get_config('system.debug')}")

    # 重新加载配置
    reload_config()
    print(f"重新加载后调试模式: {get_config('system.debug')}")


def test_default_values():
    """
    测试默认值
    """
    print("\n\n测试默认值...")

    # 获取存在的配置
    existing_config = get_config("system.name")
    print(f"存在的配置: {existing_config}")

    # 获取不存在的配置，使用默认值
    non_existent_config = get_config(
        "non_existent.section.key", "default_value"
    )
    print(f"不存在的配置（使用默认值）: {non_existent_config}")


if __name__ == "__main__":
    print("=== 配置管理器使用示例 ===")

    # 运行所有测试
    test_basic_config_operations()
    test_nested_config()
    test_config_update()
    test_full_config()
    test_reload_config()
    test_default_values()

    print("\n=== 配置管理器使用示例完成 ===")
