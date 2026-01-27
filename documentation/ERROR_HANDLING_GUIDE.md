# 错误处理和异常管理指南

## 概述

本文档提供了Vision System项目中错误处理和异常管理的详细指南，包括：
- 异常捕获和处理机制
- 错误信息管理和显示
- 系统级错误恢复机制
- 最佳实践和使用示例

## 错误处理架构

### 1. 异常类层次结构

项目使用层次化的异常类结构，基于`VisionMasterException`基类：

```
VisionMasterException
├── CameraException
│   ├── CameraConnectionException
│   └── CameraCaptureException
├── ToolException
│   ├── ToolExecutionException
│   └── ToolNotFoundException
├── ParameterException
│   └── InvalidParameterException
├── ProcedureException
├── SolutionException
├── ImageException
├── ROIException
├── ConfigException
├── CommunicationException
├── TimeoutException
├── PermissionException
├── FileException
├── LicenseException
└── ModelException
```

### 2. 错误管理模块

项目提供了`utils.error_management`模块，用于统一管理和显示错误消息：

- **错误代码**：使用HTTP风格的错误代码（400-599）
- **错误严重程度**：INFO、WARNING、ERROR、CRITICAL
- **错误类别**：参数错误、图像错误、相机错误等
- **错误消息格式化**：统一的错误消息格式
- **错误日志记录**：基于严重程度的日志记录

### 3. 错误恢复模块

项目提供了`utils.error_recovery`模块，实现系统级错误恢复机制：

- **恢复策略**：重试、降级、重启、忽略、告警
- **自动恢复**：针对不同类型错误的自动恢复处理
- **恢复历史**：记录错误恢复的历史记录

## 使用指南

### 1. 工具错误处理

所有工具都继承自`ToolBase`类，该类提供了统一的错误处理机制：

```python
from core.tool_base import ToolBase
from utils.exceptions import ParameterException

class MyTool(ToolBase):
    tool_name = "我的工具"
    tool_category = "Custom"
    
    def _run_impl(self):
        # 检查参数
        threshold = self.get_param("threshold")
        if threshold < 0 or threshold > 1:
            raise ParameterException("阈值必须在0-1之间")
        
        # 执行处理逻辑
        # ...
        
        return {"result": "success"}
```

### 2. 错误消息管理

使用`utils.error_management`模块管理错误消息：

```python
from utils.error_management import get_error_message, log_error

# 格式化错误消息
error_msg = get_error_message(400, "参数值无效")
print(error_msg)  # 输出: [ERROR] 参数错误: 参数值无效

# 记录错误日志
log_error(400, "参数值无效", {"tool": "my_tool", "param": "threshold"})
```

### 3. 错误恢复

使用`utils.error_recovery`模块进行错误恢复：

```python
from utils.error_recovery import recover_from_error, RecoveryStatus

# 执行错误恢复
status = recover_from_error(
    error_type="ParameterError",
    error_code=400,
    error_message="参数值无效",
    component="my_tool",
    details={"tool": "my_tool", "param": "threshold"}
)

print(f"恢复状态: {status.value}")
```

## 最佳实践

### 1. 异常处理最佳实践

- **捕获具体异常**：优先捕获具体的异常类型，而不是通用的`Exception`
- **提供详细错误信息**：异常消息应包含足够的信息，便于调试
- **记录异常上下文**：记录异常发生时的上下文信息
- **适当的异常传播**：根据需要决定是处理异常还是向上传播

### 2. 错误消息最佳实践

- **使用统一格式**：使用`get_error_message`函数格式化错误消息
- **包含错误代码**：错误消息应包含错误代码，便于识别错误类型
- **提供具体信息**：错误消息应包含具体的错误原因
- **推荐操作**：对于常见错误，提供推荐的解决方法

### 3. 错误恢复最佳实践

- **选择合适的恢复策略**：根据错误类型选择合适的恢复策略
- **设置合理的重试参数**：为重试策略设置合理的尝试次数和延迟
- **监控恢复过程**：记录错误恢复的过程和结果
- **定期分析错误**：定期分析错误日志，优化错误处理和恢复机制

## 错误代码参考

