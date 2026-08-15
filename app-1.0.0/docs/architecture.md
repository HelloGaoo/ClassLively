# 架构总览

> [!NOTE]
> 编写者：HelloGaoo　最后修改：2026/08/13

## 1. 技术栈

| 层      | 技术                                        |
| ------ | ----------------------------------------- |
| 语言     | Python 3.11（主）、C++17                      |
| GUI 框架 | PyQt6 6.11                                |
| UI 组件库 | PyQt6-Fluent-Widgets 1.11                 |
| 无边框窗口  | PyQt6-Frameless-Window                    |
| 原生绑定   | pybind11（`Glimpseon_native.pyd`）          |
| 配置     | qfluentwidgets `QConfig`（.json）           |
| 国际化    |  `TranslationManager` + json              |
| 打包     | PyInstaller 6.20                          |
| 媒体/OCR | easyocr、pytesseract、opencv-headless、torch |
| 网络     | requests、aria2c（外部）、7z（外部）                |

完整依赖见 [requirements.txt](file:///e:/260523/py/Glimpseon/requirements.txt)。

## 2. 分层结构

```mermaid
graph TD
    A["启动器 Glimpseon.py<br/>版本选择"]
    A -- "subprocess/环境变量" --> B

    B["主程序 app-1.0.0/GlimpseonMain.py"]
    B --- B1["SplashScreen 启动窗口<br/>初始化页面 获取壁纸 一言 更新等"]
    B --- B2["WizardWindow 首次运行向导"]
    B --- B3["MainWindow FluentWindow 主壳<br/>导航 子界面"]
    B --- B4["Preloader QThread<br/>预加载壁纸/天气/一言"]

    B -- 组合 --> C["core/ 后台层<br/>给ui干活"]
    B -- 组合 --> D["ui/ 界面层"]
    B -- 组合 --> E["services/ 数据服务层<br/>请求api/解析返回"]

    D -- 依赖 --> C
    D -- 调用 --> E
    C -- 读取 --> F["resource/ 资源<br/>qss/icon/font/locale/city/software"]
    C -- 调用 --> G["glimpseon_native/ C++<br/>壁纸/模糊/钩子/系统"]
```

## 3. 设计原则

1. **单一组件库约束**：UI 控件使用 PyQt6 Fluent Widgets
2. **路径处理**：所有目录路径由 [core/paths.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/paths.py) 在导入期计算 支持开发态 / 打包态（`sys.frozen` + `_MEIPASS`）/ 启动器态
3. **配置**：可调项以 `ConfigItem` 形式声明在 [core/config.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/config.py) 的 `Config` 类中
4. **资源查找**：`get_resource_path()` 依次查 `APP_DIR → MEIPASS_DIR → APP_DIR`
5. **主题样式**：每个页面含dark/light两个qss文件 切换主题时清理缓存 加载新qss
6. **预加载/缓存**：壁纸 / 天气 / 一言在 `Preloader`（QThread）中同时拉取 通过 `pyqtSignal` 回主线程刷新 UI，避免阻塞启动。
7. **性能优化**：高斯模糊（Direct2D）空闲检测 单例互斥 图标提取等 部分由c++处理

## 4. 数据处理（例如：壁纸显示）

### 阶段一：子线程预加载 `Preloader._load_wp()`

| 步骤 | 动作 | 结果 |
|------|------|------|
| 1 | 读缓存 `get_cached_content("wallpaper")`（`ignore_expiry=True`，过期也用旧的） | 命中则直接进入步骤 4 |
| 2 | 未命中：`requests.get(API, stream=True, timeout=15)` 拉取壁纸 | HTTP 200 → 落盘 `wp_HHMMSS.jpg` |
| 3 | 落盘后 `_manageWallpaperLimit()` 控制数量，`save_cache()` 写缓存 | 失败则回退默认壁纸 / 历史最新 |
| 4 | `sig_wp.emit(path, src, url)` 通过信号回到主线程 | 触发阶段二 |

### 阶段二：主线程槽 `_upd_wp()`

1. `wallpaper.current_pixmap = QPixmap(path)` —— 载入像素图
2. `wallpaper._updateMainWindowBackground()` —— 设为主窗口背景
3. `wallpaper._applyEffects()` —— 模糊 / 亮度（调用 `Glimpseon_native`）
4. `wallpaper.infoCard.updateInfo(...)` —— 更新信息卡
5. `wallpaper.historyManager.add(...)` —— 加入历史记录
6. `wallpaper.wallpaperChanged.emit()` —— 通知主界面刷新

## 5. 关键全局对象

| 对象                                       | 定义位置                                                                      | 作用          |
| ---------------------------------------- | ------------------------------------------------------------------------- | ----------- |
| `cfg`                                    | [core/config.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/config.py) | 全局配置单例      |
| `logger`                                 | [core/logger.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/logger.py) | 日志器         |
| `tr()`                                   | [core/utils.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/utils.py)   | 翻译查找函数      |
| `FUI`                                    | [core/utils.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/utils.py)   | Fluent 图标枚举 |
| `PACKAGE_ROOT` / `APP_DIR` / `DATA_ROOT` | [core/paths.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/paths.py)   | 路径常量        |

## 6. 外部联动

Glimpseon 可与以下外部系统集成（见 [core/linkage.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/linkage.py)）：

- **ClassIsland**：读取 `Profiles/Default.json` 与 `Settings.json`，同步课表 / 时间状态等
- **ClassWidgets**：同样读取类似档案

时间状态枚举 `TimeState`：`NONE / PREPARE_ON_CLASS / ON_CLASS / BREAKING / AFTER_SCHOOL`。

> [!NOTE]
> 早期尝试过进程通信 / http 方式进行联动
>
> 稳定性原因最终直接找软件目录 读软件json配置

## 7. 数据目录

运行期所有数据保存在 `PACKAGE_ROOT/data/`（见 [core/paths.py](file:///e:/260523/py/Glimpseon/app-1.0.0/core/paths.py)）：

```
data/
├── config/      config.json + Setup_Wizard.json + 课表 json
├── log/         日志
├── cache/       缓存
├── temp/        临时
├── profile/     课表
├── user/        数据
├── icon/        图标
├── wallpaper/   壁纸
├── classphotos/ 照片
└── notes/       便签
```

软件启动时调用 `ensure_data_dirs()` 保证目录存在
