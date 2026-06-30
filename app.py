"""
云上·归墅 - 微信公众号客服系统
Flask 主应用入口 — 初始化 + 生命周期钩子
路由分发: views.py (页面) / api_routes.py (JSON API) / wechat_routes.py (微信XML)
"""
from flask import Flask, request, render_template, g
from services.logger import info, warning
from config import DEBUG, SECRET_KEY, BNB_NAME, BNB_CONFIGS
from seed_data import seed_all
from bnb_context import get_current_bnb, get_current_bnb_id, get_bnb_id_from_path, set_current_bnb

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ── CORS 支持（限制来源）──────────────────────────────────
@app.after_request
def add_cors_headers(response):
    # 仅允许已知可信来源
    trusted = [
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "https://yunshangguishu.com",
    ]
    origin = request.headers.get("Origin", "")
    if origin and origin in trusted:
        response.headers["Access-Control-Allow-Origin"] = origin
    # 生产模式不允许任意跨域
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Staff-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return app.make_default_options_response()


# ── BnB 上下文注入 ──────────────────────────────────────
@app.before_request
def set_bnb_context():
    """在每次请求前注入当前民宿标识到 Flask g 对象"""
    g.bnb_id = get_bnb_id_from_path(request.path)
    g.bnb_config = get_current_bnb()


# ── 模板全局变量注入 ───────────────────────────────────
@app.context_processor
def inject_bnb():
    """所有 Jinja2 模板自动获得 bnb / bnb_id / bnb_prefix / request_path 变量"""
    bnb_id = get_current_bnb_id()
    prefix_map = {"guishu": "/gs", "shanji": "/sj", "donglinwai": "/dlw"}
    return {
        "bnb": get_current_bnb(),
        "bnb_id": bnb_id,
        "bnb_prefix": prefix_map.get(bnb_id, ""),
        "BNB_CONFIGS": BNB_CONFIGS,
        "request_path": request.path,
    }


# ── 错误页面 ─────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ── BnB 上下文注入 ───────────────────────────────────────
@app.before_request
def _inject_bnb_context():
    """每个请求开始时自动注入 BnB 上下文（路径解析 → Flask g）"""
    set_current_bnb(get_bnb_id_from_path())


# ── 应用初始化 ───────────────────────────────────────────
def init_app():
    """初始化应用：创建数据库并填充种子数据"""
    info(f"🌄 正在初始化{BNB_NAME}客服系统...")
    try:
        seed_all()
    except Exception as e:
        warning(f"⚠️ 数据库初始化: {e}")
    info(f"✅ {BNB_NAME} 客服系统已就绪")


# ── 路由注册（底部导入，标准 Flask 循环导入模式）─────────
import views          # noqa: E402 — 页面渲染路由
import api_routes     # noqa: E402 — JSON API 路由
import wechat_routes  # noqa: E402 — 微信 XML 路由


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_app()
    info(f"🏔️  {BNB_NAME} 微信公众号客服系统 v2")
    info(f"📍 本地访问: http://127.0.0.1:5000")
    info(f"📍 微信接入: http://你的域名/wechat")
    info(f"📍 员工看板: http://127.0.0.1:5000/staff")
    info(f"📍 平台口碑: http://127.0.0.1:5000/api/monitor/report")
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
