# Vision System - 视觉检测系统

> 🎯 **海康VisionMaster V4.4.0的Python完整重构版本**  
> 📅 **项目完成时间**: 2026年1月30日  
> 🏆 **项目状态**: ✅ 完成并通过案例测试  
> 📊 **最新更新**: 2026年2月27日 - 新增图像切片工具

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
| **图像源** | 图像读取器、多图像选择器、相机采集、相机参数设置 |
| **图像处理** | 滤波、形态学、阈值、缩放、图像拼接、图像计算 |
| **视觉算法** | 模板匹配、几何检测、斑点分析、YOLO26-CPU、OCR、标定、图像切片 |
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

### 2026-02-26 - 通讯自动连接与ROI编辑器优化

#### 🚀 新增功能
- **通讯自动连接**
  - 方案加载后自动连接已配置的通讯项
  - 新增"自动连接"选项（默认开启）
  - 支持多通讯会话并存时同时连接

- **ROI编辑器实时预览**
  - 绘制ROI过程中实时显示预览框
  - 显示坐标和尺寸信息
  - 便于可视化调整

- **ROI编辑器模式切换**
  - 区分"绘制ROI模式"和"拖拽移动模式"
  - 支持图像缩放后拖拽移动
  - 模式切换保持图像位置

#### 🐛 Bug修复
- **通讯连接问题**
  - 修复保存设置后重新打开应用需要手动重连的问题

- **ROI编辑器问题**
  - 修复拖拽移动时ROI坐标计算错误

#### 📝 文档更新
- 新增 `CHANGELOG.md` - 更新日志（合并原RECENT_UPDATES.md内容）
- 更新 `documentation/INDEX.md`
- 更新 `documentation/PROJECT_OPTIMIZATION_GUIDE.md`
- 更新 `AGENTS.md` - 添加经验总结

---

### 2026-02-09 - 多图像选择器、条码识别与结果面板优化

#### 🚀 新增功能
- **多图像选择器工具**
  - 支持加载多张图片，一次性选择多文件
  - 提供上一张/下一张/跳转切换功能
  - 切换图片后自动运行流程
  - 循环模式支持
  - 完整中文参数界面

- **条码识别结果优化**
  - 将条码结果拆分为单独字段（code_data、code_type、code_x、code_y、code_width、code_height）
  - 支持在数据选择器中自由选择需要发送的特定字段

#### 🔧 优化改进
- **算法工具结果数据完善**
  - 为OCR、外观检测、标定、几何变换、图像保存等工具添加缺失的tool_name和result_category
  - 确保所有工具的结果都能正确显示在结果面板中

- **数据选择器字段翻译**
  - 添加条码、二维码、OCR、外观检测、标定等工具字段的中文翻译
  - 提升中文用户体验

#### 🐛 Bug修复
- **结果面板同步修复**
  - 修复删除算法模块后结果面板未同步的问题
  - 统一使用tool.name（实例名称）来添加和删除结果

- **条码识别结果显示异常**
  - 修复条码识别工具执行后结果面板不显示或显示异常的问题

- **日志与参数修复**
  - 修复日志记录中 filename 与 LogRecord 冲突问题
  - 修复 result_panel 日志 extra 参数冲突
  - 修复多图像选择器参数同步问题
  - 修复回调函数参数传递问题

#### 📝 文档更新
- 新增 TECHNICAL_DOCUMENTATION.md 综合技术文档
- 新增 MULTI_IMAGE_SELECTOR.md 多图像选择器使用说明
- 合并 TECHNICAL_DOCUMENT.md + PROJECT_DOCUMENTATION.md
- 合并 ERROR_RECORD.md → ERROR_HANDLING_GUIDE.md
- 更新 INDEX.md 文档索引和导航
- 更新 AGENTS.md 添加 5 个新错误记录 (#34-38)

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
| 方案问题 | ✅ 已修复 | 保存方案后能正常使用 |


---

## 📄 许可证

MIT License

## 👥 作者

hzphzphzp

---

**注意**: 本项目为学习和研究目的，部分功能可能需要根据实际环境进行调整。
