# Vision System - 视觉检测系统

> 🎯 **海康VisionMaster V4.4.0的Python完整重构版本**  
> 📅 **项目完成时间**: 2026年1月30日  
> 🏆 **项目状态**: ✅ 完成并通过案例测试

## 🌟 项目特色

- 🏗️ **模块化架构**: 四层架构设计，松耦合高内聚
- 🖱️ **可视化编程**: 拖拽式工具连接，所见即所得
- 🌏 **完整中文化**: 界面和参数全面中文化
- 🔌 **工业级通信**: 支持TCP/串口/Modbus/WebSocket等协议
- 💾 **方案管理**: 保存/加载/导出完整方案
- 📊 **结果可视化**: 多种数据类型实时显示
- 🎥 **设备集成**: 海康机器人/OpenCV相机支持
- 🚀 **代码生成**: 自动生成可执行Python代码
- 🔄 **连续运行**: 支持单次/连续运行模式
- 🛡️ **内存优化**: 修复多处内存泄漏问题
- 📷 **图像拼接**: 支持任意顺序图像拼接，智能融合
- 🎯 **YOLO26-CPU**: 高性能目标检测，支持CPU优化
- ⚡ **性能优化**: __slots__内存优化，**内存池** + **确定性流水线**
- 🔁 **内存池 (ImageBufferPool)**: 预分配固定大小图像内存，避免频繁malloc/free，提升118x分配速度
- 📋 **确定性流水线 (DeterministicPipeline)**: 生产者-消费者模式，严格顺序处理，无共享状态

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
- **增强结果面板**: 多类型结果可视化、数据类型选择器、多模块数据连接、数据导出
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

## 📁 项目结构

```
vision_system-opencode/
├── 📁 config/              # 配置文件
├── 📁 configs/             # 配置模板
├── 📁 core/                # 核心模块
│   ├── 📁 communication/   # 通讯模块 (TCP/串口/Modbus/WebSocket)
│   ├── memory_pool.py      # 图像缓冲区内存池 (NEW)
│   ├── pipeline.py         # 确定性图像处理流水线 (NEW)
│   ├── procedure.py        # 流程管理
│   ├── roi_tool_mixin.py   # ROI工具混入
│   ├── solution.py         # 方案管理
│   ├── solution_file_manager.py # 方案文件管理
│   ├── tool_base.py        # 工具基类
│   └── zoomable_image.py   # 可缩放图像组件
├── 📁 data/                # 数据结构
│   ├── image_data.py       # 图像数据
│   ├── result_data.py      # 结果数据
│   └── 📁 models/          # 模型文件
├── 📁 documentation/       # 技术文档
│   ├── ARCHITECTURE.md     # 系统架构设计 (NEW)
│   ├── INDEX.md            # 文档导航索引 (NEW)
│   ├── ERROR_HANDLING_GUIDE.md   # 错误处理指南
│   ├── PROJECT_DOCUMENTATION.md  # 项目综合文档
│   ├── PROJECT_OPTIMIZATION_GUIDE.md # 优化指南
│   ├── TECHNICAL_DOCUMENT.md     # 技术文档
│   └── ...                # 其他文档
├── 📁 docs/                # 用户文档
│   ├── edge_algorithms.md  # 边缘设备AI算法推荐
│   └── 📁 plans/           # 实施计划
├── 📁 examples/            # 示例代码
├── 📁 modules/             # 功能模块
│   ├── 📁 camera/          # 相机模块
│   │   ├── camera_manager.py   # 相机管理
│   │   ├── camera_adapter.py   # 相机适配器
│   │   └── basler_camera.py    # Basler相机
│   └── 📁 cpu_optimization/    # CPU优化模块
│       ├── 📁 api/         # API接口
│       ├── 📁 core/        # 核心优化引擎
│       ├── 📁 models/      # YOLO26-CPU模型
│       └── 📁 utils/       # 性能监控
├── 📁 tests/               # 测试代码
│   ├── test_calibration.py # 标定工具测试 (NEW)
│   ├── test_memory_pool.py # 内存池测试 (NEW)
│   ├── test_pipeline.py    # 流水线测试 (NEW)
│   ├── test_integration.py # 集成测试
│   ├── test_image_stitching.py # 图像拼接测试
│   └── ...                 # 其他测试文件
├── 📁 tools/               # 算法工具 (子包结构)
│   ├── 📁 vision/          # 视觉工具
│   │   ├── calibration.py  # 标定工具 (NEW)
│   │   ├── template_match.py   # 模板匹配
│   │   ├── image_filter.py     # 图像滤波
│   │   ├── image_stitching.py  # 图像拼接
│   │   ├── image_calculation.py# 图像计算
│   │   ├── appearance_detection.py # 外观检测
│   │   ├── ocr.py          # OCR识别
│   │   ├── recognition.py  # 条码/二维码识别
│   │   └── cpu_optimization.py # CPU优化工具
│   ├── 📁 communication/   # 通信工具
│   │   ├── communication.py    # 通信基类
│   │   ├── enhanced_communication.py # 增强通信
│   │   └── io_control.py       # IO控制
│   ├── 📁 analysis/        # 分析工具
│   │   └── analysis.py     # 斑点分析、卡尺测量
│   ├── image_source.py     # 图像源
│   └── camera_parameter_setting.py # 相机参数设置
├── 📁 ui/                  # 用户界面
│   ├── main_window.py      # 主窗口
│   ├── tool_library.py     # 工具库
│   ├── property_panel.py   # 属性面板
│   ├── result_panel.py     # 结果面板
│   ├── enhanced_result_panel.py  # 增强结果面板 (NEW)
│   ├── communication_config.py   # 通信配置
│   ├── communication_dialog.py   # 通信对话框
│   ├── cpu_optimization_dialog.py# CPU优化对话框
│   ├── qt_compat.py        # Qt兼容性层
│   └── ...                 # 其他UI组件
├── 📁 utils/               # 工具函数
│   ├── error_management.py # 错误管理
│   ├── exceptions.py       # 异常定义
│   ├── image_filter_utils.py   # 图像滤波工具
│   └── performance_optimization.py # 性能优化
├── 📄 professional_app.py  # 专业应用
├── 📄 requirements.txt     # 依赖文件
├── 📄 run.py               # 运行脚本
└── 📄 README.md            # 项目说明
```

