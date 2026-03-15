from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QFileDialog, QGraphicsBlurEffect,QStackedLayout
from PyQt5.QtCore import QTimer, Qt, QTime, QDate
from PyQt5.QtCore import QLocale, QTranslator, QUrl
from PyQt5.QtGui import QFontDatabase, QFont, QIcon, QPixmap, QImage, QPainter, QColor
from qfluentwidgets import (
    setTheme, Theme, FluentWindow, FluentTranslator,
    FluentIcon as FIF, NavigationItemPosition, RoundMenu, Action, MessageBox, ScrollArea, SmoothScrollArea, ExpandLayout, isDarkTheme,
    PushButton, CardWidget, ProgressBar, InfoBar, ImageLabel
)
import requests
import sys
import os
import platform
import ctypes
import json
from setting import SettingInterface
import shutil
from config import cfg
from logger import logger
from version import VERSION, BUILD_DATE
from constants import APP_NAME
import datetime
import cnlunar
def check_single_instance():
    """ 检查是否已经有实例 """
    config_path = 'config/config.json'
    allow_multiple = False
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if 'Other' in config and 'AllowMultipleInstances' in config['Other']:
                allow_multiple = config['Other']['AllowMultipleInstances']
        except Exception:
            pass
    
    if not allow_multiple:
        # 创建互斥体
        mutex_name = f"Global\\{APP_NAME}_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False
    return True

# 路径设置
if getattr(sys, 'frozen', False):
    # 打包为exe时
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    MEIPASS_DIR = sys._MEIPASS
else:
    # 脚本运行时
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEIPASS_DIR = None

def get_resource_path(relative_path):
    """获取绝对路径"""
    if MEIPASS_DIR:
        return os.path.join(MEIPASS_DIR, relative_path)
    return os.path.join(BASE_DIR, relative_path)


