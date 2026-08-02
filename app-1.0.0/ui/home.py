# Glimpseon
# Copyright (C) 2026 HelloGaoo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""主界面模块"""

import ctypes
import datetime
import json
import os
import re
import time

from PyQt6.QtCore import (
    QByteArray,
    QDate,
    QEasingCurve,
    QEvent,
    QFileInfo,
    QPropertyAnimation,
    QRect,
    QRectF,
    QPointF,
    QPoint,
    QSize,
    Qt,
    QTime,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
    QFileDialog,
    QFileIconProvider,
)
from qfluentwidgets import (
    InfoBar,
    PushButton,
    MessageBoxBase,
    CalendarPicker,
    TimePicker,
    ComboBox,
    SwitchButton,
    SpinBox,
    LineEdit,
    ListWidget,
    ToolButton,
    StrongBodyLabel,
    BodyLabel,
    SubtitleLabel,
    SmoothScrollArea,
    CardWidget,
    RoundMenu,
    Action,
    isDarkTheme,
)

from core.config import cfg, save_cfg
from core.constants import PACKAGE_ROOT, DATA_CONFIG, load_qss
from core.logger import logger
from core.utils import tr, TranslatableWidget, precise_now, FUI
from resource.software_list import get_software_icon_path
from ui.component import DraggableContainer, QuickLaunchDock, resolve_app_from_path

FONT_FAMILY = '"HarmonyOS Sans", "Microsoft YaHei", "SimHei", sans-serif'


