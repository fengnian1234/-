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
    AUTO_REPLY_NIGHT, HUMAN_SERVICE_OPEN_HOURS,
    BNB_PHONE, BNB_CONFIGS,
)
from services.rooms import format_rooms_text, format_room_detail_text, format_rooms_with_images
from services.menu import format_menu_text, format_recommended_text, format_order_status_text
from services.travel import (
    format_routes_text, format_route_detail_text,
    format_food_text, format_food_detail_text, format_location_text,
)
from services.quick import format_services_text, handle_service_request
from services.ai import chat, chat_pre_arrival, chat_travel_advisor, chat_post_stay, continue_reply, reset_conversation, get_conversation_mode
from services.booking import (
    is_ai_enabled, is_checked_in, format_booking_platforms_text,
    generate_review_message, get_review_reminders_due,
    mark_review_sent, bind_room_guest, get_room_guests,
)
from services.monitor import generate_monitor_report, get_platform_review_links
from services.logger import info, warning, error as log_error, debug, log_keyword, log_booking


def _get_openid(msg) -> str:
    """从微信消息对象提取 openid"""
    return str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown')))


def _require_booking_reply(bnb_id: str = "guishu") -> str:
    """未预订用户尝试使用住店服务时的统一回复"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    return (
        "🎐 这是入住后才能使用的服务哦～\n\n"
        "您目前还没有确认的预订记录。\n\n"
        f"🏨 预订方式：携程/美团/飞猪/大众点评搜索「{cfg['short_name']}」\n"
        "💡 预订后回复「绑定预订」，联系前台确认即可解锁全部住店服务\n\n"
        "不过在预订之前，您可以：\n"
        "  · 直接问我任何庐山旅游问题\n"
        "  · 回复「1」查看房型\n"
        "  · 回复「3」查看游玩攻略\n"
        "  · 回复「人工」联系前台咨询"
    )


def _require_check_in_reply(openid: str, bnb_id: str = "guishu") -> str:
    """已预订但未入住的用户尝试使用住店服务时的回复"""
    from services.booking import get_booking_by_openid
    booking = get_booking_by_openid(openid, bnb_id=bnb_id)
    check_in = booking.get('check_in_date', '待确认') if booking else '待确认'
    return (
        f"🎐 这些服务需要您到店入住后才能使用哦～\n\n"
        f"📅 您的入住日期：{check_in}\n"
        f"🛎️ 期待您入住后再为您安排！\n\n"
        f"在到店之前，您可以：\n"
        f"  · 了解房型设施和房间详情\n"
        f"  · 规划庐山游玩路线\n"
        f"  · 查看周边美食推荐\n"
        f"  · 告知到店偏好（交通方式、预计到达时间等）\n"
        f"  · 回复「4」查看全部服务菜单提前了解\n\n"
        f"💡 有任何问题随时问我～"
    )


def _guard_service(service_name: str, bnb_id: str = "guishu"):
    """
    包装服务请求处理：先检查是否已实际入住，未入住则拒绝。
    """
    def handler(msg, match):
        openid = _get_openid(msg)
        if not is_ai_enabled(openid, bnb_id=bnb_id):
            return _require_booking_reply(bnb_id=bnb_id)
        if not is_checked_in(openid, bnb_id=bnb_id):
            return _require_check_in_reply(openid, bnb_id=bnb_id)
        return handle_service_request(service_name, openid=openid, bnb_id=bnb_id)
    return handler


def _guard_service_capture(msg, match, bnb_id: str = "guishu"):
    """
    处理「服务+名称」类关键词（含捕获组）。
    先检查是否已实际入住，未入住则拒绝。
    """
    openid = _get_openid(msg)
    if not is_ai_enabled(openid, bnb_id=bnb_id):
        return _require_booking_reply(bnb_id=bnb_id)
    if not is_checked_in(openid, bnb_id=bnb_id):
        return _require_check_in_reply(openid, bnb_id=bnb_id)
    return handle_service_request(match.group(2), openid=openid, bnb_id=bnb_id)


def is_human_service_time() -> bool:
    """判断当前是否在人工客服时间内"""
    hour = datetime.now().hour
    return HUMAN_SERVICE_OPEN_HOURS[0] <= hour < HUMAN_SERVICE_OPEN_HOURS[1]


def format_welcome(bnb_id="guishu") -> str:
    """格式化欢迎消息（按民宿）"""
    return _welcome_for_bnb(bnb_id)


# ══════════════════════════════════════════════════════════
#  关键词路由表（v2 - 按额外要求更新）
# ══════════════════════════════════════════════════════════
def build_keyword_routes(bnb_id="guishu"):
    """构建关键词路由（闭包，方便扩展）"""
    return [
        # ── 房间相关 ─────────────────────────────────────
        (r"^(房型|房间|客房|住宿|1)$",
         lambda msg, m: format_rooms_text(bnb_id=bnb_id)),
        (r"^房间(\d+)$",
         lambda msg, m: format_room_detail_text(int(m.group(1)), bnb_id=bnb_id)),
        (r"^(房间图片|房间照片|看图)$",
         lambda msg, m: format_rooms_with_images(bnb_id=bnb_id)),

        # ── 预订相关（要求3：跳转主流平台）───────────────
        (r"^(预订|订房|预约|房价|价格)$",
         lambda msg, m: format_booking_platforms_text(bnb_id=bnb_id)),
        (r"^(绑定预订|绑定订单|我的预订)$",
         lambda msg, m: handle_bind_booking(msg)),
        (r"^绑定房间\s*(\S+)$",
         lambda msg, m: handle_bind_room_code(msg, m.group(1))),
        (r"^(房间码|共享码|分享房间)$",
         lambda msg, m: handle_show_room_code(msg)),
        (r"^(携程|美团|飞猪|点评)$",
         lambda msg, m: format_booking_platforms_text(bnb_id=bnb_id)),

        # ── 菜单点餐相关（要求5：咖啡简餐+微信支付）─────
        (r"^(菜单|点餐|吃饭|用餐|咖啡|简餐|2)$",
         lambda msg, m: format_menu_text(bnb_id=bnb_id)),
        (r"^(推荐|招牌|特色)$",
         lambda msg, m: format_recommended_text(bnb_id=bnb_id)),
        (r"^(下单|点单)(.+)$",
         lambda msg, m: handle_order_flow(msg, m)),
        (r"^(我的订单|订单|查单)$",
         lambda msg, m: format_order_status_text(
             str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown'))), bnb_id=bnb_id)),

        # ── 旅游攻略相关 ─────────────────────────────────
        (r"^(攻略|游玩|路线|旅游|景点|3)$",
         lambda msg, m: format_routes_text(bnb_id=bnb_id)),
        (r"^路线(\d+)$",
         lambda msg, m: format_route_detail_text(int(m.group(1)), bnb_id=bnb_id)),
        (r"^(美食推荐|周边美食|好吃的|餐厅|正餐)$",
         lambda msg, m: format_food_text(bnb_id=bnb_id)),
        (r"^美食(\d+)$",
         lambda msg, m: format_food_detail_text(int(m.group(1)), bnb_id=bnb_id)),
        (r"^(地图|位置|导航|在哪|怎么走|地址)$",
         lambda msg, m: format_location_text(bnb_id=bnb_id)),
        (r"^美食(.+)$",
         lambda msg, m: f"🍜 关于「{m.group(1)}」类美食，回复「周边美食」查看完整美食指南～\n\n💡 回复「美食+编号」如「美食7」查看饮品店详情～"),

        # ── 快捷服务相关（要求2：通知员工，需预订后才能使用）─
        (r"^(服务|快捷|4)$",
         lambda msg, m: format_services_text(bnb_id=bnb_id)),
        (r"^(服务|我要)(.+)$",
         lambda msg, m: _guard_service_capture(msg, m, bnb_id=bnb_id)),
        (r"^(打扫|清洁|卫生)$",
         lambda msg, m: _guard_service("打扫", bnb_id=bnb_id)(msg, m)),
        (r"^(续住|续房|延住)$",
         lambda msg, m: handle_extend_stay(msg, bnb_id=bnb_id)),
        (r"^(维修|修理|坏了)$",
         lambda msg, m: _guard_service("维修", bnb_id=bnb_id)(msg, m)),
        (r"^(叫醒|叫早|morning.?call)$",
         lambda msg, m: _guard_service("叫醒", bnb_id=bnb_id)(msg, m)),
        (r"^(退房|离店|退宿)$",
         lambda msg, m: _guard_service("退房", bnb_id=bnb_id)(msg, m)),
        (r"^(加床|加被|婴儿床|儿童床)$",
         lambda msg, m: "🛏️ 温馨提示：本民宿所有房型不可加床，不提供婴儿床。\n\n如需额外被褥枕头，可回复「补充用品」或「人工」联系前台～"),
        (r"^(送餐|送饭)$",
         lambda msg, m: _guard_service("送餐", bnb_id=bnb_id)(msg, m)),
        (r"^(wifi|WiFi|无线|网络)$",
         lambda msg, m: format_wifi_info(bnb_id=bnb_id)),

        # ── 茶园相关（山纪专属）──────────────────────────
        (r"^(茶|茶园|品茶|茶叶|制茶|茶道|茶文化)$",
         lambda msg, m: _tea_or_fallback(bnb_id)),
        (r"^(茶园体验|采茶|制茶体验)$",
         lambda msg, m: _tea_or_fallback(bnb_id)),

        # ── 疗愈相关（东林外专属）─────────────────────────
        (r"^(疗愈|SPA|spa|禅修|冥想|瑜伽|按摩|身心)$",
         lambda msg, m: _healing_or_fallback(bnb_id)),
        (r"^(东林|禅意|禅堂)$",
         lambda msg, m: _healing_or_fallback(bnb_id)),

        # ── 平台口碑相关（要求6）─────────────────────────
        (r"^(口碑|评价|评分|声誉)$",
         lambda msg, m: generate_monitor_report(bnb_id=bnb_id)),
        (r"^(平台评价|好评链接|评价链接)$",
         lambda msg, m: format_review_links(bnb_id=bnb_id)),

        # ── 客服相关 ─────────────────────────────────────
        (r"^(人工|转人工|客服|人工客服|5)$",
         lambda msg, m: handle_human_service(bnb_id=bnb_id)),
        (r"^(帮助|help|功能|菜单|说明)$",
         lambda msg, m: format_welcome(bnb_id=bnb_id)),
        (r"^(你好|hi|hello|嗨|在吗|您好)$",
         lambda msg, m: format_greeting(bnb_id=bnb_id)),
        (r"^(谢谢|感谢|多谢|3Q|thanks)$",
         lambda msg, m: "不客气！祝您在庐山度过美好的时光～ 🌄✨\n有任何需要随时找我哦！"),
        (r"^(继续|继续生成|续写)$",
         lambda msg, m: handle_continue(msg)),
    ]


# ══════════════════════════════════════════════════════════
#  辅助处理函数
# ══════════════════════════════════════════════════════════
def handle_bind_booking(msg) -> str:
    """处理预订绑定请求（要求1：解锁AI的前提）"""
    openid = str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown')))
    from bnb_context import get_current_bnb_id
    bnb_id = get_current_bnb_id()
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])

    if is_ai_enabled(openid, bnb_id=bnb_id):
        from services.booking import get_booking_by_openid
        booking = get_booking_by_openid(openid, bnb_id=bnb_id)
        room_code = booking.get("room_code", "") if booking else ""
        lines = [
            "✅ 您的专属AI管家已就绪～",
            "",
            "有什么可以帮您的吗？可以直接向我提问哦！",
        ]
        if room_code:
            lines.append("")
            lines.append(f"🔑 房间共享码：{room_code}")
            lines.append(f"💡 同住人回复「绑定房间 {room_code}」即可共享管家全部功能～")
            lines.append("   您可以回复「房间码」随时查看已绑定的同住人")
        return "\n".join(lines)

    return (
        "🔗 *绑定预订*\n\n"
        "请在以下平台预订后，联系前台确认预订即可解锁专属AI管家：\n\n"
        "🏨 携程 | 🏠 美团 | ✈️ 飞猪 | ⭐ 大众点评\n"
        f"  搜索「{cfg['short_name']}」\n\n"
        "💡 前台确认预订后，专属AI管家自动解锁\n"
        "💡 现在就可以免费使用旅行顾问～直接问我庐山攻略\n"
        "💡 回复「预订」查看各平台预订链接\n"
        "💡 回复「人工」联系前台确认绑定"
    )


def handle_bind_room_code(msg, room_code: str) -> str:
    """合住人通过房间码绑定AI管家"""
    openid = _get_openid(msg)
    result = bind_room_guest(room_code.upper(), openid)

    if result["success"]:
        return (
            f"🔑 {result['message']}\n\n"
            f"🏠 房型：{result['booking'].get('room_type', '未知')}\n"
            f"📅 入住：{result['booking'].get('check_in_date', '')}\n"
            f"🛎️ 现在可以使用全部管家服务啦～\n\n"
            f"💡 回复「帮助」查看功能列表"
        )
    else:
        return (
            f"❌ {result['message']}\n\n"
            f"💡 请确认：\n"
            f"  · 房间码输入正确（6位字母数字）\n"
            f"  · 预订仍然有效\n"
            f"  · 码区分大小写？不区分，直接输入即可\n\n"
            f"📞 如有疑问，联系前台：{BNB_PHONE}"
        )


def handle_show_room_code(msg) -> str:
    """预订者查看自己的房间共享码"""
    openid = _get_openid(msg)
    from services.booking import get_booking_by_openid
    from bnb_context import get_current_bnb_id
    booking = get_booking_by_openid(openid, bnb_id=get_current_bnb_id())
    if not booking:
        return "您还没有有效预订，无法生成房间共享码。\n\n💡 预订后回复「绑定预订」解锁 AI 管家～"

    room_code = booking.get("room_code", "")
    if not room_code:
        return "您的预订暂未生成共享码，请联系前台获取。"

    guests = get_room_guests(room_code)
    lines = [
        "🔑 您的房间共享码",
        "",
        f"房间码：{room_code}",
        f"房型：{booking.get('room_type', '')}",
        f"入住：{booking.get('check_in_date', '')}",
        "",
        f"👥 已绑定 {len(guests)} 人：",
    ]
    for g in guests:
        lines.append(f"  · {g.get('guest_name', '未知')} ({g.get('relation', '同住')})")

    lines.append("")
    lines.append("💡 同住人回复「绑定房间 " + room_code + "」即可共享 AI 管家～")
    return "\n".join(lines)


def handle_continue(msg) -> str:
    """处理「继续生成」请求"""
    openid = _get_openid(msg)
    return continue_reply(openid)


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


def handle_extend_stay(msg, bnb_id: str = "guishu") -> str:
    """处理续住/延住请求——既创建员工通知，又实际延长预订日期"""
    openid = _get_openid(msg)
    phone = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"]).get("phone", BNB_PHONE)

    # 1. 必须先有有效预订
    if not is_ai_enabled(openid, bnb_id=bnb_id):
        return _require_booking_reply(bnb_id=bnb_id)

    # 2. 必须已实际入住
    if not is_checked_in(openid, bnb_id=bnb_id):
        return _require_check_in_reply(openid, bnb_id=bnb_id)

    # 3. 尝试延长预订（默认+1天）
    from services.booking import extend_booking, get_booking_by_openid
    updated = extend_booking(openid, extra_days=1, bnb_id=bnb_id)
    booking = get_booking_by_openid(openid, include_checked_out=True, bnb_id=bnb_id)

    # 4. 创建员工通知
    try:
        from services.notify import create_service_request
        create_service_request(
            openid=openid,
            service_name="续住",
            room_number=booking.get('room_number', '') if booking else '',
            urgency="high",
            bnb_id=bnb_id,
        )
    except Exception as e:
        log_error("wechat.ai_fallback", str(e))

    # 5. 拼装回复
    if updated:
        new_date = updated.get('check_out_date', '待确认')
        return (
            f"🏨 续住已确认！\n\n"
            f"📅 退房日期已延长至：{new_date}\n"
            f"🛎️ 续住期间所有管家服务照常使用～\n\n"
            f"💡 如需续住多天，请直接告知或联系前台调整\n"
            f"📞 前台电话：{phone}"
        )
    else:
        return (
            f"🏨 续住请求已收到！\n\n"
            f"📅 已通知前台为您办理续住手续\n"
            f"💡 默认为您延长1天，如需续住多天请告知前台\n\n"
            f"📞 前台电话：{phone}\n\n"
            f"当前管家服务不受影响，请放心～"
        )


def format_wifi_info(bnb_id: str = "guishu") -> str:
    from bnb_context import get_bnb_config
    cfg = get_bnb_config(bnb_id)
    ssid = cfg.get("wifi_ssid", "云上·归墅")
    pwd = cfg.get("wifi_password", "yunshang888")
    return (
        "📶 *WiFi 信息*\n\n"
        f"网络名称：{ssid}\n"
        f"密码：{pwd}\n\n"
        "连接后即可畅享高速网络～"
    )


def format_greeting(bnb_id="guishu") -> str:
    from bnb_context import get_bnb_config
    cfg = get_bnb_config(bnb_id)
    return (
        f"您好呀！👋 欢迎来到{cfg['name']}～\n\n"
        "我是您的智能管家，有什么可以帮您的吗？\n"
        "您可以回复以下数字快速查询：\n"
        "【1】房型展示  【2】咖啡简餐\n"
        "【3】游玩攻略  【4】快捷服务\n"
        "【5】在线咨询\n\n"
        "💡 预订请通过携程/美团/飞猪/大众点评\n"
        "🎐 预订确认后解锁专属AI管家～预订前也能免费使用旅行顾问哦～"
    )


def handle_human_service(bnb_id: str = "guishu") -> str:
    """处理人工客服转接"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    if is_human_service_time():
        phone = cfg.get("phone", BNB_PHONE)
        return (
            "正在为您转接人工客服... 👩‍💼\n\n"
            f"☎️ 也可直接拨打前台电话：{phone}\n"
            "🕐 人工客服在线时间：8:00 - 22:00\n\n"
            "请稍候，客服马上为您服务～"
        )
    else:
        return AUTO_REPLY_NIGHT.replace("{short_name}", cfg["short_name"])


