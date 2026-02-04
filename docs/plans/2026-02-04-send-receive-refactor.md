# 发送/接收数据工具重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构发送/接收数据工具，移除通讯管理功能，改为复用已有连接并处理流程数据

**Architecture:** 
1. **解耦原则**：SendDataTool/ReceiveDataTool 只负责数据转换和路由，不管理通讯连接
2. **连接复用**：通过参数选择 CommunicationManager 中已建立的连接
3. **数据流**：发送工具接收上游算法结果→转换格式→通过已有连接发送；接收工具通过已有连接接收→转换格式→输出给下游

**Tech Stack:** Python, ToolBase, CommunicationManager, ProtocolBase

---

## Phase 1: 重构 SendDataTool（发送数据工具）

### Task 1: 创建数据映射配置类

**Files:**
- Create: `core/data_mapping.py`
- Test: `tests/test_data_mapping.py`

**Step 1: 编写失败测试**

```python
# tests/test_data_mapping.py
import pytest
import numpy as np
from core.data_mapping import DataMapper, DataMappingRule

def test_data_mapper_creation():
    """测试数据映射器创建"""
    mapper = DataMapper()
    assert mapper is not None

def test_simple_mapping():
    """测试简单字段映射"""
    mapper = DataMapper()
    
    # 添加映射规则：将输入的"result"字段映射到输出的"status"
    mapper.add_rule(DataMappingRule(
        source_field="result",
        target_field="status",
        transform_func=lambda x: "OK" if x else "NG"
    ))
    
    # 测试映射
    input_data = {"result": True, "other": "ignore"}
    output = mapper.map(input_data)
    
    assert output["status"] == "OK"
    assert "other" not in output  # 未映射的字段被忽略

def test_nested_mapping():
    """测试嵌套字段映射"""
    mapper = DataMapper()
    
    # 嵌套字段映射：input.position.x -> output.x
    mapper.add_rule(DataMappingRule(
        source_field="position.x",
        target_field="x",
        transform_func=float
    ))
    
    input_data = {"position": {"x": 100, "y": 200}}
    output = mapper.map(input_data)
    
    assert output["x"] == 100.0
```

**Step 2: 运行测试确认失败**

```bash
cd D:\vision_system-opencode
pytest tests/test_data_mapping.py -v
```

Expected: FAIL - "DataMapper not defined"

**Step 3: 实现数据映射类**

