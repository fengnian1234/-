"""
微信消息处理核心（v2 - 按额外要求文档更新）
- 要求1：AI对话仅在预订确认后解锁
- 要求2：服务请求自动通知员工
- 要求3：预订引导至主流平台，不走微信支付
- 要求4：退房30分钟后自动推送好评
- 要求5：菜单为咖啡简餐 + 微信支付
- 要求6：平台信息收集子Agent
"""
import re
from datetime import datetime
from config import (
    WELCOME_MESSAGE, AUTO_REPLY_NIGHT, HUMAN_SERVICE_OPEN_HOURS,
    BNB_NAME, BNB_ADDRESS, BNB_PHONE,
)
from services.rooms import format_rooms_text, format_room_detail_text, format_rooms_with_images
from services.menu import format_menu_text, format_recommended_text, format_order_status_text
from services.travel import (
    format_routes_text, format_route_detail_text,
    format_food_text, format_food_detail_text, format_location_text,
)
from services.quick import format_services_text, handle_service_request
from services.ai import chat, chat_travel_advisor, chat_post_stay, reset_conversation, get_conversation_mode
from services.booking import (
    is_ai_enabled, format_booking_platforms_text,
    generate_review_message, get_review_reminders_due,
    mark_review_sent,
)
from services.monitor import generate_monitor_report, get_platform_review_links


def is_human_service_time() -> bool:
    """判断当前是否在人工客服时间内"""
    hour = datetime.now().hour
    return HUMAN_SERVICE_OPEN_HOURS[0] <= hour < HUMAN_SERVICE_OPEN_HOURS[1]


def format_welcome() -> str:
    """格式化欢迎消息（区分已预订/未预订用户）"""
    return WELCOME_MESSAGE


