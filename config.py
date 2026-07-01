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

# ── 员工鉴权（保护预订管理/退房等敏感操作）─────────────────
STAFF_API_KEY = os.getenv("STAFF_API_KEY", "")
# 如果未设置，在 DEBUG 模式下允许本地请求通过，生产模式拒绝所有未鉴权请求
STAFF_AUTH_REQUIRED = not DEBUG or bool(STAFF_API_KEY)

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
# AI 请求间隔：每 N 秒最多 1 次 AI 请求（全局限流，改为per-user限流后此处作为兜底）
AI_REQUEST_INTERVAL = float(os.getenv("AI_REQUEST_INTERVAL", "0.5"))
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
        "theme_color": "#7B5D3B",  # 茶褐 — 陈年普洱，温润沉稳
        "tagline": "U型三层山居小院 · 11间客房",
        "footer_poems": {
            "spring": "云无心以出岫，鸟倦飞而知还",
            "summer": "云无心以出岫，鸟倦飞而知还",
            "autumn": "山山唯落晖，树树皆秋色",
            "winter": "庐山雪霁处，疑是玉京来",
        },
        "room_count": 11,
        "cafe_name": "三山二水咖啡",
        "description": "庐山之巅，大林沟路27号，云雾深处的静谧之所。U型三层山居小院，11间精品客房。",
        "short_description": "大林沟路27号 · 云雾深处 · 11间山居客房",
        "wifi_ssid": "云上·归墅",
        "wifi_password": os.getenv("WIFI_PASSWORD_GS", "yunshang888"),
        "extra_bed_policy": "本民宿所有房型不可加床，不提供婴儿床",
        "wechat_token": os.getenv("WECHAT_TOKEN_GS", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_GS", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_GS", ""),
    },
    "shanji": {
        "name": "云上·山纪民宿",
        "short_name": "云上山纪",
        "address": "庐山山上·庐山风景名胜区慧远路104号",
        "phone": "19880281717",
        "latitude": 29.572595,
        "longitude": 115.978075,
        "theme_color": "#2C4335",
        "tagline": "30间客房 · 私享300平花园庭院",
        "footer_poems": {
            "spring": "山中何事？松花酿酒，春水煎茶",
            "summer": "山中何事？松花酿酒，春水煎茶",
            "autumn": "茶鼎夜烹千古雪，花影晨动九天风",
            "winter": "寒夜客来茶当酒，竹炉汤沸火初红",
        },
        "room_count": 30,
        "cafe_name": "云上茶吧",
        "description": "位于景区中心，距索道出口步行3分钟，牯岭街步行8分钟。30间精品客房，私享300平米户外花园庭院。咖啡书吧、云上茶吧、山货餐厅，星级酒店标准打造，提供贴心管家服务。",
        "short_description": "索道出口步行3分钟 · 30间客房 · 300㎡花园庭院 · 咖啡书吧 & 云上茶吧",
        "wifi_ssid": "云上·山纪",
        "wifi_password": os.getenv("WIFI_PASSWORD_SJ", "yunshang888"),
        "extra_bed_policy": "部分房型可加床（¥150/晚），请提前联系前台确认",
        "wechat_token": os.getenv("WECHAT_TOKEN_SJ", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_SJ", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_SJ", ""),
    },
    "donglinwai": {
        "name": "云上·东林外民宿",
        "short_name": "云上东林外",
        "address": "庐山山下·九江濂溪区赛阳镇赛阳路8号",
        "phone": "18807028687",
        "latitude": 29.595012,
        "longitude": 115.940758,
        "theme_color": "#4A5D78",
        "tagline": "东林寺旁 · 禅意疗愈 · 宠物友好",
        "footer_poems": {
            "spring": "曲径通幽处，禅房花木深",
            "summer": "曲径通幽处，禅房花木深",
            "autumn": "山光悦鸟性，潭影空人心",
            "winter": "万籁此都寂，但余钟磬音",
        },
        "room_count": 20,
        "cafe_name": "东林外咖啡",
        "description": "东林寺旁，禅意疗愈之所。20间禅房式客房，禅拍律动/铜锣沐心/五音涤尘/僧厨素斋/晨钟暮课。专属疗愈师定制精力管理营，可携带宠物，免费洗衣。放下尘嚣，身心归一。",
        "short_description": "东林寺旁 · 20间禅房 · 禅拍/铜锣/素斋/暮课 · 疗愈师定制 · 宠物友好",
        "wifi_ssid": "云上·东林外",
        "wifi_password": os.getenv("WIFI_PASSWORD_DLW", "yunshang888"),
        "extra_bed_policy": "部分禅房可加蒲团地铺（¥100/晚），请提前联系前台确认",
        "wechat_token": os.getenv("WECHAT_TOKEN_DLW", ""),
        "wechat_app_id": os.getenv("WECHAT_APP_ID_DLW", ""),
        "wechat_app_secret": os.getenv("WECHAT_APP_SECRET_DLW", ""),
    },
}

# ── 向后兼容别名（DEPRECATED：始终为归墅值，多 BnB 场景请用 BNB_CONFIGS[bnb_id] 或 bnb_context）──
BNB_NAME = BNB_CONFIGS["guishu"]["name"]
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
        "携程": {"name": "携程旅行", "url": f"https://hotels.ctrip.com/hotel/search?keyword={q}", "icon": "·", "color": "#2577e3"},
        "美团": {"name": "美团民宿", "url": f"https://hotel.meituan.com/search?keyword={q}", "icon": "·", "color": "#ffc300"},
        "飞猪": {"name": "飞猪旅行", "url": f"https://www.fliggy.com/search?keyword={q}", "icon": "·", "color": "#ff5a00"},
        "大众点评": {"name": "大众点评", "url": f"https://www.dianping.com/search/keyword/{q}", "icon": "★", "color": "#ffc300"},
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
        "携程": {"name": "携程旅行", "review_url": f"https://hotels.ctrip.com/hotel/dianping/{q}", "icon": "·"},
        "美团": {"name": "美团", "review_url": f"https://hotel.meituan.com/dianping/{q}", "icon": "·"},
        "飞猪": {"name": "飞猪旅行", "review_url": f"https://www.fliggy.com/review/{q}", "icon": "·"},
        "大众点评": {"name": "大众点评", "review_url": f"https://www.dianping.com/shop/{q}/review", "icon": "★"},
        "小红书": {"name": "小红书", "review_url": f"https://www.xiaohongshu.com/search_result?keyword={q}", "icon": "·"},
        "抖音": {"name": "抖音", "review_url": f"https://www.douyin.com/search/{q}", "icon": "·"},
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
# ── 客服配置 ─────────────────────────────────────────────
HUMAN_SERVICE_OPEN_HOURS = (8, 22)
AUTO_REPLY_NIGHT = "夜深了·，{short_name}已进入梦乡。您的问题我们会在明早8点后第一时间回复，感谢您的理解～"
# WELCOME_MESSAGE — DEPRECATED since v3.7（wechat.py 改用 _welcome_for_bnb() 按 BnB 动态生成）
# 保留仅作参考，新增代码禁止使用此常量
