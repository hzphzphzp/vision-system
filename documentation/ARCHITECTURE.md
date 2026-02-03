# Vision System 架构设计文档

> 最后更新: 2026-02-03

## 1. 系统架构概览

```
应用层 (MainWindow) 
    ↓
核心层 (Solution/Procedure/Pipeline/MemoryPool)
    ↓  
工具层 (40+ Algorithm Tools)
    ↓
数据层 (ImageData/ResultData/ROI)
```

## 2. 核心组件

### 2.1 内存池系统 (Memory Pool)

**文件**: `core/memory_pool.py`

```python
class ImageBufferPool:
    """图像缓冲区内存池
    
    预分配固定大小的图像内存，避免频繁的malloc/free
    线程安全
    """
    
    def __init__(self, max_size: int = 10, buffer_shape: Tuple = (480, 640, 3)):
        # 预分配缓冲区
        self._available = queue.Queue(maxsize=max_size)
        self._in_use: Set[int] = set()
        
    def acquire(self, timeout: float = None) -> Optional[np.ndarray]:
        """获取缓冲区"""
        
    def release(self, buffer: np.ndarray) -> None:
        """释放缓冲区"""
```

**性能提升**: 118x 内存分配速度

### 2.2 确定性流水线 (Deterministic Pipeline)

**文件**: `core/pipeline.py`

```python
class PipelineStage:
    """流水线处理阶段"""
    
class DeterministicPipeline:
    """确定性图像处理流水线
    
    特点：
    1. 严格顺序处理，保证结果一致性
    2. 每个阶段独立线程，无共享状态
    3. 队列大小限制，防止内存爆炸
    """
```

**使用方法**:
```python
solution = Solution("test")
solution.enable_pipeline_mode(buffer_size=5)
solution.put_input(image_data)
```

## 3. 数据结构

### 3.1 ImageData

**文件**: `data/image_data.py`

```python
class ImageData:
    """图像数据结构，封装图像及其元数据"""
    
    __slots__ = (
        '_data', '_timestamp', '_roi', '_camera_id', '_pixel_format',
        '_image_type', '_metadata', '_height', '_width', '_channels',
        '_pool', '_use_pool', '_buffer'
    )
```

### 3.2 ResultData

**文件**: `data/image_data.py`

```python
class ResultData:
    """结果数据类，封装算法检测结果"""
```

## 4. 核心模块

### 4.1 Solution (方案管理)

**文件**: `core/solution.py`

```python
class Solution:
    """方案类，管理多个流程"""
    
    def enable_pipeline_mode(self, buffer_size: int = 3) -> None:
        """启用流水线处理模式"""
        
    def put_input(self, image_data: ImageData) -> bool:
        """放入输入图像(流水线模式)"""
```

### 4.2 Procedure (流程管理)

**文件**: `core/procedure.py`

```python
class Procedure:
    """流程类，管理工具序列"""
```

### 4.3 ToolBase (工具基类)

**文件**: `core/tool_base.py`

```python
class ToolBase:
    """算法工具基类"""
    
class ToolRegistry:
    """工具注册表"""
```

## 5. 工具分类

| 类别 | 工具数量 | 说明 |
|------|---------|------|
| 图像源 | 3+ | 图像读取器、相机采集 |
| 图像处理 | 8+ | 滤波、形态学、阈值、缩放 |
| 视觉算法 | 15+ | 模板匹配、几何检测、斑点分析 |
| 测量工具 | 2+ | 卡尺测量、尺寸测量 |
| 识别工具 | 4+ | 条码、二维码、OCR |
| 通信工具 | 8+ | TCP、串口、Modbus、WebSocket |
| 分析工具 | 3+ | 斑点分析、像素计数、直方图 |
| 外观检测 | 2+ | 外观检测器、表面缺陷检测器 |

## 6. 测试结构

```
tests/
├── test_memory_pool.py           # 内存池测试 (3 tests)
├── test_image_data_pool.py       # ImageData集成测试 (2 tests)
├── test_pipeline.py              # 流水线测试 (3 tests)
├── test_solution_pipeline.py     # Solution集成测试 (2 tests)
├── test_integration.py           # 系统集成测试
├── test_image_stitching.py       # 图像拼接测试
├── test_yolo26.py                # YOLO26测试
└── ...
```

## 7. 性能基准

| 组件 | 性能指标 |
|------|---------|
| 内存池 | 118x 提升 vs 普通分配 |
| ImageData __slots__ | 创建速度 +11%，复制速度 +29% |
| 流水线 | 严格顺序处理，多线程并行 |

## 8. 扩展指南

### 8.1 添加新工具

```python
@ToolRegistry.register
class MyNewTool(ToolBase):
    tool_name = "新工具名称"
    tool_category = "工具类别"
    
    def _run_impl(self):
        # 实现逻辑
        pass
```

### 8.2 添加流水线阶段

```python
def my_process_func(frame):
    """处理函数"""
    return result

stage = PipelineStage("my_stage", my_process_func)
pipeline.add_stage(stage)
```

## 9. 依赖关系

```
MainWindow
    ↓
Solution → Procedure → ToolBase → [Tools]
    ↓           ↓
Pipeline    MemoryPool
    ↓           ↓
ImageData ←────┘
```

## 10. 注意事项

1. **内存池**: 形状不匹配时回退到普通分配
2. **流水线**: 需要手动启动/停止
3. **线程安全**: 内存池使用锁保护
4. **资源释放**: ImageData析构时自动释放缓冲区
