"""
云上归墅 · 统一日志系统
替换全项目 print() 调用，支持日志级别、文件轮转、结构化输出
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ── 主日志器 ─────────────────────────────────────────
_logger = logging.getLogger("yunshang")
_logger.setLevel(logging.DEBUG)

# 控制台输出（开发环境）
_console = logging.StreamHandler()
_console.setLevel(logging.DEBUG)
_console.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname).1s] %(name)s.%(funcName)s:%(lineno)d — %(message)s",
    datefmt="%H:%M:%S"
))
_logger.addHandler(_console)

# 文件输出（生产环境，按天轮转）
_file = RotatingFileHandler(
    os.path.join(LOG_DIR, "yunshang.log"),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=30,
    encoding="utf-8"
)
_file.setLevel(logging.INFO)
_file.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
_logger.addHandler(_file)

# 错误日志单独文件
_error_file = RotatingFileHandler(
    os.path.join(LOG_DIR, "error.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=10,
    encoding="utf-8"
)
_error_file.setLevel(logging.WARNING)
_error_file.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
_logger.addHandler(_error_file)


def get_logger(name: str = "yunshang") -> logging.Logger:
    """获取命名日志器"""
    return logging.getLogger(name)


# ── 便捷函数 ─────────────────────────────────────────
def info(msg: str, **kwargs):
    _logger.info(msg, extra=kwargs)


def warning(msg: str, **kwargs):
    _logger.warning(msg, extra=kwargs)


def error(msg: str, exc_info=False, **kwargs):
    _logger.error(msg, exc_info=exc_info, extra=kwargs)


def debug(msg: str, **kwargs):
    _logger.debug(msg, extra=kwargs)


def log_ai(openid: str, mode: str, user_msg: str, reply: str, duration_ms: float = 0):
    """记录 AI 对话"""
    _logger.info(
        f"[AI] openid={openid} mode={mode} duration={duration_ms:.0f}ms "
        f"q=\"{user_msg[:80]}\" a=\"{reply[:80]}\""
    )


def log_keyword(openid: str, pattern: str, content: str):
    """记录关键词命中"""
    _logger.info(f"[KW] openid={openid} pattern={pattern} content=\"{content[:60]}\"")


def log_service(openid: str, service_name: str, success: bool):
    """记录服务请求"""
    if success:
        _logger.info(f"[SVC] openid={openid} service={service_name} ✓")
    else:
        _logger.warning(f"[SVC] openid={openid} service={service_name} ✗")


def log_booking(openid: str, action: str, detail: str = ""):
    """记录预订操作"""
    _logger.info(f"[BOOK] openid={openid} action={action} {detail}".strip())


def log_error(module: str, error_msg: str, exc_info=False):
    """记录错误"""
    _logger.error(f"[ERR] {module} — {error_msg}", exc_info=exc_info)
