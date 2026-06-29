"""
此山茶场预约服务层（云上·山纪专属）
- 日期/时间槽查询
- 预约创建与核验
- 点单解锁控制
"""
import random
import string
from datetime import date, datetime, timedelta
from models import SessionLocal, TeaReservation
from bnb_context import get_service_bnb_id

_get_bnb_id = lambda bnb_id=None: get_service_bnb_id(bnb_id, "shanji")

# ── 营业时间常量 ──
MORNING_START = 7   # 早场 7:00
MORNING_END = 10    # 早场 10:00
EVENING_START = 15  # 晚场 15:00
EVENING_END = 22    # 晚场 22:00
SLOT_INTERVAL = 30  # 30分钟一个时间槽
ALCOHOL_START_HOUR = 18  # 酒水18:00后开放
MAX_ADVANCE_DAYS = 7  # 最多提前7天


def _today_str():
    return date.today().strftime("%Y-%m-%d")


def _generate_reservation_code():
    """生成6位预约核验码（大写字母+数字，碰撞重试10次）"""
    chars = string.ascii_uppercase + string.digits
    db = SessionLocal()
    try:
        for _ in range(10):
            code = ''.join(random.choices(chars, k=6))
            if not db.query(TeaReservation).filter(
                TeaReservation.reservation_code == code
            ).first():
                return code
        # 10次全碰撞，加一位
        for _ in range(10):
            code = ''.join(random.choices(chars, k=7))
            if not db.query(TeaReservation).filter(
                TeaReservation.reservation_code == code
            ).first():
                return code
        return ''.join(random.choices(chars, k=8))
    finally:
        db.close()


def get_available_dates(bnb_id=None):
    """获取可预约日期列表（今天起7天）"""
    bnb_id = _get_bnb_id(bnb_id)
    today = date.today()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    dates = []
    for i in range(MAX_ADVANCE_DAYS):
        d = today + timedelta(days=i)
        if i == 0:
            label = "今天"
        elif i == 1:
            label = "明天"
        else:
            label = f"{i}天后"
        dates.append({
            "date": d.strftime("%Y-%m-%d"),
            "label": label,
            "weekday": weekdays[d.weekday()],
            "available": True,
        })
    return dates


def get_available_slots(date_str, bnb_id=None):
    """获取指定日期的可用时间槽"""
    bnb_id = _get_bnb_id(bnb_id)
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "日期格式错误，应为 YYYY-MM-DD"}

    today = date.today()
    if target_date < today:
        return {"error": "不可预约过去的日期"}
    if target_date > today + timedelta(days=MAX_ADVANCE_DAYS - 1):
        return {"error": f"仅可预约{MAX_ADVANCE_DAYS}天内的日期"}

    # 生成当天所有时间槽
    all_slots = []
    # 早场
    h = MORNING_START
    m = 0
    while h < MORNING_END or (h == MORNING_END and m == 0):
        all_slots.append(f"{h:02d}:{m:02d}")
        m += SLOT_INTERVAL
        if m >= 60:
            h += 1
            m -= 60
    # 晚场
    h = EVENING_START
    m = 0
    while h < EVENING_END or (h == EVENING_END and m == 0):
        all_slots.append(f"{h:02d}:{m:02d}")
        m += SLOT_INTERVAL
        if m >= 60:
            h += 1
            m -= 60

    # 查询当天已确认的预约（含 pending 和 checked_in 状态）
    db = SessionLocal()
    try:
        booked = db.query(TeaReservation.reservation_time).filter(
            TeaReservation.bnb_id == bnb_id,
            TeaReservation.reservation_date == date_str,
            TeaReservation.status.in_(["pending", "checked_in"]),
        ).all()
        booked_times = {b[0] for b in booked}
    finally:
        db.close()

    is_today = (target_date == today)
    now = datetime.now()
    now_time = now.strftime("%H:%M")

    slots = []
    for t in all_slots:
        available = t not in booked_times
        reason = None
        if not available:
            reason = "该时段已被预约"
        elif is_today and t < now_time:
            available = False
            reason = "该时段已过"

        # 判断时段归属
        hour = int(t.split(":")[0])
        if hour < MORNING_END + 1:
            period = "早场"
        else:
            period = "晚场"

        slots.append({
            "time": t,
            "label": t,
            "period": period,
            "available": available,
            "reason": reason,
        })

    return {
        "date": date_str,
        "slots": slots,
    }


