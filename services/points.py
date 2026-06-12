"""
积分体系服务 — 会员积分获取、兑换、等级管理
"""
from datetime import datetime
from models import SessionLocal, GuestPoints, PointLog, REDEEM_ITEMS, EARN_RULES, MEMBERSHIP_TIERS


def _get_or_create_points(db, openid: str) -> GuestPoints:
    """获取或创建用户积分记录"""
    gp = db.query(GuestPoints).filter(GuestPoints.openid == openid).first()
    if not gp:
        gp = GuestPoints(openid=openid, total_points=0, total_earned=0, total_spent=0, membership="silver")
        db.add(gp)
        db.flush()
    return gp


def _update_membership(gp: GuestPoints):
    """根据总积分更新会员等级"""
    if gp.total_earned >= 8000:
        gp.membership = "diamond"
    elif gp.total_earned >= 3000:
        gp.membership = "gold"
    else:
        gp.membership = "silver"


def get_guest(openid: str) -> dict | None:
    """获取用户积分概览"""
    db = SessionLocal()
    try:
        gp = db.query(GuestPoints).filter(GuestPoints.openid == openid).first()
        if not gp:
            return None
        return gp.to_dict()
    finally:
        db.close()


def get_logs(openid: str, limit: int = 20) -> list:
    """获取积分变动记录"""
    db = SessionLocal()
    try:
        logs = db.query(PointLog).filter(
            PointLog.openid == openid
        ).order_by(PointLog.created_at.desc()).limit(limit).all()
        return [l.to_dict() for l in logs]
    finally:
        db.close()


def earn_points(openid: str, action: str, amount: int = None, description: str = "") -> dict:
    """
    获取积分
    action: booking|checkin|review|share|birthday|xhs_note|social_post
    """
    from datetime import datetime as dt
    db = SessionLocal()
    try:
        gp = _get_or_create_points(db, openid)
        rule = EARN_RULES.get(action)
        if not rule:
            return {"success": False, "message": "未知的积分获取方式"}

        # 特殊处理：设置生日月份
        if action == "birthday":
            birthday_month = amount if amount and 1 <= amount <= 12 else None
            if birthday_month:
                gp.birthday_month = birthday_month
            db.commit()
            return {
                "success": True,
                "earned": 0,
                "total_points": gp.total_points,
                "membership": gp.to_dict()["membership_name"],
                "message": f"已登记生日月份：{gp.birthday_month}月，该月所有积分×1.5！" if birthday_month else "请告知您的生日月份（1-12）～",
            }

        pts = amount or rule["points"]

        # 生日月 1.5 倍积分
        now = dt.utcnow()
        birthday_bonus = False
        if gp.birthday_month and gp.birthday_month == now.month and action != "birthday":
            pts = int(pts * 1.5)
            birthday_bonus = True

        gp.total_points += pts
        gp.total_earned += pts

        desc = description or rule["name"]
        if birthday_bonus:
            desc += "（生日月×1.5）"

        log = PointLog(
            openid=openid, points=pts, action=f"earn_{action}",
            description=desc
        )
        db.add(log)

        _update_membership(gp)
        db.commit()

        return {
            "success": True,
            "earned": pts,
            "total_points": gp.total_points,
            "membership": gp.to_dict()["membership_name"],
            "birthday_bonus": birthday_bonus,
        }
    finally:
        db.close()


def redeem(openid: str, item_key: str, description: str = "") -> dict:
    """
    兑换商品
    item_key: coffee|upgrade|late|coupon50
    """
    db = SessionLocal()
    try:
        gp = _get_or_create_points(db, openid)
        item = REDEEM_ITEMS.get(item_key)
        if not item:
            return {"success": False, "message": "未知的兑换商品"}

        if gp.total_points < item["points"]:
            return {"success": False, "message": f"积分不足！需要{item['points']}分，当前{gp.total_points}分"}

        gp.total_points -= item["points"]
        gp.total_spent += item["points"]

        log = PointLog(
            openid=openid, points=-item["points"], action=item["type"],
            description=description or item["name"]
        )
        db.add(log)

        db.commit()

        return {
            "success": True,
            "redeemed": item["name"],
            "spent": item["points"],
            "total_points": gp.total_points,
            "message": f"成功兑换：{item['name']}！已通知前台处理～",
        }
    finally:
        db.close()


def get_redeem_items() -> list:
    """获取可兑换商品列表（带用户积分显示）"""
    return [
        {"key": k, **v} for k, v in REDEEM_ITEMS.items()
    ]


def get_earn_rules() -> list:
    """获取积分获取规则"""
    return [{"key": k, **v} for k, v in EARN_RULES.items()]


def get_membership_info() -> list:
    """获取会员等级信息"""
    return [{"key": k, **v} for k, v in MEMBERSHIP_TIERS.items()]
