# UI 模块（ui/）

`ui/` 是基于 PyQt6 Fluent Widgets 的界面层。所有界面通过 `MainWindow.addSubInterface()` 注册到 FluentWindow 导航。每个界面通过 `load_qss()` 加载对应主题 QSS，并实现 `_onThemeChanged` 响应主题切换。

> **约束**：UI 控件必须使用 PyQt6 Fluent Widgets，不得引入其它组件库。组件配置面板必须 parent 到 MainWindow 以保证 z-order 正确。

***

## 1. common.py — 公共基类

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/common.py)

- `BaseScrollAreaInterface(ScrollArea)`：滚动界面基类，统一滚动条与边距。
- `show_text_file(title, ...)`：以对话框形式展示文本文件（协议 / 许可证）。

***

## 2. home.py — 主界面

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/home.py) · QSS：`home.qss`

### 2.1 HomeInterface

`HomeInterface(QWidget, TranslatableWidget)` 是应用主画布，承载壁纸背景与所有桌面组件。

**核心职责**：

- 渲染壁纸背景（含模糊 / 亮度效果）。
- 管理组件网格布局（编辑模式拖拽 / 缩放）。
- 聚合时钟、天气、一言、倒计时、媒体、快捷启动、学校信息等组件。
- 提供页面指示器（多页切换）与编辑模式遮罩。

**关键信号**：

- `weather_updated(dict)` — 天气数据更新（由 Preloader 触发）
- `poetry_updated(str)` — 一言更新
- `wallpaperChanged` — 壁纸变更（间接触发）

**关键属性**：`_cached_weather`、`_cached_poetry`、`current_weather_code`、`isEditMode`。

### 2.2 辅助控件

| 类                     | 作用          |
| --------------------- | ----------- |
| `GuideLineOverlay`    | 编辑模式参考线覆盖层  |
| `PageIndicator`       | 多页小圆点指示器    |
| `_GridOverlay`        | 网格背景显示      |
| `CountdownEditDialog` | 倒计时编辑对话框    |
| `AppEditDialog`       | 快捷启动应用编辑对话框 |

### 2.3 主题适配

NavigationPage 提示文字颜色随主题：深色 `rgba(230,230,230,0.95)`，浅色 `rgba(60,60,60,1.0)`，切换时自动更新。

***

## 3. component.py — 组件实现库

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py) · QSS：`component.qss` / `home.qss`

### 3.1 核心基类与管理

| 类                                       | 作用                                   |
| --------------------------------------- | ------------------------------------ |
| `DraggableWidget(QWidget)`              | 可拖拽组件基类（移动、缩放手柄、选中框、编辑/删除按钮）         |
| `DraggableContainer(DraggableWidget)`   | 带配置存储的容器基类，所有具体组件的父类                 |
| `ComponentManager`                      | 组件实例生命周期 / 布局 / 持久化管理                |
| `ComponentConfigDialog(MessageBoxBase)` | 组件配置弹窗（独立配置，parent 到 MainWindow）     |
| `ComponentCard(CardWidget)`             | 组件库中的卡片项                             |
| `CategoryPage(ScrollArea)`              | 组件库分类页                               |
| `ComponentLibraryWindow(FluentWindow)`  | 组件库窗口（固定 650×550），加载 `component.qss` |

### 3.2 编辑模式约定

- 编辑/删除按钮：48×48px，22px 图标，8px 间距；hover 色 编辑 `(0,120,212)` / 删除 `(220,80,80)`；直接使用全局 `componentCardOpacity` / `componentCardRadius`，无值限制。
- 选中框：主题色（`#30c361`），2px 边框，距组件边 3px，圆角 8；外层 4 层同色发光（alpha=60）。
- 调整柄：右下角圆弧柄（`arc_r=18`），外层 7px + 内层 4px，非 8 点方形手柄。
- 编辑模式：`_GridOverlay` 网格 + `GuideLineOverlay` 参考线（无黑色遮罩）。
- 组件移动事件必须触发按钮重新定位。

### 3.3 内置组件清单