```python
# core/data_mapping.py
"""
数据映射模块

用于将上游工具的输出数据映射为发送格式
支持字段映射、数据转换、嵌套字段访问
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class DataMappingRule:
    """数据映射规则"""
    source_field: str  # 源字段名（支持嵌套，如"position.x"）
    target_field: str  # 目标字段名
    transform_func: Optional[Callable] = None  # 转换函数
    default_value: Any = None  # 默认值


class DataMapper:
    """数据映射器
    
    将输入数据按照规则映射为输出格式
    支持：
    - 字段重命名
    - 数据类型转换
    - 嵌套字段访问
    - 默认值填充
    """
    
    def __init__(self):
        self._rules: List[DataMappingRule] = []
    
    def add_rule(self, rule: DataMappingRule) -> None:
        """添加映射规则"""
        self._rules.append(rule)
    
    def remove_rule(self, target_field: str) -> None:
        """移除映射规则"""
        self._rules = [r for r in self._rules if r.target_field != target_field]
    
    def clear_rules(self) -> None:
        """清除所有规则"""
        self._rules.clear()
    
    def map(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据映射
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            映射后的输出数据字典
        """
        output = {}
        
        for rule in self._rules:
            try:
                # 获取源字段值（支持嵌套）
                value = self._get_nested_value(input_data, rule.source_field)
                
                # 应用转换函数
                if rule.transform_func and value is not None:
                    value = rule.transform_func(value)
                
                # 使用默认值
                if value is None:
                    value = rule.default_value
                
                # 设置目标字段
                if value is not None:
                    self._set_nested_value(output, rule.target_field, value)
                    
            except Exception as e:
                # 映射失败，跳过该字段
                print(f"Mapping failed for {rule.source_field}: {e}")
                continue
        
        return output
    
    def _get_nested_value(self, data: Dict, field_path: str) -> Any:
        """获取嵌套字段值
        
        Args:
            data: 数据字典
            field_path: 字段路径（如"a.b.c"）
            
        Returns:
            字段值，如果不存在返回None
        """
        parts = field_path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict, field_path: str, value: Any) -> None:
        """设置嵌套字段值
        
        Args:
            data: 数据字典
            field_path: 字段路径
            value: 要设置的值
        """
        parts = field_path.split(".")
        current = data
        
        # 创建中间层级
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # 设置最终值
        current[parts[-1]] = value
    
    def to_json(self) -> str:
        """将映射规则序列化为JSON"""
        rules_data = []
        for rule in self._rules:
            rules_data.append({
                "source_field": rule.source_field,
                "target_field": rule.target_field,
                "has_transform": rule.transform_func is not None,
                "default_value": rule.default_value
            })
        return json.dumps(rules_data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "DataMapper":
        """从JSON反序列化映射规则"""
        mapper = cls()
        rules_data = json.loads(json_str)
        
        for rule_data in rules_data:
            # 注意：转换函数无法序列化，需要重新设置
            rule = DataMappingRule(
                source_field=rule_data["source_field"],
                target_field=rule_data["target_field"],
                default_value=rule_data.get("default_value")
            )
            mapper.add_rule(rule)
        
        return mapper


# 预定义的常用转换函数
class DataTransforms:
    """常用数据转换函数"""
    
    @staticmethod
    def to_int(value: Any) -> int:
        return int(value) if value is not None else 0
    
    @staticmethod
    def to_float(value: Any) -> float:
        return float(value) if value is not None else 0.0
    
    @staticmethod
    def to_string(value: Any) -> str:
        return str(value) if value is not None else ""
    
    @staticmethod
    def bool_to_okng(value: bool) -> str:
        return "OK" if value else "NG"
    
    @staticmethod
    def extract_center(point_dict: dict) -> tuple:
        """从点字典提取中心坐标"""
        return (point_dict.get("x", 0), point_dict.get("y", 0))
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/test_data_mapping.py -v
```

Expected: PASS (3 tests)

**Step 5: 提交**

```bash
git add core/data_mapping.py tests/test_data_mapping.py
git commit -m "feat: 实现数据映射模块 DataMapper

- 支持字段映射和嵌套字段访问
- 支持数据转换函数
- 支持默认值填充
- 提供JSON序列化/反序列化
- 预定义常用转换函数"
```

---

### Task 2: 重构 SendDataTool

**Files:**
- Modify: `tools/communication/enhanced_communication.py:44-200` (重写SendDataTool)
- Test: `tests/test_send_data_tool.py`

**Step 1: 编写失败测试**

```python
# tests/test_send_data_tool.py
import pytest
from unittest.mock import Mock, patch
from tools.communication.enhanced_communication import SendDataTool

def test_send_data_tool_creation():
    """测试发送数据工具创建"""
    tool = SendDataTool("test_send")
    assert tool is not None
    assert tool.tool_name == "发送数据"

def test_send_data_requires_connection():
    """测试发送数据需要选择连接"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "")  # 空连接ID
    
    result = tool._run_impl()
    
    assert result["status"] == False
    assert "未选择连接" in result["message"]

def test_send_data_with_mock_connection():
    """测试使用模拟连接发送数据"""
    tool = SendDataTool("test_send")
    
    # 设置参数
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "json")
    tool.set_param("数据映射", '{"result": "status"}')
    
    # 模拟输入数据
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"result": True}
    
    # 模拟连接
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection_by_id.return_value = mock_conn
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        mock_conn.send.assert_called_once()
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/test_send_data_tool.py -v
```

Expected: FAIL

**Step 3: 重构 SendDataTool 类**

