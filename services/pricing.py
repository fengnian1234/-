"""
每日房价服务 — 主理人面板
- 获取今日各房型基准价格
- 更新/录入房价
- 查看调价历史
"""
from datetime import datetime, UTC
from models import SessionLocal, DailyPricing
from bnb_context import get_service_bnb_id as _get_bnb_id


def get_today_pricing(bnb_id=None) -> list:
    """获取今日各房型定价列表（可能为空，需主理人录入）"""
    bnb_id = _get_bnb_id(bnb_id)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        records = db.query(DailyPricing).filter(
            DailyPricing.bnb_id == bnb_id,
            DailyPricing.date == today,
        ).order_by(DailyPricing.room_type).all()
        return [r.to_dict() for r in records]
    finally:
        db.close()


def update_pricing(room_type: str, base_price: float, bnb_id=None,
                   weekend_price: float = None, holiday_price: float = None,
                   special_price: float = None, updated_by: str = "",
                   notes: str = "") -> dict:
    """更新或创建今日房价记录（upsert）"""
    bnb_id = _get_bnb_id(bnb_id)
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        record = db.query(DailyPricing).filter(
            DailyPricing.bnb_id == bnb_id,
            DailyPricing.room_type == room_type,
            DailyPricing.date == today,
        ).first()
        if record:
            record.base_price = base_price
            if weekend_price is not None:
                record.weekend_price = weekend_price
            if holiday_price is not None:
                record.holiday_price = holiday_price
            if special_price is not None:
                record.special_price = special_price
            record.updated_by = updated_by
            if notes:
                record.notes = notes
            record.updated_at = datetime.now(UTC)
        else:
            record = DailyPricing(
                bnb_id=bnb_id,
                room_type=room_type,
                base_price=base_price,
                weekend_price=weekend_price,
                holiday_price=holiday_price,
                special_price=special_price,
                date=today,
                updated_by=updated_by,
                notes=notes,
            )
            db.add(record)
        db.commit()
        db.refresh(record)
        return {"success": True, "pricing": record.to_dict()}
    finally:
        db.close()


def get_pricing_history(room_type: str = None, days: int = 7, bnb_id=None) -> list:
    """获取调价历史记录"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        q = db.query(DailyPricing).filter(DailyPricing.bnb_id == bnb_id)
        if room_type:
            q = q.filter(DailyPricing.room_type == room_type)
        q = q.order_by(DailyPricing.date.desc(), DailyPricing.updated_at.desc()).limit(days * 10)
        return [r.to_dict() for r in q.all()]
    finally:
        db.close()
