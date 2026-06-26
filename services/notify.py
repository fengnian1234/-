"""
员工通知服务（要求2：醒目有效的通知方式）
- 服务请求实时通知
- 员工看板数据
- 浏览器声音提醒支持
"""
from datetime import datetime
from models import SessionLocal, ServiceRequest
from bnb_context import get_service_bnb_id as _get_bnb_id


def create_service_request(openid: str, service_name: str,
                           room_number: str = "",
                           urgency: str = "normal",
                           notes: str = "", bnb_id=None) -> ServiceRequest:
    """创建服务请求并记录到通知队列"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        req = ServiceRequest(
            bnb_id=bnb_id,
            openid=openid,
            service_name=service_name,
            room_number=room_number,
            urgency=urgency,
            notes=notes,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req
    finally:
        db.close()


def get_pending_requests():
    """获取所有待处理的服务请求"""
    db = SessionLocal()
    try:
        requests = db.query(ServiceRequest).filter(
            ServiceRequest.status.in_(["pending", "acknowledged"])
        ).order_by(ServiceRequest.urgency.desc(),
                   ServiceRequest.created_at.asc()).all()
        return [r.to_dict() for r in requests]
    finally:
        db.close()


def get_all_requests_today():
    """获取今日所有服务请求"""
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        requests = db.query(ServiceRequest).filter(
            ServiceRequest.created_at >= today
        ).order_by(ServiceRequest.created_at.desc()).all()
        return [r.to_dict() for r in requests]
    finally:
        db.close()


def acknowledge_request(request_id: int, handler: str = ""):
    """员工确认收到请求"""
    db = SessionLocal()
    try:
        req = db.query(ServiceRequest).filter(
            ServiceRequest.id == request_id
        ).first()
        if req:
            req.status = "acknowledged"
            req.handler = handler
            req.acknowledged_at = datetime.utcnow()
            db.commit()
            return True
        return False
    finally:
        db.close()


def complete_request(request_id: int, notes: str = ""):
    """完成服务请求"""
    db = SessionLocal()
    try:
        req = db.query(ServiceRequest).filter(
            ServiceRequest.id == request_id
        ).first()
        if req:
            req.status = "completed"
            req.completed_at = datetime.utcnow()
            if notes:
                req.notes = notes
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_pending_count() -> int:
    """获取待处理请求数量（用于角标显示）"""
    db = SessionLocal()
    try:
        return db.query(ServiceRequest).filter(
            ServiceRequest.status == "pending"
        ).count()
    finally:
        db.close()


def get_notification_stats() -> dict:
    """获取通知统计"""
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        pending = db.query(ServiceRequest).filter(
            ServiceRequest.status == "pending"
        ).count()
        today_total = db.query(ServiceRequest).filter(
            ServiceRequest.created_at >= today
        ).count()
        today_completed = db.query(ServiceRequest).filter(
            ServiceRequest.created_at >= today,
            ServiceRequest.status == "completed"
        ).count()

        return {
            "pending": pending,
            "today_total": today_total,
            "today_completed": today_completed,
            "completion_rate": f"{today_completed/today_total*100:.0f}%"
            if today_total > 0 else "N/A",
        }
    finally:
        db.close()