def format_review_links(bnb_id="guishu") -> str:
    """格式化各平台好评链接（要求4）"""
    lines = ["⭐ *各平台评价入口*\n"]
    platforms = get_platform_review_links(bnb_id=bnb_id)
    for key, info in platforms.items():
        lines.append(f"{info['icon']} *{info['name']}*")
        lines.append(f"  {info['review_url']}\n")

    lines.append("💡 您的每一条评价都是对我们最大的鼓励～🙏")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  消息匹配与路由
# ══════════════════════════════════════════════════════════
KEYWORD_ROUTES = build_keyword_routes()  # 默认归墅，向后兼容
_ROUTES_CACHE = {}  # 按 bnb_id 缓存


def match_keyword(content: str, bnb_id="guishu"):
    """匹配关键词路由（按民宿动态构建）"""
    content = content.strip()
    if bnb_id not in _ROUTES_CACHE:
        _ROUTES_CACHE[bnb_id] = build_keyword_routes(bnb_id)
    routes = _ROUTES_CACHE[bnb_id]
    for pattern, handler in routes:
        m = re.match(pattern, content, re.IGNORECASE)
        if m:
            return handler, m
    return None, None


def _welcome_for_bnb(bnb_id="guishu"):
    """按民宿生成欢迎消息"""
    from bnb_context import get_bnb_config
    cfg = get_bnb_config(bnb_id)
    return (
        f"🏔️ 欢迎来到{cfg['name']}！\n\n"
        f"{cfg.get('description', '')}\n\n"
        "回复以下数字或关键词探索：\n"
        "【1】🛏️ 房型展示\n"
        "【2】☕ 咖啡简餐\n"
        "【3】🗺️ 游玩攻略\n"
        "【4】🛎️ 快捷服务\n"
        "【5】💬 在线咨询\n\n"
        f"🏨 预订请通过携程/美团/飞猪/大众点评搜索「{cfg['short_name']}」\n"
        "🎐 预订前免费旅行顾问 · 预订后解锁专属AI管家～"
    )


