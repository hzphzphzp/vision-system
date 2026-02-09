# 通讯配置与结果面板修复记录

**日期**: 2026-02-09  
**作者**: Vision System Team  
**版本**: 1.0

---

## 概述

本文档记录了2026-02-09期间修复的通讯配置、结果面板、发送数据等相关问题。这些问题影响了系统的稳定性和用户体验。

---

## 修复问题清单

### 1. 通讯配置单例模式问题

#### 问题描述
发送数据工具无法找到通讯连接，或找到错误的连接。

#### 错误现象
- 发送数据工具执行时提示"未找到连接"
- 或者连接到错误的连接实例
- 日志显示连接已加载，但工具无法找到

#### 根本原因
`ConnectionManager`虽然使用了`__new__`方法实现单例模式，但`__init__`方法每次获取实例时都会被调用，导致`self._connections = {}`清空了所有连接数据。

#### 修复方案
1. 在`ConnectionManager.__init__`中添加`_initialized`标志，只在第一次初始化时创建属性
2. `CommunicationConfigWidget`使用`get_connection_manager()`获取单例，而不是直接创建`ConnectionManager()`实例
3. 简化`get_connection_manager()`函数，直接返回`ConnectionManager()`，让`__new__`方法处理单例逻辑

#### 代码变更
```python
# ui/communication_config.py
class ConnectionManager:
    def __init__(self):
        # 只在第一次初始化时创建属性，避免单例重复初始化清空数据
        if not hasattr(self, '_initialized'):
            self._connections: Dict[str, ProtocolConnection] = {}
            self._lock = threading.Lock()
            self._status_callback: Optional[Callable] = None
            self._storage = ConnectionStorage()
            self._pending_workers: Dict[str, ProtocolCreateWorker] = {}
            self._initialized = True
```

---

### 2. 通讯配置编辑卡顿问题

#### 问题描述
编辑通讯配置时程序卡顿无响应。

#### 错误现象
- 添加或编辑连接后，程序界面卡顿
- 显示"提示"对话框后，需要手动关闭才能继续操作
- 后台线程已完成连接，但对话框仍在显示

#### 根本原因
1. `QMessageBox.information`是模态对话框，会阻塞事件循环直到用户关闭
2. 对话框显示"正在后台建立连接..."，但连接实际上已经完成
3. 频繁的状态回调导致UI频繁刷新

#### 修复方案
1. 移除阻塞的`QMessageBox.information`对话框，改为更新状态栏显示连接状态
2. 使用`QTimer`延迟刷新UI，合并多次状态变化，避免频繁更新
3. 优化`on_connection_status_changed`回调，使用单次定时器延迟100ms刷新

#### 代码变更
```python
# ui/communication_config.py
def on_connection_status_changed(self, connection):
    """连接状态变化回调（使用延迟刷新避免频繁更新）"""
    # 使用单次定时器延迟刷新，避免频繁更新UI导致卡顿
    if not hasattr(self, '_refresh_timer'):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh_connections)
    
    # 如果定时器已经在运行，停止并重新启动
    if self._refresh_timer.isActive():
        self._refresh_timer.stop()
    
    # 延迟100ms刷新，合并多次状态变化
    self._refresh_timer.start(100)
```

---

### 3. 图像拼接结果不显示问题

#### 问题描述
图像拼接工具执行后结果面板不显示结果。

#### 错误现象
- 图像拼接工具执行成功
- 日志显示"拼接成功"
- 但结果面板没有显示图像拼接的结果

#### 根本原因
图像拼接工具的`process`方法返回`ResultData`对象，但没有保存到`_result_data`。主窗口通过`tool.get_result()`获取结果数据，但`get_result()`返回`self._result_data`，而`_result_data`没有被设置。

#### 修复方案
在`_run_impl`方法中，将`process`返回的`ResultData`保存到`self._result_data`：

```python
# tools/vision/image_stitching.py
def _run_impl(self):
    # ... 前面的代码 ...
    
    # 调用process方法进行多图像拼接
    process_result = self.process(self._input_data_list)
    
    # 保存结果数据到_result_data，以便结果面板可以显示
    self._result_data = process_result
    if not self._result_data.tool_name:
        self._result_data.tool_name = self._name
    
    # ... 后面的代码 ...
```

---

### 4. 灰度匹配结果显示问题

#### 问题描述
灰度匹配结果显示"匹配失败：相似度=0.00%"，但实际匹配成功。

#### 错误现象
- 灰度匹配工具执行成功，日志显示匹配成功
- 结果面板显示"匹配失败：相似度=0.00%"
- 发送数据工具可以获取到正确的匹配结果

