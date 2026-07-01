"""
预订管理服务（要求1、3、4）
- 预订验证与AI解锁
- 平台预订链接
- 退房后自动好评推送
"""
import secrets
import string
from datetime import datetime, timedelta, UTC
from models import get_db, Booking, RoomGuest
from services.logger import info, warning, error as log_error, debug, log_booking
from config import (
    REVIEW_REMINDER_DELAY_MINUTES, BNB_CONFIGS,
)


def _resolve_bnb_id(bnb_id: str = None) -> str:
    """解析 bnb_id：优先参数 > Flask g > 线程本地 > 默认 guishu"""
    if bnb_id:
        return bnb_id
    try:
        from bnb_context import get_current_bnb_id
        return get_current_bnb_id()
    except Exception:
        debug("bnb_id解析失败，降级为guishu", exc_info=True)
        return "guishu"


def get_booking_by_openid(openid: str, include_checked_out: bool = False, bnb_id: str = None):
    """获取用户最近预订（预订者本人 或 合住人），按 bnb_id 过滤"""
    bnb_id = _resolve_bnb_id(bnb_id)
    with get_db() as db:
        booking, role = _get_active_booking_for_openid(db, openid, bnb_id=bnb_id)
        if booking:
            result = booking.to_dict()
            result["role"] = role
            return result

        if include_checked_out:
            # 查本人
            booking = db.query(Booking).filter(
                Booking.openid == openid,
                Booking.bnb_id == bnb_id,
                Booking.status == "checked_out",
            ).order_by(Booking.created_at.desc()).first()
            # 查合住人关联的已退房记录
            if not booking:
                guest = db.query(RoomGuest).filter(
                    RoomGuest.openid == openid,
                ).first()
                if guest:
                    booking = db.query(Booking).filter(
                        Booking.room_code == guest.room_code,
                        Booking.bnb_id == bnb_id,
                        Booking.status == "checked_out",
                    ).order_by(Booking.created_at.desc()).first()
            if booking:
                result = booking.to_dict()
                return result
        return None


def _get_active_booking_for_openid(db, openid: str, bnb_id: str = None):
    """
    查找用户关联的有效预订（预订者本人 或 通过房间码绑定的合住人）
    返回 (Booking, role) 或 (None, None)
    """
    bnb_id = _resolve_bnb_id(bnb_id)

    # 1. 先查本人预订
    booking = db.query(Booking).filter(
        Booking.openid == openid,
        Booking.bnb_id == bnb_id,
        Booking.ai_enabled == True,
        Booking.status.in_(["confirmed", "checked_in"]),
    ).first()
    if booking:
        return booking, "primary"

    # 2. 查合住人关联
    guest = db.query(RoomGuest).filter(
        RoomGuest.openid == openid,
        RoomGuest.is_active == True,
    ).first()
    if guest:
        booking = db.query(Booking).filter(
            Booking.room_code == guest.room_code,
            Booking.bnb_id == bnb_id,
            Booking.ai_enabled == True,
            Booking.status.in_(["confirmed", "checked_in"]),
        ).first()
        if booking:
            return booking, "guest"

    return None, None


def is_checked_in(openid: str, bnb_id: str = None) -> bool:
    """检查用户是否已实际入住（含合住人），按 bnb_id 过滤"""
    bnb_id = _resolve_bnb_id(bnb_id)
    with get_db() as db:
        booking, _ = _get_active_booking_for_openid(db, openid, bnb_id=bnb_id)
        if booking and booking.status == "checked_in":
            return True
        return False


def is_ai_enabled(openid: str, bnb_id: str = None) -> bool:
    """检查用户的AI对话是否已解锁（预订者本人或合住人），按 bnb_id 过滤"""
    bnb_id = _resolve_bnb_id(bnb_id)
    with get_db() as db:
        booking, _ = _get_active_booking_for_openid(db, openid, bnb_id=bnb_id)
        return booking is not None


