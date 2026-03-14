import os
import logging
import logging.handlers
from datetime import datetime, timedelta

# 确保日志目录存在
log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class Logger:
    """ 日志管理类 """
    
    def __init__(self, disable_log=False, log_level="INFO", max_count=50, max_days=7):
        self.logger = logging.getLogger("260311")
        self.disable_log = disable_log
        self.log_level = log_level
        self.max_count = max_count
        self.max_days = max_days
        self.file_handler = None
        self.console_handler = None
        self.__setup_handlers()
    
    def __setup_handlers(self):
        """ 设置日志处理器 """
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        if self.disable_log:
            return
        
        # 根据配置设置日志级别
        log_level_name = self.log_level.upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        
        # 确保logger的级别设置正确
        self.logger.setLevel(log_level)
        
        # 生成基于时间戳的日志文件名
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"app_{timestamp}.log"
        
        # 文件处理器
        self.file_handler = logging.FileHandler(
            os.path.join(log_dir, log_filename),
            encoding="utf-8"
        )
        self.file_handler.setLevel(log_level)
        
        # 控制台处理器
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(log_level)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
    
    def update_config(self, disable_log=False, log_level="INFO", max_count=50, max_days=7):
        """ 更新配置 """
        self.disable_log = disable_log
        self.log_level = log_level
        self.max_count = max_count
        self.max_days = max_days
        self.__setup_handlers()
    
    def debug(self, message):
        """ 调试日志 """
        self.logger.debug(message)
    
    def info(self, message):
        """ 信息日志 """
        self.logger.info(message)
    
    def warning(self, message):
        """ 警告日志 """
        self.logger.warning(message)
    
    def error(self, message):
        """ 错误日志 """
        self.logger.error(message)
    
    def exception(self, message):
        """ 异常日志 """
        self.logger.exception(message)

# 创建全局日志实例
logger = Logger()
