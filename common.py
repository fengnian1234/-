"""
共享工具模块 — 零 Flask app 依赖，可被所有路由模块安全导入
"""
import time
from functools import wraps
from flask import request, jsonify
from services.logger import warning
from config import STAFF_API_KEY, STAFF_AUTH_REQUIRED


# ── 员工鉴权装饰器 ───────────────────────────────────────
def _require_staff_auth(f):
    """保护敏感管理API：需要 X-Staff-Key 请求头匹配 STAFF_API_KEY"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not STAFF_AUTH_REQUIRED:
            return f(*args, **kwargs)
        api_key = request.headers.get("X-Staff-Key", "")
        if not api_key or api_key != STAFF_API_KEY:
            warning(f"[AUTH] 未授权访问尝试: {request.path} from {request.remote_addr}")
            return jsonify({"success": False, "message": "未授权访问"}), 401
        return f(*args, **kwargs)
    return decorated


# ── 简易限流（内存，单进程） ──────────────────────────────
import threading

_rate_limit_store = {}
_rate_limit_lock = threading.Lock()


def rate_limit(key: str, max_req: int = 10, window: int = 60) -> bool:
    """简单的滑动窗口限流。返回 True 表示未超限。"""
    now = time.time()
    with _rate_limit_lock:
        if key not in _rate_limit_store:
            _rate_limit_store[key] = []
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window]
        if len(_rate_limit_store[key]) >= max_req:
            return False
        _rate_limit_store[key].append(now)
    return True
