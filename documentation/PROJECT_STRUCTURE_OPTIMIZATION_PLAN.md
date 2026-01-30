# 项目结构优化计划

## 1. 现状分析

通过对当前项目结构的分析，发现以下问题：

### 1.1 根目录混乱
- 根目录存在多个图像文件：`result.jpg`, `stitched_result.jpg`, `stitched_result_order1.jpg`, `stitched_result_order2.jpg`, `stitched_result_order3_1.jpg`, `stitched_result_order3_2.jpg`, `test_image_1.jpg`, `test_image_2.jpg`, `test_image_3.jpg`
- 根目录存在测试文件：`test_tool_naming.py`, `test_tool_registry.py`
- 根目录存在模型文件：`yolo26n.pt`

### 1.2 文档目录不一致
- 存在两个文档目录：`docs/` 和 `documentation/`
- 文档内容分散在两个目录中

### 1.3 测试文件分布不合理
- 测试文件分布在根目录和 `tests/` 目录
- `tests/` 目录中也存在图像文件

### 1.4 目录结构与文档描述不一致
- 当前目录结构与 `PROJECT_DOCUMENTATION.md` 中描述的结构不完全一致

## 2. 优化目标

1. **根目录整洁**：只保留必要的配置文件和入口脚本
2. **目录结构清晰**：遵循模块化、层次化的设计原则
3. **文档结构统一**：使用单一文档目录，统一文档管理
4. **资源文件集中**：创建专门的目录存放图像、模型等资源文件
5. **测试文件规范**：确保所有测试文件都在 `tests/` 目录中
6. **目录结构与文档一致**：更新文档以反映实际目录结构

## 3. 优化方案

### 3.1 目录结构调整

#### 3.1.1 根目录清理
- 保留文件：`.gitignore`, `README.md`, `professional_app.py`, `requirements.txt`, `run.py`
- 移除或移动文件：所有图像文件、测试文件、模型文件

#### 3.1.2 新增目录
- `data/images/`：存放测试图像和结果图像
- `data/models/`：存放模型文件
- `data/test_results/`：存放测试结果文件

#### 3.1.3 文档目录统一
- 保留 `documentation/` 目录作为主要文档目录
- 将 `docs/` 目录中的内容移动到 `documentation/` 目录
- 删除 `docs/` 目录

#### 3.1.4 测试目录整理
- 将根目录中的测试文件移动到 `tests/` 目录
- 将 `tests/` 目录中的图像文件移动到 `data/images/` 目录

### 3.2 文件移动计划

| 原始路径 | 目标路径 | 说明 |
|---------|---------|------|
| `result.jpg` | `data/test_results/` | 测试结果图像 |
| `stitched_result.jpg` | `data/test_results/` | 测试结果图像 |
| `stitched_result_order1.jpg` | `data/test_results/` | 测试结果图像 |
| `stitched_result_order2.jpg` | `data/test_results/` | 测试结果图像 |
| `stitched_result_order3_1.jpg` | `data/test_results/` | 测试结果图像 |
| `stitched_result_order3_2.jpg` | `data/test_results/` | 测试结果图像 |
| `test_image_1.jpg` | `data/images/` | 测试输入图像 |
| `test_image_2.jpg` | `data/images/` | 测试输入图像 |
| `test_image_3.jpg` | `data/images/` | 测试输入图像 |
| `yolo26n.pt` | `data/models/` | 模型文件 |
| `test_tool_naming.py` | `tests/` | 测试文件 |
| `test_tool_registry.py` | `tests/` | 测试文件 |
| `tests/stitched_result.jpg` | `data/test_results/` | 测试结果图像 |
| `tests/stitched_result_multiple.jpg` | `data/test_results/` | 测试结果图像 |
| `docs/END_DOCUMENT.md` | `documentation/` | 文档文件 |
| `docs/TECHNICAL_DOCUMENT.md` | `documentation/` | 文档文件 |

### 3.3 文档更新计划

1. 更新 `documentation/PROJECT_DOCUMENTATION.md` 中的项目结构描述
2. 更新 `README.md` 中的项目结构描述
3. 确保所有文档中的目录引用与实际目录结构一致

### 3.4 代码更新计划

1. 更新所有引用了移动文件的代码路径
2. 特别注意测试代码中的图像文件路径
3. 确保模型加载路径正确

## 4. 执行步骤

### 4.1 准备工作
- 创建新的目录结构
- 备份当前项目结构

### 4.2 执行文件移动
- 按照文件移动计划执行文件移动

### 4.3 更新代码和文档
- 更新所有引用了移动文件的代码
- 更新文档中的目录结构描述

### 4.4 验证
- 运行测试确保所有功能正常
- 检查文档链接是否正确
- 验证目录结构是否符合预期

## 5. 预期结果

### 5.1 优化后的目录结构

```
vision_system/
├── config/                      # 配置文件
├── configs/                     # 配置模板
├── core/                        # 核心逻辑
├── data/                        # 数据相关
│   ├── images/                  # 图像文件
│   ├── models/                  # 模型文件
│   └── test_results/            # 测试结果
├── documentation/               # 文档
├── examples/                    # 示例代码
├── modules/                     # 功能模块
├── tests/                       # 测试代码
├── tools/                       # 工具类
├── ui/                          # 用户界面
├── utils/                       # 工具函数
├── .gitignore
├── README.md
├── professional_app.py
├── requirements.txt
└── run.py
```

### 5.2 优化效果
- 根目录整洁，只包含必要的文件
- 目录结构清晰，层次分明
- 资源文件集中管理，便于维护
- 测试文件规范，便于运行和管理
- 文档结构统一，便于查阅

## 6. 风险评估

### 6.1 潜在风险
- 代码中硬编码的文件路径可能会失效
- 测试可能会因为路径变更而失败
- 文档中的链接可能会失效

### 6.2 风险缓解措施
- 仔细检查所有代码中的文件路径引用
- 运行完整的测试套件确保所有功能正常
- 更新所有文档中的路径引用
- 保留备份以便在出现问题时恢复

## 7. 结论

通过实施此优化计划，可以显著改善项目的目录结构，提高代码的可维护性和可读性。优化后的目录结构将更加清晰、规范，符合Python项目的最佳实践，便于团队协作和后续开发。