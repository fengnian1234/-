"""
积分体系服务 — 会员积分获取、兑换、等级管理
"""
from datetime import datetime, UTC
from models import SessionLocal, GuestPoints, PointLog, REDEEM_ITEMS, EARN_RULES, MEMBERSHIP_TIERS


def _get_or_create_points(db, openid: str) -> GuestPoints:
    """获取或创建用户积分记录"""
    gp = db.query(GuestPoints).filter(GuestPoints.openid == openid).first()
    if not gp:
        gp = GuestPoints(openid=openid, total_points=0, total_earned=0, base_earned=0, total_spent=0, membership="silver")
        db.add(gp)
        db.flush()
    # 存量用户迁移：base_earned 首次为空时用 total_earned 回填
    if not gp.base_earned and gp.total_earned > 0:
        gp.base_earned = gp.total_earned
        db.flush()
    return gp


def _update_membership(gp: GuestPoints):
    """根据基础积分（不含等级加成）更新会员等级"""
    base = gp.base_earned or 0
    if base >= 8000:
        gp.membership = "diamond"
    elif base >= 3000:
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
    获取积分（签到/评价/分享等）
    action: booking|checkin|review|share|birthday|xhs_note|social_post

    积分到账 = 基础积分 × 会员等级加成系数
    - 银卡 ×1.0 | 金卡 ×1.2 | 钻卡 ×1.4
    - 等级升级只看基础积分（base_earned），加成不计入升级门槛
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

        # 基础积分（EARN_RULES 中的原始值）
        # 入住消费：每5元5积分，不足5元补足5分
        if action == "booking" and amount:
            base_pts = ((amount + 4) // 5) * 5
        else:
            base_pts = amount or rule["points"]

        # 生日月 1.5 倍（先于等级加成）
        now = dt.now(UTC)
        birthday_bonus = False
        if gp.birthday_month and gp.birthday_month == now.month and action != "birthday":
            base_pts = int(base_pts * 1.5)
            birthday_bonus = True

        # 会员等级加成系数
        multiplier = MEMBERSHIP_TIERS.get(gp.membership, {}).get("point_multiplier", 1.0)
        earned_pts = max(1, int(base_pts * multiplier))  # 确保最少1分

        gp.total_points += earned_pts
        gp.total_earned += earned_pts    # 含加成，用于兑换
        gp.base_earned = (gp.base_earned or 0) + base_pts  # 基础分，用于等级升级

        desc = description or rule["name"]
        if birthday_bonus:
            desc += "（生日月×1.5）"
        if multiplier > 1.0:
            desc += f"（{MEMBERSHIP_TIERS[gp.membership]['name']}×{multiplier}）"

        log = PointLog(
            openid=openid, points=earned_pts, action=f"earn_{action}",
            description=desc
        )
        db.add(log)

        # 等级升级只用基础积分判断
        _update_membership(gp)
        db.commit()

        return {
            "success": True,
            "earned": earned_pts,
            "base_points": base_pts,
            "multiplier": multiplier,
            "total_points": gp.total_points,
            "membership": gp.to_dict()["membership_name"],
            "birthday_bonus": birthday_bonus,
        }
    finally:
        db.close()


def redeem(openid: str, item_key: str, description: str = "") -> dict:
    """
    兑换商品
    item_key: coffee|upgrade|late|tea_sample
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


def get_membership_info() -> dict:
    """获取会员等级信息（dict格式，方便前端按key访问）"""
    return {k: {"key": k, **v} for k, v in MEMBERSHIP_TIERS.items()}