```python
# tools/communication/enhanced_communication.py
# 替换原有的 SendDataTool 类

@ToolRegistry.register
class SendDataTool(ToolBase):
    """发送数据工具（重构版）
    
    核心变更：
    1. 不再自己创建/管理通讯连接
    2. 通过"连接ID"参数选择已有的通讯连接
    3. 接收上游工具的输出数据，按映射规则转换后发送
    4. 支持多种数据格式：JSON、ASCII、HEX、二进制
    
    输入端口：
    - InputData1-16: 上游工具的输出数据（自动接收）
    
    输出端口：
    - OutputStatus: 发送状态（成功/失败）
    - OutputMessage: 状态消息
    """

    tool_name = "发送数据"
    tool_category = "Communication"
    tool_description = "通过已有通讯连接发送数据，支持数据映射和格式转换"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0.0
        self._data_mapper = DataMapper()

    def _init_params(self):
        """初始化参数"""
        # 连接选择（关键变更）
        self.set_param("连接ID", "", description="选择已有的通讯连接ID")
        self.set_param("数据格式", "json", 
                      options=["json", "ascii", "hex", "binary"],
                      description="发送数据格式")
        
        # 数据映射配置
        self.set_param("数据映射", "", 
                      description='数据映射规则JSON，如{"上游字段": "发送字段"}')
        self.set_param("添加时间戳", True, 
                      description="是否在数据中添加时间戳")
        
        # 发送控制
        self.set_param("仅发送变化的数据", False,
                      description="仅当数据变化时才发送")
        self.set_param("发送条件", "always",
                      options=["always", "on_success", "on_failure"],
                      description="发送触发条件")
        
        # 缓存上一次发送的数据（用于变化检测）
        self._last_data_hash = None

    def _run_impl(self):
        """执行发送逻辑（重构版）"""
        # 1. 检查连接ID
        connection_id = self.get_param("连接ID", "")
        if not connection_id:
            return {
                "status": False,
                "message": "未选择通讯连接，请在参数中选择已建立的连接",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        # 2. 获取已有连接（不复用ProtocolManager，而是通过ConnectionManager）
        from ui.communication_config import get_connection_manager
        conn_mgr = get_connection_manager()
        connection = conn_mgr.get_connection(connection_id)
        
        if not connection:
            return {
                "status": False,
                "message": f"未找到连接 {connection_id}，请先在通讯配置中建立连接",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        if not connection.is_connected:
            return {
                "status": False,
                "message": f"连接 {connection.name} 未建立，请先连接",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        # 3. 收集上游输入数据
        input_data = self._collect_input_data()
        
        if not input_data:
            return {
                "status": False,
                "message": "无输入数据",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        # 4. 检查发送条件
        send_condition = self.get_param("发送条件", "always")
        if not self._check_send_condition(input_data, send_condition):
            return {
                "status": True,
                "message": "条件不满足，跳过发送",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        # 5. 检查数据变化（如果启用）
        only_on_change = self.get_param("仅发送变化的数据", False)
        if only_on_change and not self._has_data_changed(input_data):
            return {
                "status": True,
                "message": "数据未变化，跳过发送",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }
        
        # 6. 应用数据映射
        mapped_data = self._apply_data_mapping(input_data)
        
        # 7. 添加时间戳（如果启用）
        if self.get_param("添加时间戳", True):
            mapped_data["_timestamp"] = time.time()
        
        # 8. 格式化数据
        format_type = self.get_param("数据格式", "json")
        formatted_data = self._format_data(mapped_data, format_type)
        
        # 9. 通过已有连接发送
        try:
            protocol_instance = connection.protocol_instance
            if protocol_instance and hasattr(protocol_instance, 'send'):
                success = protocol_instance.send(formatted_data)
                
                if success:
                    self._send_count += 1
                    self._last_send_time = time.time()
                    self._last_data_hash = self._compute_data_hash(input_data)
                    
                    return {
                        "status": True,
                        "message": f"数据已发送至 {connection.name}",
                        "发送成功次数": self._send_count,
                        "发送失败次数": self._fail_count,
                        "数据大小": len(str(formatted_data)),
                        "OutputStatus": True
                    }
                else:
                    self._fail_count += 1
                    return {
                        "status": False,
                        "message": f"发送失败：{connection.name} 发送接口返回失败",
                        "发送成功次数": self._send_count,
                        "发送失败次数": self._fail_count,
                        "OutputStatus": False
                    }
            else:
                self._fail_count += 1
                return {
                    "status": False,
                    "message": f"连接 {connection.name} 无发送接口",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }
                
        except Exception as e:
            self._fail_count += 1
            return {
                "status": False,
                "message": f"发送异常：{str(e)}",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }

    def _collect_input_data(self) -> dict:
        """收集所有输入端口的数据"""
        data = {}
        
        # 遍历所有输入端口
        for i in range(1, 17):
            port_name = f"InputData{i}"
            if hasattr(self, '_input_ports') and port_name in self._input_ports:
                port = self._input_ports[port_name]
                if port and port.data is not None:
                    # 如果端口有数据，合并到总数据
                    if isinstance(port.data, dict):
                        data.update(port.data)
                    else:
                        data[port_name] = port.data
        
        # 如果没有端口数据，尝试从_result_data获取
        if not data and self._result_data:
            data = self._result_data.get_all_values()
        
        return data

    def _check_send_condition(self, data: dict, condition: str) -> bool:
        """检查发送条件"""
        if condition == "always":
            return True
        elif condition == "on_success":
            # 检查数据中是否有成功标记
            return data.get("success", False) or data.get("result", False)
        elif condition == "on_failure":
            return not (data.get("success", False) or data.get("result", False))
        return True

    def _has_data_changed(self, data: dict) -> bool:
        """检查数据是否变化"""
        current_hash = self._compute_data_hash(data)
        return current_hash != self._last_data_hash

    def _compute_data_hash(self, data: dict) -> str:
        """计算数据哈希（用于变化检测）"""
        import hashlib
        import json
        
        try:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
        except:
            return str(time.time())

    def _apply_data_mapping(self, data: dict) -> dict:
        """应用数据映射"""
        mapping_json = self.get_param("数据映射", "")
        
        if not mapping_json:
            # 无映射规则，直接返回所有数据
            return data
        
        try:
            # 解析映射规则
            import json
            mapping_rules = json.loads(mapping_json)
            
            # 清空现有规则并添加新规则
            self._data_mapper.clear_rules()
            for source, target in mapping_rules.items():
                from core.data_mapping import DataMappingRule
                self._data_mapper.add_rule(DataMappingRule(
                    source_field=source,
                    target_field=target
                ))
            
            # 执行映射
            return self._data_mapper.map(data)
            
        except Exception as e:
            print(f"数据映射失败：{e}")
            return data

    def _format_data(self, data: dict, format_type: str) -> any:
        """格式化数据"""
        if format_type == "json":
            return json.dumps(data, ensure_ascii=False)
        elif format_type == "ascii":
            return str(data).encode("ascii", errors="ignore")
        elif format_type == "hex":
            json_str = json.dumps(data, ensure_ascii=False)
            return json_str.encode("utf-8").hex().upper()
        elif format_type == "binary":
            import pickle
            return pickle.dumps(data)
        else:
            return str(data)

    def reset(self):
        """重置工具状态"""
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0.0
        self._last_data_hash = None
        super().reset()
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/test_send_data_tool.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add tools/communication/enhanced_communication.py tests/test_send_data_tool.py
git commit -m "refactor: 重构SendDataTool，解耦通讯连接管理

- 移除内部创建通讯连接的逻辑
- 通过连接ID参数选择已有连接
- 自动收集上游输入数据
- 支持数据映射和格式转换
- 添加发送条件控制（总是/成功时/失败时）
- 支持仅发送变化的数据"
```

