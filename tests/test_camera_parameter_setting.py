#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相机参数设置模块测试

测试相机参数设置工具的基本功能和导入情况。

Author: Vision System Team
Date: 2026-01-28
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


class TestCameraParameterSetting(unittest.TestCase):
    """相机参数设置模块测试"""

    def test_import_camera_parameter_setting_tool(self):
        """测试相机参数设置工具的导入"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            self.assertIsNotNone(CameraParameterSettingTool)
            print("✓ 相机参数设置工具导入成功")
        except ImportError as e:
            self.fail(f"相机参数设置工具导入失败: {e}")

    def test_camera_parameter_setting_tool_initialization(self):
        """测试相机参数设置工具的初始化"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            tool = CameraParameterSettingTool("test_camera_setting")
            self.assertIsNotNone(tool)
            self.assertEqual(tool.name, "test_camera_setting")
            self.assertEqual(tool.tool_name, "相机参数设置")
            self.assertEqual(tool.tool_category, "ImageSource")
            print("✓ 相机参数设置工具初始化成功")
        except Exception as e:
            self.fail(f"相机参数设置工具初始化失败: {e}")

    def test_camera_parameter_setting_tool_parameters(self):
        """测试相机参数设置工具的参数"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            tool = CameraParameterSettingTool()

            # 测试默认参数值
            self.assertEqual(tool.get_param("camera_id"), "")
            self.assertEqual(tool.get_param("exposure"), 10000.0)
            self.assertEqual(tool.get_param("gain"), 0.0)
            self.assertEqual(tool.get_param("gamma"), 1.0)
            self.assertEqual(tool.get_param("width"), 1920)
            self.assertEqual(tool.get_param("height"), 1080)
            self.assertEqual(tool.get_param("fps"), 30.0)
            self.assertEqual(tool.get_param("trigger_mode"), "continuous")
            self.assertEqual(tool.get_param("auto_exposure"), True)
            self.assertEqual(tool.get_param("auto_gain"), True)

            print("✓ 相机参数设置工具默认参数测试成功")
        except Exception as e:
            self.fail(f"相机参数设置工具参数测试失败: {e}")

    def test_camera_parameter_setting_tool_update_parameters(self):
        """测试相机参数设置工具的参数更新"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            tool = CameraParameterSettingTool()

            # 更新参数
            tool.set_param("camera_id", "hik_0")
            tool.set_param("exposure", 20000.0)
            tool.set_param("gain", 5.0)
            tool.set_param("gamma", 1.2)
            tool.set_param("width", 1280)
            tool.set_param("height", 720)
            tool.set_param("fps", 60.0)
            tool.set_param("trigger_mode", "software")
            tool.set_param("auto_exposure", False)
            tool.set_param("auto_gain", False)

            # 验证参数更新
            self.assertEqual(tool.get_param("camera_id"), "hik_0")
            self.assertEqual(tool.get_param("exposure"), 20000.0)
            self.assertEqual(tool.get_param("gain"), 5.0)
            self.assertEqual(tool.get_param("gamma"), 1.2)
            self.assertEqual(tool.get_param("width"), 1280)
            self.assertEqual(tool.get_param("height"), 720)
            self.assertEqual(tool.get_param("fps"), 60.0)
            self.assertEqual(tool.get_param("trigger_mode"), "software")
            self.assertEqual(tool.get_param("auto_exposure"), False)
            self.assertEqual(tool.get_param("auto_gain"), False)

            print("✓ 相机参数设置工具参数更新测试成功")
        except Exception as e:
            self.fail(f"相机参数设置工具参数更新测试失败: {e}")

    def test_camera_parameter_setting_tool_get_available_cameras(self):
        """测试相机参数设置工具获取可用相机列表"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            tool = CameraParameterSettingTool()

            # 测试获取可用相机列表（这里可能返回空列表，因为没有实际相机）
            cameras = tool.get_available_cameras()
            self.assertIsInstance(cameras, list)
            print(
                f"✓ 相机参数设置工具获取可用相机列表测试成功，发现 {len(cameras)} 个相机"
            )
        except Exception as e:
            self.fail(f"相机参数设置工具获取可用相机列表测试失败: {e}")

    @patch("modules.camera.camera_manager.CameraManager.connect")
    def test_camera_parameter_setting_tool_connect_camera(self, mock_connect):
        """测试相机参数设置工具连接相机"""
        try:
            from tools.camera_parameter_setting import (
                CameraParameterSettingTool,
            )

            tool = CameraParameterSettingTool()

            # 创建模拟相机对象
            mock_camera = Mock()
            mock_camera.get_all_parameter_info.return_value = {
                "exposure": 10000.0,
                "gain": 0.0,
                "fps": 30.0,
                "width": 1920,
                "height": 1080,
            }
            mock_connect.return_value = mock_camera

            # 测试连接相机
            camera = tool._connect_camera("hik_0")
            self.assertIsNotNone(camera)
            mock_connect.assert_called_once_with("hik_0")
            print("✓ 相机参数设置工具连接相机测试成功")
        except Exception as e:
            self.fail(f"相机参数设置工具连接相机测试失败: {e}")


if __name__ == "__main__":
    unittest.main()
