# CPU优化模块集成文档

## 概述

本文档描述如何将CPU优化模块集成到现有的视觉检测项目中。模块提供了基于CPU的高性能计算优化方案，包括多线程并行处理、SIMD指令集优化、内存池管理和YOLO26模型推理功能。

## 目录结构

```
modules/cpu_optimization/
├── __init__.py              # 模块入口
├── core/
│   ├── __init__.py          # 核心模块初始化
│   ├── parallel_engine.py   # 并行处理引擎
│   ├── memory_pool.py       # 内存池管理
│   └── simd_optimizations.py # SIMD优化
├── models/
│   ├── __init__.py          # 模型模块初始化
│   └── yolo26_cpu.py        # YOLO26 CPU适配器
├── api/
│   ├── __init__.py          # API模块初始化
│   └── cpu_detector.py      # CPU检测器API
└── utils/
    ├── __init__.py          # 工具模块初始化
    └── performance_monitor.py # 性能监控
```

## 快速开始

### 1. 基本使用

```python
import sys
from pathlib import Path

# 添加模块路径
module_path = Path(__file__).parent / "modules"
sys.path.insert(0, str(module_path))

from modules.cpu_optimization import (
    YOLO26CPUDetector,
    CPUInferenceConfig,
    PerformanceMonitor
)

# 创建检测器
config = CPUInferenceConfig(
    num_threads=4,           # CPU线程数
    conf_threshold=0.25,     # 置信度阈值
    nms_threshold=0.45       # NMS阈值
)

detector = YOLO26CPUDetector(config)

# 加载模型
if detector.load_model("yolov8n.onnx"):
    # 预热模型
    detector.warmup(5)
    
    # 检测图像
    import cv2
    image = cv2.imread("test.jpg")
    result = detector.detect(image)
    
    print(f"检测到 {len(result.boxes)} 个目标")
    for box in result.boxes:
        print(f"  - {box.class_name}: {box.confidence:.2f}")
    
    detector.release()
```

### 2. 使用API接口

```python
from modules.cpu_optimization import (
    CPUDetectorAPI,
    APIConfig,
    get_performance_monitor
)

# 创建API实例
api = CPUDetectorAPI(APIConfig(
    num_threads=4,
    confidence_threshold=0.25
))

# 加载模型
api.load_model("yolov8n.onnx", "coco_classes.txt")

# 预热
api.warmup(5)

# 启动性能监控
monitor = get_performance_monitor(0.5)
monitor.start()

# 检测图像
result = api.detect(image)

# 获取性能统计
print(api.get_performance_stats())

# 释放资源
api.release()
monitor.stop()
```

### 3. 与现有项目集成

#### 3.1 集成到工具模块

```python
# 在您的tools目录中创建新工具
from modules.cpu_optimization import YOLO26CPUDetector, CPUInferenceConfig

class YOLO26CPUTool:
    """YOLO26 CPU检测工具"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.detector = None
        
    def initialize(self, parameters):
        """初始化工具"""
        model_path = parameters.get("model_path", "yolov8n.onnx")
        conf_thresh = parameters.get("conf_threshold", 0.25)
        
        inference_config = CPUInferenceConfig(
            num_threads=self.config.get("num_threads", 4),
            conf_threshold=conf_thresh
        )
        
        self.detector = YOLO26CPUDetector(inference_config)
        self.detector.load_model(model_path)
        self.detector.warmup()
        
    def execute(self, input_data):
        """执行检测"""
        if isinstance(input_data, dict) and "image" in input_data:
            image = input_data["image"]
        else:
            image = input_data
            
        result = self.detector.detect(image)
        
        return {
            "boxes": result.boxes,
            "inference_time_ms": result.inference_time_ms
        }
        
    def release(self):
        """释放资源"""
        if self.detector:
            self.detector.release()
```

#### 3.2 集成到UI界面