#### 根本原因
1. 结果面板期望的字段名（`matched`、`score`、`center`、`match_score`）与灰度匹配工具设置的字段名（`best_score`、`best_x`、`best_y`）不一致
2. 灰度匹配工具没有设置`result_category`，导致结果面板无法正确识别结果类型，调用`_show_general_result`而不是`_show_match_result`

#### 修复方案
1. 在灰度匹配工具中添加结果面板期望的字段
2. 设置`result_category = "match"`，使结果面板调用`_show_match_result`方法

#### 代码变更
```python
# tools/vision/template_match.py
# 保存结果
self._result_data = ResultData()
self._result_data.tool_name = self._name
self._result_data.result_category = "match"  # 设置结果类别

# 保存第一个匹配位置
if filtered_locations:
    best_match = filtered_locations[0]
    self._result_data.set_value("best_x", best_match[0])
    self._result_data.set_value("best_y", best_match[1])
    self._result_data.set_value("best_score", best_match[2])
    
    # 设置结果面板期望的字段
    self._result_data.set_value("matched", True)
    self._result_data.set_value("score", best_match[2])
    self._result_data.set_value("center", {"x": best_match[0], "y": best_match[1]})
    self._result_data.set_value("match_score", best_match[2])
```

---

### 5. 结果面板显示不完整问题

#### 问题描述
结果面板只显示2条结果，但算法编辑器有4个模块。

#### 错误现象
- 算法编辑器中有4个模块（2个图像读取器、1个图像拼接、1个发送数据）
- 结果面板只显示2条结果（发送数据和图像读取器）
- 两个图像读取器的结果被合并了

#### 根本原因
`EnhancedResultPanel.add_result`方法使用`tool_name`（工具类型名称，如"图像读取器"）来区分结果，导致相同类型的工具（如两个"图像读取器"）的结果被合并。

#### 修复方案
在`main_window.py`中，将`result_data.tool_name`设置为`tool.name`（工具实例名称，如"图像读取器_1"）而不是`tool.tool_name`：

```python
# ui/main_window.py
# 将结果添加到结果面板
if result_data:
    # 确保结果数据包含工具名称（使用实例名称以区分相同类型的不同工具）
    if not result_data.tool_name:
        result_data.tool_name = tool.name  # 使用 tool.name 而不是 tool.tool_name
    self.result_dock.add_result(result_data)
```

---

### 6. 数据选择器缺少图像结果问题

#### 问题描述
数据选择器中缺少图像拼接工具的图像结果。

#### 错误现象
- 数据选择器显示图像读取器和发送数据的结果
- 缺少图像拼接工具的`stitched_image`结果
- 无法选择拼接后的图像进行发送

#### 根本原因
`_update_property_panel_modules`方法只检查`result_data._values`，没有检查`result_data._images`。图像拼接工具使用`set_image`方法将图像保存到`_images`字典中，而不是`_values`。

#### 修复方案
在`_update_property_panel_modules`方法中，添加对`result_data._images`的检查：

```python
# ui/main_window.py
# 获取结果数据的所有值
if hasattr(result_data, "_values"):
    for key, value in result_data._values.items():
        available_modules[module_name][key] = value

# 获取结果数据中的图像
if hasattr(result_data, "_images"):
    for key, image in result_data._images.items():
        available_modules[module_name][key] = image
```

---

### 7. 发送数据编码错误

#### 问题描述
发送数据时报错`'ascii' codec can't encode characters`。

#### 错误现象
- 发送数据工具执行时抛出编码错误
- 错误发生在`enhanced_communication.py`第845行的`_format_data`方法
- 无法发送包含中文字符的数据

#### 根本原因
`_format_data`方法在格式化ASCII数据时使用`encode("ascii")`，无法编码中文字符。

#### 修复方案
将ASCII编码改为UTF-8编码：

```python
# tools/communication/enhanced_communication.py
elif format_lower == "ascii" or format_lower == "字符串":
    # 使用UTF-8编码以支持中文字符
    if isinstance(data, str):
        return data.encode("utf-8")
    return str(data).encode("utf-8")
```

---

### 8. 热重载回调错误（结果面板）

#### 问题描述
热重载时报错`'EnhancedResultDockWidget' object has no attribute 'refresh'`。

#### 错误现象
- 代码修改后触发热重载
- 报错`AttributeError: 'EnhancedResultDockWidget' object has no attribute 'refresh'`
- 热重载回调执行失败

#### 根本原因
`EnhancedResultDockWidget`类缺少`refresh`方法，但热重载回调`main_window.py`第1867行尝试调用它。

#### 修复方案
在`EnhancedResultDockWidget`类中添加`refresh`方法：

```python
# ui/enhanced_result_dock.py
def refresh(self):
    """刷新结果面板（热重载回调用）"""
    try:
        # 刷新增强面板
        if hasattr(self.enhanced_panel, 'refresh'):
            self.enhanced_panel.refresh()
        # 刷新传统面板
        if hasattr(self.traditional_panel, 'refresh'):
            self.traditional_panel.refresh()
        logger.info("结果面板已刷新")
    except Exception as e:
        logger.error(f"刷新结果面板失败: {e}")
```