# ══════════════════════════════════════════════════════════
#  关键词路由表（v2 - 按额外要求更新）
# ══════════════════════════════════════════════════════════
def build_keyword_routes():
    """构建关键词路由（闭包，方便扩展）"""
    return [
        # ── 房间相关 ─────────────────────────────────────
        (r"^(房型|房间|客房|住宿|1)$",
         lambda msg, m: format_rooms_text()),
        (r"^房间(\d+)$",
         lambda msg, m: format_room_detail_text(int(m.group(1)))),
        (r"^(房间图片|房间照片|看图)$",
         lambda msg, m: format_rooms_with_images()),

        # ── 预订相关（要求3：跳转主流平台）───────────────
        (r"^(预订|订房|预约|房价|价格)$",
         lambda msg, m: format_booking_platforms_text()),
        (r"^(绑定预订|绑定订单|我的预订)$",
         lambda msg, m: handle_bind_booking(msg)),
        (r"^(携程|美团|飞猪|点评)$",
         lambda msg, m: format_booking_platforms_text()),

        # ── 菜单点餐相关（要求5：咖啡简餐+微信支付）─────
        (r"^(菜单|点餐|吃饭|用餐|咖啡|简餐|2)$",
         lambda msg, m: format_menu_text()),
        (r"^(推荐|招牌|特色)$",
         lambda msg, m: format_recommended_text()),
        (r"^(下单|点单)(.+)$",
         lambda msg, m: handle_order_flow(msg, m)),
        (r"^(我的订单|订单|查单)$",
         lambda msg, m: format_order_status_text(
             str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown'))))),

        # ── 旅游攻略相关 ─────────────────────────────────
        (r"^(攻略|游玩|路线|旅游|景点|3)$",
         lambda msg, m: format_routes_text()),
        (r"^路线(\d+)$",
         lambda msg, m: format_route_detail_text(int(m.group(1)))),
        (r"^(美食推荐|周边美食|好吃的|餐厅|正餐)$",
         lambda msg, m: format_food_text()),
        (r"^美食(\d+)$",
         lambda msg, m: format_food_detail_text(int(m.group(1)))),
        (r"^(地图|位置|导航|在哪|怎么走|地址)$",
         lambda msg, m: format_location_text()),
        (r"^美食(.+)$",
         lambda msg, m: f"🍜 关于「{m.group(1)}」类美食，回复「周边美食」查看完整美食指南～\n\n💡 回复「美食+编号」如「美食7」查看饮品店详情～"),

        # ── 快捷服务相关（要求2：通知员工）───────────────
        (r"^(服务|快捷|4)$",
         lambda msg, m: format_services_text()),
        (r"^(服务|我要)(.+)$",
         lambda msg, m: handle_service_request(m.group(2),
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(打扫|清洁|卫生)$",
         lambda msg, m: handle_service_request("打扫",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(续住|续房|延住)$",
         lambda msg, m: handle_service_request("续住",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(维修|修理|坏了)$",
         lambda msg, m: handle_service_request("维修",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(叫醒|叫早|morning.?call)$",
         lambda msg, m: handle_service_request("叫醒",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(退房|离店|退宿)$",
         lambda msg, m: handle_service_request("退房",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(加床|加被|婴儿床|儿童床)$",
         lambda msg, m: "🛏️ 温馨提示：本民宿所有房型<strong>不可加床</strong>，不提供婴儿床。\n\n如需额外被褥枕头，可回复「补充用品」或「人工」联系前台～"),
        (r"^(送餐|送饭)$",
         lambda msg, m: handle_service_request("送餐",
             openid=str(getattr(msg, 'source', getattr(msg, 'from_user', ''))))),
        (r"^(wifi|WiFi|无线|网络)$",
         lambda msg, m: format_wifi_info()),

        # ── 平台口碑相关（要求6）─────────────────────────
        (r"^(口碑|评价|评分|声誉)$",
         lambda msg, m: generate_monitor_report()),
        (r"^(平台评价|好评链接|评价链接)$",
         lambda msg, m: format_review_links()),

        # ── 客服相关 ─────────────────────────────────────
        (r"^(人工|转人工|客服|人工客服|5)$",
         lambda msg, m: handle_human_service()),
        (r"^(帮助|help|功能|菜单|说明)$",
         lambda msg, m: format_welcome()),
        (r"^(你好|hi|hello|嗨|在吗|您好)$",
         lambda msg, m: format_greeting()),
        (r"^(谢谢|感谢|多谢|3Q|thanks)$",
         lambda msg, m: "不客气！祝您在庐山度过美好的时光～ 🌄✨\n有任何需要随时找我哦！"),
    ]


# ══════════════════════════════════════════════════════════
#  辅助处理函数
# ══════════════════════════════════════════════════════════
def handle_bind_booking(msg) -> str:
    """处理预订绑定请求（要求1：解锁AI的前提）"""
    openid = str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown')))

    if is_ai_enabled(openid):
        return (
            "✅ 您的专属AI管家已就绪～\n\n"
            "有什么可以帮您的吗？可以直接向我提问哦！"
        )

    return (
        "🔗 *绑定预订*\n\n"
        "请在以下平台预订后，联系前台确认预订即可解锁专属AI管家：\n\n"
        "🏨 携程 | 🏠 美团 | ✈️ 飞猪 | ⭐ 大众点评\n"
        "  搜索「云上·归墅」\n\n"
        "💡 前台确认预订后，专属AI管家自动解锁\n"
        "💡 现在就可以免费使用旅行顾问～直接问我庐山攻略\n"
        "💡 回复「预订」查看各平台预订链接\n"
        "💡 回复「人工」联系前台确认绑定"
    )


def handle_order_flow(msg, m) -> str:
    """处理点餐下单"""
    items_text = m.group(2).strip()
    return (
        "☕ *点餐下单*\n\n"
        f"您想点：{items_text}\n\n"
        "请点击下方链接进入点餐页面\n"
        "选择菜品后可直接微信支付 💳\n\n"
        f"📱 点餐页面：{_get_menu_url()}\n\n"
        "💡 回复「菜单」查看完整菜单\n"
        "💡 回复「推荐」查看今日推荐"
    )


def _get_menu_url() -> str:
    from config import BASE_URL
    return f"{BASE_URL}/menu"


def format_wifi_info() -> str:
    return (
        "📶 *WiFi 信息*\n\n"
        "网络名称：云上·归墅\n"
        "密码：yunshang888\n\n"
        "连接后即可畅享高速网络～"
    )


def format_greeting() -> str:
    return (
        "您好呀！👋 欢迎来到云上·归墅～\n\n"
        "我是您的智能管家，有什么可以帮您的吗？\n"
        "您可以回复以下数字快速查询：\n"
        "【1】房型展示  【2】咖啡简餐\n"
        "【3】游玩攻略  【4】快捷服务\n"
        "【5】在线咨询\n\n"
        "💡 预订请通过携程/美团/飞猪/大众点评\n"
        "🎐 预订确认后解锁专属AI管家～预订前也能免费使用旅行顾问哦～"
    )


def handle_human_service() -> str:
    """处理人工客服转接"""
    if is_human_service_time():
        return (
            "正在为您转接人工客服... 👩‍💼\n\n"
            f"☎️ 也可直接拨打前台电话：{BNB_PHONE}\n"
            "🕐 人工客服在线时间：8:00 - 22:00\n\n"
            "请稍候，客服马上为您服务～"
        )
    else:
        return AUTO_REPLY_NIGHT


def format_review_links() -> str:
    """格式化各平台好评链接（要求4）"""
    lines = ["⭐ *各平台评价入口*\n"]
    platforms = get_platform_review_links()
    for key, info in platforms.items():
        lines.append(f"{info['icon']} *{info['name']}*")
        lines.append(f"  {info['review_url']}\n")

    lines.append("💡 您的每一条评价都是对我们最大的鼓励～🙏")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  消息匹配与路由
# ══════════════════════════════════════════════════════════
KEYWORD_ROUTES = build_keyword_routes()


def match_keyword(content: str):
    """匹配关键词路由"""
    content = content.strip()
    for pattern, handler in KEYWORD_ROUTES:
        m = re.match(pattern, content, re.IGNORECASE)
        if m:
            return handler, m
    return None, None


# ══════════════════════════════════════════════════════════
#  微信消息主入口
# ══════════════════════════════════════════════════════════
def handle_wechat_message(msg):
    """
    处理微信消息的主入口
    路由优先级：关键词匹配 > AI对话（需预订） > 兜底
    """
    # 获取用户消息内容
    if hasattr(msg, 'content'):
        content = msg.content.strip()
    elif hasattr(msg, 'text'):
        content = msg.text.strip()
    else:
        return WELCOME_MESSAGE

    openid = str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown')))

    # 1. 尝试关键词匹配
    handler, match = match_keyword(content)
    if handler:
        try:
            return handler(msg, match)
        except Exception:
            pass  # 关键词失败，降级

    # 2. AI智能对话（v3 全链路：预订前旅行顾问 / 预订后专属管家 / 离店后复购关怀）
    try:
        mode = get_conversation_mode(openid)
        if mode == 'travel_advisor':
            ai_reply = chat_travel_advisor(openid, content)
        elif mode == 'post_stay':
            ai_reply = chat_post_stay(openid, content)
        else:
            ai_reply = chat(openid, content)
        return ai_reply
    except Exception:
        pass

    # 3. 兜底回复
    return (
        "我收到了您的消息～ 💬\n\n"
        "如需帮助，可以：\n"
        "  · 回复数字 1-5 使用快捷功能\n"
        "  · 回复「人工」转接人工客服\n"
        "  · 回复「预订」查看平台预订链接\n"
        "  · 拨打前台电话咨询\n\n"
        "或直接告诉我您需要什么，我会尽力帮您～"
    )


# ══════════════════════════════════════════════════════════
#  事件处理（关注/菜单点击）
# ══════════════════════════════════════════════════════════
def handle_event(event_msg):
    """处理微信事件推送"""
    event_type = getattr(event_msg, 'event', '')

    if event_type == 'subscribe':
        return WELCOME_MESSAGE
    elif event_type == 'unsubscribe':
        return ""
    elif event_type == 'CLICK':
        event_key = getattr(event_msg, 'key', '')
        return handle_menu_click(event_key)
    elif event_type == 'SCAN':
        return WELCOME_MESSAGE

    return ""


def handle_menu_click(event_key: str) -> str:
    """处理自定义菜单点击"""
    menu_handlers = {
        'rooms': lambda: format_rooms_text(),
        'menu': lambda: format_menu_text(),
        'travel': lambda: format_routes_text(),
        'service': lambda: format_services_text(),
        'location': lambda: format_location_text(),
        'booking': lambda: format_booking_platforms_text(),
        'contact': lambda: handle_human_service(),
        'food': lambda: format_food_text(),
        'reviews': lambda: generate_monitor_report(),
    }

    handler = menu_handlers.get(event_key)
    if handler:
        return handler()

    return WELCOME_MESSAGE


# ══════════════════════════════════════════════════════════
#  定时任务：退房好评推送检查（要求4）
# ══════════════════════════════════════════════════════════
def check_and_send_review_reminders():
    """
    检查是否有需要推送好评提醒的退房记录
    此函数应由定时任务（如cron/APScheduler）每分钟调用
    """
    from models import SessionLocal

    due_bookings = get_review_reminders_due()
    results = []

    for booking in due_bookings:
        # 生成好评推送消息
        message = generate_review_message(booking)

        # 实际发送：通过微信客服消息API推送
        # send_wechat_customer_message(booking.openid, message)

        # 标记已发送
        mark_review_sent(booking.id, booking.platform or "")

        results.append({
            "openid": booking.openid,
            "guest_name": booking.guest_name,
            "platform": booking.platform,
            "sent_at": datetime.utcnow().isoformat(),
        })

    return results
