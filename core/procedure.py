#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程管理模块

提供流程(Procedure)类，管理一组工具的执行顺序和数据流转。

Author: Vision System Team
Date: 2025-01-04
"""

import logging
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ToolBase, ToolRegistry
from data.image_data import ImageData, ResultData
from utils.exceptions import ProcedureException


@dataclass
class ToolConnection:
    """工具连接定义"""

    from_tool: str  # 源工具名称
    to_tool: str  # 目标工具名称
    from_port: str = "OutputImage"  # 源端口
    to_port: str = "InputImage"  # 目标端口


class Procedure:
    """
    流程类，管理一组工具的执行

    功能：
    - 工具管理（添加/移除/查找）
    - 工具连接（数据流转）
    - 流程执行（按依赖顺序执行）
    - 流程控制（启用/禁用）

    示例：
        # 创建流程
        procedure = Procedure("检测流程")

        # 添加工具
        camera = ToolRegistry.create_tool("ImageSource", "Camera")
        filter = ToolRegistry.create_tool("ImageFilter", "BoxFilter")
        matcher = ToolRegistry.create_tool("Vision", "GrayMatch")

        procedure.add_tool(camera)
        procedure.add_tool(filter)
        procedure.add_tool(matcher)

        # 连接工具
        procedure.connect(camera, filter)
        procedure.connect(filter, matcher)

        # 执行流程
        results = procedure.run()
    """

    def __init__(self, name: str = "Procedure"):
        """
        初始化流程

        Args:
            name: 流程名称
        """
        self._name = name
        self._tools: Dict[str, ToolBase] = {}  # 工具名称 -> 工具实例
        self._connections: List[ToolConnection] = []
        self._is_enabled = True
        self._is_running = False
        self._last_error: Optional[str] = None
        self._execution_time = 0.0

        self._logger = logging.getLogger(f"Procedure.{self._name}")

    @property
    def name(self) -> str:
        """获取流程名称"""
        return self._name

    @name.setter
    def name(self, value: str):
        """设置流程名称"""
        self._name = value

    @property
    def is_enabled(self) -> bool:
        """获取启用状态"""
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value: bool):
        """设置启用状态"""
        self._is_enabled = value

    @property
    def is_running(self) -> bool:
        """获取运行状态"""
        return self._is_running

    @property
    def last_error(self) -> Optional[str]:
        """获取最后错误"""
        return self._last_error

    @property
    def execution_time(self) -> float:
        """获取执行时间(秒)"""
        return self._execution_time

    @property
    def tool_count(self) -> int:
        """获取工具数量"""
        return len(self._tools)

    @property
    def tools(self) -> List[ToolBase]:
        """获取所有工具"""
        return list(self._tools.values())

    @property
    def connections(self) -> List[ToolConnection]:
        """获取所有连接"""
        return self._connections.copy()

    def add_tool(
        self, tool: ToolBase, position: Tuple[int, int] = None
    ) -> bool:
        """
        添加工具到流程

        Args:
            tool: 工具实例
            position: 位置 (x, y)，用于算法编辑器显示

        Returns:
            添加成功返回True
        """
        if tool.name in self._tools:
            self._logger.warning(f"工具已存在: {tool.name}")
            return True  # 允许同一工具实例重复添加

        self._tools[tool.name] = tool
        self._logger.info(f"添加工具: {tool.name}")

        return True

    def remove_tool(self, tool_name: str) -> bool:
        """
        从流程移除工具

        Args:
            tool_name: 工具名称

        Returns:
            移除成功返回True
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools.pop(tool_name)

        # 移除相关的连接
        self._connections = [
            conn
            for conn in self._connections
            if conn.from_tool != tool_name and conn.to_tool != tool_name
        ]

        self._logger.info(f"移除工具: {tool_name}")
        return True

    def get_tool(self, tool_name: str) -> Optional[ToolBase]:
        """
        获取工具

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，如果不存在返回None
        """
        return self._tools.get(tool_name)

    def get_tool_by_id(self, tool_id: int) -> Optional[ToolBase]:
        """
        通过ID获取工具

        Args:
            tool_id: 工具ID

        Returns:
            工具实例，如果不存在返回None
        """
        for tool in self._tools.values():
            if tool.id == tool_id:
                return tool
        return None

    def connect(
        self,
        from_tool: str,
        to_tool: str,
        from_port: str = "OutputImage",
        to_port: str = "InputImage",
    ) -> bool:
        """
        连接两个工具

        Args:
            from_tool: 源工具名称
            to_tool: 目标工具名称
            from_port: 源端口
            to_port: 目标端口

        Returns:
            连接成功返回True
        """
        if from_tool not in self._tools:
            self._logger.error(f"源工具不存在: {from_tool}")
            return False

        if to_tool not in self._tools:
            self._logger.error(f"目标工具不存在: {to_tool}")
            return False

        # 检查端口是否存在
        from_tool_obj = self._tools[from_tool]
        to_tool_obj = self._tools[to_tool]

        from_port_exists = any(
            p.name == from_port for p in from_tool_obj.output_ports
        )
        to_port_exists = any(
            p.name == to_port for p in to_tool_obj.input_ports
        )

        if not from_port_exists:
            self._logger.error(
                f"源工具不存在输出端口: {from_tool}.{from_port}"
            )
            return False

        if not to_port_exists:
            self._logger.error(f"目标工具不存在输入端口: {to_tool}.{to_port}")
            return False

        connection = ToolConnection(
            from_tool=from_tool,
            to_tool=to_tool,
            from_port=from_port,
            to_port=to_port,
        )

        self._connections.append(connection)
        self._logger.info(
            f"连接工具: {from_tool}.{from_port} -> {to_tool}.{to_port}"
        )

        return True

    def disconnect(self, from_tool: str, to_tool: str) -> bool:
        """
        断开两个工具的连接

        Args:
            from_tool: 源工具名称
            to_tool: 目标工具名称

        Returns:
            断开成功返回True
        """
        original_count = len(self._connections)

        self._connections = [
            conn
            for conn in self._connections
            if not (conn.from_tool == from_tool and conn.to_tool == to_tool)
        ]

        return len(self._connections) < original_count

    def get_connections_from(self, tool_name: str) -> List[ToolConnection]:
        """
        获取从指定工具出发的所有连接

        Args:
            tool_name: 工具名称

        Returns:
            连接列表
        """
        return [
            conn for conn in self._connections if conn.from_tool == tool_name
        ]

    def get_connections_to(self, tool_name: str) -> List[ToolConnection]:
        """
        获取到达指定工具的所有连接

        Args:
            tool_name: 工具名称

        Returns:
            连接列表
        """
        return [
            conn for conn in self._connections if conn.to_tool == tool_name
        ]

    def get_execution_order(self) -> List[str]:
        """
        获取执行顺序（拓扑排序）

        Returns:
            工具名称列表
        """
        if not self._tools:
            return []

        # 构建依赖图
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # 初始化所有节点
        for tool_name in self._tools.keys():
            in_degree[tool_name] = 0

        # 构建图
        for conn in self._connections:
            graph[conn.from_tool].append(conn.to_tool)
            in_degree[conn.to_tool] += 1

        # 拓扑排序 (Kahn算法)
        queue = [tool for tool in self._tools.keys() if in_degree[tool] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 如果有循环，只返回能排序的部分
        if len(result) != len(self._tools):
            self._logger.warning("检测到循环依赖，使用原始顺序")
            result = list(self._tools.keys())

        return result

    def run(self, input_data: ImageData = None) -> Dict[str, Any]:
        """
        执行流程

        Args:
            input_data: 输入图像数据（可选）

        Returns:
            执行结果字典，包含每个工具的输出
        """
        if not self._is_enabled:
            self._logger.debug(f"流程已禁用，跳过执行: {self._name}")
            return {}

        if self._is_running:
            self._logger.warning(f"流程正在运行中: {self._name}")
            return {}

        self._is_running = True
        self._last_error = None

        start_time = time.time()
        results = {}

        try:
            self._logger.info(f"开始执行流程: {self._name}")

            # 获取执行顺序
            execution_order = self.get_execution_order()
            self._logger.debug(f"执行顺序: {execution_order}")

            # 记录当前可用的输入数据
            current_input = input_data

            # 执行每个工具
            for tool_name in execution_order:
                tool = self._tools[tool_name]

                if not tool.is_enabled:
                    self._logger.debug(f"工具已禁用，跳过: {tool_name}")
                    continue

                # 处理输入数据：
                # 1. 检查是否有连接到该工具的连接
                has_connections = len(self.get_connections_to(tool_name)) > 0

                # 2. 如果没有连接，并且有当前可用的输入数据，设置为该工具的输入
                # 这确保了即使工具之间没有连接，每个工具都能获得输入数据
                if not has_connections and current_input is not None:
                    tool.set_input(current_input)
                    self._logger.debug(
                        f"为工具 {tool_name} 设置当前可用输入数据: {current_input.shape if current_input.is_valid else '无效'}"
                    )

                # 3. 检查工具是否有输入数据
                self._logger.debug(
                    f"工具 {tool_name} 输入状态: 有输入={tool.has_input()}"
                )

                # 执行工具
                try:
                    tool.run()

                    # 保存结果
                    output = tool.get_output()
                    result = tool.get_result()
                    if output is not None:
                        results[tool_name] = {
                            "output": output,
                            "result": result,
                        }
                        self._logger.debug(
                            f"工具 {tool_name} 输出: {output.shape if output.is_valid else '无效'}"
                        )

                        # 更新当前可用的输入数据为该工具的输出
                        current_input = output

                    # 将输出和结果传递给下一个工具
                    self._propagate_output(tool_name, output, result)

                except Exception as e:
                    self._logger.error(
                        f"工具执行失败: {tool_name}, 错误: {str(e)}"
                    )
                    results[tool_name] = {"error": str(e), "result": None}

            self._execution_time = time.time() - start_time
            self._logger.info(
                f"流程执行完成: {self._name}, 耗时={self._execution_time*1000:.2f}ms"
            )

            return results

        except Exception as e:
            self._last_error = str(e)
            self._logger.error(
                f"流程执行失败: {self._name}, 错误={self._last_error}"
            )
            return {"error": self._last_error}

        finally:
            self._is_running = False

    def _propagate_output(self, tool_name: str, output: Optional[ImageData],
                          result: Optional[ResultData] = None):
        """
        将工具输出和结果传递给下一个工具

        Args:
            tool_name: 工具名称
            output: 输出图像数据
            result: 输出结果数据（包含检测值等），可选
        """
        if output is None:
            return

        connections = self.get_connections_from(tool_name)
        for conn in connections:
            target_tool = self._tools.get(conn.to_tool)
            if target_tool is not None:
                target_tool.set_input(output, conn.to_port)
                # 同时传递结果数据，供通讯工具等使用
                if result is not None:
                    target_tool.set_upstream_result(result)

    def reset(self):
        """重置流程状态"""
        for tool in self._tools.values():
            tool.reset()
        self._is_running = False
        self._last_error = None
        self._execution_time = 0.0

    def clear(self):
        """清空流程"""
        self.reset()
        self._tools.clear()
        self._connections.clear()

    def get_info(self) -> Dict[str, Any]:
        """获取流程信息"""
        return {
            "name": self._name,
            "is_enabled": self._is_enabled,
            "tool_count": self.tool_count,
            "connection_count": len(self._connections),
            "tools": [tool.get_info() for tool in self._tools.values()],
            "connections": [
                {
                    "from": conn.from_tool,
                    "to": conn.to_tool,
                    "from_port": conn.from_port,
                    "to_port": conn.to_port,
                }
                for conn in self._connections
            ],
        }

    def copy(self) -> "Procedure":
        """创建流程拷贝"""
        new_procedure = Procedure(self._name)

        for tool in self._tools.values():
            new_tool = tool.copy()
            new_procedure.add_tool(new_tool)

        for conn in self._connections:
            new_procedure.connect(
                conn.from_tool, conn.to_tool, conn.from_port, conn.to_port
            )

        return new_procedure

    def __repr__(self) -> str:
        return f"Procedure(name={self._name}, tools={self.tool_count}, connections={len(self._connections)})"

    def __str__(self) -> str:
        return self.__repr__()


class ProcedureManager:
    """
    流程管理器，管理多个流程
    """

    def __init__(self):
        self._procedures: Dict[str, Procedure] = {}
        self._logger = logging.getLogger("ProcedureManager")

    @property
    def procedure_count(self) -> int:
        """获取流程数量"""
        return len(self._procedures)

    @property
    def procedures(self) -> List[Procedure]:
        """获取所有流程"""
        return list(self._procedures.values())

    def add_procedure(self, procedure: Procedure) -> bool:
        """
        添加流程

        Args:
            procedure: 流程实例

        Returns:
            添加成功返回True
        """
        if procedure.name in self._procedures:
            self._logger.warning(f"流程已存在: {procedure.name}")
            return False

        self._procedures[procedure.name] = procedure
        self._logger.info(f"添加流程: {procedure.name}")
        return True

    def remove_procedure(self, name: str) -> bool:
        """
        移除流程

        Args:
            name: 流程名称

        Returns:
            移除成功返回True
        """
        if name not in self._procedures:
            return False

        del self._procedures[name]
        self._logger.info(f"移除流程: {name}")
        return True

    def get_procedure(self, name: str) -> Optional[Procedure]:
        """
        获取流程

        Args:
            name: 流程名称

        Returns:
            流程实例，如果不存在返回None
        """
        return self._procedures.get(name)

    def run_all(self, input_data: ImageData = None) -> Dict[str, Any]:
        """
        运行所有流程

        Args:
            input_data: 输入图像数据

        Returns:
            所有流程的执行结果
        """
        results = {}
        for procedure in self._procedures.values():
            if procedure.is_enabled:
                results[procedure.name] = procedure.run(input_data)
        return results

    def reset_all(self):
        """重置所有流程"""
        for procedure in self._procedures.values():
            procedure.reset()

    def clear(self):
        """清空所有流程"""
        for procedure in self._procedures.values():
            procedure.clear()
        self._procedures.clear()

    def get_info(self) -> Dict[str, Any]:
        """获取管理器信息"""
        return {
            "procedure_count": self.procedure_count,
            "procedures": [p.get_info() for p in self._procedures.values()],
        }
