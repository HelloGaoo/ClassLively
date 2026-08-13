# 服务模块（services/）

`services/` 是数据获取层，从网络或系统获取外部数据。所有服务统一使用 `core.utils` 的文件缓存机制（`save_cache` / `get_cached_content`）减少请求。

[包导出](file:///e:/260523/py/Glimpseon/app-1.0.0/services/__init__.py)：`from .media import *`、`PoetryService`、`WeatherService`、`NewsService`。

***

## 1. weather.py — 天气服务

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/services/weather.py)

### 1.1 数据源

- API：`https://weatherapi.market.xiaomi.com/wtr-v3/weather/all`（小米天气接口）
- 鉴权：固定 `APPKEY=weather20151024`、`SIGN=zUFJoAR2ZVrDy1vF3D07`
- 入参：经纬度（`cfg.latitude` / `cfg.longitude`）

### 1.2 主要类

| 类                                      | 作用                                                                           |
| -------------------------------------- | ---------------------------------------------------------------------------- |
| `WeatherService`                       | 天气获取主服务，含天气代码映射表 `WEATHER_MAP` / `ICON_MAP` / `WEATHER_TEXT_MAP`             |
| `RegionDatabase`                       | 基于 SQLite 读取 `resource/city.db`，提供 `get_coordinates(city_name) → (lon, lat)` |
| `RegionSelectorDialog(MessageBoxBase)` | 城市选择对话框（搜索 + 列表）                                                             |

### 1.3 天气代码体系

- `WEATHER_MAP`：0\~20 基础天气代码 → 中文名 + SVG 文件名。
- `ICON_MAP`：扩展天气代码（含 21\~99）→ 图标 SVG 映射。
- `WEATHER_TEXT_MAP`：天气代码 → i18n 键（如 `weather.sunny`），通过 `tr()` 翻译。
- 图标资源位于 `resource/icons/weather/`，含 `alerts/`（蓝/橙/红/黄预警）与 `reminders/`（高低温/降雨提醒）。

### 1.4 刷新与缓存

- `fetch_all()`：一次拉取当前温度、天气代码、逐小时、每日预报。
- 刷新间隔由 `cfg.weatherUpdateInterval`（`5m/15m/30m/1h/.../24m/never`）控制。
- 缓存键 `"weather"`，由 `Preloader._load_wt` 预加载。

***

## 2. poetry.py — 一言服务

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/services/poetry.py)

### 2.1 配置

- API：`cfg.poetryApiUrl`，默认 `https://www.ffapi.cn/int/v1/shici`
- 回退文案：`tr("poetry.default")`
- 刷新间隔：`cfg.poetryUpdateInterval`

### 2.2 PoetryService

| 方法                         | 作用                      |
| -------------------------- | ----------------------- |
| `get_poetry(api_url=None)` | 直接请求 API，返回纯文本；失败返回回退文案 |
| `get_poetry_with_cache()`  | 带缓存读取，缓存键 `"poetry"`    |

***

## 3. news.py — 新闻服务

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/services/news.py)

### 3.1 数据源

| 平台                   | API                                                       |
| -------------------- | --------------------------------------------------------- |
| 央视新闻                 | `https://api.xcvts.cn/api/hotlist/ysxw?type=json`         |
| 百度 / 微博 / 今日头条 / 腾讯网 | `https://orz.ai/api/v1/dailynews/`（`SUPPORTED_PLATFORMS`） |

### 3.2 NewsService

- `_create_session()`：带浏览器 UA 的 `requests.Session`。
- `fetch_cctv_news(use_cache=True)`：央视新闻列表，缓存键 `news_cctv`。
- 各平台热点抓取，缓存间隔统一 `30m`。
- 图标映射见 `core/constants.py` 的 `NEWS_ICONS`（`resource/icons/news/*.svg`）。

***

## 4. media.py — 媒体服务

[源码](file:///e:/260523/py/Glimpseon/app-1.0.0/services/media.py)

**职责**：从多个本地播放器获取正在播放的媒体信息（标题/艺术家/封面/进度/歌词）。

### 4.1 数据模型

| 类                     | 作用                                           |
| --------------------- | -------------------------------------------- |
| `MediaInfo`           | 媒体信息（标题、艺术家、专辑、时长、进度、封面、歌词等），`is_valid()` 校验 |
| `SongDetail`          | 歌曲详情                                         |
| `LyricLine`           | 单行歌词（时间戳 + 文本）                               |
| `Lyrics`              | 歌词集合                                         |
| `parse_lrc(lrc_text)` | LRC 文本解析为 `List[LyricLine]`                  |

### 4.2 媒体源（Reader）

`MediaProvider` 按顺序尝试多个源，首个返回有效信息者胜出：

| 源类                  | 名称                | 数据获取方式                           |
| ------------------- | ----------------- | -------------------------------- |
| `NeteaseCloudMusic` | NeteaseCloudMusic | 网易云音乐 API/内存读取（貌似最近更新Windows接口了） |
| `QQMusicReader`     | QQMusic           | QQ 音乐内存/接口读取                     |
| `KugouMemoryReader` | Kugou             | 酷狗音乐内存读取                         |
| `GSMTCReader`       | GSMTC             | Windows GSMT                     |

每个源实现 `available` 属性、`get_info() → MediaInfo`、`close()`。

### 4.3 调度器与公共 API

- `MediaProvider`：维护源列表，`get_info()` 顺序探测；`_last_media_key` 去重日志。
- `_get_provider()`：懒加载单例。
- `get_media_info()`：快捷入口。
- `get_netease()` / `get_gstmtc()`：获取特定源实例。
- `fetch_all_info(song_name, artist)`：聚合多源补全（歌词、封面）。
- `close()`：释放所有源资源。

### 4.4 与 UI 协作

- UI 端 `MediaWidget` 通过 `_MediaFetchWorker`（QObject）后台调用 `get_media_info()`。
- `_KugouThumbWorker`：酷狗封面缩略图抓取。
- **媒体组件需 500ms 延迟启动检测**（见项目 memory 约束）。
- 进度条默认色：激活 `#4cc2ff`，非激活 `#FFFFFF33`。

***

## 5. 跨服务约定

### 5.1 缓存

所有服务使用 `core.utils.save_cache(name, content, interval_str)` 与 `get_cached_content(name)`。缓存文件位于 `DATA_CACHE`，结构含 `content` + `expiry` 时间戳。

### 5.2 日志

子模块日志器命名 `Glimpseon.services.{module}`，遵循层级命名约定。

### 5.3 预加载

壁纸 / 天气 / 一言在启动期由 `Preloader`（QThread）并行预加载，通过信号回主线程，避免 UI 卡顿。详见 [启动流程](launch-flow.md)。

### 5.4 错误处理

- 网络异常统一 `try/except` + `logger.error`，返回 `None` 或回退值。
- 不向上抛出，保证 UI 始终拿到可渲染数据。

