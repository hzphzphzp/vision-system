# 通讯模块修复文档 - 2026-02-05

## 概述

本文档详细记录了2026年2月5日对通讯模块（发送数据/接收数据工具）的修复内容，包括问题分析、解决方案和代码变更。

## 修复内容汇总

### 1. 属性面板参数保存问题

#### 问题描述
用户在属性面板中选择"目标连接"和"数据内容"后，参数没有被正确保存，导致工具运行时提示"未选择连接"。

#### 错误日志
```
ERROR - 未选择连接
ERROR - 可用参数: ['目标连接', '__type_目标连接', '__desc_目标连接', ...]
目标连接: '' (类型: str)
```

#### 根本原因分析

1. **QComboBox信号问题**: 使用`currentTextChanged`信号发送的是显示文本，而不是实际值(userData)
2. **DataContentSelector信号未连接**: `data_selected`信号没有连接到属性面板的参数变更处理器
3. **空值触发信号**: 设置空字符串时触发不必要的信号发射

#### 解决方案

**文件**: `ui/property_panel.py`

##### 1.1 修改QComboBox信号连接
```python
# 修改前
elif isinstance(widget, QComboBox):
    widget.currentTextChanged.connect(
        partial(self._on_parameter_changed, param_name)
    )

# 修改后
elif isinstance(widget, QComboBox):
    # 使用lambda获取当前选中的userData而不是显示文本
    widget.currentIndexChanged.connect(
        lambda index, w=widget, p=param_name: self._on_combobox_changed(p, w)
    )
    # 备用信号：当用户手动选择时触发
    widget.activated.connect(
        lambda index, w=widget, p=param_name: self._on_combobox_activated(p, w)
    )
```

##### 1.2 添加信号处理函数
```python
def _on_combobox_changed(self, param_name: str, combobox: QComboBox):
    """下拉框选项变更处理（currentIndexChanged信号）"""
    current_data = combobox.currentData()
    current_text = combobox.currentText()
    current_index = combobox.currentIndex()
    self._logger.info(f"【属性面板】下拉框变更(currentIndexChanged): {param_name}, index={current_index}, currentText='{current_text}', currentData='{current_data}'")
    
    # 使用userData作为参数值（如果存在），否则使用显示文本
    value = current_data if current_data is not None else current_text
    self._on_parameter_changed(param_name, value)

def _on_combobox_activated(self, param_name: str, combobox: QComboBox):
    """下拉框选项激活处理（activated信号）- 当用户手动选择时触发"""
    current_data = combobox.currentData()
    current_text = combobox.currentText()
    current_index = combobox.currentIndex()
    self._logger.info(f"【属性面板】下拉框激活(activated): {param_name}, index={current_index}, currentText='{current_text}', currentData='{current_data}'")
    
    # 使用userData作为参数值（如果存在），否则使用显示文本
    value = current_data if current_data is not None else current_text
    self._on_parameter_changed(param_name, value)
```

##### 1.3 连接DataContentSelector信号
```python
else:
    # 检查是否是 DataContentSelector（使用 duck typing）
    if hasattr(widget, 'data_selected') and hasattr(widget, 'text_edit'):
        # 数据内容选择器连接信号
        widget.data_selected.connect(
            partial(self._on_parameter_changed, param_name)
        )
        # 同时连接文本框的 textChanged 信号作为备用
        widget.text_edit.textChanged.connect(
            partial(self._on_parameter_changed, param_name)
        )
        self._logger.info(f"【属性面板】已连接 DataContentSelector 信号: {param_name}")
```

##### 1.4 避免空值设置
```python
# 修改前
if value is not None:
    # 设置当前值

# 修改后
if value is not None and str(value).strip():
    # 设置当前值
else:
    print(f"【属性面板】值为空，不设置当前选中项")
```

---

### 2. 数据发送逻辑优化

#### 问题描述
用户选择特定字段（如`Width`）时，发送的是整个上游数据字典，而不是选中的字段值。

#### 接收到的数据
```python
{'data': {'OutputImage': ImageData(...), 'Width': 3072, 'Height': 2048, 'Channels': 3}}
```

