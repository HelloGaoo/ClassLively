import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel
from qfluentwidgets import (
    SettingCardGroup, OptionsSettingCard, ScrollArea, ExpandLayout, 
    Theme, setTheme, isDarkTheme, FluentIcon as FIF, CustomColorSettingCard, setThemeColor
)
from config import cfg


class SettingInterface(ScrollArea):
    """ 设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.settingLabel = QLabel("设置", self)

        self.appearanceGroup = SettingCardGroup("外观", self.scrollWidget)
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            "应用颜色主题",
            "更改应用程序的颜色外观",
            texts=[
                "浅色", "深色",
                "使用系统设置"
            ],
            parent=self.appearanceGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            "主要颜色",
            "更改应用程序的主要颜色",
            parent=self.appearanceGroup
        )

        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面 """
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.__setQss()

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        """ 初始化布局 """
        self.settingLabel.move(60, 63)

        self.appearanceGroup.addSettingCard(self.themeCard)
        self.appearanceGroup.addSettingCard(self.themeColorCard)

        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.appearanceGroup)

    def __setQss(self):
        """ 设置样式表 """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'resource', 'qss', theme, 'setting_interface.qss')
            print(f"加载QSS文件: {qss_path}")
            with open(qss_path, encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"QSS文件加载失败: {e}")
            pass

    def __onThemeChanged(self, theme: Theme):
        """ 主题变更槽函数 """
        setTheme(theme)

        self.__setQss()

    def __connectSignalToSlot(self):
        """ 连接信号与槽 """
        cfg.themeChanged.connect(self.__onThemeChanged)
        self.themeColorCard.colorChanged.connect(setThemeColor)
