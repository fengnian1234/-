"""
云上·归墅 - 配置文件
所有配置项集中管理，敏感信息通过环境变量注入
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 基础配置 ─────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "yunshang-guishu-secret-2024")

# ── 微信配置 ─────────────────────────────────────────────
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN", "your_wechat_token_here")
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY", "")
WECHAT_MCH_ID = os.getenv("WECHAT_MCH_ID", "")         # 微信支付商户号
WECHAT_MCH_KEY = os.getenv("WECHAT_MCH_KEY", "")       # 微信支付API密钥

# ── 数据库配置 ───────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///yunshang_bnb.db")

# ── AI 配置 (Anthropic Claude) ──────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")
AI_ENABLED = bool(ANTHROPIC_API_KEY)
# 重要：AI仅在用户有确认预订后解锁（要求1）
AI_REQUIRES_BOOKING = True

# ── 民宿信息（已修正为文档指定内容）──────────────────────
BNB_NAME = "云上·归墅民宿"
BNB_SHORT_NAME = "云上归墅"
BNB_ADDRESS = "庐山山上·庐山风景名胜区大林沟路27号"
BNB_PHONE = "0792-XXXXXXX"
BNB_LATITUDE = 29.5568
BNB_LONGITUDE = 115.9797

# ── 预订平台链接（要求3：跳转主流平台，不走微信支付订房）─
BOOKING_PLATFORMS = {
    "携程": {
        "name": "携程旅行",
        "url": "https://hotels.ctrip.com/hotel/search?keyword=云上归墅",
        "icon": "🏨",
        "color": "#2577e3",
    },
    "美团": {
        "name": "美团民宿",
        "url": "https://hotel.meituan.com/search?keyword=云上归墅",
        "icon": "🏠",
        "color": "#ffc300",
    },
    "飞猪": {
        "name": "飞猪旅行",
        "url": "https://www.fliggy.com/search?keyword=云上归墅",
        "icon": "✈️",
        "color": "#ff5a00",
    },
    "大众点评": {
        "name": "大众点评",
        "url": "https://www.dianping.com/search/keyword/云上归墅",
        "icon": "⭐",
        "color": "#ffc300",
    },
}

# ── 好评推送配置（要求4：退房30分钟后推送平台评价链接）──
REVIEW_PLATFORMS = {
    "携程": {
        "name": "携程旅行",
        "review_url": "https://hotels.ctrip.com/hotel/dianping/云上归墅",
        "icon": "🏨",
    },
    "美团": {
        "name": "美团",
        "review_url": "https://hotel.meituan.com/dianping/云上归墅",
        "icon": "🏠",
    },
    "飞猪": {
        "name": "飞猪旅行",
        "review_url": "https://www.fliggy.com/review/云上归墅",
        "icon": "✈️",
    },
    "大众点评": {
        "name": "大众点评",
        "review_url": "https://www.dianping.com/shop/云上归墅/review",
        "icon": "⭐",
    },
    "小红书": {
        "name": "小红书",
        "review_url": "https://www.xiaohongshu.com/search_result?keyword=云上归墅",
        "icon": "📕",
    },
    "抖音": {
        "name": "抖音",
        "review_url": "https://www.douyin.com/search/云上归墅",
        "icon": "🎵",
    },
}
# 退房后自动推送好评提醒的延迟（分钟）
REVIEW_REMINDER_DELAY_MINUTES = 30

# ── 平台监控配置（要求6）─────────────────────────────────
MONITOR_PLATFORMS = ["美团", "大众点评", "飞猪", "携程", "小红书", "抖音"]
MONITOR_KEYWORDS = ["云上·归墅", "云上归墅", "庐山民宿", "庐山云上归墅"]
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
🎐 AI管家仅在您确认预订后解锁～"""
