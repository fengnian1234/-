"""
JSON API 路由 — 员工看板、预订管理、点餐支付、平台监控、积分、茶园、疗愈、小程序
"""
from app import app
from common import _require_staff_auth, rate_limit
from flask import request, jsonify
from services.logger import error as log_error
from config import DEBUG, BNB_NAME, BASE_URL, WECHAT_MINI_APP_ID, WECHAT_MINI_APP_SECRET


def _err(msg: str, code: int = 400):
    """统一 API 错误响应: {"success": False, "message": msg}"""
    return jsonify({"success": False, "message": msg}), code


def _ok(data: dict = None):
    """统一 API 成功响应: {"success": True, ...data}"""
    if data is None:
        data = {}
    data["success"] = True
    return jsonify(data)


# ══════════════════════════════════════════════════════════
#  员工通知看板（要求2：醒目有效的通知方式）
# ══════════════════════════════════════════════════════════
@app.route("/api/staff/dashboard")
def api_staff_dashboard():
    """获取员工看板数据 — 含点餐订单（前台）+ 服务请求（主理人）"""
    from services.notify import get_pending_requests, get_all_requests_today, get_notification_stats
    from services.booking import get_review_reminders_due
    from models import SessionLocal, Order
    from datetime import datetime, UTC

    stats = get_notification_stats()
    pending_svc = get_pending_requests()
    all_today_svc = get_all_requests_today()
    completed_svc = [r for r in all_today_svc if r["status"] == "completed"]

    # 点餐订单：已支付未完成的
    db = SessionLocal()
    try:
        paid_orders = db.query(Order).filter(
            Order.pay_status == "paid",
            Order.status.in_(["paid", "preparing"])
        ).order_by(Order.created_at.asc()).all()
        orders_frontdesk = [o.to_dict() for o in paid_orders if o.notify_target == "frontdesk"]
        orders_manager = [o.to_dict() for o in paid_orders if o.notify_target == "manager"]
        # 今日完成的订单
        today = datetime.now(UTC).date()
        completed_orders = db.query(Order).filter(
            Order.status.in_(["completed", "delivered"]),
            Order.created_at >= today
        ).order_by(Order.created_at.desc()).limit(20).all()
    finally:
        db.close()

    # 检查好评推送提醒
    review_reminders = get_review_reminders_due()

    # 合并统计
    total_pending = stats["pending"] + len(orders_frontdesk) + len(orders_manager)
    stats["pending"] = total_pending
    stats["frontdesk_pending"] = len(orders_frontdesk)
    stats["manager_pending"] = stats["pending"] - len(orders_frontdesk)  # original + manager orders

    return jsonify({
        "stats": stats,
        "pending_svc": pending_svc,
        "pending_orders_frontdesk": orders_frontdesk,
        "pending_orders_manager": orders_manager,
        "completed_svc": completed_svc[:20],
        "completed_orders": [o.to_dict() for o in completed_orders],
        "review_reminders_count": len(review_reminders),
    })

@app.route("/api/staff/acknowledge", methods=["POST"])
@_require_staff_auth
def api_acknowledge_request():
    """员工确认收到请求 — 需员工鉴权"""
    from services.notify import acknowledge_request
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"success": False, "message": "缺少请求ID"}), 400
    acknowledge_request(data["id"], data.get("handler", "前台"))
    return jsonify({"success": True})

@app.route("/api/staff/complete", methods=["POST"])
@_require_staff_auth
def api_complete_request():
    """员工完成请求 — 需员工鉴权"""
    from services.notify import complete_request
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"success": False, "message": "缺少请求ID"}), 400
    complete_request(data["id"], data.get("notes", ""))
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════
#  预订管理API（要求1、3、4）
# ══════════════════════════════════════════════════════════
@app.route("/api/booking/confirm", methods=["POST"])
@_require_staff_auth
def api_confirm_booking():
    """前台确认预订（解锁AI）— 需员工鉴权"""
    from services.booking import confirm_booking
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "数据为空"}), 400

    required = ["openid", "guest_name", "platform", "check_in", "check_out"]
    for field in required:
        if field not in data:
            return jsonify({"success": False, "message": f"缺少字段: {field}"}), 400

    booking = confirm_booking(
        openid=data["openid"],
        guest_name=data["guest_name"],
        phone=data.get("phone", ""),
        platform=data["platform"],
        check_in=data["check_in"],
        check_out=data["check_out"],
        room_type=data.get("room_type", ""),
    )
    # 生成到店前关怀消息（Phase 3 通过微信客服消息发送）
    from services.ai import generate_pre_arrival_message
    pre_arrival_msg = generate_pre_arrival_message(
        guest_name=data["guest_name"],
        check_in_date=data["check_in"],
        room_name=data.get("room_type", ""),
        room_code=booking.room_code,
        bnb_id=booking.bnb_id,
    )
    return jsonify({
        "success": True,
        "booking": booking.to_dict(),
        "room_code": booking.room_code,
        "room_code_tip": f"🔑 房间共享码：{booking.room_code}\n同住人回复「绑定房间 {booking.room_code}」即可共享AI管家全部功能",
        "pre_arrival_message": pre_arrival_msg,
    })