# ══════════════════════════════════════════════════════════
#  微信消息主入口
# ══════════════════════════════════════════════════════════
def handle_wechat_message(msg, bnb_id="guishu"):
    """
    处理微信消息的主入口
    路由优先级：关键词匹配 > AI对话（需预订） > 兜底
    """
    # 注入请求级 BnB 上下文（服务层可通过 get_current_bnb_id() 获取）
    from bnb_context import set_current_bnb
    set_current_bnb(bnb_id)

    # 获取用户消息内容
    if hasattr(msg, 'content'):
        content = msg.content.strip()
    elif hasattr(msg, 'text'):
        content = msg.text.strip()
    else:
        from config import BNB_CONFIGS
        return _welcome_for_bnb(bnb_id)

    openid = str(getattr(msg, 'source', getattr(msg, 'from_user', 'unknown')))

    # 1. 尝试关键词匹配
    handler, match = match_keyword(content, bnb_id=bnb_id)
    if handler:
        try:
            reply = handler(msg, match)
            try:
                from models import SessionLocal, MessageLog
                db = SessionLocal()
                log_entry = MessageLog(openid=openid, bnb_id=bnb_id, message_type="text", content=content, reply=str(reply)[:500])
                db.add(log_entry); db.commit(); db.close()
            except Exception:
                debug("消息日志记录失败")
            if match:
                log_keyword(openid, str(match.re.pattern), content)
            return reply
        except Exception as e:
            log_error("wechat.keyword", str(e))

    # 2. AI智能对话（v3.2 四层权限：旅行顾问 / 到店前 / 入住中 / 离店后）
    try:
        mode = get_conversation_mode(openid, bnb_id=bnb_id)
        if mode == 'travel_advisor':
            ai_reply = chat_travel_advisor(openid, content, bnb_id=bnb_id)
        elif mode == 'pre_arrival':
            ai_reply = chat_pre_arrival(openid, content, bnb_id=bnb_id)
        elif mode == 'post_stay':
            ai_reply = chat_post_stay(openid, content, bnb_id=bnb_id)
        else:
            ai_reply = chat(openid, content, bnb_id=bnb_id)
        return ai_reply
    except Exception as e:
        log_error("wechat.ai_fallback", str(e))

    warning("wechat.fallback", extra={"openid": openid, "content": content[:60]})
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
def handle_event(event_msg, bnb_id="guishu"):
    """处理微信事件推送"""
    from bnb_context import set_current_bnb
    set_current_bnb(bnb_id)
    event_type = getattr(event_msg, 'event', '')

    if event_type == 'subscribe':
        return _welcome_for_bnb(bnb_id)
    elif event_type == 'unsubscribe':
        return ""
    elif event_type == 'CLICK':
        event_key = getattr(event_msg, 'key', '')
        return handle_menu_click(event_key, bnb_id=bnb_id)
    elif event_type == 'SCAN':
        return _welcome_for_bnb(bnb_id)

    return ""


