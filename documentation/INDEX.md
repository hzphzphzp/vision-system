# 文档索引

> Vision System 项目文档导航

## 核心文档

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [README.md](../README.md) | 项目介绍、快速开始、使用示例 | ⭐⭐⭐ |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计、核心组件说明 | ⭐⭐⭐ |
| [AGENTS.md](../AGENTS.md) | AI Agent开发指南 | ⭐⭐ |
| [docs/performance_benchmark.md](../docs/performance_benchmark.md) | 性能优化基准测试报告 | ⭐⭐ |

## 功能文档

| 文档 | 说明 | 类别 |
|------|------|------|
| [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | 项目综合文档 | 综合 |
| [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) | 错误处理和异常管理 | 开发 |
| [PROJECT_OPTIMIZATION_GUIDE.md](PROJECT_OPTIMIZATION_GUIDE.md) | 项目优化指南 | 开发 |
| [tools/vision/CALIBRATION.md](../tools/vision/CALIBRATION.md) | 标定工具使用指南 | 工具 |

## 工具文档

| 文档 | 说明 |
|------|------|
| [tools/vision/calibration.py](../tools/vision/calibration.py) | 标定工具源代码 |
| [tools/vision/CALIBRATION.md](../tools/vision/CALIBRATION.md) | 标定工具使用指南 |
| [tests/test_calibration.py](../tests/test_calibration.py) | 标定工具测试 |

## 参考文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [PROJECT_REFERENCE.md](PROJECT_REFERENCE.md) | 项目参考信息 | 参考 |
| [SKILL_USAGE_GUIDE.md](SKILL_USAGE_GUIDE.md) | 技能使用指南 | 参考 |
| [config_management_summary.md](config_management_summary.md) | 配置管理总结 | 参考 |

## 归档文档

| 文档 | 说明 | 说明 |
|------|------|------|
| [archives/performance_optimization_summary.md](archives/performance_optimization_summary.md) | Polars性能优化 | 已归档 |

## 计划文档

| 文档 | 说明 |
|------|------|
| [docs/plans/2026-02-03-performance-optimization.md](../docs/plans/2026-02-03-performance-optimization.md) | 性能优化实施计划 |
| [core/communication/tcp_server_refactor_plan.md](../core/communication/tcp_server_refactor_plan.md) | TCP服务端重构计划 |
| [core/communication/tcp_client_refactor_plan.md](../core/communication/tcp_client_refactor_plan.md) | TCP客户端重构计划 |
| [ui/communication_config_refactor_plan.md](../ui/communication_config_refactor_plan.md) | 通信配置重构计划 |
| [modules/cpu_optimization/INTEGRATION.md](../modules/cpu_optimization/INTEGRATION.md) | CPU优化集成文档 |

## 文档更新指南

### 添加新文档

1. 选择合适的目录:
   - `documentation/` - 通用开发文档
   - `docs/` - 用户级文档
   - `docs/plans/` - 实施计划

2. 文档命名规范:
   - 使用 CamelCase 或 snake_case
   - 清晰描述文档内容
   - 添加适当的后缀 (GUIDE.md, SUMMARY.md, etc.)

3. 文档结构:
   ```markdown
   # 文档标题
   
   ## 1. 概述
   ## 2. 详细内容
   ## 3. 示例
   ## 4. 参考
   ```

### 更新现有文档

1. 更新文档顶部的"最后更新"日期
2. 在相关位置添加更新日志
3. 确保文档与代码同步

### 归档文档

将不再使用但有参考价值的文档移到 `documentation/archives/`

## 文档质量标准

- ✅ 清晰的标题和结构
- ✅ 完整的示例代码
- ✅ 适当的格式化
- ✅ 定期更新维护
- ✅ 与代码同步更新
