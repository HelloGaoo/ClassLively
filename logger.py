import os
import logging
import logging.handlers
import inspect
import sys
from datetime import datetime, timedelta
from constants import APP_NAME

# 路径设置
if getattr(sys, 'frozen', False):
    # 打包为exe时
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # 脚本运行时
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

log_dir = os.path.join(BASE_DIR, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

class CustomLogger(logging.Logger):

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=3):
        caller_frame = inspect.stack()[stacklevel]
        module_name = caller_frame[1].split(os.sep)[-1].replace('.py', '')
        function_name = caller_frame[3]
        
        # 获取类名
        class_name = ''
        frame = caller_frame[0]
        try:
            if 'self' in frame.f_locals:
                class_name = frame.f_locals['self'].__class__.__name__
            elif 'cls' in frame.f_locals:
                class_name = frame.f_locals['cls'].__name__
        except Exception:
            pass
        
        # 构建调用路径
        if class_name:
            caller_info = f"{APP_NAME}.{class_name}.{function_name}"
        else:
            if function_name == '<module>':
                caller_info = f"{APP_NAME}.Main.<module>"
            else:
                caller_info = f"{APP_NAME}.{function_name}"
        
        if extra is None:
            extra = {}
        extra['caller_info'] = caller_info
        
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

logging.setLoggerClass(CustomLogger)

class Logger:
    """ 日志管理类 """
    
    def __init__(self, disable_log=False, log_level="INFO", max_count=50, max_days=7):
        self.logger = logging.getLogger(APP_NAME)
        self.disable_log = disable_log
        self.log_level = log_level
        self.max_count = max_count
        self.max_days = max_days
        self.file_handler = None
        self.console_handler = None
        self.__setup_handlers()
    
    def __clean_old_logs(self):
        """ 清理旧日志文件 """
        if not os.path.exists(log_dir):
            return
        
        # 获取所有日志文件
        log_files = []
        for file in os.listdir(log_dir):
            if file.startswith("app_") and file.endswith(".log"):
                file_path = os.path.join(log_dir, file)
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    mtime = os.path.getmtime(file_path)
                    log_files.append((file_path, mtime))
        
        # 按修改时间排序（最新的在前）
        log_files.sort(key=lambda x: x[1], reverse=True)
        
        # 按数量清理
        if len(log_files) > self.max_count:
            for file_path, _ in log_files[self.max_count:]:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        
        # 按天数清理
        cutoff_time = datetime.now().timestamp() - (self.max_days * 24 * 3600)
        for file_path, mtime in log_files:
            if mtime < cutoff_time:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
    
    def __setup_handlers(self):
        """ 日志处理 """
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        if self.disable_log:
            return
        
        log_level_name = self.log_level.upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        
        self.logger.setLevel(log_level)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"app_{timestamp}.log"
        
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
            '%(asctime)s|%(levelname)s|%(caller_info)s|{APP_NAME}:%(process)d|%(message)s'.format(APP_NAME=APP_NAME),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
        
        # 清理旧日志
        self.__clean_old_logs()
    
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

logger = Logger()