class TitleInterface(ScrollArea):
    """ 标题界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.scrollWidget)

        self.titleLabel = QLabel("标题", self)
        self.contentLabel = QLabel("这是一个标题页面，用于展示标题相关内容。", self)
        self.contentLabel.setAlignment(Qt.AlignCenter)
        self.contentLabel.setWordWrap(True)

        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面 """
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, -40, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.__setQss()
        self.__initLayout()

    def __initLayout(self):
        """ 初始化布局 """
        # 标题
        self.titleLabel.move(60, 63)

        # 主布局
        self.mainLayout.setSpacing(20)
        self.mainLayout.setContentsMargins(60, 160, 60, 0)
        self.mainLayout.addWidget(self.contentLabel)

    def __setQss(self):
        """ 设置样式表 """
        self.scrollWidget.setObjectName('scrollWidget')
        self.titleLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = get_resource_path(os.path.join('resource', 'qss', theme, 'setting_interface.qss'))
            with open(qss_path, encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

class WallpaperInterface(ScrollArea):
    """ 壁纸界面 """

    def __init__(self, mainWindow=None, parent=None):
        super().__init__(parent=parent)
        self.mainWindow = mainWindow
        self.scrollWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.scrollWidget)

        self.wallpaperLabel = QLabel("壁纸", self)
        self.scrollArea = SmoothScrollArea()
        self.imageLabel = ImageLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.scrollArea.setWidget(self.imageLabel)
        # 滚动区域的属性
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.getButton = PushButton(FIF.DOWNLOAD, "获取壁纸")
        self.getButton.setFixedHeight(50)
        self.getButton.setFixedWidth(200)
        
        # 按钮
        self.saveButton = PushButton(FIF.SAVE, "另存壁纸")
        self.saveButton.setFixedHeight(50)
        self.saveButton.setFixedWidth(200)
        
        self.selectButton = PushButton(FIF.FOLDER, "手动选择")
        self.selectButton.setFixedHeight(50)
        self.selectButton.setFixedWidth(200)
        
        self.setWallpaperButton = PushButton(FIF.HOME, "设为桌面")
        self.setWallpaperButton.setFixedHeight(50)
        self.setWallpaperButton.setFixedWidth(200)
        
        self.current_pixmap = None
        self.current_wallpaper_path = None
        self.last_sync_path = None
        self.autoGetTimer = QTimer(self)
        self.autoGetTimer.timeout.connect(self.__getWallpaper)
        self.autoSyncCheckTimer = QTimer(self)
        self.autoSyncCheckTimer.timeout.connect(self.__checkAutoSync)

        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面 """
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, -40, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.__setQss()
        self.__initLayout()
        self.__connectSignalToSlot()
        
        # 程序运行时自动获取壁纸
        self.__getWallpaper()

    def __initLayout(self):
        """ 初始化布局 """
        # 标题
        self.wallpaperLabel.move(60, 63)

        # 按钮水平布局
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.getButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.selectButton)
        buttonLayout.addSpacing(10)
        buttonLayout.addWidget(self.setWallpaperButton)
        
        # 主布局
        self.mainLayout.setSpacing(20)
        self.mainLayout.setContentsMargins(60, 160, 60, 0) 
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addLayout(buttonLayout)

    def __setQss(self):
        """ 设置样式表 """
        self.scrollWidget.setObjectName('scrollWidget')
        self.wallpaperLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = get_resource_path(os.path.join('resource', 'qss', theme, 'setting_interface.qss'))
            with open(qss_path, encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

    def __connectSignalToSlot(self):
        """ 连接信号与槽 """
        self.getButton.clicked.connect(self.__getWallpaper)
        self.saveButton.clicked.connect(self.__saveWallpaper)
        self.selectButton.clicked.connect(self.__selectWallpaper)
        self.setWallpaperButton.clicked.connect(self.__setWallpaper)
        
        # 连接配置变更信号
        cfg.autoGetInterval.valueChanged.connect(self.__updateAutoGetTimer)
        cfg.autoSyncToDesktop.valueChanged.connect(self.__updateAutoSyncCheckTimer)
        cfg.backgroundBlurRadius.valueChanged.connect(self.__updateBackgroundBlur)
        
        # 初始更新定时器
        self.__updateAutoGetTimer()
        self.__updateAutoSyncCheckTimer()

    def __updateAutoGetTimer(self):
        """ 更新自动获取壁纸的定时器 """
        # 停止当前定时器
        self.autoGetTimer.stop()
        
        # 获取时间间隔
        interval_str = cfg.autoGetInterval.value
        
        if interval_str != "从不":
            if interval_str == "10分钟":
                interval = 10 * 60 * 1000
            elif interval_str == "30分钟":
                interval = 30 * 60 * 1000
            elif interval_str == "1小时":
                interval = 60 * 60 * 1000
            elif interval_str == "3小时":
                interval = 3 * 60 * 60 * 1000
            elif interval_str == "6小时":
                interval = 6 * 60 * 60 * 1000
            elif interval_str == "12小时":
                interval = 12 * 60 * 60 * 1000
            elif interval_str == "1天":
                interval = 24 * 60 * 60 * 1000
            elif interval_str == "3天":
                interval = 3 * 24 * 60 * 60 * 1000
            elif interval_str == "5天":
                interval = 5 * 24 * 60 * 60 * 1000
            elif interval_str == "7天":
                interval = 7 * 24 * 60 * 60 * 1000
            else:
                interval = 30 * 60 * 1000
            
            # 启动定时器
            self.autoGetTimer.start(interval)
    
    def __checkAutoSync(self):
        """ 检测自动同步至桌面是否启用 """
        if cfg.autoSyncToDesktop.value and self.current_wallpaper_path is not None:
            # 壁纸路径发生变化时重新设置
            if self.last_sync_path != self.current_wallpaper_path:
                self.__setWallpaper(show_notification=False)
                self.last_sync_path = self.current_wallpaper_path
    
    def __updateAutoSyncCheckTimer(self):
        """ 更新自动同步检测定时器 """
        # 停止当前定时器
        self.autoSyncCheckTimer.stop()
        
        if cfg.autoSyncToDesktop.value:
            self.autoSyncCheckTimer.start(5000)  # 5 秒
    
    def __updateBackgroundBlur(self):
        """ 更新背景模糊强度 """
        if hasattr(self, 'mainWindow') and self.mainWindow and hasattr(self.mainWindow, 'homeBackgroundImage'):
            if self.mainWindow.originalPixmap is not None and not self.mainWindow.originalPixmap.isNull():
                self.mainWindow.resizeEvent(None)

    def resizeEvent(self, event):
        """ 窗口大小变化时调整滚动区域大小 """
        super().resizeEvent(event)
        
        # 计算滚动区域的尺寸
        margin = 60
        available_width = self.width() - margin * 2
        available_height = self.height() - 240
        
        scroll_width = available_width
        # 限制滚动区域的高度
        scroll_height = min(int(scroll_width * 0.5), available_height)
        
        # 设置滚动区域的大小
        self.scrollArea.setFixedSize(scroll_width, scroll_height)

    def __getWallpaper(self):
        """ 获取壁纸 """
        try:
            url = "https://wp.upx8.com/api.php?content=风景"
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                # 保存文件
                wallpaper_dir = os.path.join(BASE_DIR, 'wallpaper')
                if not os.path.exists(wallpaper_dir):
                    os.makedirs(wallpaper_dir)
                
                current_date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                wallpaper_path = os.path.join(wallpaper_dir, f'wallpaper_{current_date}.jpg')
                
                with open(wallpaper_path, 'wb') as f:
                    f.write(response.content)
                
                # 管理壁纸保存量
                save_limit = cfg.wallpaperSaveLimit.value
                self.__manageWallpaperLimit(wallpaper_dir, save_limit)
                
                self.current_pixmap = QPixmap(wallpaper_path)
                self.current_wallpaper_path = wallpaper_path
                if not self.current_pixmap.isNull():
                    self.imageLabel.setPixmap(self.current_pixmap)
                    # 更新主界面的背景照片
                    if self.mainWindow and hasattr(self.mainWindow, 'homeBackgroundImage'):
                        self.mainWindow.originalPixmap = self.current_pixmap
                        available_width = self.mainWindow.width() - 50
                        available_height = self.mainWindow.height()
                        scaled_pixmap = self.current_pixmap.scaled(available_width, available_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        self.mainWindow.homeBackgroundImage.setPixmap(scaled_pixmap)
                        QApplication.processEvents()
                
                InfoBar.success(
                    "成功",
                    f"壁纸已下载到: {wallpaper_path}",
                    duration=5000,
                    parent=self
                )
                
                if cfg.autoSyncToDesktop.value:
                    self.__setWallpaper(show_notification=True)
                    self.last_sync_path = wallpaper_path
            else:
                InfoBar.error(
                    "错误",
                    f"获取壁纸失败，状态码: {response.status_code}",
                    duration=5000,
                    parent=self
                )
        except Exception as e:
            InfoBar.error(
                "错误",
                f"获取壁纸失败: {str(e)}",
                duration=5000,
                parent=self
            )
    
    def __saveWallpaper(self):
        """ 另存壁纸 """
        if self.current_pixmap is None:
            InfoBar.warning(
                "提示",
                "请先获取壁纸",
                duration=5000,
                parent=self
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "另存壁纸", 
            os.path.join(BASE_DIR, "wallpaper"), 
            "JPEG图片 (*.jpg);;PNG图片 (*.png)"
        )
        
        if file_path:
            try:
                self.current_pixmap.save(file_path)
                InfoBar.success(
                    "成功",
                    f"壁纸已保存到: {file_path}",
                    duration=5000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    "错误",
                    f"保存壁纸失败: {str(e)}",
                    duration=5000,
                    parent=self
                )
    
    def __selectWallpaper(self):
        """ 手动选择壁纸 """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择壁纸", 
            os.path.join(BASE_DIR, "wallpaper"), 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        
        if file_path:
            try:
                self.current_pixmap = QPixmap(file_path)
                self.current_wallpaper_path = file_path
                if not self.current_pixmap.isNull():
                    self.imageLabel.setPixmap(self.current_pixmap)
                    # 更新主界面的背景照片
                    if self.mainWindow and hasattr(self.mainWindow, 'homeBackgroundImage'):
                        self.mainWindow.originalPixmap = self.current_pixmap
                        available_width = self.mainWindow.width() - 50
                        available_height = self.mainWindow.height()
                        scaled_pixmap = self.current_pixmap.scaled(available_width, available_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        self.mainWindow.homeBackgroundImage.setPixmap(scaled_pixmap)
                        QApplication.processEvents()
                
                InfoBar.success(
                    "成功",
                    f"已选择壁纸：{file_path}",
                    duration=5000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    "错误",
                    f"选择壁纸失败: {str(e)}",
                    duration=5000,
                    parent=self
                )
    
    def __manageWallpaperLimit(self, wallpaper_dir, save_limit):
        """ 管理壁纸保存量，超过限制时删除最旧的壁纸 """
        wallpapers = []
        for file in os.listdir(wallpaper_dir):
            if file.endswith('.jpg') and file.startswith('wallpaper_'):
                file_path = os.path.join(wallpaper_dir, file)
                mtime = os.path.getmtime(file_path)
                wallpapers.append((mtime, file_path))
        
        wallpapers.sort(key=lambda x: x[0])
        
        # 删除超过限制的最旧壁纸
        while len(wallpapers) > save_limit:
            _, file_path = wallpapers.pop(0)
            try:
                os.remove(file_path)
            except Exception:
                pass
    
    def __setWallpaper(self, show_notification=True):
        """ 设为桌面壁纸 """
        if self.current_wallpaper_path is None:
            if show_notification:
                InfoBar.warning(
                    "提示",
                    "请先获取或选择壁纸",
                    duration=5000,
                    parent=self
                )
            return
        
        try:
            # 使用ctypes设置桌面壁纸
            SPI_SETDESKWALLPAPER = 20
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDWININICHANGE = 0x02
            
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 
                0, 
                self.current_wallpaper_path, 
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )
            

            self.last_sync_path = self.current_wallpaper_path
            
            if show_notification:
                InfoBar.success(
                    "成功",
                    "壁纸已设置为桌面背景",
                    duration=5000,
                    parent=self
                )
        except Exception as e:
            if show_notification:
                InfoBar.error(
                    "错误",
                    f"设置壁纸失败: {str(e)}",
                    duration=5000,
                    parent=self
                )

class MainWindow(FluentWindow):
    """ 主窗口 """

    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)
        
        # 设置窗口图标
        icon_path = get_resource_path(os.path.join("resource", "icons", "CY.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.initMainNavigation()
        self.initSettingsNavigation()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 700)
        self.setMinimumSize(400, 300)
        self.moveToCenter()
        
        # 初始化系统托盘
        self.initSystemTray()
        
        # 时钟更新定时器
        self.clockTimer = QTimer(self)
        self.clockTimer.timeout.connect(self.__updateClock)
        self.clockTimer.start(1000)
        cfg.showClockSeconds.valueChanged.connect(self.__updateClock)
        cfg.showLunarCalendar.valueChanged.connect(self.__updateClock)
        cfg.clockColor.valueChanged.connect(self.updateClockStyle)
        self.__updateClock()
        
        # 诗词更新定时器
        self.poetryTimer = QTimer(self)
        self.poetryTimer.timeout.connect(self.__updatePoetry)
        cfg.showPoetry.valueChanged.connect(self.__updatePoetry)
        cfg.poetryApiUrl.valueChanged.connect(self.__updatePoetry)
        cfg.poetryUpdateInterval.valueChanged.connect(self.__updatePoetryInterval)
        self.__updatePoetryInterval()
    
    def initSystemTray(self):
        """ 初始化系统托盘 """
        icon_path = get_resource_path(os.path.join("resource", "icons", "CY.png"))
        if os.path.exists(icon_path):
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        else:
            self.tray_icon = QSystemTrayIcon(self)
        
        self.tray_menu = RoundMenu(APP_NAME, self)
        
        show_action = Action(FIF.HOME, "显示主窗口", self)
        show_action.triggered.connect(self.show)
        self.tray_menu.addAction(show_action)
        
        exit_action = Action(FIF.CLOSE, "退出", self)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        self.tray_icon.activated.connect(self.__onTrayIconActivated)
        
        self.tray_icon.show()
    
    def __onTrayIconActivated(self, reason):
        """ 托盘图标激活槽函数 """
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    
    def closeEvent(self, event):
        """ 关闭事件处理 """
        if cfg.closeAction.value == "minimize":
            # 最小化到托盘
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                APP_NAME,
                "应用已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # 退出应用
            QApplication.quit()

    def initMainNavigation(self):
        """ 初始化主界面导航 """
        home = QWidget()
        home.setObjectName("home")
        
        # 创建主界面的照片显示控件
        self.homeBackgroundImage = QLabel()
        self.homeBackgroundImage.setAlignment(Qt.AlignCenter)
        self.originalPixmap = None  # 保存原始图片
        
        # 时钟和日期标签
        self.clockLabel = QLabel("00:00:00")
        self.clockLabel.setAlignment(Qt.AlignCenter)
        
        self.dateLabel = QLabel("")
        self.dateLabel.setAlignment(Qt.AlignCenter)
        
        # 诗词标签
        self.poetryLabel = QLabel("")
        self.poetryLabel.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.poetryLabel.setStyleSheet("""
            color: #FFFFFF; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei';
            background-color: transparent;
        """)
        self.poetryLabel.setWordWrap(False)
        
        self.updateClockStyle()
        
        # 时钟容器
        clockContainer = QWidget()
        clockLayout = QVBoxLayout(clockContainer)
        clockLayout.setAlignment(Qt.AlignTop)
        clockLayout.setContentsMargins(0, 100, 0, 0)
        clockLayout.setSpacing(0)  # 时钟和日期之间的间距
        clockLayout.addWidget(self.clockLabel)
        clockLayout.addWidget(self.dateLabel)
        clockContainer.setStyleSheet("background-color: transparent;")
    
        # 诗词容器
        poetryContainer = QWidget()
        poetryLayout = QVBoxLayout(poetryContainer)
        poetryLayout.setAlignment(Qt.AlignBottom)
        poetryLayout.setContentsMargins(0, 0, 0, 20)# 最后一个为底部向上预留
        poetryLayout.addWidget(self.poetryLabel)
        poetryContainer.setStyleSheet("background-color: transparent;")
    
        stackLayout = QStackedLayout()
        stackLayout.addWidget(self.homeBackgroundImage)  # 底层：背景图片
        stackLayout.addWidget(clockContainer)  # 上层：时钟
        stackLayout.addWidget(poetryContainer)  # 上层：诗词
        
        stackLayout.setStackingMode(QStackedLayout.StackAll)
        
        stackWidget = QWidget()
        stackWidget.setLayout(stackLayout)
        
        # 主界面布局
        homeLayout = QVBoxLayout(home)
        homeLayout.setAlignment(Qt.AlignCenter)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.addWidget(stackWidget)
        
        self.addSubInterface(home, FIF.HOME, "主界面")
        
        self.title = TitleInterface()
        self.title.setObjectName("title")
        self.addSubInterface(self.title, FIF.INFO, "标题")
        
        self.wallpaper = WallpaperInterface(mainWindow=self)
        self.wallpaper.setObjectName("wallpaper")
        self.addSubInterface(self.wallpaper, FIF.PHOTO, "壁纸")

    def initSettingsNavigation(self):
        """ 初始化设置导航 """
        setting = SettingInterface()
        setting.setObjectName("setting")
        self.addSubInterface(setting, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)
        
        # 创建关于界面
        about = ScrollArea()
        about.scrollWidget = QWidget()
        about.mainLayout = QVBoxLayout(about.scrollWidget)
        aboutLabel = QLabel("关于", about)
        
        # 初始化界面
        about.resize(1000, 800)
        about.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        about.setViewportMargins(0, 120, 0, 20)
        about.setWidget(about.scrollWidget)
        about.setWidgetResizable(True)
        
        # 设置样式
        aboutLabel.setObjectName('settingLabel')
        about.scrollWidget.setObjectName('scrollWidget')
        aboutLabel.move(60, 63)
        
        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = get_resource_path(os.path.join('resource', 'qss', theme, 'setting_interface.qss'))
            with open(qss_path, encoding='utf-8') as f:
                about.setStyleSheet(f.read())
        except Exception:
            pass
        
        self.addSubInterface(about, FIF.INFO, "关于", NavigationItemPosition.BOTTOM)

    def resizeEvent(self, event):
        """ 窗口大小变化时调整图片大小 """
        super().resizeEvent(event)
        if hasattr(self, 'homeBackgroundImage') and self.originalPixmap is not None:
            available_width = self.width() - 50
            available_height = self.height()
            
            # 从原始图片重新缩放
            if not self.originalPixmap.isNull():
                scaled_pixmap = self.originalPixmap.scaled(available_width, available_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                
                # 应用模糊效果
                blur_effect = QGraphicsBlurEffect()
                blur_radius = cfg.backgroundBlurRadius.value
                blur_effect.setBlurRadius(blur_radius)
                self.homeBackgroundImage.setGraphicsEffect(blur_effect)
                
                self.homeBackgroundImage.setPixmap(scaled_pixmap)
                
                QApplication.processEvents()

    def moveToCenter(self):
        """ 移动窗口到屏幕中央 """
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def __updateClock(self):
        """ 更新时钟显示 """
        # 获取当前时间
        currentTime = QTime.currentTime()
        currentDate = QDate.currentDate()
        
        if cfg.showClockSeconds.value:
            timeString = currentTime.toString("HH:mm:ss")
        else:
            timeString = currentTime.toString("HH:mm")
        self.clockLabel.setText(timeString)
        
        # 公历日期
        solarString = currentDate.toString("yyyy 年 M 月 d 日 dddd")
        
        # 根据配置决定是否显示农历
        if cfg.showLunarCalendar.value:
            # 农历日期
            try:
                from cnlunar import Lunar
                import datetime
                # 将 QDate 转换为 datetime.datetime 对象
                py_datetime = datetime.datetime(currentDate.year(), currentDate.month(), currentDate.day(), 0, 0, 0)
                lunar = Lunar(py_datetime)
                lunarMonthCn = lunar.lunarMonthCn
                lunarDayCn = lunar.lunarDayCn
                # 去掉月份中的"大"、"小"字
                lunarMonthCn = lunarMonthCn.replace("大", "").replace("小", "")
                lunarString = f"{lunarMonthCn}{lunarDayCn}"
                dateString = f"{solarString} {lunarString}"
            except Exception as e:
                import logging
                logging.error(f"农历显示错误：{e}")
                dateString = solarString
        else:
            # 不显示农历，只显示公历
            dateString = solarString
        
        self.dateLabel.setText(dateString)
    
    def updateClockStyle(self):
        """ 更新时钟样式 """
        clock_color = cfg.clockColor.value
        color_str = clock_color.name() if hasattr(clock_color, 'name') else str(clock_color)
        
        self.clockLabel.setStyleSheet(f"""
            color: {color_str}; 
            font-size: 120px; 
            font-weight: bold; 
            font-family: 'Segoe UI', 'Microsoft YaHei';
            background-color: transparent;
        """)
        
        self.dateLabel.setStyleSheet(f"""
            color: {color_str}; 
            font-size: 20px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei';
            background-color: transparent;
        """)
        
        # 诗词标签也使用相同的颜色
        self.poetryLabel.setStyleSheet(f"""
            color: {color_str}; 
            font-size: 16px; 
            font-weight: bold; 
            font-family: 'Microsoft YaHei';
            background-color: transparent;
        """)
    
    def __updatePoetryInterval(self):
        """ 更新诗词更新间隔定时器 """
        self.poetryTimer.stop()
        
        interval_str = cfg.poetryUpdateInterval.value
        if interval_str == "从不":
            return
        elif interval_str == "10 分钟":
            interval = 10 * 60 * 1000
        elif interval_str == "30 分钟":
            interval = 30 * 60 * 1000
        elif interval_str == "1 小时":
            interval = 60 * 60 * 1000
        elif interval_str == "3 小时":
            interval = 3 * 60 * 60 * 1000
        elif interval_str == "6 小时":
            interval = 6 * 60 * 60 * 1000
        elif interval_str == "12 小时":
            interval = 12 * 60 * 60 * 1000
        elif interval_str == "1 天":
            interval = 24 * 60 * 60 * 1000
        else:
            interval = 60 * 60 * 1000
        
        self.poetryTimer.start(interval)
        self.__updatePoetry()
    
    def __updatePoetry(self):
        """ 更新诗词显示 """
        if not cfg.showPoetry.value:
            self.poetryLabel.setText("")
            self.poetryLabel.hide()
            return
        
        # 显示标签（如果有内容）
        self.poetryLabel.show()
        
        try:
            api_url = cfg.poetryApiUrl.value
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                # 尝试解析为 JSON
                try:
                    data = response.json()
                    if data.get('success') and 'data' in data:
                        poetry_data = data['data']
                        content = poetry_data.get('content', '')
                        author = poetry_data.get('author', '')
                        origin = poetry_data.get('origin', '')
                        
                        # 格式化诗词内容
                        poetry_text = f"「{content}」"
                        if author or origin:
                            poetry_text += f"\n——{author if author else ''}《{origin}》" if origin else f"\n——{author if author else ''}"
                        
                        self.poetryLabel.setText(poetry_text)
                    else:
                        logger.error(f"诗词 API 返回数据格式错误：{data}")
                        self.poetryLabel.setText("")
                except:
                    # 如果不是 JSON，直接显示返回的文本
                    poetry_text = response.text.strip()
                    self.poetryLabel.setText(poetry_text)
            else:
                logger.error(f"诗词 API 请求失败，状态码：{response.status_code}")
                self.poetryLabel.setText("")
        except Exception as e:
            logger.error(f"诗词更新失败：{e}")
            self.poetryLabel.setText("")

def install_fonts():
    """ 检查并安装鸿蒙字体到系统 """
    system_font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
    local_font_dir = get_resource_path(os.path.join("font", "HarmonyOS_Sans"))
    font_files = [
        "HarmonyOS_Sans_Thin.ttf",
        "HarmonyOS_Sans_Light.ttf",
        "HarmonyOS_Sans_Regular.ttf",
        "HarmonyOS_Sans_Medium.ttf",
        "HarmonyOS_Sans_Bold.ttf",
        "HarmonyOS_Sans_Black.ttf"
    ]

    fonts_installed = True
    for font_file in font_files:
        system_font_path = os.path.join(system_font_dir, font_file)
        if not os.path.exists(system_font_path):
            fonts_installed = False
            break

    if not fonts_installed:
        try:
            for font_file in font_files:
                local_font_path = os.path.join(local_font_dir, font_file)
                system_font_path = os.path.join(system_font_dir, font_file)
                if os.path.exists(local_font_path) and not os.path.exists(system_font_path):
                    shutil.copy2(local_font_path, system_font_path)
                    ctypes.windll.gdi32.AddFontResourceW(system_font_path)

            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            SMTO_ABORTIFHUNG = 0x0002
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_FONTCHANGE, 0, 0, SMTO_ABORTIFHUNG, 1000, None
            )
        except Exception:
            pass

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建QApplication
    app = QApplication(sys.argv)
    
    # 检查是否已经有实例在运行
    if not check_single_instance():
        # 加载翻译
        locale = QLocale(QLocale.Chinese, QLocale.China)
        fluentTranslator = FluentTranslator(locale)
        app.installTranslator(fluentTranslator)
        
        # 创建一个全屏临时窗口作为父窗口
        temp_widget = QWidget()
        temp_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        temp_widget.setAttribute(Qt.WA_TranslucentBackground)
        
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry()
        temp_widget.setGeometry(screen_rect)
        temp_widget.show()
        
        title = f"{APP_NAME} 已有实例运行"
        content = f"检测到{APP_NAME} 已有一个实例在运行中，请勿重复启动。\n\n(您可在“设置”中启用“允许重复启动”，可能会有不可言喻的问题。)"
        w = MessageBox(title, content, temp_widget)
        w.yesButton.setText('取消')
        w.hideCancelButton()
        w.exec()
        sys.exit(0)
    
    install_fonts()

    config_path = 'config/config.json'

    if not os.path.exists('config'):
        os.makedirs('config')

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['QFluentWidgets'] = {'FontFamilies': ['HarmonyOS Sans SC']}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    else:
        default_config = {
            "MainWindow": {
                "DpiScale": "Auto",
                "Language": "Auto",
                "ThemeColor": "#00C780",
                "ThemeMode": "Auto"
            },
            "Log": {
                "DisableLog": False,
                "LogLevel": "Info",
                "MaxCount": 50,
                "MaxDays": 7
            },
            "QFluentWidgets": {
                "FontFamilies": ["HarmonyOS Sans SC"]
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)

    if hasattr(cfg.logLevel.value, 'value'):
        log_level_str = cfg.logLevel.value.value
    else:
        log_level_str = str(cfg.logLevel.value)
    
    logger.update_config(
        disable_log=cfg.disableLog.value,
        log_level=log_level_str,
        max_count=cfg.logMaxCount.value,
        max_days=cfg.logMaxDays.value
    )
    logger.info(f"读取日志禁用配置: {cfg.disableLog.value}")
    logger.info(f"读取重复启动开关配置: {cfg.allowMultipleInstances.value}")
    logger.info(f"读取主题配置设置: {cfg.themeMode.value}")
    logger.info(f"读取颜色配置设置: {cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else cfg.themeColor.value}")
    logger.info(f"读取日志级别配置: {cfg.logLevel.value}")
    logger.info(f"读取日志数量上限配置: {cfg.logMaxCount.value}")
    logger.info(f"读取日志时间上限配置: {cfg.logMaxDays.value}")
    logger.info(f"读取关闭事件行为配置: {cfg.closeAction.value}")

    locale = QLocale(QLocale.Chinese, QLocale.China)
    fluentTranslator = FluentTranslator(locale)
    app.installTranslator(fluentTranslator)

    font_dir = get_resource_path(os.path.join("font", "HarmonyOS_Sans"))
    font_files = [
        "HarmonyOS_Sans_Thin.ttf",
        "HarmonyOS_Sans_Light.ttf",
        "HarmonyOS_Sans_Regular.ttf",
        "HarmonyOS_Sans_Medium.ttf",
        "HarmonyOS_Sans_Bold.ttf",
        "HarmonyOS_Sans_Black.ttf"
    ]

    for font_file in font_files:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)

    QApplication.setFont(QFont("HarmonyOS Sans SC", 10))
    logger.info("字体已设置为: HarmonyOS Sans SC")

    window = MainWindow()
    window.show()
    logger.info(f"{APP_NAME}版本信息：")
    logger.info(f"版本号：{VERSION} 构建日期：{BUILD_DATE}")
    logger.info(f"{APP_NAME}环境信息：")
    logger.info(f"系统版本：Windows {platform.version()} Python版本：{platform.python_version()}")
    logger.info(f"软件运行路径：{BASE_DIR}")
    
    sys.exit(app.exec_())
