from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, MessageBox,
                            setTheme, Theme, FluentWindow, NavigationAvatarWidget,
                            isDarkTheme, InfoBar, InfoBarPosition)
from qfluentwidgets import FluentIcon as FIF
import sys

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 主题
        setTheme(Theme.LIGHT)
        
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