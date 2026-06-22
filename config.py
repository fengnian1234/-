"""
云上·归墅 - 配置文件
所有配置项集中管理，敏感信息通过环境变量注入
"""
import os
from dotenv import load_dotenv

load_dotenv()
# 加载本地覆盖配置（不提交到仓库）
load_dotenv(".env.local", override=True)

# ── 基础配置 ─────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"  # 安全默认：生产关闭
SECRET_KEY = os.getenv("SECRET_KEY", "")
# 若未设置 SECRET_KEY，生成随机密钥（每次重启变化，仅开发可用）
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    import sys
    print("[安全] 未设置 SECRET_KEY，已生成临时随机密钥（重启后失效）", file=sys.stderr)

# ── 微信配置（三民宿各一套）────────────────────────────
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN", "your_wechat_token_here")
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY", "")
WECHAT_MCH_ID = os.getenv("WECHAT_MCH_ID", "")         # 微信支付商户号
WECHAT_MCH_KEY = os.getenv("WECHAT_MCH_KEY", "")       # 微信支付API密钥

# ── 微信小程序配置 ─────────────────────────────────────────
WECHAT_MINI_APP_ID = os.getenv("WECHAT_MINI_APP_ID", "")
WECHAT_MINI_APP_SECRET = os.getenv("WECHAT_MINI_APP_SECRET", "")

# ── 数据库配置 ───────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///yunshang_bnb.db")
# 自动检测数据库类型
DB_TYPE = "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite"
# PostgreSQL 连接池参数（SQLite 忽略）
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_POOL_OVERFLOW = int(os.getenv("DB_POOL_OVERFLOW", "20"))

# ── AI 配置 (DeepSeek / Anthropic Claude 兼容接口) ───────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
AI_ENABLED = bool(ANTHROPIC_API_KEY)
# 重要：AI仅在用户有确认预订后解锁（要求1）
AI_REQUIRES_BOOKING = True
# AI 请求间隔：每 N 秒最多 1 次 AI 请求
AI_REQUEST_INTERVAL = int(os.getenv("AI_REQUEST_INTERVAL", "3"))
# 单条消息最大长度（超过截断，防止 token 浪费）
AI_MAX_MESSAGE_LENGTH = int(os.getenv("AI_MAX_MESSAGE_LENGTH", "500"))

# ── 三民宿配置 ───────────────────────────────────────
BNB_CONFIGS = {
    "guishu": {
        "name": "云上·归墅民宿",
        "short_name": "云上归墅",
        "address": "庐山山上·庐山风景名胜区大林沟路27号",
        "phone": "16607927666",
        "latitude": 29.5568,
        "longitude": 115.9797,
        "theme_color": "#4a7c59",
        "description": "庐山之巅，大林沟路27号，云雾深处的静谧之所。U型三层山居小院，11间精品客房。",
        "wechat_token": os.getenv("WECHAT_TOKEN_GS", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_GS", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_GS", ""),
    },
    "shanji": {
        "name": "云上·山纪民宿",
        "short_name": "云上山纪",
        "address": "庐山山上·庐山风景名胜区XX路XX号",
        "phone": "待填写",
        "latitude": 29.5600,
        "longitude": 115.9850,
        "theme_color": "#8B6914",
        "description": "茶园环绕，品茗观山。庐山云雾茶香，伴你悠然山居时光。",
        "wechat_token": os.getenv("WECHAT_TOKEN_SJ", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_SJ", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_SJ", ""),
    },
    "donglinwai": {
        "name": "云上·东林外民宿",
        "short_name": "云上东林外",
        "address": "庐山山上·庐山风景名胜区XX路XX号",
        "phone": "待填写",
        "latitude": 29.5500,
        "longitude": 115.9700,
        "theme_color": "#7B8DAD",
        "description": "东林寺旁，禅意疗愈之所。放下尘嚣，身心归一。",
        "wechat_token": os.getenv("WECHAT_TOKEN_DLW", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_DLW", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_DLW", ""),
    },
}

# ── 向后兼容别名（旧代码引用 BNB_NAME 等）──────────────
BNB_NAME = BNB_CONFIGS["guishu"]["name"]
BNB_SHORT_NAME = BNB_CONFIGS["guishu"]["short_name"]
BNB_ADDRESS = BNB_CONFIGS["guishu"]["address"]
BNB_PHONE = BNB_CONFIGS["guishu"]["phone"]
BNB_LATITUDE = BNB_CONFIGS["guishu"]["latitude"]
BNB_LONGITUDE = BNB_CONFIGS["guishu"]["longitude"]

