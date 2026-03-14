import os
import logging
import time
import glob
from logging.handlers import RotatingFileHandler
import sys
from config import cfg
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "Logs")

DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s|%(levelname)s|%(name)s.%(funcName)s|%(module)s:%(lineno)d|%(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_MAX_BYTES = 1 * 1024 * 1024
LOG_BACKUP_COUNT = getattr(cfg, 'logMaxCount', 50)
LOG_RETENTION_DAYS = getattr(cfg, 'logMaxDays', 7)

def get_logger(module_name):
    """获取指定模块的日志记录器"""
    return logging.getLogger(module_name)

# 确保日志目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

def custom_exception_hook(exctype, value, tb):
    """自定义异常钩子，用于记录未处理的异常"""
    if issubclass(exctype, KeyboardInterrupt):
        sys.__excepthook__(exctype, value, tb)
        return
    
    # 记录异常信息
    try:
        logging.critical(f"未处理的异常: {exctype.__name__}: {value}", exc_info=(exctype, value, tb))
    except Exception:
        print(f"未处理的异常: {exctype.__name__}: {value}")
        import traceback
        traceback.print_exc()
    sys.__excepthook__(exctype, value, tb)

# 设置全局异常钩子
sys.excepthook = custom_exception_hook

def setup_logging(level=DEFAULT_LOG_LEVEL):
    """配置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件日志
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(LOGS_DIR, f"app_{timestamp}.log")
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def cleanup_old_logs_by_count(directory, max_count=None, keep_count=None):
    """根据文件数量清理旧日志文件"""
    # 使用配置中的值，如果未提供
    from config import cfg
    if max_count is None:
        max_count = getattr(cfg, 'logMaxCount', 50)
    
    # 获取实际值
    if hasattr(max_count, 'value'):
        max_count = max_count.value
    
    if keep_count is None:
        keep_count = max(3, max_count // 5)  # 保留数量为最大数量的1/5，最少3个
    
    try:
        log_files = glob.glob(os.path.join(directory, "*.log"))
        log_files.extend(glob.glob(os.path.join(directory, "*.log.*")))
        
        log_files = [f for f in log_files if os.path.isfile(f)]
        
        if len(log_files) > max_count:
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            files_to_delete = log_files[keep_count:]
            total_files = len(log_files)
            deleted_count = 0
            failed_count = 0
            
            for log_file in files_to_delete:
                try:
                    get_logger("Main").info(f"删除过期日志文件: {log_file}")
                    os.remove(log_file)
                    deleted_count += 1
                except Exception as err:
                    failed_count += 1
                    if failed_count <= 5:
                        get_logger("Main").error(f"删除日志文件 {log_file} 失败: {str(err)}")
            
            get_logger("Main").info(f"清理日志完成: 共 {total_files} 个文件，保留 {keep_count} 个，删除 {deleted_count} 个，失败 {failed_count} 个")
    except Exception as err:
        get_logger("Main").error(f"清理旧日志时出错: {str(err)}")

def cleanup_old_logs(directory, retention_days=None):
    """清理旧日志文件"""
    # 使用配置中的值，如果未提供
    from config import cfg
    if retention_days is None:
        retention_days = getattr(cfg, 'logMaxDays', 7)
    
    # 获取配置中的日志最大数量
    max_count = getattr(cfg, 'logMaxCount', 50)
    cleanup_old_logs_by_count(directory, max_count=max_count)

# 初始化函数，在配置加载后调用
def init_logger():
    """初始化日志系统"""
    from config import cfg
    
    # 获取配置中的日志级别
    log_level = getattr(cfg, 'logLevel', 'Info')
    level_map = {
        'Debug': logging.DEBUG,
        'Info': logging.INFO,
        'Warning': logging.WARNING,
        'Error': logging.ERROR
    }
    level = level_map.get(log_level.value if hasattr(log_level, 'value') else log_level, logging.INFO)
    
    # 设置日志系统
    setup_logging(level=level)
    
    # 清理旧日志
    cleanup_old_logs(LOGS_DIR)
    
    # 获取配置值
    log_max_count = getattr(cfg, 'logMaxCount', 50)
    log_max_days = getattr(cfg, 'logMaxDays', 7)
    
    # 获取实际值
    if hasattr(log_max_count, 'value'):
        log_max_count = log_max_count.value
    if hasattr(log_max_days, 'value'):
        log_max_days = log_max_days.value
    
    # 记录初始化完成
    get_logger("Main").info("日志系统初始化完成")
    get_logger("Main").info(f"日志级别: {log_level}")
    get_logger("Main").info(f"日志最大数量: {log_max_count}")
    get_logger("Main").info(f"日志保留天数: {log_max_days}")