"""
预订管理服务（要求1、3、4）
- 预订验证与AI解锁
- 平台预订链接
- 退房后自动好评推送
"""
import secrets
import string
from datetime import datetime, timedelta
from models import SessionLocal, Booking, RoomGuest
from services.logger import info, warning, error as log_error, log_booking
from config import (
    BOOKING_PLATFORMS, REVIEW_PLATFORMS, REVIEW_REMINDER_DELAY_MINUTES,
    BNB_NAME, BNB_ADDRESS,
)


def get_booking_by_openid(openid: str, include_checked_out: bool = False):
    """获取用户最近预订（预订者本人 或 合住人）"""
    db = SessionLocal()
    try:
        booking, role = _get_active_booking_for_openid(db, openid)
        if booking:
            result = booking.to_dict()
            result["role"] = role
            return result

        if include_checked_out:
            # 查本人
            booking = db.query(Booking).filter(
                Booking.openid == openid,
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
                        Booking.status == "checked_out",
                    ).order_by(Booking.created_at.desc()).first()
            if booking:
                result = booking.to_dict()
                return result
        return None
    finally:
        db.close()


def _get_active_booking_for_openid(db, openid: str):
    """
    查找用户关联的有效预订（预订者本人 或 通过房间码绑定的合住人）
    返回 (Booking, role) 或 (None, None)
    """
    # 1. 先查本人预订
    booking = db.query(Booking).filter(
        Booking.openid == openid,
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
            Booking.ai_enabled == True,
            Booking.status.in_(["confirmed", "checked_in"]),
        ).first()
        if booking:
            return booking, "guest"

    return None, None


def is_checked_in(openid: str) -> bool:
    """检查用户是否已实际入住（含合住人）"""
    db = SessionLocal()
    try:
        booking, _ = _get_active_booking_for_openid(db, openid)
        if booking and booking.status == "checked_in":
            return True
        return False
    finally:
        db.close()


def is_ai_enabled(openid: str) -> bool:
    """检查用户的AI对话是否已解锁（预订者本人或合住人）"""
    db = SessionLocal()
    try:
        booking, _ = _get_active_booking_for_openid(db, openid)
        return booking is not None
    finally:
        db.close()


def _generate_room_code() -> str:
    """生成 6 位房间共享码（易记、不易碰撞）"""
    chars = string.ascii_uppercase + string.digits
    for _ in range(10):  # 最多重试10次
        code = ''.join(secrets.choice(chars) for _ in range(6))
        db = SessionLocal()
        try:
            exists = db.query(Booking).filter(Booking.room_code == code).first()
            if not exists:
                return code
        finally:
            db.close()
    return ''.join(secrets.choice(chars) for _ in range(6))  # 兜底


def bind_room_guest(room_code: str, openid: str, guest_name: str = "", relation: str = "同住") -> dict:
    """
    合住人通过房间码绑定，共享 AI 管家全部权限。
    返回 {"success": True/False, "message": "...", "booking": {...}}
    """
    db = SessionLocal()
    try:
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

        return {
            "success": True,
            "message": f"绑定成功！欢迎加入 {booking.room_type or '云上归墅'}，AI 管家已就绪～",
            "booking": booking.to_dict(),
            "room_code": room_code,
            "role": "guest",
        }

    finally:
        db.close()


def get_room_guests(room_code: str) -> list:
    """获取某房间码下的所有合住人"""
    db = SessionLocal()
    try:
        guests = db.query(RoomGuest).filter(
            RoomGuest.room_code == room_code,
            RoomGuest.is_active == True,
        ).all()
        return [g.to_dict() for g in guests]
    finally:
        db.close()


def confirm_booking(openid: str, guest_name: str, phone: str,
                    platform: str, check_in: str, check_out: str,
                    room_type: str = "") -> Booking:
    """前台确认预订（解锁AI + 生成房间共享码）"""
    db = SessionLocal()
    try:
        room_code = _generate_room_code()
        booking = Booking(
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
        return booking
    finally:
        db.close()


def check_in_booking(booking_id: int, room_number: str = "") -> Booking:
    """办理入住"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.status = "checked_in"
            booking.room_number = room_number
            booking.ai_enabled = True
            db.commit()
            # 预加载属性，避免返回后 session 关闭导致 DetachedInstanceError
            _ = (booking.id, booking.status, booking.room_number, booking.guest_name, booking.room_type)
        return booking
    finally:
        db.close()


def extend_booking(openid: str, extra_days: int = 1) -> dict:
    """
    续住：延长客人的退房日期。
    返回更新后的预订信息，失败返回 None。
    """
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(
            Booking.openid == openid,
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
    finally:
        db.close()


def check_out_booking(booking_id: int) -> Booking:
    """办理退房（标记退房时间，触发好评推送倒计时）"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.status = "checked_out"
            booking.checked_out_at = datetime.utcnow()
            db.commit()
            # 预加载属性，避免返回后 session 关闭导致 DetachedInstanceError
            _ = (booking.id, booking.status, booking.guest_name, booking.room_type, booking.checked_out_at)
        return booking
    finally:
        db.close()


def get_review_reminders_due():
    """获取需要推送好评提醒的退房记录（退房30分钟后）"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=REVIEW_REMINDER_DELAY_MINUTES)
        bookings = db.query(Booking).filter(
            Booking.status == "checked_out",
            Booking.review_sent == False,
            Booking.checked_out_at <= cutoff,
        ).all()
        return bookings
    finally:
        db.close()


def mark_review_sent(booking_id: int, platform: str):
    """标记好评已推送"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.review_sent = True
            booking.review_sent_at = datetime.utcnow()
            booking.review_platform = platform
            booking.status = "completed"
            db.commit()
    finally:
        db.close()


def generate_review_message(booking: Booking) -> str:
    """生成得体的好评推送消息（要求4）— 使用 AI 模块的 review_request 模板"""
    from services.ai import generate_review_request_message
    return generate_review_request_message(
        guest_name=booking.guest_name or "",
        room_name=booking.room_type or "",
    )


def format_booking_platforms_text() -> str:
    """格式化预订平台信息（要求3：跳转主流平台）"""
    lines = [
        "🏨 *预订云上·归墅*\n",
        f"📍 {BNB_ADDRESS}\n",
        "本民宿已接入以下主流预订平台，\n点击链接即可跳转预订：\n",
    ]

    for key, plat in BOOKING_PLATFORMS.items():
        lines.append(
            f"{plat['icon']} *{plat['name']}* → 搜索「云上归墅」\n"
            f"  {plat['url']}\n"
        )

    lines.append("")
    lines.append("💡 *温馨提示*")
    lines.append("  · 不同平台价格和优惠可能不同，建议多平台比价")
    lines.append("  · 预订成功后，请在公众号内回复「绑定预订」")
    lines.append("    解锁专属AI管家～预订前也能免费使用旅行顾问哦～")
    lines.append("  · 本服务号不支持直接支付房费，请通过平台预订")

    return "\n".join(lines)