def create_reservation(data, bnb_id=None):
    """创建茶场预约"""
    bnb_id = _get_bnb_id(bnb_id)

    guest_name = (data.get("guest_name") or "").strip()
    guest_phone = (data.get("guest_phone") or "").strip()
    guest_count = data.get("guest_count", 1)
    reservation_date = (data.get("reservation_date") or "").strip()
    reservation_time = (data.get("reservation_time") or "").strip()
    openid = (data.get("openid") or "web_user").strip()

    # ── 参数校验 ──
    if not guest_name:
        return {"error": "请输入姓名"}
    if not guest_phone or len(guest_phone) < 10:
        return {"error": "请输入正确的手机号"}
    if guest_count not in (1, 2):
        return {"error": "人数仅支持单人(1)或双人(2)"}
    if not reservation_date:
        return {"error": "请选择预约日期"}
    if not reservation_time:
        return {"error": "请选择到店时间"}

    # 日期合法性
    try:
        target_date = datetime.strptime(reservation_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "日期格式错误"}
    today = date.today()
    if target_date < today:
        return {"error": "不可预约过去的日期"}
    if target_date > today + timedelta(days=MAX_ADVANCE_DAYS - 1):
        return {"error": f"仅可预约{MAX_ADVANCE_DAYS}天内的日期"}

    # 时间合法性
    try:
        datetime.strptime(reservation_time, "%H:%M")
    except ValueError:
        return {"error": "时间格式错误"}

    # 时间槽二次校验（防止并发冲突）
    slots_info = get_available_slots(reservation_date, bnb_id=bnb_id)
    if "error" in slots_info:
        return slots_info
    time_slot = next((s for s in slots_info["slots"] if s["time"] == reservation_time), None)
    if not time_slot:
        return {"error": "所选时间不在营业时段内"}
    if not time_slot["available"]:
        return {"error": f"该时段不可预约：{time_slot.get('reason', '已被占用')}"}

    # 生成预约码
    reservation_code = _generate_reservation_code()

    db = SessionLocal()
    try:
        reservation = TeaReservation(
            bnb_id=bnb_id,
            openid=openid,
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_count=guest_count,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            reservation_code=reservation_code,
            status="pending",
            ordering_unlocked=False,
        )
        db.add(reservation)
        db.commit()
        result = reservation.to_dict()
        return {"success": True, "reservation": result}
    except Exception as e:
        db.rollback()
        return {"error": f"预约创建失败：{e}"}
    finally:
        db.close()


def check_in_reservation(code, bnb_id=None):
    """核验预约码，解锁点单功能"""
    bnb_id = _get_bnb_id(bnb_id)
    code = (code or "").strip().upper()
    if not code or len(code) < 6:
        return {"error": "请输入有效的6位预约码"}

    db = SessionLocal()
    try:
        reservation = db.query(TeaReservation).filter(
            TeaReservation.reservation_code == code,
            TeaReservation.bnb_id == bnb_id,
        ).first()

        if not reservation:
            return {"error": "预约码无效，请核对后重试"}

        if reservation.status == "checked_in":
            return {
                "success": True,
                "reservation": reservation.to_dict(),
                "message": "该预约码已核验，点单功能已解锁",
            }

        if reservation.status == "cancelled":
            return {"error": "该预约已取消"}

        if reservation.status == "completed":
            return {"error": "该预约已完成"}

        # 检查预约日期是否为今天
        reservation_date = reservation.reservation_date
        today = _today_str()
        if reservation_date != today:
            return {"error": f"预约日期为 {reservation_date}，仅可当天核验。请今天({today})再来"}

        # 核验通过
        reservation.status = "checked_in"
        reservation.ordering_unlocked = True
        reservation.checked_in_at = datetime.utcnow()
        db.commit()
        return {
            "success": True,
            "reservation": reservation.to_dict(),
            "message": "核验成功！点单功能已解锁，请开始点单",
        }
    except Exception as e:
        db.rollback()
        return {"error": f"核验失败：{e}"}
    finally:
        db.close()


def is_ordering_unlocked(code, bnb_id=None):
    """查询预约码对应的点单解锁状态"""
    bnb_id = _get_bnb_id(bnb_id)
    code = (code or "").strip().upper()
    if len(code) < 6:
        return {"unlocked": False, "reason": "无效的预约码"}

    db = SessionLocal()
    try:
        reservation = db.query(TeaReservation).filter(
            TeaReservation.reservation_code == code,
            TeaReservation.bnb_id == bnb_id,
        ).first()
        if not reservation:
            return {"unlocked": False, "reason": "预约码无效"}
        return {
            "unlocked": reservation.ordering_unlocked,
            "reservation": reservation.to_dict(),
        }
    finally:
        db.close()


def get_reservation_by_code(code, bnb_id=None):
    """按预约码查询预约详情"""
    bnb_id = _get_bnb_id(bnb_id)
    code = (code or "").strip().upper()
    if len(code) < 6:
        return None

    db = SessionLocal()
    try:
        reservation = db.query(TeaReservation).filter(
            TeaReservation.reservation_code == code,
            TeaReservation.bnb_id == bnb_id,
        ).first()
        return reservation.to_dict() if reservation else None
    finally:
        db.close()
