from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFontDatabase, QFont
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, MessageBox,
                            setTheme, Theme, FluentWindow, NavigationAvatarWidget,
                            isDarkTheme, InfoBar, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF
import sys
import os

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 加载字体
        self.loadGlobalFont()
        
        # 设置主题
        setTheme(Theme.DARK)
        
        # 主界面导航
        self.initMainNavigation()
        
        # 设置导航
        self.initSettingsNavigation()
        
        # 窗口标题 大小
        self.setWindowTitle("260311")
        self.resize(1100, 700)
        
        # 移动窗口到屏幕中央
        self.moveToCenter()
        
    def initMainNavigation(self):
        # 主界面导航区域
        home = QWidget()
        home.setObjectName("home")
        self.addSubInterface(home, FIF.HOME, "主界面")
        
    def initSettingsNavigation(self):
        # 设置导航区域
        setting = QWidget()
        setting.setObjectName("setting")
        self.addSubInterface(setting, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)
        
    def loadGlobalFont(self):
        # HarmonyOS Sans
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
        
        # 默认字体Regular
        app_font = QFont("HarmonyOS Sans", 10)
        QApplication.setFont(app_font)
    
    def moveToCenter(self):
        # 移动窗口到屏幕中央
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())