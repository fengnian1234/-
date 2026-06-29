"""
疗愈模块服务（云上·东林外专属）
- 一对一个案服务（音疗/芳香/情绪）
- 预约时间槽系统（提前2小时预约）
"""
from datetime import datetime, timedelta, date as date_type
from models import SessionLocal, HealingCourse, HealingAppointment
from bnb_context import get_service_bnb_id
from services.logger import error as log_error

BUSINESS_HOURS_START = 9   # 9:00
BUSINESS_HOURS_END = 20    # 20:00
SLOT_INTERVAL = 30         # 每30分钟一个时间槽
MIN_ADVANCE_HOURS = 2      # 至少提前2小时预约

# 疗愈模块专属东林外，覆写默认值
_get_bnb_id = lambda bnb_id=None: get_service_bnb_id(bnb_id, "donglinwai")


def _parse_duration_minutes(dur_str):
    """解析时长字符串为分钟数"""
    if not dur_str:
        return 60
    dur_str = dur_str.strip()
    if '小时' in dur_str and '分钟' in dur_str:
        # "1小时30分钟" 等
        parts = dur_str.replace('小时','|').replace('分钟','').split('|')
        return int(parts[0]) * 60 + int(parts[1]) if len(parts) > 1 else int(parts[0]) * 60
    elif '小时' in dur_str:
        return int(dur_str.replace('小时', '').strip()) * 60
    elif '分钟' in dur_str:
        return int(dur_str.replace('分钟', '').strip())
    return 60


def _time_to_minutes(t_str):
    """将 HH:MM 转为分钟数"""
    h, m = t_str.split(':')
    return int(h) * 60 + int(m)


def _minutes_to_time(m):
    """将分钟数转为 HH:MM"""
    return f"{m // 60:02d}:{m % 60:02d}"


def get_available_slots(course_id, tier_index, date_str, bnb_id=None):
    """
    获取指定日期和疗愈项目的可用时间槽。
    返回 [{time, label, available}] 列表。
    """
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        # 获取项目档位时长
        course = db.query(HealingCourse).filter(HealingCourse.id == course_id).first()
        if not course:
            return {"error": "项目不存在"}

        tiers = course.price_tiers or []
        if tier_index < 0 or tier_index >= len(tiers):
            return {"error": "档位不存在"}

        tier = tiers[tier_index]
        duration_min = _parse_duration_minutes(tier.get('duration', '1小时'))

        # 当天所有已确认预约
        appointments = db.query(HealingAppointment).filter(
            HealingAppointment.bnb_id == bnb_id,
            HealingAppointment.appointment_date == date_str,
            HealingAppointment.status.in_(["pending", "paid"])
        ).all()

        # 已占用时间段（分钟数范围）
        occupied = []
        for a in appointments:
            start = _time_to_minutes(a.appointment_time)
            end = start + a.duration_minutes
            occupied.append((start, end))

        # 生成时间槽
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        slots = []

        slot_start = BUSINESS_HOURS_START * 60  # 540 = 9:00
        slot_end = BUSINESS_HOURS_END * 60      # 1200 = 20:00

        while slot_start + duration_min <= slot_end:
            time_str = _minutes_to_time(slot_start)
            slot_available = True
            reason = None

            # 检查是否与已有预约冲突
            slot_finish = slot_start + duration_min
            for occ_start, occ_end in occupied:
                if slot_start < occ_end and slot_finish > occ_start:
                    slot_available = False
                    reason = "该时段已被预约"
                    break

            # 检查提前2小时限制（仅当天）
            if slot_available and date_str == today_str:
                # 当前时间 + 2小时 > 时段开始时间 → 不可用
                if now + timedelta(hours=MIN_ADVANCE_HOURS) > datetime.combine(
                    date_type.today(),
                    datetime.strptime(time_str, "%H:%M").time()
                ):
                    slot_available = False
                    reason = "需提前2小时预约"

            # 检查是否已过（仅当天）
            if slot_available and date_str == today_str:
                if now > datetime.combine(
                    date_type.today(),
                    datetime.strptime(time_str, "%H:%M").time()
                ):
                    slot_available = False
                    reason = "该时段已过"

            # 检查是否为过去日期
            if slot_available and date_str < today_str:
                slot_available = False
                reason = "不可预约过去日期"

            slots.append({
                "time": time_str,
                "label": f"{time_str} — {_minutes_to_time(slot_finish)}",
                "available": slot_available,
                "reason": reason,
            })

            slot_start += SLOT_INTERVAL

        return {
            "date": date_str,
            "course_name": course.name,
            "tier_duration": tier.get('duration'),
            "tier_price": tier.get('price'),
            "duration_minutes": duration_min,
            "slots": slots,
        }
    finally:
        db.close()


