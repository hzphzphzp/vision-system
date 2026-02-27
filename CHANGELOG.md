# 更新日志 (Changelog)

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布] - 2026-02-27

### 🚀 新增功能

- **图像切片工具 (ImageSliceTool)**
  - 对匹配目标进行精确切片处理
  - 支持从上游工具（如灰度匹配）获取匹配结果
  - 支持两种切片模式：提取（保留区域）/去除（删除区域）
  - 支持多结果浏览，通过"结果索引"切换
  - 新增"运行后递增"功能，每次运行自动切换到下一个结果
  - 文件: `tools/vision/image_slice.py`, `ui/tool_library.py`

- **属性面板自动刷新**
  - 图像切片工具运行后自动刷新属性面板显示更新后的索引
  - 文件: `ui/main_window.py`

### 🐛 错误修复

- **工具注册问题**
  - 修复新建工具未注册到系统的问题
  - 原因: 未在 `tools/vision/__init__.py` 中导入新工具

- **参数定义错误**
  - 修复 `option_labels` 参数错误
  - 原因: 在 `set_param()` 中使用了 `option_labels`，应使用 `PARAM_DEFINITIONS`

- **上游数据获取错误**
  - 修复获取上游数据方法不存在的问题
  - 原因: 使用了错误的方法名 `get_input_data_recursive()`

- **匹配数据格式错误**
  - 修复 tuple 格式匹配数据无法处理的问题
  - 原因: 灰度匹配返回 tuple 格式 `[(x,y,score),...]`，需要转换为 dict

- **属性面板不刷新**
  - 修复运行后属性面板参数不更新的问题
  - 原因: 需要手动调用 `update_parameter()` 刷新UI

### 📝 文档更新

- 更新 `AGENTS.md` - 添加图像切片工具开发经验总结（第42节）

---

### 🚀 性能优化集成

- **新增性能优化模块**
  - `core/parallel_processing.py` - joblib多进程并行处理
  - `core/numba_utils.py` - Numba JIT编译加速函数
  - `core/image_utils.py` - 快速图像I/O操作

- **工具集成优化**
  - `tools/image_source.py` - 集成快速图像加载
  - `tools/vision/image_saver.py` - 集成快速图像保存
  - `tools/vision/template_match.py` - 集成Numba加速（SSD模式）

### 🐛 错误修复

- **语法错误**
  - 修复 `template_match.py` 导入语句语法错误
  - 原因: 在try/except块后意外删除了import语句的闭合括号

- **图像色彩问题**
  - 修复优化后保存图像偏蓝的问题
  - 原因: Pillow使用RGB格式，OpenCV使用BGR格式，需要转换

### 📝 文档更新

- 更新 `AGENTS.md` - 添加性能优化集成经验总结（第43节）

---

## [未发布] - 2026-02-26

### 🚀 新增功能

- **通讯自动连接**
  - 方案加载后自动连接已配置的通讯项
  - 新增"自动连接"选项（默认开启）
  - 支持多通讯会话并存时同时连接
  - 文件: `ui/communication_config.py`

- **ROI编辑器实时预览**
  - 绘制ROI过程中实时显示预览框
  - 显示坐标和尺寸信息
  - 便于可视化调整
  - 文件: `ui/roi_selection_dialog.py`

- **ROI编辑器模式切换**
  - 区分"绘制ROI模式"和"拖拽移动模式"
  - 支持图像缩放后拖拽移动
  - 模式切换保持图像位置

### 🐛 错误修复

- **通讯连接问题**
  - 修复保存设置后重新打开应用需要手动重连的问题
  - 问题原因: `load_from_solution()` 加载配置后未触发自动连接

- **ROI编辑器问题**
  - 修复拖拽移动时ROI坐标计算错误
  - 修复 QPointF 未定义错误
  - 修复 _offset_x 属性不存在错误

### 📝 文档更新

- 新增 `documentation/RECENT_UPDATES.md`
- 更新 `documentation/INDEX.md`
- 更新 `documentation/PROJECT_OPTIMIZATION_GUIDE.md`
- 更新 `AGENTS.md` - 添加经验总结

---

## [未发布] - 2026-02-06

### 🚀 新增功能

- **图像拼接性能模式** - 添加三种性能模式：快速/平衡/高质量
  - 快速模式：ORB检测器，800特征点，0.03秒完成
  - 平衡模式：ORB检测器，1500特征点，0.03秒完成
  - 高质量模式：SIFT检测器，3000特征点，0.46秒完成
- **快速预处理选项** - 可选择启用/禁用快速预处理模式
- **性能监控** - 添加详细的步骤时间记录（特征检测、排序、拼接）
- **新增工具** - 几何变换和图像保存工具
  - 几何变换：支持旋转、缩放等几何操作
  - 图像保存：支持多种格式（PNG/JPG/BMP/TIFF）和自动命名

