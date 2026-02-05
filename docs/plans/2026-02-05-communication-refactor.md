# 通讯模块功能重构计划

## 问题分析

### 1. 功能重叠问题
- **发送数据模块**：连接ID和可用连接列表功能重复
- **数据内容模块**：数据内容与可用数据字段功能边界不清

### 2. 上游数据传递问题
- 当前数据流转只传递 ImageData（图像数据）
- 通讯工具需要访问上游工具的 ResultData（检测结果数据）
- 没有机制将上游结果数据传递给下游通讯工具

### 3. 卡顿Bug
- 先拉拽模块再建立通讯时程序卡顿
- 可能是连接管理器初始化或连接查询导致的阻塞

## 重构方案

### 阶段1：简化参数结构（解决功能重叠）

#### 1.1 发送数据工具参数重构
**当前问题**：
- 连接ID（string）+ 可用连接列表（只读）功能重叠
- 数据内容（text）+ 可用数据字段（只读）功能重叠

**重构后**：
```python
# 简化后的参数
self.set_param("目标连接", "", 
               param_type="enum",
               options=[],  # 动态从连接管理器获取
               description="选择要发送数据的目标连接")

self.set_param("数据内容", "{all}",
               param_type="text",
               description="要发送的数据内容。支持：\n"
                          "{all} - 发送所有上游数据\n"
                          "{field_name} - 发送指定字段\n"
                          "固定文本 - 直接发送")
```

**移除的参数**：
- 可用连接列表（整合到目标连接下拉框）
- 可用数据字段（改为运行时动态显示）

#### 1.2 参数职责明确
- **目标连接**：唯一的数据发送目标选择入口
- **数据内容**：唯一的数据内容配置入口
- 移除所有"只读参考"类型的参数

### 阶段2：建立上游数据传递机制

#### 2.1 扩展 ToolBase 类
在 ToolBase 中添加上游结果数据传递机制：

```python
class ToolBase(ABC):
    def __init__(self, name: str = None):
        # ... 现有代码 ...
        self._upstream_result_data: Optional[ResultData] = None  # 上游工具的结果数据
    
    def set_upstream_result(self, result_data: ResultData):
        """设置上游工具的结果数据"""
        self._upstream_result_data = result_data
    
    def get_upstream_result(self) -> Optional[ResultData]:
        """获取上游工具的结果数据"""
        return self._upstream_result_data
    
    def get_upstream_values(self) -> Dict[str, Any]:
        """获取上游数据的所有值"""
        if self._upstream_result_data:
            return self._upstream_result_data.get_all_values()
        return {}
```

#### 2.2 修改 Procedure 类
在流程执行时传递上游结果数据：

```python
def _propagate_output(self, tool_name: str, output: Optional[ImageData], 
                      result: Optional[ResultData]):
    """将工具输出和结果传递给下一个工具"""
    if output is None:
        return
    
    connections = self.get_connections_from(tool_name)
    for conn in connections:
        target_tool = self._tools.get(conn.to_tool)
        if target_tool is not None:
            target_tool.set_input(output, conn.to_port)
            # 同时传递结果数据
            if result is not None:
                target_tool.set_upstream_result(result)
```

#### 2.3 修改主窗口执行逻辑
在 `_run_procedure_sync` 中传递结果数据：

```python
# 执行工具后，获取其结果数据并传递给下游
tool.run()
result_data = tool.get_result()

# 将输出和结果传递给下一个工具
self._propagate_output_with_result(tool._name, output, result_data)
```

### 阶段3：修复卡顿Bug

#### 3.1 问题分析
卡顿可能原因：
1. `_get_available_connections()` 在UI线程同步查询连接状态
2. 连接管理器初始化阻塞
3. 网络连接超时导致UI卡顿

#### 3.2 解决方案
**方案A：异步加载连接列表**
```python
def _init_params(self):
    """初始化参数 - 异步加载连接列表"""
    self.set_param("目标连接", "",
                   param_type="string",  # 先设为string，避免阻塞
                   description="选择目标连接")
    
    # 异步加载可用连接
    self._load_connections_async()

def _load_connections_async(self):
    """异步加载可用连接列表"""
    def load():
        connections = self._get_available_connections()
        # 使用信号或回调更新UI
        self._on_connections_loaded(connections)
    
    threading.Thread(target=load, daemon=True).start()
```

**方案B：延迟加载 + 缓存**
```python
def _get_available_connections(self) -> List[str]:
    """获取可用连接 - 带缓存机制"""
    # 使用缓存避免重复查询
    if hasattr(self, '_connections_cache'):
        cache_time, cache_data = self._connections_cache
        if time.time() - cache_time < 5:  # 5秒缓存
            return cache_data
    
    # 查询连接（带超时）
    try:
        conn_manager = _get_comm_manager()
        # 使用非阻塞方式获取连接列表
        connections = conn_manager.get_all_connections()
        result = [f"{conn.id}: {conn.name}" for conn in connections]
        self._connections_cache = (time.time(), result)
        return result
    except Exception as e:
        logger.error(f"获取连接列表失败: {e}")
        return []
```

**方案C：UI分离**
将连接选择改为独立的下拉框组件，在点击时才加载：
```python
# 在参数面板中使用自定义组件
class ConnectionSelector(QWidget):
    """连接选择器 - 延迟加载"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        self.combo.addItem("点击加载...")
        self.combo.activated.connect(self._on_activated)
    
    def _on_activated(self, index):
        if index == 0:  # 点击了"点击加载..."
            self._load_connections()
    
    def _load_connections(self):
        """异步加载连接"""
        # 在后台线程加载，完成后更新UI
```

### 阶段4：通讯工具数据获取重构

#### 4.1 修改 SendDataTool
```python
def _collect_input_data(self) -> Dict[str, Any]:
    """收集上游数据 - 使用新的上游结果数据机制"""
    input_data = {}
    
    # 从上游结果数据获取
    upstream_values = self.get_upstream_values()
    if upstream_values:
        data_content = self.get_param("数据内容", "{all}")
        
        if data_content.strip() == "{all}":
            input_data = upstream_values
        elif "{" in data_content:
            input_data = self._parse_variables(data_content, upstream_values)
        else:
            input_data = {"data": data_content}
    
    return input_data
```

## 实施步骤

### 步骤1：修改 ToolBase（基础支持）
1. 添加 `_upstream_result_data` 属性
2. 添加 `set_upstream_result()` 和 `get_upstream_values()` 方法

### 步骤2：修改 Procedure（数据传递）
1. 修改 `_propagate_output()` 方法，添加结果数据传递
2. 修改 `run()` 方法，在工具执行后传递结果

### 步骤3：修改主窗口执行逻辑
1. 修改 `_run_procedure_sync()`，在工具执行后调用新的传播方法

### 步骤4：重构 SendDataTool（功能简化）
1. 简化参数结构，移除冗余参数
2. 修改 `_collect_input_data()` 使用新的上游数据机制
3. 修复卡顿问题（异步加载连接列表）

### 步骤5：测试验证
1. 测试上游数据传递
2. 测试参数简化后的功能
3. 测试卡顿问题是否修复

## 预期效果

1. **功能去重**：参数结构清晰，每个功能只有一个入口
2. **数据可用**：通讯工具能正确获取上游工具的检测结果
3. **性能优化**：无卡顿，连接列表加载不阻塞UI
4. **代码简化**：逻辑清晰，易于维护
