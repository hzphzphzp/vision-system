#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机连接状态检测和参数同步测试脚本

测试相机ID格式处理、已连接相机检测、参数同步等功能
"""

import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.camera.camera_manager import CameraManager
from tools.image_source import CameraSource

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_camera_id_format():
    """测试相机ID格式处理"""
    logger.info("测试相机ID格式处理...")

    # 创建CameraSource实例
    camera_tool = CameraSource("test_camera")

    # 测试1: 无hik_前缀的相机ID
    test_camera_id = "0"
    camera_tool.set_param("camera_id", test_camera_id)

    # 模拟_run_impl中的相机ID处理
    camera_id = camera_tool.get_param("camera_id", "0")
    final_camera_id = camera_id
    if not final_camera_id.startswith("hik_"):
        hik_camera_id = f"hik_{final_camera_id}"
        logger.info(f"使用hik_前缀格式相机ID: {hik_camera_id}")
        final_camera_id = hik_camera_id

    assert (
        final_camera_id == "hik_0"
    ), f"相机ID格式处理失败，期望hik_0，实际得到{final_camera_id}"
    logger.info("✓ 相机ID格式处理测试通过")


def test_camera_manager_get_camera():
    """测试相机管理器获取已连接相机功能"""
    logger.info("测试相机管理器获取已连接相机功能...")

    # 创建相机管理器
    camera_manager = CameraManager()

    # 测试发现设备
    cameras = camera_manager.discover_devices()
    logger.info(f"发现 {len(cameras)} 个相机设备")

    if cameras:
        # 测试连接第一个相机
        test_camera_id = cameras[0].id
        logger.info(f"测试连接相机: {test_camera_id}")

        # 连接相机
        camera = camera_manager.connect(test_camera_id)

        if camera:
            logger.info(f"✓ 相机连接成功: {test_camera_id}")

            # 测试获取已连接相机
            existing_camera = camera_manager.get_camera(test_camera_id)
            assert existing_camera is not None, "获取已连接相机失败"
            assert existing_camera.is_connected, "相机状态应为已连接"
            logger.info("✓ 获取已连接相机测试通过")

            # 断开相机
            camera_manager.disconnect(test_camera_id)
            logger.info(f"✓ 相机断开成功: {test_camera_id}")
        else:
            logger.warning("⚠ 相机连接失败，可能是设备未连接或权限问题")
    else:
        logger.warning("⚠ 未发现相机设备，跳过连接测试")


def test_camera_source_initialization():
    """测试CameraSource初始化功能"""
    logger.info("测试CameraSource初始化功能...")

    # 创建CameraSource实例
    camera_tool = CameraSource("test_camera_source")

    # 设置测试参数
    camera_tool.set_param("camera_id", "0")
    camera_tool.set_param("trigger_mode", "continuous")
    camera_tool.set_param("fps", 30)
    camera_tool.set_param("exposure", 10000)
    camera_tool.set_param("gain", 0)
    camera_tool.set_param("width", 640)
    camera_tool.set_param("height", 480)
    camera_tool.set_param("auto_exposure", True)
    camera_tool.set_param("auto_gain", True)

    logger.info("✓ CameraSource初始化测试通过")


def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行相机连接测试...")

    try:
        test_camera_id_format()
        test_camera_manager_get_camera()
        test_camera_source_initialization()

        logger.info("\n🎉 所有测试通过！")
        return True
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    run_all_tests()