def _generate_room_code() -> str:
    """生成 6 位房间共享码（易记、不易碰撞）"""
    chars = string.ascii_uppercase + string.digits
    for _ in range(10):  # 最多重试10次
        code = ''.join(secrets.choice(chars) for _ in range(6))
        with get_db() as db:
            exists = db.query(Booking).filter(Booking.room_code == code).first()
            if not exists:
                return code
    return ''.join(secrets.choice(chars) for _ in range(6))  # 兜底


def bind_room_guest(room_code: str, openid: str, guest_name: str = "", relation: str = "同住") -> dict:
    """
    合住人通过房间码绑定，共享 AI 管家全部权限。
    返回 {"success": True/False, "message": "...", "booking": {...}}
    """
    with get_db() as db:
        # 1. 验证房间码有效性
        booking = db.query(Booking).filter(
            Booking.room_code == room_code,
            Booking.ai_enabled == True,
            Booking.status.in_(["confirmed", "checked_in"]),
        ).first()

        if not booking:
            return {"success": False, "message": "房间码无效或预订已失效，请确认码是否正确"}

        # 2. 检查是否已绑定（去重）
        existing = db.query(RoomGuest).filter(
            RoomGuest.room_code == room_code,
            RoomGuest.openid == openid,
        ).first()
        if existing:
            if existing.is_active:
                return {
                    "success": True,
                    "message": f"已绑定过该房间，AI 管家已就绪～",
                    "booking": booking.to_dict(),
                    "room_code": room_code,
                    "role": "guest",
                }
            else:
                existing.is_active = True
                db.commit()
        else:
            # 3. 创建绑定
            guest = RoomGuest(
                room_code=room_code,
                openid=openid,
                guest_name=guest_name or f"同住人{openid[:6]}",
                relation=relation,
            )
            db.add(guest)
            db.commit()
            log_booking(openid, "bind_room", f"room_code={room_code} name={guest_name}")

        bnb_name = BNB_CONFIGS.get(booking.bnb_id, BNB_CONFIGS["guishu"]).get("short_name", BNB_CONFIGS["guishu"]["short_name"]) if booking.bnb_id else BNB_CONFIGS["guishu"]["short_name"]
        return {
            "success": True,
            "message": f"绑定成功！欢迎加入 {booking.room_type or bnb_name}，AI 管家已就绪～",
            "booking": booking.to_dict(),
            "room_code": room_code,
            "role": "guest",
        }


def get_room_guests(room_code: str) -> list:
    """获取某房间码下的所有合住人"""
    with get_db() as db:
        guests = db.query(RoomGuest).filter(
            RoomGuest.room_code == room_code,
            RoomGuest.is_active == True,
        ).all()
        return [g.to_dict() for g in guests]


def confirm_booking(openid: str, guest_name: str, phone: str,
                    platform: str, check_in: str, check_out: str,
                    room_type: str = "", bnb_id=None) -> Booking:
    """前台确认预订（解锁AI + 生成房间共享码）"""
    if not bnb_id:
        try:
            from flask import g
            bnb_id = getattr(g, 'bnb_id', 'guishu')
        except RuntimeError:
            bnb_id = 'guishu'
    with get_db() as db:
        room_code = _generate_room_code()
        booking = Booking(
            bnb_id=bnb_id,
            openid=openid,
            guest_name=guest_name,
            phone=phone,
            platform=platform,
            check_in_date=check_in,
            check_out_date=check_out,
            room_type=room_type,
            room_code=room_code,
            status="confirmed",
            ai_enabled=True,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        db.expunge(booking)  # 脱离session避免调用方DetachedInstanceError
        return booking


def check_in_booking(booking_id: int, room_number: str = "") -> Booking:
    """办理入住"""
    with get_db() as db:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.status = "checked_in"
            booking.room_number = room_number
            booking.ai_enabled = True
            db.commit()
            db.expunge(booking)  # 脱离session避免调用方DetachedInstanceError
        return booking


def extend_booking(openid: str, extra_days: int = 1, bnb_id: str = None) -> dict:
    """
    续住：延长客人的退房日期，按 bnb_id 过滤。
    返回更新后的预订信息，失败返回 None。
    """
    bnb_id = _resolve_bnb_id(bnb_id)
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.openid == openid,
            Booking.bnb_id == bnb_id,
            Booking.status.in_(["confirmed", "checked_in"]),
        ).order_by(Booking.created_at.desc()).first()

        if not booking:
            return None

        # 解析现有退房日期，增加天数
        from datetime import timedelta
        try:
            current_checkout = datetime.strptime(booking.check_out_date, "%Y-%m-%d")
            new_checkout = current_checkout + timedelta(days=extra_days)
            booking.check_out_date = new_checkout.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            # 日期格式异常时不更新
            return None

        db.commit()
        return booking.to_dict()


