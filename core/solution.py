#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案管理模块

提供方案(Solution)类，管理多个流程的执行和状态控制。

Author: Vision System Team
Date: 2025-01-04
"""

import logging
import os
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加Qt相关导入用于非阻塞操作
try:
    from PyQt5.QtCore import QEventLoop, QTimer
    from PyQt5.QtWidgets import QApplication
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    try:
        from PyQt6.QtCore import QEventLoop, QTimer
        from PyQt6.QtWidgets import QApplication
        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False

from core.procedure import Procedure, ProcedureManager
from data.image_data import ImageData
from utils.exceptions import SolutionException
from core.pipeline import DeterministicPipeline, PipelineStage


class SolutionState(Enum):
    """方案状态"""

    IDLE = "idle"
    RUNNING = "running"
    CONTINUOUS_RUN = "continuous_run"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SolutionEvent:
    """方案事件"""

    event_type: str  # 事件类型
    procedure_name: str = None
    tool_name: str = None
    data: Any = None
    timestamp: float = field(default_factory=time.time)


class SolutionCallback:
    """方案回调接口"""

    def __init__(self):
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def register(self, event_type: str, callback: Callable):
        """注册事件回调"""
        self._callbacks[event_type].append(callback)

    def unregister(self, event_type: str, callback: Callable):
        """取消事件回调"""
        if callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)

    def trigger(self, event_type: str, **kwargs):
        """触发事件"""
        event = SolutionEvent(event_type=event_type, **kwargs)
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logging.getLogger("SolutionCallback").error(
                    f"回调执行失败: {e}"
                )


class Solution:
    """
    方案类，管理多个流程

    功能：
    - 流程管理（添加/移除流程）
    - 执行控制（单次运行/连续运行/停止）
    - 状态管理（运行状态/错误状态）
    - 事件回调（执行开始/结束/错误等）
    - 方案保存/加载

    示例：
        # 创建方案
        solution = Solution("检测方案")

        # 添加流程
        procedure1 = Procedure("流程1")
        solution.add_procedure(procedure1)

        # 单次运行
        solution.run()

        # 连续运行
        solution.runing()
        time.sleep(10)
        solution.stop_run()

        # 保存方案
        solution.save("my_solution.vmsol")
    """

    def __init__(self, name: str = "Solution"):
        """
        初始化方案

        Args:
            name: 方案名称
        """
        self._name = name
        self._procedure_manager = ProcedureManager()
        self._state = SolutionState.IDLE
        self._run_interval = 100  # ms
        self._continuous_thread = None
        self._is_running = False
        self._last_error: Optional[str] = None
        self._execution_time = 0.0
        self._current_input: Optional[ImageData] = None
        self._solution_path: Optional[str] = None  # 添加方案路径属性

        # 流水线相关
        self._pipeline: Optional[DeterministicPipeline] = None
        self._pipeline_mode = False
        self._pipeline_buffer_size = 3
        self._results: Dict = {}

        self._callback = SolutionCallback()
        self._logger = logging.getLogger(f"Solution.{self._name}")

        # 初始化回调
        self._init_callbacks()

    def _init_callbacks(self):
        """初始化默认回调"""
        pass

    @property
    def name(self) -> str:
        """获取方案名称"""
        return self._name

    @name.setter
    def name(self, value: str):
        """设置方案名称"""
        self._name = value

    @property
    def state(self) -> SolutionState:
        """获取方案状态"""
        return self._state

    @property
    def run_interval(self) -> int:
        """获取运行间隔(ms)"""
        return self._run_interval

    @run_interval.setter
    def run_interval(self, value: int):
        """设置运行间隔(ms)"""
        self._run_interval = max(0, value)

    @property
    def is_running(self) -> bool:
        """获取运行状态"""
        return self._state in [
            SolutionState.RUNNING,
            SolutionState.CONTINUOUS_RUN,
        ]

    @property
    def solution_path(self) -> Optional[str]:
        """获取方案路径"""
        return self._solution_path

    @solution_path.setter
    def solution_path(self, value: Optional[str]):
        """设置方案路径"""
        self._solution_path = value

    @property
    def is_continuous_run(self) -> bool:
        """是否为连续运行状态"""
        return self._state == SolutionState.CONTINUOUS_RUN

    @property
    def last_error(self) -> Optional[str]:
        """获取最后错误"""
        return self._last_error

    @property
    def execution_time(self) -> float:
        """获取执行时间(秒)"""
        return self._execution_time

    @property
    def procedure_count(self) -> int:
        """获取流程数量"""
        return self._procedure_manager.procedure_count

    @property
    def procedures(self) -> List[Procedure]:
        """获取所有流程"""
        return self._procedure_manager.procedures

    @property
    def current_input(self) -> Optional[ImageData]:
        """获取当前输入数据"""
        return self._current_input

    def set_input(self, image_data: ImageData):
        """
        设置输入数据

        Args:
            image_data: 输入图像数据
        """
        self._current_input = image_data

    def add_procedure(self, procedure: Procedure) -> bool:
        """
        添加流程

        Args:
            procedure: 流程实例

        Returns:
            添加成功返回True
        """
        return self._procedure_manager.add_procedure(procedure)

    def remove_procedure(self, name: str) -> bool:
        """
        移除流程

        Args:
            name: 流程名称

        Returns:
            移除成功返回True
        """
        return self._procedure_manager.remove_procedure(name)

    def get_procedure(self, name: str) -> Optional[Procedure]:
        """
        获取流程

        Args:
            name: 流程名称

        Returns:
            流程实例，如果不存在返回None
        """
        return self._procedure_manager.get_procedure(name)

    def run(self, input_data: ImageData = None) -> Dict[str, Any]:
        """
        单次运行方案

        Args:
            input_data: 输入图像数据（可选）

        Returns:
            执行结果字典
        """
        if self._pipeline_mode and self._pipeline is not None:
            return self._run_pipeline(input_data)
        
        if self._state == SolutionState.CONTINUOUS_RUN:
            self._logger.warning("连续运行中，请先停止")
            return {"error": "连续运行中，请先停止"}

        if self._is_running:
            self._logger.warning("方案正在运行中")
            return {"error": "方案正在运行中"}

        self._is_running = True
        self._state = SolutionState.RUNNING
        self._last_error = None

        start_time = time.time()
        results = {}

        try:
            self._logger.info(f"开始运行方案: {self._name}")

            # 触发开始事件
            self._callback.trigger("run_started")

            # 使用提供的输入数据或当前输入数据
            input_image = input_data or self._current_input

            # 执行所有流程
            results = self._procedure_manager.run_all(input_image)

            self._execution_time = time.time() - start_time
            self._state = SolutionState.IDLE
            self._is_running = False

            # 触发完成事件
            self._callback.trigger("run_completed", data=results)

            self._logger.info(
                f"方案运行完成: {self._name}, 耗时={self._execution_time*1000:.2f}ms"
            )

            return results

        except Exception as e:
            self._last_error = str(e)
            self._state = SolutionState.ERROR
            self._execution_time = time.time() - start_time
            self._is_running = False

            self._logger.error(
                f"方案运行失败: {self._name}, 错误={self._last_error}"
            )

            # 触发错误事件
            self._callback.trigger(
                "run_error", data={"error": self._last_error}
            )

            return {"error": self._last_error}

    def enable_pipeline_mode(self, buffer_size: int = 3) -> None:
        """启用流水线处理模式
        
        Args:
            buffer_size: 流水线缓冲区大小
        """
        self._pipeline_mode = True
        self._pipeline_buffer_size = buffer_size
        
        # 创建流水线
        self._pipeline = DeterministicPipeline(max_pipeline_depth=buffer_size)
        
        # 阶段1: 执行流程
        def execute_stage(frame):
            results = {}
            for proc in self._procedure_manager.procedures:
                if proc.is_enabled:
                    result = proc.run(frame.data)
                    results[proc.name] = result
            return results
        
        stage = PipelineStage("execute", execute_stage,
                             output_callback=self._on_pipeline_output)
        self._pipeline.add_stage(stage)
        
        self._logger.info(f"流水线模式已启用，缓冲区大小: {buffer_size}")
    
    def _on_pipeline_output(self, frame, result):
        """流水线输出回调"""
        self._results[frame.frame_id] = {
            "frame_id": frame.frame_id,
            "timestamp": frame.timestamp,
            "result": result
        }
    
    def put_input(self, image_data: ImageData) -> bool:
        """放入输入图像(流水线模式)
        
        Args:
            image_data: 图像数据
            
        Returns:
            是否成功放入
        """
        if not self._pipeline_mode or self._pipeline is None:
            raise RuntimeError("Pipeline mode not enabled")
        
        return self._pipeline.put_frame(image_data)
    
    def _run_pipeline(self, input_data: ImageData = None) -> Dict:
        """流水线模式运行"""
        if self._pipeline is None:
            return {}
        
        # 启动流水线
        self._pipeline.start()
        
        try:
            if input_data is not None:
                # 放入输入数据
                self.put_input(input_data)
                
                # 等待处理完成
                time.sleep(0.1)
                
                # 返回最新结果
                if self._results:
                    latest_id = max(self._results.keys())
                    return self._results[latest_id]
            
            return {}
        finally:
            self._pipeline.stop()

    def runing(self):
        """
        连续运行方案

        注意事项：
        - 此方法会启动一个新线程
        - 调用stop_run()停止连续运行
        """
        if self._state == SolutionState.CONTINUOUS_RUN:
            self._logger.warning("已经在连续运行中")
            return

        if self._is_running:
            self._logger.warning("方案正在运行，请先停止")
            return

        self._state = SolutionState.CONTINUOUS_RUN
        self._is_running = True
        self._last_error = None

        self._logger.info(f"开始连续运行方案: {self._name}")

        # 触发开始事件
        self._callback.trigger("continuous_run_started")

        # 启动连续运行线程
        self._continuous_thread = threading.Thread(
            target=self._continuous_run_loop, daemon=True
        )
        self._continuous_thread.start()

    def _continuous_run_loop(self):
        """连续运行循环"""
        interval_sec = self._run_interval / 1000.0

        while self._state == SolutionState.CONTINUOUS_RUN and self._is_running:
            try:
                start_time = time.time()

                # 执行方案
                self.run()

                # 等待间隔 - 使用time.sleep避免Qt线程问题
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_sec - elapsed)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                self._logger.error(f"连续运行出错: {e}")
                time.sleep(interval_sec)

        self._logger.info(f"连续运行已停止: {self._name}")

    def stop_run(self, wait_time: int = 3):
        """
        停止运行

        Args:
            wait_time: 等待超时（秒）
        """
        if self._state == SolutionState.IDLE:
            self._logger.warning("方案未在运行")
            return

        self._logger.info(f"停止方案运行: {self._name}")

        # 设置停止标志
        self._is_running = False
        self._state = SolutionState.IDLE

        # 等待连续运行线程停止
        if self._continuous_thread is not None:
            self._continuous_thread.join(timeout=wait_time)
            if self._continuous_thread.is_alive():
                self._logger.warning("连续运行线程未在规定时间内停止")
            self._continuous_thread = None

        # 重置所有流程
        self._procedure_manager.reset_all()

        self._logger.info(f"方案运行已停止: {self._name}")

        # 触发停止事件
        self._callback.trigger("run_stopped")

    def step_run(self, procedure_name: str = None) -> Dict[str, Any]:
        """
        单步运行

        Args:
            procedure_name: 流程名称，如果为None则运行第一个流程

        Returns:
            执行结果
        """
        if procedure_name:
            procedure = self.get_procedure(procedure_name)
            if procedure:
                return procedure.run(self._current_input)
        elif self.procedures:
            return self.procedures[0].run(self._current_input)
        return {"error": "没有可执行的流程"}

    def register_callback(self, event_type: str, callback: Callable):
        """
        注册事件回调

        Args:
            event_type: 事件类型 (run_started/run_completed/run_error/run_stopped/continuous_run_started)
            callback: 回调函数
        """
        self._callback.register(event_type, callback)

    def unregister_callback(self, event_type: str, callback: Callable):
        """
        取消事件回调

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self._callback.unregister(event_type, callback)

    def save(self, path: str = None, password: str = None) -> bool:
        """
        保存方案

        Args:
            path: 保存路径，如果为None则使用默认路径
            password: 密码（暂未实现）

        Returns:
            保存成功返回True
        """
        import json

        path = path or f"{self._name}.vmsol"

        try:
            data = {
                "name": self._name,
                "run_interval": self._run_interval,
                "procedures": [],
            }

            for procedure in self.procedures:
                proc_data = {
                    "name": procedure.name,
                    "is_enabled": procedure.is_enabled,
                    "tools": [],
                    "connections": [],
                }

                for tool in procedure.tools:
                    tool_info = tool.get_info()
                    proc_data["tools"].append(
                        {
                            "category": tool.tool_category,
                            "name": tool.tool_name,
                            "display_name": tool.name,
                            "params": tool.get_all_params(),
                            "position": tool_info.get("position"),
                        }
                    )

                for conn in procedure.connections:
                    proc_data["connections"].append(
                        {
                            "from": conn.from_tool,
                            "to": conn.to_tool,
                            "from_port": conn.from_port,
                            "to_port": conn.to_port,
                        }
                    )

                data["procedures"].append(proc_data)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 保存路径
            self._solution_path = path

            self._logger.info(f"方案已保存: {path}")
            return True

        except Exception as e:
            self._logger.error(f"保存方案失败: {e}")
            return False

    def load(self, path: str, password: str = None) -> bool:
        """
        加载方案

        Args:
            path: 加载路径
            password: 密码（暂未实现）

        Returns:
            加载成功返回True
        """
        import json

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 清空当前方案
            self._procedure_manager.clear()
            self._name = data.get("name", "Solution")
            self._run_interval = data.get("run_interval", 100)

            # 加载流程
            for proc_data in data.get("procedures", []):
                procedure = Procedure(proc_data.get("name", "Procedure"))
                procedure.is_enabled = proc_data.get("is_enabled", True)

                # 加载工具
                tool_instances = {}
                for tool_data in proc_data.get("tools", []):
                    category = tool_data.get("category")
                    tool_name = tool_data.get("name")
                    display_name = tool_data.get("display_name")

                    try:
                        from core.tool_base import ToolRegistry

                        tool = ToolRegistry.create_tool(
                            category, tool_name, display_name
                        )

                        # 设置参数
                        for key, value in tool_data.get("params", {}).items():
                            tool.set_param(key, value)

                        procedure.add_tool(tool)
                        tool_instances[display_name] = tool

                    except Exception as e:
                        self._logger.warning(
                            f"加载工具失败: {category}.{tool_name}, {e}"
                        )

                # 加载连接
                for conn_data in proc_data.get("connections", []):
                    from_name = conn_data.get("from")
                    to_name = conn_data.get("to")
                    from_port = conn_data.get("from_port", "OutputImage")
                    to_port = conn_data.get("to_port", "InputImage")

                    # 尝试使用新名称
                    if from_name not in tool_instances:
                        for tool in tool_instances.values():
                            if tool.tool_name == from_name:
                                from_name = tool.name
                                break

                    if to_name not in tool_instances:
                        for tool in tool_instances.values():
                            if tool.tool_name == to_name:
                                to_name = tool.name
                                break

                    procedure.connect(from_name, to_name, from_port, to_port)

                self.add_procedure(procedure)

            # 保存加载的路径
            self._solution_path = path

            self._logger.info(f"方案已加载: {path}")
            return True

        except Exception as e:
            self._logger.error(f"加载方案失败: {e}")
            return False

    def reset(self):
        """重置方案状态"""
        self.stop_run()
        self._procedure_manager.reset_all()
        self._current_input = None
        self._last_error = None
        self._execution_time = 0.0
        self._state = SolutionState.IDLE

    def clear(self):
        """清空方案"""
        self.reset()
        self._procedure_manager.clear()

    def get_info(self) -> Dict[str, Any]:
        """获取方案信息"""
        return {
            "name": self._name,
            "state": self._state.value,
            "run_interval": self._run_interval,
            "is_running": self.is_running,
            "procedure_count": self.procedure_count,
            "execution_time": self._execution_time,
            "procedures": [p.get_info() for p in self.procedures],
        }

    def copy(self) -> "Solution":
        """创建方案拷贝"""
        new_solution = Solution(self._name)
        new_solution._run_interval = self._run_interval

        for procedure in self.procedures:
            new_solution.add_procedure(procedure.copy())

        return new_solution

    def __repr__(self) -> str:
        return (
            f"Solution(name={self._name}, "
            f"state={self._state.value}, "
            f"procedures={self.procedure_count})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class SolutionManager:
    """
    方案管理器，管理多个方案
    """

    def __init__(self):
        self._solutions: Dict[str, Solution] = {}
        self._logger = logging.getLogger("SolutionManager")

    @property
    def solution_count(self) -> int:
        """获取方案数量"""
        return len(self._solutions)

    @property
    def solutions(self) -> List[Solution]:
        """获取所有方案"""
        return list(self._solutions.values())

    @property
    def current_solution(self) -> Optional[Solution]:
        """获取当前方案"""
        if self._solutions:
            return list(self._solutions.values())[0]
        return None

    def add_solution(self, solution: Solution) -> bool:
        """
        添加方案

        Args:
            solution: 方案实例

        Returns:
            添加成功返回True
        """
        if solution.name in self._solutions:
            self._logger.warning(f"方案已存在: {solution.name}")
            return False

        self._solutions[solution.name] = solution
        self._logger.info(f"添加方案: {solution.name}")
        return True

    def remove_solution(self, name: str) -> bool:
        """
        移除方案

        Args:
            name: 方案名称

        Returns:
            移除成功返回True
        """
        if name not in self._solutions:
            return False

        solution = self._solutions[name]
        solution.stop_run()
        del self._solutions[name]
        self._logger.info(f"移除方案: {name}")
        return True

    def get_solution(self, name: str) -> Optional[Solution]:
        """
        获取方案

        Args:
            name: 方案名称

        Returns:
            方案实例，如果不存在返回None
        """
        return self._solutions.get(name)

    def run_all(self, input_data: ImageData = None) -> Dict[str, Any]:
        """
        运行所有方案

        Args:
            input_data: 输入图像数据

        Returns:
            所有方案的执行结果
        """
        results = {}
        for solution in self._solutions.values():
            if solution.is_enabled:
                results[solution.name] = solution.run(input_data)
        return results

    def stop_all(self):
        """停止所有方案"""
        for solution in self._solutions.values():
            solution.stop_run()

    def clear(self):
        """清空所有方案"""
        for solution in self._solutions.values():
            solution.stop_run()
        self._solutions.clear()

    def get_info(self) -> Dict[str, Any]:
        """获取管理器信息"""
        return {
            "solution_count": self.solution_count,
            "solutions": [s.get_info() for s in self._solutions.values()],
        }
