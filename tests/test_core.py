#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心模块测试

测试core模块中的工具基类、流程和方案管理功能
"""

import pytest
import numpy as np
from core.tool_base import ToolBase, ToolRegistry
from core.procedure import Procedure, ToolConnection
from core.solution import Solution
from data.image_data import ImageData


class TestToolBase:
    """测试ToolBase类"""
    
    def test_tool_creation(self):
        """测试工具创建"""
        # 定义一个测试工具类
        class TestTool(ToolBase):
            tool_name = "测试工具"
            tool_category = "Test"
            
            def _run_impl(self):
                pass
        
        # 创建工具实例
        tool = TestTool("test_instance")
        assert tool is not None
        assert tool.name == "test_instance"
        assert tool.tool_name == "测试工具"
        assert tool.tool_category == "Test"
        assert tool.is_enabled
        assert not tool.is_running
    
    def test_tool_params(self):
        """测试工具参数设置"""
        class TestTool(ToolBase):
            tool_name = "测试工具"
            tool_category = "Test"
            
            def _init_params(self):
                self.set_param("threshold", 100)
                self.set_param("enabled", True)
            
            def _run_impl(self):
                pass
        
        tool = TestTool("test_instance")
        
        # 测试初始参数
        assert tool.get_param("threshold") == 100
        assert tool.get_param("enabled") is True
        assert tool.get_param("nonexistent_param") is None
        assert tool.get_param("nonexistent_param", "default") == "default"
        
        # 测试设置参数
        tool.set_param("threshold", 200)
        tool.set_param("enabled", False)
        assert tool.get_param("threshold") == 200
        assert tool.get_param("enabled") is False
        
        # 测试获取所有参数
        all_params = tool.get_all_params()
        assert "threshold" in all_params
        assert "enabled" in all_params
    
    def test_tool_input_output(self, sample_image):
        """测试工具输入输出"""
        class TestTool(ToolBase):
            tool_name = "测试工具"
            tool_category = "Test"
            
            def _run_impl(self):
                # 将输入图像作为输出
                if self.has_input():
                    self._output_data = self._input_data.copy()
        
        tool = TestTool("test_instance")
        
        # 测试输入
        assert not tool.has_input()
        tool.set_input(sample_image)
        assert tool.has_input()
        assert tool.get_input() == sample_image
        
        # 测试输出
        assert not tool.has_output()
        
        # 运行工具
        tool.run()
        assert tool.has_output()
        
        # 测试重置
        tool.reset()
        assert not tool.has_output()
    
    def test_tool_run(self, sample_image):
        """测试工具运行"""
        class TestTool(ToolBase):
            tool_name = "测试工具"
            tool_category = "Test"
            
            def _run_impl(self):
                if self.has_input():
                    self._output_data = self._input_data.copy()
        
        tool = TestTool("test_instance")
        tool.set_input(sample_image)
        
        # 测试运行
        result = tool.run()
        assert result is True
        assert tool.has_output()
        assert tool.execution_time > 0
    
    def test_disabled_tool(self, sample_image):
        """测试禁用工具"""
        class TestTool(ToolBase):
            tool_name = "测试工具"
            tool_category = "Test"
            
            def _run_impl(self):
                if self.has_input():
                    self._output_data = self._input_data.copy()
        
        tool = TestTool("test_instance")
        tool.is_enabled = False  # 禁用工具
        tool.set_input(sample_image)
        
        # 测试运行禁用的工具
        result = tool.run()
        assert result is True  # 禁用工具返回True但不执行
        assert not tool.has_output()  # 没有输出


class TestToolRegistry:
    """测试ToolRegistry类"""
    
    def test_registry_initialization(self, tool_registry):
        """测试工具注册表初始化"""
        assert tool_registry is not None
        
        # 测试获取所有工具
        all_tools = tool_registry.get_all_tools()
        assert len(all_tools) > 0
        
        # 测试获取工具类别
        categories = tool_registry.get_categories()
        assert len(categories) > 0
    
    def test_tool_creation_from_registry(self, tool_registry):
        """测试从注册表创建工具"""
        # 测试创建一个已知工具
        tool = tool_registry.create_tool("ImageFilter", "高斯滤波", "gaussian_test")
        assert tool is not None
        assert tool.name == "gaussian_test"
        assert tool.tool_name == "高斯滤波"
        assert tool.tool_category == "ImageFilter"
    
    def test_invalid_tool_creation(self, tool_registry):
        """测试创建无效工具"""
        with pytest.raises(ValueError):
            tool_registry.create_tool("InvalidCategory", "InvalidTool", "invalid_test")
    
    def test_get_tools_by_category(self, tool_registry):
        """测试按类别获取工具"""
        # 测试获取ImageFilter类别的工具
        filter_tools = tool_registry.get_tools_by_category("ImageFilter")
        assert len(filter_tools) > 0
        
        # 测试获取Vision类别的工具
        vision_tools = tool_registry.get_tools_by_category("Vision")
        assert len(vision_tools) > 0
        
        # 测试获取不存在的类别
        invalid_tools = tool_registry.get_tools_by_category("InvalidCategory")
        assert len(invalid_tools) == 0


class TestProcedure:
    """测试Procedure类"""
    
    def test_procedure_creation(self, sample_procedure):
        """测试流程创建"""
        assert sample_procedure is not None
        assert sample_procedure.name == "测试流程"
        assert sample_procedure.is_enabled
        assert not sample_procedure.is_running
        assert sample_procedure.tool_count == 0
    
    def test_add_remove_tool(self, sample_procedure, tool_registry):
        """测试添加和移除工具"""
        # 创建一个工具
        tool = tool_registry.create_tool("ImageFilter", "高斯滤波", "gaussian_tool")
        
        # 测试添加工具
        result = sample_procedure.add_tool(tool)
        assert result is True
        assert sample_procedure.tool_count == 1
        
        # 测试重复添加同一工具
        result = sample_procedure.add_tool(tool)
        assert result is True  # 允许添加同一工具实例多次
        assert sample_procedure.tool_count == 2
        
        # 测试移除工具
        result = sample_procedure.remove_tool("gaussian_tool")
        assert result is True
        assert sample_procedure.tool_count == 1
        
        # 测试移除不存在的工具
        result = sample_procedure.remove_tool("nonexistent_tool")
        assert result is False
    
    def test_tool_connections(self, sample_procedure, tool_registry):
        """测试工具连接"""
        # 创建两个工具
        tool1 = tool_registry.create_tool("ImageFilter", "高斯滤波", "gaussian_tool")
        tool2 = tool_registry.create_tool("Vision", "直线查找", "line_tool")
        
        # 添加工具到流程
        sample_procedure.add_tool(tool1)
        sample_procedure.add_tool(tool2)
        
        # 测试连接工具
        result = sample_procedure.connect("gaussian_tool", "line_tool")
        assert result is True
        
        # 测试连接不存在的工具
        result = sample_procedure.connect("nonexistent_tool", "line_tool")
        assert result is False
        
        result = sample_procedure.connect("gaussian_tool", "nonexistent_tool")
        assert result is False
        
        # 测试断开连接
        result = sample_procedure.disconnect("gaussian_tool", "line_tool")
        assert result is True
    
    def test_execution_order(self, sample_procedure, tool_registry):
        """测试执行顺序"""
        # 创建多个工具
        tool1 = tool_registry.create_tool("ImageFilter", "高斯滤波", "gaussian_tool")
        tool2 = tool_registry.create_tool("Vision", "直线查找", "line_tool")
        tool3 = tool_registry.create_tool("Recognition", "二维码识别", "qr_tool")
        
        # 添加工具到流程
        sample_procedure.add_tool(tool1)
        sample_procedure.add_tool(tool2)
        sample_procedure.add_tool(tool3)
        
        # 连接工具，形成执行顺序
        sample_procedure.connect("gaussian_tool", "line_tool")
        sample_procedure.connect("line_tool", "qr_tool")
        
        # 获取执行顺序
        execution_order = sample_procedure.get_execution_order()
        assert len(execution_order) == 3
        
        # 验证执行顺序：tool1 -> tool2 -> tool3
        assert execution_order.index("gaussian_tool") < execution_order.index("line_tool")
        assert execution_order.index("line_tool") < execution_order.index("qr_tool")


class TestSolution:
    """测试Solution类"""
    
    def test_solution_creation(self, sample_solution):
        """测试方案创建"""
        assert sample_solution is not None
        assert sample_solution.name == "测试方案"
        assert sample_solution.procedure_count == 0
        assert sample_solution.is_running is False
    
    def test_add_remove_procedure(self, sample_solution):
        """测试添加和移除流程"""
        # 创建一个流程
        procedure = Procedure("测试流程2")
        
        # 测试添加流程
        result = sample_solution.add_procedure(procedure)
        assert result is True
        assert sample_solution.procedure_count == 1
        
        # 测试重复添加同一流程
        result = sample_solution.add_procedure(procedure)
        assert result is False  # 不允许添加同名流程
        assert sample_solution.procedure_count == 1
        
        # 测试移除流程
        result = sample_solution.remove_procedure("测试流程2")
        assert result is True
        assert sample_solution.procedure_count == 0
        
        # 测试移除不存在的流程
        result = sample_solution.remove_procedure("nonexistent_procedure")
        assert result is False
    
    def test_solution_run(self, sample_solution, sample_image):
        """测试方案运行"""
        # 创建流程和工具
        procedure = Procedure("测试流程")
        
        from core.tool_base import ToolRegistry
        import tools
        tool = ToolRegistry.create_tool("ImageFilter", "高斯滤波", "gaussian_tool")
        
        # 添加工具到流程
        procedure.add_tool(tool)
        
        # 添加流程到方案
        sample_solution.add_procedure(procedure)
        
        # 设置输入数据
        sample_solution.set_input(sample_image)
        
        # 测试运行方案
        result = sample_solution.run()
        assert isinstance(result, dict)
        assert "测试流程" in result
    
    def test_solution_state(self, sample_solution):
        """测试方案状态管理"""
        # 测试初始状态
        assert sample_solution.state.name == "IDLE"
        assert sample_solution.is_running is False
        
        # 测试连续运行
        sample_solution.runing()
        assert sample_solution.state.name == "CONTINUOUS_RUN"
        assert sample_solution.is_running is True
        
        # 测试停止运行
        sample_solution.stop_run()
        assert sample_solution.state.name == "IDLE"
        assert sample_solution.is_running is False