def check_out_booking(booking_id: int) -> Booking:
    """办理退房（标记退房时间，触发好评推送倒计时）"""
    with get_db() as db:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.status = "checked_out"
            booking.checked_out_at = datetime.now(UTC)
            db.commit()
            db.expunge(booking)  # 脱离session避免调用方DetachedInstanceError
        return booking


def get_review_reminders_due(bnb_id=None):
    """获取需要推送好评提醒的退房记录（退房30分钟后），可按 BnB 过滤"""
    with get_db() as db:
        cutoff = datetime.now(UTC) - timedelta(minutes=REVIEW_REMINDER_DELAY_MINUTES)
        q = db.query(Booking).filter(
            Booking.status == "checked_out",
            Booking.review_sent == False,
            Booking.checked_out_at <= cutoff,
        )
        if bnb_id:
            q = q.filter(Booking.bnb_id == bnb_id)
        return q.all()


def mark_review_sent(booking_id: int, platform: str):
    """标记好评已推送"""
    with get_db() as db:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.review_sent = True
            booking.review_sent_at = datetime.now(UTC)
            booking.review_platform = platform
            booking.status = "completed"
            db.commit()


def generate_review_message(booking: Booking) -> str:
    """生成得体的好评推送消息（要求4）— 使用 AI 模块的 review_request 模板"""
    from services.ai import generate_review_request_message
    return generate_review_request_message(
        guest_name=booking.guest_name or "",
        room_name=booking.room_type or "",
    )


def format_booking_platforms_text(bnb_id="guishu") -> str:
    """格式化预订平台信息（要求3：跳转主流平台）"""
    from config import BOOKING_PLATFORMS_BY_BNB, BNB_CONFIGS
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    platforms = BOOKING_PLATFORMS_BY_BNB.get(bnb_id, BOOKING_PLATFORMS_BY_BNB["guishu"])
    lines = [
        f"· *预订{cfg['name']}*\n",
        f"· {cfg['address']}\n",
        "本民宿已接入以下主流预订平台，\n点击链接即可跳转预订：\n",
    ]

    for key, plat in platforms.items():
        lines.append(
            f"{plat['icon']} *{plat['name']}* → 搜索「{cfg['short_name']}」\n"
            f"  {plat['url']}\n"
        )

    lines.append("")
    lines.append("▸ 提示： *温馨提示*")
    lines.append("  · 不同平台价格和优惠可能不同，建议多平台比价")
    lines.append("  · 预订成功后，请在公众号内回复「绑定预订」")
    lines.append("    解锁专属AI管家～预订前也能免费使用旅行顾问哦～")
    lines.append("  · 本服务号不支持直接支付房费，请通过平台预订")

    return "\n".join(lines)


def send_review_reminder(openid: str, bnb_id: str, message: str):
    """
    通过微信客服消息发送好评提醒。
    当前为 stub 实现，需微信认证后通过 wechatpy 发送。
    """
    from services.logger import info as _info
    _info(f"好评推送 [{bnb_id}] openid={openid[:12]}: {message[:80]}...")
    # TODO: 微信认证后替换为:
    # from wechatpy import WeChatClient
    # client = WeChatClient(app_id, app_secret)
    # client.message.send_text(openid, message)
