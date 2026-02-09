#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
几何变换算法工具

提供图像的几何变换功能，包括：
- 四种预设变换：无变换、水平镜像、垂直镜像、水平垂直镜像
- 自定义旋转角度
- 处理顺序：先应用预设变换，再执行旋转

Author: Vision System Team
Date: 2026-02-06
"""

import cv2
import numpy as np
from typing import Any, Dict, List, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from data.image_data import ImageData, ResultData


@ToolRegistry.register
class GeometricTransformTool(ToolBase):
    """几何变换工具
    
    对图像进行几何变换，支持镜像和旋转操作。
    
    功能特性:
    - 四种预设变换选项
    - 自定义旋转角度
    - 先镜像后旋转的处理顺序
    
    输入端口:
    - InputImage: 输入图像
    
    输出端口:
    - OutputImage: 变换后的图像
    """
    
    tool_name = "几何变换"
    tool_category = "Vision"
    tool_description = "对图像进行几何变换，支持镜像和旋转"
    
    # 预设变换类型
    TRANSFORM_TYPES = {
        "无变换": "none",
        "水平镜像": "horizontal",
        "垂直镜像": "vertical",
        "水平垂直镜像": "both",
    }
    
    def __init__(self, name: str = None):
        super().__init__(name)
        
    def _init_params(self):
        """初始化参数"""
        # 预设变换类型
        self.set_param(
            "变换类型",
            "无变换",
            param_type="enum",
            options=list(self.TRANSFORM_TYPES.keys()),
            description="选择预设的几何变换类型"
        )
        
        # 旋转角度
        self.set_param(
            "旋转角度",
            0.0,
            param_type="float",
            description="旋转角度（度），正值为顺时针，负值为逆时针",
        )
        
        # 旋转中心
        self.set_param(
            "旋转中心X",
            -1.0,
            param_type="float",
            description="旋转中心X坐标（-1表示图像中心）",
        )
        
        self.set_param(
            "旋转中心Y",
            -1.0,
            param_type="float",
            description="旋转中心Y坐标（-1表示图像中心）",
        )
        
        # 缩放比例
        self.set_param(
            "缩放比例",
            1.0,
            param_type="float",
            description="旋转后的缩放比例",
        )
        
    def _get_input_ports(self) -> List[ToolParameter]:
        """获取输入端口定义"""
        return [
            ToolParameter(
                name="InputImage",
                param_type="image",
                description="输入图像",
                required=True,
            )
        ]
    
    def _get_output_ports(self) -> List[ToolParameter]:
        """获取输出端口定义"""
        return [
            ToolParameter(
                name="OutputImage",
                param_type="image",
                description="变换后的图像",
            )
        ]
    
    def _run_impl(self) -> Dict[str, Any]:
        """执行几何变换
        
        处理顺序：
        1. 应用预设变换（镜像）
        2. 执行旋转
        
        Returns:
            包含变换后图像的字典
        """
        # 获取输入图像
        input_image = self.get_input("InputImage")
        if input_image is None:
            raise Exception("未提供输入图像")
        
        # 转换为OpenCV格式
        image = input_image.data
        if image is None:
            raise Exception("输入图像数据为空")
        
        # 获取参数
        transform_type = self.get_param("变换类型", "无变换")
        rotation_angle = self.get_param("旋转角度", 0.0)
        center_x = self.get_param("旋转中心X", -1.0)
        center_y = self.get_param("旋转中心Y", -1.0)
        scale = self.get_param("缩放比例", 1.0)
        
        self._logger.info(f"几何变换: 类型={transform_type}, 角度={rotation_angle}°")
        
        # 步骤1: 应用预设变换（镜像）
        transformed_image = self._apply_preset_transform(image, transform_type)
        
        # 步骤2: 执行旋转
        if rotation_angle != 0.0:
            result_image = self._apply_rotation(
                transformed_image, 
                rotation_angle, 
                center_x, 
                center_y, 
                scale
            )
        else:
            result_image = transformed_image
        
        # 创建输出数据
        height, width = result_image.shape[:2]
        channels = 1 if len(result_image.shape) == 2 else result_image.shape[2]
        output_data = ImageData(result_image, width, height, channels)
        
        self._logger.info(f"几何变换完成: 输出尺寸={width}x{height}")
        
        # 设置结果数据
        self._result_data = ResultData()
        self._result_data.tool_name = self._name
        self._result_data.result_category = "transform"
        self._result_data.set_value("transform_type", transform_type)
        self._result_data.set_value("rotation_angle", rotation_angle)
        self._result_data.set_value("output_width", width)
        self._result_data.set_value("output_height", height)
        
        return {
            "OutputImage": output_data,
        }
    
    def _apply_preset_transform(self, image: np.ndarray, transform_type: str) -> np.ndarray:
        """应用预设变换
        
        Args:
            image: 输入图像
            transform_type: 变换类型名称
            
        Returns:
            变换后的图像
        """
        transform_code = self.TRANSFORM_TYPES.get(transform_type, "none")
        
        if transform_code == "none":
            return image.copy()
        elif transform_code == "horizontal":
            # 水平镜像（左右翻转）
            return cv2.flip(image, 1)
        elif transform_code == "vertical":
            # 垂直镜像（上下翻转）
            return cv2.flip(image, 0)
        elif transform_code == "both":
            # 水平垂直镜像（180度旋转）
            return cv2.flip(image, -1)
        else:
            return image.copy()
    
    def _apply_rotation(
        self, 
        image: np.ndarray, 
        angle: float, 
        center_x: float, 
        center_y: float, 
        scale: float
    ) -> np.ndarray:
        """应用旋转变换
        
        Args:
            image: 输入图像
            angle: 旋转角度（度）
            center_x: 旋转中心X坐标（-1表示图像中心）
            center_y: 旋转中心Y坐标（-1表示图像中心）
            scale: 缩放比例
            
        Returns:
            旋转后的图像
        """
        height, width = image.shape[:2]
        
        # 确定旋转中心
        if center_x < 0:
            cx = width / 2
        else:
            cx = center_x
            
        if center_y < 0:
            cy = height / 2
        else:
            cy = center_y
        
        # 创建旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D((cx, cy), -angle, scale)
        
        # 计算输出图像尺寸（保持完整图像）
        # 获取旋转后图像的边界框
        cos_angle = np.abs(np.cos(np.radians(angle)))
        sin_angle = np.abs(np.sin(np.radians(angle)))
        
        new_width = int((height * sin_angle + width * cos_angle) * scale)
        new_height = int((height * cos_angle + width * sin_angle) * scale)
        
        # 调整旋转矩阵的平移部分，使图像居中
        rotation_matrix[0, 2] += (new_width - width) / 2
        rotation_matrix[1, 2] += (new_height - height) / 2
        
        # 执行旋转
        rotated_image = cv2.warpAffine(
            image, 
            rotation_matrix, 
            (new_width, new_height),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0)
        )
        
        return rotated_image


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试图像
    test_image = np.ones((300, 400, 3), dtype=np.uint8) * 200
    cv2.rectangle(test_image, (50, 50), (150, 150), (255, 0, 0), -1)
    cv2.circle(test_image, (200, 150), 50, (0, 255, 0), -1)
    
    image_data = ImageData(test_image)
    
    # 测试各种变换
    transforms = ["无变换", "水平镜像", "垂直镜像", "水平垂直镜像"]
    
    for transform in transforms:
        tool = GeometricTransformTool(f"test_{transform}")
        tool.set_input_data("InputImage", image_data)
        tool.set_param("变换类型", transform)
        tool.set_param("旋转角度", 45.0)
        
        result = tool.run()
        
        if result:
            output = result.get("OutputImage")
            print(f"{transform}: 输出尺寸={output.width}x{output.height}")
        else:
            print(f"{transform}: 执行失败")
    
    print("测试完成!")
