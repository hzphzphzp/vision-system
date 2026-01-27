# 视觉系统项目参考文档

## 项目概述

本项目是一个基于Python的视觉系统，旨在重构海康VisionMaster软件，提供类似的功能和性能。项目采用模块化架构，支持图像处理、目标检测、OCR识别、性能优化等功能。

### 项目状态

**当前状态：未完善**

- 核心功能已实现，但部分功能仍在开发中
- 存在一些已知问题和待优化的部分
- 欢迎社区贡献和反馈

## 目录结构

```
vision_system/
├── core/             # 核心模块
│   ├── communication/  # 通信模块
│   ├── __init__.py
│   ├── procedure.py    # 流程管理
│   ├── solution.py     # 解决方案管理
│   ├── tool_base.py    # 工具基类
│   └── zoomable_image.py # 可缩放图像组件
├── data/             # 数据处理模块
│   ├── __init__.py
│   └── image_data.py   # 图像数据处理
├── config/           # 配置管理
│   └── config_manager.py # 配置管理器
├── configs/          # 配置文件
│   ├── config.example.yaml
│   └── config.yaml
├── modules/          # 扩展模块
│   ├── cpu_optimization/ # CPU优化模块
│   ├── basler_camera.py  # Basler相机支持
│   ├── camera_adapter.py # 相机适配器
│   └── camera_manager.py # 相机管理器
├── tools/            # 工具实现
│   ├── __init__.py
│   ├── analysis.py      # 分析工具
│   ├── communication.py # 通信工具
│   ├── cpu_optimization.py # CPU优化工具
│   ├── enhanced_communication.py # 增强通信工具
│   ├── image_filter.py  # 图像过滤工具
│   ├── image_source.py  # 图像源工具
│   ├── ocr.py           # OCR识别工具
│   ├── recognition.py   # 识别工具
│   └── template_match.py # 模板匹配工具
├── ui/               # 用户界面
│   ├── __init__.py
│   ├── communication_config.py # 通信配置
│   ├── communication_dialog.py # 通信对话框
│   ├── communication_monitor.py # 通信监控
│   ├── cpu_optimization_dialog.py # CPU优化对话框
│   ├── enhanced_result_dock.py # 增强结果面板
│   ├── enhanced_result_panel.py # 增强结果面板
│   ├── main_window.py   # 主窗口
│   ├── project_browser.py # 项目浏览器
│   ├── property_panel.py # 属性面板
│   ├── result_panel.py  # 结果面板
│   ├── roi_selection_dialog.py # ROI选择对话框
│   ├── theme.py         # 主题管理
│   └── tool_library.py  # 工具库
├── utils/            # 工具函数
│   ├── __init__.py
│   ├── error_management.py # 错误管理
│   └── performance_optimization.py # 性能优化
├── documentation/    # 文档
│   ├── ERROR_HANDLING_GUIDE.md # 错误处理指南
│   ├── PROJECT_DOCUMENTATION.md # 项目文档
│   ├── PROJECT_REFERENCE.md # 项目参考
│   ├── PROJECT_SUMMARY.md # 项目摘要
│   └── SKILL_USAGE_GUIDE.md # 技能使用指南
├── examples/         # 示例代码
│   ├── config_usage_example.py # 配置使用示例
│   └── polars_optimization_example.py # Polars优化示例
├── tests/            # 测试代码
├── professional_app.py # 专业应用
├── requirements.txt  # 依赖项
├── run.py            # 运行脚本
└── README.md         # 项目说明
```

## 核心功能模块

### 1. 图像处理

- **图像加载和保存**：支持多种图像格式
- **图像变换**：缩放、旋转、翻转等
- **图像过滤**：模糊、锐化、边缘检测等
- **ROI操作**：区域选择、裁剪、标注

### 2. 目标检测

- **YOLO26模型**：使用最新的YOLO26模型进行目标检测
- **自定义模型支持**：允许加载自定义训练的模型
- **多类别检测**：支持同时检测多种目标
- **实时检测**：优化的推理速度

