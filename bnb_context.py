"""
BnB 上下文管理器 — 从请求路径提取民宿标识，注入 Flask g 对象
三家民宿：guishu(归墅) / shanji(山纪) / donglinwai(东林外)
"""
from flask import g, request
from config import BNB_CONFIGS

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
    """获取当前请求的 bnb_id"""
    if "bnb_id" not in g:
        g.bnb_id = get_bnb_id_from_path()
    return g.bnb_id


def get_bnb_config(bnb_id: str) -> dict:
    """按 bnb_id 获取配置，不存在返回归墅默认"""
    return BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])


def get_all_bnbs() -> list[dict]:
    """获取所有活跃民宿配置列表"""
    return [
        {"bnb_id": k, **v}
        for k, v in BNB_CONFIGS.items()
    ]
