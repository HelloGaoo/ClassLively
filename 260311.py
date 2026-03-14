from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QLocale, QTranslator
from PyQt5.QtGui import QFontDatabase, QFont
from qfluentwidgets import (
    setTheme, Theme, FluentWindow, FluentTranslator,
    FluentIcon as FIF, NavigationItemPosition
)
import sys
import os
from setting import SettingInterface
import shutil
import ctypes
from config import cfg

class MainWindow(FluentWindow):
    """ 主窗口 """

    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)
        self.initMainNavigation()
        self.initSettingsNavigation()
        self.setWindowTitle("260311")
        self.resize(1100, 700)
        self.moveToCenter()

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
    local_font_dir = os.path.join(os.getcwd(), "font", "HarmonyOS_Sans")
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
    try:
        print("开始安装字体")
        install_fonts()
        print("字体安装完成")

        print("开始配置设置文件")
        import json
        config_path = 'config/config.json'

        if not os.path.exists('config'):
            os.makedirs('config')
            print("创建config目录")

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['QFluentWidgets'] = {'FontFamilies': ['HarmonyOS Sans SC']}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print("更新配置文件")
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
            print("创建默认配置文件")

        # 重新加载配置，确保获取最新值
        from config import cfg
        import qfluentwidgets
        qfluentwidgets.qconfig.load('config/config.json', cfg)

        # 导入并初始化日志系统
        import logger
        from logger import get_logger, init_logger
        init_logger()

        # 初始化日志记录器
        main_logger = get_logger("Main")
        main_logger.info("程序启动")
        main_logger.info("字体安装完成")
        main_logger.info("配置文件处理完成")

        main_logger.info("初始化应用程序")
        app = QApplication(sys.argv)

        main_logger.info("设置国际化")
        locale = QLocale(QLocale.Chinese, QLocale.China)
        fluentTranslator = FluentTranslator(locale)
        app.installTranslator(fluentTranslator)

        main_logger.info("加载字体")
        font_dir = os.path.join(os.getcwd(), "font", "HarmonyOS_Sans")
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

        main_logger.info("设置全局字体为: HarmonyOS Sans SC")
        QApplication.setFont(QFont("HarmonyOS Sans SC", 10))

        main_logger.info("创建主窗口")
        window = MainWindow()
        main_logger.info("显示主窗口")
        window.show()
        main_logger.info("进入事件循环")
        sys.exit(app.exec_())
    except Exception as e:
        # 如果日志系统未初始化，使用print
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
