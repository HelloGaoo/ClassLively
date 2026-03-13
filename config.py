import os
from enum import Enum

from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtGui import QGuiApplication, QFont
from qfluentwidgets import (
    qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
    ColorConfigItem, OptionsValidator, RangeConfigItem, RangeValidator,
    FolderListValidator, EnumSerializer, FolderValidator, ConfigSerializer, __version__,
    Theme
)


class ThemeSerializer(ConfigSerializer):
    """ 主题序列化 """

    def serialize(self, theme):
        return theme.value

    def deserialize(self, value: str):
        return Theme(value)


class Language(Enum):
    """ 语言枚举 """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ 语言序列化器 """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


class LogLevel(Enum):
    """ 日志级别枚举 """
    DEBUG = "Debug"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


class LogLevelSerializer(ConfigSerializer):
    """ 日志级别序列化器 """

    def serialize(self, level):
        return level.value

    def deserialize(self, value: str):
        for level in LogLevel:
            if level.value == value:
                return level
        return LogLevel.INFO


class Config(QConfig):
    """ 应用配置 """

    themeMode = OptionsConfigItem(
        "MainWindow", "ThemeMode", Theme.AUTO, OptionsValidator([Theme.LIGHT, Theme.DARK, Theme.AUTO]), ThemeSerializer()
    )
    themeColor = ColorConfigItem("MainWindow", "ThemeColor", "#0099BC")
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True
    )
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True
    )
    
    # 日志配置
    logLevel = OptionsConfigItem(
        "Log", "LogLevel", LogLevel.INFO, OptionsValidator(LogLevel), LogLevelSerializer()
    )
    disableLog = ConfigItem(
        "Log", "DisableLog", False, BoolValidator()
    )
    logMaxCount = RangeConfigItem(
        "Log", "MaxCount", 50, RangeValidator(10, 500)
    )
    logMaxDays = RangeConfigItem(
        "Log", "MaxDays", 7, RangeValidator(30, 365)
    )


cfg = Config()
if not os.path.exists('config'):
    os.makedirs('config')
qconfig.load('config/config.json', cfg)