class GuideLineOverlay(QWidget):
    """辅助线"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alignLines = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def setAlignLines(self, lines):
        self._alignLines = lines
        self.update()

    def showOverlay(self):
        self.show()
        self.raise_()

    def hideOverlay(self):
        self._alignLines = []
        self.hide()

    def paintEvent(self, event):
        if not self._alignLines:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        theme_color = cfg.themeColor.value
        if isinstance(theme_color, str):
            primary_color = QColor(theme_color)
        else:
            primary_color = theme_color

        pen = QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 100))
        pen.setWidthF(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        for direction, pos in self._alignLines:
            if direction == 'h':
                painter.drawLine(0, int(pos), w, int(pos))
            else:
                painter.drawLine(int(pos), 0, int(pos), h)

        painter.end()


class PageIndicator(QWidget):
    """底部条页面指示器：N 个圆点，当前页加粗+主题色，左/右键点击切页。"""

    pageClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageIndicator")
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._count = 0
        self._current = 0
        self._dot_radius = 4
        self._dot_radius_active = 6
        self._dot_gap = 10
        self._press_pos = None
        self._pressed_index = -1

        theme_color = cfg.themeColor.value
        if isinstance(theme_color, str):
            self._active_color = QColor(theme_color)
        else:
            self._active_color = theme_color
        try:
            cfg.themeColor.valueChanged.connect(self._onThemeColorChanged)
        except Exception:
            pass

    def _onThemeColorChanged(self):
        c = cfg.themeColor.value
        if isinstance(c, str):
            self._active_color = QColor(c)
        else:
            self._active_color = c
        self.update()

    def set_count(self, count: int):
        self._count = max(0, count)
        if self._current >= self._count:
            self._current = max(0, self._count - 1)
        self._updateGeometry()
        self.update()

    def set_current(self, index: int):
        if 0 <= index < self._count:
            self._current = index
            self.update()

    def _updateGeometry(self):
        w = self._count * (self._dot_radius * 2) + max(0, self._count - 1) * self._dot_gap
        h = self._dot_radius_active * 2 + 4
        self.setFixedSize(max(w + 8, 16), h)

    def sizeHint(self):
        w = self._count * (self._dot_radius * 2) + max(0, self._count - 1) * self._dot_gap
        h = self._dot_radius_active * 2 + 4
        return QSize(max(w + 8, 16), h)

    def _dotRect(self, i: int) -> QRectF:
        r = self._dot_radius
        r_active = self._dot_radius_active
        total_w = self._count * (r * 2) + max(0, self._count - 1) * self._dot_gap
        start_x = (self.width() - total_w) / 2
        x = start_x + i * (r * 2 + self._dot_gap) + r
        y = self.height() / 2
        radius = r_active if i == self._current else r
        return QRectF(x - radius, y - radius, radius * 2, radius * 2)

    def _hitTest(self, pos: QPoint) -> int:
        for i in range(self._count):
            if self._dotRect(i).contains(QPointF(pos)):
                return i
        return -1

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self._press_pos = event.position().toPoint()
            idx = self._hitTest(self._press_pos)
            self._pressed_index = idx
            if idx >= 0:
                self.pageClicked.emit(idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._press_pos = None
        self._pressed_index = -1
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = isDarkTheme()
        inactive = QColor(180, 180, 180, 200) if not is_dark else QColor(160, 160, 160, 200)
        for i in range(self._count):
            r = self._dotRect(i)
            if i == self._current:
                painter.setBrush(QBrush(self._active_color))
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                painter.setBrush(QBrush(inactive))
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(r)
        painter.end()


class HomeInterface(QWidget, TranslatableWidget):
    """主界面"""

    weather_updated = pyqtSignal(dict)
    poetry_updated = pyqtSignal(str)

    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setObjectName("home")
        self.isEditMode = False
        self._guideOverlay = None
        self._snapThreshold = 8

        # 拖拽预览
        self._drag_preview_visible = False
        self._drag_preview_component_id = None
        self._drag_preview_def = None
        self._drag_preview_x = 0
        self._drag_preview_y = 0
        self._drag_preview_width = 0
        self._drag_preview_height = 0
        self._drag_preview_collision = False
        self._drag_preview_size = (200, 80)

        # 编辑模式
        self._edit_mode_active = False
        self._edit_selected_placement_id = None
        self.current_weather_code = None

        # 翻页相关
        self._page_anim = None
        self._swipe_start_x = None
        self._swipe_start_y = None
        self._swipe_dragging = False
        self._swipe_moved = False
        self._swipe_last_dx = 0
        # 检测 pagesStack 是否卡在两页中间
        self._page_safety_timer = QTimer(self)
        self._page_safety_timer.setSingleShot(True)
        self._page_safety_timer.timeout.connect(self._checkPagePosition)
        # 周期性检查鼠标是否还按着
        self._swipe_watchdog = QTimer(self)
        self._swipe_watchdog.setSingleShot(False)
        self._swipe_watchdog.setInterval(100)
        self._swipe_watchdog.timeout.connect(self._swipeWatchdog)

        self.setAcceptDrops(True)

        self._initBackground()

        # PageManager 必须在 _initLayout 之前
        from core.component import PageManager
        self.page_manager = PageManager(DATA_CONFIG)

        self._initLayout()
        self._initPages()

        self._cached_poetry = None
        self._last_lunar_date = None
        self._cached_lunar_string = ""

        from core.component import GridLayoutService, GridSettings, ComponentRegistry, BUILTIN_COMPONENT_DEFINITIONS
        self.grid_service = GridLayoutService()
        short_side_cells = cfg.gridShortSideCells.value if hasattr(cfg, 'gridShortSideCells') else 6
        inset_percent = cfg.gridInsetPercent.value if hasattr(cfg, 'gridInsetPercent') else 5
        self.grid_settings = GridSettings(
            short_side_cells=short_side_cells,
            gap_ratio=0.12,
            inset_percent=inset_percent
        )
        self._grid_metrics = None

        self.component_registry = ComponentRegistry(self)
        self.component_registry.register_batch(BUILTIN_COMPONENT_DEFINITIONS)

        from ui.component import ComponentManager
        self.component_manager = ComponentManager(self)
        self.component_manager.load_components()
        self._draggable_widgets = self.component_manager.get_all_containers()
        # 组件加载完毕吗根据当前页显示/隐藏
        self._applyPageVisibility()

        self._initBottomBar()

        self.setStyleSheet(load_qss('home.qss'))
        cfg.themeChanged.connect(self._updateTheme)
        cfg.componentCardOpacity.valueChanged.connect(self._updateComponentCardStyle)
        cfg.componentCardRadius.valueChanged.connect(self._updateComponentCardStyle)
        cfg.backgroundBlurRadius.valueChanged.connect(self._computeBlurredBackground)
        if hasattr(cfg, 'gridShortSideCells'):
            cfg.gridShortSideCells.valueChanged.connect(self._onGridSettingsChanged)
        if hasattr(cfg, 'gridInsetPercent'):
            cfg.gridInsetPercent.valueChanged.connect(self._onGridSettingsChanged)
        self._updateComponentCardStyle()

        self.setup_translatable_ui()

        logger.info(tr("home.init_complete"))
    
    def _update_grid_metrics(self):
        """更新网格尺寸计算"""
        self._grid_metrics = self.grid_service.calculate_grid_metrics(
            self.width(), self.height(), self.grid_settings
        )

    def _onGridSettingsChanged(self):
        """网格配置变化时更新网格设置"""
        short_side_cells = cfg.gridShortSideCells.value if hasattr(cfg, 'gridShortSideCells') else 6
        inset_percent = cfg.gridInsetPercent.value if hasattr(cfg, 'gridInsetPercent') else 5
        GridSettings = type(self.grid_settings)
        self.grid_settings = GridSettings(
            short_side_cells=short_side_cells,
            gap_ratio=0.12,
            inset_percent=inset_percent
        )
        self._update_grid_metrics()
        # 更新网格
        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            self._grid_overlay.update_grid_metrics(self._grid_metrics)

    def paintEvent(self, event):
        """绘制"""
        super().paintEvent(event)

    def _initBackground(self):
        self.homeBackgroundImage = QLabel()
        self.homeBackgroundImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.homeBackgroundImage.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.originalPixmap = QPixmap(1, 1)
        self.originalPixmap.fill(Qt.GlobalColor.transparent)
        self.homeBackgroundImage.setPixmap(self.originalPixmap)
        self.homeBackgroundImage.setMinimumSize(100, 100)

        self.homeDimOverlay = QWidget()
        self.homeDimOverlay.setObjectName("dimOverlay")
        self.homeDimOverlay.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    def _initLayout(self):
        self.homeContent = QWidget(self)
        self.homeContent.setObjectName("homeContent")
        self.homeContent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.gridLayout = QGridLayout(self.homeContent)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)

        self.gridLayout.addWidget(self.homeBackgroundImage, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.homeDimOverlay, 0, 0, 1, 1)

        # 翻页容器
        from PyQt6.QtWidgets import QFrame
        self.pagesContainer = QFrame(self.homeContent)
        self.pagesContainer.setObjectName("pagesContainer")
        self.pagesContainer.setStyleSheet("background: transparent; border: none;")
        self.pagesContainer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.pagesStack = QWidget(self.pagesContainer)
        self.pagesStack.setObjectName("pagesStack")
        self.pagesStack.setStyleSheet("background: transparent;")
        self.pagesStack.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.pagesStack.show()

        homeLayout = QVBoxLayout(self)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.addWidget(self.homeContent)

        self._grid_overlay = _GridOverlay(self)
        self._grid_overlay.setObjectName("gridOverlay")
        self._grid_overlay.hide()
        self._grid_overlay.setup(self)

    def _initPages(self):
        """根据 PageManager 创建所有页面 widget"""
        # 用 dict 按 page_index 取对应 widget
        self._page_widgets = {}        # page_index -> QWidget

        from ui.component import NavigationPage
        for i, meta in enumerate(self.page_manager.pages()):
            if meta.type == "nav":
                page = NavigationPage(self.pagesStack, page_index=i, page_manager=self.page_manager)
            else:
                page = QWidget(self.pagesStack)
                page.setObjectName("infoPageWidget")
                page.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self._page_widgets[i] = page
            page.show()

        self._currentPageIndex = self.page_manager.get_current_page()
        if not (0 <= self._currentPageIndex < len(self._page_widgets)):
            self._currentPageIndex = 0
        self._layoutPages()
        self._applyPageVisibility()

    def _layoutPages(self):
        """所有页面横向排列在 pagesStack 内 第 i 页 move(i*width, 0)
        pagesStack 自身偏移到 -currentPage*width"""
        if not hasattr(self, 'pagesContainer') or not self.pagesContainer:
            return
        w = self.pagesContainer.width()
        h = self.pagesContainer.height()
        n = max(1, len(self._page_widgets))
        for i, page in self._page_widgets.items():
            page.setFixedSize(w, h)
            page.move(i * w, 0)
        # pagesStack 宽度 = 页数 * 单页宽度
        self.pagesStack.setFixedSize(n * w, h)
        self.pagesStack.move(-self._currentPageIndex * w, 0)

    def _applyPageOffset(self, offset_x: int):
        """临时偏移 pagesStack"""
        w = self.pagesContainer.width()
        self.pagesStack.move(-self._currentPageIndex * w + offset_x, 0)

    def _applyPageVisibility(self, visible_pages=None):
        """根据当前页设置组件可见性"""
        if not hasattr(self, 'component_manager') or not self.component_manager:
            return
        cur = self._currentPageIndex
        if visible_pages is None:
            visible_pages = set()
        else:
            visible_pages = set(visible_pages)
        visible_pages.add(cur)
        for comp_id, instance in self.component_manager.components.items():
            try:
                page_idx = self.component_manager.get_component_page(comp_id)
                if page_idx in visible_pages:
                    stored = self.component_manager._component_data.get(comp_id, {})
                    if stored.get("enabled", True):
                        instance.show()
                    else:
                        instance.hide()
                else:
                    instance.hide()
            except Exception as e:
                logger.warning(f"[_applyPageVisibility] {comp_id}: {e}")

    def get_info_page_widget(self, page_index: int):
        """返回指定信息页的 widget"""
        if not hasattr(self, '_page_widgets'):
            return None
        meta = self.page_manager.get_page(page_index)
        if meta is None or meta.type != "info":
            return None
        return self._page_widgets.get(page_index)

    def _stopPageAnim(self):
        """停止翻页动画：断开 finished 信号再 stop"""
        if self._page_anim:
            anim = self._page_anim
            self._page_anim = None
            try:
                anim.finished.disconnect()
            except Exception:
                pass
            anim.stop()

    def _goToPage(self, index: int, animate: bool = True):
        """切换到指定页面"""
        if not (0 <= index < len(self._page_widgets)):
            return
        if hasattr(self, '_deselectAll'):
            try:
                self._deselectAll()
            except Exception:
                pass

        self._stopPageAnim()

        old_index = self._currentPageIndex
        self._currentPageIndex = index
        self.page_manager.set_current_page(index)

        w = self.pagesContainer.width()
        target_x = -index * w

        # 翻页过渡
        if animate and old_index != index:
            self._applyPageVisibility(visible_pages={old_index, index})

        if animate:
            cur_x = self.pagesStack.x()
            if cur_x == target_x:
                self._onPageAnimFinished()
            else:
                # QPropertyAnimation 在 C++ 动画 pos 属性，
                anim = QPropertyAnimation(self.pagesStack, b"pos", self)
                anim.setStartValue(QPoint(cur_x, 0))
                anim.setEndValue(QPoint(target_x, 0))
                anim.setDuration(250)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.finished.connect(self._onPageAnimFinished)
                self._page_anim = anim
                anim.start()
        else:
            self._applyRawOffset(target_x)
            self._onPageAnimFinished()

        if hasattr(self, 'pageIndicator'):
            self.pageIndicator.set_current(index)

    def _applyRawOffset(self, x0: int):
        """设置 pagesStack 的 x"""
        self.pagesStack.move(int(x0), 0)

    def _onPageAnimFinished(self):
        self._page_anim = None
        # snap 到当前页的精确位置
        w = self.pagesContainer.width()
        if w > 0:
            self.pagesStack.move(-self._currentPageIndex * w, 0)
        self._applyPageVisibility()
        if hasattr(self, 'pageIndicator'):
            self.pageIndicator.set_current(self._currentPageIndex)
        # 网格 overlay 只在信息页显示
        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            if self._edit_mode_active and self.page_manager.get_page(self._currentPageIndex) and \
               self.page_manager.get_page(self._currentPageIndex).type == "info":
                self._grid_overlay.show()
            else:
                self._grid_overlay.hide()
        self._page_safety_timer.start(300)

    def _checkPagePosition(self):
        """如果不在拖拽/动画中 pagesStack 不在页边界：强制 snap"""
        if self._swipe_dragging or self._page_anim:
            return
        if not hasattr(self, 'pagesStack') or not self.pagesStack:
            return
        w = self.pagesContainer.width()
        if w <= 0:
            return
        expected_x = -self._currentPageIndex * w
        if self.pagesStack.x() != expected_x:
            self.pagesStack.move(expected_x, 0)

    def _initBottomBar(self):
        """底部栏"""
        self.bottomBar = QWidget(self.homeContent)
        self.bottomBar.setObjectName("bottomBar")
        self.bottomBar.setFixedSize(1400, 60)
        self.bottomBar.show()

        barLayout = QHBoxLayout(self.bottomBar)
        barLayout.setContentsMargins(16, 0, 16, 0)
        barLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.backToDesktopBtn = PushButton(tr("home.back_to_desktop"), self.bottomBar)
        self.backToDesktopBtn.setObjectName("backToDesktopBtn")
        self.backToDesktopBtn.clicked.connect(self.mainWindow.showMinimized)
        barLayout.addWidget(self.backToDesktopBtn)

        barLayout.addStretch()

        # 中间：页面指示器
        self.pageIndicator = PageIndicator(self.bottomBar)
        self.pageIndicator.set_count(self.page_manager.page_count())
        self.pageIndicator.set_current(self._currentPageIndex)
        self.pageIndicator.pageClicked.connect(lambda i: self._goToPage(i, animate=True))
        barLayout.addWidget(self.pageIndicator)

        barLayout.addStretch()

        # 编辑模式显示：
        # 添加页面按钮
        self.addPageBtn = PushButton(self.bottomBar)
        self.addPageBtn.setObjectName("addPageBtn")
        self.addPageBtn.setIcon(FUI.ADD)
        self._refreshAddPageBtn()
        self.addPageBtn.clicked.connect(self._addNewPage)
        self.addPageBtn.hide()
        barLayout.addWidget(self.addPageBtn)

        # 重命名页面按钮
        self.renamePageBtn = PushButton(self.bottomBar)
        self.renamePageBtn.setObjectName("renamePageBtn")
        self.renamePageBtn.setIcon(FUI.EDIT)
        self.renamePageBtn.setText(tr("home.rename_page"))
        self.renamePageBtn.clicked.connect(lambda: self._renamePage(self._currentPageIndex))
        self.renamePageBtn.hide()
        barLayout.addWidget(self.renamePageBtn)

        # 删除页面按钮
        self.delPageBtn = PushButton(self.bottomBar)
        self.delPageBtn.setObjectName("delPageBtn")
        self.delPageBtn.setIcon(FUI.DELETE)
        self.delPageBtn.setText(tr("home.delete_page"))
        self.delPageBtn.clicked.connect(lambda: self._deletePage(self._currentPageIndex))
        self.delPageBtn.hide()
        barLayout.addWidget(self.delPageBtn)

        self.menuBtn = ToolButton(FUI.MENU, self.bottomBar)
        self.menuBtn.setObjectName("bottomMenuBtn")
        self.menuBtn.setFixedSize(36, 36)
        self.menuBtn.setIconSize(QSize(28, 28))
        self.menuBtn.clicked.connect(self._showBottomMenu)
        barLayout.addWidget(self.menuBtn)

        self._updateBottomBarPosition()

    def _refreshAddPageBtn(self):
        """刷新添加页面按钮文案"""
        if not hasattr(self, 'addPageBtn') or not self.addPageBtn:
            return
        total = self.page_manager.page_count()
        self.addPageBtn.setText(tr("home.add_page_with_count", count=total))

    def _addNewPage(self):
        """添加新信息页"""
        new_index = self.page_manager.add_page(page_type="info")
        if new_index < 0:
            from qfluentwidgets import InfoBar
            InfoBar.warning(title=tr("home.page_limit"),
                            content="", parent=self, duration=2000)
            return
        # 新建对应页 widget
        page = QWidget(self.pagesStack)
        page.setObjectName("infoPageWidget")
        page.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._page_widgets[new_index] = page
        page.show()
        self._layoutPages()
        self.pageIndicator.set_count(self.page_manager.page_count())
        self._refreshAddPageBtn()
        self._goToPage(new_index, animate=True)

    def _renamePage(self, index: int):
        from qfluentwidgets import MessageBoxBase, LineEdit, SubtitleLabel
        meta = self.page_manager.get_page(index)
        if meta is None:
            return
        box = MessageBoxBase(self.window())
        title = SubtitleLabel(tr("home.rename_page_title"), box)
        box.viewLayout.addWidget(title)
        edit = LineEdit(box)
        edit.setText(meta.name)
        edit.setClearButtonEnabled(True)
        box.viewLayout.addWidget(edit)
        if box.exec():
            new_name = edit.text().strip()
            if new_name:
                self.page_manager.rename_page(index, new_name)

    def _deletePage(self, index: int):
        """删除页面"""
        from qfluentwidgets import MessageBox
        meta = self.page_manager.get_page(index)
        if meta is None or meta.type == "nav":
            return
        if self.page_manager.page_count() <= 1:
            return

        # 找一个信息页作为 fallback
        fallback = -1
        for i, m in enumerate(self.page_manager.pages()):
            if i != index and m.type == "info":
                fallback = i
                break

        # 确认
        if fallback >= 0:
            content = tr("home.delete_page_confirm", name=meta.name)
        else:
            content = tr("home.delete_page_no_fallback", name=meta.name)
        msg_box = MessageBox(
            tr("home.delete_page"),
            content,
            self.window(),
        )
        if not msg_box.exec():
            return

        # 迁移或删除被删页的组件
        to_remove = []
        for comp_id, instance in self.component_manager.components.items():
            pi = self.component_manager.get_component_page(comp_id)
            if pi == index:
                if fallback >= 0:
                    self.component_manager.set_component_page(comp_id, fallback)
                    new_parent = self._page_widgets.get(fallback)
                    if new_parent is not None:
                        instance.setParent(new_parent)
                else:
                    to_remove.append(comp_id)
        for cid in to_remove:
            self.component_manager.remove_component(cid)

        # 调整其他组件的 page_index
        self.component_manager.shift_pages_after_delete(index, fallback_index=fallback if fallback >= 0 else 0)

        self.page_manager.delete_page(index)

        old_widget = self._page_widgets.pop(index, None)
        if old_widget:
            old_widget.setParent(None)
            old_widget.deleteLater()

        # 重建 _page_widgets 的 key
        new_map = {}
        for i in sorted(self._page_widgets.keys()):
            new_map[len(new_map)] = self._page_widgets[i]
        self._page_widgets = new_map

        for i, page in self._page_widgets.items():
            if hasattr(page, '_page_index'):
                page._page_index = i

        self.pageIndicator.set_count(self.page_manager.page_count())
        self._refreshAddPageBtn()

        # 跳到合适页
        new_cur = self.page_manager.get_current_page()
        self._currentPageIndex = new_cur
        self._layoutPages()
        self._applyPageVisibility()
        if hasattr(self, 'pageIndicator'):
            self.pageIndicator.set_current(new_cur)

    def _updateBottomBarPosition(self):
        """距底部25px"""
        if not hasattr(self, 'bottomBar') or not self.bottomBar:
            return
        parent = self.homeContent
        x = (parent.width() - self.bottomBar.width()) // 2
        y = parent.height() - self.bottomBar.height() - 25
        self.bottomBar.move(x, y)

    def _openSettingsWindow(self):
        """打开设置窗口"""
        from ui.settings import SettingsWindow
        if not hasattr(self, '_settings_window') or self._settings_window is None:
            self._settings_window = SettingsWindow(self.mainWindow)
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _openComponentEditWindow(self):
        """打开组件库窗口"""
        from ui.component import ComponentLibraryWindow
        if not hasattr(self, '_component_library_window') or self._component_library_window is None:
            self._component_library_window = ComponentLibraryWindow(self.component_registry)
            self._component_library_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            self._component_library_window.installEventFilter(self)
            self._component_library_window.destroyed.connect(self._on_component_library_destroyed)

        # 进入编辑模式
        self._enterEditMode()

        self._component_library_window.show()
        self._component_library_window.raise_()
        self._component_library_window.activateWindow()

    def _on_component_library_destroyed(self):
        """组件库窗口销毁时清理引用"""
        self._component_library_window = None
        self._exitEditMode()

    def eventFilter(self, obj, event):
        """监听组件库窗口事件"""
        if obj == self._component_library_window and event.type() == QEvent.Type.Close:
            self._exitEditMode()
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event):
        """拖拽进入"""
        if event.mimeData().hasFormat("application/x-Glimpseon-component"):
            # 当前页为导航页时不接受组件拖入
            meta = self.page_manager.get_page(self._currentPageIndex) if hasattr(self, 'page_manager') else None
            if meta is not None and meta.type == "nav":
                event.ignore()
                return
            event.acceptProposedAction()
            self._drag_hover = True
            self._drag_preview_visible = True

            data = event.mimeData().data("application/x-Glimpseon-component").data().decode('utf-8')
            self._drag_preview_component_id = data

            if "|" in data:
                comp_type, comp_style = data.split("|", 1)
                self._drag_preview_def = self.component_registry.get_definition(f"{comp_type}_{comp_style}")
            else:
                self._drag_preview_def = self.component_registry.get_definition(data)

            logger.info(f"dragEnter: component={data}, def={self._drag_preview_def}")

            from ui.component import COMPONENT_STYLES
            comp_type, comp_style = self._resolve_component_type_style(data)
            style_info = COMPONENT_STYLES.get(comp_type, {}).get(comp_style, {})
            comp_class = style_info.get("class")
            if comp_class:
                try:
                    import uuid
                    temp_data = {
                        "id": f"temp_preview_{uuid.uuid4().hex[:8]}",
                        "type": comp_type,
                        "style": comp_style,
                        "config": style_info.get("default_config", {}),
                    }
                    temp_widget = comp_class(self, temp_data)
                    temp_widget.hide()
                    w, h = style_info.get("default_size", (200, 80))
                    self._drag_preview_size = (w, h)
                    temp_widget.setParent(None)
                    temp_widget.deleteLater()
                    logger.info(f"预览框实际尺寸: {w}x{h} ({comp_type}/{comp_style})")
                except Exception as e:
                    logger.warning(f"默认尺寸: {e}")
                    self._drag_preview_size = style_info.get("default_size", (200, 80))
            else:
                self._drag_preview_size = style_info.get("default_size", (200, 80))

            self._update_grid_metrics()
            logger.info(f"grid_metrics cell_size={self._grid_metrics.cell_size if self._grid_metrics else 'None'}")

            if hasattr(self, '_drag_preview_size') and self._drag_preview_size:
                self._drag_preview_width = self._drag_preview_size[0]
                self._drag_preview_height = self._drag_preview_size[1]

            if hasattr(self, '_grid_overlay') and self._grid_overlay:
                self._grid_overlay.update_grid_metrics(self._grid_metrics)
                self._grid_overlay.show_preview(False)
                self._grid_overlay.show()

            self.update()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动"""
        if event.mimeData().hasFormat("application/x-Glimpseon-component"):
            event.acceptProposedAction()

            pos = event.position()
            default_size = getattr(self, '_drag_preview_size', (200, 80))
            comp_width, comp_height = default_size

            raw_x = pos.x() - comp_width / 2
            raw_y = pos.y() - comp_height / 2

            if self._grid_metrics and self._drag_preview_def:
                SNAP_THRESHOLD = 20
                snapped_x, snapped_y = self._snap_to_grid(
                    raw_x, raw_y, comp_width, comp_height, SNAP_THRESHOLD
                )
            else:
                snapped_x, snapped_y = raw_x, raw_y

            snapped_x = max(0, min(snapped_x, self.width() - comp_width))
            snapped_y = max(0, min(snapped_y, self.height() - comp_height))

            self._drag_preview_x = snapped_x
            self._drag_preview_y = snapped_y
            self._drag_preview_width = comp_width
            self._drag_preview_height = comp_height

            self._drag_preview_collision = self._check_pixel_collision(
                snapped_x, snapped_y, comp_width, comp_height
            )

            if hasattr(self, '_grid_overlay') and self._grid_overlay:
                self._grid_overlay.update_preview_pixel(
                    snapped_x, snapped_y, comp_width, comp_height,
                    self._drag_preview_collision
                )
                self._grid_overlay.show()
        else:
            event.ignore()

    def _snap_to_grid(self, x: float, y: float, width: float, height: float, threshold: float) -> tuple:
        """自由吸附"""
        metrics = self._grid_metrics
        inset = metrics.edge_inset_px
        pitch = metrics.pitch

        left = x
        right = x + width
        top = y
        bottom = y + height

        def find_nearest_grid_line(pos, is_vertical: bool):
            if is_vertical:
                for col in range(metrics.column_count + 1):
                    line_x = inset + col * pitch
                    if abs(pos - line_x) <= threshold:
                        return line_x
            else:
                for row in range(metrics.row_count + 1):
                    line_y = inset + row * pitch
                    if abs(pos - line_y) <= threshold:
                        return line_y
            return pos

        snapped_left = find_nearest_grid_line(left, True)
        snapped_right = find_nearest_grid_line(right, True)
        snapped_top = find_nearest_grid_line(top, False)
        snapped_bottom = find_nearest_grid_line(bottom, False)

        final_x = snapped_left if snapped_left != left else (snapped_right - width if snapped_right != right else x)
        final_y = snapped_top if snapped_top != top else (snapped_bottom - height if snapped_bottom != bottom else y)

        return (final_x, final_y)

    def _check_pixel_collision(self, x: float, y: float, width: float, height: float) -> bool:
        """像素位置碰撞检测"""
        if hasattr(self, 'component_manager') and self.component_manager:
            containers = self.component_manager.get_all_containers()
            for container in containers:
                if container and container.isVisible():
                    cx = container.x()
                    cy = container.y()
                    cw = container.width()
                    ch = container.height()
                    if not (x + width < cx or x > cx + cw or
                            y + height < cy or y > cy + ch):
                        return True
        return False

    def dragLeaveEvent(self, event):
        """拖拽离开"""
        self._drag_preview_visible = False
        self._drag_preview_component_id = None
        self._drag_preview_def = None
        self._drag_preview_x = 0
        self._drag_preview_y = 0
        self._drag_preview_width = 0
        self._drag_preview_height = 0
        self._drag_preview_collision = False

        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            if not self._edit_mode_active:
                self._grid_overlay.hide()
            else:
                self._grid_overlay.show_preview(False)

        self.update()
        event.accept()

    def dropEvent(self, event):
        """放置"""
        if not event.mimeData().hasFormat("application/x-Glimpseon-component"):
            event.ignore()
            return

        saved_x = self._drag_preview_x
        saved_y = self._drag_preview_y
        saved_w = self._drag_preview_width
        saved_h = self._drag_preview_height
        has_valid_preview = saved_w > 0 and saved_h > 0

        self._drag_preview_visible = False
        self._drag_preview_component_id = None
        self._drag_preview_def = None
        self._drag_preview_x = 0
        self._drag_preview_y = 0
        self._drag_preview_width = 0
        self._drag_preview_height = 0
        self._drag_preview_collision = False

        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            if self._edit_mode_active:
                self._grid_overlay.show_preview(False)
            else:
                self._grid_overlay.hide()

        data = event.mimeData().data("application/x-Glimpseon-component").data().decode('utf-8')

        component_type, component_style = self._resolve_component_type_style(data)

        drop_pos = event.position()
        if has_valid_preview:
            available_width = self.width() - saved_w
            available_height = self.height() - saved_h
            if available_width > 0 and available_height > 0:
                pos_x_pct = saved_x / available_width
                pos_y_pct = saved_y / available_height
            else:
                pos_x_pct = drop_pos.x() / self.width() if self.width() > 0 else 0.5
                pos_y_pct = drop_pos.y() / self.height() if self.height() > 0 else 0.5
        else:
            pos_x_pct = drop_pos.x() / self.width() if self.width() > 0 else 0.5
            pos_y_pct = drop_pos.y() / self.height() if self.height() > 0 else 0.5

        logger.info(f"dropEvent: saved=({saved_x},{saved_y},{saved_w},{saved_h}), "
                    f"has_valid_preview={has_valid_preview}, pct=({pos_x_pct:.3f},{pos_y_pct:.3f})")

        if hasattr(self, 'component_manager') and self.component_manager:
            comp_id = self.component_manager.add_component(component_type, component_style,
                                                            page_index=self._currentPageIndex)
            if comp_id:
                comp = self.component_manager.components.get(comp_id)
                if comp:
                    # 组件实际尺寸重新计算
                    comp_width = comp.width()
                    comp_height = comp.height()
                    if has_valid_preview:
                        available_width = self.width() - comp_width
                        available_height = self.height() - comp_height
                        if available_width > 0 and available_height > 0:
                            pos_x_pct = saved_x / available_width
                            pos_y_pct = saved_y / available_height
                    else:
                        # 没有就鼠标位置减半宽高居中
                        if comp_width > 0 and comp_height > 0:
                            center_x = drop_pos.x() - comp_width / 2
                            center_y = drop_pos.y() - comp_height / 2
                            available_width = self.width() - comp_width
                            available_height = self.height() - comp_height
                            if available_width > 0 and available_height > 0:
                                pos_x_pct = center_x / available_width
                                pos_y_pct = center_y / available_height

                    pos_x_pct = max(0.0, min(1.0, pos_x_pct))
                    pos_y_pct = max(0.0, min(1.0, pos_y_pct))
                    comp.setPositionPercent(pos_x_pct, pos_y_pct)
                    self.component_manager.save_components()
                    if comp not in self._draggable_widgets:
                        self._draggable_widgets.append(comp)
                    if self._edit_mode_active and hasattr(comp, 'setDraggable'):
                        comp.setDraggable(True)
                        try:
                            comp.selected.connect(self._selectComponent)
                        except Exception:
                            pass

                event.acceptProposedAction()
                self.update()

                from qfluentwidgets import InfoBarPosition
                InfoBar.success(
                    tr("component_edit.add_success"),
                    "",
                    orient=Qt.Orientation.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return

        logger.warning(f"dropEvent: 组件创建失败 type={component_type} style={component_style}")
        event.ignore()
        self.update()

    def _resolve_component_type_style(self, component_id: str) -> tuple:
        """从 definition ID 或 type|style 格式读 component_manager 要的 type style"""
        try:
            from ui.component import COMPONENT_STYLES
            if '|' in component_id:
                comp_type, comp_style = component_id.split('|', 1)
                if comp_type in COMPONENT_STYLES:
                    if comp_style in COMPONENT_STYLES[comp_type]:
                        return (comp_type, comp_style)
                    first_style = next(iter(COMPONENT_STYLES[comp_type]))
                    return (comp_type, first_style)
            parts = component_id.split('_')
            for i in range(len(parts), 0, -1):
                potential_type = '_'.join(parts[:i])
                potential_style = '_'.join(parts[i:])
                if potential_type in COMPONENT_STYLES and potential_style in COMPONENT_STYLES[potential_type]:
                    return (potential_type, potential_style)
        except Exception:
            pass
        parts = component_id.replace('|', '_').split('_')
        return (parts[0], '_'.join(parts[1:]))

    def _showBottomMenu(self):
        """底部菜单按钮的弹出菜单"""
        menu = RoundMenu(parent=self.menuBtn)

        settings_action = Action(FUI.SETTING, tr("home.menu_settings"))
        settings_action.triggered.connect(self._openSettingsWindow)
        menu.addAction(settings_action)

        edit_action = Action(FUI.EDIT, tr("home.menu_component_edit"))
        edit_action.triggered.connect(self._openComponentEditWindow)
        menu.addAction(edit_action)

        menu.addSeparator()

        restart_action = Action(FUI.UPDATE, tr("home.menu_restart"))
        restart_action.triggered.connect(lambda: os.system('shutdown /r /t 0'))
        menu.addAction(restart_action)

        shutdown_action = Action(FUI.CLOSE, tr("home.menu_shutdown"))
        shutdown_action.triggered.connect(lambda: os.system('shutdown /s /t 0'))
        menu.addAction(shutdown_action)

        menu.exec(self.menuBtn.mapToGlobal(
            self.menuBtn.rect().bottomRight()
        ))

    def _enterEditMode(self):
        """进入编辑模式"""
        self.isEditMode = True
        self._edit_mode_active = True
        # 更新网格度量
        self._update_grid_metrics()
        logger.info(f"进入编辑模式: grid_metrics={self._grid_metrics}, "
                    f"cell_size={self._grid_metrics.cell_size if self._grid_metrics else 'None'}")
        # 显示网格（信息页）
        meta = self.page_manager.get_page(self._currentPageIndex) if hasattr(self, 'page_manager') else None
        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            self._grid_overlay.update_grid_metrics(self._grid_metrics)
            self._grid_overlay.show_preview(False)
            if meta is None or meta.type == "info":
                self._grid_overlay.show()
                self._grid_overlay.raise_()
            else:
                self._grid_overlay.hide()
        if hasattr(self, 'addPageBtn') and self.addPageBtn:
            self.addPageBtn.show()
        if hasattr(self, 'renamePageBtn') and self.renamePageBtn:
            self.renamePageBtn.show()
        if hasattr(self, 'delPageBtn') and self.delPageBtn:
            self.delPageBtn.show()
        # 设置可拖动
        self._set_all_draggable(True)

    def _selectComponent(self, component_id: str):
        """选中组件"""
        self._deselectAll()
        self._edit_selected_placement_id = component_id
        container = self.component_manager.components.get(component_id)
        if container:
            container.setSelected(True)
            container.showEditControls(True)

    def _deselectAll(self):
        """取消所有组件选中"""
        if self._edit_selected_placement_id:
            old = self.component_manager.components.get(self._edit_selected_placement_id)
            if old:
                old.setSelected(False)
                old.showEditControls(False)
        self._edit_selected_placement_id = None

    def deleteSelectedComponent(self, component_id: str):
        """删除指定组件"""
        self._deselectAll()
        self.component_manager.remove_component(component_id)
        self._draggable_widgets = [
            w for w in self._draggable_widgets
            if not (hasattr(w, 'component_id') and w.component_id == component_id)
        ]

    def mousePressEvent(self, event):
        """点击空白取消选中 + 翻页拖拽起点"""
        if self.isEditMode and event.button() == Qt.MouseButton.LeftButton:
            self._deselectAll()
        # 翻页拖拽：记录起点
        if event.button() == Qt.MouseButton.LeftButton:
            meta = self.page_manager.get_page(self._currentPageIndex) if hasattr(self, 'page_manager') else None
            if not self._edit_mode_active or (meta and meta.type == "nav"):
                self._stopPageAnim()
                w = self.pagesContainer.width()
                if w > 0:
                    self.pagesStack.move(-self._currentPageIndex * w, 0)
                self._swipe_start_x = event.position().x()
                self._swipe_start_y = event.position().y()
                self._swipe_dragging = True
                self._swipe_moved = False
                self._swipe_last_dx = 0
                self.grabMouse()
                self._swipe_watchdog.start()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """翻页跟手"""
        if self._swipe_dragging and self._swipe_start_x is not None:
            dx = event.position().x() - self._swipe_start_x
            dy = event.position().y() - self._swipe_start_y
            if abs(dx) > 10 and abs(dx) > abs(dy):
                if not self._swipe_moved:
                    self._swipe_moved = True
                    # 首次移动时显示相邻页组件
                    pages = {self._currentPageIndex}
                    if self._currentPageIndex > 0:
                        pages.add(self._currentPageIndex - 1)
                    if self._currentPageIndex < len(self._page_widgets) - 1:
                        pages.add(self._currentPageIndex + 1)
                    self._applyPageVisibility(visible_pages=pages)
                # 边缘阻尼
                w = self.pagesContainer.width()
                raw_dx = dx
                if (self._currentPageIndex == 0 and raw_dx > 0) or \
                   (self._currentPageIndex == len(self._page_widgets) - 1 and raw_dx < 0):
                    raw_dx = int(raw_dx * 0.3)
                self._swipe_last_dx = int(raw_dx)
                self.pagesStack.move(-self._currentPageIndex * w + self._swipe_last_dx, 0)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """翻页释放"""
        if self._swipe_dragging and self._swipe_start_x is not None:
            self._swipe_watchdog.stop()
            try:
                self.releaseMouse()
            except Exception:
                pass
            dx = event.position().x() - self._swipe_start_x
            w = self.pagesContainer.width()
            threshold = max(60, w * 0.15)
            target = self._currentPageIndex
            if self._swipe_moved:
                if dx > threshold and self._currentPageIndex > 0:
                    target = self._currentPageIndex - 1
                elif dx < -threshold and self._currentPageIndex < len(self._page_widgets) - 1:
                    target = self._currentPageIndex + 1
            self._swipe_dragging = False
            self._swipe_start_x = None
            self._swipe_moved = False
            self._goToPage(target, animate=True)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _swipeWatchdog(self):
        """如果鼠标已释放但 releaseEvent 漏掉 手动处理"""
        if not self._swipe_dragging:
            self._swipe_watchdog.stop()
            return
        # 检查鼠标左键还按着
        from PyQt6.QtWidgets import QApplication
        if not (QApplication.mouseButtons() & Qt.MouseButton.LeftButton):
            self._swipe_watchdog.stop()
            try:
                self.releaseMouse()
            except Exception:
                pass
            w = self.pagesContainer.width()
            threshold = max(60, w * 0.15)
            target = self._currentPageIndex
            if self._swipe_moved:
                if self._swipe_last_dx > threshold and self._currentPageIndex > 0:
                    target = self._currentPageIndex - 1
                elif self._swipe_last_dx < -threshold and self._currentPageIndex < len(self._page_widgets) - 1:
                    target = self._currentPageIndex + 1
            self._swipe_dragging = False
            self._swipe_start_x = None
            self._swipe_moved = False
            self._goToPage(target, animate=True)

    def wheelEvent(self, event):
        """水平滚轮翻页"""
        if not self._edit_mode_active:
            delta = event.angleDelta()
            dx = delta.x()
            dy = delta.y()
            if abs(dx) < 1 and abs(dy) != 0:
                dx = -dy
            if abs(dx) > 30:
                if dx > 0:
                    self._goToPage(self._currentPageIndex - 1, animate=True)
                else:
                    self._goToPage(self._currentPageIndex + 1, animate=True)
                event.accept()
                return
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Delete 键删除选中组件 方向键翻页"""
        if self.isEditMode and self._edit_selected_placement_id:
            if event.key() == Qt.Key.Key_Delete:
                self.deleteSelectedComponent(self._edit_selected_placement_id)
                return
        # 左右方向键翻页
        if event.key() == Qt.Key.Key_Left:
            self._goToPage(self._currentPageIndex - 1, animate=True)
            return
        if event.key() == Qt.Key.Key_Right:
            self._goToPage(self._currentPageIndex + 1, animate=True)
            return
        super().keyPressEvent(event)

    def _exitEditMode(self):
        """退出编辑模式"""
        self.isEditMode = False
        self._edit_mode_active = False
        self._deselectAll()
        # 隐藏网格
        if hasattr(self, '_grid_overlay') and self._grid_overlay:
            self._grid_overlay.hide()
        # 隐藏辅助线
        self._hideGuideLines()
        if hasattr(self, 'addPageBtn') and self.addPageBtn:
            self.addPageBtn.hide()
        if hasattr(self, 'renamePageBtn') and self.renamePageBtn:
            self.renamePageBtn.hide()
        if hasattr(self, 'delPageBtn') and self.delPageBtn:
            self.delPageBtn.hide()
        # 设置不可拖动
        self._set_all_draggable(False)

    def _set_all_draggable(self, enabled: bool):
        """设置可拖动"""
        if not hasattr(self, '_draggable_widgets'):
            self._draggable_widgets = []

        if hasattr(self, 'component_manager') and self.component_manager:
            containers = self.component_manager.get_all_containers()
            logger.info(f"component_manager 有 {len(containers)} 个容器")
            for container in containers:
                if container not in self._draggable_widgets:
                    self._draggable_widgets.append(container)
                    logger.info(f"添加新容器到拖拽列表: {container}")

        try:
            from ui.component import DraggableContainer as DCont
            for child in self.findChildren(DCont):
                if child not in self._draggable_widgets:
                    self._draggable_widgets.append(child)
                    logger.info(f"findChildren 补充: {child}")
        except Exception:
            pass

        logger.info(f"拖拽列表共有 {len(self._draggable_widgets)} 个组件，设置draggable={enabled}")

        for widget in self._draggable_widgets:
            if widget and hasattr(widget, 'setDraggable'):
                try:
                    widget.setDraggable(enabled)
                    widget.raise_()
                    try:
                        widget.selected.disconnect(self._selectComponent)
                    except Exception:
                        pass
                    if enabled:
                        widget.selected.connect(self._selectComponent)
                except Exception as e:
                    logger.warning(f"设置组件可拖动状态失败: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available_width = self.width()
        available_height = self.height()

        # 更新网格计算
        self._update_grid_metrics()

        # 翻页容器跟随尺寸
        if hasattr(self, 'pagesContainer') and self.pagesContainer and hasattr(self, 'homeContent') and self.homeContent:
            self.pagesContainer.setGeometry(0, 0, self.homeContent.width(), self.homeContent.height())
            if hasattr(self, '_page_widgets'):
                self._stopPageAnim()
                self._layoutPages()

        if hasattr(self, 'homeBackgroundImage') and self.homeBackgroundImage:
            try:
                blurred = getattr(self, '_blurredOriginalPixmap', None)
                if blurred and not blurred.isNull():
                    self.homeBackgroundImage.setPixmap(
                        blurred.scaled(available_width, available_height,
                                       Qt.AspectRatioMode.IgnoreAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                    )
                elif hasattr(self, 'originalPixmap') and self.originalPixmap is not None and not self.originalPixmap.isNull():
                    self.homeBackgroundImage.setPixmap(
                        self.originalPixmap.scaled(available_width, available_height,
                                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
                    )
            except Exception as e:
                logger.error(f"resizeEvent 错误：{e}")

        if hasattr(self, '_draggable_widgets'):
            for widget in self._draggable_widgets:
                if widget and hasattr(widget, 'onParentResize'):
                    widget.onParentResize()

        self._updateBottomBarPosition()

        if hasattr(self, '_guideOverlay') and self._guideOverlay and self._guideOverlay.isVisible():
            self._updateGuideLinesPosition()

    def _computeBlurredBackground(self):
        if not hasattr(self, 'originalPixmap') or self.originalPixmap is None or self.originalPixmap.isNull():
            return
        blur_radius = cfg.backgroundBlurRadius.value
        if blur_radius <= 0:
            self._blurredOriginalPixmap = None
            self.resizeEvent(None)
            return

        src = self.originalPixmap
        try:
            from Glimpseon_native import blur_image
            qimg = src.toImage().convertToFormat(QImage.Format.Format_ARGB32)
            t0 = time.perf_counter()
            blurred_bytes = blur_image(qimg.bits().asstring(qimg.sizeInBytes()), qimg.width(), qimg.height(), float(blur_radius))
            elapsed = (time.perf_counter() - t0) * 1000
            blurred_qimage = QImage(blurred_bytes, qimg.width(), qimg.height(), QImage.Format.Format_ARGB32)
            self._blurredOriginalPixmap = QPixmap.fromImage(blurred_qimage)
            logger.info(f"[HOME-BLUR] 模糊完成: {qimg.width()}x{qimg.height()}, radius={blur_radius}, {elapsed:.1f}ms")
        except Exception as e:
            logger.error(f"[HOME-BLUR] 模糊失败: {e}")
            self._blurredOriginalPixmap = None
        self.resizeEvent(None)
    def _updateTheme(self):
        base_qss = load_qss('home.qss')
        card_qss = self._buildComponentCardQss()
        self.setStyleSheet(base_qss + "\n" + card_qss)

    def _buildComponentCardQss(self):
        opacity = cfg.componentCardOpacity.value / 100.0
        radius = cfg.componentCardRadius.value
        dark = isDarkTheme()
        if dark:
            bg_color = f"rgba(18, 18, 22, {opacity:.2f})"
            border_color = "rgba(255, 255, 255, 0.06)"
        else:
            bg_color = f"rgba(255, 255, 255, {opacity:.2f})"
            border_color = "rgba(0, 0, 0, 0.06)"
        return f"""
#clockContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#weatherContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#weatherHourlyContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#weatherWeeklyContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#schoolInfoContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#poetryContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#countdownContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#classAlbumContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#mediaWidget {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#bottomBar {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#timetableContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#newsBaiduContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#newsWeiboContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#newsJinritoutiaoContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#newsTenxunwangContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#newsCCTVContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#writingPadContainer {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
}}
#navItemCell {{
    background-color: {bg_color};
    border-radius: {radius}px;
    border: 1px solid {border_color};
    font-family: "HarmonyOS Sans", "Microsoft YaHei", "SimHei", sans-serif;
}}
#navItemCell:hover {{
    background-color: {"rgba(255, 255, 255, 0.12)" if dark else "rgba(0, 0, 0, 0.10)"};
}}
"""

    def _updateComponentCardStyle(self):
        self._updateTheme()

    def _updateQuickLaunch(self):
        if not hasattr(self, 'quickLaunchContainer'):
            return
        if not cfg.showQuickLaunch.value:
            if self.isEditMode:
                self.quickLaunchContainer.setContentVisible(False)
                self.quickLaunchContainer.show()
            else:
                self.quickLaunchContainer.hide()
            return
        self.quickLaunchContainer.setContentVisible(True)
        self.quickLaunchContainer.show()
        apps = cfg.quickLaunchApps.value or []
        self.quickLaunchDock.update_icon_size(cfg.quickLaunchIconSize.value)
        self.quickLaunchDock.set_apps(apps)
        self.quickLaunchContainer.updateSize()

    def _hideGuideLines(self):
        if self._guideOverlay:
            self._guideOverlay.hideOverlay()

    def _updateGuideLinesPosition(self):
        if not self._guideOverlay or not self._guideOverlay.isVisible():
            return
        if not hasattr(self, 'homeContent') or not self.homeContent:
            return
        self._guideOverlay.setGeometry(self.homeContent.rect())
    def clearDragAlignLines(self):
        if self._guideOverlay:
            self._guideOverlay.setAlignLines([])

    # 组件拖拽位置变更回调
    def saveComponentPositions(self):
        if not hasattr(self, '_draggable_widgets'):
            return

        if hasattr(self, 'page_manager'):
            try:
                self.page_manager.set_current_page(self._currentPageIndex)
            except Exception as e:
                logger.error(f"保存当前页失败: {e}")

        if hasattr(self, 'component_manager') and self.component_manager:
            try:
                self.component_manager.save_components()
            except Exception as e:
                logger.error(f"保存组件位置失败: {e}")


class EditPanel(QWidget):
    """编辑面板"""

    def __init__(self, mainWindow, width=300):
        """初始化编辑面板"""
        super().__init__(parent=mainWindow)
        self.mainWindow = mainWindow
        self._width = width
        self.setFixedWidth(self._width)
        self.setObjectName('EditPanel')
        self.isLeftSide = False
        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self._updateCountdownList)
        self.updateTimer.start(1000)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self._updateTheme()

        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        v = QVBoxLayout(content)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)
        titleLayout = QHBoxLayout()
        titleLabel = StrongBodyLabel(tr("home.edit_panel"), self)  # 编辑面板
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()

        self.positionButton = ToolButton(parent=self)
        self.positionButton.setFixedSize(32, 32)
        self.positionButton.setToolTip(tr("home.switch_to_left"))  # 切换到左侧
        self.positionButton.setIcon(FUI.CARE_LEFT_SOLID)
        self.positionButton.clicked.connect(self._togglePosition)
        titleLayout.addWidget(self.positionButton)
        v.addLayout(titleLayout)

        self._addSeparator(v)
        self._createTimeSettings(v)
        self._updateTimeSettingsEnabled(cfg.showClock.value)
        self._addSeparator(v)
        self._createPoetrySettings(v)
        self._updatePoetrySettingsEnabled(cfg.showPoetry.value)
        self._addSeparator(v)
        self._createWeatherSettings(v)
        self._updateWeatherSettingsEnabled(cfg.showWeather.value)
        self._addSeparator(v)
        self._createCountdownListCard(v)
        self._addSeparator(v)
        self._createCountdownSettings(v)
        self._updateCountdownSettingsEnabled(cfg.showCountdown.value)
        self._addSeparator(v)
        self._createSchoolInfoSettings(v)
        self._updateSchoolInfoSettingsEnabled(cfg.showSchoolInfo.value)
        self._addSeparator(v)
        self._createQuickLaunchSettings(v)
        self._updateQuickLaunchSettingsEnabled(cfg.showQuickLaunch.value)
        self._addSeparator(v)
        self._createMediaSettings(v)
        self._updateMediaSettingsEnabled(cfg.showMediaInfo.value)
        self._connectConfigSignals()
        self.__connectSignalToSlot()

        v.addStretch()

        self.closeButton = PushButton(tr("common.close"), self, icon=FUI.CLOSE)  # 关闭
        self.closeButton.setFixedHeight(36)
        v.addWidget(self.closeButton)
        self.closeButton.clicked.connect(self.hidePanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # 动画
        self.anim = QPropertyAnimation(self, QByteArray(b'geometry'))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._updateTheme()

        self.hide()

    def _addSeparator(self, layout):
        """添加分隔线"""
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setObjectName('separator')
        layout.addWidget(separator)

    def _updateTimeSettingsEnabled(self, enabled):
        self.showSecondsSwitch.setEnabled(enabled)
        self.showLunarSwitch.setEnabled(enabled)
        self.clockColorCombo.setEnabled(enabled)
        self.clockSizeSpin.setEnabled(enabled)
        self.dateSizeSpin.setEnabled(enabled)

    def _updatePoetrySettingsEnabled(self, enabled):
        self.poetryApiCombo.setEnabled(enabled)
        self.poetrySizeSpin.setEnabled(enabled)
        self.poetryUpdateIntervalCombo.setEnabled(enabled)

    def _updateWeatherSettingsEnabled(self, enabled):
        self.cityButton.setEnabled(enabled)
        self.weatherSizeSpin.setEnabled(enabled)
        self.weatherIconSizeSpin.setEnabled(enabled)
        self.weatherUpdateIntervalCombo.setEnabled(enabled)

    def _updateCountdownSettingsEnabled(self, enabled):
        self.countdownTextColorCombo.setEnabled(enabled)
        self.countdownConnectorColorCombo.setEnabled(enabled)
        self.countdownAddButton.setEnabled(enabled)
        self.countdownListWidget.setEnabled(enabled)
        self.countdownEditButton.setEnabled(enabled)
        self.countdownDeleteButton.setEnabled(enabled)
        self.countdownTextSizeSpin.setEnabled(enabled)
        self.countdownConnectorSizeSpin.setEnabled(enabled)
        self.countdownDisplayModeCombo.setEnabled(enabled)
        self.countdownCarouselIntervalSpin.setEnabled(enabled)

    def _updateSchoolInfoSettingsEnabled(self, enabled):
        self.schoolEdit.setEnabled(enabled)
        self.schoolClassEdit.setEnabled(enabled)
        self.schoolInfoTextColorCombo.setEnabled(enabled)
        self.schoolInfoTextSizeSpin.setEnabled(enabled)

    def _updateQuickLaunchSettingsEnabled(self, enabled):
        self.showQuickLaunchSwitch.setEnabled(enabled)
        self.quickLaunchEditButton.setEnabled(enabled)

    def _updateMediaSettingsEnabled(self, enabled):
        self.showMediaCoverSwitch.setEnabled(enabled)
        self.mediaWidthSpin.setEnabled(enabled)
        self.mediaLyricsAdvanceSpin.setEnabled(enabled)

    def _connectConfigSignals(self):
        """连接配置变化信到 UI 更新"""
        # 时间设置
        cfg.showClock.valueChanged.connect(self._updateShowClockSwitch)
        cfg.showClockSeconds.valueChanged.connect(self._updateShowSecondsSwitch)
        cfg.showLunarCalendar.valueChanged.connect(self._updateShowLunarSwitch)
        cfg.clockColor.valueChanged.connect(self._updateClockColorCombo)
        cfg.clockSize.valueChanged.connect(self._updateClockSizeSpin)
        cfg.dateSize.valueChanged.connect(self._updateDateSizeSpin)

        # 一言设置
        cfg.showPoetry.valueChanged.connect(self._updateShowPoetrySwitch)
        cfg.poetryApiUrl.valueChanged.connect(self._updatePoetryApiEdit)
        cfg.poetrySize.valueChanged.connect(self._updatePoetrySizeSpin)
        cfg.poetryUpdateInterval.valueChanged.connect(self._updatePoetryUpdateIntervalCombo)

        # 天气设置
        cfg.showWeather.valueChanged.connect(self._updateShowWeatherSwitch)
        cfg.weatherSize.valueChanged.connect(self._updateWeatherSizeSpin)
        cfg.weatherIconSize.valueChanged.connect(self._updateWeatherIconSizeSpin)
        cfg.weatherUpdateInterval.valueChanged.connect(self._updateWeatherUpdateIntervalCombo)
        cfg.city.valueChanged.connect(self._updateCityButton)

        # 倒计时设置
        cfg.showCountdown.valueChanged.connect(self._updateShowCountdownSwitch)
        cfg.countdownDisplayMode.valueChanged.connect(self._updateCountdownDisplayModeCombo)
        cfg.countdownTextSize.valueChanged.connect(self._updateCountdownTextSizeSpin)
        cfg.countdownConnectorSize.valueChanged.connect(self._updateCountdownConnectorSizeSpin)
        cfg.countdownCarouselInterval.valueChanged.connect(self._updateCountdownCarouselIntervalSpin)
        cfg.countdownList.valueChanged.connect(self._updateCountdownList)
        cfg.countdownTextColor.valueChanged.connect(self._updateCountdownTextColorCombo)
        cfg.countdownConnectorColor.valueChanged.connect(self._updateCountdownConnectorColorCombo)

        # 学校信息设置
        cfg.showSchoolInfo.valueChanged.connect(self._updateShowSchoolInfoSwitch)
        cfg.schoolInfoTextColor.valueChanged.connect(self._updateSchoolInfoTextColorCombo)
        cfg.schoolInfoTextSize.valueChanged.connect(self._updateSchoolInfoTextSizeSpin)
        cfg.school.valueChanged.connect(self._updateSchoolEdit)
        cfg.schoolClass.valueChanged.connect(self._updateSchoolClassEdit)

        # 媒体设置
        cfg.showMediaInfo.valueChanged.connect(self._updateShowMediaInfoSwitch)
        cfg.showMediaCover.valueChanged.connect(self._updateShowMediaCoverSwitch)
        cfg.mediaWidth.valueChanged.connect(self._updateMediaWidthSpin)
        cfg.mediaLyricsAdvance.valueChanged.connect(self._updateMediaLyricsAdvanceSpin)

    def __connectSignalToSlot(self):
        cfg.themeChanged.connect(self._onThemeChanged)
        cfg.themeColor.valueChanged.connect(self._onThemeColorChanged)

    def _onThemeChanged(self, theme):
        self._updateTheme()

    def _onThemeColorChanged(self, value):
        self._updateCountdownTextColorCombo(cfg.countdownTextColor.value)
        self._updateCountdownConnectorColorCombo(cfg.countdownConnectorColor.value)

    def _updateShowClockSwitch(self, value):
        """更新启用时钟开关"""
        self.showClockSwitch.setChecked(value)

    def _updateShowSecondsSwitch(self, value):
        """更新显示秒针开关"""
        self.showSecondsSwitch.setChecked(value)

    def _updateShowLunarSwitch(self, value):
        """更新显示农历开关"""
        self.showLunarSwitch.setChecked(value)

    def _updateClockColorCombo(self, value):
        """更新时钟颜色下拉框"""
        try:
            self.clockColorCombo.currentTextChanged.disconnect(self._onClockColorChanged)
        except TypeError:
            pass
        self.clockColorCombo.setCurrentText(self._getColorText(value))
        self.clockColorCombo.currentTextChanged.connect(self._onClockColorChanged)

    def _updateClockSizeSpin(self, value):
        """更新时钟大小旋转框"""
        self.clockSizeSpin.setValue(value)

    def _updateDateSizeSpin(self, value):
        """更新日期大小旋转框"""
        self.dateSizeSpin.setValue(value)

    def _updateShowPoetrySwitch(self, value):
        """更新启用一言开关"""
        self.showPoetrySwitch.setChecked(value)

    def _updatePoetryApiEdit(self, value):
        """更新一言 API 地址下拉框"""
        try:
            self.poetryApiCombo.currentTextChanged.disconnect(self._onPoetryApiChanged)
        except TypeError:
            pass
        if value == 'https://api.imlcd.cn/yy/api.php':
            self.poetryApiCombo.setCurrentText(tr("home.yiyan_api"))
        elif value == 'https://www.ffapi.cn/int/v1/shici':
            self.poetryApiCombo.setCurrentText(tr("home.poetry_api"))
        else:
            self.poetryApiCombo.setCurrentText(tr("home.yiyan_api"))
        self.poetryApiCombo.currentTextChanged.connect(self._onPoetryApiChanged)

    def _updatePoetrySizeSpin(self, value):
        """更新一言大小旋转框"""
        self.poetrySizeSpin.setValue(value)

    def _updatePoetryUpdateIntervalCombo(self, value):
        """更新一言更新间隔下拉框"""
        try:
            self.poetryUpdateIntervalCombo.currentTextChanged.disconnect(self._onPoetryUpdateIntervalChanged)
        except TypeError:
            pass
        self.poetryUpdateIntervalCombo.setCurrentText(value)
        self.poetryUpdateIntervalCombo.currentTextChanged.connect(self._onPoetryUpdateIntervalChanged)

    def _updateShowWeatherSwitch(self, value):
        """更新启用天气开关"""
        self.showWeatherSwitch.setChecked(value)

    def _updateWeatherSizeSpin(self, value):
        """更新天气文字大小旋转框"""
        self.weatherSizeSpin.setValue(value)

    def _updateWeatherIconSizeSpin(self, value):
        """更新天气图标大小旋转框"""
        self.weatherIconSizeSpin.setValue(value)

    def _updateWeatherUpdateIntervalCombo(self, value):
        """更新天气更新间隔下拉框"""
        try:
            self.weatherUpdateIntervalCombo.currentTextChanged.disconnect(self._onWeatherUpdateIntervalChanged)
        except TypeError:
            pass
        self.weatherUpdateIntervalCombo.setCurrentText(value)
        self.weatherUpdateIntervalCombo.currentTextChanged.connect(self._onWeatherUpdateIntervalChanged)

    def _updateCityButton(self, value):
        """更新城市按钮"""
        self.cityButton.setText(value)

    def _createTimeSettings(self, layout):
        titleLabel = StrongBodyLabel(tr("home.time_settings"), self)  # 时间设置
        layout.addWidget(titleLabel)
        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_clock"), self)  # 启用时钟
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showClockSwitch = SwitchButton(self)
        self.showClockSwitch.setOffText('')
        self.showClockSwitch.setOnText('')
        self.showClockSwitch.setChecked(cfg.showClock.value)
        self.showClockSwitch.checkedChanged.connect(self._onShowClockChanged)
        enableLayout.addWidget(self.showClockSwitch)
        layout.addLayout(enableLayout)
        secondsLayout = QHBoxLayout()
        secondsLabel = BodyLabel(tr("home.show_seconds"), self)  # 显示秒针
        secondsLabel.setFixedWidth(100)
        secondsLayout.addWidget(secondsLabel)
        secondsLayout.addStretch()
        self.showSecondsSwitch = SwitchButton(self)
        self.showSecondsSwitch.setOffText('')
        self.showSecondsSwitch.setOnText('')
        self.showSecondsSwitch.setChecked(cfg.showClockSeconds.value)
        self.showSecondsSwitch.checkedChanged.connect(self._onShowSecondsChanged)
        secondsLayout.addWidget(self.showSecondsSwitch)
        layout.addLayout(secondsLayout)
        lunarLayout = QHBoxLayout()
        lunarLabel = BodyLabel(tr("home.show_lunar"), self)  # 显示农历
        lunarLabel.setFixedWidth(100)
        lunarLayout.addWidget(lunarLabel)
        lunarLayout.addStretch()
        self.showLunarSwitch = SwitchButton(self)
        self.showLunarSwitch.setOffText('')
        self.showLunarSwitch.setOnText('')
        self.showLunarSwitch.setChecked(cfg.showLunarCalendar.value)
        self.showLunarSwitch.checkedChanged.connect(self._onShowLunarChanged)
        lunarLayout.addWidget(self.showLunarSwitch)
        layout.addLayout(lunarLayout)
        colorLayout = QHBoxLayout()
        colorLabel = BodyLabel(tr("home.clock_color"), self)  # 时钟颜色
        colorLabel.setFixedWidth(100)
        colorLayout.addWidget(colorLabel)
        colorLayout.addStretch()
        self.clockColorCombo = ComboBox(self)
        self.clockColorCombo.addItems([tr("color.primary"), tr("color.white"), tr("color.black")])  # 主要颜色 / 白色 / 黑色
        self.clockColorCombo.setCurrentText(self._getColorText(cfg.clockColor.value))
        self.clockColorCombo.setFixedWidth(120)
        self.clockColorCombo.currentTextChanged.connect(self._onClockColorChanged)
        colorLayout.addWidget(self.clockColorCombo)
        layout.addLayout(colorLayout)
        clockSizeLayout = QHBoxLayout()
        clockSizeLabel = BodyLabel(tr("home.clock_size"), self)  # 时钟大小
        clockSizeLabel.setFixedWidth(100)
        clockSizeLayout.addWidget(clockSizeLabel)
        clockSizeLayout.addStretch()
        self.clockSizeSpin = SpinBox(self)
        self.clockSizeSpin.setRange(80, 200)
        self.clockSizeSpin.setValue(cfg.clockSize.value)
        self.clockSizeSpin.setFixedWidth(120)
        self.clockSizeSpin.valueChanged.connect(self._onClockSizeChanged)
        clockSizeLayout.addWidget(self.clockSizeSpin)
        layout.addLayout(clockSizeLayout)
        dateSizeLayout = QHBoxLayout()
        dateSizeLabel = BodyLabel(tr("home.date_size"), self)  # 日期大小
        dateSizeLabel.setFixedWidth(100)
        dateSizeLayout.addWidget(dateSizeLabel)
        dateSizeLayout.addStretch()
        self.dateSizeSpin = SpinBox(self)
        self.dateSizeSpin.setRange(12, 50)
        self.dateSizeSpin.setValue(cfg.dateSize.value)
        self.dateSizeSpin.setFixedWidth(120)
        self.dateSizeSpin.valueChanged.connect(self._onDateSizeChanged)
        dateSizeLayout.addWidget(self.dateSizeSpin)
        layout.addLayout(dateSizeLayout)

    def _createPoetrySettings(self, layout):
        titleLabel = StrongBodyLabel(tr("home.poetry_settings"), self)  # 一言设置
        layout.addWidget(titleLabel)
        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_poetry"), self)  # 启用一言
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showPoetrySwitch = SwitchButton(self)
        self.showPoetrySwitch.setOffText('')
        self.showPoetrySwitch.setOnText('')
        self.showPoetrySwitch.setChecked(cfg.showPoetry.value)
        self.showPoetrySwitch.checkedChanged.connect(self._onShowPoetryChanged)
        enableLayout.addWidget(self.showPoetrySwitch)
        layout.addLayout(enableLayout)
        apiLayout = QHBoxLayout()
        apiLabel = BodyLabel(tr("home.poetry_api_url"), self)  # 一言 API 地址
        apiLabel.setFixedWidth(100)
        apiLayout.addWidget(apiLabel)
        apiLayout.addStretch()
        self.poetryApiCombo = ComboBox(self)
        self.poetryApiCombo.addItems([
            tr("home.yiyan_api"),  # 一言 API
            tr("home.poetry_api")  # 诗词 API
        ])
        if cfg.poetryApiUrl.value == 'https://www.ffapi.cn/int/v1/shici':
            self.poetryApiCombo.setCurrentText(tr("home.poetry_api"))
        else:
            self.poetryApiCombo.setCurrentText(tr("home.yiyan_api"))
        self.poetryApiCombo.setFixedWidth(120)
        self.poetryApiCombo.currentTextChanged.connect(self._onPoetryApiChanged)
        apiLayout.addWidget(self.poetryApiCombo)
        layout.addLayout(apiLayout)
        poetrySizeLayout = QHBoxLayout()
        poetrySizeLabel = BodyLabel(tr("home.poetry_size"), self)  # 一言大小
        poetrySizeLabel.setFixedWidth(100)
        poetrySizeLayout.addWidget(poetrySizeLabel)
        poetrySizeLayout.addStretch()
        self.poetrySizeSpin = SpinBox(self)
        self.poetrySizeSpin.setRange(12, 50)
        self.poetrySizeSpin.setValue(cfg.poetrySize.value)
        self.poetrySizeSpin.setFixedWidth(120)
        self.poetrySizeSpin.valueChanged.connect(self._onPoetrySizeChanged)
        poetrySizeLayout.addWidget(self.poetrySizeSpin)
        layout.addLayout(poetrySizeLayout)
        poetryIntervalLayout = QHBoxLayout()
        poetryIntervalLabel = BodyLabel(tr("home.poetry_update_interval"), self)  # 一言更新间隔
        poetryIntervalLabel.setFixedWidth(100)
        poetryIntervalLayout.addWidget(poetryIntervalLabel)
        poetryIntervalLayout.addStretch()
        self.poetryUpdateIntervalCombo = ComboBox(self)
        self.poetryUpdateIntervalCombo.addItems([tr("time.never"), tr("time.minutes_5"), tr("time.minutes_10"), tr("time.minutes_30"), tr("time.hour_1"), tr("time.hours_3"), tr("time.hours_6"), tr("time.hours_12"), tr("time.day_1")])  # 从不 / 5 分钟 / 10 分钟 / 30 分钟 / 1 小时 / 3 小时 / 6 小时 / 12 小时 / 1 天
        self.poetryUpdateIntervalCombo.setCurrentText(cfg.poetryUpdateInterval.value)
        self.poetryUpdateIntervalCombo.setFixedWidth(120)
        self.poetryUpdateIntervalCombo.currentTextChanged.connect(self._onPoetryUpdateIntervalChanged)
        poetryIntervalLayout.addWidget(self.poetryUpdateIntervalCombo)
        layout.addLayout(poetryIntervalLayout)

    def _createWeatherSettings(self, layout):
        """创建天气设置部分"""
        titleLabel = StrongBodyLabel(tr("home.weather_settings"), self)  # 天气设置
        layout.addWidget(titleLabel)
        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_weather"), self)  # 启用天气
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showWeatherSwitch = SwitchButton(self)
        self.showWeatherSwitch.setOffText('')
        self.showWeatherSwitch.setOnText('')
        self.showWeatherSwitch.setChecked(cfg.showWeather.value)
        self.showWeatherSwitch.checkedChanged.connect(self._onShowWeatherChanged)
        enableLayout.addWidget(self.showWeatherSwitch)
        layout.addLayout(enableLayout)
        cityLayout = QHBoxLayout()
        cityLabel = BodyLabel(tr("home.city"), self)  # 城市
        cityLabel.setFixedWidth(100)
        cityLayout.addWidget(cityLabel)
        cityLayout.addStretch()
        self.cityButton = PushButton(self)
        self.cityButton.setFixedHeight(36)
        _city = cfg.city.value
        if not _city or _city in ("点击选择", "Click to select", "點據選擇"):
            self.cityButton.setText(tr("component_settings.click_to_select"))
        else:
            self.cityButton.setText(_city)
        self.cityButton.clicked.connect(self._onCityButtonClicked)
        cityLayout.addWidget(self.cityButton)
        layout.addLayout(cityLayout)
        weatherSizeLayout = QHBoxLayout()
        weatherSizeLabel = BodyLabel(tr("home.weather_text_size"), self)  # 天气文字大小
        weatherSizeLabel.setFixedWidth(100)
        weatherSizeLayout.addWidget(weatherSizeLabel)
        weatherSizeLayout.addStretch()
        self.weatherSizeSpin = SpinBox(self)
        self.weatherSizeSpin.setRange(5, 50)
        self.weatherSizeSpin.setValue(cfg.weatherSize.value)
        self.weatherSizeSpin.setFixedWidth(120)
        self.weatherSizeSpin.valueChanged.connect(self._onWeatherSizeChanged)
        weatherSizeLayout.addWidget(self.weatherSizeSpin)
        layout.addLayout(weatherSizeLayout)
        iconSizeLayout = QHBoxLayout()
        iconSizeLabel = BodyLabel(tr("home.weather_icon_size"), self)  # 天气图标大小
        iconSizeLabel.setFixedWidth(100)
        iconSizeLayout.addWidget(iconSizeLabel)
        iconSizeLayout.addStretch()
        self.weatherIconSizeSpin = SpinBox(self)
        self.weatherIconSizeSpin.setRange(32, 128)
        self.weatherIconSizeSpin.setValue(cfg.weatherIconSize.value)
        self.weatherIconSizeSpin.setFixedWidth(120)
        self.weatherIconSizeSpin.valueChanged.connect(self._onWeatherIconSizeChanged)
        iconSizeLayout.addWidget(self.weatherIconSizeSpin)
        layout.addLayout(iconSizeLayout)
        weatherIntervalLayout = QHBoxLayout()
        weatherIntervalLabel = BodyLabel(tr("home.weather_update_interval"), self)  # 天气更新间隔
        weatherIntervalLabel.setFixedWidth(100)
        weatherIntervalLayout.addWidget(weatherIntervalLabel)
        weatherIntervalLayout.addStretch()
        self.weatherUpdateIntervalCombo = ComboBox(self)
        self.weatherUpdateIntervalCombo.addItems([tr("time.never"), tr("time.minutes_5"), tr("time.minutes_15"), tr("time.minutes_30"), tr("time.hour_1"), tr("time.hours_3"), tr("time.hours_6"), tr("time.hours_12"), tr("time.hours_24")])  # 从不 / 5 分钟 / 15 分钟 / 30 分钟 / 1 小时 / 3 小时 / 6 小时 / 12 小时 / 24 小时
        self.weatherUpdateIntervalCombo.setCurrentText(cfg.weatherUpdateInterval.value)
        self.weatherUpdateIntervalCombo.setFixedWidth(120)
        self.weatherUpdateIntervalCombo.currentTextChanged.connect(self._onWeatherUpdateIntervalChanged)
        weatherIntervalLayout.addWidget(self.weatherUpdateIntervalCombo)
        layout.addLayout(weatherIntervalLayout)

    def _updateTheme(self):
        """更新主题"""
        self.setStyleSheet(load_qss('home.qss'))

    def showPanel(self):
        """显示编辑面板"""
        parent = self.parent()
        if not parent:
            return

        pr = parent.rect()
        if self.isLeftSide:
            end_rect = QRect(0, 0, self._width, pr.height())
            start_rect = QRect(-self._width, 0, self._width, pr.height())
        else:
            end_rect = QRect(pr.width() - self._width, 0, self._width, pr.height())
            start_rect = QRect(pr.width(), 0, self._width, pr.height())

        self.setGeometry(start_rect)
        self.show()
        self.updateTimer.start(1000)

        try:
            self.anim.finished.disconnect(self._onShowFinished)
        except Exception:
            pass
        self.anim.stop()
        self.anim.setDuration(300)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.start()

    def _onShowFinished(self):
        """显示动画完成"""
        try:
            self.anim.finished.disconnect(self._onShowFinished)
        except Exception:
            pass

    def hidePanel(self):
        """退出编辑模式"""
        parent = self.parent()
        if not parent:return

        home = self.mainWindow.homeInterface if hasattr(self.mainWindow, 'homeInterface') else None

        if home and hasattr(home, '_exitEditMode'):
            home._exitEditMode()

        if hasattr(parent, 'navigationInterface'):parent.navigationInterface.setEnabled(True)

        if home and hasattr(home, '_hideGuideLines'):home._hideGuideLines()

        pr = parent.rect()
        if self.isLeftSide:
            start_rect = QRect(0, 0, self._width, pr.height())
            end_rect = QRect(-self._width, 0, self._width, pr.height())
        else:
            start_rect = QRect(pr.width() - self._width, 0, self._width, pr.height())
            end_rect = QRect(pr.width(), 0, self._width, pr.height())

        # 滑出动画
        self.anim.stop()
        self.anim.setDuration(250)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)

        try:
            self.anim.finished.disconnect(self._onHideFinished)
        except Exception:
            pass
        self.anim.finished.connect(self._onHideFinished)
        self.anim.start()

    def _onHideFinished(self):
        """隐藏动画完成"""
        try:
            self.updateTimer.stop()
            self.hide()
        finally:
            try:
                self.anim.finished.disconnect(self._onHideFinished)
            except Exception:
                pass

    def _onShowClockChanged(self, checked: bool):
        """启用时钟开关变化"""
        cfg.showClock.value = checked
        self._updateTimeSettingsEnabled(checked)
        logger.info(f"时间设置：启用时钟={'开启' if checked else '关闭'}")

    def _onShowSecondsChanged(self, checked: bool):
        """显示秒针开关变化"""
        cfg.showClockSeconds.value = checked
        logger.info(f"时间设置：显示秒针={'开启' if checked else '关闭'}")

    def _onShowLunarChanged(self, checked: bool):
        """显示农历开关变化"""
        cfg.showLunarCalendar.value = checked
        logger.info(f"时间设置：显示农历={'开启' if checked else '关闭'}")

    def _getColorText(self, color, default='main'):
        """获取颜色文本表示"""
        if not hasattr(color, 'name'):
            if default == 'red':return tr("color.red")  # 红色
            elif default == 'white':return tr("color.white")  # 白色
            return tr("color.primary")  # 主要颜色
        color_hex = color.name().upper()
        try:
            theme_color = cfg.themeColor.value
            if hasattr(theme_color, 'name'):
                theme_hex = theme_color.name().upper()
                if theme_hex == color_hex:return tr("color.primary")  # 主要颜色
        except Exception:pass
        if color_hex == '#FF0000':return tr("color.red")  # 红色
        elif color_hex == '#FFFFFF':return tr("color.white")  # 白色
        elif color_hex == '#000000':return tr("color.black")  # 黑色
        return tr("color.primary")  # 主要颜色

    def _onClockColorChanged(self, text: str):
        """时钟颜色变化"""

        if text == tr("color.white"):
            cfg.clockColor.value = "#FFFFFF"  # 白色
        elif text == tr("color.black"):
            cfg.clockColor.value = "#000000"  # 黑色
        else:
            cfg.clockColor.value = cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else str(cfg.themeColor.value)

        logger.info(f"时间设置：时钟颜色={text}")

    def _onClockSizeChanged(self, value: int):
        """时钟大小变化"""
        cfg.clockSize.value = value
        logger.info(f"时间设置：时钟大小={value}px")

    def _onDateSizeChanged(self, value: int):
        """日期大小变化"""
        cfg.dateSize.value = value
        logger.info(f"时间设置：日期大小={value}px")

    def _onShowPoetryChanged(self, checked: bool):
        """启用一言开关变化"""
        cfg.showPoetry.value = checked
        self._updatePoetrySettingsEnabled(checked)
        if hasattr(self.mainWindow, 'homeContent'):
            for widget in self.mainWindow.homeContent.findChildren(QWidget):
                if widget.objectName() == 'poetryWidget':
                    widget.setVisible(checked)
        logger.info(f"一言设置：启用一言={'开启' if checked else '关闭'}")

    def _onPoetryApiChanged(self, text: str):
        """一言 API 地址变化"""
        if text == tr("home.yiyan_api"):  # 一言 API
            cfg.poetryApiUrl.value = 'https://api.imlcd.cn/yy/api.php'
        elif text == tr("home.poetry_api"):  # 诗词 API
            cfg.poetryApiUrl.value = 'https://www.ffapi.cn/int/v1/shici'
        else:
            cfg.poetryApiUrl.value = 'https://api.imlcd.cn/yy/api.php'
        logger.info(f"一言设置：API 地址={cfg.poetryApiUrl.value}")

    def _onPoetryUpdateIntervalChanged(self, text: str):
        """一言更新间隔变化"""
        cfg.poetryUpdateInterval.value = text
        logger.info(f"一言设置：更新间隔={text}")

    def _onPoetrySizeChanged(self, value: int):
        """一言大小变化"""
        cfg.poetrySize.value = value
        logger.info(f"一言设置：一言大小={value}px")

    def _onShowWeatherChanged(self, checked: bool):
        """启用天气开关变化"""
        cfg.showWeather.value = checked
        self._updateWeatherSettingsEnabled(checked)
        logger.info(f"天气设置：启用天气={'开启' if checked else '关闭'}")

    def _onWeatherSizeChanged(self, value: int):
        """天气文字大小变化"""
        cfg.weatherSize.value = value
        logger.info(f"天气设置：天气文字大小={value}px")

    def _onWeatherIconSizeChanged(self, value: int):
        """天气图标大小变化"""
        cfg.weatherIconSize.value = value
        logger.info(f"天气设置：天气图标大小={value}px")

    def _onWeatherUpdateIntervalChanged(self, text: str):
        """天气更新间隔变化"""
        cfg.weatherUpdateInterval.value = text
        logger.info(f"天气设置：更新间隔={text}")
    def _onCityButtonClicked(self):
        """城市选择按钮点击"""
        from services.weather import RegionSelectorDialog, RegionDatabase
        dialog = RegionSelectorDialog(self.mainWindow)
        if dialog.exec():
            selected_region = dialog.get_selected_region()
            if selected_region:
                cfg.city.value = selected_region
                
                # 从数据库获取经纬度
                db = RegionDatabase()
                lon, lat = db.get_coordinates(selected_region)
                if lon is not None and lat is not None:
                    cfg.longitude.value = lon
                    cfg.latitude.value = lat
                    logger.info(f"天气设置：城市={selected_region}, 经纬度=({lon}, {lat})")
                    

    def _togglePosition(self):
        """切换编辑面板位置"""
        self.isLeftSide = not self.isLeftSide
        if self.isLeftSide:
            self.positionButton.setIcon(FUI.CARE_RIGHT_SOLID)
            self.positionButton.setToolTip(tr("home.switch_to_right"))  # 切换到右侧
        else:
            self.positionButton.setIcon(FUI.CARE_LEFT_SOLID)
            self.positionButton.setToolTip(tr("home.switch_to_left"))  # 切换到左侧

        if self.isVisible():
            self.showPanel()

    def updatePositionOnResize(self):
        if not self.isVisible():return
        parent = self.parent()
        pr = parent.rect()
        if self.isLeftSide:new_rect = QRect(0, 0, self._width, pr.height())
        else:new_rect = QRect(pr.width() - self._width, 0, self._width, pr.height())
        self.anim.stop()
        self.setGeometry(new_rect)

    def _createCountdownSettings(self, layout):
        """创建倒计时设置"""
        layout.setSpacing(8)

        titleLabel = StrongBodyLabel(tr("home.countdown_settings"), self)  # 倒计时设置
        layout.addWidget(titleLabel)

        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_countdown"), self)  # 启用倒计时
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showCountdownSwitch = SwitchButton(self)
        self.showCountdownSwitch.setOffText('')
        self.showCountdownSwitch.setOnText('')
        self.showCountdownSwitch.setChecked(cfg.showCountdown.value)
        self.showCountdownSwitch.checkedChanged.connect(self._onShowCountdownChanged)
        enableLayout.addWidget(self.showCountdownSwitch)
        layout.addLayout(enableLayout)

        # 文字颜色
        textColorLayout = QHBoxLayout()
        textColorLabel = BodyLabel(tr("home.text_color"), self)
        textColorLabel.setFixedWidth(100)
        textColorLayout.addWidget(textColorLabel)
        textColorLayout.addStretch()
        self.countdownTextColorCombo = ComboBox(self)
        self.countdownTextColorCombo.addItems([tr("color.red"), tr("color.white"), tr("color.black"), tr("color.primary")])  # 红色 / 白色 / 黑色 / 主要颜色
        self.countdownTextColorCombo.setCurrentText(self._getColorText(cfg.countdownTextColor.value, 'red'))
        self.countdownTextColorCombo.setFixedWidth(120)
        self.countdownTextColorCombo.currentTextChanged.connect(self._onCountdownTextColorChanged)
        textColorLayout.addWidget(self.countdownTextColorCombo)
        layout.addLayout(textColorLayout)

        # 连接词颜色
        connectorColorLayout = QHBoxLayout()
        connectorColorLabel = BodyLabel(tr("home.connector_color"), self)  # 连接符颜色
        connectorColorLabel.setFixedWidth(100)
        connectorColorLayout.addWidget(connectorColorLabel)
        connectorColorLayout.addStretch()
        self.countdownConnectorColorCombo = ComboBox(self)
        self.countdownConnectorColorCombo.addItems([tr("color.red"), tr("color.white"), tr("color.black"), tr("color.primary")])  # 红色 / 白色 / 黑色 / 主要颜色
        self.countdownConnectorColorCombo.setCurrentText(self._getColorText(cfg.countdownConnectorColor.value, 'white'))
        self.countdownConnectorColorCombo.setFixedWidth(120)
        self.countdownConnectorColorCombo.currentTextChanged.connect(self._onCountdownConnectorColorChanged)
        connectorColorLayout.addWidget(self.countdownConnectorColorCombo)
        layout.addLayout(connectorColorLayout)

        # 文字大小
        textSizeLayout = QHBoxLayout()
        textSizeLabel = BodyLabel(tr("home.text_size"), self)
        textSizeLabel.setFixedWidth(100)
        textSizeLayout.addWidget(textSizeLabel)
        textSizeLayout.addStretch()
        self.countdownTextSizeSpin = SpinBox(self)
        self.countdownTextSizeSpin.setRange(12, 120)
        self.countdownTextSizeSpin.setValue(cfg.countdownTextSize.value)
        self.countdownTextSizeSpin.setFixedWidth(120)
        self.countdownTextSizeSpin.valueChanged.connect(self._onCountdownTextSizeChanged)
        textSizeLayout.addWidget(self.countdownTextSizeSpin)
        layout.addLayout(textSizeLayout)

        # 连接词大小
        connectorSizeLayout = QHBoxLayout()
        connectorSizeLabel = BodyLabel(tr("home.connector_size"), self)  # 连接符大小
        connectorSizeLabel.setFixedWidth(100)
        connectorSizeLayout.addWidget(connectorSizeLabel)
        connectorSizeLayout.addStretch()
        self.countdownConnectorSizeSpin = SpinBox(self)
        self.countdownConnectorSizeSpin.setRange(12, 60)
        self.countdownConnectorSizeSpin.setValue(cfg.countdownConnectorSize.value)
        self.countdownConnectorSizeSpin.setFixedWidth(120)
        self.countdownConnectorSizeSpin.valueChanged.connect(self._onCountdownConnectorSizeChanged)
        connectorSizeLayout.addWidget(self.countdownConnectorSizeSpin)
        layout.addLayout(connectorSizeLayout)

        # 显示模式
        displayModeLayout = QHBoxLayout()
        displayModeLabel = BodyLabel(tr("home.display_mode"), self)  # 显示模式
        displayModeLabel.setFixedWidth(100)
        displayModeLayout.addWidget(displayModeLabel)
        displayModeLayout.addStretch()
        self.countdownDisplayModeCombo = ComboBox(self)
        self.countdownDisplayModeCombo.addItems([tr("home.simultaneous"), tr("home.carousel")])  # 同时显示 / 轮播显示
        self.countdownDisplayModeCombo.setCurrentText(tr("home.simultaneous") if cfg.countdownDisplayMode.value == 'simultaneous' else tr("home.carousel"))
        self.countdownDisplayModeCombo.setFixedWidth(120)
        self.countdownDisplayModeCombo.currentTextChanged.connect(self._onCountdownDisplayModeChanged)
        displayModeLayout.addWidget(self.countdownDisplayModeCombo)
        layout.addLayout(displayModeLayout)

        # 轮播间隔
        carouselIntervalLayout = QHBoxLayout()
        carouselIntervalLabel = BodyLabel(tr("home.carousel_interval"), self)  # 轮播间隔
        carouselIntervalLabel.setFixedWidth(100)
        carouselIntervalLayout.addWidget(carouselIntervalLabel)
        carouselIntervalLayout.addStretch()
        self.countdownCarouselIntervalSpin = SpinBox(self)
        self.countdownCarouselIntervalSpin.setRange(1, 60)
        self.countdownCarouselIntervalSpin.setValue(cfg.countdownCarouselInterval.value)
        self.countdownCarouselIntervalSpin.setFixedWidth(120)
        self.countdownCarouselIntervalSpin.valueChanged.connect(self._onCountdownCarouselIntervalChanged)
        carouselIntervalLayout.addWidget(self.countdownCarouselIntervalSpin)
        layout.addLayout(carouselIntervalLayout)

        actionLayout = QHBoxLayout()
        actionLabel = BodyLabel(tr("home.countdown_actions"), self)  # 倒计时操作
        actionLabel.setFixedWidth(100)
        actionLayout.addWidget(actionLabel)
        actionLayout.addStretch()
        self.countdownAddButton = PushButton(FUI.ADD, tr("home.add"), self)  # 添加
        self.countdownAddButton.clicked.connect(self._onCountdownAddClicked)
        actionLayout.addWidget(self.countdownAddButton)
        self.countdownEditButton = PushButton(FUI.EDIT, tr("home.edit"), self)  # 编辑
        self.countdownEditButton.clicked.connect(self._onCountdownEditClicked)
        actionLayout.addWidget(self.countdownEditButton)
        self.countdownDeleteButton = PushButton(FUI.DELETE, tr("home.delete"), self)  # 删除
        self.countdownDeleteButton.clicked.connect(self._onCountdownDeleteClicked)
        actionLayout.addWidget(self.countdownDeleteButton)
        actionLayout.addStretch()
        layout.addLayout(actionLayout)

    def _createCountdownListCard(self, layout):
        self.countdownListCard = CardWidget(self)
        cardLayout = QVBoxLayout(self.countdownListCard)
        cardLayout.setContentsMargins(16, 12, 16, 12)
        cardLayout.setSpacing(10)

        listLabel = StrongBodyLabel(tr("home.countdown_list"), self)  # 倒计时列表
        cardLayout.addWidget(listLabel)

        self.countdownListWidget = ListWidget(self.countdownListCard)
        self.countdownListWidget.setMinimumHeight(120)
        self._updateCountdownList()
        cardLayout.addWidget(self.countdownListWidget)

        layout.addWidget(self.countdownListCard)

    def _updateShowCountdownSwitch(self, value):
        self.showCountdownSwitch.setChecked(value)
        self._updateCountdownSettingsEnabled(value)

    def _updateCountdownDisplayModeCombo(self, value):
        try:
            self.countdownDisplayModeCombo.currentTextChanged.disconnect(self._onCountdownDisplayModeChanged)
        except TypeError:
            pass
        self.countdownDisplayModeCombo.setCurrentText(tr("home.simultaneous") if value == 'simultaneous' else tr("home.carousel"))  # 同时显示 / 轮播显示
        self.countdownDisplayModeCombo.currentTextChanged.connect(self._onCountdownDisplayModeChanged)

    def _updateCountdownTextSizeSpin(self, value):
        self.countdownTextSizeSpin.setValue(value)

    def _updateCountdownConnectorSizeSpin(self, value):
        self.countdownConnectorSizeSpin.setValue(value)

    def _updateCountdownCarouselIntervalSpin(self, value):
        self.countdownCarouselIntervalSpin.setValue(value)

    def _updateCountdownTextColorCombo(self, value):
        self.countdownTextColorCombo.setCurrentText(self._getColorText(value, 'red'))

    def _updateCountdownConnectorColorCombo(self, value):
        self.countdownConnectorColorCombo.setCurrentText(self._getColorText(value, 'white'))

    def _updateShowSchoolInfoSwitch(self, value):
        self.schoolInfoSwitch.setChecked(value)
        self._updateSchoolInfoSettingsEnabled(value)

    def _updateSchoolInfoTextColorCombo(self, value):
        self.schoolInfoTextColorCombo.setCurrentText(self._getColorText(value, 'white'))

    def _updateSchoolInfoTextSizeSpin(self, value):
        self.schoolInfoTextSizeSpin.setValue(value)

    def _updateSchoolEdit(self, value):
        self.schoolEdit.setText(value)

    def _updateSchoolClassEdit(self, value):
        self.schoolClassEdit.setText(value)

    def _formatRemainingTime(self, target_time_str):
        try:
            target = datetime.datetime.strptime(target_time_str, '%Y-%m-%d %H:%M')
            now = precise_now()
            delta = target - now
            total_seconds = int(delta.total_seconds())
            target_date = target.date()
            now_date = now.date()
            if target_date == now_date and total_seconds < 0:
                return tr("time.today")
            elif total_seconds > 0:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                if days >= 3:
                    return f"{days}天"
                elif days >= 1:
                    return f"{days}天{hours}时"
                elif hours >= 1:
                    return f"{hours}时"
                elif minutes >= 1:
                    return f"{minutes}分{seconds}秒"
                else:
                    return f"{seconds}秒"
            else:
                return f"已过去{abs(total_seconds) // 86400}天"
        except Exception:
            return ""

    def _updateCountdownList(self):
        if not hasattr(self, 'countdownListWidget') or self.countdownListWidget is None:
            return
        current_row = self.countdownListWidget.currentRow()
        self.countdownListWidget.clear()
        countdown_list = cfg.countdownList.value or []
        for cd in countdown_list:
            title = cd.get('title', '')
            target_time = cd.get('target_time', '')
            if title and target_time:
                remaining = self._formatRemainingTime(target_time)
                if remaining:
                    self.countdownListWidget.addItem(f"{title} {remaining}")
        if 0 <= current_row < self.countdownListWidget.count():
            self.countdownListWidget.setCurrentRow(current_row)

    def _onShowCountdownChanged(self, checked: bool):
        cfg.showCountdown.value = checked
        self._updateCountdownSettingsEnabled(checked)
        logger.info(f"倒计时设置：启用倒计时={'开启' if checked else '关闭'}")

    def _onCountdownDisplayModeChanged(self, text: str):
        cfg.countdownDisplayMode.value = 'simultaneous' if text == tr("home.simultaneous") else 'carousel'  # 同时显示 / 轮播显示
        logger.info(f"倒计时设置：显示模式={text}")

    def _onCountdownTextSizeChanged(self, value: int):
        cfg.countdownTextSize.value = value
        logger.info(f"倒计时设置：文字大小={value}px")

    def _onCountdownConnectorSizeChanged(self, value: int):
        cfg.countdownConnectorSize.value = value
        logger.info(f"倒计时设置：连接词大小={value}px")

    def _onCountdownCarouselIntervalChanged(self, value: int):
        cfg.countdownCarouselInterval.value = value
        logger.info(f"倒计时设置：轮播间隔={value}秒")

    def _onCountdownAddClicked(self):
        dialog = CountdownEditDialog(self.mainWindow)
        if dialog.exec():
            countdown_data = dialog.get_countdown()
            if countdown_data:
                countdown_list = cfg.countdownList.value or []
                countdown_list.append(countdown_data)
                cfg.countdownList.value = countdown_list
                save_cfg()
                current_row = self.countdownListWidget.currentRow()
                self._updateCountdownList()
                if self.countdownListWidget.count() > 0:
                    self.countdownListWidget.setCurrentRow(self.countdownListWidget.count() - 1)
                logger.info(f"倒计时设置：添加倒计时={countdown_data}")

    def _onCountdownEditClicked(self):
        current_row = self.countdownListWidget.currentRow()
        if current_row < 0:
            InfoBar.warning(tr("home.edit_countdown"), tr("home.select_countdown_first"), parent=self, duration=3000)  # 编辑倒计时 / 请先选择一个倒计时
            return
        countdown_list = cfg.countdownList.value or []
        if current_row >= len(countdown_list):
            return

        dialog = CountdownEditDialog(self.mainWindow, countdown_list[current_row])
        if dialog.exec():
            countdown_data = dialog.get_countdown()
            if countdown_data:
                countdown_list[current_row] = countdown_data
                cfg.countdownList.value = countdown_list
                save_cfg()
                self._updateCountdownList()
                if 0 <= current_row < self.countdownListWidget.count():
                    self.countdownListWidget.setCurrentRow(current_row)
                logger.info(f"倒计时设置：编辑倒计时={countdown_data}")

    def _onCountdownDeleteClicked(self):
        current_row = self.countdownListWidget.currentRow()
        if current_row < 0:
            InfoBar.warning(tr("home.delete_countdown"), tr("home.select_countdown_first"), parent=self, duration=3000)  # 删除倒计时 / 请先选择一个倒计时
            return
        countdown_list = cfg.countdownList.value or []
        if current_row >= len(countdown_list):
            return
        countdown_list.pop(current_row)
        cfg.countdownList.value = countdown_list
        save_cfg()
        self._updateCountdownList()
        if self.countdownListWidget.count() > 0:
            new_row = min(current_row, self.countdownListWidget.count() - 1)
            self.countdownListWidget.setCurrentRow(new_row)
        logger.info(f"倒计时设置：删除倒计时索引={current_row}")

    def _onCountdownTextColorChanged(self, text: str):
        """倒计时文字颜色变化"""

        if text == tr("color.red"):
            cfg.countdownTextColor.value = "#FF0000"
        elif text == tr("color.white"):  # 白色
            cfg.countdownTextColor.value = "#FFFFFF"
        elif text == tr("color.black"):
            cfg.countdownTextColor.value = "#000000"
        else:
            cfg.countdownTextColor.value = cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else str(cfg.themeColor.value)

        logger.info(f"倒计时设置：文字颜色={text}")

    def _onCountdownConnectorColorChanged(self, text: str):
        """倒计时连接词颜色变化"""

        if text == tr("color.red"):
            cfg.countdownConnectorColor.value = "#FF0000"
        elif text == tr("color.white"):
            cfg.countdownConnectorColor.value = "#FFFFFF"
        elif text == tr("color.black"):
            cfg.countdownConnectorColor.value = "#000000"
        else:
            cfg.countdownConnectorColor.value = cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else str(cfg.themeColor.value)

        logger.info(f"倒计时设置：连接词颜色={text}")

    def _onShowSchoolInfoChanged(self, checked: bool):
        cfg.showSchoolInfo.value = checked
        self._updateSchoolInfoSettingsEnabled(checked)
        logger.info(f"学校信息：启用学校信息={'开启' if checked else '关闭'}")

    def _onSchoolClassChanged(self, text: str):
        cfg.schoolClass.value = text
        logger.info(f"学校信息：班级={text}")

    def _onSchoolChanged(self, text: str):
        cfg.school.value = text
        logger.info(f"学校信息：学校={text}")

    def _onSchoolInfoTextColorChanged(self, text: str):

        if text == tr("color.white"):
            cfg.schoolInfoTextColor.value = "#FFFFFF"
        elif text == tr("color.black"):
            cfg.schoolInfoTextColor.value = "#000000"
        elif text == tr("color.red"):  # 红色
            cfg.schoolInfoTextColor.value = "#FF0000"
        else:
            cfg.schoolInfoTextColor.value = cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else str(cfg.themeColor.value)

        logger.info(f"学校信息：文字颜色={text}")

    def _onSchoolInfoTextSizeChanged(self, value: int):
        cfg.schoolInfoTextSize.value = value
        logger.info(f"学校信息：文字大小={value}px")

    def _onShowQuickLaunchChanged(self, checked: bool):
        cfg.showQuickLaunch.value = checked
        save_cfg()
        self.mainWindow.refresh_quick_launch()

    def _onQuickLaunchEditClicked(self):
        dialog = QuickLaunchEditDialog(self.mainWindow)
        dialog.exec()
        self.mainWindow.refresh_quick_launch()

    def _onQuickLaunchIconSizeChanged(self, value: int):
        cfg.quickLaunchIconSize.value = value
        save_cfg()
        self.mainWindow.refresh_quick_launch()

    def _onQuickLaunchIconSpacingChanged(self, value: int):
        cfg.quickLaunchIconSpacing.value = value
        save_cfg()
        self.mainWindow.refresh_quick_launch()

    def _onQuickLaunchShowLabelsChanged(self, checked: bool):
        cfg.quickLaunchShowLabels.value = checked
        save_cfg()
        self.mainWindow.refresh_quick_launch()

    def refreshQuickLaunchSettings(self):
        self.showQuickLaunchSwitch.setChecked(cfg.showQuickLaunch.value)
        self.quickLaunchIconSizeSpin.setValue(cfg.quickLaunchIconSize.value)
        self.quickLaunchIconSpacingSpin.setValue(cfg.quickLaunchIconSpacing.value)
        self.quickLaunchShowLabelsSwitch.setChecked(cfg.quickLaunchShowLabels.value)

    def refreshAllSettings(self):
        self.showClockSwitch.setChecked(cfg.showClock.value)
        self.showSecondsSwitch.setChecked(cfg.showClockSeconds.value)
        self.showLunarSwitch.setChecked(cfg.showLunarCalendar.value)
        self.clockColorCombo.setCurrentText(self._getColorText(cfg.clockColor.value))
        self.clockSizeSpin.setValue(cfg.clockSize.value)
        self.dateSizeSpin.setValue(cfg.dateSize.value)

        self.showPoetrySwitch.setChecked(cfg.showPoetry.value)
        if cfg.poetryApiUrl.value == 'https://www.ffapi.cn/int/v1/shici':
            self.poetryApiCombo.setCurrentText(tr("home.poetry_api"))
        else:
            self.poetryApiCombo.setCurrentText(tr("home.yiyan_api"))
        self.poetrySizeSpin.setValue(cfg.poetrySize.value)
        self.poetryUpdateIntervalCombo.setCurrentText(cfg.poetryUpdateInterval.value)

        self.showWeatherSwitch.setChecked(cfg.showWeather.value)
        self.cityButton.setText(cfg.city.value)
        self.weatherSizeSpin.setValue(cfg.weatherSize.value)
        self.weatherIconSizeSpin.setValue(cfg.weatherIconSize.value)
        self.weatherUpdateIntervalCombo.setCurrentText(cfg.weatherUpdateInterval.value)

        self.showCountdownSwitch.setChecked(cfg.showCountdown.value)
        self.countdownDisplayModeCombo.setCurrentText(tr("home.simultaneous") if cfg.countdownDisplayMode.value == 'simultaneous' else tr("home.carousel"))
        self.countdownTextSizeSpin.setValue(cfg.countdownTextSize.value)
        self.countdownConnectorSizeSpin.setValue(cfg.countdownConnectorSize.value)
        self.countdownCarouselIntervalSpin.setValue(cfg.countdownCarouselInterval.value)
        self.countdownTextColorCombo.setCurrentText(self._getColorText(cfg.countdownTextColor.value, 'red'))
        self.countdownConnectorColorCombo.setCurrentText(self._getColorText(cfg.countdownConnectorColor.value, 'white'))
        self._updateCountdownList()

        self.schoolInfoSwitch.setChecked(cfg.showSchoolInfo.value)
        self.schoolEdit.setText(cfg.school.value)
        self.schoolClassEdit.setText(cfg.schoolClass.value)
        self.schoolInfoTextColorCombo.setCurrentText(self._getColorText(cfg.schoolInfoTextColor.value, 'white'))
        self.schoolInfoTextSizeSpin.setValue(cfg.schoolInfoTextSize.value)

        self.refreshQuickLaunchSettings()
        self.refreshMediaSettings()

    def refreshMediaSettings(self):
        self.showMediaInfoSwitch.setChecked(cfg.showMediaInfo.value)
        self.showMediaCoverSwitch.setChecked(cfg.showMediaCover.value)
        self.mediaWidthSpin.setValue(cfg.mediaWidth.value)
        self.mediaLyricsAdvanceSpin.setValue(cfg.mediaLyricsAdvance.value)

    def _createSchoolInfoSettings(self, layout):
        """创建学校信息设置"""
        titleLabel = StrongBodyLabel(tr("home.school_info"), self)  # 学校信息
        layout.addWidget(titleLabel)

        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_school_info"), self)  # 启用学校信息
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.schoolInfoSwitch = SwitchButton(self)
        self.schoolInfoSwitch.setOffText('')
        self.schoolInfoSwitch.setOnText('')
        self.schoolInfoSwitch.setChecked(cfg.showSchoolInfo.value)
        self.schoolInfoSwitch.checkedChanged.connect(self._onShowSchoolInfoChanged)
        enableLayout.addWidget(self.schoolInfoSwitch)
        layout.addLayout(enableLayout)

        schoolClassLayout = QHBoxLayout()
        schoolClassLabel = BodyLabel(tr("home.class_name"), self)  # 班级名称
        schoolClassLabel.setFixedWidth(100)
        schoolClassLayout.addWidget(schoolClassLabel)
        schoolClassLayout.addStretch()
        self.schoolClassEdit = LineEdit(self)
        self.schoolClassEdit.setText(cfg.schoolClass.value)
        self.schoolClassEdit.setPlaceholderText(tr("home.class_name_example"))  # 例如：高三(1)班
        self.schoolClassEdit.setFixedWidth(120)
        self.schoolClassEdit.textChanged.connect(self._onSchoolClassChanged)
        schoolClassLayout.addWidget(self.schoolClassEdit)
        layout.addLayout(schoolClassLayout)

        schoolLayout = QHBoxLayout()
        schoolLabel = BodyLabel(tr("home.school_name"), self)  # 学校名称
        schoolLabel.setFixedWidth(100)
        schoolLayout.addWidget(schoolLabel)
        schoolLayout.addStretch()
        self.schoolEdit = LineEdit(self)
        self.schoolEdit.setText(cfg.school.value)
        self.schoolEdit.setPlaceholderText(tr("home.school_name_example"))  # 例如：XX中学
        self.schoolEdit.setFixedWidth(120)
        self.schoolEdit.textChanged.connect(self._onSchoolChanged)
        schoolLayout.addWidget(self.schoolEdit)
        layout.addLayout(schoolLayout)

        textColorLayout = QHBoxLayout()
        textColorLabel = BodyLabel(tr("home.text_color"), self)
        textColorLabel.setFixedWidth(100)
        textColorLayout.addWidget(textColorLabel)
        textColorLayout.addStretch()
        self.schoolInfoTextColorCombo = ComboBox(self)
        self.schoolInfoTextColorCombo.addItems([tr("color.white"), tr("color.black"), tr("color.red"), tr("color.primary")])  # 白色 / 黑色 / 红色 / 主要颜色
        self.schoolInfoTextColorCombo.setCurrentText(self._getColorText(cfg.schoolInfoTextColor.value, 'white'))
        self.schoolInfoTextColorCombo.setFixedWidth(120)
        self.schoolInfoTextColorCombo.currentTextChanged.connect(self._onSchoolInfoTextColorChanged)
        textColorLayout.addWidget(self.schoolInfoTextColorCombo)
        layout.addLayout(textColorLayout)

        textSizeLayout = QHBoxLayout()
        textSizeLabel = BodyLabel(tr("home.text_size"), self)
        textSizeLabel.setFixedWidth(100)
        textSizeLayout.addWidget(textSizeLabel)
        textSizeLayout.addStretch()
        self.schoolInfoTextSizeSpin = SpinBox(self)
        self.schoolInfoTextSizeSpin.setRange(12, 60)
        self.schoolInfoTextSizeSpin.setValue(cfg.schoolInfoTextSize.value)
        self.schoolInfoTextSizeSpin.setFixedWidth(120)
        self.schoolInfoTextSizeSpin.valueChanged.connect(self._onSchoolInfoTextSizeChanged)
        textSizeLayout.addWidget(self.schoolInfoTextSizeSpin)
        layout.addLayout(textSizeLayout)

    def _createQuickLaunchSettings(self, layout):
        """创建快捷启动栏设置"""
        titleLabel = StrongBodyLabel(tr("home.quick_launch_bar"), self)  # 快捷启动栏
        layout.addWidget(titleLabel)

        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_quick_launch"), self)
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showQuickLaunchSwitch = SwitchButton(self)
        self.showQuickLaunchSwitch.setOffText('')
        self.showQuickLaunchSwitch.setOnText('')
        self.showQuickLaunchSwitch.setChecked(cfg.showQuickLaunch.value)
        self.showQuickLaunchSwitch.checkedChanged.connect(self._onShowQuickLaunchChanged)
        enableLayout.addWidget(self.showQuickLaunchSwitch)
        layout.addLayout(enableLayout)

        iconSizeLayout = QHBoxLayout()
        iconSizeLabel = BodyLabel(tr("home.icon_size"), self)
        iconSizeLabel.setFixedWidth(100)
        iconSizeLayout.addWidget(iconSizeLabel)
        iconSizeLayout.addStretch()
        self.quickLaunchIconSizeSpin = SpinBox(self)
        self.quickLaunchIconSizeSpin.setRange(32, 96)
        self.quickLaunchIconSizeSpin.setValue(cfg.quickLaunchIconSize.value)
        self.quickLaunchIconSizeSpin.setFixedWidth(120)
        self.quickLaunchIconSizeSpin.valueChanged.connect(lambda v: self._onQuickLaunchIconSizeChanged(v))
        iconSizeLayout.addWidget(self.quickLaunchIconSizeSpin)
        layout.addLayout(iconSizeLayout)

        iconSpacingLayout = QHBoxLayout()
        iconSpacingLabel = BodyLabel(tr("home.icon_spacing"), self)
        iconSpacingLabel.setFixedWidth(100)
        iconSpacingLayout.addWidget(iconSpacingLabel)
        iconSpacingLayout.addStretch()
        self.quickLaunchIconSpacingSpin = SpinBox(self)
        self.quickLaunchIconSpacingSpin.setRange(4, 40)
        self.quickLaunchIconSpacingSpin.setValue(cfg.quickLaunchIconSpacing.value)
        self.quickLaunchIconSpacingSpin.setFixedWidth(120)
        self.quickLaunchIconSpacingSpin.valueChanged.connect(lambda v: self._onQuickLaunchIconSpacingChanged(v))
        iconSpacingLayout.addWidget(self.quickLaunchIconSpacingSpin)
        layout.addLayout(iconSpacingLayout)

        showLabelsLayout = QHBoxLayout()
        showLabelsLabel = BodyLabel(tr("home.show_name"), self)
        showLabelsLabel.setFixedWidth(100)
        showLabelsLayout.addWidget(showLabelsLabel)
        showLabelsLayout.addStretch()
        self.quickLaunchShowLabelsSwitch = SwitchButton(self)
        self.quickLaunchShowLabelsSwitch.setChecked(cfg.quickLaunchShowLabels.value)
        self.quickLaunchShowLabelsSwitch.setOffText('')
        self.quickLaunchShowLabelsSwitch.setOnText('')
        self.quickLaunchShowLabelsSwitch.checkedChanged.connect(lambda v: self._onQuickLaunchShowLabelsChanged(v))
        showLabelsLayout.addWidget(self.quickLaunchShowLabelsSwitch)
        layout.addLayout(showLabelsLayout)

        appsLayout = QHBoxLayout()
        appsLabel = BodyLabel(tr("home.app_management"), self)
        appsLabel.setFixedWidth(100)
        appsLayout.addWidget(appsLabel)
        appsLayout.addStretch()
        self.quickLaunchEditButton = PushButton(tr("home.edit_apps"), self)
        self.quickLaunchEditButton.setFixedHeight(36)
        self.quickLaunchEditButton.clicked.connect(self._onQuickLaunchEditClicked)
        appsLayout.addWidget(self.quickLaunchEditButton)
        layout.addLayout(appsLayout)

    def _createMediaSettings(self, layout):
        """创建媒体设置部分"""
        titleLabel = StrongBodyLabel(tr("home.media_info"), self)
        layout.addWidget(titleLabel)

        enableLayout = QHBoxLayout()
        enableLabel = BodyLabel(tr("home.enable_media"), self)
        enableLabel.setFixedWidth(100)
        enableLayout.addWidget(enableLabel)
        enableLayout.addStretch()
        self.showMediaInfoSwitch = SwitchButton(self)
        self.showMediaInfoSwitch.setOffText('')
        self.showMediaInfoSwitch.setOnText('')
        self.showMediaInfoSwitch.setChecked(cfg.showMediaInfo.value)
        self.showMediaInfoSwitch.checkedChanged.connect(self._onShowMediaInfoChanged)
        enableLayout.addWidget(self.showMediaInfoSwitch)
        layout.addLayout(enableLayout)

        coverLayout = QHBoxLayout()
        coverLabel = BodyLabel(tr("home.show_cover"), self)
        coverLabel.setFixedWidth(100)
        coverLayout.addWidget(coverLabel)
        coverLayout.addStretch()
        self.showMediaCoverSwitch = SwitchButton(self)
        self.showMediaCoverSwitch.setOffText('')
        self.showMediaCoverSwitch.setOnText('')
        self.showMediaCoverSwitch.setChecked(cfg.showMediaCover.value)
        self.showMediaCoverSwitch.checkedChanged.connect(self._onShowMediaCoverChanged)
        coverLayout.addWidget(self.showMediaCoverSwitch)
        layout.addLayout(coverLayout)

        widthLayout = QHBoxLayout()
        widthLabel = BodyLabel(tr("home.component_width"), self)
        widthLabel.setFixedWidth(100)
        widthLayout.addWidget(widthLabel)
        widthLayout.addStretch()
        self.mediaWidthSpin = SpinBox(self)
        self.mediaWidthSpin.setRange(200, 800)
        self.mediaWidthSpin.setValue(cfg.mediaWidth.value)
        self.mediaWidthSpin.setFixedWidth(120)
        self.mediaWidthSpin.valueChanged.connect(self._onMediaWidthChanged)
        widthLayout.addWidget(self.mediaWidthSpin)
        layout.addLayout(widthLayout)

        lyricsAdvanceLayout = QHBoxLayout()
        lyricsAdvanceLabel = BodyLabel(tr("home.lyrics_advance"), self)
        lyricsAdvanceLabel.setFixedWidth(100)
        lyricsAdvanceLayout.addWidget(lyricsAdvanceLabel)
        lyricsAdvanceLayout.addStretch()
        self.mediaLyricsAdvanceSpin = SpinBox(self)
        self.mediaLyricsAdvanceSpin.setRange(0, 2000)
        self.mediaLyricsAdvanceSpin.setValue(cfg.mediaLyricsAdvance.value)
        self.mediaLyricsAdvanceSpin.setFixedWidth(120)
        self.mediaLyricsAdvanceSpin.valueChanged.connect(self._onMediaLyricsAdvanceChanged)
        lyricsAdvanceLayout.addWidget(self.mediaLyricsAdvanceSpin)
        layout.addLayout(lyricsAdvanceLayout)

    def _updateShowMediaInfoSwitch(self, value):
        self.showMediaInfoSwitch.setChecked(value)
        self._updateMediaSettingsEnabled(value)

    def _updateShowMediaCoverSwitch(self, value):
        self.showMediaCoverSwitch.setChecked(value)

    def _updateMediaWidthSpin(self, value):
        self.mediaWidthSpin.setValue(value)

    def _updateMediaLyricsAdvanceSpin(self, value):
        self.mediaLyricsAdvanceSpin.setValue(value)

    def _onShowMediaInfoChanged(self, checked: bool):
        cfg.showMediaInfo.value = checked
        self._updateMediaSettingsEnabled(checked)
        logger.info(f"媒体设置：启用媒体信息={'开启' if checked else '关闭'}")

    def _onShowMediaCoverChanged(self, checked: bool):
        cfg.showMediaCover.value = checked
        logger.info(f"媒体设置：显示封面={'开启' if checked else '关闭'}")

    def _onMediaWidthChanged(self, value: int):
        cfg.mediaWidth.value = value
        logger.info(f"媒体设置：组件宽度={value}px")

    def _onMediaLyricsAdvanceChanged(self, value: int):
        cfg.mediaLyricsAdvance.value = value
        logger.info(f"媒体设置：歌词提前时间={value}ms")


class CountdownEditDialog(MessageBoxBase):
    """倒计时编辑对话框"""

    def __init__(self, parent=None, countdown_data=None):
        super().__init__(parent)
        self._countdown_data = countdown_data
        self._result = None
        self._init_ui()

    def _init_ui(self):

        self.viewLayout.setSpacing(8)

        title = SubtitleLabel(tr("home.edit_countdown") if self._countdown_data else tr("home.add_countdown"))
        self.viewLayout.addWidget(title)
        infoLabel = BodyLabel(tr("home.countdown_description"))
        self.viewLayout.addWidget(infoLabel)

        titleLabel = BodyLabel(tr("home.target_name"))
        self.viewLayout.addWidget(titleLabel)
        self.titleEdit = LineEdit()
        self.titleEdit.setPlaceholderText(tr("home.target_name_example"))
        if self._countdown_data:
            self.titleEdit.setText(self._countdown_data.get('title', ''))
        self.viewLayout.addWidget(self.titleEdit)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.viewLayout.addWidget(spacer)

        dateLabel = BodyLabel(tr("home.target_date"))
        self.viewLayout.addWidget(dateLabel)
        self.datePicker = CalendarPicker()
        if self._countdown_data:
            target_time = self._countdown_data.get('target_time', '')
            if target_time:
                try:
                    dt = datetime.datetime.strptime(target_time, '%Y-%m-%d %H:%M')
                    self.datePicker.setDate(QDate(dt.year, dt.month, dt.day))
                except Exception:
                    pass
        else:
            now = datetime.datetime.now()
            self.datePicker.setDate(QDate(now.year, now.month, now.day))
        self.viewLayout.addWidget(self.datePicker)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.viewLayout.addWidget(spacer)

        timeLabel = BodyLabel(tr("home.target_time"))
        self.viewLayout.addWidget(timeLabel)
        self.timePicker = TimePicker()
        if self._countdown_data:
            target_time = self._countdown_data.get('target_time', '')
            if target_time:
                try:
                    dt = datetime.datetime.strptime(target_time, '%Y-%m-%d %H:%M')
                    self.timePicker.setTime(QTime(dt.hour, dt.minute))
                except Exception:
                    pass
        else:
            self.timePicker.setTime(QTime(0, 0))
        self.viewLayout.addWidget(self.timePicker)

        self.yesButton.setText(tr("common.confirm"))
        self.cancelButton.setText(tr("common.cancel"))

        self.widget.setMinimumWidth(360)

        try:
            self.yesButton.clicked.disconnect()
        except TypeError:
            pass
        self.yesButton.clicked.connect(self._on_ok)

    def _on_ok(self):
        try:
            title_text = self.titleEdit.text().strip()
            if not title_text:
                InfoBar.error(tr("common.error"), tr("home.enter_target_name"), parent=self, duration=3000)
                return

            qdate = self.datePicker.date
            qtime = self.timePicker.time
            if not qdate.isValid() or not qtime.isValid():
                InfoBar.error(tr("common.error"), tr("home.enter_valid_datetime"), parent=self, duration=3000)
                return
            dt = datetime.datetime(qdate.year(), qdate.month(), qdate.day(), qtime.hour(), qtime.minute())
            self._result = {
                'title': title_text,
                'target_time': dt.strftime('%Y-%m-%d %H:%M')
            }
            self.accept()
        except Exception as e:
            logger.error(f'保存倒计时失败：{e}')
            InfoBar.error(tr("common.error"), tr("home.enter_valid_datetime_error", error=str(e)), parent=self, duration=5000)

    def get_countdown(self):
        return self._result


class QuickLaunchEditDialog(MessageBoxBase):
    """快捷启动栏编辑对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        apps = cfg.quickLaunchApps.value
        self._apps = list(apps) if apps else []
        self._deleted_apps = []  # 记录要删除的列表 确认后再删图标
        self._init_ui()

    def _init_ui(self):
        self.viewLayout.setSpacing(8)
        title = SubtitleLabel(tr("home.edit_quick_launch"))
        self.viewLayout.addWidget(title)
        infoLabel = BodyLabel(tr("home.quick_launch_description"))
        self.viewLayout.addWidget(infoLabel)

        self.appListWidget = ListWidget(self)
        self.appListWidget.setFixedHeight(200)
        self.appListWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.appListWidget.itemClicked.connect(self._on_item_clicked)
        self._update_app_list()
        self.viewLayout.addWidget(self.appListWidget)

        buttonLayout = QHBoxLayout()
        self.addButton = PushButton(tr("home.add_app"), self)
        self.addButton.clicked.connect(self._on_add_app)
        buttonLayout.addWidget(self.addButton)

        self.editButton = PushButton(tr("home.edit"), self)
        self.editButton.clicked.connect(self._on_edit_app)
        buttonLayout.addWidget(self.editButton)

        self.deleteButton = PushButton(tr("home.delete"), self)
        self.deleteButton.clicked.connect(self._on_delete_app)
        buttonLayout.addWidget(self.deleteButton)

        self.viewLayout.addLayout(buttonLayout)

        self.yesButton.setText(tr("common.done"))
        self.cancelButton.setText(tr("common.cancel"))
        self.widget.setMinimumWidth(400)

        self._selected_row = -1
        self.setAcceptDrops(True)

    def _on_item_clicked(self, item):
        self._selected_row = self.appListWidget.row(item)

    def _update_app_list(self):
        self.appListWidget.clear()
        for app in self._apps:
            name = app.get('name', tr("common.unknown"))
            path = app.get('path', '')
            display_text = f"{name} - {path if path else tr('home.no_path_configured')}"
            self.appListWidget.addItem(display_text)

    def _on_add_app(self):
        if len(self._apps) >= QuickLaunchDock.MAX_APPS:
            InfoBar.warning(tr("common.tip"), tr("home.max_apps_warning", max=QuickLaunchDock.MAX_APPS), parent=self, duration=3000)
            return
        dialog = AppEditDialog(self.parent())
        if dialog.exec():
            app_data = dialog.get_app_data()
            if app_data:
                self._apps.append(app_data)
                self._update_app_list()
                self._refresh_dock()

    def _on_edit_app(self):
        if self._selected_row < 0 or self._selected_row >= len(self._apps):
            InfoBar.warning(tr("common.tip"), tr("home.select_app_first"), parent=self, duration=2000)
            return

        dialog = AppEditDialog(self.parent(), self._apps[self._selected_row])
        if dialog.exec():
            app_data = dialog.get_app_data()
            if app_data:
                self._apps[self._selected_row] = app_data
                self._update_app_list()
                if 0 <= self._selected_row < self.appListWidget.count():
                    self.appListWidget.setCurrentRow(self._selected_row)
                self._refresh_dock()

    def _on_delete_app(self):
        if self._selected_row < 0 or self._selected_row >= len(self._apps):
            InfoBar.warning(tr("common.tip"), tr("home.select_app_first"), parent=self, duration=2000)
            return

        deleted_app = self._apps.pop(self._selected_row)
        self._deleted_apps.append(deleted_app)
        self._update_app_list()
        if self.appListWidget.count() > 0:
            new_row = min(self._selected_row, self.appListWidget.count() - 1)
            self.appListWidget.setCurrentRow(new_row)
            self._selected_row = new_row

    def _delete_app_icon(self, app_data):
        if not app_data:return
        icon_filename = app_data.get('icon', '')
        if not icon_filename or icon_filename in ('exe.ico', 'default.ico'):return

        icon_path = os.path.join(PACKAGE_ROOT, 'data', 'icon', icon_filename)
        if os.path.exists(icon_path):
            try:
                os.remove(icon_path)
                logger.info(f"已删除图标文件：{icon_path}")
            except Exception as e:
                logger.warning(f"删除图标文件失败：{e}")

    def _refresh_dock(self):
        """刷新 dock 栏显示"""
        if hasattr(self, 'mainWindow'):
            self.mainWindow.refresh_quick_launch()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            urls = e.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                if path and (path.lower().endswith('.exe') or path.lower().endswith('.lnk')):
                    e.acceptProposedAction()
                    return
        e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        e.acceptProposedAction()
        urls = e.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if not path:
                continue
            if not (path.lower().endswith('.exe') or path.lower().endswith('.lnk')):
                continue
            if len(self._apps) >= QuickLaunchDock.MAX_APPS:
                InfoBar.warning(tr("common.tip"), tr("home.max_apps_warning", max=QuickLaunchDock.MAX_APPS), parent=self, duration=3000)
                return
            app_data = resolve_app_from_path(path)
            if app_data:
                self._apps.append(app_data)
                self._update_app_list()
                self._refresh_dock()

    def accept(self):
        cfg.quickLaunchApps.value = self._apps
        save_cfg()
        for deleted_app in self._deleted_apps:
            self._delete_app_icon(deleted_app)
        self._refresh_dock()
        super().accept()

    def get_apps(self):
        return self._apps