---

### 9. 发送数据目标连接刷新问题

#### 问题描述
发送数据工具的目标连接需要多次点击才刷新，或选择"点击刷新获取连接列表"后未自动选择实际连接。

#### 错误现象
- 点击"目标连接"下拉框显示"暂无可用连接"
- 需要多次点击才能刷新出实际连接
- 选择"点击刷新获取连接列表"后，没有自动选择连接
- 运行工具时提示"未找到连接: 点击刷新获取连接列表"

#### 根本原因
1. 缓存时间过长（5秒），导致旧数据被使用
2. 刷新连接列表后，没有自动选择第一个可用连接
3. 用户选择"点击刷新获取连接列表"后，该值被保存为实际的目标连接值

#### 修复方案
1. 缩短缓存时间到1秒，确保能获取最新连接状态
2. 刷新连接列表后，自动选择第一个可用连接
3. 运行时检查目标连接是否为提示文本，如果是则自动刷新
4. 添加更多调试日志，方便排查问题

#### 代码变更
```python
# tools/communication/enhanced_communication.py

def _refresh_connection_options(self):
    """刷新连接列表选项"""
    # 清除缓存，强制获取最新连接
    if hasattr(self, '_connections_cache'):
        delattr(self, '_connections_cache')
    
    available_connections = self._get_available_connections()
    
    if available_connections:
        self._params["__options_目标连接"] = available_connections
        # 自动选择第一个可用连接
        first_connection = available_connections[0]
        self.set_param("目标连接", first_connection)
    else:
        self._params["__options_目标连接"] = ["暂无可用连接"]
        self.set_param("目标连接", "")

def _run_impl(self):
    # ...
    # 检查是否是提示文本，如果是则自动刷新
    if connection_id in ["点击刷新获取连接列表", "暂无可用连接", "刷新失败，请重试"]:
        self._logger.info(f"当前选择的是提示文本 '{connection_id}'，自动刷新连接列表")
        self._refresh_connection_options()
        # 重新获取连接ID
        connection_id = self.get_param("目标连接", "")
```

---

## 修改文件清单

| 文件路径 | 修改内容 |
|---------|---------|
| `ui/communication_config.py` | 修复单例模式、优化刷新机制、移除阻塞对话框 |
| `tools/vision/image_stitching.py` | 修复结果数据保存 |
| `tools/vision/template_match.py` | 添加结果面板期望的字段和类别 |
| `ui/main_window.py` | 修复结果面板显示、数据选择器图像结果 |
| `tools/communication/enhanced_communication.py` | 修复编码错误、优化连接刷新机制 |
| `ui/enhanced_result_dock.py` | 添加`refresh`方法 |
| `ui/data_selector.py` | 添加灰度匹配字段的翻译 |

---

## 测试建议

1. **通讯配置测试**
   - 建立TCP客户端连接
   - 编辑连接配置，检查是否卡顿
   - 保存方案，重新加载，检查连接是否保留

2. **结果面板测试**
   - 添加多个相同类型的工具（如2个图像读取器）
   - 执行流程，检查所有结果是否正确显示
   - 检查图像拼接结果是否显示

3. **发送数据测试**
   - 建立通讯连接
   - 添加发送数据工具
   - 点击目标连接下拉框，检查是否自动刷新并选择连接
   - 发送包含中文字符的数据

4. **灰度匹配测试**
   - 执行灰度匹配工具
   - 检查结果面板是否正确显示匹配结果（相似度、中心点等）

5. **数据选择器测试**
   - 执行图像拼接工具
   - 打开发送数据工具的数据选择器
   - 检查是否包含`stitched_image`选项

---

## 相关文档

- [CHANGELOG.md](../CHANGELOG.md) - 更新日志
- [通信修复记录](communication_fix_2026-02-05.md) - 之前的通信修复记录
- [性能优化计划](plans/2026-02-03-performance-optimization.md) - 性能优化相关

---

## 附录：调试技巧

### 查看连接状态
```python
# 在Python控制台中执行
from ui.communication_config import get_connection_manager
conn_manager = get_connection_manager()
connections = conn_manager.get_all_connections()
for conn in connections:
    print(f"{conn.id}: {conn.name} - {conn.is_connected}")
```

### 查看工具结果数据
```python
# 在Python控制台中执行
for proc in main_window.solution.procedures:
    for tool in proc.tools:
        if hasattr(tool, '_result_data') and tool._result_data:
            print(f"{tool.name}: {tool._result_data.get_all_values().keys()}")
```

---

**文档结束**