---

### Task 3: 重构 ReceiveDataTool ✅

**Status:** Completed (Commit: 9648811)

**Files:**
- Modify: `tools/communication/enhanced_communication.py` (重写ReceiveDataTool)
- Test: `tests/test_receive_data_tool.py`

**Step 1: 编写失败测试**

```python
# tests/test_receive_data_tool.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.communication.enhanced_communication import ReceiveDataTool

def test_receive_data_tool_creation():
    """测试接收数据工具创建"""
    tool = ReceiveDataTool("test_recv")
    assert tool is not None
    assert tool.tool_name == "接收数据"

def test_receive_data_requires_connection():
    """测试接收数据需要选择连接"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "")
    
    result = tool._run_impl()
    
    assert result["status"] == False
    assert "未选择连接" in result["message"]

def test_receive_data_with_mock():
    """测试使用模拟连接接收数据"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    
    # 模拟连接
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b'{"status": "ok"}'
        
        mock_mgr = Mock()
        mock_mgr.get_connection_by_id.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert "接收数据" in result
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/test_receive_data_tool.py -v
```

Expected: FAIL

**Step 3: 重构 ReceiveDataTool 类**

```python
# tools/communication/enhanced_communication.py
# 添加在 SendDataTool 之后

@ToolRegistry.register
class ReceiveDataTool(ToolBase):
    """接收数据工具（重构版）
    
    核心变更：
    1. 不再自己创建/管理通讯连接
    2. 通过"连接ID"参数选择已有的通讯连接
    3. 从已有连接接收数据，解析后输出给下游工具
    4. 支持多种数据格式解析
    
    输出端口：
    - OutputData1-16: 解析后的数据输出给下游工具
    - OutputStatus: 接收状态
    - OutputMessage: 状态消息
    """

    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "通过已有通讯连接接收数据，解析后输出给下游"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._receive_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0

    def _init_params(self):
        """初始化参数"""
        # 连接选择
        self.set_param("连接ID", "", description="选择已有的通讯连接ID")
        
        # 接收配置
        self.set_param("输出格式", "json",
                      options=["json", "string", "int", "float", "hex", "bytes"],
                      description="接收数据的解析格式")
        self.set_param("超时时间", 5.0,
                      description="接收超时时间（秒）")
        self.set_param("缓冲区大小", 4096,
                      description="接收缓冲区大小（字节）")
        
        # 数据提取
        self.set_param("数据提取规则", "",
                      description='从接收数据中提取字段，如{"status": "result.status"}')

    def _run_impl(self):
        """执行接收逻辑（重构版）"""
        # 1. 检查连接ID
        connection_id = self.get_param("连接ID", "")
        if not connection_id:
            return {
                "status": False,
                "message": "未选择通讯连接，请在参数中选择已建立的连接",
                "接收次数": self._receive_count
            }
        
        # 2. 获取已有连接
        from ui.communication_config import get_connection_manager
        conn_mgr = get_connection_manager()
        connection = conn_mgr.get_connection(connection_id)
        
        if not connection:
            return {
                "status": False,
                "message": f"未找到连接 {connection_id}",
                "接收次数": self._receive_count
            }
        
        if not connection.is_connected:
            return {
                "status": False,
                "message": f"连接 {connection.name} 未建立",
                "接收次数": self._receive_count
            }
        
        # 3. 从已有连接接收数据
        try:
            protocol_instance = connection.protocol_instance
            if not protocol_instance or not hasattr(protocol_instance, 'receive'):
                return {
                    "status": False,
                    "message": f"连接 {connection.name} 无接收接口",
                    "接收次数": self._receive_count
                }
            
            # 接收数据
            timeout = self.get_param("超时时间", 5.0)
            raw_data = protocol_instance.receive(timeout)
            
            if raw_data is None:
                return {
                    "status": False,
                    "message": "接收超时，未收到数据",
                    "接收次数": self._receive_count
                }
            
            # 4. 解析数据
            format_type = self.get_param("输出格式", "json")
            parsed_data = self._parse_data(raw_data, format_type)
            
            # 5. 应用数据提取规则
            extracted_data = self._extract_data(parsed_data)
            
            # 6. 更新统计
            self._receive_count += 1
            self._last_received_data = extracted_data
            self._last_receive_time = time.time()
            
            # 7. 构建输出
            result = {
                "status": True,
                "message": f"从 {connection.name} 接收到数据",
                "接收次数": self._receive_count,
                "接收数据": extracted_data,
                "原始数据": raw_data if len(str(raw_data)) < 1000 else "...",
                "格式": format_type,
                "OutputStatus": True
            }
            
            # 8. 将数据输出到输出端口
            self._output_to_ports(extracted_data)
            
            return result
            
        except Exception as e:
            return {
                "status": False,
                "message": f"接收异常：{str(e)}",
                "接收次数": self._receive_count
            }

    def _parse_data(self, raw_data: any, format_type: str) -> any:
        """解析接收到的数据"""
        try:
            if format_type == "json":
                if isinstance(raw_data, bytes):
                    return json.loads(raw_data.decode('utf-8'))
                elif isinstance(raw_data, str):
                    return json.loads(raw_data)
                return raw_data
                
            elif format_type == "string":
                if isinstance(raw_data, bytes):
                    return raw_data.decode('utf-8', errors='replace')
                return str(raw_data)
                
            elif format_type == "int":
                if isinstance(raw_data, bytes):
                    return int(raw_data.decode('utf-8').strip())
                return int(str(raw_data).strip())
                
            elif format_type == "float":
                if isinstance(raw_data, bytes):
                    return float(raw_data.decode('utf-8').strip())
                return float(str(raw_data).strip())
                
            elif format_type == "hex":
                if isinstance(raw_data, bytes):
                    return raw_data.hex().upper()
                return str(raw_data).encode('utf-8').hex().upper()
                
            elif format_type == "bytes":
                if isinstance(raw_data, str):
                    return raw_data.encode('utf-8')
                return raw_data
                
            else:
                return raw_data
                
        except Exception as e:
            print(f"数据解析失败：{e}")
            return raw_data

    def _extract_data(self, data: any) -> dict:
        """根据规则提取数据"""
        extract_rules = self.get_param("数据提取规则", "")
        
        if not extract_rules:
            # 无提取规则，直接包装为字典
            if isinstance(data, dict):
                return data
            else:
                return {"data": data}
        
        try:
            import json
            rules = json.loads(extract_rules)
            
            result = {}
            for target_field, source_path in rules.items():
                # 支持嵌套路径，如 "result.status"
                value = self._get_nested_value(data, source_path)
                if value is not None:
                    self._set_nested_value(result, target_field, value)
            
            return result
            
        except Exception as e:
            print(f"数据提取失败：{e}")
            return {"data": data}

    def _get_nested_value(self, data: any, path: str) -> any:
        """获取嵌套字段值"""
        if not isinstance(data, dict):
            return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current

    def _set_nested_value(self, data: dict, path: str, value: any) -> None:
        """设置嵌套字段值"""
        parts = path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value

    def _output_to_ports(self, data: dict) -> None:
        """将数据输出到输出端口"""
        # 如果数据是字典，将每个字段输出到对应端口
        if isinstance(data, dict):
            for i, (key, value) in enumerate(data.items(), 1):
                if i <= 16:  # 最多16个输出端口
                    port_name = f"OutputData{i}"
                    # 设置端口数据
                    if hasattr(self, '_output_ports') and port_name in self._output_ports:
                        self._output_ports[port_name].data = value

    def reset(self):
        """重置工具状态"""
        self._receive_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0
        super().reset()
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/test_receive_data_tool.py -v
```