| 错误代码 | 错误消息 | 严重程度 | 类别 | 描述 | 推荐操作 |
|---------|---------|---------|------|------|----------|
| 400 | 参数错误 | ERROR | PARAMETER | 输入参数无效或超出范围 | 检查参数值是否符合要求 |
| 422 | 图像处理错误 | ERROR | IMAGE | 图像数据无效或处理失败 | 检查图像源是否正确 |
| 502 | 相机错误 | CRITICAL | CAMERA | 相机连接或采集失败 | 检查相机连接和配置 |
| 500 | 工具执行错误 | ERROR | TOOL | 工具执行过程中发生错误 | 检查工具配置和输入数据 |
| 503 | 网络错误 | ERROR | NETWORK | 网络连接或通信失败 | 检查网络连接和目标设备状态 |
| 404 | 文件未找到 | ERROR | FILE | 请求的文件不存在 | 检查文件路径是否正确 |
| 501 | 系统错误 | CRITICAL | SYSTEM | 系统内部错误 | 检查系统日志和配置 |

## 示例

### 1. 工具实现示例

```python
from core.tool_base import ToolBase
from utils.exceptions import ParameterException, ImageException
from data.image_data import ImageData

class EdgeDetectionTool(ToolBase):
    tool_name = "边缘检测"
    tool_category = "Vision"
    
    def _run_impl(self):
        # 获取参数
        threshold1 = self.get_param("threshold1", 50)
        threshold2 = self.get_param("threshold2", 150)
        
        # 检查参数
        if threshold1 < 0 or threshold1 > 255:
            raise ParameterException("阈值1必须在0-255之间")
        if threshold2 < 0 or threshold2 > 255:
            raise ParameterException("阈值2必须在0-255之间")
        if threshold1 >= threshold2:
            raise ParameterException("阈值1必须小于阈值2")
        
        # 获取输入图像
        input_image = self._input_data
        if not input_image or not input_image.is_valid:
            raise ImageException("输入图像无效")
        
        # 执行边缘检测
        import cv2
        gray = cv2.cvtColor(input_image.data, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, threshold1, threshold2)
        
        # 创建输出图像
        output_image = ImageData(data=edges)
        
        return {"OutputImage": output_image, "edges_detected": True}
```

### 2. 错误处理示例

```python
from core.tool_base import ToolBase
from utils.exceptions import ToolException
from utils.error_management import log_error

# 创建工具实例
tool = EdgeDetectionTool("edge_detection")

# 设置参数
tool.set_param("threshold1", 100)
tool.set_param("threshold2", 200)

# 执行工具
try:
    success = tool.run()
    if success:
        print("工具执行成功")
    else:
        print(f"工具执行失败: {tool.last_error}")
except ToolException as e:
    print(f"工具异常: {e}")
    log_error(500, str(e), {"tool": tool.name})
except Exception as e:
    print(f"系统异常: {e}")
    log_error(501, str(e), {"tool": tool.name})
```

### 3. 错误恢复示例

```python
from utils.error_recovery import recover_from_error, RecoveryStatus, register_recovery_strategy, RecoveryAction, RecoveryStrategy

# 注册自定义恢复策略
def custom_recovery_action(error_context):
    """自定义恢复操作"""
    print(f"执行自定义恢复: {error_context.error_message}")
    # 执行恢复操作
    return True

register_recovery_strategy(
    "CustomError",
    RecoveryAction(
        strategy=RecoveryStrategy.RETRY,
        action=custom_recovery_action,
        max_attempts=3,
        delay=1.0,
        description="自定义错误恢复策略"
    )
)

# 执行错误恢复
status = recover_from_error(
    error_type="CustomError",
    error_code=500,
    error_message="自定义错误",
    component="my_component",
    details={"key": "value"}
)

print(f"恢复状态: {status.value}")
```

## 故障排除

### 常见错误及解决方法

1. **参数错误（400）**
   - 检查参数值是否在有效范围内
   - 检查参数类型是否正确
   - 参考工具的参数定义

2. **图像错误（422）**
   - 检查输入图像是否有效
   - 检查图像路径是否正确
   - 检查图像格式是否支持

3. **相机错误（502）**
   - 检查相机连接是否正常
   - 检查相机驱动是否安装
   - 检查相机配置是否正确

4. **系统错误（501）**
   - 检查系统日志获取详细信息
   - 检查依赖库是否正确安装
   - 检查硬件资源是否充足

### 日志分析

项目使用Python标准的`logging`模块进行日志记录，日志级别包括：

- **DEBUG**：详细的调试信息
- **INFO**：一般信息
- **WARNING**：警告信息
- **ERROR**：错误信息
- **CRITICAL**：严重错误信息

日志文件默认保存在`app.log`中，可以通过配置文件修改。

## 总结

良好的错误处理和异常管理是构建稳定可靠系统的关键。通过本文档提供的指南和最佳实践，开发人员可以：

- 实现统一的错误处理机制
- 提供清晰一致的错误信息
- 构建自动错误恢复能力
- 提高系统的稳定性和可靠性

遵循这些指南，将有助于构建更加健壮的Vision System系统，为用户提供更好的使用体验。