## 📚 文档结构

| 文档 | 说明 |
|------|------|
| **[README.md](README.md)** | 项目介绍和快速开始 |
| **[documentation/INDEX.md](documentation/INDEX.md)** | 文档索引和导航 (NEW) |
| **[documentation/ARCHITECTURE.md](documentation/ARCHITECTURE.md)** | 系统架构设计 (NEW) |
| **[docs/performance_benchmark.md](docs/performance_benchmark.md)** | 性能优化基准测试报告 |
| **[documentation/PROJECT_DOCUMENTATION.md](documentation/PROJECT_DOCUMENTATION.md)** | 项目综合文档 |
| **[documentation/ERROR_HANDLING_GUIDE.md](documentation/ERROR_HANDLING_GUIDE.md)** | 错误处理指南 |
| **[documentation/PROJECT_OPTIMIZATION_GUIDE.md](documentation/PROJECT_OPTIMIZATION_GUIDE.md)** | 项目优化指南 |
| **[documentation/TECHNICAL_DOCUMENT.md](documentation/TECHNICAL_DOCUMENT.md)** | 技术文档 |
| **[AGENTS.md](AGENTS.md)** | AI Agent开发指南 |

## 🧪 测试验证

### 测试代码结构
所有测试代码统一存放在 `tests/` 文件夹中，按功能分类组织：

| 测试类别 | 测试文件 | 说明 |
|---------|---------|------|
| **图像拼接** | test_image_stitching.py | 图像拼接功能测试 |
| | test_stitching_consistency.py | 拼接一致性测试 |
| | test_stitching_fix.py | 拼接修复测试 |
| **工具位置** | test_tool_position_stability.py | 工具位置稳定性测试 |
| | test_position_sensitivity.py | 位置敏感性测试 |
| **相机功能** | test_camera.py | 相机功能测试 |
| | test_camera_parameter_setting.py | 相机参数设置测试 |
| | test_camera_connection.py | 相机连接测试 |
| **YOLO26** | test_yolo26.py | YOLO26功能测试 |
| | test_yolo26_new.py | YOLO26新功能测试 |
| **外观检测** | test_appearance_detection.py | 外观检测功能测试 |
| **性能优化** | test_memory_pool.py | 内存池测试 |
| | test_image_data_pool.py | ImageData内存池集成测试 |
| | test_pipeline.py | 流水线框架测试 |
| | test_solution_pipeline.py | Solution流水线集成测试 |
| **集成测试** | test_integration.py | 系统集成测试 |
| **标定工具** | test_calibration.py | 标定工具测试 (8/8 passed) |

