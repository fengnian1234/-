"""
BnB 上下文管理器 — 请求级 BnB 上下文 + Flask g 注入
三家民宿：guishu(归墅) / shanji(山纪) / donglinwai(东林外)

使用方式：
  入口（app.py / wechat.py）：
      from bnb_context import set_current_bnb
      set_current_bnb(bnb_id)  # 一次设置，全链路可用

  业务层（services/*.py）：
      from bnb_context import get_current_bnb_id
      bnb_id = get_current_bnb_id()  # 无需传参

  服务层（无 Flask 上下文时）：
      from bnb_context import get_service_bnb_id
      bnb_id = get_service_bnb_id(bnb_id)  # 优先参数 > Flask g > default
"""
import threading
import logging
from flask import g, request, has_request_context
from config import BNB_CONFIGS

logger = logging.getLogger(__name__)

# URL 路径前缀 → bnb_id 映射
_PREFIX_MAP = {
    "/gs": "guishu",
    "/sj": "shanji",
    "/dlw": "donglinwai",
}

# 微信路径 → bnb_id 映射
_WECHAT_MAP = {
    "/wechat/gs": "guishu",
    "/wechat/sj": "shanji",
    "/wechat/dlw": "donglinwai",
}

# 线程本地存储（非 Flask 环境 / 后台任务兜底）
_thread_local = threading.local()


def set_current_bnb(bnb_id: str):
    """在请求/任务入口显式设置当前 BnB。
    建议在 app.py before_request 和 wechat.py handle_wechat_message 中调用。
    """
    if has_request_context():
        g.bnb_id = bnb_id
        g.bnb_config = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    _thread_local.bnb_id = bnb_id


def get_bnb_id_from_path(path: str = None) -> str:
    """从请求路径提取 bnb_id，未匹配则默认归墅"""
    if path is None:
        try:
            path = request.path
        except RuntimeError:
            return "guishu"

    # 微信路径优先匹配
    for prefix, bnb_id in _WECHAT_MAP.items():
        if path.startswith(prefix):
            return bnb_id

    # Web 路径前缀匹配
    for prefix, bnb_id in _PREFIX_MAP.items():
        if path.startswith(prefix + "/") or path == prefix:
            return bnb_id

    # 默认归墅（向后兼容旧路径 /rooms /menu 等）
    return "guishu"


def get_current_bnb() -> dict:
    """获取当前请求的民宿配置，结果缓存在 g 对象"""
    if "bnb_config" not in g:
        bnb_id = get_bnb_id_from_path()
        g.bnb_id = bnb_id
        g.bnb_config = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    return g.bnb_config


def get_current_bnb_id() -> str:
    """获取当前请求/任务的 bnb_id。
    优先级：Flask g > 线程本地 > 路径推断 > "guishu"
    """
    # 1. Flask 请求上下文
    if has_request_context() and hasattr(g, 'bnb_id'):
        return g.bnb_id

    # 2. 线程本地（后台任务 / 非 Flask 环境）
    if hasattr(_thread_local, 'bnb_id'):
        return _thread_local.bnb_id

    # 3. 路径推断（兜底）
    try:
        return get_bnb_id_from_path()
    except RuntimeError:
        pass

    # 4. 最终默认
    logger.warning("bnb_context: 无法确定 bnb_id，fallback 到 guishu — 建议在入口处调用 set_current_bnb()")
    return "guishu"


def get_bnb_config(bnb_id: str) -> dict:
    """按 bnb_id 获取配置，不存在返回归墅默认"""
    return BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])


def get_service_bnb_id(bnb_id: str = None, default: str = "guishu") -> str:
    """服务层统一获取 bnb_id：优先参数 > Flask g > 线程本地 > 默认值。
    当最终使用默认值时会发出 warning，帮助发现遗漏的 bnb_id 传递。
    """
    if bnb_id:
        return bnb_id
    try:
        from flask import g, has_request_context
        if has_request_context() and hasattr(g, 'bnb_id'):
            return g.bnb_id
        if hasattr(_thread_local, 'bnb_id'):
            return _thread_local.bnb_id
    except RuntimeError:
        pass

    logger.warning(f"bnb_context: get_service_bnb_id() fallback 到默认值 '{default}' — 建议显式传入 bnb_id 或调用 set_current_bnb()")
    return default


def get_all_bnbs() -> list[dict]:
    """获取所有活跃民宿配置列表"""
    return [
        {"bnb_id": k, **v}
        for k, v in BNB_CONFIGS.items()
    ]