@app.route("/api/booking/<int:booking_id>/checkin", methods=["POST"])
@_require_staff_auth
def api_check_in(booking_id: int):
    """办理入住 — 需员工鉴权"""
    from services.booking import check_in_booking
    data = request.get_json() or {}
    booking = check_in_booking(booking_id, data.get("room_number", ""))
    if not booking:
        return jsonify({"success": False, "message": "预订不存在"}), 404
    return jsonify({"success": True, "booking": booking.to_dict()})

@app.route("/api/booking/<int:booking_id>/checkout", methods=["POST"])
@_require_staff_auth
def api_check_out(booking_id: int):
    """办理退房（触发30分钟好评推送倒计时）— 需员工鉴权"""
    from services.booking import check_out_booking
    booking = check_out_booking(booking_id)
    if not booking:
        return jsonify({"success": False, "message": "预订不存在"}), 404
    # 生成离店后关怀消息（Phase 3 通过微信客服消息发送）
    from services.ai import generate_post_stay_message
    post_stay_msg = generate_post_stay_message(
        guest_name=booking.guest_name or "",
        room_name=booking.room_type or "",
        bnb_id=booking.bnb_id,
    )
    return jsonify({
        "success": True,
        "message": f"退房成功，将在30分钟后推送好评提醒",
        "booking": booking.to_dict(),
        "post_stay_message": post_stay_msg,
    })

@app.route("/api/booking/check-ai", methods=["POST"])
def api_check_ai_enabled():
    """检查用户AI是否解锁"""
    from services.booking import is_ai_enabled
    from bnb_context import get_current_bnb_id
    data = request.get_json()
    if not data or "openid" not in data:
        return _err("缺少openid")
    enabled = is_ai_enabled(data["openid"], bnb_id=get_current_bnb_id())
    return jsonify({"ai_enabled": enabled})


@app.route("/api/booking/bind-room", methods=["POST"])
def api_bind_room_guest():
    """合住人通过房间码自助绑定（客人自助，无需员工鉴权）"""
    from services.booking import bind_room_guest
    data = request.get_json()
    if not data or "openid" not in data or "room_code" not in data:
        return jsonify({"success": False, "message": "缺少 openid 或 room_code"}), 400
    result = bind_room_guest(data["room_code"].upper(), data["openid"],
                             data.get("guest_name", ""), data.get("relation", "同住"))
    return jsonify(result)


@app.route("/api/booking/room-code", methods=["POST"])
def api_get_room_code():
    """获取用户的房间共享码"""
    from services.booking import get_booking_by_openid, get_room_guests
    from bnb_context import get_current_bnb_id
    data = request.get_json()
    if not data or "openid" not in data:
        return jsonify({"success": False, "message": "缺少 openid"}), 400
    booking = get_booking_by_openid(data["openid"], bnb_id=get_current_bnb_id())
    if not booking:
        return jsonify({"success": False, "message": "未找到有效预订"})
    return jsonify({
        "success": True,
        "room_code": booking.get("room_code", ""),
        "room_type": booking.get("room_type", ""),
        "check_in_date": booking.get("check_in_date", ""),
        "guests": get_room_guests(booking.get("room_code", "")),
    })


# ══════════════════════════════════════════════════════════
#  好评推送检查（要求4：退房30分钟后自动推送）
# ══════════════════════════════════════════════════════════
@app.route("/api/review/check-reminders", methods=["POST"])
def api_check_review_reminders():
    """
    检查并推送好评提醒
    此接口应由定时任务每分钟调用
    """
    from wechat import check_and_send_review_reminders
    results = check_and_send_review_reminders()
    return jsonify({
        "success": True,
        "sent_count": len(results),
        "details": results,
    })

@app.route("/api/review/platforms")
def api_review_platforms():
    """获取所有平台评价链接"""
    from services.monitor import get_platform_review_links
    from bnb_context import get_current_bnb_id
    return jsonify(get_platform_review_links(bnb_id=get_current_bnb_id()))