def create_appointment(data, bnb_id=None):
    """创建疗愈预约"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        course_id = data.get("course_id")
        tier_index = data.get("tier_index")
        date_str = data.get("date")
        time_str = data.get("time")
        guest_name = data.get("guest_name", "").strip()
        guest_phone = data.get("guest_phone", "").strip()

        # 参数校验
        if not all([course_id, tier_index is not None, date_str, time_str, guest_name, guest_phone]):
            return {"error": "请填写完整信息"}

        course = db.query(HealingCourse).filter(HealingCourse.id == course_id).first()
        if not course:
            return {"error": "项目不存在"}

        tiers = course.price_tiers or []
        if tier_index < 0 or tier_index >= len(tiers):
            return {"error": "档位不存在"}

        tier = tiers[tier_index]
        duration_min = _parse_duration_minutes(tier.get('duration', '1小时'))

        # 检查时段是否仍然可用
        slots_result = get_available_slots(course_id, tier_index, date_str, bnb_id=bnb_id)
        if "error" in slots_result:
            return slots_result

        target_slot = None
        for s in slots_result["slots"]:
            if s["time"] == time_str:
                target_slot = s
                break

        if not target_slot:
            return {"error": "时段不存在"}
        if not target_slot["available"]:
            return {"error": target_slot.get("reason", "该时段不可用")}

        # 创建预约
        appt = HealingAppointment(
            bnb_id=bnb_id,
            course_id=course_id,
            course_name=course.name,
            tier_index=tier_index,
            tier_duration=tier.get('duration'),
            tier_price=tier.get('price'),
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_openid=data.get("openid"),
            appointment_date=date_str,
            appointment_time=time_str,
            duration_minutes=duration_min,
            status="pending",
            pay_status="unpaid",
            note=data.get("note"),
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        return {
            "success": True,
            "appointment": appt.to_dict(),
            "message": (
                f"预约成功！\n"
                f"📋 {course.name}\n"
                f"⏰ {date_str} {time_str}（{tier.get('duration')}）\n"
                f"· ¥{tier.get('price')}\n"
                f"👤 {guest_name}\n"
                f"☎ {guest_phone}\n\n"
                f"· 琼儿老师将在约定时间等候您的到来～"
            ),
        }
    except Exception as e:
        db.rollback()
        log_error("healing.create_appointment", str(e), exc_info=True)
        return {"error": "预约失败，请稍后重试"}
    finally:
        db.close()


def confirm_payment(appointment_id, bnb_id=None):
    """模拟微信支付成功后确认预约"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        appt = db.query(HealingAppointment).filter(
            HealingAppointment.id == appointment_id,
            HealingAppointment.bnb_id == bnb_id,
        ).first()
        if not appt:
            return {"error": "预约不存在"}
        if appt.pay_status == "paid":
            return {"error": "已支付，无需重复支付"}
        appt.pay_status = "paid"
        appt.status = "paid"
        db.commit()
        return {"success": True, "message": "支付成功！· 琼儿老师将在约定时间等候您～"}
    except Exception as e:
        db.rollback()
        log_error("healing.confirm_payment", str(e), exc_info=True)
        return {"error": "支付确认失败，请稍后重试"}
    finally:
        db.close()


def get_appointments(date_str=None, bnb_id=None):
    """查询预约列表"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        q = db.query(HealingAppointment).filter(
            HealingAppointment.bnb_id == bnb_id,
            HealingAppointment.status.in_(["pending", "paid"])
        )
        if date_str:
            q = q.filter(HealingAppointment.appointment_date == date_str)
        q = q.order_by(HealingAppointment.appointment_date, HealingAppointment.appointment_time)
        return [a.to_dict() for a in q.all()]
    finally:
        db.close()


def get_healing_courses(bnb_id=None, category=None):
    """获取疗愈项目列表"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        q = db.query(HealingCourse).filter(
            HealingCourse.bnb_id == bnb_id,
            HealingCourse.is_available == True
        )
        if category:
            q = q.filter(HealingCourse.category == category)
        q = q.order_by(HealingCourse.sort_order)
        return [c.to_dict() for c in q.all()]
    finally:
        db.close()


def get_healing_categories(bnb_id=None):
    """获取疗愈类别列表"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        rows = db.query(HealingCourse.category).filter(
            HealingCourse.bnb_id == bnb_id,
            HealingCourse.is_available == True
        ).distinct().order_by(HealingCourse.sort_order).all()
        return [r[0] for r in rows]
    finally:
        db.close()


def format_healing_text(bnb_id=None):
    """格式化为微信文本输出"""
    bnb_id = _get_bnb_id(bnb_id)
    from bnb_context import get_bnb_config
    cfg = get_bnb_config(bnb_id)
    categories = get_healing_categories(bnb_id=bnb_id)

    lines = [f"· *{cfg['short_name']} · 疗愈空间*\n"]
    lines.append("所有项目均由琼儿老师一对一服务\n")

    for cat in categories:
        courses = get_healing_courses(bnb_id=bnb_id, category=cat)
        if not courses:
            continue
        lines.append(f"── *{cat}* ──")
        for c in courses:
            tiers = c.get('price_tiers', [])
            if len(tiers) == 1:
                t = tiers[0]
                lines.append(f"  {c['name']}  ¥{t['price']} / {t['duration']}")
            else:
                price_str = " / ".join(f"¥{t['price']}({t['duration']})" for t in tiers)
                lines.append(f"  {c['name']}")
                lines.append(f"    {price_str}")
            if c.get('description'):
                lines.append(f"    {c['description'][:80]}")
        lines.append("")

    lines.append(f"· {cfg['short_name']} | 庐山·东林寺旁")
    lines.append("☎ 回复「预订」或联系前台预约")
    lines.append("▸ 提示： 回复「疗愈」查看更多详情")
    return "\n".join(lines)
