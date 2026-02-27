#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像保存算法工具

支持通过连线方式建立与其他算法模块的关联，
允许用户自由选择需要保存图像数据的来源算法模块，
确保能够准确获取并保存所选算法模块处理后的图像数据。

Author: Vision System Team
Date: 2026-02-06
"""

import cv2
import numpy as np
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from data.image_data import ImageData, ResultData

USE_FAST_SAVE = False
try:
    from core.image_utils import save_image_fast
    USE_FAST_SAVE = True
except ImportError:
    pass


@ToolRegistry.register
class ImageSaverTool(ToolBase):
    """图像保存工具
    
    保存输入的图像数据到指定路径。
    
    功能特性:
    - 支持通过连线获取上游工具的图像输出
    - 支持多种图像格式（PNG、JPG、BMP、TIFF）
    - 支持自定义文件名格式（支持时间戳、序号等变量）
    - 支持自动创建目录
    - 支持保存质量设置（针对JPG格式）
    
    输入端口:
    - InputImage: 输入图像（通过连线连接上游工具）
    
    输出端口:
    - OutputImage: 输出图像（透传输入图像，便于后续处理）
    - SavePath: 保存的文件路径
    """
    
    tool_name = "图像保存"
    tool_category = "Vision"
    tool_description = "保存图像数据到指定路径，支持通过连线获取上游图像"
    
    # 支持的图像格式
    SUPPORTED_FORMATS = {
        "PNG": ".png",
        "JPG": ".jpg",
        "JPEG": ".jpeg",
        "BMP": ".bmp",
        "TIFF": ".tiff",
    }
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self._save_count = 0  # 保存计数器
        
    def _init_params(self):
        """初始化参数"""
        # 保存路径
        self.set_param(
            "保存路径",
            "./output_images",
            param_type="folder_path",
            description="图像保存的文件夹路径（支持相对路径和绝对路径）"
        )
        
        # 文件名格式
        self.set_param(
            "文件名格式",
            "image_{timestamp}_{index}",
            param_type="text",
            description="文件名格式，支持变量：{timestamp}时间戳, {index}序号, {date}日期, {time}时间"
        )
        
        # 图像格式
        self.set_param(
            "图像格式",
            "PNG",
            param_type="enum",
            options=list(self.SUPPORTED_FORMATS.keys()),
            description="保存的图像文件格式"
        )
        
        # JPG质量（仅JPG格式有效）
        self.set_param(
            "JPG质量",
            95,
            param_type="integer",
            description="JPG格式的保存质量（1-100，数值越高质量越好）",
        )
        
        # 自动创建目录
        self.set_param(
            "自动创建目录",
            True,
            param_type="boolean",
            description="如果保存目录不存在，是否自动创建"
        )
        
        # 序号起始值
        self.set_param(
            "序号起始值",
            1,
            param_type="integer",
            description="文件名中序号的起始值",
        )
        
        # 序号位数
        self.set_param(
            "序号位数",
            4,
            param_type="integer",
            description="序号填充的位数（例如4位序号为0001, 0002...）",
        )
        
        # 时间戳格式
        self.set_param(
            "时间戳格式",
            "%Y%m%d_%H%M%S",
            param_type="text",
            description="时间戳格式（Python datetime格式）"
        )
        
        # 覆盖已存在文件
        self.set_param(
            "覆盖已存在文件",
            False,
            param_type="boolean",
            description="如果文件已存在，是否覆盖（False则自动添加序号）"
        )
        
    def _get_input_ports(self) -> List[ToolParameter]:
        """获取输入端口定义"""
        return [
            ToolParameter(
                name="InputImage",
                param_type="image",
                description="输入图像（通过连线连接上游工具的图像输出）",
                required=True,
            )
        ]
    
    def _get_output_ports(self) -> List[ToolParameter]:
        """获取输出端口定义"""
        return [
            ToolParameter(
                name="OutputImage",
                param_type="image",
                description="输出图像（透传输入图像）",
            ),
            ToolParameter(
                name="SavePath",
                param_type="string",
                description="保存的文件路径",
            ),
        ]
    
    def _run_impl(self) -> Dict[str, Any]:
        """执行图像保存
        
        Returns:
            包含输出图像和保存路径的字典
        """
        # 获取输入图像
        input_image = self.get_input("InputImage")
        if input_image is None:
            raise Exception("未提供输入图像，请通过连线连接上游工具的图像输出端口")
        
        # 转换为OpenCV格式
        image = input_image.data
        if image is None:
            raise Exception("输入图像数据为空")
        
        # 获取参数
        save_dir = self.get_param("保存路径", "./output_images")
        filename_format = self.get_param("文件名格式", "image_{timestamp}_{index}")
        image_format = self.get_param("图像格式", "PNG")
        jpg_quality = self.get_param("JPG质量", 95)
        auto_create_dir = self.get_param("自动创建目录", True)
        start_index = self.get_param("序号起始值", 1)
        index_digits = self.get_param("序号位数", 4)
        timestamp_format = self.get_param("时间戳格式", "%Y%m%d_%H%M%S")
        overwrite = self.get_param("覆盖已存在文件", False)
        
        # 确保保存目录存在
        if auto_create_dir and not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
                self._logger.info(f"创建保存目录: {save_dir}")
            except Exception as e:
                raise Exception(f"创建保存目录失败: {e}")
        
        if not os.path.exists(save_dir):
            raise Exception(f"保存目录不存在: {save_dir}")
        
        # 生成文件名
        filename = self._generate_filename(
            filename_format,
            timestamp_format,
            start_index,
            index_digits,
            overwrite
        )
        
        # 添加扩展名
        ext = self.SUPPORTED_FORMATS.get(image_format, ".png")
        if not filename.lower().endswith(ext.lower()):
            filename += ext
        
        # 完整文件路径
        file_path = os.path.join(save_dir, filename)
        
        # 保存图像
        try:
            if USE_FAST_SAVE:
                if image_format in ["JPG", "JPEG"]:
                    quality = int(jpg_quality)
                else:
                    quality = 95
                success = save_image_fast(image, file_path, quality=quality)
            else:
                if image_format in ["JPG", "JPEG"]:
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpg_quality]
                    success = cv2.imwrite(file_path, image, encode_params)
                elif image_format == "PNG":
                    encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
                    success = cv2.imwrite(file_path, image, encode_params)
                else:
                    success = cv2.imwrite(file_path, image)
            
            if not success:
                raise Exception(f"保存返回失败")
            
            self._save_count += 1
            self._logger.info(f"图像保存成功: {file_path}")
            
        except Exception as e:
            raise Exception(f"保存图像失败: {e}")
        
        # 创建输出数据（透传输入图像）
        output_image = ImageData(
            image.copy(),
            input_image.width,
            input_image.height,
            input_image.channels
        )
        
        # 设置结果数据
        self._result_data = ResultData()
        self._result_data.tool_name = self._name
        self._result_data.result_category = "saver"
        self._result_data.set_value("save_path", file_path)
        self._result_data.set_value("save_count", self._save_count)
        self._result_data.set_value("image_format", image_format)
        
        return {
            "OutputImage": output_image,
            "SavePath": file_path,
        }
    
    def _generate_filename(
        self,
        filename_format: str,
        timestamp_format: str,
        start_index: int,
        index_digits: int,
        overwrite: bool
    ) -> str:
        """生成文件名
        
        Args:
            filename_format: 文件名格式模板
            timestamp_format: 时间戳格式
            start_index: 序号起始值
            index_digits: 序号位数
            overwrite: 是否覆盖已存在文件
            
        Returns:
            生成的文件名（不含扩展名）
        """
        # 获取当前时间
        now = datetime.now()
        
        # 生成时间戳
        timestamp = now.strftime(timestamp_format)
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        
        # 生成序号
        index = start_index + self._save_count
        index_str = str(index).zfill(index_digits)
        
        # 替换变量
        filename = filename_format.format(
            timestamp=timestamp,
            index=index_str,
            date=date_str,
            time=time_str,
        )
        
        # 清理文件名（移除非法字符）
        filename = self._sanitize_filename(filename)
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows非法字符: < > : " / \ | ? *
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 移除首尾空格和点
        filename = filename.strip(' .')
        
        # 如果文件名为空，使用默认名称
        if not filename:
            filename = "image"
        
        return filename
    
    def reset_counter(self):
        """重置保存计数器"""
        self._save_count = 0
        self._logger.info("保存计数器已重置")


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试图像
    test_image = np.ones((300, 400, 3), dtype=np.uint8) * 200
    cv2.rectangle(test_image, (50, 50), (150, 150), (255, 0, 0), -1)
    cv2.circle(test_image, (200, 150), 50, (0, 255, 0), -1)
    cv2.putText(test_image, "Test Image", (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    image_data = ImageData(test_image)
    
    # 测试图像保存工具
    tool = ImageSaverTool("test_saver")
    tool.set_input_data("InputImage", image_data)
    tool.set_param("保存路径", "./test_output")
    tool.set_param("文件名格式", "test_{timestamp}_{index}")
    tool.set_param("图像格式", "PNG")
    
    result = tool.run()
    
    if result:
        save_path = result.get("SavePath")
        output_image = result.get("OutputImage")
        print(f"保存成功: {save_path}")
        print(f"输出图像尺寸: {output_image.width}x{output_image.height}")
    else:
        print("保存失败")
    
    print("测试完成!")