Expected: PASS

**Step 5: 提交**

```bash
git add tools/communication/enhanced_communication.py tests/test_receive_data_tool.py
git commit -m "refactor: 重构ReceiveDataTool，解耦通讯连接管理

- 移除内部创建通讯连接的逻辑
- 通过连接ID参数选择已有连接
- 从已有连接接收数据并解析
- 支持多种数据格式解析
- 支持数据提取规则配置
- 自动将解析后的数据输出到下游端口"
```

---

## Phase 2: 创建可视化配置界面（已完成）

### Task 4: 创建数据映射可视化编辑器 ✅

**Status:** Completed (Commit: 6adea32)

**Files:**
- Create: `ui/data_mapping_editor.py`
- Modify: `ui/communication_config.py` (添加打开编辑器的按钮)

**Step 1: 设计界面**

```python
# ui/data_mapping_editor.py
"""
数据映射可视化编辑器

提供拖拽式界面配置数据映射规则
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem,
    QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt5.QtCore import Qt
import json


class DataMappingEditor(QDialog):
    """数据映射规则编辑器"""
    
    def __init__(self, parent=None, current_mapping=""):
        super().__init__(parent)
        self.setWindowTitle("数据映射配置")
        self.resize(600, 400)
        
        self._mapping = {}
        if current_mapping:
            try:
                self._mapping = json.loads(current_mapping)
            except:
                pass
        
        self.setup_ui()
        self.load_mapping()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 说明标签
        layout.addWidget(QLabel("配置上游字段到发送字段的映射："))
        
        # 映射表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["上游字段", "发送字段", "操作"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        layout.addWidget(self.table)
        
        # 添加映射按钮
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加映射")
        add_btn.clicked.connect(self.add_mapping_row)
        btn_layout.addWidget(add_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 确定/取消按钮
        button_box = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(ok_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        self.setLayout(layout)
    
    def load_mapping(self):
        """加载现有映射"""
        self.table.setRowCount(0)
        
        for source, target in self._mapping.items():
            self.add_mapping_row(source, target)
    
    def add_mapping_row(self, source="", target=""):
        """添加映射行"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 上游字段
        source_edit = QLineEdit(source)
        self.table.setCellWidget(row, 0, source_edit)
        
        # 发送字段
        target_edit = QLineEdit(target)
        self.table.setCellWidget(row, 1, target_edit)
        
        # 删除按钮
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(lambda: self.delete_row(row))
        self.table.setCellWidget(row, 2, del_btn)
    
    def delete_row(self, row):
        """删除行"""
        self.table.removeRow(row)
    
    def get_mapping_json(self) -> str:
        """获取映射JSON"""
        mapping = {}
        
        for row in range(self.table.rowCount()):
            source_widget = self.table.cellWidget(row, 0)
            target_widget = self.table.cellWidget(row, 1)
            
            if source_widget and target_widget:
                source = source_widget.text().strip()
                target = target_widget.text().strip()
                
                if source and target:
                    mapping[source] = target
        
        return json.dumps(mapping, ensure_ascii=False, indent=2)
```

