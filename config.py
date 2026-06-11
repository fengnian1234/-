"""
云上归墅 - 配置文件
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

# ── 数据库配置 ───────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///yunshang_bnb.db")

# ── AI 配置 (Anthropic Claude) ──────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

# ── 民宿信息 ─────────────────────────────────────────────
BNB_NAME = "云上归墅"
BNB_SHORT_NAME = "云上归墅"
BNB_ADDRESS = "江西省九江市庐山市庐山风景区牯岭镇"
BNB_PHONE = "0792-XXXXXXX"
BNB_LATITUDE = 29.5568    # 庐山牯岭镇坐标
BNB_LONGITUDE = 115.9797

# ── 客服配置 ─────────────────────────────────────────────
HUMAN_SERVICE_OPEN_HOURS = (8, 22)  # 人工客服时间 8:00-22:00
AUTO_REPLY_NIGHT = "夜深了🌙，云上归墅已进入梦乡。您的问题我们会在明早8点后第一时间回复，感谢您的理解～"
WELCOME_MESSAGE = """🏔️ 欢迎来到云上归墅！

这里是庐山之巅的静谧之所，云雾缭绕中的温暖归宿。

回复以下数字或关键词探索：
【1】🛏️ 房型展示
【2】🍜 山间美餐
【3】🗺️ 游玩攻略
【4】🛎️ 快捷服务
【5】💬 在线咨询

您也可以直接向我提问～"""
