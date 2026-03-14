from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QLocale, QTranslator
from PyQt5.QtGui import QFontDatabase, QFont, QIcon
from qfluentwidgets import (
    setTheme, Theme, FluentWindow, FluentTranslator,
    FluentIcon as FIF, NavigationItemPosition
)
import sys
import os
import platform
from setting import SettingInterface
import shutil
import ctypes
from config import cfg
from logger import logger
from version import VERSION, BUILD_DATE
from constants import APP_NAME
import json
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
        self.moveToCenter()
        
        # 初始化系统托盘
        self.initSystemTray()
    
    def initSystemTray(self):
        """ 初始化系统托盘 """
        icon_path = get_resource_path(os.path.join("resource", "icons", "CY.png"))
        if os.path.exists(icon_path):
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        else:
            self.tray_icon = QSystemTrayIcon(self)
        
        # 创建托盘菜单
        self.tray_menu = QMenu(self)
        
        # 显示主窗口动作
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        self.tray_menu.addAction(show_action)
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 双击托盘图标显示/隐藏主窗口
        self.tray_icon.activated.connect(self.__onTrayIconActivated)
        
        # 显示托盘图标
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
        # 最小化到托盘而不是退出
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "应用已最小化到系统托盘",
            QSystemTrayIcon.Information,
            2000
        )

    def initMainNavigation(self):
        """ 初始化主界面导航 """
        home = QWidget()
        home.setObjectName("home")
        self.addSubInterface(home, FIF.HOME, "主界面")

    def initSettingsNavigation(self):
        """ 初始化设置导航 """
        setting = SettingInterface()
        setting.setObjectName("setting")
        self.addSubInterface(setting, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)

    def moveToCenter(self):
        """ 移动窗口到屏幕中央 """
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

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
    logger.info(f"读取主题配置设置: {cfg.themeMode.value}")
    logger.info(f"读取颜色配置设置: {cfg.themeColor.value.name() if hasattr(cfg.themeColor.value, 'name') else cfg.themeColor.value}")
    logger.info(f"读取日志级别配置: {cfg.logLevel.value}")
    logger.info(f"读取日志数量上限配置: {cfg.logMaxCount.value}")
    logger.info(f"读取日志时间上限配置: {cfg.logMaxDays.value}")

    app = QApplication(sys.argv)

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
