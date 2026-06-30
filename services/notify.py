"""
员工通知服务（要求2：醒目有效的通知方式）
- 服务请求实时通知
- 员工看板数据
- 浏览器声音提醒支持
"""
from datetime import datetime, UTC
from models import get_db, ServiceRequest
from bnb_context import get_service_bnb_id as _get_bnb_id


def create_service_request(openid: str, service_name: str,
                           room_number: str = "",
                           urgency: str = "normal",
                           notes: str = "", bnb_id=None) -> ServiceRequest:
    """创建服务请求并记录到通知队列"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
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


def get_pending_requests(bnb_id=None):
    """获取待处理的服务请求，可按 BnB 过滤"""
    with get_db() as db:
        q = db.query(ServiceRequest).filter(
            ServiceRequest.status.in_(["pending", "acknowledged"])
        )
        if bnb_id:
            q = q.filter(ServiceRequest.bnb_id == bnb_id)
        q = q.order_by(ServiceRequest.urgency.desc(),
                       ServiceRequest.created_at.asc())
        return [r.to_dict() for r in q.all()]


def get_all_requests_today(bnb_id=None):
    """获取今日所有服务请求，可按 BnB 过滤"""
    with get_db() as db:
        today = datetime.now(UTC).date()
        q = db.query(ServiceRequest).filter(
            ServiceRequest.created_at >= today
        )
        if bnb_id:
            q = q.filter(ServiceRequest.bnb_id == bnb_id)
        q = q.order_by(ServiceRequest.created_at.desc())
        return [r.to_dict() for r in q.all()]


def acknowledge_request(request_id: int, handler: str = ""):
    """员工确认收到请求"""
    with get_db() as db:
        req = db.query(ServiceRequest).filter(
            ServiceRequest.id == request_id
        ).first()
        if req:
            req.status = "acknowledged"
            req.handler = handler
            req.acknowledged_at = datetime.now(UTC)
            db.commit()
            return True
        return False


def complete_request(request_id: int, notes: str = ""):
    """完成服务请求"""
    with get_db() as db:
        req = db.query(ServiceRequest).filter(
            ServiceRequest.id == request_id
        ).first()
        if req:
            req.status = "completed"
            req.completed_at = datetime.now(UTC)
            if notes:
                req.notes = notes
            db.commit()
            return True
        return False


def get_pending_count() -> int:
    """获取待处理请求数量（用于角标显示）"""
    with get_db() as db:
        return db.query(ServiceRequest).filter(
            ServiceRequest.status == "pending"
        ).count()


def get_notification_stats(bnb_id=None) -> dict:
    """获取通知统计，可按 BnB 过滤"""
    with get_db() as db:
        today = datetime.now(UTC).date()

        def _count(status_filter, date_filter=False):
            q = db.query(ServiceRequest)
            if bnb_id:
                q = q.filter(ServiceRequest.bnb_id == bnb_id)
            if date_filter:
                q = q.filter(ServiceRequest.created_at >= today)
            if status_filter:
                q = q.filter(ServiceRequest.status == status_filter)
            return q.count()

        pending = _count("pending")
        today_total = _count(None, date_filter=True)
        today_completed = _count("completed", date_filter=True)

        return {
            "pending": pending,
            "today_total": today_total,
            "today_completed": today_completed,
            "completion_rate": f"{today_completed/today_total*100:.0f}%"
            if today_total > 0 else "N/A",
        }
