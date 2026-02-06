# Vision System - 视觉检测系统

> 🎯 **海康VisionMaster V4.4.0的Python完整重构版本**  
> 📅 **项目完成时间**: 2026年1月30日  
> 🏆 **项目状态**: ✅ 完成并通过案例测试  
> 📊 **最新更新**: 2026年2月6日 - 图像拼接性能优化

---

## 📋 目录

1. [项目特色](#-项目特色)
2. [快速开始](#-快速开始)
3. [功能模块](#-功能模块)
4. [系统架构](#-系统架构)
5. [项目结构](#-项目结构)
6. [文档导航](#-文档导航)
7. [测试验证](#-测试验证)
8. [使用示例](#-使用示例)
9. [技术亮点](#-技术亮点)
10. [更新日志](#-更新日志)
11. [已知问题](#-已知问题)

---

## 🌟 项目特色

### 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| 🏗️ **模块化架构** | 四层架构设计，松耦合高内聚 | ✅ |
| 🖱️ **可视化编程** | 拖拽式工具连接，所见即所得 | ✅ |
| 🌏 **完整中文化** | 界面和参数全面中文化 | ✅ |
| 🔌 **工业级通信** | TCP/串口/Modbus/WebSocket | ✅ |
| 💾 **方案管理** | 保存/加载/导出完整方案 | ✅ |
| 📊 **结果可视化** | 多种数据类型实时显示 | ✅ |
| 🎥 **设备集成** | 海康机器人/OpenCV相机 | ✅ |
| 🚀 **代码生成** | 自动生成可执行Python代码 | ✅ |
| 🔄 **连续运行** | 支持单次/连续运行模式 | ✅ |

### 性能优化

| 优化项 | 技术 | 提升 |
|--------|------|------|
| 🛡️ **内存优化** | 修复多处内存泄漏 | 稳定运行 |
| 📷 **图像拼接** | ORB + Sigmoid融合 | **17x** |
| 🎯 **YOLO26-CPU** | CPU优化推理 | 实时检测 |
| ⚡ **内存池** | ImageBufferPool | **118x** |
| 📋 **流水线** | DeterministicPipeline | 并行处理 |

---

## 🚀 快速开始

### 环境要求

```bash
Python 3.7+
PySide6 / PyQt5 / PyQt6
OpenCV 4.5+
NumPy 1.26.4 (兼容PyTorch和OpenCV)
PyTorch 2.1.0+ (用于YOLO26)
Ultralytics 8.4.7+ (用于YOLO26)
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动系统

```bash
# 方式1: 直接启动主界面
python ui/main_window.py

# 方式2: 使用启动脚本
python main.py

# 方式3: 使用运行脚本
python run.py --gui
```

---

## 📖 功能模块

### 🔧 核心工具库

| 类别 | 工具 |
|------|------|
| **图像源** | 图像读取器、相机采集、相机参数设置 |
| **图像处理** | 滤波、形态学、阈值、缩放、图像拼接、图像计算 |
| **视觉算法** | 模板匹配、几何检测、斑点分析、YOLO26-CPU、OCR、标定 |
| **测量工具** | 卡尺测量、尺寸测量 |
| **识别工具** | 条码、二维码、OCR识别 |
| **通信工具** | TCP、串口、Modbus、WebSocket、IO控制 |
| **分析工具** | 斑点分析、像素计数、直方图 |
| **外观检测** | 外观检测器、表面缺陷检测器 |
| **标定工具** | 手动标定、棋盘格标定、圆点标定 |

### 🖥️ 用户界面

- **主窗口**: VisionMaster风格的专业界面
- **工具库**: 分类显示所有可用工具
- **算法编辑器**: 拖拽式可视化编程
- **属性面板**: 实时参数调节
- **结果面板**: 树形结构显示，支持展开/折叠
- **增强结果面板**: 多类型结果可视化、数据类型选择器
- **通信监控**: 实时连接状态监控

### 💾 方案管理

- **多格式支持**: JSON/YAML/Pickle/VMSOL
- **代码生成**: 自动生成可执行Python代码
- **文档导出**: 生成Markdown技术文档
- **方案打包**: 一键导出完整方案

### 🔄 运行控制

- **单次运行**: 执行一次完整流程
- **连续运行**: 定时循环执行流程
- **停止运行**: 立即停止连续运行

---

## 🏗️ 系统架构

```
应用层 (MainWindow) 
    ↓
核心层 (Solution/Procedure/SolutionFileManager)
    ↓  
工具层 (40+ Algorithm Tools)
    ↓
数据层 (ImageData/ResultData/ROI)
```

---

## 📁 项目结构

```
vision_system-opencode/
├── 📁 config/              # 配置文件
├── 📁 configs/             # 配置模板
├── 📁 core/                # 核心模块
│   ├── 📁 communication/   # 通讯模块
│   ├── memory_pool.py      # 内存池
│   ├── pipeline.py         # 确定性流水线
│   ├── procedure.py        # 流程管理
│   ├── solution.py         # 方案管理
│   └── tool_base.py        # 工具基类
├── 📁 data/                # 数据结构
├── 📁 documentation/       # 技术文档
├── 📁 docs/                # 用户文档
├── 📁 examples/            # 示例代码
├── 📁 modules/             # 功能模块
│   ├── 📁 camera/          # 相机模块
│   └── 📁 cpu_optimization/# CPU优化
├── 📁 tests/               # 测试代码
├── 📁 tools/               # 算法工具
│   ├── 📁 vision/          # 视觉工具
│   ├── 📁 communication/   # 通信工具
│   └── 📁 analysis/        # 分析工具
├── 📁 ui/                  # 用户界面
├── 📁 utils/               # 工具函数
├── 📄 requirements.txt     # 依赖文件
├── 📄 run.py               # 运行脚本
└── 📄 README.md            # 项目说明
```

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[README.md](README.md)** | 项目介绍和快速开始 |
| **[CHANGELOG.md](CHANGELOG.md)** | 更新日志 |
| **[documentation/INDEX.md](documentation/INDEX.md)** | 文档索引和导航 |
| **[documentation/ARCHITECTURE.md](documentation/ARCHITECTURE.md)** | 系统架构设计 |
| **[docs/performance_benchmark.md](docs/performance_benchmark.md)** | 性能基准测试报告 |
| **[AGENTS.md](AGENTS.md)** | AI Agent开发指南 |

---

## 🧪 测试验证

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行图像拼接测试
python -m tests.test_image_stitching

# 运行集成测试
python -m tests.test_integration
```

### 测试结果

```
✅ 方案文件管理器测试 - PASSED
✅ 通信模块增强测试 - PASSED  
✅ 通信监控面板测试 - PASSED
✅ 图像拼接功能测试 - PASSED
✅ 标定工具测试 - 8/8 passed
🎉 [SUCCESS] 所有案例测试通过！
```

---

## 🎯 使用示例

### 1. 图像拼接

```python
from tools.vision.image_stitching import ImageStitchingTool
from data.image_data import ImageData

# 创建工具
stitcher = ImageStitchingTool()

# 设置参数（中文）
stitcher.set_parameters({
    "性能模式": "balanced",      # fast/balanced/quality
    "快速预处理": True,
    "特征检测器": "ORB",        # ORB/SIFT/AKAZE
    "匹配器类型": "BFM",        # BFM/FLANN
})

# 执行拼接
result = stitcher.process([image_data1, image_data2])

if result.status:
    stitched = result.get_image("stitched_image")
    print(f"拼接成功！尺寸: {stitched.width}x{stitched.height}")
```

### 2. 通信配置

```python
# TCP通信配置
{
    "设备名称": "PLC_01",
    "协议类型": "TCP客户端",
    "目标IP": "192.168.1.100",
    "目标端口": 8080,
}

# 串口通信配置
{
    "设备名称": "传感器_01",
    "协议类型": "串口",
    "串口号": "COM1",
    "波特率": 9600,
}
```

---

## 🔧 技术亮点

### 1. 图像拼接优化

| 优化项 | 改进 | 效果 |
|--------|------|------|
| 检测器 | ORB替代SIFT | 10-20x速度提升 |
| 匹配 | BFMatcher + crossCheck | 更稳定 |
| 融合 | Sigmoid权重过渡 | 消除重影 |
| 预处理 | fast_mode | 减少计算 |

### 2. 性能优化

- **内存池**: 预分配缓冲区，118x分配速度提升
- **流水线**: 生产者-消费者模式，并行处理
- **向量化**: NumPy向量化计算，10-15x性能提升

### 3. 中文化实现

```python
# 所有参数完全中文化
tool_params = {
    "设备名称": "相机_01",
    "匹配分数": 0.8,
    "检测区域": "矩形ROI",
    "输出结果": "匹配位置"
}
```

---

## 📝 更新日志

### 2026-02-06 - 图像拼接优化

- ✅ **性能提升17倍**
  - ORB检测器替代SIFT
  - 优化特征点数量（800-3000）
  - 快速预处理模式
- ✅ **重影问题修复**
  - Sigmoid陡峭权重过渡
  - 几何一致性检查
- ✅ **新增参数**
  - 性能模式（快速/平衡/高质量）
  - 快速预处理选项
- ✅ **文档更新**
  - 更新AGENTS.md
  - 新增CHANGELOG.md
  - 更新性能基准报告

### 2026-02-05 - 通讯模块完善

- ✅ 修复发送数据工具参数保存问题
- ✅ 修复接收数据工具输入检查
- ✅ 支持特定字段发送

### 2026-02-03 - 性能优化

- ✅ 内存池 (ImageBufferPool) - 118x提升
- ✅ 确定性流水线 (DeterministicPipeline)
- ✅ 标定工具 - 8/8测试通过

[查看更多更新日志](CHANGELOG.md)

---

## 🐛 已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 方案导入 | ✅ 已修复 | 导入后自动加载到编辑器 |
| 图像拼接 | ✅ 已修复 | 性能提升17倍，无重影 |
| 通讯模块 | ✅ 已修复 | 发送/接收数据功能完善 |
| 相机参数 | ✅ 已修复 | 设置对话框功能完善 |
| 标定模块 | ⚠️ 案例测试 | 8/8 passed，未现场验证 |
| 外观检测 | ⚠️ 未测试 | 算法模块未实际测试 |
| 方案问题 | 未修复 | 先建立通讯然后建立方案流程能正常使用，先建立方案流程再建立通讯程序会卡顿 |


---

## 📄 许可证

MIT License

## 👥 作者

hzphzphzp

---

**注意**: 本项目为学习和研究目的，部分功能可能需要根据实际环境进行调整。