### 3. OCR识别

- **文本检测**：定位图像中的文本区域
- **文本识别**：识别检测到的文本内容
- **多语言支持**：支持多种语言的文本识别
- **结果导出**：支持将识别结果导出为多种格式

### 4. 性能优化

- **CPU优化**：针对CPU环境的性能优化
- **内存管理**：内存池和张量池管理
- **并行处理**：多线程和并行计算
- **SIMD优化**：利用CPU的SIMD指令加速计算

### 5. 通信功能

- **TCP/IP通信**：支持TCP客户端和服务器
- **Modbus TCP**：支持Modbus协议
- **串口通信**：支持RS-232/485串口通信
- **WebSocket**：支持WebSocket通信
- **HTTP客户端**：支持HTTP请求

#### 通信模块实现状态

- **核心实现**：已完成，包含所有通信协议的基本功能
- **配置界面**：已实现，支持通过UI配置通信参数
- **测试状态**：已创建测试用例（tests/test_communication.py），但尚未进行全面测试
- **稳定性**：部分通信协议的稳定性需要进一步改进

#### 通信模块使用指南

1. **打开通信配置**：点击"工具" -> "通信配置"
2. **添加连接**：点击"添加"按钮，选择通信协议类型
3. **配置参数**：根据选择的协议类型填写相应的配置参数
4. **测试连接**：点击"测试"按钮验证连接是否正常
5. **保存配置**：点击"保存"按钮保存配置
6. **使用连接**：在流程中使用通信工具发送和接收数据

### 6. 配置管理

- **YAML/JSON配置**：支持多种配置文件格式
- **配置验证**：自动验证配置参数的有效性
- **配置热加载**：支持运行时修改配置
- **配置备份**：自动备份配置文件

### 7. 用户界面

- **PyQt5界面**：基于PyQt5的现代化界面
- **拖拽操作**：支持拖拽添加工具和组件
- **实时预览**：实时显示图像处理结果
- **性能监控**：实时显示系统性能指标
- **主题支持**：支持多种界面主题

## 技术栈

- **Python 3.8+**：主要开发语言
- **PyQt5**：用户界面库
- **OpenCV**：图像处理库
- **NumPy**：科学计算库
- **Polars**：高性能数据处理库
- **YOLO26**：目标检测模型
- **PySerial**：串口通信
- **psutil**：系统资源监控

## 依赖项

项目依赖项已在`requirements.txt`文件中列出，包括：

- PyQt5
- opencv-python
- numpy
- polars
- pyserial
- psutil
- pyyaml

## 安装和运行

### 安装

1. 克隆项目仓库
2. 安装依赖项：`pip install -r requirements.txt`
3. 运行应用程序：`python run.py`

### 运行模式

- **开发模式**：`python run.py --dev`
- **测试模式**：`python run.py --test`
- **生产模式**：`python run.py --prod`

## 使用指南

### 基本工作流程

1. **创建解决方案**：点击"文件" -> "新建解决方案"
2. **添加工具**：从工具库拖拽工具到流程画布
3. **配置工具**：在属性面板中配置工具参数
4. **运行流程**：点击"运行"按钮执行流程
5. **查看结果**：在结果面板中查看处理结果
6. **保存解决方案**：点击"文件" -> "保存解决方案"

### 工具使用

#### 图像源工具

- **功能**：加载图像文件或从相机获取图像
- **参数**：
  - `source_type`：图像源类型（文件/相机）
  - `file_path`：图像文件路径
  - `camera_id`：相机ID

#### 目标检测工具

- **功能**：使用YOLO26模型检测目标
- **参数**：
  - `model_path`：模型文件路径
  - `conf_threshold`：置信度阈值
  - `nms_threshold`：非极大值抑制阈值

#### OCR工具

- **功能**：检测和识别图像中的文本
- **参数**：
  - `lang`：语言类型
  - `text_only`：是否只返回文本
  - `detect_only`：是否只检测文本区域

#### 分析工具

