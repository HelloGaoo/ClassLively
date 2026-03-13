from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFontDatabase, QFont
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, MessageBox,
                            setTheme, Theme, FluentWindow, NavigationAvatarWidget,
                            isDarkTheme, InfoBar, InfoBarPosition, FluentTranslator)
from qfluentwidgets import FluentIcon as FIF
import sys
import os
from setting import SettingInterface

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
    import shutil
    import ctypes
    from ctypes import wintypes
    
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
        print("正在安装鸿蒙字体...")
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
            
            print("鸿蒙字体安装成功！")
        except Exception as e:
            print(f"字体安装失败: {e}")

if __name__ == "__main__":
    # 安装字体
    install_fonts()
    
    app = QApplication(sys.argv)
    
    # 国际化
    locale = QLocale(QLocale.Chinese, QLocale.China)
    fluentTranslator = FluentTranslator(locale)
    app.installTranslator(fluentTranslator)
    
    # 加载字体
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
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
