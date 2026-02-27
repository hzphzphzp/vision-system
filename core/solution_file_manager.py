#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案文件管理模块

提供完善的方案保存、加载和导出功能，支持多种格式。

Author: Vision System Team
Date: 2026-01-19
"""

import json
import logging
import os
import pickle
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from core.procedure import Procedure
from core.solution import Solution
from core.tool_base import ToolBase


class SolutionFileManager:
    """方案文件管理器"""

    def __init__(self):
        self._logger = logging.getLogger("SolutionFileManager")
        self._default_dir = Path("solutions")
        self._default_dir.mkdir(exist_ok=True)

    def save_solution(
        self,
        solution: Solution,
        path: str = None,
        format: str = "json",
        include_images: bool = False,
        compress: bool = False,
    ) -> bool:
        """
        保存方案到文件

        Args:
            solution: 方案实例
            path: 保存路径，如果为None则使用默认路径
            format: 文件格式 (json/yaml/pickle/vmsol)
            include_images: 是否包含图像数据
            compress: 是否压缩文件

        Returns:
            保存成功返回True
        """
        if path is None:
            path = self._default_dir / f"{solution.name}.{format}"

        try:
            # 准备方案数据
            data = self._prepare_solution_data(solution, include_images)

            # 根据格式保存
            if format.lower() == "json":
                self._save_json(data, path)
            elif format.lower() == "yaml":
                self._save_yaml(data, path)
            elif format.lower() == "pickle":
                self._save_pickle(data, path)
            elif format.lower() == "vmsol":
                self._save_vmsol(data, path, compress)
            else:
                raise ValueError(f"不支持的格式: {format}")

            self._logger.info(f"方案已保存: {path}")
            return True

        except Exception as e:
            self._logger.error(f"保存方案失败: {e}")
            return False

    def load_solution(
        self, path: str, format: str = None
    ) -> Optional[Solution]:
        """
        从文件加载方案

        Args:
            path: 文件路径
            format: 文件格式，如果为None则从文件扩展名推断

        Returns:
            加载的方案实例，失败返回None
        """
        if not os.path.exists(path):
            self._logger.error(f"文件不存在: {path}")
            return None

        if format is None:
            format = os.path.splitext(path)[1][1:]

        try:
            # 根据格式加载
            if format.lower() == "json":
                data = self._load_json(path)
            elif format.lower() == "yaml":
                data = self._load_yaml(path)
            elif format.lower() == "pickle":
                data = self._load_pickle(path)
            elif format.lower() == "vmsol":
                data = self._load_vmsol(path)
            else:
                raise ValueError(f"不支持的格式: {format}")

            # 创建方案实例
            solution = self._create_solution_from_data(data)

            self._logger.info(f"方案已加载: {path}")
            return solution

        except Exception as e:
            self._logger.error(f"加载方案失败: {e}")
            return None

    def export_solution_package(
        self,
        solution: Solution,
        path: str = None,
        include_code: bool = True,
        include_docs: bool = True,
        include_images: bool = False,
    ) -> bool:
        """
        导出方案包（包含代码、文档等）

        Args:
            solution: 方案实例
            path: 导出路径
            include_code: 是否包含代码
            include_docs: 是否包含文档
            include_images: 是否包含图像

        Returns:
            导出成功返回True
        """
        if path is None:
            path = self._default_dir / f"{solution.name}_package.zip"

        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                # 保存方案数据
                solution_data = self._prepare_solution_data(
                    solution, include_images
                )
                zf.writestr(
                    "solution.json",
                    json.dumps(solution_data, ensure_ascii=False, indent=2),
                )

                # 生成并保存代码
                if include_code:
                    code_generator = CodeGenerator()
                    code = code_generator.generate_solution_code(solution)
                    zf.writestr("solution.py", code)

                    # 生成工具代码
                    for procedure in solution.procedures:
                        proc_code = code_generator.generate_procedure_code(
                            procedure
                        )
                        zf.writestr(
                            f"procedures/{procedure.name}.py", proc_code
                        )

                # 生成文档
                if include_docs:
                    doc_generator = DocumentationGenerator()
                    doc = doc_generator.generate_solution_documentation(
                        solution
                    )
                    zf.writestr("README.md", doc)

                    # 生成API文档
                    api_doc = doc_generator.generate_api_documentation(
                        solution
                    )
                    zf.writestr("API.md", api_doc)

                # 保存配置文件
                config = {
                    "name": solution.name,
                    "version": "1.0.0",
                    "created": datetime.now().isoformat(),
                    "format": "vmsol",
                    "include_code": include_code,
                    "include_docs": include_docs,
                    "include_images": include_images,
                }
                zf.writestr(
                    "config.json",
                    json.dumps(config, ensure_ascii=False, indent=2),
                )

            self._logger.info(f"方案包已导出: {path}")
            return True

        except Exception as e:
            self._logger.error(f"导出方案包失败: {e}")
            return False

    def _prepare_solution_data(
        self, solution: Solution, include_images: bool = False
    ) -> Dict[str, Any]:
        """准备方案数据"""
        data = {
            "version": "1.0.0",
            "name": solution.name,
            "description": f"视觉检测方案: {solution.name}",
            "created": datetime.now().isoformat(),
            "run_interval": solution.run_interval,
            "procedures": [],
        }

        # 添加流程数据
        for procedure in solution.procedures:
            proc_data = {
                "name": procedure.name,
                "description": f"检测流程: {procedure.name}",
                "is_enabled": procedure.is_enabled,
                "tools": [],
                "connections": [],
                "metadata": {
                    "tool_count": len(procedure.tools),
                    "connection_count": len(procedure.connections),
                },
            }

            # 添加工具数据
            for tool in procedure.tools:
                tool_info = tool.get_info()
                tool_data = {
                    "category": tool.tool_category,
                    "name": tool.tool_name,
                    "display_name": tool.name,
                    "description": tool.tool_description,
                    "params": tool.get_all_params(),
                    "position": tool_info.get("position"),
                    "metadata": {
                        "has_output": tool.has_output(),
                        "is_enabled": tool.is_enabled,
                    },
                }

                # 包含图像数据
                if include_images and hasattr(tool, "get_output_image"):
                    try:
                        output = tool.get_output()
                        if output and hasattr(output, "data"):
                            import base64

                            import numpy as np

                            if isinstance(output.data, np.ndarray):
                                img_data = base64.b64encode(
                                    output.data.tobytes()
                                ).decode("utf-8")
                                tool_data["output_image"] = {
                                    "format": "numpy_base64",
                                    "shape": output.data.shape,
                                    "dtype": str(output.data.dtype),
                                    "data": img_data,
                                }
                    except Exception:
                        pass

                proc_data["tools"].append(tool_data)

            # 添加连接数据
            for conn in procedure.connections:
                conn_data = {
                    "from": conn.from_tool,
                    "to": conn.to_tool,
                    "from_port": conn.from_port,
                    "to_port": conn.to_port,
                    "metadata": {"connection_type": "data_flow"},
                }
                proc_data["connections"].append(conn_data)

            data["procedures"].append(proc_data)

        return data

    def _save_json(self, data: Dict[str, Any], path: str):
        """保存为JSON格式"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_yaml(self, data: Dict[str, Any], path: str):
        """保存为YAML格式"""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data, f, default_flow_style=False, allow_unicode=True, indent=2
            )

    def _save_pickle(self, data: Dict[str, Any], path: str):
        """保存为Pickle格式"""
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def _save_vmsol(
        self, data: Dict[str, Any], path: str, compress: bool = False
    ):
        """保存为VisionMaster格式"""
        if compress:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "solution.json",
                    json.dumps(data, ensure_ascii=False, indent=2),
                )
        else:
            self._save_json(data, path)

    def _load_json(self, path: str) -> Dict[str, Any]:
        """加载JSON格式"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """加载YAML格式"""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_pickle(self, path: str) -> Dict[str, Any]:
        """加载Pickle格式"""
        with open(path, "rb") as f:
            return pickle.load(f)

    def _load_vmsol(self, path: str) -> Dict[str, Any]:
        """加载VisionMaster格式"""
        if path.endswith(".zip"):
            with zipfile.ZipFile(path, "r") as zf:
                with zf.open("solution.json") as f:
                    return json.load(f)
        else:
            return self._load_json(path)

    def _create_solution_from_data(self, data: Dict[str, Any]) -> Solution:
        """从数据创建方案实例"""
        solution = Solution(data.get("name", "Solution"))
        solution.run_interval = data.get("run_interval", 100)

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

            solution.add_procedure(procedure)

        return solution

    def import_solution_package(self, path: str) -> Optional[Solution]:
        """导入方案包并加载为Solution实例

        Args:
            path: 方案包文件路径

        Returns:
            加载的方案实例，失败返回None
        """
        try:
            if not os.path.exists(path):
                self._logger.error(f"文件不存在: {path}")
                return None

            # 根据文件扩展名选择加载方式
            if path.endswith(".vmsol"):
                data = self._load_vmsol(path)
            elif path.endswith(".json"):
                data = self._load_json(path)
            elif path.endswith(".yaml") or path.endswith(".yml"):
                data = self._load_yaml(path)
            elif path.endswith(".pickle") or path.endswith(".pkl"):
                data = self._load_pickle(path)
            else:
                # 尝试所有格式
                data = (
                    self._load_json(path)
                    or self._load_yaml(path)
                    or self._load_pickle(path)
                    or self._load_vmsol(path)
                )

            if data:
                # 从数据创建Solution实例
                solution = self._create_solution_from_data(data)
                self._logger.info(f"方案包已导入并加载: {path}")
                return solution
            else:
                self._logger.error(f"无法解析方案包: {path}")
                return None

        except Exception as e:
            self._logger.error(f"导入方案包失败: {e}")
            return None


class CodeGenerator:

    def __init__(self):
        self._logger = logging.getLogger("CodeGenerator")

    def generate_solution_code(self, solution: Solution) -> str:
        """生成方案代码"""
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{solution.name} 视觉检测方案

自动生成的代码，包含完整的方案实现。

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import os
import logging
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.solution import Solution
from core.procedure import Procedure
from data.image_data import ImageData
from core.tool_base import ToolRegistry


class {solution.name.replace(' ', '')}Solution:
    """
    {solution.name} 视觉检测方案
    
    包含 {solution.procedure_count} 个检测流程。
    """
    
    def __init__(self):
        """初始化方案"""
        self.solution = Solution("{solution.name}")
        self._setup_procedures()
    
    def _setup_procedures(self):
        """设置流程"""
'''

        # 为每个流程生成代码
        for i, procedure in enumerate(solution.procedures):
            code += f"""
        # 流程 {i+1}: {procedure.name}
        self._setup_procedure_{i+1}()"""

        code += '''
    
    def run(self, input_image: ImageData = None) -> Dict[str, Any]:
        """
        运行方案
        
        Args:
            input_image: 输入图像数据
            
        Returns:
            执行结果字典
        """
        return self.solution.run(input_image)
    
    def run_continuous(self):
        """连续运行方案"""
        self.solution.runing()
    
    def stop(self):
        """停止运行"""
        self.solution.stop_run()
    
    def save(self, path: str) -> bool:
        """保存方案"""
        return self.solution.save(path)
    
    def load(self, path: str) -> bool:
        """加载方案"""
        return self.solution.load(path)


if __name__ == "__main__":
    # 创建并运行方案
    solution = {solution.name.replace(' ', '')}Solution()
    
    # 运行方案
    result = solution.run()
    print("方案运行结果:", result)
    
    # 连续运行（可选）
    # solution.run_continuous()
    # import time
    # time.sleep(10)
    # solution.stop()
'''

        return code

    def generate_procedure_code(self, procedure: Procedure) -> str:
        """生成流程代码"""
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{procedure.name} 检测流程

自动生成的流程代码。

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import os
import logging
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.procedure import Procedure
from core.tool_base import ToolRegistry
from data.image_data import ImageData


class {procedure.name.replace(' ', '')}Procedure:
    """
    {procedure.name} 检测流程
    
    包含 {len(procedure.tools)} 个工具。
    """
    
    def __init__(self):
        """初始化流程"""
        self.procedure = Procedure("{procedure.name}")
        self._setup_tools()
        self._setup_connections()
    
    def _setup_tools(self):
        """设置工具"""
'''

        # 为每个工具生成代码
        for i, tool in enumerate(procedure.tools):
            code += f"""
        # 工具 {i+1}: {tool.name}
        self._add_tool_{i+1}()"""

        code += '''
    
    def _setup_connections(self):
        """设置工具连接"""
'''

        # 为每个连接生成代码
        for i, conn in enumerate(procedure.connections):
            code += f"""
        # 连接 {i+1}: {conn.from_tool} -> {conn.to_tool}
        self.procedure.connect("{conn.from_tool}", "{conn.to_tool}", 
                              "{conn.from_port}", "{conn.to_port}")"""

        code += '''
    
    def run(self, input_image: ImageData = None) -> Dict[str, Any]:
        """
        运行流程
        
        Args:
            input_image: 输入图像数据
            
        Returns:
            执行结果字典
        """
        return self.procedure.run(input_image)
    
    def get_result(self) -> Optional[Any]:
        """获取最后一个工具的输出结果"""
        if self.procedure.tools:
            last_tool = self.procedure.tools[-1]
            if last_tool.has_output():
                return last_tool.get_output()
        return None


if __name__ == "__main__":
    # 创建并运行流程
    procedure = {procedure.name.replace(' ', '')}Procedure()
    
    # 运行流程
    result = procedure.run()
    print("流程运行结果:", result)
    
    # 获取结果
    final_result = procedure.get_result()
    if final_result:
        print("最终结果:", final_result)
'''

        return code


class DocumentationGenerator:
    """文档生成器"""

    def __init__(self):
        self._logger = logging.getLogger("DocumentationGenerator")

    def generate_solution_documentation(self, solution: Solution) -> str:
        """生成方案文档"""
        doc = f"""# {solution.name} 视觉检测方案