#### 期望的数据
```python
{'Width': 3072}
```

#### 根本原因分析
`_collect_input_data()`方法直接将整个`upstream_values`字典作为数据发送，没有根据用户选择的字段进行提取。

#### 解决方案

**文件**: `tools/communication/enhanced_communication.py`

##### 2.1 修改数据收集逻辑
```python
# 修改前
if upstream_values:
    # 上游数据已经是解析后的值，直接使用
    input_data = {"data": upstream_values}

# 修改后
if upstream_values:
    # 提取特定字段的值
    if field_name in upstream_values:
        field_value = upstream_values[field_name]
        input_data = {field_name: field_value}
        self._logger.info(f"提取字段 '{field_name}' 的值: {field_value}")
    else:
        # 字段不存在，发送所有数据并提示
        self._logger.warning(f"字段 '{field_name}' 不在上游数据中，发送所有数据")
        input_data = {"data": upstream_values}
```

---

### 3. 连接查找逻辑增强

#### 问题描述
连接ID格式为`device_id: display_name`（如`conn_1770271774: [conn_1770271774] TCP客户端 - TCP客户端_1 (127.0.0.1:8080)`），需要正确解析和查找。

#### 解决方案

**文件**: `tools/communication/enhanced_communication.py`

##### 3.1 增强_get_available_connections方法
```python
def _get_available_connections(self) -> List[str]:
    """获取可用的连接列表（带缓存机制，避免卡顿）"""
    # ... 缓存检查代码 ...
    
    try:
        conn_manager = _get_comm_manager()
        result = []
        
        # 方法1：使用get_available_connections（推荐）
        if hasattr(conn_manager, 'get_available_connections'):
            connections = conn_manager.get_available_connections()
            self._logger.debug(f"获取到 {len(connections)} 个可用连接")
            for conn in connections:
                display_name = conn.get("display_name", "")
                device_id = conn.get("device_id", "")
                name = conn.get("name", "")
                protocol = conn.get("protocol_type", "Unknown")
                
                self._logger.debug(f"连接信息: device_id={device_id}, name={name}, display_name={display_name}")
                
                # 确保 display_name 不为空
                if not display_name:
                    display_name = f"[{protocol}] {name}"
                
                # 确保 device_id 不为空
                if not device_id:
                    device_id = name
                
                result.append(f"{device_id}: {display_name}")
        
        # 更新缓存
        setattr(self, cache_attr, (time.time(), result))
        return result
        
    except Exception as e:
        # 出错时返回缓存数据（如果可用）
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)[1]
        return []
```

##### 3.2 增强_get_connection_by_display_name方法
```python
def _get_connection_by_display_name(self, display_name: str) -> Optional[Any]:
    """根据显示名称获取连接"""
    try:
        conn_manager = _get_comm_manager()
        connections = conn_manager.get_available_connections()
        
        self._logger.debug(f"尝试根据显示名称查找连接: {display_name}")
        self._logger.debug(f"可用连接数: {len(connections)}")
        
        # 尝试直接匹配 display_name
        for conn in connections:
            conn_display_name = conn.get("display_name", "")
            self._logger.debug(f"检查连接: display_name={conn_display_name}")
            if conn_display_name == display_name:
                device_id = conn.get("device_id", conn.get("name", ""))
                self._logger.debug(f"找到匹配，使用 device_id: {device_id}")
                return conn_manager.get_connection(device_id)
        
        # 尝试解析 device_id: display_name 格式
        if ": " in display_name:
            parts = display_name.split(": ", 1)
            if len(parts) == 2:
                device_id = parts[0]
                self._logger.debug(f"尝试使用解析的 device_id 查找: {device_id}")
                # 使用device_id查找
                for conn in connections:
                    if conn.get("device_id") == device_id:
                        self._logger.debug(f"找到匹配的 device_id: {device_id}")
                        return conn_manager.get_connection(device_id)
        
        self._logger.warning(f"未找到匹配的连接: {display_name}")
        return None
    except Exception as e:
        self._logger.error(f"根据显示名称获取连接失败: {e}")
        import traceback
        self._logger.error(traceback.format_exc())
        return None
```

