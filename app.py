"""
云上·归墅 - 微信公众号客服系统
Flask 主应用 + 微信消息接入（v2 - 按额外要求文档更新）
"""
import os
import hashlib
import time
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, abort, g
from services.logger import info, warning, error as log_error, debug, log_ai, log_keyword, log_booking
from config import (
    DEBUG, SECRET_KEY, WECHAT_TOKEN, WECHAT_APP_ID, WECHAT_APP_SECRET,
    WECHAT_MINI_APP_ID, WECHAT_MINI_APP_SECRET,
    BASE_URL, BNB_NAME, BNB_CONFIGS,
    STAFF_API_KEY, STAFF_AUTH_REQUIRED,
)
from models import init_db, SessionLocal, Booking
from seed_data import seed_all
from bnb_context import get_current_bnb, get_current_bnb_id, get_bnb_id_from_path, set_current_bnb

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── 员工鉴权装饰器 ───────────────────────────────────────
def _require_staff_auth(f):
    """保护敏感管理API：需要 X-Staff-Key 请求头匹配 STAFF_API_KEY"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not STAFF_AUTH_REQUIRED:
            return f(*args, **kwargs)
        api_key = request.headers.get("X-Staff-Key", "")
        if not api_key or api_key != STAFF_API_KEY:
            warning(f"[AUTH] 未授权访问尝试: {request.path} from {request.remote_addr}")
            return jsonify({"success": False, "message": "未授权访问"}), 401
        return f(*args, **kwargs)
    return decorated

# ── CORS 支持（限制来源）──────────────────────────────────
@app.after_request
def add_cors_headers(response):
    # 仅允许已知可信来源
    trusted = [
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "https://yunshangguishu.com",
    ]
    origin = request.headers.get("Origin", "")
    if origin and origin in trusted:
        response.headers["Access-Control-Allow-Origin"] = origin
    # 生产模式不允许任意跨域
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Staff-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return app.make_default_options_response()

# ── BnB 上下文注入 ──────────────────────────────────────
@app.before_request
def set_bnb_context():
    """在每次请求前注入当前民宿标识到 Flask g 对象"""
    g.bnb_id = get_bnb_id_from_path(request.path)
    g.bnb_config = get_current_bnb()

# ── 模板全局变量注入 ───────────────────────────────────
@app.context_processor
def inject_bnb():
    """所有 Jinja2 模板自动获得 bnb / bnb_id / bnb_prefix / request_path 变量"""
    bnb_id = get_current_bnb_id()
    prefix_map = {"guishu": "/gs", "shanji": "/sj", "donglinwai": "/dlw"}
    return {
        "bnb": get_current_bnb(),
        "bnb_id": bnb_id,
        "bnb_prefix": prefix_map.get(bnb_id, ""),
        "BNB_CONFIGS": BNB_CONFIGS,
        "request_path": request.path,
    }

# ── 简易限流（内存，单进程） ──────────────────────────────
_rate_limit_store = {}

def rate_limit(key: str, max_req: int = 10, window: int = 60) -> bool:
    """简单的滑动窗口限流。返回 True 表示未超限。"""
    now = time.time()
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window]
    if len(_rate_limit_store[key]) >= max_req:
        return False
    _rate_limit_store[key].append(now)
    return True


# ── 错误页面 ─────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ── BnB 上下文注入 ───────────────────────────────────────
@app.before_request
def _inject_bnb_context():
    """每个请求开始时自动注入 BnB 上下文（路径解析 → Flask g）"""
    set_current_bnb(get_bnb_id_from_path())


# ── 应用初始化 ───────────────────────────────────────────
def init_app():
    """初始化应用：创建数据库并填充种子数据"""
    info(f"🌄 正在初始化{BNB_NAME}客服系统...")
    try:
        seed_all()
    except Exception as e:
        warning(f"⚠️ 数据库初始化: {e}")
    info(f"✅ {BNB_NAME} 客服系统已就绪")


# ══════════════════════════════════════════════════════════
#  微信服务器接入（三民宿各一路径）
# ══════════════════════════════════════════════════════════

def _verify_wechat(bnb_id="guishu"):
    """微信服务器签名验证（按民宿取对应 token）"""
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")
    echostr = request.args.get("echostr", "")

    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    token = cfg.get("wechat_token", WECHAT_TOKEN)
    tmp_list = sorted([token, timestamp, nonce])
    tmp_str = "".join(tmp_list)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

    if tmp_str == signature:
        return echostr
    else:
        abort(403)


def _handle_wechat_post(bnb_id="guishu"):
    """处理微信消息推送（注入 bnb_id 到消息处理）"""
    set_current_bnb(bnb_id)  # 显式设置请求级 BnB 上下文
    from wechatpy import parse_message
    from wechatpy.replies import TextReply
    from wechat import handle_wechat_message, handle_event

    xml_data = request.data
    if not xml_data:
        return "success"

    try:
        msg = parse_message(xml_data)
    except Exception:
        log_error("wechat.parse_xml", "XML解析失败", exc_info=True)
        return "success"

    msg_type = getattr(msg, 'type', '')

    try:
        if msg_type == 'text':
            reply_text = handle_wechat_message(msg, bnb_id=bnb_id)
            reply = TextReply(content=reply_text, message=msg)
        elif msg_type == 'event':
            reply_text = handle_event(msg, bnb_id=bnb_id)
            if not reply_text:
                return "success"
            reply = TextReply(content=reply_text, message=msg)
        elif msg_type == 'image':
            reply = TextReply(
                content="📷 收到您的图片啦～\n如需人工服务，请回复「人工」转接客服～",
                message=msg,
            )
        elif msg_type == 'voice':
            reply = TextReply(
                content="🎤 收到您的语音消息～\n我暂时还不能听懂语音，请用文字告诉我您的需求吧～",
                message=msg,
            )
        else:
            reply = TextReply(
                content="收到您的消息啦～回复「帮助」查看我能为您做什么～",
                message=msg,
            )

        xml_response = reply.render()
        return xml_response

    except Exception:
        log_error("wechat.handle_message", "消息处理异常", exc_info=True)
        return "success"


# 归墅（旧路径兼容）
@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    if request.method == "GET":
        return _verify_wechat("guishu")
    return _handle_wechat_post("guishu")

# 三家民宿独立路径
@app.route("/wechat/gs", methods=["GET", "POST"])
def wechat_gs():
    if request.method == "GET":
        return _verify_wechat("guishu")
    return _handle_wechat_post("guishu")

@app.route("/wechat/sj", methods=["GET", "POST"])
def wechat_sj():
    if request.method == "GET":
        return _verify_wechat("shanji")
    return _handle_wechat_post("shanji")

@app.route("/wechat/dlw", methods=["GET", "POST"])
def wechat_dlw():
    if request.method == "GET":
        return _verify_wechat("donglinwai")
    return _handle_wechat_post("donglinwai")


# ══════════════════════════════════════════════════════════
#  H5 页面路由（支持 /path 和 /<bnb_prefix>/path 双模式）
# ══════════════════════════════════════════════════════════

@app.route("/docs")
def docs_page():
    """API 文档"""
    return render_template("docs.html")


# ── 三民宿 BnB 前缀 H5 路由 ───────────────────────────────
# 每个路由同时支持旧路径(默认归墅)和 BnB 前缀路径
def _bnb_route(rule, **kwargs):
    """注册同时支持 /path 和 /<bnb_prefix>/path 的路由"""
    def decorator(f):
        app.add_url_rule(rule, f.__name__ + "_default", f, **kwargs)
        app.add_url_rule("/<bnb_prefix>" + rule, f.__name__ + "_prefixed", f, **kwargs)
        return f
    return decorator


@_bnb_route("/")
def bnb_index(bnb_prefix=None):
    from services.rooms import get_featured_rooms
    return render_template("index.html", featured_rooms=get_featured_rooms(4))

@_bnb_route("/rooms")
def bnb_rooms(bnb_prefix=None):
    from services.rooms import get_all_rooms
    return render_template("rooms.html", rooms=get_all_rooms())

@_bnb_route("/rooms/<int:room_id>")
def bnb_room_detail(room_id: int, bnb_prefix=None):
    from services.rooms import get_room_by_id
    room = get_room_by_id(room_id)
    if not room: abort(404)
    return render_template("room_detail.html", room=room)

@_bnb_route("/menu")
def bnb_menu(bnb_prefix=None):
    from services.menu import get_menu_categories
    return render_template("menu.html", categories=get_menu_categories())

@_bnb_route("/travel")
def bnb_travel(bnb_prefix=None):
    from services.travel import get_all_routes, get_all_food_recommends
    return render_template("travel.html", routes=get_all_routes(), foods=get_all_food_recommends())

@_bnb_route("/travel/<int:route_id>")
def bnb_travel_detail(route_id: int, bnb_prefix=None):
    from services.travel import get_route_by_id
    route = get_route_by_id(route_id)
    if not route: abort(404)
    return render_template("travel_detail.html", route=route)

@_bnb_route("/travel/food/<int:food_id>")
def bnb_food_detail(food_id: int, bnb_prefix=None):
    from services.travel import get_food_by_id
    food = get_food_by_id(food_id)
    if not food: abort(404)
    return render_template("food_detail.html", food=food)

@_bnb_route("/services")
def bnb_services(bnb_prefix=None):
    from services.quick import get_all_services
    return render_template("services.html", services=get_all_services())

@_bnb_route("/map")
def bnb_map(bnb_prefix=None):
    return render_template("map.html")

@_bnb_route("/points")
def bnb_points(bnb_prefix=None):
    return render_template("points.html")

@_bnb_route("/orders")
def bnb_orders(bnb_prefix=None):
    return render_template("orders.html")

@_bnb_route("/simulator")
def bnb_simulator(bnb_prefix=None):
    return render_template("wechat-simulator.html")

@app.route("/miniapp")
def miniapp_simulator():
    """小程序模拟器 — 5 Tab + BnB 切换 + AI 管家"""
    return render_template("miniapp-simulator.html")

@app.route("/miniapp/chat")
def miniapp_chat():
    """小程序 AI 管家聊天页"""
    bnb_id = request.args.get("bnb", "guishu")
    from bnb_context import get_bnb_config
    bnb = get_bnb_config(bnb_id)
    return render_template("miniapp-chat.html", bnb_id=bnb_id, bnb=bnb)

@_bnb_route("/tea")
def bnb_tea(bnb_prefix=None):
    """茶园板块（山纪专属）"""
    return render_template("tea.html")

@_bnb_route("/healing")
def bnb_healing(bnb_prefix=None):
    """疗愈板块（东林外专属）"""
    return render_template("healing.html")


# ══════════════════════════════════════════════════════════
#  员工通知看板（要求2：醒目有效的通知方式）
# ══════════════════════════════════════════════════════════
@app.route("/staff")
def staff_dashboard():
    """员工通知看板页面"""
    return render_template("staff.html")

@app.route("/api/staff/dashboard")
def api_staff_dashboard():
    """获取员工看板数据 — 含点餐订单（前台）+ 服务请求（主理人）"""
    from services.notify import get_pending_requests, get_all_requests_today, get_notification_stats
    from services.booking import get_review_reminders_due
    from models import SessionLocal, Order
    from datetime import datetime

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
        today = datetime.utcnow().date()
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
    data = request.get_json()
    if not data or "openid" not in data:
        return jsonify({"error": "缺少openid"}), 400
    enabled = is_ai_enabled(data["openid"])
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
    data = request.get_json()
    if not data or "openid" not in data:
        return jsonify({"success": False, "message": "缺少 openid"}), 400
    booking = get_booking_by_openid(data["openid"])
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
    return jsonify(get_platform_review_links())


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
        return jsonify({"error": "数据为空"}), 400
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"error": "缺少订单ID"}), 400
    from models import SessionLocal, Order
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return jsonify({"error": "订单不存在"}), 404
        if order.pay_status == "paid":
            return jsonify({"error": "已支付，无需重复支付"}), 400
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
        log_error("api.pay_order", str(e), exc_info=True)
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
        log_error("api.order_status", str(e), exc_info=True)
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
    info = agent_collect_platform_info()
    return jsonify(info)

@app.route("/api/monitor/report")
def api_monitor_report():
    """获取平台口碑文字报告"""
    from services.monitor import generate_monitor_report
    return jsonify({"report": generate_monitor_report()})

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
        log_error("api.staff.acknowledge", "操作失败", exc_info=True)
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
        return jsonify({"error": "缺少content字段"}), 400

    content = data["content"].strip()
    openid = data.get("openid", "sim_test_user")

    if not content:
        return jsonify({"reply": "请输入消息内容", "handler": "empty", "mode": "travel_advisor", "matched": None})

    # 构建模拟消息
    msg = _MockWechatMessage(content, openid)

    # 1. 尝试关键词匹配
    handler, match = match_keyword(content)
    if handler:
        try:
            reply = handler(msg, match)
            return jsonify({
                "reply": reply,
                "handler": "keyword",
                "mode": get_conversation_mode(openid),
                "matched": str(match.re.pattern) if match else None,
            })
        except Exception:
            debug("关键词匹配异常，降级到AI")

    # 2. AI 智能对话
    mode = get_conversation_mode(openid)
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
        warning("AI对话异常，返回兜底回复")

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
    from datetime import datetime, timedelta

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
                now = datetime.utcnow()
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
                now = datetime.utcnow()
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
            ).update({"status": "checked_out", "checked_out_at": datetime.utcnow()}, synchronize_session=False)
            db.commit()
            existing = db.query(Booking).filter(
                Booking.openid == openid,
                Booking.status == "checked_out"
            ).first()
            if not existing:
                now = datetime.utcnow()
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
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "types": get_tea_types(bnb_id=bnb_id)})

@app.route("/api/tea/experiences")
def api_tea_experiences():
    from services.tea import get_tea_experiences
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "experiences": get_tea_experiences(bnb_id=bnb_id)})

@app.route("/api/tea/products")
def api_tea_products():
    from services.tea import get_tea_products
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    return jsonify({"success": True, "products": get_tea_products(bnb_id=bnb_id)})

# ══════════════════════════════════════════════════════════
#  疗愈模块 API（云上·东林外）
# ══════════════════════════════════════════════════════════
@app.route("/api/healing/courses")
def api_healing_courses():
    from services.healing import get_healing_courses, get_healing_categories
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
    bnb_id = request.args.get("bnb_id", get_current_bnb_id())
    course_id = request.args.get("course_id", type=int)
    tier_index = request.args.get("tier_index", type=int)
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    if not course_id or tier_index is None:
        return jsonify({"success": False, "error": "缺少参数 course_id / tier_index"}), 400
    result = get_available_slots(course_id, tier_index, date_str, bnb_id=bnb_id)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 400
    return jsonify({"success": True, **result})


@app.route("/api/healing/pay", methods=["POST"])
def api_healing_pay():
    """模拟微信支付确认"""
    from services.healing import confirm_payment
    bnb_id = get_current_bnb_id()
    data = request.get_json(silent=True) or {}
    appointment_id = data.get("appointment_id")
    if not appointment_id:
        return jsonify({"success": False, "error": "缺少 appointment_id"}), 400
    result = confirm_payment(appointment_id, bnb_id=bnb_id)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 400
    return jsonify(result)


@app.route("/api/healing/book", methods=["POST"])
def api_healing_book():
    """创建疗愈预约"""
    from services.healing import create_appointment
    bnb_id = request.json.get("bnb_id", get_current_bnb_id()) if request.is_json else get_current_bnb_id()
    data = request.get_json(silent=True) or {}
    data["openid"] = request.args.get("openid") or data.get("openid")
    result = create_appointment(data, bnb_id=bnb_id)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 400
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
    return jsonify({"success": True, "rooms": get_all_rooms()})


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
    return jsonify({
        "success": True,
        "categories": get_menu_categories(),
        "recommended": get_recommended_items(),
    })


# ── 旅游 API ─────────────────────────────────────────────
@app.route("/api/travel")
def api_travel():
    """获取旅游路线和美食推荐（JSON）"""
    from services.travel import get_all_routes, get_all_food_recommends
    return jsonify({
        "success": True,
        "routes": get_all_routes(),
        "foods": get_all_food_recommends(),
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
    return jsonify({"success": True, "services": get_all_services()})


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
        log_error("api.wx_login", str(e), exc_info=True)
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


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_app()
    info(f"🏔️  {BNB_NAME} 微信公众号客服系统 v2")
    info(f"📍 本地访问: http://127.0.0.1:5000")
    info(f"📍 微信接入: http://你的域名/wechat")
    info(f"📍 员工看板: http://127.0.0.1:5000/staff")
    info(f"📍 平台口碑: http://127.0.0.1:5000/api/monitor/report")
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