| 分类          | 组件类                                                     | 说明                                                                          |
| ----------- | ------------------------------------------------------- | --------------------------------------------------------------------------- |
| Clock       | `DigitalClockComponent`                                 | 数字时钟（秒/农历）                                                                  |
| Clock       | `CalendarMonthComponent`                                | 月历（`_DayCell`）                                                              |
| Weather     | `WeatherIconTempComponent`                              | 图标 + 温度                                                                     |
| Weather     | `WeatherHourlyComponent`                                | 逐小时预报                                                                       |
| Weather     | `WeatherWeeklyComponent`                                | 每周预报                                                                        |
| Poetry      | `PoetryOneLineComponent`                                | 一言                                                                          |
| News        | `NewsBaidu/Weibo/Jinritoutiao/Tenxunwang/CCTVComponent` | 新闻（继承 `NewsComponent`）                                                      |
| Countdown   | `CountdownEventComponent`                               | 事件倒计时                                                                       |
| Countdown   | `TimerCountdownComponent`                               | 计时器（`TimeColumnWidget` / `TimerTimeDisplayWidget`）                          |
| School      | `SchoolInfoComponent`                                   | 学校班级信息                                                                      |
| Media       | `MediaPlayerComponent`                                  | 媒体播放信息（封面/进度/歌词）                                                            |
| QuickLaunch | `QuickLaunchDockComponent` / `QuickLaunchDock`          | 快捷启动栏                                                                       |
| Timetable   | `TimetablePreviewComponent`                             | 课表预览（`_TimetableRow`）                                                       |
| Timetable   | `TimetableNowLessonComponent`                           | 当前课程                                                                        |
| Tool        | `CalculatorComponent`                                   | 计算器                                                                         |
| Tool        | `WritingPadComponent`                                   | 手写画板（`_WritingOverlay` / `_PenSettingsPopup` / `_OverToolBtn`，16ms 定时器擦除架构） |
| Tool        | `NavigationPage`                                        | 导航页（`NavItemCell`）                                                          |
| Album       | `ClassAlbumHorizontal/VerticalComponent`                | 班级相册（继承 `ClassAlbumBaseComponent`）                                          |
| Note        | `StickyNoteComponent`                                   | 便签                                                                          |

### 3.4 媒体组件

- `MediaWidget`：媒体信息展示（标题/艺术家/封面/进度/歌词）。
- `LyricsWidget`：歌词逐行高亮渲染。
- `MediaProgressBar(ProgressBar)`：进度条，默认色 `#30c361`（`cfg.mediaProgressColor`），非激活 `#FFFFFF1A`（`cfg.mediaProgressTrackColor`）。
- 后台抓取：`FetchWorker` / `_MediaFetchWorker` / `_KugouThumbWorker`（酷狗封面）。
- **媒体组件需 500ms 延迟后启动媒体检测**以保证初始化。

### 3.5 手写画板（擦除）架构

- 永久层 `_buffer` 做实际擦除，临时层渲染光标。
- **16ms 定时器循环驱动**（非事件驱动），避免输入停止时半径冻结。
- 擦除速度：`(上次速度 + 欧氏距离) * 0.5` EMA。
- `drawingScale = min(屏宽/1920, 屏高/1080)`。
- 光标：灰色 `(130,130,130,200)` 3px 空心圆，实时调大小，输入停止时消失。
- 严格复刻 Inkeys 算法：速度用欧氏距离，鼠标/触控用特定曲线，双变量平滑追随。

***

## 4. wallpaper.py — 壁纸管理

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/wallpaper.py) · QSS：`wallpaper.qss`

### 4.1 主要类

| 类                                                    | 作用                                      |
| ---------------------------------------------------- | --------------------------------------- |
| `WallpaperInterface(ScrollArea, TranslatableWidget)` | 壁纸主界面                                   |
| `WallpaperRecord`                                    | 单条壁纸记录（路径/来源/URL/时间）                    |
| `WallpaperHistory`                                   | 历史记录管理（持久化 + 数量限制 `wallpaperSaveLimit`） |
| `WallpaperInfoCard(CardWidget)`                      | 当前壁纸信息卡                                 |
| `WallpaperPreviewDialog(MessageBoxBase)`             | 壁纸预览                                    |
| `WallpaperThumbnailCard(CardWidget)`                 | 缩略图卡片                                   |
| `WallpaperHistoryWidget(QWidget)`                    | 历史缩略图列表                                 |
| `_ShrinkableWidget(QWidget)`                         | 可收缩容器                                   |

### 4.2 关键能力

- 多 API 源获取壁纸（`_getApiUrl` 按 `cfg.wallpaperApi`）。
- 模糊 / 亮度效果（`_applyEffects`，调用 `Glimpseon_native`）。
- 设为桌面壁纸（`Glimpseon_native` wallpaper 接口）。
- 自动同步到桌面（`autoSyncToDesktop`）。
- 历史记录与数量管理（`_manageWallpaperLimit`）。
- `wallpaperChanged` 信号通知主界面更新背景。

***

## 5. notification.py — 通知管理

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/notification.py) · QSS：`notification.qss`

| 类                                                  | 作用              |
| -------------------------------------------------- | --------------- |
| `NotificationPage(ScrollArea, TranslatableWidget)` | 通知编辑/预览/队列/定时发送 |
| `_PreviewWidget(QWidget)`                          | 通知预览            |
| `_ConfigEditDialog(Dialog)`                        | 通知配置编辑          |