### 运行测试

```bash
# 运行集成测试
python -m tests.test_integration

# 运行图像拼接测试
python -m tests.test_image_stitching

# 运行拼接一致性测试
python -m tests.test_stitching_consistency

# 运行所有测试
python -m pytest tests/ -v
```

### 测试结果

```
✅ 方案文件管理器测试 - PASSED
✅ 通信模块增强测试 - PASSED  
✅ 通信监控面板测试 - PASSED
✅ 图像拼接功能测试 - PASSED
✅ 工具位置稳定性测试 - PASSED
🎉 [SUCCESS] 所有案例测试通过！
```

## 🎯 使用示例

### 1. 创建视觉检测流程

```python
# 1. 拖拽工具到算法编辑器
图像读取器 → 灰度匹配 → 条码识别 → 数据发送

# 2. 设置参数
- 图像读取器: 选择相机或本地图片
- 灰度匹配: 上传模板，设置匹配阈值
- 条码识别: 选择条码类型
- 数据发送: 配置通信协议

# 3. 运行测试
点击"单次运行"查看结果
点击"连续运行"循环执行
点击"停止运行"停止循环

# 4. 导出方案
文件 → 导出方案包 → 生成完整代码
```

### 2. 图像拼接示例

```python
from tools.image_stitching import ImageStitchingTool
from data.image_data import ImageData
import cv2

# 创建图像拼接工具
stitcher = ImageStitchingTool()

# 设置参数
stitcher.set_parameters({
    "feature_detector": "SIFT",    # 选择特征点检测器
    "matcher_type": "BFM",        # 选择匹配器类型
    "blend_method": "multi_band",  # 选择融合方法
    "blend_strength": 1,           # 融合强度
    "parallel_processing": False   # 禁用并行处理
})

# 加载测试图像
img1 = cv2.imread("A1.jpg")
img2 = cv2.imread("A2.jpg")

# 创建ImageData对象
image_data1 = ImageData(data=img1)
image_data2 = ImageData(data=img2)

# 执行拼接（任意顺序）
result = stitcher.process([image_data1, image_data2])

# 获取拼接结果
if result.status:
    stitched_image = result.get_image("stitched_image")
    if stitched_image:
        cv2.imwrite("stitched_result.jpg", stitched_image.data)
        print(f"拼接成功！输出尺寸: {stitched_image.width}x{stitched_image.height}")
```

### 3. 通信配置示例

```python
# TCP通信配置
SendData工具参数:
{
    "设备名称": "PLC_01",
    "协议类型": "TCP客户端",
    "目标IP": "192.168.1.100",
    "目标端口": 8080,
    "波特率": 9600,
    "发送数据": "检测结果"
}

# 串口通信配置  
ReceiveData工具参数:
{
    "设备名称": "传感器_01",
    "协议类型": "串口",
    "串口号": "COM1",
    "波特率": 9600,
    "数据位": 8,
    "停止位": 1,
    "数据过滤": True
}
```

## 🔧 技术亮点

### 1. 中文化实现
```python
# 所有参数完全中文化
tool_params = {
    "设备名称": "相机_01",
    "匹配分数": 0.8,
    "检测区域": "矩形ROI",
    "输出结果": "匹配位置"
}
```

### 2. 图像拼接技术
- **任意顺序拼接**: 智能排序，支持任意输入顺序
- **双向特征匹配**: 提高匹配精度和鲁棒性
- **智能融合**: 自适应融合强度，根据场景自动调整
- **镜像检测**: 自动检测和校正镜像问题


****注意：目前只测试了两张图片的顺序调换拼接，输出一致的图像，并没测试多张图片****

### 3. 性能优化
- **向量化计算**: 灰度匹配性能提升10-15倍
- **图像缓存**: 避免重复处理，提升响应速度
- **内存管理**: 修复斑点分析、相机模块内存泄漏
- **QTimer**: 使用Qt定时器实现连续运行，避免线程安全问题
- **内存池 (ImageBufferPool)**: 预分配图像缓冲区，提升118x分配速度
- **确定性流水线 (DeterministicPipeline)**: 多线程并行处理，保证结果一致性

