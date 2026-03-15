from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import (
    MessageBoxBase, SearchLineEdit, ListWidget, SubtitleLabel, BodyLabel,
    PushButton, InfoBar
)
import sqlite3
import os
import sys

# 路径设置
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    MEIPASS_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEIPASS_DIR = None

def get_resource_path(relative_path):
    """获取绝对路径"""
    if MEIPASS_DIR:
        return os.path.join(MEIPASS_DIR, relative_path)
    return os.path.join(BASE_DIR, relative_path)


class CityDatabase:
    """城市数据库管理类"""
    
    def __init__(self):
        self.db_path = get_resource_path(os.path.join('data', 'xiaomi_weather.db'))
        if not os.path.exists(self.db_path):
            # 尝试在数据目录查找
            self.db_path = os.path.join(BASE_DIR, 'data', 'xiaomi_weather.db')
    
    def search_by_name(self, search_term):
        """根据城市名搜索城市"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM citys WHERE name LIKE ?', ('%' + search_term + '%',))
            cities_results = cursor.fetchall()
            conn.close()
            return [city[2] for city in cities_results]  # 返回城市名称列表
        except Exception as e:
            print(f'搜索城市失败：{e}')
            return []
    
    def search_by_num(self, city_code):
        """根据城市代码获取城市名称"""
        try:
            if not os.path.exists(self.db_path):
                return ''
            
            # 去掉 weathercn: 前缀
            if city_code.startswith('weathercn:'):
                city_code = city_code.replace('weathercn:', '')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM citys WHERE city_num LIKE ?', ('%' + city_code + '%',))
            cities_results = cursor.fetchall()
            conn.close()
            
            if cities_results:
                return cities_results[0][2]  # 返回城市名称
            return ''
        except Exception as e:
            print(f'根据代码搜索城市失败：{e}')
            return ''
    
    def search_code_by_name(self, city_name):
        """根据城市名获取城市代码"""
        try:
            if not os.path.exists(self.db_path):
                return ''
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM citys WHERE name = ?', (city_name,))
            city_result = cursor.fetchone()
            conn.close()
            
            if city_result:
                return city_result[3]  # 返回城市代码 (索引 3 是 city_num 列)
            return ''
        except Exception as e:
            print(f'根据名称搜索代码失败：{e}')
            return ''


class SelectCityDialog(MessageBoxBase):
    """城市选择对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.city_db = CityDatabase()
        
        # 标题和副标题
        title_label = SubtitleLabel()
        subtitle_label = BodyLabel()
        
        title_label.setText(QCoreApplication.translate('SelectCity', '搜索城市'))
        subtitle_label.setText(QCoreApplication.translate('SelectCity', '请输入当地城市名进行搜索'))
        
        # 搜索框
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText(QCoreApplication.translate('SelectCity', '输入城市名'))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.search_city)
        
        # 城市列表
        self.city_list = ListWidget()
        self.city_list.addItems(self.city_db.search_by_name(''))
        self.city_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        self.viewLayout.addWidget(title_label)
        self.viewLayout.addWidget(subtitle_label)
        self.viewLayout.addWidget(self.search_edit)
        self.viewLayout.addWidget(self.city_list)
        
        # 设置按钮文字
        self.yesButton.setText(QCoreApplication.translate('SelectCity', '选择此城市'))
        self.cancelButton.setText(QCoreApplication.translate('SelectCity', '取消'))
        
        self.widget.setMinimumWidth(500)
        self.widget.setMinimumHeight(600)
        
        self.__select_current_city()
    
    def __select_current_city(self):
        """选中当前配置的城市"""
        try:
            from config import cfg
            current_city = cfg.city.value
            if current_city:
                # 在列表中查找该城市
                items = self.city_list.findItems(current_city, Qt.MatchExactly)
                if items:
                    item = items[0]
                    self.city_list.setCurrentItem(item)
                    self.city_list.scrollToItem(item)
        except Exception as e:
            print(f'选中当前城市失败：{e}')
    
    def search_city(self):
        """搜索城市"""
        search_text = self.search_edit.text()
        self.city_list.clear()
        cities = self.city_db.search_by_name(search_text)
        self.city_list.addItems(cities)
        self.city_list.clearSelection()
    
    def on_item_double_clicked(self, item):
        """双击城市项时自动确认"""
        self.yesButton.click()
    
    def get_selected_city(self):
        """获取选中的城市"""
        selected_items = self.city_list.selectedItems()
        if selected_items:
            return selected_items[0].text()
        return None
