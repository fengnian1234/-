"""
多平台订单聚合服务 — 统一管理各OTA平台订单
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from models import SessionLocal, AggregatedOrder, Room


PLATFORMS = {
    "ctrip":     {"name": "携程",     "icon": "🏨", "color": "#2577e3", "fee_rate": 0.12},
    "meituan":   {"name": "美团民宿", "icon": "🏠", "color": "#ffc300", "fee_rate": 0.10},
    "fliggy":    {"name": "飞猪",     "icon": "✈️", "color": "#ff5a00", "fee_rate": 0.10},
    "dianping":  {"name": "大众点评", "icon": "⭐", "color": "#ffc300", "fee_rate": 0.08},
    "direct":    {"name": "直接预订", "icon": "📞", "color": "#5b8c5a", "fee_rate": 0.00},
    "xiaohongshu":{"name":"小红书",   "icon": "📕", "color": "#ff2442", "fee_rate": 0.00},
    "douyin":    {"name": "抖音",     "icon": "🎵", "color": "#010101", "fee_rate": 0.00},
}


def get_platforms() -> list:
    """获取平台列表"""
    return [{"key": k, **v} for k, v in PLATFORMS.items()]


def _get_bnb_id(bnb_id=None):
    if bnb_id:
        return bnb_id
    try:
        from flask import g
        return getattr(g, 'bnb_id', 'guishu')
    except RuntimeError:
        return 'guishu'


def add_order(data: dict) -> dict:
    """添加新订单（手动录入或API推送）"""
    bnb_id = _get_bnb_id(data.get("bnb_id"))
    db = SessionLocal()
    try:
        platform = data.get("platform", "direct")
        fee_rate = PLATFORMS.get(platform, {}).get("fee_rate", 0)
        total = float(data.get("total_amount", 0) or 0)
        platform_fee = float(data.get("platform_fee", 0) or 0)
        if not platform_fee and fee_rate > 0:
            platform_fee = round(total * fee_rate, 2)

        order = AggregatedOrder(
            bnb_id=bnb_id,
            platform=platform,
            platform_order_id=data.get("platform_order_id", ""),
            guest_name=data["guest_name"],
            guest_phone=data.get("guest_phone", ""),
            room_type=data.get("room_type", ""),
            check_in=data["check_in"],
            check_out=data["check_out"],
            nights=data.get("nights", 1),
            total_amount=total,
            platform_fee=platform_fee,
            net_revenue=round(total - platform_fee, 2) if total else None,
            guest_count=data.get("guest_count", 1),
            status=data.get("status", "confirmed"),
            remark=data.get("remark", ""),
            source=data.get("source", "manual"),
        )
        db.add(order)
        db.commit()
        return {"success": True, "order": order.to_dict()}
    finally:
        db.close()


def get_orders(date_from: str = None, date_to: str = None, platform: str = None, status: str = None, limit: int = 50, bnb_id=None) -> list:
    """查询订单列表"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        q = db.query(AggregatedOrder).filter(AggregatedOrder.bnb_id == bnb_id)
        if date_from:
            q = q.filter(AggregatedOrder.check_in >= date_from)
        if date_to:
            q = q.filter(AggregatedOrder.check_in <= date_to)
        if platform:
            q = q.filter(AggregatedOrder.platform == platform)
        if status:
            q = q.filter(AggregatedOrder.status == status)
        orders = q.order_by(AggregatedOrder.check_in.desc()).limit(limit).all()
        return [o.to_dict() for o in orders]
    finally:
        db.close()


def update_order_status(order_id: int, status: str, room_number: str = "") -> dict:
    """更新订单状态"""
    db = SessionLocal()
    try:
        order = db.query(AggregatedOrder).filter(AggregatedOrder.id == order_id).first()
        if not order:
            return {"success": False, "message": "订单不存在"}
        order.status = status
        if room_number:
            order.room_number = room_number
        order.updated_at = datetime.utcnow()
        db.commit()
        return {"success": True, "order": order.to_dict()}
    finally:
        db.close()