## 概述

本方案包含 {solution.procedure_count} 个检测流程，用于实现视觉检测功能。

## 流程列表

"""

        for i, procedure in enumerate(solution.procedures):
            doc += f"### {i+1}. {procedure.name}\n\n"
            doc += f"- 工具数量: {len(procedure.tools)}\n"
            doc += f"- 连接数量: {len(procedure.connections)}\n"
            doc += f"- 状态: {'启用' if procedure.is_enabled else '禁用'}\n\n"

            if procedure.tools:
                doc += "#### 工具列表\n\n"
                for j, tool in enumerate(procedure.tools):
                    doc += f"{j+1}. **{tool.name}** ({tool.tool_category})\n"
                    doc += f"   - 描述: {tool.tool_description}\n"
                    doc += f"   - 状态: {'启用' if tool.is_enabled else '禁用'}\n\n"

        doc += """## 使用方法

```python
from core.solution import Solution
from data.image_data import ImageData

# 加载方案
solution = Solution.load("solution.vmsol")

# 准备输入图像
input_image = ImageData.from_file("input.jpg")

# 运行方案
result = solution.run(input_image)
print("运行结果:", result)
```

## 参数说明

每个工具都有相应的参数，可以通过以下方式设置：

```python
# 获取工具
tool = solution.get_procedure("流程1").get_tool("工具名")

# 设置参数
tool.set_param("参数名", 参数值)

# 获取参数
value = tool.get_param("参数名")
```