class AppEditDialog(MessageBoxBase):
    """应用编辑对话框"""

    def __init__(self, parent=None, app_data=None):
        super().__init__(parent)
        self._app_data = app_data
        self._result = None
        self._init_ui()

    def _init_ui(self):
        self.viewLayout.setSpacing(8)

        title = SubtitleLabel(tr("home.edit_app") if self._app_data else tr("home.add_app"))
        self.viewLayout.addWidget(title)

        descLabel = BodyLabel(tr("home.app_config_description"))
        self.viewLayout.addWidget(descLabel)

        nameLabel = BodyLabel(tr("home.app_name"))
        self.viewLayout.addWidget(nameLabel)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText(tr("home.app_name_example"))
        if self._app_data:self.nameEdit.setText(self._app_data.get('name', ''))
        self.viewLayout.addWidget(self.nameEdit)
        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.viewLayout.addWidget(spacer)

        pathLabel = BodyLabel(tr("home.app_path"))
        self.viewLayout.addWidget(pathLabel)
        pathLayout = QHBoxLayout()
        self.pathEdit = LineEdit(self)
        self.pathEdit.setPlaceholderText(tr("home.app_path_example"))
        if self._app_data:self.pathEdit.setText(self._app_data.get('path', ''))
        self.pathEdit.textChanged.connect(self._on_path_changed)
        pathLayout.addWidget(self.pathEdit)
        self.browseButton = PushButton(tr("common.browse"), self)
        self.browseButton.clicked.connect(self._on_browse)
        pathLayout.addWidget(self.browseButton)
        self.viewLayout.addLayout(pathLayout)
        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.viewLayout.addWidget(spacer)

        iconPathLabel = BodyLabel(tr("home.icon_path"))
        self.viewLayout.addWidget(iconPathLabel)
        iconInputLayout = QHBoxLayout()
        self.iconPreviewLabel = QLabel(self)
        self.iconPreviewLabel.setObjectName("iconPreviewLabel")
        self.iconPreviewLabel.setFixedSize(48, 48)
        self.iconPreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_default_icon()
        iconInputLayout.addWidget(self.iconPreviewLabel)
        self.iconPathEdit = LineEdit(self)
        self.iconPathEdit.setPlaceholderText(tr("home.icon_path_placeholder"))
        if self._app_data:self.iconPathEdit.setText(self._app_data.get('icon', ''))
        self.iconPathEdit.textChanged.connect(self._on_icon_path_changed)
        iconInputLayout.addWidget(self.iconPathEdit)
        self.iconBrowseButton = PushButton(tr("common.browse"), self)
        self.iconBrowseButton.clicked.connect(self._on_icon_browse)
        iconInputLayout.addWidget(self.iconBrowseButton)
        self.viewLayout.addLayout(iconInputLayout)

        self.yesButton.setText(tr("common.confirm"))
        self.cancelButton.setText(tr("common.cancel"))
        self.widget.setMinimumWidth(400)

        try:
            self.yesButton.clicked.disconnect()
        except TypeError:
            pass
        self.yesButton.clicked.connect(self._on_ok)

        self._icon_filename = self._app_data.get('icon', '') if self._app_data else ''
        if self._icon_filename:
            self._load_icon_preview(self._icon_filename)

    def _set_default_icon(self):
        default_icon = QIcon.fromTheme('application-x-executable')
        if default_icon.isNull():
            pixmap = QPixmap(48, 48)
            pixmap.fill(QColor(100, 100, 100))
            self.iconPreviewLabel.setPixmap(pixmap)
        else:
            self.iconPreviewLabel.setPixmap(default_icon.pixmap(48, 48))

    def _load_icon_preview(self, icon_filename):
        icon_path = get_software_icon_path(icon_filename)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.iconPreviewLabel.setPixmap(scaled)
            else:
                self._set_default_icon()
        else:
            self._set_default_icon()

    def _extract_icon(self, exe_path):
        try:
            provider = QFileIconProvider()
            fi = QFileInfo(exe_path)
            icon = provider.icon(fi)

            sizes = icon.availableSizes()
            if not sizes:
                return 'exe.ico'

            best_size = max(sizes, key=lambda s: s.width() * s.height())
            pixmap = icon.pixmap(best_size)

            if pixmap.isNull():
                return 'exe.ico'

            target_size = 256
            if pixmap.width() < target_size:
                pixmap = pixmap.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            icon_filename = self._get_icon_name()
            icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ql_icon')
            os.makedirs(icon_dir, exist_ok=True)
            icon_save_path = os.path.join(icon_dir, icon_filename)
            pixmap.save(icon_save_path, 'PNG')

            return icon_filename
        except Exception as e:
            logger.error(f"提取图标失败：{e}")
            return 'exe.ico'

    def _get_icon_name(self):
        name_text = self.nameEdit.text().strip()
        if name_text:
            cleaned_name = re.sub(r'[^\w\u4e00-\u9fff]', '', name_text)
            if cleaned_name:
                return cleaned_name + '.ico'
        return 'default.ico'

    def _on_path_changed(self, path):
        if path.lower().endswith('.exe') and os.path.exists(path):
            base_name = os.path.splitext(os.path.basename(path))[0]
            self.nameEdit.setText(base_name)
            self._do_extract_icon(path)

    def _do_extract_icon(self, exe_path):
        icon_path = self._extract_icon(exe_path)
        if icon_path:
            self._icon_filename = icon_path
            self.iconPathEdit.setText('')
            self._load_icon_preview(icon_path)

    def _on_icon_path_changed(self, path):
        if path:
            self._icon_filename = path
            self._load_icon_preview(path)

    def _on_icon_browse(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择图标',
            '',
            'Image Files (*.ico *.png *.jpg *.jpeg *.bmp);;All Files (*)'
        )

        if file_path:
            self.iconPathEdit.setText(file_path)

    def _on_browse(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择应用程序',
            '',
            'Executable Files (*.exe);;All Files (*)'
        )

        if file_path:
            self.pathEdit.setText(file_path)

    def _on_ok(self):
        name_text = self.nameEdit.text().strip()
        if not name_text:
            InfoBar.error(tr("dialog.error"), tr("home.enter_target_name"), parent=self, duration=2000)
            return

        path_text = self.pathEdit.text().strip()
        icon_text = self.iconPathEdit.text().strip()

        if icon_text:
            icon_val = icon_text
        elif self._icon_filename:
            icon_val = self._icon_filename
        else:
            icon_val = self._get_icon_name()

        self._result = {
            'name': name_text,
            'path': path_text,
            'icon': icon_val
        }
        self.accept()

    def get_app_data(self):
        return self._result