def get_dashboard_stats(bnb_id=None) -> dict:
    """获取订单看板统计数据"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        base_filter = AggregatedOrder.bnb_id == bnb_id

        total = db.query(AggregatedOrder).filter(base_filter, AggregatedOrder.status != "cancelled").count()

        today_arrivals = db.query(AggregatedOrder).filter(
            base_filter, AggregatedOrder.check_in == today, AggregatedOrder.status != "cancelled"
        ).count()

        today_departures = db.query(AggregatedOrder).filter(
            base_filter, AggregatedOrder.check_out == today, AggregatedOrder.status == "checked_in"
        ).count()

        currently_in = db.query(AggregatedOrder).filter(
            base_filter, AggregatedOrder.status == "checked_in"
        ).count()

        # 各平台订单数
        platform_stats = db.query(
            AggregatedOrder.platform, func.count(AggregatedOrder.id), func.sum(AggregatedOrder.total_amount)
        ).filter(base_filter, AggregatedOrder.status != "cancelled").group_by(AggregatedOrder.platform).all()

        platforms = []
        total_revenue = 0
        for p, cnt, amt in platform_stats:
            platforms.append({"platform": p, "icon": PLATFORMS.get(p, {}).get("icon", "📋"), "count": cnt, "revenue": round(amt or 0, 2)})
            total_revenue += (amt or 0)

        # 本月统计
        month_start = today[:7] + "-01"
        month_orders = db.query(AggregatedOrder).filter(
            base_filter, AggregatedOrder.check_in >= month_start, AggregatedOrder.status != "cancelled"
        ).count()
        month_revenue = db.query(func.sum(AggregatedOrder.net_revenue)).filter(
            base_filter, AggregatedOrder.check_in >= month_start, AggregatedOrder.status != "cancelled"
        ).scalar() or 0

        # 未来7天到店
        week_later = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        upcoming = db.query(AggregatedOrder).filter(
            base_filter, AggregatedOrder.check_in > today, AggregatedOrder.check_in <= week_later,
            AggregatedOrder.status == "confirmed"
        ).count()

        return {
            "today": today,
            "total_orders": total,
            "today_arrivals": today_arrivals,
            "today_departures": today_departures,
            "currently_in": currently_in,
            "upcoming_week": upcoming,
            "month_orders": month_orders,
            "month_revenue": round(month_revenue, 2),
            "platforms": platforms,
            "total_revenue": round(total_revenue, 2),
        }
    finally:
        db.close()


def get_room_calendar(days: int = 14, bnb_id: str = "guishu") -> list:
    """获取未来N天的房态日历"""
    db = SessionLocal()
    try:
        today = datetime.utcnow()
        # 按民宿查询实际客房总数
        total_rooms = db.query(Room).filter(
            Room.bnb_id == bnb_id
        ).count()
        # fallback: count total_count sum
        if total_rooms == 0:
            total_rooms = 1
        else:
            room_sum = db.query(Room).filter(Room.bnb_id == bnb_id).with_entities(
                Room.total_count
            ).all()
            total_rooms = sum(r[0] for r in room_sum) if room_sum else total_rooms
        calendar = []
        for i in range(days):
            day = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            arrivals = db.query(AggregatedOrder).filter(
                AggregatedOrder.check_in == day, AggregatedOrder.status.in_(["confirmed", "checked_in"])
            ).count()
            departures = db.query(AggregatedOrder).filter(
                AggregatedOrder.check_out == day, AggregatedOrder.status == "checked_in"
            ).count()
            staying = db.query(AggregatedOrder).filter(
                AggregatedOrder.check_in <= day, AggregatedOrder.check_out > day,
                AggregatedOrder.status.in_(["confirmed", "checked_in"])
            ).count()

            weekday = ["日","一","二","三","四","五","六"][(today + timedelta(days=i)).weekday()]
            occupancy = min(100, round(staying / total_rooms * 100))

            calendar.append({
                "date": day, "weekday": weekday,
                "arrivals": arrivals, "departures": departures,
                "staying": staying, "occupancy": occupancy,
            })
        return calendar
    finally:
        db.close()