## 注意事项

1. 确保所有依赖的库已正确安装
2. 检查图像路径是否正确
3. 根据实际需求调整工具参数
4. 运行前建议先进行单步测试

## 版本信息

- 版本: 1.0.0
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 生成工具: Vision System Code Generator
"""

        return doc

    def generate_api_documentation(self, solution: Solution) -> str:
        """生成API文档"""
        doc = f"""# {solution.name} API文档

## Solution类

### 属性

- `name`: 方案名称
- `state`: 方案状态
- `run_interval`: 运行间隔(ms)
- `is_running`: 是否正在运行
- `is_continuous_run`: 是否连续运行
- `procedures`: 流程列表

### 方法

#### run(input_image: ImageData = None) -> Dict[str, Any]
单次运行方案。

**参数:**
- `input_image`: 输入图像数据

**返回:**
- 执行结果字典

#### runing() -> None
开始连续运行。

#### stop_run(wait_time: int = 3) -> None
停止运行。

**参数:**
- `wait_time`: 等待超时（秒）

#### save(path: str = None) -> bool
保存方案。

**参数:**
- `path`: 保存路径

**返回:**
- 保存是否成功

#### load(path: str) -> bool
加载方案。

**参数:**
- `path`: 加载路径

**返回:**
- 加载是否成功