**信号**：`send_notification` → 连接到 `NotificationManager.handle_notification`；`notification_finished` 回调 `_on_notification_shown`。

***

## 6. timetable.py — 课程表

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/timetable.py) · QSS：`timetable.qss`

`TimetablePage(ScrollArea, TranslatableWidget)`：课程表编辑、时间安排、课程管理。配合 `core/timetable.py` 与 `core/linkage.py`。

***

## 7. download.py — 软件下载中心

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/download.py) · QSS：`download.qss`

`DownloadInterface(BaseScrollAreaInterface, TranslatableWidget)`：

- 按 `SOFTWARE_CATEGORIES`（`resource/software_list.py`）分节展示。
- 支持多源下载、批量下载、软件详情。
- 图标来自 `resource/software_icon/`（`get_software_icon_path`）。
- 链接来自 `resource/url_dir.py` 的 `url_dir`。
- `_onDataPopulated()` 在数据填充后回调。
- `_onThemeChanged` 响应主题切换。

***

## 8. settings.py — 设置窗口

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/settings.py) · QSS：`setting.qss`

### 8.1 自定义设置卡片

| 类                                             | 作用     |
| --------------------------------------------- | ------ |
| `LineEditSettingCard` / `TextLineSettingCard` | 行编辑    |
| `SpinBoxSettingCard`                          | 数值     |
| `SyncStatusSettingCard`                       | 同步状态显示 |
| `AutoOffsetSettingCard`                       | 自动时间偏移 |
| `ButtonSettingCard` / `DualButtonSettingCard` | 按钮触发   |

### 8.2 设置子页

`SettingsSubPage(ScrollArea)` 为基类，子页：

| 子页               | 内容                                                                             |
| ---------------- | ------------------------------------------------------------------------------ |
| `GeneralPage`    | 通用（关闭动作、多实例、自启、空闲、更新）                                                          |
| `TimePage`       | 时间（时钟、农历、偏移、NTP）                                                               |
| `AppearancePage` | 外观（主题、颜色、模糊、壁纸亮度）                                                              |
| `LogPage`        | 日志（级别、禁用、数量、天数）                                                                |
| `AdvancedPage`   | 高级（GPU、调试、下载源）                                                                 |
| `GridPage`       | 网格（格子数、边距、卡片透明度/圆角，含 `_GridPreviewWidget` / `_CornerRadiusPreviewWidget` 实时预览） |

### 8.3 SettingsWindow

`SettingsWindow(FluentWindow)`：独立 FluentWindow，承载上述子页。

***

## 9. about.py — 关于

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/about.py) · QSS：`about.qss`

- `AboutInterface(ScrollArea, TranslatableWidget)`：版本信息、链接卡片、更新检查（`checkUpdateAuto`）、鸣谢。
- `_TechDialog(MessageBoxBase)`：依赖库与许可证弹窗（数据来自 `resource/credits.json`）。

***

## 10. debug.py — 调试面板

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/debug.py) · QSS：`debug.qss`

`DebugPanel(BaseScrollAreaInterface, TranslatableWidget)`：系统监控、快捷操作、网络诊断、API 测试。仅在 `debugMode` 为真时显示于导航底部，`F12` 快速跳转。`_updateTheme` 响应主题。

***

## 11. 跨界面约定

### 11.1 主题切换链

`MainWindow._initThemeConnections()` 将 `cfg.themeChanged` 连接到各界面的 `_onThemeChanged`：

```
cfg.themeChanged → downloadInterface / wallpaper / notificationPage /
                   timetablePage / aboutInterface / _onDebugPanelThemeChanged
```

切换流程：`_onThemeModeChanged` → `clear_qss_cache()` → `setTheme()` → 若未触发则手动 `cfg.themeChanged.emit()` → 各界面重载 QSS。

### 11.2 国际化

所有界面继承 `TranslatableWidget`，`tr()` 取键。语言切换会弹出重启确认框（`_onLanguageConfigChanged`）。

### 11.3 QSS 映射表

| 界面           | QSS 文件             |
| ------------ | ------------------ |
| Home / 部分组件  | `home.qss`         |
| 组件库 / 配置弹窗   | `component.qss`    |
| Wallpaper    | `wallpaper.qss`    |
| Notification | `notification.qss` |
| Timetable    | `timetable.qss`    |
| Download     | `download.qss`     |
| Settings     | `setting.qss`      |
| About        | `about.qss`        |
| Debug        | `debug.qss`        |
| 启动闪屏 / 向导    | `app.qss`          |

