"""
微信消息处理核心
- 接收微信服务器推送的消息
- 关键词匹配自动回复
- 智能路由到各业务服务
"""
import re
from datetime import datetime
from config import (
    WECHAT_TOKEN, WECHAT_APP_ID, WECHAT_APP_SECRET,
    WELCOME_MESSAGE, AUTO_REPLY_NIGHT, HUMAN_SERVICE_OPEN_HOURS,
    BNB_PHONE,
)
from services.rooms import format_rooms_text, format_room_detail_text, format_rooms_with_images
from services.menu import format_menu_text, format_recommended_text, format_order_status_text
from services.travel import (
    format_routes_text, format_route_detail_text,
    format_food_text, format_location_text,
)
from services.quick import format_services_text, handle_service_request
from services.ai import chat, reset_conversation


def is_human_service_time() -> bool:
    """判断当前是否在人工客服时间内"""
    hour = datetime.now().hour
    return HUMAN_SERVICE_OPEN_HOURS[0] <= hour < HUMAN_SERVICE_OPEN_HOURS[1]


# ── 关键词路由表 ─────────────────────────────────────────
# 优先级从高到低匹配
KEYWORD_ROUTES = [
    # 房间相关
    (r"^(房型|房间|客房|住宿|1)$", lambda msg: format_rooms_text()),
    (r"^房间(\d+)$", lambda msg: format_room_detail_text(int(msg.group(1)))),
    (r"^(房间图片|房间照片|看图)$", lambda msg: format_rooms_with_images()),
    (r"^(预订|订房|预约|价格)$", lambda msg: (
        f"📞 *订房热线*\n\n"
        f"☎️ 电话：{BNB_PHONE}\n"
        f"🕐 服务时间：8:00 - 22:00\n\n"
        f"💡 您也可以在“携程”“飞猪”等平台搜索「云上归墅」在线预订～\n"
        f"💡 回复「房型」查看所有房间信息"
    )),

    # 菜单点餐相关
    (r"^(菜单|点餐|吃饭|用餐|美食|2)$", lambda msg: format_menu_text()),
    (r"^(推荐|招牌|特色菜)$", lambda msg: format_recommended_text()),
    (r"^(下单|点单)(.+)$", lambda msg: (
        "🛒 *点餐下单*\n\n"
        f"请直接告知我们您想点的菜品和数量，例如：\n"
        f"「一份庐山石鸡、一份云雾茶」\n\n"
        f"💡 回复「菜单」查看完整菜单\n"
        f"📞 也可拨打 {BNB_PHONE} 电话点餐"
    )),
    (r"^(我的订单|订单|查单)$", lambda msg: format_order_status_text(msg.openid if hasattr(msg, 'openid') else "")),

    # 旅游攻略相关
    (r"^(攻略|游玩|路线|旅游|景点|3)$", lambda msg: format_routes_text()),
    (r"^路线(\d+)$", lambda msg: format_route_detail_text(int(msg.group(1)))),
    (r"^(美食推荐|周边美食|好吃的)$", lambda msg: format_food_text()),
    (r"^(地图|位置|导航|在哪|怎么走|地址)$", lambda msg: format_location_text()),
    (r"^美食(.+)$", lambda msg: (
        f"🍜 关于「{msg.group(1)}」类美食，您可以直接问我，我会为您详细介绍～\n"
        f"或者回复「美食推荐」查看完整美食指南"
    )),

    # 快捷服务相关
    (r"^(服务|快捷|4)$", lambda msg: format_services_text()),
    (r"^(服务|我要)(.+)$", lambda msg: handle_service_request(msg.group(2))),
    (r"^(打扫|清洁|卫生)$", lambda msg: handle_service_request("打扫")),
    (r"^(续住|续房|延住)$", lambda msg: handle_service_request("续住")),
    (r"^(维修|修理|坏了)$", lambda msg: handle_service_request("维修")),
    (r"^(叫醒|叫早|morning.?call)$", lambda msg: handle_service_request("叫醒")),
    (r"^(退房|离店|退宿)$", lambda msg: handle_service_request("退房")),
    (r"^(加床|加被|枕头|毛毯)$", lambda msg: handle_service_request("加床")),
    (r"^(送餐|送饭)$", lambda msg: handle_service_request("送餐")),
    (r"^(wifi|WiFi|无线|网络)$", lambda msg: (
        "📶 *WiFi 信息*\n\n"
        "网络名称：云上归墅\n"
        "密码：yunshang888\n\n"
        "连接后即可畅享高速网络～"
    )),

    # 客服相关
    (r"^(人工|转人工|客服|人工客服|5)$", lambda msg: handle_human_service()),
    (r"^(帮助|help|功能|菜单|说明)$", lambda msg: WELCOME_MESSAGE),
    (r"^(你好|hi|hello|嗨|在吗|您好)$", lambda msg: (
        "您好呀！👋 欢迎来到云上归墅～\n\n"
        "我是您的智能管家，有什么可以帮您的吗？\n"
        "您可以回复以下数字快速查询：\n"
        "【1】房型展示  【2】山间美餐\n"
        "【3】游玩攻略  【4】快捷服务\n"
        "【5】在线咨询\n\n"
        "也可以直接向我提问哦～ ☁️🏔️"
    )),
    (r"^(谢谢|感谢|多谢|3Q|thanks)$", lambda msg: (
        "不客气！祝您在庐山度过美好的时光～ 🌄✨\n"
        "有任何需要随时找我哦！"
    )),
]


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


def match_keyword(content: str):
    """
    匹配关键词路由
    返回 (handler, match_object) 或 (None, None)
    """
    content = content.strip()
    for pattern, handler in KEYWORD_ROUTES:
        m = re.match(pattern, content, re.IGNORECASE)
        if m:
            return handler, m
    return None, None


# ── 微信消息入口 ─────────────────────────────────────────
def handle_wechat_message(msg):
    """
    处理微信消息的主入口
    由 wechatpy 的消息处理器调用

    参数 msg: wechatpy 的消息对象
    返回: 回复文本字符串
    """
    # 获取用户消息内容
    if hasattr(msg, 'content'):
        content = msg.content.strip()
    elif hasattr(msg, 'text'):
        content = msg.text.strip()
    else:
        return WELCOME_MESSAGE

    # 获取用户openid
    openid = getattr(msg, 'source', None) or getattr(msg, 'from_user', 'unknown')

    # 1. 尝试关键词匹配
    handler, match = match_keyword(content)
    if handler:
        try:
            return handler(match if match else msg)
        except Exception as e:
            # 关键词处理失败，降级到AI
            pass

    # 2. 所有关键词都不匹配时，使用AI智能对话
    try:
        ai_reply = chat(str(openid), content)
        return ai_reply
    except Exception:
        pass

    # 3. AI也失败时的兜底
    return (
        "我收到了您的消息～ 💬\n\n"
        "如需帮助，可以：\n"
        "  · 回复数字 1-5 使用快捷功能\n"
        "  · 回复「人工」转接人工客服\n"
        "  · 拨打前台电话咨询\n\n"
        "或直接告诉我您需要什么，我会尽力帮您～"
    )


def handle_event(event_msg):
    """
    处理微信事件推送（关注、取消关注、菜单点击等）
    """
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
        'contact': lambda: handle_human_service(),
        'food': lambda: format_food_text(),
    }

    handler = menu_handlers.get(event_key)
    if handler:
        return handler()

    return WELCOME_MESSAGE