## Procedure类

### 属性

- `name`: 流程名称
- `is_enabled`: 是否启用
- `tools`: 工具列表
- `connections`: 连接列表

### 方法

#### run(input_image: ImageData = None) -> Dict[str, Any]
运行流程。

#### add_tool(tool: ToolBase) -> bool
添加工具。

#### connect(from_tool: str, to_tool: str, from_port: str, to_port: str) -> bool
连接工具。

## ToolBase类

### 属性

- `tool_name`: 工具名称
- `tool_category`: 工具类别
- `is_enabled`: 是否启用
- `has_output`: 是否有输出

### 方法

#### set_param(name: str, value: Any) -> None
设置参数。

#### get_param(name: str, default: Any = None) -> Any
获取参数。

#### run() -> bool
运行工具。

#### get_output() -> Optional[Any]
获取输出结果。

## 示例代码

```python
# 创建方案
solution = Solution("我的方案")

# 添加流程
procedure = Procedure("流程1")
solution.add_procedure(procedure)

# 添加工具
from core.tool_base import ToolRegistry
tool = ToolRegistry.create_tool("ImageSource", "本地图像")
procedure.add_tool(tool)

# 连接工具
procedure.connect("本地图像", "高斯滤波", "OutputImage", "InputImage")

# 运行方案
result = solution.run()
```
"""

        return doc