# ── 预订平台链接（按民宿区分）────────────────────────
def _make_booking_platforms(bnb_name: str) -> dict:
    """按民宿名称生成预订平台搜索链接"""
    from urllib.parse import quote
    q = quote(bnb_name)
    return {
        "携程": {"name": "携程旅行", "url": f"https://hotels.ctrip.com/hotel/search?keyword={q}", "icon": "🏨", "color": "#2577e3"},
        "美团": {"name": "美团民宿", "url": f"https://hotel.meituan.com/search?keyword={q}", "icon": "🏠", "color": "#ffc300"},
        "飞猪": {"name": "飞猪旅行", "url": f"https://www.fliggy.com/search?keyword={q}", "icon": "✈️", "color": "#ff5a00"},
        "大众点评": {"name": "大众点评", "url": f"https://www.dianping.com/search/keyword/{q}", "icon": "⭐", "color": "#ffc300"},
    }

BOOKING_PLATFORMS = _make_booking_platforms("云上归墅")
BOOKING_PLATFORMS_BY_BNB = {
    k: _make_booking_platforms(v["name"]) for k, v in BNB_CONFIGS.items()
}

def _make_review_platforms(bnb_name: str) -> dict:
    """按民宿名生成好评推送平台链接"""
    from urllib.parse import quote
    q = quote(bnb_name)
    return {
        "携程": {"name": "携程旅行", "review_url": f"https://hotels.ctrip.com/hotel/dianping/{q}", "icon": "🏨"},
        "美团": {"name": "美团", "review_url": f"https://hotel.meituan.com/dianping/{q}", "icon": "🏠"},
        "飞猪": {"name": "飞猪旅行", "review_url": f"https://www.fliggy.com/review/{q}", "icon": "✈️"},
        "大众点评": {"name": "大众点评", "review_url": f"https://www.dianping.com/shop/{q}/review", "icon": "⭐"},
        "小红书": {"name": "小红书", "review_url": f"https://www.xiaohongshu.com/search_result?keyword={q}", "icon": "📕"},
        "抖音": {"name": "抖音", "review_url": f"https://www.douyin.com/search/{q}", "icon": "🎵"},
    }

REVIEW_PLATFORMS = _make_review_platforms("云上归墅")
REVIEW_PLATFORMS_BY_BNB = {
    k: _make_review_platforms(v["name"]) for k, v in BNB_CONFIGS.items()
}
# 退房后自动推送好评提醒的延迟（分钟）
REVIEW_REMINDER_DELAY_MINUTES = 30

# ── 平台监控配置（按民宿区分）──────────────────────
MONITOR_PLATFORMS = ["大众点评", "携程", "小红书", "微博"]
MONITOR_KEYWORDS_BY_BNB = {
    "guishu": ["云上·归墅", "云上归墅", "庐山民宿", "庐山云上归墅"],
    "shanji": ["云上·山纪", "云上山纪", "庐山山纪", "庐山茶园民宿"],
    "donglinwai": ["云上·东林外", "云上东林外", "庐山东林外", "庐山东林民宿"],
}
MONITOR_KEYWORDS = MONITOR_KEYWORDS_BY_BNB["guishu"]
MONITOR_SEARCH_QUERY = "云上·归墅民宿 庐山 评价"

# ── 客服配置 ─────────────────────────────────────────────
HUMAN_SERVICE_OPEN_HOURS = (8, 22)
AUTO_REPLY_NIGHT = "夜深了🌙，云上·归墅已进入梦乡。您的问题我们会在明早8点后第一时间回复，感谢您的理解～"
WELCOME_MESSAGE = """🏔️ 欢迎来到云上·归墅！

庐山之巅，大林沟路27号，云雾深处的静谧之所。

回复以下数字或关键词探索：
【1】🛏️ 房型展示
【2】☕ 咖啡简餐
【3】🗺️ 游玩攻略
【4】🛎️ 快捷服务
【5】💬 在线咨询

🏨 预订请通过携程/美团/飞猪/大众点评搜索「云上归墅」
🎐 预订前免费旅行顾问 · 预订后解锁专属AI管家～"""