# ══════════════════════════════════════════════════════════
#  点餐 + 微信支付（要求5）
# ══════════════════════════════════════════════════════════
@app.route("/api/order", methods=["POST"])
def api_create_order():
    """创建点餐订单"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "数据为空"}), 400

    openid = data.get("openid", "web_user")
    items = data.get("items", [])
    room_number = data.get("room_number", "")
    remark = data.get("remark", "")

    if not items:
        return jsonify({"success": False, "message": "请选择菜品"}), 400
    # 限流：同一用户每分钟最多10次
    if not rate_limit(f"order:{openid}", max_req=10, window=60):
        return jsonify({"success": False, "message": "下单太频繁，请稍后再试"}), 429

    from services.menu import create_order
    order = create_order(openid, items, room_number, remark)

    return jsonify({
        "success": True,
        "message": "下单成功！",
        "order": order.to_dict(),
    })


@app.route("/api/order/pay", methods=["POST"])
def api_order_pay():
    """模拟微信支付 — 确认订单付款"""
    data = request.get_json()
    if not data:
        return _err("数据为空")
    order_id = data.get("order_id")
    if not order_id:
        return _err("缺少订单ID")
    from models import SessionLocal, Order
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return _err("订单不存在", 404)
        if order.pay_status == "paid":
            return _err("已支付，无需重复支付")
        order.pay_status = "paid"
        order.status = "paid"
        db.commit()
        return jsonify({
            "success": True,
            "message": "支付成功",
            "order": order.to_dict(),
        })
    except Exception as e:
        db.rollback()
        from services.logger import error as log_error
        log_error(f"api.pay_order 失败: {e}", exc_info=True)
        return jsonify({"message": "支付处理失败，请稍后重试"}), 500
    finally:
        db.close()


@app.route("/api/order/<int:order_id>/status", methods=["POST"])
def api_order_status(order_id: int):
    """更新点餐订单状态（员工看板用）paid→preparing→delivered→completed"""
    data = request.get_json() or {}
    new_status = data.get("status", "")
    if new_status not in ("preparing", "delivered", "completed", "cancelled"):
        return jsonify({"success": False, "message": f"无效状态: {new_status}"}), 400
    from models import SessionLocal, Order
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return jsonify({"success": False, "message": "订单不存在"}), 404
        order.status = new_status
        if new_status == "delivered":
            order.status = "completed"  # 送餐即完成
        db.commit()
        return jsonify({"success": True, "status": order.status, "order": order.to_dict()})
    except Exception as e:
        db.rollback()
        log_error(f"api.order_status 失败: {e}", exc_info=True)
        return jsonify({"success": False, "message": "状态更新失败，请稍后重试"}), 500
    finally:
        db.close()


@app.route("/api/pay/create", methods=["POST"])
def api_create_payment():
    """
    创建微信支付订单（要求5：微信支付）
    实际部署时需要完整的微信支付商户配置
    """
    from services.menu import create_wechat_pay_params
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "数据为空"}), 400

    pay_result = create_wechat_pay_params(
        openid=data.get("openid", ""),
        order_id=data.get("order_id", 0),
        total_fee=data.get("total_fee", 0),
        body=f"{BNB_NAME} - 咖啡简餐",
        notify_url=f"{BASE_URL}/api/pay/notify",
    )

    return jsonify({"success": True, **pay_result})

@app.route("/api/pay/notify", methods=["POST"])
def api_pay_notify():
    """微信支付回调通知"""
    from services.menu import handle_pay_notify
    result = handle_pay_notify(request.data)
    return jsonify(result)


# ══════════════════════════════════════════════════════════
#  平台信息收集（要求6：子Agent接口）
# ══════════════════════════════════════════════════════════
@app.route("/api/monitor/summary")
def api_monitor_summary():
    """获取各平台信息汇总（供主Agent使用）"""
    from services.monitor import agent_collect_platform_info
    from bnb_context import get_current_bnb_id
    info = agent_collect_platform_info(bnb_id=get_current_bnb_id())
    return jsonify(info)

@app.route("/api/monitor/report")
def api_monitor_report():
    """获取平台口碑文字报告"""
    from services.monitor import generate_monitor_report
    from bnb_context import get_current_bnb_id
    return jsonify({"report": generate_monitor_report(bnb_id=get_current_bnb_id())})

@app.route("/api/monitor/collect", methods=["POST"])
@_require_staff_auth
def api_trigger_collection():
    """触发平台信息收集（昂贵操作，需员工鉴权）"""
    from services.monitor import search_platform_mentions
    results = search_platform_mentions()
    return jsonify({"success": True, "results": results})


# ══════════════════════════════════════════════════════════
#  平台预订链接（要求3）
# ══════════════════════════════════════════════════════════
@app.route("/api/booking/platforms")
def api_booking_platforms():
    """获取所有预订平台链接"""
    from config import BOOKING_PLATFORMS
    return jsonify(BOOKING_PLATFORMS)


# ══════════════════════════════════════════════════════════
#  积分体系 API
# ══════════════════════════════════════════════════════════
@app.route("/api/points/<openid>")
def api_get_points(openid: str):
    """获取用户积分概览"""
    from services.points import get_guest, get_logs, get_redeem_items, get_earn_rules, get_membership_info
    guest = get_guest(openid)
    return jsonify({
        "guest": guest,
        "logs": get_logs(openid, 10) if guest else [],
        "redeem_items": get_redeem_items(),
        "earn_rules": get_earn_rules(),
        "membership_info": get_membership_info(),
    })

@app.route("/api/points/earn", methods=["POST"])
def api_earn_points():
    """获取积分（签到/评价/分享等）"""
    from services.points import earn_points, EARN_RULES
    data = request.get_json()
    if not data or "openid" not in data or "action" not in data:
        return jsonify({"success": False, "message": "缺少openid或action"}), 400
    # 校验 action 合法性
    if data["action"] not in EARN_RULES:
        return jsonify({"success": False, "message": f"无效的action: {data['action']}"}), 400
    # 限流：同一用户每分钟最多5次
    if not rate_limit(f"earn:{data['openid']}", max_req=5, window=60):
        return jsonify({"success": False, "message": "操作太频繁，请稍后再试"}), 429
    result = earn_points(data["openid"], data["action"], data.get("amount"), data.get("description", ""))
    return jsonify(result)

@app.route("/api/points/redeem", methods=["POST"])
def api_redeem():
    """兑换商品"""
    from services.points import redeem, REDEEM_ITEMS
    data = request.get_json()
    if not data or "openid" not in data or "item" not in data:
        return jsonify({"success": False, "message": "缺少openid或item"}), 400
    # 校验 item 合法性
    if data["item"] not in REDEEM_ITEMS:
        return jsonify({"success": False, "message": f"无效的兑换项: {data['item']}"}), 400
    # 限流：同一用户每分钟最多5次
    if not rate_limit(f"redeem:{data['openid']}", max_req=5, window=60):
        return jsonify({"success": False, "message": "操作太频繁，请稍后再试"}), 429
    result = redeem(data["openid"], data["item"], data.get("description", ""))
    return jsonify(result)


# ══════════════════════════════════════════════════════════
#  多平台订单聚合
# ══════════════════════════════════════════════════════════
@app.route("/api/orders/dashboard")
def api_orders_dashboard():
    """获取订单看板统计数据"""
    from services.orders import get_dashboard_stats, get_room_calendar, get_platforms
    from bnb_context import get_current_bnb_id
    stats = get_dashboard_stats()
    stats["calendar"] = get_room_calendar(14, bnb_id=get_current_bnb_id())
    stats["platform_list"] = get_platforms()
    return jsonify(stats)

@app.route("/api/orders", methods=["GET", "POST"])
def api_orders():
    """查询或新增订单"""
    from services.orders import get_orders, add_order
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "数据为空"}), 400
        result = add_order(data)
        return jsonify(result)
    else:
        platform = request.args.get("platform")
        status = request.args.get("status")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        return jsonify(get_orders(date_from, date_to, platform, status))

@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def api_update_order_status(order_id: int):
    """更新订单状态"""
    from services.orders import update_order_status
    data = request.get_json() or {}
    result = update_order_status(order_id, data.get("status", ""), data.get("room_number", ""))
    return jsonify(result)


# ══════════════════════════════════════════════════════════
#  周报生成（DOCX）
# ══════════════════════════════════════════════════════════
@app.route("/api/report/weekly", methods=["POST"])
@_require_staff_auth
def api_generate_weekly_report():
    """
    生成口碑监控周报（DOCX格式）— 昂贵操作，需员工鉴权
    """
    from services.report import generate_weekly_report
    try:
        result = generate_weekly_report()
        return jsonify(result)
    except Exception:
        from services.logger import error as log_error
        log_error(f"api.staff.acknowledge: 操作失败", exc_info=True)
        return jsonify({"success": False, "message": "操作失败，请稍后重试"}), 500


# ══════════════════════════════════════════════════════════
#  快捷服务 H5 请求
# ══════════════════════════════════════════════════════════
@app.route("/api/service/request", methods=["POST"])
def api_create_service_request():
    """H5页面创建服务请求（通知员工看板）"""
    from services.notify import create_service_request
    data = request.get_json()
    if not data or "service_name" not in data:
        return jsonify({"success": False, "message": "缺少service_name"}), 400
    req = create_service_request(
        openid=data.get("openid", "web_user"),
        service_name=data["service_name"],
        room_number=data.get("room_number", ""),
        urgency=data.get("urgency", "normal"),
        notes=data.get("notes", ""),
    )
    return jsonify({"success": True, "request": req.to_dict()})


# ══════════════════════════════════════════════════════════
#  微信模拟器 API（项目未落成期间的测试工具）
# ══════════════════════════════════════════════════════════
class _MockWechatMessage:
    """模拟微信消息对象，供模拟器使用"""
    def __init__(self, content: str, openid: str):
        self.content = content
        self.text = content
        self.source = openid
        self.from_user = openid
        self.type = 'text'

@app.route("/api/simulate-chat", methods=["POST"])
def api_simulate_chat():
    """
    模拟微信消息处理（用于本地测试）
    接收 {"content": "...", "openid": "test_xxx"}
    返回 {"reply": "...", "handler": "keyword|ai|fallback", "mode": "...", "matched": "..."}
    """
    from wechat import match_keyword
    from services.ai import get_conversation_mode

    data = request.get_json()
    if not data or "content" not in data:
        return _err("缺少content字段")

    content = data["content"].strip()
    openid = data.get("openid", "sim_test_user")

    if not content:
        return jsonify({"reply": "请输入消息内容", "handler": "empty", "mode": "travel_advisor", "matched": None})

    # 构建模拟消息
    msg = _MockWechatMessage(content, openid)

    # 1. 尝试关键词匹配
    from wechat import match_keyword as _match
    from services.ai import get_conversation_mode as _get_mode
    handler, match = _match(content)
    if handler:
        try:
            reply = handler(msg, match)
            return jsonify({
                "reply": reply,
                "handler": "keyword",
                "mode": _get_mode(openid),
                "matched": str(match.re.pattern) if match else None,
            })
        except Exception:
            from services.logger import debug
            debug("关键词匹配异常，降级到AI", exc_info=True)

    # 2. AI 智能对话
    mode = _get_mode(openid)
    try:
        if mode == "travel_advisor":
            from services.ai import chat_travel_advisor
            reply = chat_travel_advisor(openid, content)
            handler_type = "ai_travel_advisor"
        elif mode == "pre_arrival":
            from services.ai import chat_pre_arrival
            reply = chat_pre_arrival(openid, content)
            handler_type = "ai_pre_arrival"
        elif mode == "post_stay":
            from services.ai import chat_post_stay
            reply = chat_post_stay(openid, content)
            handler_type = "ai_post_stay"
        else:
            from services.ai import chat
            reply = chat(openid, content)
            handler_type = "ai_guest_butler"

        return jsonify({
            "reply": reply,
            "handler": handler_type,
            "mode": mode,
            "matched": None,
        })
    except Exception:
        from services.logger import warning
        warning("AI对话异常，返回兜底回复", exc_info=True)

    # 3. 兜底
    return jsonify({
        "reply": "我收到了您的消息～\n\n如需帮助，可以回复数字 1-5 使用快捷功能，或回复「人工」转接人工客服。",
        "handler": "fallback",
        "mode": mode,
        "matched": None,
    })


@app.route("/api/simulate/reset", methods=["POST"])
def api_simulate_reset():
    """重置模拟用户对话历史"""
    from services.ai import reset_conversation as ai_reset
    data = request.get_json() or {}
    openid = data.get("openid", "sim_test_user")
    ai_reset(openid)
    return jsonify({"success": True, "message": f"已重置 {openid} 的对话历史"})


@app.route("/api/simulate/mode", methods=["POST"])
def api_simulate_set_mode():
    """
    设置模拟用户的 AI 模式（仅 DEBUG 模式可用）
    """
    if not DEBUG:
        return jsonify({"success": False, "message": "模拟器仅限开发模式使用"}), 403
    from services.ai import get_conversation_mode, reset_conversation
    from models import SessionLocal, Booking
    from datetime import datetime, timedelta, UTC

    data = request.get_json() or {}
    openid = data.get("openid", "sim_test_user")
    mode = data.get("mode", "travel_advisor")

    if mode == "pre_arrival":
        # 已预订但未入住：创建 confirmed 预订，入住日期设为未来
        db = SessionLocal()
        try:
            # 清理所有旧记录，避免 is_checked_in 误判
            db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status.in_(["confirmed", "checked_in", "checked_out"])
            ).update({"status": "cancelled"}, synchronize_session=False)
            db.commit()
            existing = db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status == "confirmed"
            ).first()
            if not existing:
                now = datetime.now(UTC)
                booking = Booking(
                    openid=openid,
                    guest_name="测试客人",
                    phone="13800000000",
                    platform="携程",
                    check_in_date=str((now + timedelta(days=3)).date()),  # 3天后入住
                    check_out_date=str((now + timedelta(days=5)).date()),
                    room_type="山野大床房",
                    status="confirmed",
                    ai_enabled=True,
                )
                db.add(booking)
                db.commit()
                reset_conversation(openid)
        finally:
            db.close()

    elif mode == "guest_butler":
        # 已入住：创建 checked_in 预订
        db = SessionLocal()
        try:
            # 清理所有旧记录，确保 is_checked_in 唯一判断
            db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status.in_(["confirmed", "checked_in", "checked_out"])
            ).update({"status": "cancelled"}, synchronize_session=False)
            db.commit()
            existing = db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status == "checked_in"
            ).first()
            if not existing:
                now = datetime.now(UTC)
                booking = Booking(
                    openid=openid,
                    guest_name="测试客人",
                    phone="13800000000",
                    platform="携程",
                    check_in_date=str(now.date()),
                    check_out_date=str((now + timedelta(days=2)).date()),
                    room_type="山野大床房",
                    status="checked_in",
                    ai_enabled=True,
                )
                db.add(booking)
                db.commit()
                reset_conversation(openid)
        finally:
            db.close()

    elif mode == "post_stay":
        db = SessionLocal()
        try:
            # 清理活跃预订（confirmed/checked_in），避免 is_ai_enabled 误判
            db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status.in_(["confirmed", "checked_in"])
            ).update({"status": "checked_out", "checked_out_at": datetime.now(UTC)}, synchronize_session=False)
            db.commit()
            existing = db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status == "checked_out"
            ).first()
            if not existing:
                now = datetime.now(UTC)
                booking = Booking(
                    openid=openid,
                    guest_name="测试客人",
                    phone="13800000000",
                    platform="携程",
                    check_in_date=str((now - timedelta(days=3)).date()),
                    check_out_date=str((now - timedelta(days=1)).date()),
                    room_type="山野大床房",
                    status="checked_out",
                    ai_enabled=True,
                    checked_out_at=now - timedelta(days=1),
                )
                db.add(booking)
                db.commit()
                reset_conversation(openid)
        finally:
            db.close()

    elif mode == "travel_advisor":
        db = SessionLocal()
        try:
            db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status.in_(["confirmed", "checked_in", "checked_out"])
            ).update({"status": "cancelled"}, synchronize_session=False)
            db.commit()
            db.commit()
            reset_conversation(openid)
        finally:
            db.close()

    current_mode = get_conversation_mode(openid)
    return jsonify({
        "success": True,
        "mode": current_mode,
        "message": f"当前 AI 模式: {current_mode}",
    })


@app.route("/api/simulate/keywords")
def api_simulate_keywords():
    """返回所有关键词路由列表（供模拟器展示可测试的关键词）"""
    import re as _re
    from wechat import KEYWORD_ROUTES
    routes = []
    for pattern, handler in KEYWORD_ROUTES:
        p = pattern.strip("^$")
        p = _re.sub(r'\([^)]*\)', '1', p)
        p = _re.sub(r'\\d\+', '1', p)
        routes.append({
            "pattern": pattern,
            "example": p,
        })
    return jsonify({"routes": routes})


# ══════════════════════════════════════════════════════════
#  茶园模块 API（云上·山纪）
# ══════════════════════════════════════════════════════════
@app.route("/api/tea/types")
def api_tea_types():
    from services.tea import get_tea_types
    from bnb_context import get_current_bnb_id
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "types": get_tea_types(bnb_id=bnb_id)})

@app.route("/api/tea/experiences")
def api_tea_experiences():
    from services.tea import get_tea_experiences
    from bnb_context import get_current_bnb_id
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "experiences": get_tea_experiences(bnb_id=bnb_id)})

@app.route("/api/tea/products")
def api_tea_products():
    from services.tea import get_tea_products
    from bnb_context import get_current_bnb_id
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "products": get_tea_products(bnb_id=bnb_id)})


# ══════════════════════════════════════════════════════════
#  此山茶场预约 API（云上·山纪专属）
# ══════════════════════════════════════════════════════════

@app.route("/api/tea/reservation/dates")
def api_tea_reservation_dates():
    """获取可预约日期列表（7天窗口）"""
    from services.tea_reservation import get_available_dates
    from bnb_context import get_current_bnb_id
    from datetime import datetime
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "dates": get_available_dates(bnb_id=bnb_id)})


@app.route("/api/tea/reservation/slots")
def api_tea_reservation_slots():
    """获取指定日期的可用时间槽"""
    from services.tea_reservation import get_available_slots
    from bnb_context import get_current_bnb_id
    from datetime import datetime
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    result = get_available_slots(date_str, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify({"success": True, **result})


@app.route("/api/tea/reservation/book", methods=["POST"])
def api_tea_reservation_book():
    """创建茶场预约（山纪专属）"""
    from services.tea_reservation import create_reservation
    bnb_id = request.args.get("bnb_id")  # None → 服务层默认 shanji
    data = request.get_json(silent=True) or {}
    data["openid"] = data.get("openid", "web_user")
    result = create_reservation(data, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)


@app.route("/api/tea/reservation/checkin", methods=["POST"])
@_require_staff_auth
def api_tea_reservation_checkin():
    """核验预约码，解锁点单功能（员工操作，山纪专属）"""
    from services.tea_reservation import check_in_reservation
    bnb_id = request.args.get("bnb_id")  # None → 服务层默认 shanji
    data = request.get_json(silent=True) or {}
    reservation_code = data.get("reservation_code", "").strip().upper()
    if not reservation_code:
        return _err("请输入预约码")
    result = check_in_reservation(reservation_code, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)


@app.route("/api/tea/reservation/cancel", methods=["POST"])
def api_tea_reservation_cancel():
    """取消预约，释放时段名额"""
    from services.tea_reservation import cancel_reservation
    bnb_id = request.args.get("bnb_id")
    data = request.get_json(silent=True) or {}
    code = data.get("reservation_code", "").strip()
    if not code:
        return _err("缺少预约码")
    result = cancel_reservation(code, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)


@app.route("/api/tea/reservation/complete", methods=["POST"])
@_require_staff_auth
def api_tea_reservation_complete():
    """客人离店，释放座位（仅员工操作）"""
    from services.tea_reservation import complete_reservation
    data = request.get_json(silent=True) or {}
    code = data.get("reservation_code", "").strip()
    if not code:
        return _err("缺少预约码")
    result = complete_reservation(code)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)


@app.route("/api/tea/reservation/status")
def api_tea_reservation_status():
    """查询预约状态和点单解锁状态"""
    from services.tea_reservation import get_reservation_by_code
    from bnb_context import get_current_bnb_id
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    code = request.args.get("code", "").strip().upper()
    if not code:
        return _err("缺少预约码")
    result = get_reservation_by_code(code, bnb_id=bnb_id)
    if not result:
        return _err("预约码无效", 404)
    return jsonify({"success": True, "reservation": result})


@app.route("/api/tea/reservation/queue")
def api_tea_reservation_queue():
    """查询预约排队信息：排序位置、前方人数、同时段人数、预计时间"""
    from services.tea_reservation import get_queue_info
    bnb_id = request.args.get("bnb_id")
    code = request.args.get("code", "").strip()
    if not code:
        return _err("缺少预约码")
    result = get_queue_info(code, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"], 404)
    return jsonify(result)


# ══════════════════════════════════════════════════════════
#  疗愈模块 API（云上·东林外）
# ══════════════════════════════════════════════════════════
@app.route("/api/healing/courses")
def api_healing_courses():
    from services.healing import get_healing_courses, get_healing_categories
    from bnb_context import get_current_bnb_id
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    category = request.args.get("category")
    return jsonify({
        "success": True,
        "categories": get_healing_categories(bnb_id=bnb_id),
        "courses": get_healing_courses(bnb_id=bnb_id, category=category),
    })


@app.route("/api/healing/slots")
def api_healing_slots():
    """获取可预约时间槽"""
    from services.healing import get_available_slots
    from bnb_context import get_current_bnb_id
    from datetime import datetime
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    course_id = request.args.get("course_id", type=int)
    tier_index = request.args.get("tier_index", type=int)
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    if not course_id or tier_index is None:
        return _err("缺少参数 course_id / tier_index")
    result = get_available_slots(course_id, tier_index, date_str, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify({"success": True, **result})


@app.route("/api/healing/pay", methods=["POST"])
def api_healing_pay():
    """模拟微信支付确认"""
    from services.healing import confirm_payment
    from bnb_context import get_current_bnb_id
    bnb_id = get_current_bnb_id()
    data = request.get_json(silent=True) or {}
    appointment_id = data.get("appointment_id")
    if not appointment_id:
        return _err("缺少 appointment_id")
    result = confirm_payment(appointment_id, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)


@app.route("/api/healing/book", methods=["POST"])
def api_healing_book():
    """创建疗愈预约"""
    from services.healing import create_appointment
    from bnb_context import get_current_bnb_id
    bnb_id = request.json.get("bnb_id", get_current_bnb_id()) if request.is_json else get_current_bnb_id()
    data = request.get_json(silent=True) or {}
    data["openid"] = request.args.get("openid") or data.get("openid")
    result = create_appointment(data, bnb_id=bnb_id)
    if "error" in result:
        return _err(result["error"])
    return jsonify(result)

# ══════════════════════════════════════════════════════════
#  健康检查
# ══════════════════════════════════════════════════════════
@app.route("/health")
def health():
    return jsonify({"status": "ok", "name": BNB_NAME})


# ══════════════════════════════════════════════════════════
#  小程序 JSON API（与公众号 H5 页面并存，互不影响）
# ══════════════════════════════════════════════════════════

# ── 房型 API ─────────────────────────────────────────────
@app.route("/api/rooms")
def api_rooms():
    """获取所有房型列表（JSON）"""
    from services.rooms import get_all_rooms
    from bnb_context import get_current_bnb_id
    return jsonify({"success": True, "rooms": get_all_rooms(bnb_id=get_current_bnb_id())})


@app.route("/api/rooms/<int:room_id>")
def api_room_detail(room_id: int):
    """获取单个房型详情（JSON）"""
    from services.rooms import get_room_by_id
    room = get_room_by_id(room_id)
    if not room:
        return jsonify({"success": False, "message": "房型不存在"}), 404
    return jsonify({"success": True, "room": room})


# ── 菜单 API ─────────────────────────────────────────────
@app.route("/api/menu")
def api_menu():
    """获取菜单（含分类和菜品，JSON）"""
    from services.menu import get_menu_categories, get_recommended_items
    from bnb_context import get_current_bnb_id
    bid = get_current_bnb_id()
    return jsonify({
        "success": True,
        "categories": get_menu_categories(bnb_id=bid),
        "recommended": get_recommended_items(bnb_id=bid),
    })


# ── 旅游 API ─────────────────────────────────────────────
@app.route("/api/travel")
def api_travel():
    """获取旅游路线和美食推荐（JSON）"""
    from services.travel import get_all_routes, get_all_food_recommends
    from bnb_context import get_current_bnb_id
    bid = get_current_bnb_id()
    return jsonify({
        "success": True,
        "routes": get_all_routes(bnb_id=bid),
        "foods": get_all_food_recommends(bnb_id=bid),
    })


@app.route("/api/travel/<int:route_id>")
def api_travel_detail(route_id: int):
    """获取单条路线详情（JSON）"""
    from services.travel import get_route_by_id
    route = get_route_by_id(route_id)
    if not route:
        return jsonify({"success": False, "message": "路线不存在"}), 404
    return jsonify({"success": True, "route": route})


@app.route("/api/travel/food/<int:food_id>")
def api_food_detail(food_id: int):
    """获取单个美食详情（JSON）"""
    from services.travel import get_food_by_id
    food = get_food_by_id(food_id)
    if not food:
        return jsonify({"success": False, "message": "美食不存在"}), 404
    return jsonify({"success": True, "food": food})


# ── 快捷服务 API ─────────────────────────────────────────
@app.route("/api/services")
def api_services():
    """获取所有快捷服务（JSON）"""
    from services.quick import get_all_services
    from bnb_context import get_current_bnb_id
    return jsonify({"success": True, "services": get_all_services(bnb_id=get_current_bnb_id())})


# ── 小程序登录 ───────────────────────────────────────────
@app.route("/api/auth/miniapp-login", methods=["POST"])
def api_miniapp_login():
    """
    小程序登录：用 wx.login() 返回的 code 换取 openid 和 session_key
    前端调用 wx.login() 获取 code → 后端调微信接口换取身份信息
    """
    import requests as http_requests

    data = request.get_json()
    if not data or "code" not in data:
        return jsonify({"success": False, "message": "缺少 code"}), 400

    code = data["code"]
    try:
        resp = http_requests.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": WECHAT_MINI_APP_ID,
                "secret": WECHAT_MINI_APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        result = resp.json()
    except Exception as e:
        log_error(f"api.wx_login 失败: {e}", exc_info=True)
        return jsonify({"success": False, "message": "微信登录失败，请稍后重试"}), 502

    if result.get("errcode", 0) != 0:
        return jsonify({
            "success": False,
            "message": result.get("errmsg", "登录失败"),
            "errcode": result.get("errcode"),
        }), 400

    return jsonify({
        "success": True,
        "openid": result.get("openid"),
        "unionid": result.get("unionid"),
        # 注意：session_key 不应返回给前端，由后端自行保管
    })
