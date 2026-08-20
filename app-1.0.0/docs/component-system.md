# 组件系统

> [!NOTE]
> 编写者：HelloGaoo　最后修改：2026/08/20

Glimpseon 定位是桌面信息看板，已编写了注册组件等函数，每个组件独立类，与主页面沟通能做到拖拽、删除、配置相关操作

[核心定义](file:///e:/260523/py/Glimpseon/app-1.0.0/core/component.py) · [UI 实现](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py)

***

## 1. 数据模型（core/component.py）

### 1.1 ResizeMode

```python
class ResizeMode(Enum):
    FIXED = "fixed"           # 固定尺寸
    HORIZONTAL = "horizontal" # 仅水平调整
    VERTICAL = "vertical"     # 仅垂直调整
    FREE = "free"             # 自由调整
```

### 1.2 ComponentDefinition

组件类型的元数据描述：

| 字段                                             | 类型         | 说明     |
| ---------------------------------------------- | ---------- | ------ |
| `id`                                           | str        | 唯一标识   |
| `display_name`                                 | str        | 显示名称   |
| `category`                                     | str        | 分类     |
| `icon`                                         | str        | 图标名    |
| `min_width_cells` / `min_height_cells`         | int        | 最小格子数  |
| `default_width_cells` / `default_height_cells` | int        | 默认格子数  |
| `resize_mode`                                  | ResizeMode | 调整模式   |
| `component_class`                              | Type       | UI 实现类 |
| `default_config`                               | dict       | 默认配置   |

支持 `to_dict()` / `from_dict()`

### 1.3 GridSettings / GridMetrics

```python
@dataclass
class GridSettings:
    short_side_cells: int = 6   # 短边格子数（cfg.gridShortSideCells）
    gap_ratio: float = 0.12     # 间隙比例
    inset_percent: int = 5      # 边距百分比（cfg.gridInsetPercent）

@dataclass
class GridMetrics:
    column_count, row_count     # 行列数
    cell_size                   # 单格像素
    gap_px                      # 间隙像素
    edge_inset_px               # 边距像素
    grid_width_px / grid_height_px  # 网格完整尺寸
```

### 1.4 PageMeta / PageManager

页面分两种类型：

| `type`   | 内容                       |
| -------- | ------------------------ |
| `"info"` | 组件页，含 `components` 列表    |
| `"nav"`  | 导航页，含 `items` 列表（应用快捷方式） |

`PageManager` 负责页面 CRUD 与持久化，配置文件 `data/config/home_layout.json`：

```json
{
  "current_page": 0,
  "pages": [
    {
      "name": "信息页",
      "type": "info",
      "components": [
        {"id":"...", "type":"...", "style":"...",
         "position":{"x":0.5,"y":0.5}, "size":{"w":200,"h":80},
         "enabled": true, "config": {}}
      ]
    },
    {"name":"导航页","type":"nav","items":[
      {"name":"...","path":"...","icon":"...","type":"app"}
    ]}
  ]
}
```

- 默认 2 页（信息页 + 导航页），`MAX_PAGES = 10`。

***

## 2. 网格布局算法（GridLayoutService）

### 2.1 calculate\_grid\_metrics

输入画布尺寸 + `GridSettings`，输出 `GridMetrics`。

```
edge_inset_px = min(80, base_cell * inset_percent/100)
            其中 base_cell = short_side_px / short_side_cells

若横向 (width >= height):
    row_count = short_side_cells
    denominator = row_count + (row_count-1)*gap_ratio
    cell_size = available_height / denominator
    gap_px = cell_size * gap_ratio
    pitch = cell_size + gap_px
    column_count = int((available_width + gap_px) // pitch)
若纵向:
    column_count = short_side_cells
    ...（对称）
```

### 2.2 坐标换算

- `get_cell_rect(metrics, col, row, w_cells, h_cells) → QRect`：格子坐标 → 屏幕像素矩形。
- `point_to_cell(metrics, point) → (row, column)`：屏幕点 → 格子坐标，**网格外或间隙中返回** **`(-1, -1)`**。

### 2.3 碰撞检测

`check_collision(placements, target_row, target_col, w, h, exclude_id, page_index)`：同页、已启用、非自身的组件矩形是否重叠。`_rects_overlap` 用行列闭区间判断。

***

## 3. 组件注册（ComponentRegistry）

```python
class ComponentRegistry(QObject):
    definitions_changed = pyqtSignal()
```

| 方法                                          | 作用              |
| ------------------------------------------- | --------------- |
| `register(definition)`                      | 注册单个，发信号        |
| `register_batch(definitions)`               | 批量注册            |
| `unregister(id)`                            | 注销              |
| `get_definition(id)` / `has_definition(id)` | 查询              |
| `get_all_definitions()`                     | 全部              |
| `get_definitions_by_category(cat)`          | 按分类             |
| `get_categories()`                          | 所有分类            |
| `load_from_json(path, component_classes)`   | 从 json 加载并绑定实现类 |

### 内置组件

`BUILTIN_COMPONENT_DEFINITIONS` 预定义组件（数字时钟、月历等），仅用于组件库窗口展示卡片。注意：这些 `ComponentDefinition` 的 `component_class` 字段默认为 `None`，**不参与实例化**——实际创建 UI 走 [ui/component.py](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py) 的 `COMPONENT_STYLES`（见第 9 章）。

***

## 4. UI 实现层（ui/component.py）

### 4.1 类层次

```
QWidget
 └─ DraggableWidget                # 拖拽/缩放/选中/按钮 基类
     └─ DraggableContainer         # 含配置存储的容器基类
         ├─ DigitalClockComponent
         ├─ WeatherComponentBase
         │   ├─ WeatherIconTempComponent
         │   ├─ WeatherHourlyComponent
         │   └─ WeatherWeeklyComponent
         ├─ PoetryOneLineComponent
         ├─ NewsComponent
         │   └─ NewsBaidu/Weibo/...Component
         ├─ HistoryTodayComponent
         ├─ DailyWordComponent
         ├─ CountdownEventComponent
         ├─ TimerCountdownComponent
         ├─ SchoolInfoComponent
         ├─ MediaPlayerComponent
         ├─ QuickLaunchDockComponent
         ├─ TimetablePreviewComponent
         ├─ TimetableNowLessonComponent
         ├─ CalculatorComponent
         ├─ WritingPadComponent
         ├─ ClassAlbumBaseComponent
         │   ├─ ClassAlbumHorizontalComponent
         │   └─ ClassAlbumVerticalComponent
         ├─ StickyNoteComponent
         ├─ CalendarMonthComponent
         └─ NavigationPage
```

### 4.2 DraggableWidget 编辑能力

- **选中框**：主题色（`_cached_primary_color`，默认 `#30c361`），2px 边框（alpha=200），距组件边 3px，圆角 8；外层 4 层同色发光（alpha=60，逐层 `widthF=i*2`），距边 4px。
- **调整柄**：右下角圆弧柄（`arc_r=18`，drawArc `-30°~-90°`），外层 7px（alpha=220，`darker(150)`）+ 内层 4px（alpha=230）。非传统 8 点方形手柄。
- **编辑/删除按钮**：48×48px，22px 图标，8px 间距；悬停色 编辑 `(0,120,212)` / 删除 `(220,80,80)`。
- **按钮直接使用全局** **`componentCardOpacity`** **/** **`componentCardRadius`**，无值限制。
- **移动事件触发按钮重定位。**

### 4.3 ComponentManager

管理组件实例的生命周期、布局应用、持久化加载/保存，协调 `ComponentRegistry`、`GridLayoutService`、`PageManager`。

### 4.4 ComponentConfigDialog

`ComponentConfigDialog(MessageBoxBase)`：组件配置弹窗。

> \[!IMPORTANT]
> 约束：配置面板必须 parent 到 MainWindow（而非组件或设置窗口），以确保正确的 z-order（不被主界面遮挡）。每个组件配置独立存储。

### 4.5 组件库窗口

`ComponentLibraryWindow(FluentWindow)`：

- 尺寸 **650×550**。
- 加载 `resource/qss/{light,dark}/component.qss`。
- `CategoryPage` 按分类展示 `ComponentCard`，用户点击卡片添加组件到当前页。

***

## 5. 编辑模式交互

### 5.1 进入/退出

`HomeInterface.isEditMode` 切换。编辑模式下：

- 显示 `_GridOverlay` 网格背景。
- 显示 `GuideLineOverlay` 参考线。
- 组件显示选中框（主题色）、右下角圆弧调整柄、编辑/删除按钮。

### 5.2 拖拽与缩放

- 拖拽：`DraggableWidget` 处理鼠标事件，按 `ResizeMode` 限制方向。
- 吸附：基于 `GridLayoutService` 的格子坐标对齐。
- 碰撞：`check_collision` 阻止重叠放置。
- 缩放：**整体等比缩放**——拖拽右下角圆弧柄时 `scale = max(scale_w, scale_h)` 等比缩放外框；内部所有视觉元素（字号/图标/图片/固定尺寸/边距/间距）跟随 `_scale_factor` 同步等比变化。

#### 缩放机制（DraggableContainer）

| 成员                    | 作用                                                                                                                          |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `_scale_factor`       | 当前缩放因子，由 `resizeEvent` 按 `当前尺寸 / natural_size` 的宽高最小值计算（`min(sw, sh)`），下限 0.3；始终跟随最新尺寸，变化 ≥0.02 时才要求重应用样式                   |
| `_scaled_px(base)`    | `max(1, int(base * _scale_factor))`，子类字号/图标/固定尺寸/圆角统一经它缩放                                                                   |
| `apply_scale(factor)` | 子类按 factor 重应用样式；由基类在缩放变化时调用                                                                                                |
| `_scale_layouts()`    | 遍历 `findChildren(QLayout)`，按 `_scale_factor` 等比缩放所有子布局的 `contentsMargins` 与 `spacing`；首次调用缓存基准值（`_layout_bases`），后续始终基于基准重算 |
| `_applied_factor`     | 上次已应用到样式的缩放因子，判断是否还有未应用的差异                                                                                                  |
| `_scale_timer`        | 拖拽缩放节流定时器（周期 30ms）                                                                                                          |
| `_apply_scale_now()`  | 统一入口：执行 `apply_scale` + `_scale_layouts` 并同步 `_applied_factor`                                                              |

流程：拖拽缩放 → `resizeEvent` 更新 `_scale_factor` → 与 `_applied_factor` 差异>0.001时启动 `_scale_timer` → 每 30ms 周期触发 `_apply_scale_now()` 跟随 → 松手停止定时器应用最终状态（`mouseReleaseEvent`）。

### 5.3 统一卡片背景（DraggableContainer）

> \[!IMPORTANT]
> **所有组件必须使用**：`_apply_card_style()` / `_card_bg_css()`。背景跟随全局设置 `componentCardOpacity` / `componentCardRadius`（浅色 `rgb(255,255,255)`，深色 `rgb(30,30,30)`，透明度=全局卡片透明度），支持组件覆盖。

基类 `DraggableContainer` 提供了统一的卡片背景：

| 成员                       | 说明                                                                                      |
| ------------------------ | --------------------------------------------------------------------------------------- |
| `_bg_opacity`            | 组件级不透明度覆盖（0\~100）；`None` 时回退全局 `cfg.componentCardOpacity.value`                         |
| `_corner_radius`         | 组件级圆角覆盖（px）；`None` 时回退全局 `cfg.componentCardRadius.value`                                |
| `_bg_mode`               | `"opacity"`（默认，跟随全局透明度）/ `"custom"`（使用 `_bg_color`）                                     |
| `_bg_color`              | `"custom"` 模式下的背景颜色（如 `"#ffffff"`）                                                      |
| `_card_bg_css(...)`      | 返回一段 QSS：`#objName { background-color: rgba(...); border-radius: Npx; [border: ...;] }` |
| `_apply_card_style(...)` | 把该 QSS 应用到 `target`（默认 `self`，取 `target.objectName()`）                                  |

`_apply_card_style(target=None, obj_name=None, bg_mode=None, bg_color=None, opacity=None, radius=None, border=None)`：

- `opacity` / `radius` 传 `None` 即使用 `self._bg_opacity` / `self._corner_radius`，再为 `None` 则回退全局设置。
- `border` 可选，用于给背景追加边框（如 `"1px solid rgba(0,0,0,0.06)"`，媒体播放器用）。

`cfg.componentCardOpacity`、`cfg.componentCardRadius` 或 `cfg.themeChanged` 变化时，基类自动触发 `_on_card_config_changed()` → 重应用背景并调用子类 `_apply_style()`，因此全局设置/主题变化无需每个组件单独监听。组件级 `bg_opacity` / `corner_radius` 由配置面板写入 `component_data["config"]`，经基类 `apply_config(config)` 读取生效。

**组件在** **`_apply_style()`** **中的两种标准写法（二选一）：**

```python
# 写法 A：背景与子控件样式分离（推荐）
def _apply_style(self):
    self._apply_card_style()                 # 容器背景跟随全局设置
    self.someLabel.setStyleSheet("...")      # 子控件只设文字/透明背景

# 写法 B：整份样式表覆盖 self 时，把卡片背景拼到最前面
def _apply_style(self):
    bg_css = self._card_bg_css()             # 用统一方法生成容器背景
    self.setStyleSheet(f"""
        {bg_css}
        #someContainer {{ ... }}
    """)
```

> \[!WARNING]
> 写法 B 必须把 `{self._card_bg_css()}` 拼进 `setStyleSheet`，因为 `setStyleSheet` 会**整体替换**原样式表——若只调 `_apply_card_style()` 再 `setStyleSheet(...)`，背景会被覆盖丢失（今日课表 `TimetablePreviewComponent` 曾因此无背景）。

### 5.4 多页与页面状态

- `PageIndicator`：多页小圆点。
  - **响应左/右键点击切换页**
- 页面切换由 `PageManager._current_page` 控制。

***

## 6. 手写画板（WritingPadComponent）

> \[!NOTE]
> 本章算法部分由 AI 基于源码（`ui/component.py` 中 `_WritingOverlay`，约 L7094–L7853）生成，如与实际实现有出入，请以源码为准。

手写画板主要是 `_WritingOverlay`（全屏透明覆盖层，`FramelessWindowHint | Tool`，`WA_TranslucentBackground`）。通过 Windows `WM_POINTER` 只读触控点（`PT_TOUCH`），并防止 Qt 重复派发 mouse event。擦除功能采用**定时器循环驱动**，参考项目 Inkeys 的算法实现。

相关类：`_WritingOverlay`（覆盖层主体）、`_PenSettingsPopup`（画笔设置）、`_OverToolBtn`（悬浮工具栏按钮）。

### 6.1 分层结构与渲染

| 层   | 载体                   | 作用                                     |
| --- | -------------------- | -------------------------------------- |
| 永久层 | `_buffer`（QPixmap）   | 实际笔画与擦除发生处，`paintEvent` 中 `drawPixmap` |
| 临时层 | `_temp_pixmaps[tid]` | 直线/矩形等形状的实时预览（抬笔前不落盘）                  |
| 光标层 | `paintEvent` 绘制      | 橡皮光标，每帧重绘，不写入 buffer                   |

`paintEvent` 顺序：白板背景（若开启）→ `_buffer` → 各 `_temp_pixmaps` → `_render_erase_cursor`。

### 6.2 三个定时器

| 定时器                  | 间隔           | 回调                     | 职责                                                          |
| -------------------- | ------------ | ---------------------- | ----------------------------------------------------------- |
| `_touch_timer`       | 0ms          | `_process_touch_queue` | 消费触控事件队列 `_touch_queue`（`deque` + `threading.Lock` 线），按模式分发 |
| `_erase_speed_timer` | 50ms（20fps）  | `_sample_erase_speed`  | 采样擦除速度                                                      |
| `_erase_loop_timer`  | 16ms（≈60fps） | `_erase_loop_tick`     | 擦除主循环                                                       |

### 6.3 drawingScale

```python
drawingScale = min(主屏宽 / 1920.0, 主屏高 / 1080.0)
```

用于将基准直径缩放到当前屏幕分辨率，保证不同分辨率下擦除范围视觉一致。

### 6.4 擦除状态（按 tid 分组）

`tid == 0` 为鼠标，其余为触控点 ID。每个 tid 维护：

| 状态                        | 含义            |
| ------------------------- | ------------- |
| `_erase_prev_pos[tid]`    | 上一次擦除位置       |
| `_erase_live_pos[tid]`    | 最新实时位置        |
| `_erase_prev_sample[tid]` | 上一次速度采样位置     |
| `_erase_speed[tid]`       | 当前速度（EMA 平滑值） |
| `_erase_rubber[tid]`      | **当前实际橡皮直径**  |
| `_erase_trubber[tid]`     | **目标橡皮直径**    |
| `_erase_cursors[tid]`     | 光标渲染数据        |

### 6.5 完整流程

#### 6.5.1 触控采集（nativeEvent）

`WM_POINTERDOWN / WM_POINTERUPDATE / WM_POINTERUP` → 校验 `PT_TOUCH` → 提取坐标 → `_push_touch_event(ev_type, tid, pos)` 入队，并返回 `True` 拦截消息。

#### 6.5.2 事件分发（\_process\_touch\_queue）

批量取出队列，擦除模式下 `DOWN/UPDATE` 调 `_erase_at`，`UP` 清理该 tid 全部状态；所有手指抬起且非鼠标按下时，停 16ms 循环并 `_end_erase_session`。

#### 6.5.3 速度采样（\_sample\_erase\_speed，50ms）

对每个活跃 tid，计算与上次采样点的欧氏距离 `dist`：

```python
speed = (speed + dist) * 0.5   # EMA 50/50 平滑
```

首次采样 `speed = 1.0`。速度由 20fps 定时器采样

#### 6.5.4 擦除入口（\_erase\_at）

- **首次按下**：初始化全部状态，`rubber = drawingScale * ERASE_INIT(20.0)`，`trubber = -1.0`，立即在 buffer 上擦除一个点，加入 `_erase_session`，设光标，启动 16ms 循环。
- **后续移动**：**仅更新** **`_erase_live_pos[tid]`**，由 16ms 循环统一处理。

#### 6.5.5 擦除主循环（\_erase\_loop\_tick，16ms）

对每个活跃 tid：

**① 计算目标直径 t\_size（鼠标与触控分别独立）**

```python
if tid == 0:                      # 鼠标
    if speed <= 30:
        t_size = max(ERASE_BASE_MIN, speed * 2.33 + 2.33)   # 25 起步
    else:
        t_size = min(ERASE_BASE_MAX, speed + 30)            # 上限 200
else:                             # 触控
    if speed <= 20:
        t_size = max(ERASE_BASE_MIN, speed * 2.33 + 13.33)
    else:
        t_size = min(ERASE_BASE_MAX, 3.0 * speed)
```

常量：`ERASE_BASE_MIN = 25.0`、`ERASE_BASE_MAX = 200.0`、`ERASE_INIT = 20.0`。

`trubber = t_size * drawingScale`

**② 当前直径 rubber 平滑追随目标 trubber（双变量追随）**

```python
if rubber < trubber:
    rubber += max(0.1, (trubber - rubber) / 50.0)   # 渐增，每帧最多追 1/50
elif rubber > trubber:
    rubber += min(-0.1, (trubber - rubber) / 50.0)  # 渐减
```

该步长保证直径以约 50 帧（≈0.8s）过渡到目标，避免直径突变。

**③ 在 buffer 上擦除**：`_erase_on_buffer(prev_pos, cur_pos, rubber)`，更新 `prev_pos = cur_pos`，记入 `_erase_session`，更新光标。

**④** **`update()`** 触发重绘。

#### 6.5.6 实际擦除（\_erase\_on\_buffer）

使用 `CompositionMode_DestinationOut`（用 alpha=255 的黑色绘制会擦除目标像素）：

- `prev != cur`：`drawLine`（`RoundCap` / `RoundJoin`），笔宽 = diameter
- `prev == cur`：`drawEllipse`（实心圆，半径 = diameter/2）

#### 6.5.7 光标渲染（\_render\_erase\_cursor）

```python
painter.setPen(QPen(QColor(130, 130, 130, 200), 3))   # 灰色 3px
painter.setBrush(Qt.BrushStyle.NoBrush)                # 空心
painter.drawEllipse(pos, diameter / 2.0, diameter / 2.0)
```

每个 tid 一个光标，直径 = 当前 `rubber`，实时反映大小变化。

#### 6.5.8 抬起与历史

- `UP`：清理该 tid 全部状态；全部抬起时停循环、`_end_erase_session`。
- `_erase_session`（`[(pos, diameter), ...]`）作为一个 `("erase", session)` 记入 `_history`。
- 画笔笔画记为 `("draw", stroke)`。

### 6.6 撤回与重建

- `_undo_last_stroke`：`_history.pop()` → `_rebuild_buffer()`。
- `_rebuild_buffer`：清空 `_buffer`，按 `_history` 顺序重放所有 `draw`（重画笔画）与 `erase`（重放擦除点）。
- `clear_all`：清空全部历史与 buffer。

### 6.7 为何用定时器循环而非事件驱动

事件驱动只在有输入时更新，**输入停止时半径会冻结**（无法继续平滑追随/衰减）。16ms 循环持续读取 `_erase_live_pos` 并重算 `rubber`，即使输入暂停也能让 `rubber` 持续向 `trubber` 追随，保证半径连续变化。速度采样独立 20fps，避免每个事件都算速度导致抖动。这是该项目从 Inkeys 复刻并验证过的关键架构。

***

## 7. 媒体组件

> \[!NOTE]
> 本章由 AI 基于源码（`ui/component.py` 中 `MediaPlayerComponent` L1772）生成，如与实际实现有出入，请以源码为准。

媒体组件为**单一** **`MediaPlayerComponent`**（`DraggableContainer` 子类），后台从 `services.media` 获取正在播放的媒体信息（标题/艺术家/封面/进度/歌词）。

### 7.1 类结构

| 类                      | 位置    | 职责                               |
| ---------------------- | ----- | -------------------------------- |
| `MediaPlayerComponent` | L1772 | UI、双定时器、抓取、LRU 缓存、封面动画、播放控制、切歌保护 |

### 7.2 双定时器架构

`MediaPlayerComponent` 用两个定时器分工：

| 定时器           | 间隔                                      | 回调                 | 职责                                    |
| ------------- | --------------------------------------- | ------------------ | ------------------------------------- |
| `_timer`      | `cfg.mediaUpdateInterval * 1000`（默认 1s） | `_poll`            | **完整抓取**（`full=True`）：标题/艺术家/封面/歌词/进度 |
| `_prog_timer` | 1000ms                                  | `_update_progress` | 播放中本地推算进度（不请求网络即更新进度条）                |

- `_update_progress`：若正在播放，本地按 `interval` 推进 `_position`（不请求网络即更新进度条）。
- `start()` 同时启动两个定时器并发起首次 `full=True` 抓取。

### 7.3 线程化抓取与防重入

用 `threading.Thread`（daemon=True）+ pyqtSignal 跨线程回主线程（Qt 自动 queued 连接）：

- `_spawn_media_fetch(full)` → `_media_worker` 线程调 `get_media_info()` → `_media_ready.emit(m, full)` → `_on_media`。
- `_fetch(m)` → `_fetch_detail` 线程调 `get_service(app_name).lyrics/cover/duration()` → `_detail_ready.emit(key, result)` → `_on_detail`。
- **防重入**：`_fetching` 标志，抓取期间若再次请求 `full=True`，置 `_pending_full=True`，完成后 `QTimer.singleShot(100, ...)` 补抓。
- `stop()` 停掉全部定时器（`closeEvent` / `__del__` 均调用），防止线程残留崩溃。

### 7.4 新歌快速更新（rapid update）

检测到 `title_artist` 变化（新歌）时：

```python
self._rapid_update_count = 5
self._timer.setInterval(500)   # 切到 500ms 快速间隔
```

连续 5 次快速抓取后恢复 `_normal_interval`，用于新歌切入时尽快拿到封面/歌词，避免长时间空白。

### 7.5 封面来源优先级

`_display` 中按 `app_name` 分流封面获取：

1. **SMTC 缩略图**：`m.thumbnail_data` 存在 → 直接 `_load_cover`（置 `_has_thumb=True`，优先级最高，不再被在线封面覆盖）。
2. **浏览器**：`is_web_browser` → 标记 `_has_thumb=True`（等待 thumbnail\_data），不触发在线查询。
3. **酷狗**：`app_name == 'Kugou'` → 详情线程内额外借用 SMTC 会话缩略图作封面。
4. **在线补全**：非浏览器 → `_fetch(m)` → 详情线程调 `get_service().lyrics/cover/duration()`，仅在 `not _has_thumb` 时应用封面。

### 7.6 封面动画与阴影

- `_load_cover`：载入后先 `_add_cover_shadow`（4 层渐变阴影 + 圆角裁剪 `SourceAtop`），再 `QPropertyAnimation` 透明度 0→1，300ms `OutCubic` 淡入。
- 默认封面 `_default_cover`：自绘圆角矩形 + 音符图标（主题自适应配色）。

### 7.7 进度条

使用 qfluentwidgets 原生 `ProgressBar`（固定高 3px），不自定义颜色、不覆盖样式。

### 7.8 歌词

- 右侧 `QLabel`（`wordWrap=True`，12px 加粗），替代原自绘 `LyricsWidget`。
- `_update_lyrics(ms)`：`adjusted_ms = ms + cfg.mediaLyricsAdvance`（提前量），`lyrics.get_line_at_time(adjusted_ms)` 定位当前行。

### 7.9 浏览器特殊处理

`_display` 检测 `app_name` 含 `chrome/edge/firefox/msedge`：

- 无 `artist` 时：标题换行显示，隐藏艺术家与歌词行。
- 有 `artist` 时：正常布局。
- 浏览器不触发在线 `_fetch`（避免用网页标题当歌名查询）。

### 7.10 切歌竞态保护

详情补全与轮询抓取异步并行，快速切歌时旧结果可能滞后返回：

- 详情结果携带歌曲 key（`title_artist`），`_on_detail(key, result)` 仅当 key 与当前 `self._media.title_artist` 一致时才应用（`_apply_detail`）。
- 详情线程忙碌时 `_fetch` 记录 `_pending_key`，返回后自动补拉当前歌，不丢请求。
- `_no_media` 重置 `_pending_key`，避免残留脏状态。

### 7.11 LRU 缓存

- `_info_cache`（`OrderedDict`，上限 50）：以 `title_artist` 为 key 缓存详情补全结果。
- 命中时 `pop` 再插入末尾（LRU）；超限时 `popitem(last=False)` 淘汰最久未用。
- `clear_cache()` 清空并 `close_media()` 释放资源。

### 7.12 播放控制

- `_on_play_pause`：先立马更新为播放/暂停 → 后台线程 `media_control(play/pause)` → `_sync_confirm_timer` 轮询 SMTC 真实状态确认（上限约 2 秒解锁）。
- `_on_next` / `_on_prev`：后台线程 `media_next()` / `media_prev()`，800ms 后重新完整拉取。
- 播放状态同步期间旧状态不覆盖图标（`_playing_sync_pending` 标志）。

***

## 8. 持久化与加载流程

```
启动时:
  PageManager.load()
    └─ 读 home_layout.json → PageMeta 列表
  ComponentManager 按当前页 components 实例化
    └─ COMPONENT_STYLES[comp_data["type"]][comp_data["style"]]["class"] → 实现类
    └─ comp_class(parent_widget, comp_data) 创建 UI
    └─ 应用 position/size/config

编辑时:
  拖拽/缩放 → 更新实例 position/size
  配置弹窗 → 更新 config
  保存 → PageManager.save() → home_layout.json
```

> \[!IMPORTANT]
> 组件加载必须在 splash 期间**同步完成**，避免 `QTimer.singleShot(0)` 导致主窗口显示后才加载的延迟。

***

## 9. 扩展新组件

### 9.1 需要理解的组件配置

项目中有两套组件元数据，职责不同，新增组件时都要照顾到：

| 表                               | 位置                                                                                   | 作用                                                                     | 是否参与实例化                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- | --------------------------------------------------------------- |
| `COMPONENT_STYLES`              | [ui/component.py L109](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py)     | `comp_type → comp_style → {name, class, default_config, default_size}` | **是**，`ComponentManager` 据此 `comp_class(parent, comp_data)` 实例化 |
| `BUILTIN_COMPONENT_DEFINITIONS` | [core/component.py L376](file:///e:/260523/py/Glimpseon/app-1.0.0/core/component.py) | `ComponentDefinition` 列表（id/分类/格子数/resize\_mode）                       | 否，仅用于组件库窗口展示卡片                                                  |

组件在 `home_layout.json` 中存储的是 `type` + `style`（如 `"type":"clock","style":"digital"`），而非 `ComponentDefinition.id`。`ComponentManager.load_components()` 通过 `COMPONENT_STYLES[type][style]["class"]` 取实现类。

### 9.2 组件数据结构

每个组件实例在 `home_layout.json` 中形如：

```json
{
  "id": "clock_1",
  "type": "clock",
  "style": "digital",
  "position": {"x": 0.5, "y": 0.5},
  "size": {"w": 400, "h": 200},
  "enabled": true,
  "page_index": 0,
  "config": {}
}
```

### 9.3 新增步骤

假设要新增一个「打卡」组件，type=`checkin`、style=`default`。

**步骤 1：注册到** **`COMPONENT_STYLES`**

在 [ui/component.py L109](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py) 的 `COMPONENT_STYLES` 字典中新增条目。若是全新分类，加一个顶层键：

```python
"checkin": {
    "default": {
        "name": "打卡",
        "class": None,                 # 先置 None，步骤 3 再绑定
        "default_config": {"goal": 100},
        "default_size": (200, 120),
    },
},
```

**步骤 2：实现组件类**

在 `ui/component.py` 中实现，继承 `DraggableContainer`，构造签名固定为 `(self, parent, component_data: dict)`：

```python
class CheckinComponent(DraggableContainer):
    def __init__(self, parent, component_data: dict):
        super().__init__(parent, component_id=component_data["id"],
                         layout_direction="vertical")
        self.setObjectName("checkinContainer")
        self._config = component_data.get("config", {})
        self._setup_ui()          # 构建内部 UI
        self._apply_style()       # 主题相关样式（含统一背景）
        # 可选：监听 cfg 变化、实现 apply_scale(factor) 等

    def _apply_style(self):
        # 必须用统一背景方法，跟随全局 componentCardOpacity / componentCardRadius
        self._apply_card_style()
        # 子控件样式设到这里（文字/透明背景）

    def apply_scale(self, factor):
        # 按 factor 缩放内部元素（参考 MediaPlayerComponent.apply_scale）
        ...
```

要点：

- 通过 `component_data["config"]` 读取独立配置。
- **背景必须走统一方法**：`_apply_style()` 中调 `self._apply_card_style()`；若用整份样式表覆盖自身，则需把 `{self._card_bg_css()}` 拼在样式表最前面（见 [5.3 统一卡片背景](#53-统一卡片背景draggablecontainer)）。不要自行写 `background-color`。
- 实现主题切换响应（`_apply_style` / 重载 `_onThemeChanged`）。
- 若需随缩放，实现 `apply_scale(factor)`：内部字号/图标/固定尺寸/圆角一律用 `self._scaled_px(base)`；子布局边距/间距由基类 `_scale_layouts()` 自动等比缩放，无需手动处理。
- **初始化与** **`apply_scale`** **必须同步**：`_setup_ui` 中用过 `_scaled_px` 的固定尺寸（行高/列宽/图标底图等），`apply_scale` 中必须重新设置，否则缩放后停留在原尺寸。
- 调用 `self._set_natural_size(w, h)` 设自然尺寸，`self._size_explicitly_set = True`。

**步骤 3：绑定 class**

在文件末尾的绑定区（[ui/component.py L8548 附近](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/component.py)）追加：

```python
COMPONENT_STYLES["checkin"]["default"]["class"] = CheckinComponent
```

> \[!WARNING]
> 绑定放在末尾是因为 `COMPONENT_STYLES` 在 L109 定义时类还未定义，必须延后到类定义之后赋值。漏掉此步会导致 `load_components` 报「组件样式未注册」并跳过。

**步骤 4：（可选）加入组件库展示**

若希望该组件出现在组件库窗口供用户添加，在 [core/component.py L376](file:///e:/260523/py/Glimpseon/app-1.0.0/core/component.py) 的 `BUILTIN_COMPONENT_DEFINITIONS` 追加 `ComponentDefinition`：

```python
ComponentDefinition(
    id="checkin_default",
    display_name="打卡",
    category="Tool",
    icon="Checkmark",
    min_width_cells=2, min_height_cells=2,
    default_width_cells=2, default_height_cells=2,
    resize_mode=ResizeMode.FREE,
    default_config={"goal": 100},
),
```

`ComponentRegistry.register_batch(BUILTIN_COMPONENT_DEFINITIONS)`（[home.py L317](file:///e:/260523/py/Glimpseon/app-1.0.0/ui/home.py)）会在启动时注册，组件库窗口据此渲染卡片。

**步骤 5：（可选）配置面板**

若组件需要用户可调配置，实现一个继承 `MessageBoxBase` 的配置对话框，并将其实例的 parent 设为 **MainWindow**（而非组件自身或设置窗口），以保证 z-order 正确、不被主界面遮挡。配置写回 `component_data["config"]` 后调 `ComponentManager.save_components()` 持久化。

**步骤 6：资源与国际化**

- 图标 SVG 放入 `resource/fluent/{light,dark}/`，命名 `ic_fluent_{name}_{24|32}_regular.svg`，通过 `FUI.{NAME}` 引用。
- 文案键加入 `locale/{zh_CN,zh_TW,en_US}.json`，代码用 `tr("key")` 读取。

### 9.4 验证

1. 启动应用，进入编辑模式，打开组件库，确认新组件卡片出现。
2. 点击卡片添加，确认 `home_layout.json` 中生成 `type=checkin, style=default` 条目。
3. 重启应用，确认组件被 `load_components` 正确还原。
4. 切换浅/深主题，确认样式随主题更新。

### 9.5 常见坑

| 现象                   | 原因                                                               |
| -------------------- | ---------------------------------------------------------------- |
| 「组件样式未注册」日志，组件不出现    | 步骤 3 的 `class` 绑定遗漏，或 `type`/`style` 拼写不一致                       |
| 组件库无卡片，但手动改 json 能加载 | 步骤 4 的 `BUILTIN_COMPONENT_DEFINITIONS` 未追加                       |
| 配置弹窗被主界面遮挡           | 弹窗未 parent 到 MainWindow                                          |
| 缩放后内部元素不变            | 未实现 `apply_scale(factor)`；或已实现但字号/尺寸仍硬编码，需改用 `self._scaled_px()` |
| 缩放后固定尺寸停留在初始值        | `_setup_ui` 用了 `_scaled_px` 但 `apply_scale` 未重设（行高/列宽/图标底图等）     |
| 切主题样式不更新             | 未在 `_apply_style` 中重读主题色 / 未连 `cfg.themeChanged`                 |