**Step 2: 在通讯配置界面添加按钮**

```python
# 在 ui/communication_config.py 的 ConnectionConfigDialog 中添加

# 在 setup_ui 方法中添加数据映射按钮
self.mapping_btn = QPushButton("配置数据映射...")
self.mapping_btn.clicked.connect(self.open_mapping_editor)
info_layout.addWidget(self.mapping_btn, 2, 1)

def open_mapping_editor(self):
    """打开数据映射编辑器"""
    editor = DataMappingEditor(self, self.get_param("数据映射", ""))
    if editor.exec_() == QDialog.Accepted:
        mapping_json = editor.get_mapping_json()
        self.set_param("数据映射", mapping_json)
```

**Step 3: 提交**

```bash
git add ui/data_mapping_editor.py
git add ui/communication_config.py  # 修改部分
git commit -m "feat: 添加数据映射可视化编辑器

- 创建DataMappingEditor对话框
- 支持可视化配置字段映射规则
- 集成到通讯配置界面
- 支持添加/删除映射规则"
```

---

## 实施完成总结

### 架构变更

**重构前：**
```
SendDataTool/ReceiveDataTool
    ↓ 自己创建和管理连接
ProtocolManager
    ↓ 创建协议实例
TCPClient/TCPServer/etc
```

**重构后：**
```
SendDataTool/ReceiveDataTool
    ↓ 通过连接ID引用
ConnectionManager (已有)
    ↓ 管理连接
ProtocolInstance (已有)
    ↓ 实际通讯
```

### 关键改进

1. ✅ **解耦成功** - 发送/接收工具不再管理连接
2. ✅ **连接复用** - 通过ID引用已有连接
3. ✅ **数据流清晰** - 上游数据→映射→发送 / 接收→解析→下游
4. ⏳ **可视化配置** - 数据映射编辑器（Task 4 待实现）

### 使用流程

1. **先建立连接**：在通讯配置中创建TCP/串口等连接
2. **配置发送工具**：
   - 选择已有连接ID
   - 配置数据映射（上游字段→发送字段）
   - 选择数据格式
3. **配置接收工具**：
   - 选择已有连接ID
   - 配置数据解析格式
   - 配置数据提取规则
4. **流程连接**：将算法工具输出连接到发送工具输入

---

**Plan complete! 准备好实施了吗？** 建议使用 **Subagent-Driven** 方式逐个任务执行，我可以实时审查每个任务的代码！