- **功能**：分析图像或检测结果
- **参数**：
  - `analysis_type`：分析类型
  - `threshold`：阈值
  - `output_format`：输出格式

### 性能优化

#### CPU优化

1. **打开CPU优化配置**：点击"工具" -> "CPU优化配置"
2. **线程配置**：设置使用的线程数
3. **内存配置**：配置内存池大小
4. **SIMD优化**：查看和启用SIMD优化

#### 性能监控

1. **打开性能监控**：点击"视图" -> "性能监控"
2. **实时指标**：查看CPU利用率、内存占用、推理速度等
3. **统计信息**：查看推理次数、平均推理时间等统计数据

## 配置管理

### 配置文件结构

配置文件采用YAML格式，主要包含以下部分：

```yaml
# 应用配置
application:
  name: "Vision System"
  version: "1.0.0"
  debug: false

# 相机配置
camera:
  default_camera: 0
  capture_width: 1280
  capture_height: 720
  fps: 30

# 性能配置
performance:
  thread_count: 4
  memory_pool_size: 512
  simd_optimization: true

# 通信配置
communication:
  tcp_server:
    host: "0.0.0.0"
    port: 5000
  modbus:
    host: "127.0.0.1"
    port: 502
```

### 配置使用示例

```python
from config.config_manager import ConfigManager

# 加载配置
config = ConfigManager()
config.load_config("configs/config.yaml")

# 获取配置
thread_count = config.get("performance.thread_count", 4)
camera_id = config.get("camera.default_camera", 0)

# 修改配置
config.set("performance.thread_count", 8)

# 保存配置
config.save_config("configs/config.yaml")
```

## 开发指南

### 代码风格

- 遵循PEP 8代码风格
- 使用4空格缩进
- 类名使用驼峰命名法
- 函数和变量名使用下划线分隔
- 模块名使用小写字母

### 测试

- 测试代码放在`tests/`目录下
- 使用pytest进行测试
- 运行测试：`pytest tests/`

### 贡献流程

1. Fork项目仓库
2. 创建特性分支
3. 提交修改
4. 创建Pull Request
5. 等待代码审查

## 已知问题

1. **图像缩放问题**：使用鼠标滚轮缩放图像时可能会出现模糊
2. **CPU优化模块**：部分功能可能无法在所有系统上正常工作
3. **通信模块**：某些通信协议的稳定性需要进一步改进
4. **内存管理**：在处理大量图像时可能会出现内存占用过高

## 待开发功能

1. **GPU支持**：添加GPU加速支持
2. **深度学习模型**：集成更多深度学习模型
3. **3D视觉**：添加3D视觉支持
4. **工业相机支持**：支持更多工业相机型号
5. **自动化流程**：添加流程自动化和脚本支持
6. **云服务集成**：集成云存储和计算服务

## 故障排除

### 常见错误

1. **无法导入模块**
   - 检查依赖项是否已安装
   - 检查Python路径是否正确

2. **相机连接失败**
   - 检查相机是否已连接
   - 检查相机驱动是否已安装
   - 检查相机ID是否正确

3. **模型加载失败**
   - 检查模型文件路径是否正确
   - 检查模型文件是否完整
   - 检查模型格式是否支持

4. **性能问题**
   - 调整线程数和内存池大小
   - 启用SIMD优化
   - 考虑使用更小的模型

### 日志管理

- 日志文件：`app.log`
- 日志级别：可在配置文件中设置
- 查看日志：使用文本编辑器打开`app.log`文件

## 联系和支持

### 项目维护者

- **名称**：hzphzphzp
- **邮箱**：1916164064@qq.com

### 反馈和贡献

- 如有问题或建议，请创建Issue
- 欢迎提交Pull Request
- 如需更多帮助，请发送邮件至维护者邮箱

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 致谢

- 感谢海康VisionMaster团队的启发
- 感谢Ultralytics提供的YOLO26模型
- 感谢所有贡献者和支持者

---

**注意**：本项目仍在开发中，部分功能可能会有所变化。请参考最新的代码和文档。