### 4. 设备集成
- **海康MVS SDK**: 完整相机功能支持，包括相机参数设置
- **相机参数设置**: 支持曝光时间、增益、gamma、分辨率、帧率、触发模式等参数配置
- **多协议通信**: 工业设备无缝对接
- **热插拔**: 设备动态识别和管理

### 5. 增强结果面板
- **多类型结果展示**: 支持条码识别、目标检测、匹配分析、测量、Blob分析、OCR等多种结果类型
- **数据类型选择器**: 动态选择要查看的数据类型（图像、数值、字符串等）
- **多模块数据连接**: 支持连接不同模块的输出数据
- **结果可视化**: 图形化展示检测结果（矩形框、标注等）
- **数据导出**: 支持CSV、JSON格式导出结果数据
- **实时更新**: 相同模块结果自动更新，避免重复显示

### 6. 内存泄漏修复
- **斑点分析**: 限制blob数量，不存储完整轮廓数据
- **相机模块**: 共享相机管理器，图像缓冲区复制
- **结果面板**: 优化数据结构，避免数据累积

## 🐛 已知问题

1. **方案管理**: ✅ 已修复 - 方案导入后自动加载到编辑器
2. **导出代码功能**: 未在其它电脑测试，只在本地电脑测试
3. **性能监控**: 性能监控面板功能待完善
4. **新增外观缺陷和表面缺陷检测**： 两个算法模块并未实际测试
5. **标定模块**: 仅通过案例测试 (test_calibration.py 8/8 passed)，未进行实际现场测试验证
6. **结果面板**: ✅ 已修复 - 算法结果无法根据模块显示
7. **拖拽算法模块**: ✅ 已修复 - 多次拖拽位置精确跟随鼠标
8. **数据模块**: 发送数据和接收数据功能任不完善
9. **相机参数设置**: ✅ 已修复 - 相机设置对话框功能已完善
10. **图像计算归一化**: ✅ 已修复 - 相同图像归一化后显示灰色而非黑色
11. **流程标签同步**: ✅ 已修复 - 橙色流程标签随流程切换自动更新
12. **导入顺序规范化**: ✅ 已修复 - 38个文件导入顺序优化
13. **Qt兼容性问题**: ✅ 已解决 - 添加PySide6兼容性层
14. **通讯模块**： ✅ 已修复 - 发送数据/接收数据功能已完善
    - 修复属性面板下拉框参数保存问题
    - 修复数据内容选择器信号连接问题
    - 支持选择特定字段发送（如只发送Width值）
    - 修复接收数据工具输入检查问题
    - 统一连接列表格式（device_id: display_name）


## 📝 更新日志

### 2026-02-05
- ✅ **通讯模块功能完善**
  - 修复发送数据工具参数保存问题
    - 修复`QComboBox`信号连接，从`currentTextChanged`改为`currentIndexChanged`
    - 添加`activated`信号作为用户手动选择的备用信号
    - 修复`DataContentSelector`信号未连接问题
  - 优化数据发送逻辑
    - 支持根据用户选择发送特定字段（如只发送`Width: 3072`）
    - 修复`_collect_input_data()`方法，提取特定字段而非发送全部数据
  - 增强调试日志
    - 添加属性面板控件创建日志
    - 添加参数变更追踪日志
    - 添加工具执行参数检查日志
  - 修复接收数据工具
    - 添加`_check_input()`方法重写，解决"输入数据无效"错误
    - 统一`_get_available_connections()`格式为`device_id: display_name`
    - 增强`_get_connection_by_display_name()`支持多种连接ID格式
  - 测试验证：发送数据/接收数据功能正常运行

### 2026-02-03
- ✅ **性能优化: 内存池 + 确定性流水线**
  - 新增 `core/memory_pool.py` - ImageBufferPool 内存池
    - 预分配固定大小图像内存，避免频繁malloc/free
    - 线程安全，使用Queue实现缓冲区管理
    - 使用id()跟踪使用中缓冲区
    - 性能提升: **118x** 内存分配速度
  - 新增 `core/pipeline.py` - DeterministicPipeline 流水线
    - 生产者-消费者模式，严格顺序处理
    - 每个阶段独立线程，无共享状态
    - 队列大小限制，防止内存爆炸
    - 自动帧ID管理，保持处理顺序
  - 集成到 `ImageData` - 自动使用内存池，析构时自动释放
  - 集成到 `Solution` - `enable_pipeline_mode(buffer_size=N)` 启用流水线
  - 新增测试: 10/10 tests passed