class _GridOverlay(QWidget):
    """网格覆盖层"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._home = None
        self._grid_metrics = None
        self._preview_visible = False
        # 格子坐标（旧）
        self._preview_row = -1
        self._preview_col = -1
        self._preview_width_cells = 0
        self._preview_height_cells = 0
        # 像素坐标
        self._preview_x = 0
        self._preview_y = 0
        self._preview_width_px = 0
        self._preview_height_px = 0
        self._use_pixel_mode = False  # 是否使用
        self._preview_collision = False
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parent().rect())
            if self._home:
                self._home._update_grid_metrics()
                self._grid_metrics = self._home._grid_metrics
                self.update()
        return super().eventFilter(obj, event)

    def setup(self, home_interface):
        """设置 HomeInterface 引用"""
        self._home = home_interface

    def update_grid_metrics(self, metrics):
        """更新网格度量并重绘"""
        self._grid_metrics = metrics
        if metrics:
            self.setGeometry(self.parent().rect())
        self.update()

    def show_preview(self, visible: bool):
        """显示/隐藏预览框"""
        self._preview_visible = visible
        if not visible:
            self._preview_row = -1
            self._preview_col = -1
            self._preview_x = 0
            self._preview_y = 0
        self.update()

    def update_preview_pixel(self, x: float, y: float, width: float, height: float, collision=False):
        self._preview_visible = True
        self._use_pixel_mode = True
        self._preview_x = x
        self._preview_y = y
        self._preview_width_px = width
        self._preview_height_px = height
        self._preview_collision = collision
        self.update()

    def paintEvent(self, event):
        """绘制网格和预览框"""
        if not self._grid_metrics or self._grid_metrics.cell_size <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        metrics = self._grid_metrics
        inset = metrics.edge_inset_px
        pitch = metrics.pitch
        cell_size = metrics.cell_size

        # 网格线样式
        dash_segment = max(2, cell_size * 0.25)
        grid_color = QColor(200, 200, 200, 220)  # 更清晰的灰色
        grid_pen = QPen(grid_color)
        grid_pen.setWidthF(1.0)
        grid_pen.setDashPattern([dash_segment, dash_segment])  # 自适应虚线
        painter.setPen(grid_pen)

        # 计算可用区域右/下边缘
        cw = self.width()
        ch = self.height()
        right_edge = cw - inset
        bottom_edge = ch - inset

        # 竖直线：从 inset 开始，每隔 pitch 画一条，直到超出右边缘
        col = 0
        while True:
            x = inset + col * pitch
            if x > right_edge:
                break
            painter.drawLine(int(x), int(inset), int(x), int(bottom_edge))
            col += 1
        # 右边缘闭合线
        painter.drawLine(int(right_edge), int(inset), int(right_edge), int(bottom_edge))

        # 水平线：从 inset 开始，每隔 pitch 画一条，直到超出下边缘
        row = 0
        while True:
            y = inset + row * pitch
            if y > bottom_edge:
                break
            painter.drawLine(int(inset), int(y), int(right_edge), int(y))
            row += 1
        # 下边缘闭合线
        painter.drawLine(int(inset), int(bottom_edge), int(right_edge), int(bottom_edge))

        # 绘制预览框
        if self._preview_visible:
            if self._use_pixel_mode:
                # 像素模式 使用像素坐标
                rect = QRectF(
                    self._preview_x,
                    self._preview_y,
                    self._preview_width_px,
                    self._preview_height_px
                )
            elif self._preview_row >= 0 and self._preview_col >= 0 and self._home:
                # 格子模式 使用格子坐标
                rect = self._home.grid_service.get_cell_rect(
                    metrics,
                    self._preview_col,
                    self._preview_row,
                    max(1, self._preview_width_cells),
                    max(1, self._preview_height_cells)
                )
                rect = QRectF(rect)
            else:
                rect = None

            if rect:
                # 颜色
                if self._preview_collision:
                    # 红色 - 碰撞/无效
                    border_color = QColor(255, 59, 48, 255)  # #FF3B30
                    fill_color = QColor(255, 59, 48, 100)    # 明显的红色填充
                else:
                    # 蓝色 - 正常
                    border_color = QColor(10, 132, 255, 255)  # #FF0A84FF
                    fill_color = QColor(10, 132, 255, 100)    # 明显的蓝色填充

                # 圆角动态计算
                min_side = min(rect.width(), rect.height())
                corner_radius = max(14, min(26, min_side * 0.11))

                # 绘制填充
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(fill_color)
                path = QPainterPath()
                path.addRoundedRect(rect, corner_radius, corner_radius)
                painter.drawPath(path)

                # 绘制边框
                border_pen = QPen(border_color)
                border_pen.setWidthF(2)
                painter.setPen(border_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(rect, corner_radius, corner_radius)

        painter.end()