def handle_menu_click(event_key: str, bnb_id="guishu") -> str:
    """处理自定义菜单点击"""
    menu_handlers = {
        'rooms': lambda: format_rooms_text(bnb_id=bnb_id),
        'menu': lambda: format_menu_text(bnb_id=bnb_id),
        'travel': lambda: format_routes_text(bnb_id=bnb_id),
        'service': lambda: format_services_text(bnb_id=bnb_id),
        'location': lambda: format_location_text(bnb_id=bnb_id),
        'booking': lambda: format_booking_platforms_text(bnb_id=bnb_id),
        'contact': lambda: handle_human_service(bnb_id=bnb_id),
        'food': lambda: format_food_text(bnb_id=bnb_id),
        'reviews': lambda: generate_monitor_report(bnb_id=bnb_id),
    }

    handler = menu_handlers.get(event_key)
    if handler:
        return handler()

    return _welcome_for_bnb(bnb_id)


def _tea_or_fallback(bnb_id="guishu"):
    """茶园相关关键词处理：山纪专属，其他民宿引导"""
    if bnb_id == "shanji":
        from services.tea import format_tea_text
        return format_tea_text(bnb_id=bnb_id)
    return (
        "🍵 茶园体验是「云上·山纪」的特色服务哦～\n\n"
        "山纪民宿坐拥庐山茶园，提供采茶、制茶、品茶等体验。\n"
        "如需了解更多，请通过小程序切换到山纪民宿，或直接搜索「云上山纪」预订～"
    )


def _healing_or_fallback(bnb_id="guishu"):
    """疗愈相关关键词处理：东林外专属，其他民宿引导"""
    if bnb_id == "donglinwai":
        from services.healing import format_healing_text
        return format_healing_text(bnb_id=bnb_id)
    return (
        "🧘 疗愈体验是「云上·东林外」的特色服务哦～\n\n"
        "东林外民宿紧邻东林寺，提供瑜伽、禅修、SPA等身心疗愈项目。\n"
        "如需了解更多，请通过小程序切换到东林外民宿，或直接搜索「云上东林外」预订～"
    )


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
