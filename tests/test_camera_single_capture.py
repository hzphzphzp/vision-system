#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机连接和单次采集测试

测试相机连接、软触发采集功能
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_source import CameraSource
from modules.camera_manager import CameraManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_camera_connection():
    """测试相机连接和采集"""
    logger.info("开始测试相机连接和采集...")
    
    # 创建CameraSource实例
    camera_tool = CameraSource("test_camera")
    
    # 检查默认参数
    trigger_mode = camera_tool.get_param("trigger_mode", "continuous")
    logger.info(f"当前触发模式: {trigger_mode}")
    
    if trigger_mode != "software":
        logger.warning(f"触发模式不是software，当前为: {trigger_mode}")
        camera_tool.set_param("trigger_mode", "software")
        logger.info("已将触发模式设置为software")
    
    try:
        # 执行采集
        logger.info("开始执行相机采集...")
        result = camera_tool._run_impl()
        
        if result and "OutputImage" in result:
            image_data = result["OutputImage"]
            logger.info(f"✅ 成功采集图像!")
            logger.info(f"   - 分辨率: {image_data.width}x{image_data.height}")
            logger.info(f"   - 通道数: {image_data.channels}")
            logger.info(f"   - 相机ID: {result.get('camera_id', 'unknown')}")
            logger.info(f"   - 触发模式: {result.get('trigger_mode', 'unknown')}")
            return True
        else:
            logger.error("❌ 采集结果为空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 相机采集失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_camera_manager_direct():
    """直接测试CameraManager的连接和采集"""
    logger.info("\n直接测试CameraManager...")
    
    camera_manager = CameraManager()
    
    # 发现设备
    cameras = camera_manager.discover_devices()
    if not cameras:
        logger.error("未发现任何相机设备")
        return False
    
    logger.info(f"发现 {len(cameras)} 个相机设备")
    
    # 连接第一个相机
    camera_id = cameras[0].id
    logger.info(f"连接相机: {camera_id}")
    
    camera = camera_manager.connect(camera_id)
    if not camera:
        logger.error("相机连接失败")
        return False
    
    logger.info("相机连接成功")
    
    # 设置为软触发模式
    logger.info("设置为软触发模式...")
    if not camera.set_trigger_mode("software"):
        logger.error("设置软触发模式失败")
        return False
    
    # 开始采集
    logger.info("开始采集图像...")
    if not camera.start_grabbing():
        logger.error("开始取流失败")
        return False
    
    # 发送软触发
    logger.info("发送软触发信号...")
    if not camera.trigger_software():
        logger.error("软触发失败")
        return False
    
    # 采集一帧
    image_data = camera.capture_frame(timeout_ms=2000)
    if not image_data:
        logger.error("采集图像失败")
        return False
    
    logger.info(f"✅ 成功采集图像: {image_data.width}x{image_data.height}")
    
    # 断开相机
    camera_manager.disconnect(camera_id)
    logger.info("相机已断开")
    
    return True

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("相机连接和单次采集测试")
    logger.info("=" * 60)
    
    # 先测试直接CameraManager连接
    success1 = test_camera_manager_direct()
    
    # 再测试CameraSource
    success2 = test_camera_connection()
    
    logger.info("\n" + "=" * 60)
    if success1 and success2:
        logger.info("🎉 所有测试通过!")
    else:
        logger.info("⚠️ 部分测试失败")
        if not success1:
            logger.info("  - CameraManager直接测试失败")
        if not success2:
            logger.info("  - CameraSource测试失败")
    logger.info("=" * 60)
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
