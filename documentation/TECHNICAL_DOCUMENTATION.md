# Vision System 技术文档

> **项目名称**: Vision System (视觉检测系统)  
> **版本**: v2.0.0 (CPU优化版)  
> **最后更新**: 2026年2月9日  
> **状态**: ✅ 持续开发中

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [核心功能模块](#3-核心功能模块)
4. [CPU优化模块](#4-cpu优化模块)
5. [工具模块详解](#5-工具模块详解)
6. [API接口设计](#6-api接口设计)
7. [集成指南](#7-集成指南)
8. [性能优化](#8-性能优化)
9. [开发进度与待办](#9-开发进度与待办)
10. [常见问题](#10-常见问题)
11. [文档合并说明](#11-文档合并说明)

---

## 1. 项目概述

### 1.1 项目目标

基于海康VisionMaster V4.4.0算法开发平台的架构，使用Python语言实现一个完整的视觉检测系统，支持：

- 图像采集与处理
- 视觉算法工具
- 流程控制与可视化编程
- 设备通讯
- CPU/GPU混合计算优化

### 1.2 技术栈

| 类别 | 技术选型 |
|------|---------|
| 编程语言 | Python 3.8+ |
| GUI框架 | PyQt5/PyQt6 |
| 图像处理 | OpenCV, NumPy |
| 深度学习 | PyTorch (CPU优化版) |
| 相机SDK | 海康MVS, Basler |
| 文档生成 | Markdown |

### 1.3 项目结构

```
vision_system/
├── config/                      # 配置文件
├── configs/                     # 配置模板
├── core/                        # 核心逻辑层
│   ├── communication/           # 通讯模块
│   ├── tool_base.py            # 工具基类
│   ├── solution.py             # 方案管理
│   ├── procedure.py            # 流程管理
│   ├── zoomable_image.py       # 可缩放图像组件
│   └── memory_pool.py          # 内存池管理
├── data/                        # 数据层
│   ├── images/                  # 图像文件
│   ├── models/                  # 模型文件
│   ├── test_results/            # 测试结果
│   ├── image_data.py           # 图像数据结构
│   └── result_data.py          # 结果数据结构
├── documentation/               # 文档目录
│   ├── TECHNICAL_DOCUMENTATION.md # 技术文档（本文档）
│   ├── ARCHITECTURE.md         # 架构设计
│   ├── ERROR_HANDLING_GUIDE.md  # 错误处理指南
│   ├── MULTI_IMAGE_SELECTOR.md  # 多图像选择器文档
│   └── ...                      # 其他文档
├── examples/                    # 示例代码
├── modules/                     # 功能模块层
│   ├── cpu_optimization/       # CPU优化模块
│   ├── camera/                 # 相机模块
│   └── hot_reload/             # 热重载模块
├── tests/                       # 测试代码
├── tools/                       # 算法工具层
│   ├── image_source.py         # 图像源工具
│   ├── multi_image_selector.py  # 多图像选择器工具 ⭐
│   ├── camera_parameter_setting.py # 相机参数设置
│   ├── vision/                 # 视觉工具子包
│   ├── communication/           # 通信工具子包
│   └── analysis/               # 分析工具子包
├── ui/                          # 界面层
│   ├── main_window.py          # 主窗口
│   ├── tool_library.py         # 工具库
│   ├── property_panel.py       # 属性面板
│   ├── result_panel.py         # 结果面板
│   └── algorithm_scene.py      # 算法编辑器场景
└── utils/                       # 工具模块
    ├── exceptions.py           # 异常定义
    ├── error_management.py     # 错误管理
    └── image_processing_utils.py # 图像处理工具
```

---

## 2. 系统架构

### 2.1 四层架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MainWindow (主窗口)                      │  │
│  │  - 菜单栏 (文件/编辑/运行/视图/帮助)                        │  │
│  │  - 工具栏 (运行控制/图像控制)                               │  │
│  │  - 停靠窗口 (项目浏览器/工具库/属性面板/结果面板)            │  │
│  │  - 中央区域 (图像视图/算法编辑器)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      核心层 (Core Layer)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Solution (方案)                       │  │
│  │  - 管理多个流程 (Procedure)                                │  │
│  │  - 执行控制 (单次运行/连续运行/停止)                       │  │
│  │  - 方案保存/加载                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Procedure (流程)                       │  │
│  │  - 管理多个工具 (Tool)                                     │  │
│  │  - 数据流转 (输入/输出)                                    │  │
│  │  - 流程控制 (条件分支/循环)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     工具层 (Tool Layer)                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐  │
│  │ 图像源模块  │ 图像处理模块│ 视觉算法模块│   通信模块       │  │
│  ├─────────────┼─────────────┼─────────────┼─────────────────┤  │
│  │ ImageSource │ BoxFilter   │ GrayMatch   │ ReadDatas       │  │
│  │ MultiImage  │ Morphology  │ BlobFind    │ SendDatas       │  │
│  │ Selector    │ Resize      │ Bcr         │ DynamicIO       │  │
│  │ Camera      │             │ Caliper     │                 │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     数据层 (Data Layer)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     ImageData (图像数据)                   │  │
│  │  - 图像数组 (numpy.ndarray)                                │  │
│  │  - 元数据 (宽度/高度/通道/时间戳)                          │  │
│  │  - ROI信息                                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    ResultData (结果数据)                  │  │
│  │  - 数值结果 (int/float)                                  │  │
│  │  - 几何形状 (点/线/圆/矩形)                              │  │
│  │  - 字符串结果                                             │  │
│  │  - 图像结果                                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心功能模块

### 3.1 方案管理 (Solution)

**核心功能**：
- 多流程管理
- 方案保存/加载 (JSON格式)
- 通讯配置管理
- 执行状态监控

**主要接口**：
```python
class Solution:
    def add_procedure(procedure: Procedure)
    def remove_procedure(name: str)
    def run(input_image: ImageData = None)
    def stop()
    def save(path: str) -> bool
    def load(path: str) -> bool
```

### 3.2 流程管理 (Procedure)

**核心功能**：
- 工具链管理
- 数据连接/流转
- 执行顺序控制

**主要接口**：
```python
class Procedure:
    def add_tool(tool: ToolBase)
    def remove_tool(name: str)
    def connect(from_tool: str, to_tool: str, from_port: str, to_port: str)
    def run(input_image: ImageData = None)
```

### 3.3 工具基类 (ToolBase)

**核心功能**：
- 参数管理 (get_param / set_param)
- 输入/输出数据管理
- 工具生命周期管理
- 错误处理和日志记录

**主要接口**：
```python
class ToolBase:
    def get_param(key: str, default=None) -> Any
    def set_param(key: str, value: Any)
    def set_input(input_data: ImageData, port_name: str = "InputImage")
    def get_output(port_name: str = "OutputImage") -> ImageData
    def run() -> bool
```

---

## 4. CPU优化模块

### 4.1 YOLO26-CPU优化

**功能特性**：
- CPU优化推理（支持动态批处理）
- 支持多种模型类型
- 结果可视化

### 4.2 内存池优化

**ImageBufferPool**：
- 预分配图像缓冲区
- 减少内存分配开销
- 支持多线程安全访问

---

## 5. 工具模块详解

### 5.1 图像源工具

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| 图像读取器 | 从本地文件读取图像 | ✅ |
| **多图像选择器** | 加载多张图片，支持切换和自动运行 | ✅ ⭐新增 |
| 相机 | 从相机采集图像 | ✅ |
| 相机参数设置 | 配置相机参数 | ✅ |

### 5.2 图像处理工具

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| 方框滤波 | 图像平滑处理 | ✅ |
| 均值滤波 | 均值模糊 | ✅ |
| 高斯滤波 | 高斯模糊 | ✅ |
| 中值滤波 | 中值模糊 | ✅ |
| 双边滤波 | 边缘保留滤波 | ✅ |
| 形态学 | 膨胀/腐蚀/开/闭运算 | ✅ |
| 图像缩放 | 图像尺寸调整 | ✅ |
| 图像拼接 | 多图像拼接 | ✅ |
| 图像计算 | 加减乘除运算 | ✅ |

### 5.3 视觉算法工具

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| 灰度匹配 | 基于灰度的模板匹配 | ✅ |
| 形状匹配 | 基于形状的模板匹配 | ✅ |
| 直线查找 | 边缘直线检测 | ✅ |
| 圆查找 | 圆形检测 | ✅ |
| Blob分析 | 斑点检测 | ✅ |
| OCR识别 | 文本识别 | ✅ |
| 条码读取 | 条码识别 | ✅ |
| 二维码读取 | 二维码识别 | ✅ |
| YOLO26-CPU | 深度学习目标检测 | ✅ |
| 标定 | 相机标定 | ✅ |

---

## 6. API接口设计

### 6.1 工具注册机制

```python
from core.tool_base import ToolRegistry

@ToolRegistry.register
class MyTool(ToolBase):
    tool_name = "我的工具"
    tool_category = "Custom"
    tool_description = "工具描述"
    
    def _init_params(self):
        self.set_param("param1", default_value)
```

### 6.2 参数类型定义

```python
class ParameterType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    FILE_PATH = "file_path"
    IMAGE_FILE_PATH = "image_file_path"
    FILE_LIST = "file_list"  # 多图像选择器使用
    ROI_RECT = "roi_rect"
    ROI_LINE = "roi_line"
    ROI_CIRCLE = "roi_circle"
    BUTTON = "button"
    DATA_CONTENT = "data_content"
```

---

## 7. 集成指南

### 7.1 创建新工具

1. **继承ToolBase**:
```python
from core.tool_base import ToolBase, ToolRegistry

@ToolRegistry.register
class MyTool(ToolBase):
    tool_name = "我的工具"
    tool_category = "Custom"
    
    def _init_params(self):
        self.set_param("threshold", 0.5)
    
    def _run_impl(self):
        # 实现具体逻辑
        return {"OutputImage": image_data}
```

2. **注册到工具库**:
在 `ui/tool_library.py` 中添加:
```python
ToolItemData(
    "Custom",
    "我的工具",
    "我的工具",
    "🔧",
    "工具描述"
)
```

### 7.2 自定义参数类型

在 `ui/property_panel.py` 中:

1. 添加枚举值:
```python
class ParameterType(Enum):
    CUSTOM_TYPE = "custom_type"
```

2. 创建编辑器控件:
```python
elif param_type == ParameterType.CUSTOM_TYPE:
    widget = CustomEditorWidget()
```

---

## 8. 性能优化

### 8.1 内存优化

- **ImageBufferPool**: 预分配图像缓冲区
- **内存泄漏修复**: 确保资源正确释放

### 8.2 算法优化

- **图像拼接**: ORB特征检测 + Sigmoid融合
- **YOLO26-CPU**: CPU优化推理

### 8.3 UI优化

- **Qt信号优化**: 减少不必要的信号发射
- **事件处理优化**: 使用Qt事件过滤器

---

## 9. 开发进度与待办

### 已完成

| 模块 | 进度 | 说明 |
|------|------|------|
| 核心框架 | 100% | Solution/Procedure/ToolBase |
| 图像源工具 | 100% | ImageSource/MultiImageSelector/Camera |
| 图像处理工具 | 100% | 滤波/形态学/缩放/拼接 |
| 视觉算法 | 100% | 模板匹配/Blob/OCR/标定 |
| 通信工具 | 100% | TCP/串口/Modbus/WebSocket |
| UI组件 | 100% | 主窗口/工具库/属性面板/结果面板 |
| 方案管理 | 100% | 保存/加载/导出 |
| CPU优化 | 100% | YOLO26-CPU/内存池 |

### 待办

| 模块 | 优先级 | 说明 |
|------|--------|------|
| 文档完善 | 中 | 补充API文档和使用示例 |
| 测试覆盖 | 中 | 增加单元测试覆盖率 |

---

## 10. 常见问题

### Q1: 如何添加新工具?

参考第7章"集成指南"，继承ToolBase并使用@ToolRegistry.register装饰器。

### Q2: 如何处理工具间的数据传递?

使用Procedure.connect()方法连接工具的输入/输出端口。

### Q3: 如何保存和加载方案?

使用Solution.save()和Solution.load()方法，支持JSON格式。

### Q4: 多图像选择器如何自动运行?

在工具属性中勾选"自动运行"选项，切换图片时会自动触发流程执行。

---

## 11. 文档合并说明

### 11.1 合并历史

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-02-09 | 合并 TECHNICAL_DOCUMENT.md + PROJECT_DOCUMENTATION.md | 整合两份重复的技术文档 |
| 2026-02-09 | 新增 ERROR_RECORD.md → ERROR_HANDLING_GUIDE.md | 将具体错误记录合并到错误处理指南 |
| 2026-02-09 | 新增多图像选择器文档 MULTI_IMAGE_SELECTOR.md | 新工具的完整使用说明 |

### 11.2 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目介绍和快速开始 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计 |
| [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) | 错误处理和异常管理 |
| [MULTI_IMAGE_SELECTOR.md](MULTI_IMAGE_SELECTOR.md) | 多图像选择器工具文档 |
| [AGENTS.md](../AGENTS.md) | AI Agent开发指南 |

---

**文档版本**: v3.0  
**最后更新**: 2026-02-09  
**维护者**: Vision System Team