---

### 4. 接收数据工具修复

#### 4.1 输入检查问题

**问题描述**：接收数据工具执行时提示"输入数据无效"错误。

**错误日志**：
```
ErrorManager - ERROR - [ERROR] 工具执行错误: 接收数据_1: [400] 输入数据无效
```

**根本原因**：`ReceiveDataTool`继承了`ToolBase`的默认`_check_input()`方法，该方法检查`_input_data`（输入图像数据）是否存在且有效。但接收数据工具不需要输入图像数据，它从外部通讯连接接收数据。

**解决方案**：

**文件**: `tools/communication/enhanced_communication.py`

```python
def _check_input(self) -> bool:
    """检查输入数据有效性
    
    接收数据工具不需要输入图像数据，
    它从外部连接接收数据，所以总是返回True
    """
    return True
```

#### 4.2 连接列表格式统一

**问题描述**：接收数据工具使用`display_name`格式，而发送数据工具使用`device_id: display_name`格式，导致连接查找失败。

**错误日志**：
```
ERROR - 未找到连接: [conn_1770273318] TCP客户端 - TCP客户端_1 (127.0.0.1:8080)
```

**解决方案**：

统一两个工具的连接列表格式为`device_id: display_name`：

```python
def _get_available_connections(self) -> List[str]:
    """获取可用的连接列表（统一格式：device_id: display_name）"""
    try:
        conn_manager = _get_comm_manager()
        connections = conn_manager.get_available_connections()
        result = []
        for conn in connections:
            if conn.get("connected"):
                device_id = conn.get("device_id", conn.get("name", ""))
                display_name = conn.get("display_name", "")
                if device_id and display_name:
                    result.append(f"{device_id}: {display_name}")
                elif display_name:
                    result.append(display_name)
        self._logger.debug(f"接收数据工具获取到 {len(result)} 个可用连接")
        return result
    except Exception as e:
        self._logger.error(f"获取可用连接列表失败: {e}")
        return []
```

增强`_get_connection_by_display_name()`支持多种格式：

```python
def _get_connection_by_display_name(self, display_name: str) -> Optional[Any]:
    """根据显示名称获取连接
    
    支持多种格式：
    1. 完整的显示格式：device_id: display_name
    2. 只有display_name
    3. 方括号格式：[device_id] display_name
    """
    try:
        conn_manager = _get_comm_manager()
        connections = conn_manager.get_available_connections()
        
        self._logger.debug(f"尝试根据显示名称查找连接: {display_name}")
        
        # 尝试直接匹配 display_name
        for conn in connections:
            conn_display_name = conn.get("display_name", "")
            if conn_display_name == display_name:
                device_id = conn.get("device_id", conn.get("name", ""))
                self._logger.debug(f"找到匹配，使用 device_id: {device_id}")
                return conn_manager.get_connection(device_id)
        
        # 尝试解析 device_id: display_name 格式
        if ": " in display_name:
            parts = display_name.split(": ", 1)
            if len(parts) == 2:
                device_id = parts[0]
                self._logger.debug(f"尝试使用解析的 device_id 查找: {device_id}")
                for conn in connections:
                    if conn.get("device_id") == device_id:
                        self._logger.debug(f"找到匹配的 device_id: {device_id}")
                        return conn_manager.get_connection(device_id)
        
        # 尝试解析 [device_id] display_name 格式
        if display_name.startswith("[") and "]" in display_name:
            parts = display_name.split("]", 1)
            if len(parts) == 2:
                device_id = parts[0][1:]  # 去掉开头的 [
                self._logger.debug(f"尝试使用方括号格式的 device_id 查找: {device_id}")
                for conn in connections:
                    if conn.get("device_id") == device_id:
                        self._logger.debug(f"找到匹配的 device_id: {device_id}")
                        return conn_manager.get_connection(device_id)
        
        self._logger.warning(f"未找到匹配的连接: {display_name}")
        return None
    except Exception as e:
        self._logger.error(f"根据显示名称获取连接失败: {e}")
        import traceback
        self._logger.error(traceback.format_exc())
        return None
```

