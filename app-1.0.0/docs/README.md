# Glimpseon 1.0.0 开发者文档

> 编写者：HelloGaoo　最后修改：2026/08/13

Glimpseon 是一款基于 PyQt6 + Fluent Widgets 的 Windows 桌面信息看板，集成壁纸管理、天气、一言、媒体信息、课程表、通知、软件下载等功能。

本目录是面向开发者 / 维护者的技术文档，按模块组织。建议按下列顺序阅读：

## 文档索引

| 文档                             | 内容                         |
| ------------------------------ | -------------------------- |
| [架构总览](architecture.md)        | 整体分层、模块职责、运行时数据流           |
| [快速开始](getting-started.md)     | 环境要求、依赖安装、运行、打包            |
| [目录结构](directory-structure.md) | 源码与资源目录详解                  |
| [核心模块](core-modules.md)        | `core/` 下各模块实现细节           |
| [UI 模块](ui-modules.md)         | `ui/` 下各界面实现细节             |
| [服务模块](services.md)            | `services/` 下数据获取服务        |
| [原生扩展](native-extension.md)    | `glimpseon_native/` C++ 扩展 |
| [配置系统](configuration.md)       | `QConfig` 配置项全表与机制         |
| [启动流程](launch-flow.md)         | 从启动器到主窗口的完整时序              |
| [组件系统](component-system.md)    | 网格布局、组件定义与编辑模式             |

## 项目关注

- **UI 组件库**：PyQt6 Fluent Widgets
- **字体**：HarmonyOS Sans（回退 Microsoft YaHei → SimHei → sans-serif）
- **许可证**：GPL-3.0

## 项目入口

- 顶层启动器：[Glimpseon.py](file:///e:/260523/py/Glimpseon/Glimpseon.py)
- 主程序：[GlimpseonMain.py](file:///e:/260523/py/Glimpseon/app-1.0.0/GlimpseonMain.py)

## 版本

版本号与构建日期来自 `app-1.0.0/record.json`，由 `core/paths.py` 读取为 `VERSION` / `BUILD_DATE`。
