#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业视觉检测系统主程序入口

演示如何使用核心框架构建完整的视觉检测系统。

Author: Vision System Team
Date: 2025-01-04
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
import time
from typing import Optional

import cv2
import numpy as np

from core.procedure import Procedure

# 导入核心框架
from core.solution import Solution, SolutionState
from core.tool_base import ToolRegistry

# 导入数据封装
from data.image_data import ImageData
from tools.image_filter import GaussianFilter, MedianFilter

# 导入工具
from tools.image_source import CameraSource, ImageSource
from tools.template_match import CircleFind, GrayMatch, LineFind

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ProfessionalApp")


class ProfessionalVisionApp:
    """
    专业视觉检测应用类

    演示如何使用框架构建完整的视觉检测系统。

    功能：
    - 方案管理
    - 流程构建
    - 图像数据流处理
    - 结果展示
    """

    def __init__(self, solution_name: str = "默认方案"):
        """
        初始化应用

        Args:
            solution_name: 方案名称
        """
        self.solution = Solution(solution_name)
        self.current_procedure: Optional[Procedure] = None

        logger.info(f"初始化专业视觉检测系统: {solution_name}")

    def create_procedure(self, procedure_name: str) -> Procedure:
        """
        创建流程

        Args:
            procedure_name: 流程名称

        Returns:
            Procedure对象
        """
        procedure = Procedure(procedure_name)
        self.solution.add_procedure(procedure)
        self.current_procedure = procedure

        logger.info(f"创建流程: {procedure_name}")
        return procedure

    def add_image_source(
        self, name: str, source_type: str = "local", file_path: str = None
    ) -> ImageSource:
        """
        添加图像源

        Args:
            name: 工具名称
            source_type: 源类型 (local/camera)
            file_path: 文件路径

        Returns:
            ImageSource对象
        """
        tool = ToolRegistry.create_tool("ImageSource", "图像读取器", name)
        tool.set_param("source_type", source_type)
        if file_path:
            tool.set_param("file_path", file_path)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加图像源: {name}")
        return tool

    def add_camera_source(
        self, name: str, camera_id: str = "0"
    ) -> CameraSource:
        """
        添加相机源

        Args:
            name: 工具名称
            camera_id: 相机ID

        Returns:
            CameraSource对象
        """
        tool = ToolRegistry.create_tool("ImageSource", "相机", name)
        tool.set_param("camera_id", camera_id)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加相机源: {name}")
        return tool

    def add_filter(
        self, name: str, filter_type: str = "gaussian", kernel_size: int = 3
    ) -> object:
        """
        添加滤波工具

        Args:
            name: 工具名称
            filter_type: 滤波类型
            kernel_size: 核大小

        Returns:
            滤波工具对象
        """
        tool_class = {
            "gaussian": ("ImageFilter", "高斯滤波"),
            "median": ("ImageFilter", "中值滤波"),
        }.get(filter_type, ("ImageFilter", "高斯滤波"))

        tool = ToolRegistry.create_tool(tool_class[0], tool_class[1], name)
        tool.set_param("kernel_size", kernel_size)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加滤波: {name}")
        return tool

    def add_gray_match(
        self, name: str, template_path: str, min_score: float = 0.7
    ) -> GrayMatch:
        """
        添加灰度匹配工具

        Args:
            name: 工具名称
            template_path: 模板路径
            min_score: 最小分数

        Returns:
            GrayMatch对象
        """
        tool = ToolRegistry.create_tool("Vision", "灰度匹配", name)
        tool.set_param("template_path", template_path)
        tool.set_param("min_score", min_score)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加灰度匹配: {name}")
        return tool

    def add_line_find(self, name: str, threshold: int = 100) -> LineFind:
        """
        添加直线查找工具

        Args:
            name: 工具名称
            threshold: 投票阈值

        Returns:
            LineFind对象
        """
        tool = ToolRegistry.create_tool("Vision", "直线查找", name)
        tool.set_param("threshold", threshold)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加直线查找: {name}")
        return tool

    def add_circle_find(
        self, name: str, min_radius: int = 10, max_radius: int = 100
    ) -> CircleFind:
        """
        添加圆查找工具

        Args:
            name: 工具名称
            min_radius: 最小半径
            max_radius: 最大半径

        Returns:
            CircleFind对象
        """
        tool = ToolRegistry.create_tool("Vision", "圆查找", name)
        tool.set_param("min_radius", min_radius)
        tool.set_param("max_radius", max_radius)

        if self.current_procedure:
            self.current_procedure.add_tool(tool)

        logger.info(f"添加圆查找: {name}")
        return tool

    def connect_tools(
        self,
        from_name: str,
        to_name: str,
        from_port: str = "OutputImage",
        to_port: str = "InputImage",
    ) -> bool:
        """
        连接两个工具

        Args:
            from_name: 源工具名称
            to_name: 目标工具名称
            from_port: 源端口
            to_port: 目标端口

        Returns:
            是否连接成功
        """
        if self.current_procedure:
            return self.current_procedure.connect(
                from_name, to_name, from_port, to_port
            )
        return False

    def run_once(self, input_image: np.ndarray = None) -> dict:
        """
        单次运行

        Args:
            input_image: 输入图像（可选）

        Returns:
            运行结果
        """
        if input_image is not None:
            image_data = ImageData(data=input_image)
            self.solution.set_input(image_data)

        logger.info("开始单次运行...")
        results = self.solution.run()

        # 提取结果
        for proc_name, proc_results in results.items():
            logger.info(f"流程 '{proc_name}' 结果:")
            if isinstance(proc_results, dict):
                for tool_name, tool_result in proc_results.items():
                    if isinstance(tool_result, dict):
                        output = tool_result.get("output")
                        if output is not None and isinstance(
                            output, ImageData
                        ):
                            logger.info(
                                f"  {tool_name}: 图像大小={output.width}x{output.height}"
                            )

        return results

    def run_continuous(self, interval: int = 1000):
        """
        连续运行

        Args:
            interval: 运行间隔（毫秒）
        """
        self.solution.run_interval = interval
        logger.info(f"开始连续运行，间隔={interval}ms")
        self.solution.runing()

    def stop(self):
        """停止运行"""
        logger.info("停止运行")
        self.solution.stop_run()

    def get_solution_info(self) -> dict:
        """获取方案信息"""
        return self.solution.get_info()

    def demo_with_image(self, image_path: str):
        """
        使用示例图像演示完整流程

        Args:
            image_path: 图像路径
        """
        logger.info(f"演示流程，图像: {image_path}")

        # 检查图像是否存在
        if not os.path.exists(image_path):
            logger.error(f"图像不存在: {image_path}")
            return

        # 创建流程
        self.create_procedure("演示流程")

        # 添加图像源
        image_source = self.add_image_source("图像源", "local", image_path)

        # 添加高斯滤波
        gaussian = self.add_filter("高斯滤波", "gaussian", 3)

        # 添加灰度匹配
        template_path = self.get_default_template_path()
        if template_path and os.path.exists(template_path):
            gray_match = self.add_gray_match("灰度匹配", template_path, 0.7)
        else:
            logger.warning(f"模板文件不存在: {template_path}")

        # 连接工具
        self.connect_tools("图像源", "高斯滤波")
        if "gray_match" in locals():
            self.connect_tools("高斯滤波", "灰度匹配")

        # 运行
        results = self.run_once()

        return results

    def get_default_template_path(self) -> str:
        """获取默认模板路径"""
        return os.path.join(project_root, "templates", "default_template.jpg")

    def create_demo_solution(self) -> Solution:
        """
        创建演示方案

        Returns:
            Solution对象
        """
        solution = Solution("演示方案")

        # 创建检测流程
        procedure = Procedure("检测流程")

        # 添加图像源
        image_source = ToolRegistry.create_tool(
            "ImageSource", "图像读取器", "图像源"
        )
        image_source.set_param("source_type", "local")
        procedure.add_tool(image_source)

        # 添加高斯滤波
        gaussian = ToolRegistry.create_tool(
            "ImageFilter", "高斯滤波", "高斯滤波"
        )
        gaussian.set_param("kernel_size", 3)
        procedure.add_tool(gaussian)

        # 添加灰度匹配
        gray_match = ToolRegistry.create_tool("Vision", "灰度匹配", "灰度匹配")
        gray_match.set_param("min_score", 0.7)
        procedure.add_tool(gray_match)

        # 连接工具
        procedure.connect("图像源", "高斯滤波")
        procedure.connect("高斯滤波", "灰度匹配")

        # 添加流程到方案
        solution.add_procedure(procedure)

        return solution


