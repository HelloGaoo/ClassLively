import os
import logging
import logging.handlers
import inspect
from datetime import datetime, timedelta

log_dir = os.path.join(os.getcwd(), "logs")
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
            caller_info = f"260311.{class_name}.{function_name}"
        else:
            if function_name == '<module>':
                caller_info = f"260311.Main.<module>"
            else:
                caller_info = f"260311.{function_name}"
        
        if extra is None:
            extra = {}
        extra['caller_info'] = caller_info
        
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

logging.setLoggerClass(CustomLogger)

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
            '%(asctime)s|%(levelname)s|%(caller_info)s|260311:%(process)d|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
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

logger = Logger()
