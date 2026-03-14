import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel
from qfluentwidgets import (
    SettingCardGroup, OptionsSettingCard, ScrollArea, ExpandLayout, 
    Theme, setTheme, isDarkTheme, FluentIcon as FIF, CustomColorSettingCard, setThemeColor,
    SwitchSettingCard, RangeSettingCard, InfoBar
)
from config import cfg

from logger import get_logger


class SettingInterface(ScrollArea):
    """ 设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.logger = get_logger("Setting")
        self.logger.info("初始化设置界面")
        
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.settingLabel = QLabel("设置", self)

        self.appearanceGroup = SettingCardGroup("外观", self.scrollWidget)
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            "应用颜色主题",
            "更改应用程序的颜色外观",
            texts=["浅色", "深色", "使用系统设置"],
            parent=self.appearanceGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            "主要颜色",
            "更改应用程序的主要颜色",
            parent=self.appearanceGroup
        )
        
        self.logGroup = SettingCardGroup("日志", self.scrollWidget)
        self.logLevelCard = OptionsSettingCard(
            cfg.logLevel,
            FIF.INFO,
            "日志级别",
            "设置日志的输出级别",
            texts=["Debug", "Info", "Warning", "Error"],
            parent=self.logGroup
        )
        self.disableLogCard = SwitchSettingCard(
            FIF.CLOSE, 
            "禁用日志",
            "完全禁用日志输出",
            configItem=cfg.disableLog,
            parent=self.logGroup
        )
        self.logMaxCountCard = RangeSettingCard(
            cfg.logMaxCount,
            FIF.INFO,
            "日志数量上限",
            "设置日志文件的最大条目数",
            parent=self.logGroup
        )
        self.logMaxDaysCard = RangeSettingCard(
            cfg.logMaxDays,
            FIF.INFO,
            "日志时间上限",
            "设置日志文件的最大保存天数",
            parent=self.logGroup
        )

        self.__initWidget()
        self.logger.info("设置界面初始化完成")

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
        
        self.logGroup.addSettingCard(self.logLevelCard)
        self.logGroup.addSettingCard(self.disableLogCard)
        self.logGroup.addSettingCard(self.logMaxCountCard)
        self.logGroup.addSettingCard(self.logMaxDaysCard)

        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.appearanceGroup)
        self.expandLayout.addWidget(self.logGroup)

    def __setQss(self):
        """ 设置样式表 """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'resource', 'qss', theme, 'setting_interface.qss')
            with open(qss_path, encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

    def __onThemeChanged(self, theme: Theme):
        """ 主题变更槽函数 """
        self.logger.info(f"主题变更为: {theme.value}")
        setTheme(theme)
        self.__setQss()
        self.logger.info("主题变更完成")

    def __showRestartTooltip(self):
        """ 显示重启提示 """
        InfoBar.warning(
            '',
            "配置需要重启应用程序才能生效",
            parent=self.window()
        )

    def __connectSignalToSlot(self):
        """ 连接信号与槽 """
        cfg.themeChanged.connect(self.__onThemeChanged)
        self.themeColorCard.colorChanged.connect(setThemeColor)
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        self.themeCard.optionChanged.connect(lambda: self.__onSettingChanged("主题"))
        self.themeColorCard.colorChanged.connect(lambda: self.__onSettingChanged("主题颜色"))
        self.logLevelCard.optionChanged.connect(lambda: self.__onSettingChanged("日志级别"))
        self.disableLogCard.checkedChanged.connect(lambda: self.__onSettingChanged("禁用日志"))
        self.logMaxCountCard.valueChanged.connect(lambda: self.__onSettingChanged("日志数量上限"))
        self.logMaxDaysCard.valueChanged.connect(lambda: self.__onSettingChanged("日志时间上限"))
    
    def __onSettingChanged(self, setting_name):
        """ 设置变更槽函数，显示保存提示 """
        from qfluentwidgets import InfoBar
        InfoBar.success(
            '',
            "设置变更已保存",
            parent=self.window()
        )
        self.logger.info(f"设置变更已保存: {setting_name}")
