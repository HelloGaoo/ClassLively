# Glimpseon 1.0.0 开发者文档

> [!NOTE]
> 编写者：HelloGaoo　最后修改：2026/08/23

Glimpseon 是一款基于 PyQt6 Fluent Widgets 的 Windows 桌面信息看板，集成壁纸管理、天气、一言、新闻、历史上的今天、每日单词、每日英语、数字/模拟时钟、媒体信息、课程表、通知、软件下载等功能。

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
- **字体**：HarmonyOS Sans（回退 Microsoft YaHei → PingFang SC → Segoe UI → sans-serif）
- **许可证**：GPL-3.0

## 项目入口

- 顶层启动器：[Glimpseon.py](file:///e:/260523/py/Glimpseon/Glimpseon.py)
- 主程序：[GlimpseonMain.py](file:///e:/260523/py/Glimpseon/app-1.0.0/GlimpseonMain.py)

## 版本

版本号与构建日期来自 `app-1.0.0/record.json`，由 `core/paths.py` 读取为 `VERSION` / `BUILD_DATE`。

## 鸣谢

本项目开发者对所有开源项目及其代码贡献者表示感谢。完整名单见 [`resource/credits.json`](file:///e:/260523/py/Glimpseon/app-1.0.0/resource/credits.json)。

（可能出现纰漏，以实际为准）

### 参考项目

本软件在开发过程中参考了以下开源项目的架构、算法或实现：

| 项目                                                                                                | 许可证                             | 版权信息 / 说明                             |
| :------------------------------------------------------------------------------------------------ | :------------------------------ | :------------------------------------ |
| [`Alan-CRL/Inkeys`](https://github.com/Alan-CRL/Inkeys)                                           | GNU General Public License v3.0 | Copyright © 2023-2025 AlanCRL（陈润林）工作室 |
| [`HelloGaoo/SeevvoDownloader`](https://github.com/HelloGaoo/SeevvoDownloader)                     | GNU General Public License v3.0 | Copyright © 2026 HelloGaoo,WHYOS      |
| [`ClassIsland/ClassIsland`](https://github.com/ClassIsland/ClassIsland)                           | GNU General Public License v3.0 | 参见项目文档                                |
| [`Class-Widgets/Class-Widgets`](https://github.com/Class-Widgets/Class-Widgets)                   | GNU General Public License v3.0 | Copyright © 2025 RinLit               |
| [`Kxnrl/NetEase-Cloud-Music-DiscordRPC`](https://github.com/Kxnrl/NetEase-Cloud-Music-DiscordRPC) | MIT License                     | Copyright (c) 2018 Kyle               |

### 第三方开源组件

| 组件名称                                                                                                            | 许可证                       | 版权信息 / 说明                         |
| :-------------------------------------------------------------------------------------------------------------- | :------------------------ | :-------------------------------- |
| [`pybind/pybind11`](https://github.com/pybind/pybind11)                                                         | BSD-3-Clause              | C++ （`glimpseon_native`）Python 绑定 |
| [`riverbankcomputing/PyQt6`](https://www.riverbankcomputing.com/software/pyqt/)                                 | GPL-3.0 / Commercial      | UI 框架                             |
| [`zhiyiYo/PyQt-Fluent-Widgets`](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)                                 | GPL-3.0                   | UI 组件库                            |
| [`zhiyiYo/PyQt-Frameless-Window`](https://github.com/zhiyiYo/PyQt-Frameless-Window)                             | GPL-3.0                   | 无边框窗口                             |
| [`pytorch/pytorch`](https://github.com/pytorch/pytorch)                                                         | BSD-3-Clause              | EasyOCR 推理后端                      |
| [`pytorch/vision`](https://github.com/pytorch/vision)                                                           | BSD-3-Clause              | torchvision，EasyOCR 依赖            |
| [`JaidedAI/EasyOCR`](https://github.com/JaidedAI/EasyOCR)                                                       | Apache License 2.0        | OCR 识别                            |
| [`madmub/pytesseract`](https://github.com/madmub/pytesseract)                                                   | Apache License 2.0        | Tesseract OCR 封装                  |
| [`opencv/opencv-python`](https://github.com/opencv/opencv-python)                                               | Apache License 2.0        | 图像处理（opencv-python-headless）      |
| [`python-pillow/Pillow`](https://github.com/python-pillow/Pillow)                                               | HPND                      | 图像处理                              |
| [`scikit-image/scikit-image`](https://github.com/scikit-image/scikit-image)                                     | BSD-3-Clause              | 图像处理                              |
| [`numpy/numpy`](https://github.com/numpy/numpy)                                                                 | BSD-3-Clause              | 数值计算                              |
| [`scipy/scipy`](https://github.com/scipy/scipy)                                                                 | BSD-3-Clause              | 科学计算                              |
| [`networkx/networkx`](https://github.com/networkx/networkx)                                                     | BSD-3-Clause              | 图计算                               |
| [`sympy/sympy`](https://github.com/sympy/sympy)                                                                 | BSD-3-Clause              | 符号计算                              |
| [`shapely/shapely`](https://github.com/shapely/shapely)                                                         | BSD-3-Clause              | 几何计算                              |
| [`psf/requests`](https://github.com/psf/requests)                                                               | Apache License 2.0        | HTTP 请求                           |
| [`urllib3/urllib3`](https://github.com/urllib3/urllib3)                                                         | MIT License               | HTTP 底层                           |
| [`certifi/python-certifi`](https://github.com/certifi/python-certifi)                                           | MPL-2.0                   | CA 证书                             |
| [`Ousret/charset_normalizer`](https://github.com/Ousret/charset_normalizer)                                     | MIT License               | 字符编码检测                            |
| [`idna`](https://github.com/kjd/idna)                                                                           | BSD-3-Clause              | 国际化域名                             |
| [`pyinstaller/pyinstaller`](https://github.com/pyinstaller/pyinstaller)                                         | GPL-2.0+                  | 打包                                |
| [`pyinstaller/pyinstaller-hooks-contrib`](https://github.com/pyinstaller/pyinstaller-hooks-contrib)             | Apache License 2.0        | PyInstaller hooks                 |
| [`ronaldoussoren/altgraph`](https://github.com/ronaldoussoren/altgraph)                                         | MIT License               | PyInstaller 依赖                    |
| [`erocarrera/pefile`](https://github.com/erocarrera/pefile)                                                     | MIT License               | PE 文件解析                           |
| [`enthought/pywin32-ctypes`](https://github.com/enthought/pywin32-ctypes)                                       | PSF-2.0                   | PyInstaller 依赖                    |
| [`mhammond/pywin32`](https://github.com/mhammond/pywin32)                                                       | PSF-2.0                   | Windows API                       |
| [`enthought/comtypes`](https://github.com/enthought/comtypes)                                                   | MIT License               | COM 接口                            |
| [`yinkaisheng/Python-UIAutomation-for-Windows`](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) | MIT License               | UI 自动化                            |
| [`pywinrt/python-winsdk`](https://github.com/pywinrt/python-winsdk)                                             | MIT License               | Windows SDK 绑定                    |
| [`AndreMiras/pycaw`](https://github.com/AndreMiras/pycaw)                                                       | MIT License               | 音频会话控制                            |
| [`ABUCKY0/py-now-playing`](https://github.com/ABUCKY0/py-now-playing)                                           | GPL-3.0                   | 媒体播放状态                            |
| [`srounet/Pymem`](https://github.com/srounet/Pymem)                                                             | MIT License               | 进程内存读写                            |
| [`giampaolo/psutil`](https://github.com/giampaolo/psutil)                                                       | BSD-3-Clause              | 系统进程信息                            |
| [`miurahr/py7zr`](https://github.com/miurahr/py7zr)                                                             | LGPLv2+                   | 7z 压缩                             |
| [`miurahr/pyppmd`](https://github.com/miurahr/pyppmd)                                                           | LGPLv2+                   | PPMD 压缩                           |
| [`miurahr/pybcj`](https://github.com/miurahr/pybcj)                                                             | LGPLv2+                   | BCJ 过滤器                           |
| [`miurahr/inflate64`](https://github.com/miurahr/inflate64)                                                     | LGPLv2+                   | inflate64 解压                      |
| [`miurahr/multivolume`](https://github.com/miurahr/multivolume)                                                 | LGPLv2+                   | 多卷归档                              |
| [`Legrandin/pycryptodome`](https://github.com/Legrandin/pycryptodome)                                           | Unlicense / BSD-2-Clause  | 加密                                |
| [`fonttools/pyclipper`](https://github.com/fonttools/pyclipper)                                                 | Custom (based on Clipper) | 多边形裁剪                             |
| [`MeirKrihavi/python-bidi`](https://github.com/MeirKrihavi/python-bidi)                                         | LGPL                      | 双向文本                              |
| [`pallets/jinja`](https://github.com/pallets/jinja)                                                             | BSD-3-Clause              | 模板引擎                              |
| [`pallets/markupsafe`](https://github.com/pallets/markupsafe)                                                   | BSD-3-Clause              | HTML 转义                           |
| [`yaml/pyyaml`](https://github.com/yaml/pyyaml)                                                                 | MIT License               | YAML 解析                           |
| [`CNlyl/cnlunar`](https://github.com/CNlyl/cnlunar)                                                             | MIT License               | 农历计算                              |
| [`fengsp/color-thief-py`](https://github.com/fengsp/color-thief-py)                                             | BSD-3-Clause              | 主色提取                              |
| [`albertosottile/darkdetect`](https://github.com/albertosottile/darkdetect)                                     | BSD-3-Clause              | 系统暗色检测                            |
| [`foutaise/texttable`](https://github.com/foutaise/texttable)                                                   | MIT License               | 文本表格                              |
| [`imageio/imageio`](https://github.com/imageio/imageio)                                                         | BSD-2-Clause              | 图像 IO                             |
| [`cgohlke/tifffile`](https://github.com/cgohlke/tifffile)                                                       | BSD-3-Clause              | TIFF 文件                           |
| [`scikit-build/ninja`](https://github.com/scikit-build/ninja)                                                   | Apache License 2.0        | 构建系统                              |
| [`scientific-python/lazy_loader`](https://github.com/scientific-python/lazy_loader)                             | BSD-3-Clause              | 懒加载                               |
| [`pycontribs/filelock`](https://github.com/pycontribs/filelock)                                                 | BSD-3-Clause              | 文件锁                               |
| [`fsspec/filesystem_spec`](https://github.com/fsspec/filesystem_spec)                                           | BSD-3-Clause              | 文件系统抽象                            |
| [`mpmath/mpmath`](https://github.com/mpmath/mpmath)                                                             | BSD-3-Clause              | 任意精度运算                            |
| [`python/typing_extensions`](https://github.com/python/typing_extensions)                                       | PSF-2.0                   | 类型扩展                              |
| [`google/brotli`](https://github.com/google/brotli)                                                             | MIT License               | Brotli 压缩                         |
| [`rgommers/backports.zstd`](https://github.com/rgommers/backports.zstd)                                         | BSD / GPLv2+              | Zstandard 压缩                      |
| [`pypa/packaging`](https://github.com/pypa/packaging)                                                           | Apache-2.0 / BSD          | 打包工具                              |

> [!NOTE]
> 以上许可证信息仅为摘要，各组件的具体权利义务以其随附的许可证文本为准。各组件的商标与名称归其各自所有者所有，本软件不主张对任何第三方组件的所有权。