---

### 5. 调试日志增强

#### 5.1 属性面板日志
- 创建ENUM控件时记录参数名、值、选项数量
- 添加选项时记录display_text和option
- 设置当前值时记录findData结果
- 参数变更时记录旧值和新值

#### 5.2 工具执行日志
- 记录所有参数及其值
- 记录目标连接参数的检查过程
- 记录连接查找过程
- 记录数据收集和发送过程

#### 5.3 主窗口日志
- 记录属性变更事件
- 记录工具参数更新
- 记录流程执行过程

---

## 测试验证

### 测试步骤
1. 添加"发送数据"工具到流程
2. 在属性面板中选择"目标连接"下拉框选项
3. 点击"数据内容"的"选择..."按钮，选择特定字段（如`Width`）
4. 运行流程
5. 验证接收到的数据

### 验证日志
```
【属性面板】下拉框激活(activated): 目标连接, index=0, currentText='conn_1770271774: [...]', currentData='conn_1770271774: [...]'
【属性面板】参数变更: 目标连接 = 'conn_1770271774: [...]' (类型: str)
【set_param】设置参数: 发送数据_1.目标连接 = 'conn_1770271774: [...]' (旧值: '')
目标连接: 'conn_1770271774: [...]' (类型: str)
数据内容: '图像读取器_图像读取器_1.Width' (类型: str)
提取字段 'Width' 的值: 3072
发送结果: True
```

### 接收到的数据
```python
{'Width': 3072}
```

---

## 文件变更清单

| 文件路径 | 变更类型 | 变更内容 |
|---------|---------|---------|
| `ui/property_panel.py` | 修改 | 修复QComboBox信号连接，添加DataContentSelector信号连接，增强日志 |
| `tools/communication/enhanced_communication.py` | 修改 | 优化数据收集逻辑，增强连接查找，添加详细日志，修复接收数据工具输入检查，统一连接列表格式 |
| `core/tool_base.py` | 修改 | 增强set_param日志 |

---

## 经验教训

### 1. 信号连接注意事项
- `QComboBox`的`currentTextChanged`发送显示文本，`currentIndexChanged`配合`currentData()`获取实际值
- 自定义控件（如`DataContentSelector`）需要显式连接信号
- 使用`activated`信号作为用户手动选择的备用信号

### 2. 调试技巧
- 在静态方法中使用`print()`代替`self._logger`
- 在信号连接的每个环节添加日志：创建→连接→触发→处理
- 使用`【标记】`格式便于日志过滤

### 3. 参数持久化验证
- 工具创建时记录参数初始值
- 用户操作后记录参数变更
- 工具执行前记录参数读取
- 对比三个时间点的参数值

### 4. 工具输入检查
- 不需要输入图像数据的工具（如通讯工具）必须重写`_check_input()`方法
- 默认返回`True`表示不需要输入数据检查
- 示例：接收数据工具、发送数据工具（如果不需要输入图像）

### 5. 连接列表格式统一
- 所有通讯工具使用统一的连接标识符格式：`device_id: display_name`
- 支持多种格式解析：
  - `device_id: display_name`（标准格式）
  - `display_name`（仅显示名称）
  - `[device_id] display_name`（方括号格式）
- 在`_get_connection_by_display_name()`中实现多种格式支持

---

## 附录：增强结果面板 (EnhancedResultPanel)

### 概述

`ui/enhanced_result_panel.py` 提供了增强的结果可视化功能，支持多种结果类型的展示、数据导出和可视化渲染。

### 核心类

#### 1. ResultCategory (枚举)
```python
class ResultCategory(Enum):
    BARCODE = "barcode"          # 条码识别
    QRCODE = "qrcode"            # 二维码识别
    MATCH = "match"              # 模板匹配
    CALIPER = "caliper"          # 卡尺测量
    BLOB = "blob"                # Blob分析
    SHAPE = "shape"              # 形状分析
    OCR = "ocr"                  # OCR识别
    CLASSIFICATION = "classification"  # 图像分类
    DEFECT = "defect"            # 缺陷检测
    CUSTOM = "custom"            # 自定义类型
    UNKNOWN = "unknown"          # 未知类型
```