- ✅ ImageData __slots__内存优化 - 创建速度提升11%，复制速度提升29%
- ✅ 新建PySide6兼容性层 (ui/qt_compat.py)
  - 统一PyQt5/PyQt6/PySide6 API
  - 自动检测最佳Qt后端
  - 解决导入冲突问题
- ✅ 修复38个文件的导入顺序规范化
- ✅ 修复流程管理功能
  - 新建/删除流程正常工作
  - 橙色流程标签随切换自动更新
  - 工具在不同流程间隔离保存
- ✅ 所有核心测试通过 (17/17 tests passed)
- ✅ 新增标定工具 (tools/vision/calibration.py)
  - 支持手动标定、棋盘格标定、圆点标定
  - 像素坐标与物理尺寸相互转换
  - 多单位支持 (mm/inch/um)
  - 测试用例: 8/8 passed (仅案例测试，未现场验证)

### 2026-02-02
- ✅ 修复方案导入功能 - 导入后自动加载到编辑器
- ✅ 添加图像计算工具 (tools/vision/image_calculation.py)
  - 支持加法、减法、乘法、除法、绝对差、加权融合、逻辑运算
  - 提供快捷工具：图像加法、图像减法、图像融合
  - 修复归一化问题 - 相同图像显示灰色而非黑色
- ✅ 修复相机参数设置对话框 - 完善参数同步和应用功能
- ✅ 修复拖拽算法模块位置偏移问题 - 精确跟随鼠标
- ✅ 更新YOLO26-CPU参数说明 - 标注为IOU阈值(NMS)
- ✅ 更新AGENTS.md开发文档
- ✅ 添加edge_algorithms.md - 边缘设备AI算法推荐文档
- ✅ 所有核心测试通过 (17/17 tests passed)

### 2026-01-30
- ✅ 修复方案导入功能 - 导入后自动加载到编辑器
- ✅ 修复相机参数设置对话框 - 完善参数同步和应用功能
- ✅ 更新AGENTS.md开发文档

### 2026-01-30
- ✅ 开发新功能外观检测，包含外观检测器和表面缺陷检测器
- ✅ 改进技能调用流程，使用标准接口
- ✅ 集成新功能到主界面
- ✅ 创建新的UI集成技能，用于测试通过后自动UI集成
- ✅ 创建新的测试管理技能，确保测试用例存储在tests/目录中
- ✅ 优化技能编排系统，实现动态配置和热更新功能
- ✅ 执行代码质量检查和格式化，使用Flake8、Black和isort
- ✅ 修复多个undefined name错误和其他代码问题
- ✅ 实现统一的配置文件结构和管理系统
- ✅ 优化性能，包括Polars数据处理、并行计算和缓存机制
- ✅ 完成代码复用与模块化优化
- ✅ 创建图像处理工具函数库 (utils/image_processing_utils.py)
- ✅ 优化相机模块目录结构 (modules/camera/)
- ✅ 重构工具模块为子包结构 (vision/communication/analysis)
- ✅ 修复相机软触发失败问题，增加重试机制
- ✅ 更新所有相关文档，反映代码结构变化
- ✅ 清理不需要的文档文件，保持文档结构清晰
- ✅ 验证所有功能正常运行，集成测试通过

### 2026-01-29
- ✅ 优化结果面板布局（图像:属性:结果 = 5:4:1）
- ✅ 简化结果面板UI，使用树形结构显示
- ✅ 修复连续运行线程安全问题（使用QTimer）
- ✅ 修复斑点分析内存泄漏
- ✅ 修复相机模块内存泄漏
- ✅ 修复UI布局重复问题
- ✅ 完善图像拼接功能，支持任意顺序拼接
- ✅ 优化YOLO26-CPU性能

### 2026-01-28
- ✅ 完成核心功能开发
- ✅ 集成测试通过
- ✅ 文档编写完成

## 📄 许可证

MIT License

## 👥 作者

hzphzphzp

---

**注意**: 本项目为学习和研究目的，部分功能可能需要根据实际环境进行调整。