def test_core_framework():
    """测试核心框架"""
    print("\n" + "=" * 60)
    print("测试核心框架")
    print("=" * 60)

    # 创建应用
    app = ProfessionalVisionApp("测试方案")

    # 创建流程
    procedure = app.create_procedure("测试流程")

    # 添加工具
    image_source = app.add_image_source("图像源", "local", "test.jpg")
    filter_tool = app.add_filter("滤波", "gaussian", 3)
    match_tool = app.add_gray_match("匹配", "", 0.7)

    # 连接工具
    app.connect_tools("图像源", "滤波")
    app.connect_tools("滤波", "匹配")

    # 获取方案信息
    info = app.get_solution_info()
    print(f"方案信息: {info}")

    # 创建测试图像
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:] = (128, 128, 128)  # 灰色背景

    # 绘制测试图案
    cv2.rectangle(test_image, (100, 100), (300, 300), (255, 0, 0), 2)
    cv2.circle(test_image, (400, 240), 50, (0, 255, 0), 2)

    # 运行
    results = app.run_once(test_image)

    print("测试完成")
    return True


def test_image_data():
    """测试图像数据封装"""
    print("\n" + "=" * 60)
    print("测试图像数据封装")
    print("=" * 60)

    # 创建测试图像
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # 创建ImageData
    image_data = ImageData(
        data=test_image, width=640, height=480, camera_id="test_camera"
    )

    print(f"图像数据: {image_data}")
    print(f"宽度: {image_data.width}")
    print(f"高度: {image_data.height}")
    print(f"通道数: {image_data.channels}")
    print(f"形状: {image_data.shape}")

    # 测试转换为灰度
    gray_image = image_data.to_gray()
    print(f"灰度图像形状: {gray_image.shape}")

    # 测试创建ROI
    from data.image_data import ROI

    roi = ROI(100, 100, 200, 200)
    roi_image = image_data.get_roi(roi)
    print(f"ROI图像形状: {roi_image.shape}")

    print("图像数据测试完成")
    return True


def test_tools():
    """测试工具注册"""
    print("\n" + "=" * 60)
    print("测试工具注册")
    print("=" * 60)

    # 获取所有已注册的工具
    tools = ToolRegistry.get_all_tools()
    print(f"已注册的工具数量: {len(tools)}")

    # 按类别显示
    categories = ToolRegistry.get_categories()
    print(f"工具类别: {categories}")

    for category in categories:
        category_tools = ToolRegistry.get_tools_by_category(category)
        print(f"\n{category} ({len(category_tools)}个工具):")
        for key, tool_class in category_tools.items():
            print(f"  - {key}")

    # 创建工具实例
    image_source = ToolRegistry.create_tool(
        "ImageSource", "图像读取器", "测试图像源"
    )
    print(f"\n创建工具: {image_source}")

    print("工具测试完成")
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("专业视觉检测系统")
    print("=" * 60)

    # 测试各个模块
    test_image_data()
    test_tools()
    test_core_framework()

    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