#### 2. EnhancedResultPanel (主面板)

**主要功能**:
- **结果列表**: 树形结构展示所有工具执行结果
- **分类过滤**: 按结果类型过滤（码识别、目标检测、匹配分析等）
- **搜索功能**: 按工具名称搜索
- **实时更新**: 相同模块结果自动更新，不重复显示
- **数据导出**: 支持CSV、JSON格式导出

**核心方法**:
```python
def add_result(self, result_data: ResultData, category: str = "")
"""添加结果（优化版：相同模块共用一个结果面板）"""

def clear_results(self)
"""清空所有结果"""

def _update_result_list(self)
"""更新结果列表显示"""

def _show_export_dialog(self)
"""显示导出对话框"""
```

#### 3. ResultDetailWidget (结果详情)

**功能**: 显示单个结果的详细信息

**支持的结果类型**:
- **条码/二维码**: 显示码内容、类型、位置、质量分数
- **目标检测**: 显示检测到的目标、置信度、边界框
- **模板匹配**: 显示匹配分数、位置、角度
- **卡尺测量**: 显示测量值、单位、公差
- **Blob分析**: 显示Blob数量、面积、中心点
- **OCR**: 显示识别文本、置信度

#### 4. DataSelectorWidget (数据选择器)

**功能**: 动态选择要查看的数据类型

**特性**:
- 自动检测可用数据类型（图像、数值、字符串等）
- 支持多模块数据连接
- 实时更新数据列表

#### 5. ResultVisualizationWidget (结果可视化)

**功能**: 图形化展示检测结果

**可视化元素**:
- 矩形边界框
- 中心点标记
- 标签文字
- 置信度/分数显示

### 使用示例

```python
from ui.enhanced_result_panel import EnhancedResultPanel
from data.result_data import ResultData

# 创建结果面板
result_panel = EnhancedResultPanel()

# 添加结果
result_data = ResultData(
    tool_name="条码识别_1",
    status=True,
    values={
        "codes": [
            {"data": "123456789", "type": "CODE128", "x": 100, "y": 200}
        ],
        "count": 1
    }
)
result_panel.add_result(result_data, category="barcode")

# 清空结果
result_panel.clear_results()
```

### 集成到主界面

在 `main_window.py` 中集成:

```python
from ui.enhanced_result_panel import EnhancedResultPanel

# 创建结果面板
self.result_panel = EnhancedResultPanel()

# 连接信号
self.result_panel.result_selected.connect(self._on_result_selected)
self.result_panel.data_connection_requested.connect(self._on_data_connection_requested)

# 添加到布局
right_layout.addWidget(self.result_panel)
```

### 特性说明

1. **智能结果分类**: 根据工具名称自动推断结果类别
   - 包含"YOLO" → detection
   - 包含"条码"/"二维码"/"读码" → code
   - 包含"匹配" → match
   - 包含"测量"/"卡尺" → caliper
   - 包含"Blob" → blob
   - 包含"OCR" → ocr

2. **结果去重**: 相同模块的新结果会替换旧结果，避免列表无限增长

3. **性能优化**: 限制最大结果数量为500条，防止内存溢出

4. **数据导出**: 支持CSV和JSON格式，便于后续分析

---

## 相关文档

- [AGENTS.md](../AGENTS.md) - 包含详细的问题分析和解决方案
- [README.md](../README.md) - 更新日志和功能说明

---

**文档版本**: 1.2  
**创建日期**: 2026-02-05  
**更新日期**: 2026-02-05  
**作者**: AI Assistant  
**审核状态**: 已完成  
**变更记录**: 
- v1.0: 初始版本，记录发送数据工具修复
- v1.1: 添加接收数据工具修复内容，统一连接列表格式
- v1.2: 添加增强结果面板文档