### 🔧 优化改进

- **图像拼接性能提升17倍**
  - 默认使用ORB替代SIFT（快10-20倍）
  - 优化特征点数量（根据模式800-3000）
  - 减少金字塔层数（从8层降至4-6层）
  - 使用BFMatcher替代FLANN（更稳定）
  - 启用crossCheck=True（一次调用完成双向检查）
  - 限制最大匹配点数量（100个）

- **重影问题修复**
  - 使用sigmoid陡峭权重过渡（替代线性）
  - 减小高斯模糊核（从21x21降至11x11）
  - 在重叠区域中心使用单一图像
  - 添加几何一致性检查

- **预处理优化**
  - 快速模式只进行高斯模糊
  - 跳过CLAHE和形态学运算
  - 添加fast_mode参数控制

### 🐛 错误修复

- **修复图像拼接输入处理问题** (#23)
  - 问题：`process()`方法立即清空`_input_data_list`
  - 症状：即使连接2张图像也提示"至少需要两张图像"
  - 修复：移除`process()`方法中错误的清空逻辑

- **修复输入数据累积问题** (#21)
  - 改进`set_input()`方法的周期检测
  - 添加`_input_count`计数器
  - 超过1秒自动识别为新周期

- **修复工具库空白问题**
  - 问题：工具库面板显示空白，无法显示工具列表
  - 原因：`ToolRegistry`动态加载失败，没有备用方案
  - 修复：恢复硬编码工具列表，确保工具正常显示

- **修复YOLO26-CPU检测器未初始化问题**
  - 问题：加载方案后YOLO26-CPU工具执行时间仅1ms，返回原图
  - 原因：加载已存在工具时未调用`initialize()`方法
  - 修复：在`_add_tool_to_scene()`方法中添加工具初始化逻辑

- **修复新工具参数错误**
  - 问题：几何变换和图像保存工具无法创建
  - 原因：`set_param()`使用了不支持的`min_value`/`max_value`参数
  - 修复：移除不支持的参数

- **修复新工具输入数据获取错误**
  - 问题：几何变换和图像保存工具执行时报错
  - 原因：使用了不存在的方法`get_input_data()`
  - 修复：改为使用正确的`get_input()`方法

- **修复方案加载后算法编辑器空白问题**
  - 问题：打开方案文件后算法编辑器不显示算子
  - 原因：`open_solution()`方法没有重新创建图形项
  - 修复：添加完整的工具加载和连接恢复逻辑

- **修复连接对象访问错误**
  - 问题：打开方案时报错`'ToolConnection' object has no attribute 'get'`
  - 原因：错误地将`ToolConnection`对象当作字典访问
  - 修复：使用正确的属性访问方式`connection.from_tool`和`connection.to_tool`

- **修复热重载回调错误**
  - 问题：热重载时报错`'PropertyDockWidget' object has no attribute 'current_tool'`
  - 原因：访问了不存在的公共属性，实际应为私有属性`_current_tool`
  - 修复：更正属性访问方式

- **修复通讯配置单例模式问题**
  - 问题：发送数据工具无法找到通讯连接，或找到错误的连接
  - 原因：`ConnectionManager`的`__init__`方法每次都被调用，导致连接数据被清空
  - 修复：添加`_initialized`标志，避免单例重复初始化清空数据

- **修复通讯配置编辑卡顿问题**
  - 问题：编辑通讯配置时程序卡顿无响应
  - 原因：`QMessageBox.information`模态对话框阻塞事件循环
  - 修复：移除阻塞对话框，改为更新状态栏；使用`QTimer`延迟刷新UI

- **修复图像拼接结果不显示问题**
  - 问题：图像拼接工具执行后结果面板不显示结果
  - 原因：`process`方法返回的`ResultData`没有保存到`_result_data`
  - 修复：在`_run_impl`方法中将`process`返回的`ResultData`保存到`self._result_data`

- **修复灰度匹配结果显示问题**
  - 问题：灰度匹配结果显示"匹配失败：相似度=0.00%"，但实际匹配成功
  - 原因：结果面板期望的字段名（`matched`、`score`、`center`）与工具设置的字段名（`best_score`、`best_x`、`best_y`）不一致
  - 修复：在灰度匹配工具中添加结果面板期望的字段；设置`result_category = "match"`使结果面板正确显示

- **修复结果面板显示不完整问题**
  - 问题：结果面板只显示2条结果，但算法编辑器有4个模块
  - 原因：`add_result`方法使用`tool_name`（工具类型名称）区分结果，导致相同类型的工具结果被合并
  - 修复：使用`tool.name`（工具实例名称）区分不同工具实例

- **修复数据选择器缺少图像结果问题**
  - 问题：数据选择器中缺少图像拼接工具的图像结果
  - 原因：`_update_property_panel_modules`方法只检查`result_data._values`，没有检查`result_data._images`
  - 修复：添加对`result_data._images`的检查，将图像数据也添加到可用模块

- **修复发送数据编码错误**
  - 问题：发送数据时报错`'ascii' codec can't encode characters`
  - 原因：`_format_data`方法使用`encode("ascii")`无法编码中文字符
  - 修复：将ASCII编码改为UTF-8编码

- **修复热重载回调错误（结果面板）**
  - 问题：热重载时报错`'EnhancedResultDockWidget' object has no attribute 'refresh'`
  - 原因：`EnhancedResultDockWidget`类缺少`refresh`方法
  - 修复：添加`refresh`方法，刷新增强面板和传统面板

- **修复发送数据目标连接刷新问题**
  - 问题：发送数据工具的目标连接需要多次点击才刷新，或选择"点击刷新获取连接列表"后未自动选择实际连接
  - 原因：缓存时间过长，刷新后未自动选择第一个可用连接
  - 修复：缩短缓存时间到1秒；刷新后自动选择第一个可用连接；运行时自动刷新

- **修复条码识别结果显示异常问题**
  - 问题：条码识别工具执行后结果面板不显示或显示异常
  - 原因：缺少`tool_name`和`result_category`设置；结果字段名与结果面板期望的不一致
  - 修复：添加`tool_name`和`result_category`设置；统一使用`codes`字段；设置正确的类别"barcode"

- **修复算法模块删除后结果面板未同步问题**
  - 问题：删除算法模块后，结果面板中该模块的结果仍然存在
  - 原因：删除结果时使用的是`tool.tool_name`（类型名称），但添加时使用的是`tool.name`（实例名称）
  - 修复：统一使用`tool.name`（实例名称）来添加和删除结果

- **优化条码/二维码识别结果数据结构**
  - 改进：将识别结果拆分为单独字段（`code_data`、`code_type`、`code_x`、`code_y`、`code_width`、`code_height`）
  - 优点：用户可以在数据选择器中自由选择需要发送的特定字段

- **补充缺失的算法工具结果数据**
  - 问题：OCR、外观检测、标定、几何变换、图像保存等工具缺少`tool_name`和`result_category`设置
  - 修复：为所有工具添加`tool_name`和`result_category`设置，确保结果面板能正确显示

### 📝 文档更新

- 更新CHANGELOG.md，添加通讯配置、结果面板、发送数据等修复记录
- 更新性能基准测试报告，添加图像拼接性能数据
- 更新README.md，添加图像拼接优化信息

### 🔢 性能数据

| 配置 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| ORB Fast | ~0.5s | 0.03s | **17x** |
| ORB Balanced | ~0.5s | 0.03s | **17x** |
| SIFT Quality | ~0.5s | 0.46s | 1.1x |

### 🌐 中文化更新

- 新增参数中文标签：
  - `performance_mode` → "性能模式"
  - `fast_mode` → "快速预处理"
  - 选项标签："快速模式 (速度优先)"/"平衡模式 (推荐)"/"高质量模式 (质量优先)"

---

## [1.0.0] - 2026-01-30

### 🎉 正式发布

- ✅ 完成海康VisionMaster V4.4.0的Python完整重构
- ✅ 通过案例测试
- ✅ 40+算法工具
- ✅ 完整中文化界面
- ✅ 工业级通信支持
- ✅ 方案管理功能
- ✅ 代码生成功能

### 🏗️ 核心功能

- **模块化架构**: 四层架构设计，松耦合高内聚
- **可视化编程**: 拖拽式工具连接，所见即所得
- **内存池**: ImageBufferPool，提升118x分配速度
- **确定性流水线**: DeterministicPipeline，严格顺序处理
- **YOLO26-CPU**: 高性能目标检测
- **图像拼接**: 支持任意顺序图像拼接

### 📚 文档

- AGENTS.md - 开发指南
- ARCHITECTURE.md - 系统架构
- 性能基准测试报告
- 错误处理指南
- 项目综合文档

---

## 版本说明

- **主版本号**: 不兼容的API更改
- **次版本号**: 向下兼容的功能新增
- **修订号**: 向下兼容的问题修复

## 标签说明

- 🚀 Added - 新功能
- 🔧 Changed - 变更
- 🐛 Fixed - 修复
- ⚠️ Deprecated - 弃用
- 🔒 Security - 安全
- 📝 Docs - 文档