```python
from PyQt5.QtCore import QTimer
from modules.cpu_optimization import PerformanceMonitor

class PerformanceDisplay(QWidget):
    """性能显示面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = get_performance_monitor(1.0)
        self.monitor.start()
        
        # 设置更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)  # 每秒更新
        
        self.setup_ui()
_display(self):
               
    def update """更新显示"""
        metrics = self.monitor.get_current_metrics()
        
        self.cpu_label.setText(f"CPU: {metrics.cpu_percent:.1f}%")
        self.memory_label.setText(f"内存: {metrics.memory_used_mb:.1f} MB")
        self.fps_label.setText(f"FPS: {metrics.fps:.1f}")
        self.inference_label.setText(f"推理: {metrics.inference_time_ms:.2f} ms")
```

## 性能优化配置

### 线程数配置

```python
# 自动检测最佳线程数
config = CPUInferenceConfig(num_threads=0)

# 手动指定线程数（建议设置为物理核心数）
config = CPUInferenceConfig(num_threads=4)

# 限制线程数以平衡性能和功耗
config = CPUInferenceConfig(num_threads=2)
```

### 量化配置

```python
# 启用INT8量化（减少内存占用，加速推理）
config = CPUInferenceConfig(
    use_quantization=True,
    quantization_bits=8
)
```

### 内存池配置

```python
from modules.cpu_optimization import get_memory_pool

# 配置内存池
pool = get_memory_pool()
pool.set_max_size(512)  # 最大512MB
```

## 性能监控

### 控制台监控

```python
from modules.cpu_optimization import get_performance_monitor

monitor = get_performance_monitor(0.5)  # 0.5秒采样间隔
monitor.start()

# 注册回调
def on_metrics(metrics):
    print(f"CPU: {metrics.cpu_percent}%, "
          f"内存: {metrics.memory_used_mb}MB, "
          f"FPS: {metrics.fps}")

monitor.register_callback(on_metrics)
```

### 导出数据

```python
# 导出性能数据到JSON
monitor.export_history("performance.json", format="json")

# 导出性能数据到CSV
monitor.export_history("performance.csv", format="csv")
```

## 常见问题

### Q1: 模型加载失败

确保模型文件路径正确，并且模型格式受支持（.onnx, .pb, .param等）。

```python
# 检查模型文件
import os
model_path = "models/yolov8n.onnx"
if os.path.exists(model_path):
    detector.load_model(model_path)
else:
    print(f"模型文件不存在: {model_path}")
```

### Q2: 推理速度慢

1. 检查线程数配置
2. 启用量化
3. 使用更小的输入尺寸
4. 确保模型已预热

```python
# 优化配置
config = CPUInferenceConfig(
    num_threads=4,              # 增加线程数
    use_quantization=True,      # 启用量化
    input_size=(320, 320)       # 减小输入尺寸
)
```

### Q3: 内存占用过高

```python
# 减少内存池大小
pool = get_memory_pool()
pool.set_max_size(256)  # 限制为256MB

# 使用更小的批次大小
config = CPUInferenceConfig(batch_size=1)
```

## 性能基准

### 测试环境
- CPU: Intel Core i7-10700 (8核心16线程)
- 内存: 16GB
- 模型: YOLOv8n (ONNX格式)

### 预期性能

| 配置 | 输入尺寸 | FPS | 推理时间 |
|------|----------|-----|----------|
| 8线程 + 量化 | 640x640 | 15-20 | 50-65ms |
| 8线程 | 640x640 | 12-15 | 65-85ms |
| 4线程 + 量化 | 640x640 | 10-12 | 85-100ms |
| 4线程 | 320x320 | 25-30 | 33-40ms |

## 与现有项目架构兼容

### 集成到Core模块

```python
# 在core/__init__.py中添加
from modules.cpu_optimization import (
    ParallelEngine,
    MemoryPool,
    SIMDOptimizer
)

__all__ = [
    # ... 现有导出
    "ParallelEngine",
    "MemoryPool",
    "SIMDOptimizer"
]
```

### 集成到Tools模块

```python
# 在tools目录中创建yolo26_cpu_tool.py
from modules.cpu_optimization import create_yolo26_detector

class YOLO26CPUTool:
    # 工具实现
    pass
```

## 更新日志

### v1.0.0 (2026-01-26)
- 初始版本发布
- 支持YOLO26 CPU推理
- 多线程并行处理
- SIMD指令优化
- 内存池管理
- 性能监控
- 完整API接口
