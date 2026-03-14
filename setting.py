import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel
from qfluentwidgets import (
    SettingCardGroup, OptionsSettingCard, ScrollArea, ExpandLayout, 
    Theme, setTheme, isDarkTheme, FluentIcon as FIF, CustomColorSettingCard, setThemeColor,
    SwitchSettingCard, RangeSettingCard, InfoBar
)
from config import cfg

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
        self.disableLogCard = SwitchSettingCard(
            FIF.CLOSE, 
            "禁用日志",
            "完全禁用日志输出",
            configItem=cfg.disableLog,
            parent=self.logGroup
        )
        self.logLevelCard = OptionsSettingCard(
            cfg.logLevel,
            FIF.INFO,
            "日志级别",
            "设置日志的输出级别",
            texts=["Debug", "Info", "Warning", "Error"],
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
        
        self.logGroup.addSettingCard(self.disableLogCard)
        self.logGroup.addSettingCard(self.logLevelCard)
        self.logGroup.addSettingCard(self.logMaxCountCard)
        self.logGroup.addSettingCard(self.logMaxDaysCard)

        self.otherGroup = SettingCardGroup("其他", self.scrollWidget)
        self.closeActionCard = OptionsSettingCard(
            cfg.closeAction,
            FIF.SETTING,
            "关闭事件行为",
            "设置点击关闭按钮时的行为",
            texts=["最小化到任务栏", "直接关闭"],
            parent=self.otherGroup
        )
        self.otherGroup.addSettingCard(self.closeActionCard)

        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.appearanceGroup)
        self.expandLayout.addWidget(self.logGroup)
        self.expandLayout.addWidget(self.otherGroup)

    def __setQss(self):
        """ 设置样式表 """
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        theme = 'dark' if isDarkTheme() else 'light'
        try:
            qss_path = get_resource_path(os.path.join('resource', 'qss', theme, 'setting_interface.qss'))
            with open(qss_path, encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

    def __onThemeChanged(self, theme: Theme):
        """ 主题变更槽函数 """
        setTheme(theme)
        self.__setQss()

    def __showRestartTooltip(self):
        """ 显示重启提示 """
        InfoBar.warning(
            '',
            "配置需要重启应用程序才能生效",
            parent=self.window()
        )

    def __onDisableLogChanged(self, disabled):
        """ 日志禁用状态变更槽函数 """
        # 当禁用日志时，禁用其他日志相关设置
        self.logLevelCard.setEnabled(not disabled)
        self.logMaxCountCard.setEnabled(not disabled)
        self.logMaxDaysCard.setEnabled(not disabled)
    
    def __connectSignalToSlot(self):
        """ 连接信号与槽 """
        cfg.themeChanged.connect(self.__onThemeChanged)
        self.themeColorCard.colorChanged.connect(setThemeColor)
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        
        # 连接日志禁用信号
        self.disableLogCard.checkedChanged.connect(self.__onDisableLogChanged)
        
        # 初始状态设置
        self.__onDisableLogChanged(cfg.disableLog.value)
