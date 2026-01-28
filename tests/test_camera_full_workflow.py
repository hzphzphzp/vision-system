#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整相机连接测试 - 模拟实际使用流程

测试：
1. 相机设置对话框连接相机
2. CameraSource执行采集
3. 多次采集测试
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.image_source import CameraSource
from tools.camera_parameter_setting import CameraParameterSettingTool
from modules.camera_manager import CameraManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_full_workflow():
    """测试完整工作流程"""
    logger.info("=" * 60)
    logger.info("完整工作流程测试")
    logger.info("=" * 60)
    
    # 1. 测试CameraManager单例
    logger.info("\n1. 测试CameraManager单例...")
    manager1 = CameraManager()
    manager2 = CameraManager()
    if manager1 is manager2:
        logger.info("✅ CameraManager是单例模式")
    else:
        logger.error("❌ CameraManager不是单例模式")
        return False
    
    # 2. 使用相机设置工具连接相机
    logger.info("\n2. 使用相机设置工具连接相机...")
    setting_tool = CameraParameterSettingTool("camera_settings")
    
    # 获取可用相机
    cameras = setting_tool.get_available_cameras()
    if not cameras:
        logger.error("❌ 未发现相机设备")
        return False
    
    logger.info(f"发现 {len(cameras)} 个相机设备")
    
    # 选择第一个相机
    camera_id = cameras[0].id
    logger.info(f"选择相机: {camera_id}")
    
    # 连接相机
    camera = setting_tool._connect_camera(camera_id)
    if not camera:
        logger.error("❌ 相机连接失败")
        return False
    
    logger.info("✅ 相机连接成功")
    
    # 3. 检查CameraManager中的相机状态
    logger.info("\n3. 检查CameraManager中的相机状态...")
    check_camera = manager1.get_camera(camera_id)
    if check_camera and check_camera.is_connected:
        logger.info(f"✅ CameraManager中存在已连接的相机: {camera_id}")
    else:
        logger.error(f"❌ CameraManager中不存在已连接的相机: {camera_id}")
        return False
    
    # 4. 使用CameraSource进行采集
    logger.info("\n4. 使用CameraSource进行采集...")
    camera_source = CameraSource("test_camera_source")
    camera_source.set_param("camera_id", camera_id.split('_')[-1])  # 使用数字ID
    camera_source.set_param("trigger_mode", "software")
    
    try:
        result = camera_source._run_impl()
        if result and "OutputImage" in result:
            image_data = result["OutputImage"]
            logger.info(f"✅ 第一次采集成功: {image_data.width}x{image_data.height}")
        else:
            logger.error("❌ 第一次采集失败")
            return False
    except Exception as e:
        logger.error(f"❌ 第一次采集异常: {e}")
        return False
    
    # 5. 第二次采集（应该复用已连接的相机）
    logger.info("\n5. 第二次采集（应该复用已连接的相机）...")
    try:
        result = camera_source._run_impl()
        if result and "OutputImage" in result:
            image_data = result["OutputImage"]
            logger.info(f"✅ 第二次采集成功: {image_data.width}x{image_data.height}")
        else:
            logger.error("❌ 第二次采集失败")
            return False
    except Exception as e:
        logger.error(f"❌ 第二次采集异常: {e}")
        return False
    
    # 6. 清理
    logger.info("\n6. 清理...")
    setting_tool._connected_camera = None
    manager1.disconnect(camera_id)
    logger.info("✅ 清理完成")
    
    return True

def main():
    """主测试函数"""
    try:
        success = test_full_workflow()
        
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("🎉 所有测试通过!")
        else:
            logger.info("❌ 测试失败")
        logger.info("=" * 60)
        
        return success
    except Exception as e:
        logger.error(f"测试异常: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
