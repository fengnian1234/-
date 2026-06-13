"""
预订管理服务（要求1、3、4）
- 预订验证与AI解锁
- 平台预订链接
- 退房后自动好评推送
"""
from datetime import datetime, timedelta
from models import SessionLocal, Booking
from config import (
    BOOKING_PLATFORMS, REVIEW_PLATFORMS, REVIEW_REMINDER_DELAY_MINUTES,
    BNB_NAME, BNB_ADDRESS,
)


def get_booking_by_openid(openid: str, include_checked_out: bool = False):
    """获取用户最近预订"""
    db = SessionLocal()
    try:
        statuses = ["confirmed", "checked_in"]
        if include_checked_out:
            statuses.append("checked_out")
        booking = db.query(Booking).filter(
            Booking.openid == openid,
            Booking.status.in_(statuses),
        ).order_by(Booking.created_at.desc()).first()
        return booking.to_dict() if booking else None
    finally:
        db.close()


def is_ai_enabled(openid: str) -> bool:
    """检查用户的AI对话是否已解锁"""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(
            Booking.openid == openid,
            Booking.ai_enabled == True,
            Booking.status.in_(["confirmed", "checked_in"]),
        ).first()
        return booking is not None
    finally:
        db.close()


def confirm_booking(openid: str, guest_name: str, phone: str,
                    platform: str, check_in: str, check_out: str,
                    room_type: str = "") -> Booking:
    """前台确认预订（解锁AI）"""
    db = SessionLocal()
    try:
        booking = Booking(
            openid=openid,
            guest_name=guest_name,
            phone=phone,
            platform=platform,
            check_in_date=check_in,
            check_out_date=check_out,
            room_type=room_type,
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
        return booking
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
