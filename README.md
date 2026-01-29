# Vision System - 视觉检测系统

> 🎯 **海康VisionMaster V4.4.0的Python完整重构版本**  
> 📅 **项目完成时间**: 2026年1月29日  
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

## 🚀 快速开始

### 环境要求

```bash
Python 3.7+
PyQt5/PyQt6
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
| **图像处理** | 滤波、形态学、阈值、缩放、图像拼接 |
| **视觉算法** | 模板匹配、几何检测、斑点分析、YOLO26-CPU |
| **测量工具** | 卡尺测量、尺寸测量 |
| **识别工具** | 条码、二维码、OCR识别 |
| **通信工具** | TCP、串口、Modbus、WebSocket |
| **分析工具** | 斑点分析、像素计数、直方图 |

### 🖥️ 用户界面
- **主窗口**: VisionMaster风格的专业界面
- **工具库**: 分类显示所有可用工具
- **算法编辑器**: 拖拽式可视化编程
- **属性面板**: 实时参数调节
- **结果面板**: 树形结构显示，支持展开/折叠
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
├── 📁 ui/                  # 用户界面
│   ├── main_window.py     # 主窗口
│   ├── tool_library.py    # 工具库
│   ├── enhanced_result_panel.py  # 增强结果面板
│   └── ...                # 其他UI组件
├── 📁 core/                # 核心模块
│   ├── tool_base.py       # 工具基类
│   ├── solution.py        # 方案管理
│   ├── procedure.py       # 流程管理
│   └── tool_registry.py   # 工具注册器
├── 📁 tools/               # 算法工具
│   ├── image_source.py    # 图像源
│   ├── image_filter.py    # 图像处理
│   ├── image_stitching.py # 图像拼接
│   ├── analysis.py        # 分析工具
│   └── communication.py   # 通信工具
├── 📁 modules/             # 功能模块
│   ├── camera_manager.py  # 相机管理
│   └── cpu_optimization/  # CPU优化模块
├── 📁 data/                # 数据结构
│   ├── image_data.py      # 图像数据
│   └── result_data.py     # 结果数据
├── 📁 tests/               # 测试代码
│   ├── test_image_stitching.py  # 图像拼接测试
│   ├── test_stitching_consistency.py  # 拼接一致性测试
│   ├── test_tool_position_stability.py  # 工具位置稳定性测试
│   └── ...                # 其他测试文件
├── 📁 documentation/       # 技术文档
│   ├── PROJECT_DOCUMENTATION.md  # 项目综合文档
│   └── ...                # 其他文档
├── 📄 main.py             # 程序入口
├── 📄 requirements.txt    # 依赖文件
└── 📄 README.md           # 项目说明
```

## 📚 文档结构

| 文档 | 说明 |
|------|------|
| **[PROJECT_DOCUMENTATION.md](documentation/PROJECT_DOCUMENTATION.md)** | 项目综合文档 |
| **[ERROR_HANDLING_GUIDE.md](documentation/ERROR_HANDLING_GUIDE.md)** | 错误处理指南 |

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
| **集成测试** | test_integration.py | 系统集成测试 |

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

### 4. 设备集成
- **海康MVS SDK**: 完整相机功能支持，包括相机参数设置
- **相机参数设置**: 支持曝光时间、增益、gamma、分辨率、帧率、触发模式等参数配置
- **多协议通信**: 工业设备无缝对接
- **热插拔**: 设备动态识别和管理

### 5. 内存泄漏修复
- **斑点分析**: 限制blob数量，不存储完整轮廓数据
- **相机模块**: 共享相机管理器，图像缓冲区复制
- **结果面板**: 优化数据结构，避免数据累积

## 🐛 已知问题

1. **方案管理**: 方案保存/加载功能需要进一步完善
2. **导出代码功能**: 未在其它电脑测试 只在本地电脑测试
3. **性能监控**: 性能监控面板功能待完善

## 📝 更新日志

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
