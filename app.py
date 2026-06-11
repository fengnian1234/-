"""
云上·归墅 - 微信公众号客服系统
Flask 主应用 + 微信消息接入（v2 - 按额外要求文档更新）
"""
import os
import hashlib
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort
from config import (
    DEBUG, SECRET_KEY, WECHAT_TOKEN, WECHAT_APP_ID, WECHAT_APP_SECRET,
    BASE_URL, BNB_NAME,
)
from models import init_db, SessionLocal, Booking
from seed_data import seed_all

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ── 应用初始化 ───────────────────────────────────────────
def init_app():
    """初始化应用：创建数据库并填充种子数据"""
    print(f"🌄 正在初始化{BNB_NAME}客服系统...")
    try:
        seed_all()
    except Exception as e:
        print(f"⚠️ 数据库初始化: {e}")
    print(f"✅ {BNB_NAME} 客服系统已就绪")


# ══════════════════════════════════════════════════════════
#  微信服务器接入
# ══════════════════════════════════════════════════════════
@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    """微信公众号服务器接入点"""
    if request.method == "GET":
        return _verify_wechat()
    return _handle_wechat_post()


def _verify_wechat():
    """微信服务器签名验证"""
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")
    echostr = request.args.get("echostr", "")

    tmp_list = sorted([WECHAT_TOKEN, timestamp, nonce])
    tmp_str = "".join(tmp_list)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

    if tmp_str == signature:
        return echostr
    else:
        abort(403)


def _handle_wechat_post():
    """处理微信消息推送"""
    from wechatpy import parse_message
    from wechatpy.replies import TextReply
    from wechat import handle_wechat_message, handle_event

    xml_data = request.data
    if not xml_data:
        return "success"

    try:
        msg = parse_message(xml_data)
    except Exception:
        return "success"

    msg_type = getattr(msg, 'type', '')

    try:
        if msg_type == 'text':
            reply_text = handle_wechat_message(msg)
            reply = TextReply(content=reply_text, message=msg)
        elif msg_type == 'event':
            reply_text = handle_event(msg)
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
        return "success"


# ══════════════════════════════════════════════════════════
#  H5 页面路由
# ══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rooms")
def rooms_page():
    from services.rooms import get_all_rooms
    return render_template("rooms.html", rooms=get_all_rooms())

@app.route("/rooms/<int:room_id>")
def room_detail(room_id: int):
    from services.rooms import get_room_by_id
    room = get_room_by_id(room_id)
    if not room: abort(404)
    return render_template("room_detail.html", room=room)

@app.route("/menu")
def menu_page():
    from services.menu import get_menu_categories
    return render_template("menu.html", categories=get_menu_categories())

@app.route("/travel")
def travel_page():
    from services.travel import get_all_routes, get_all_food_recommends
    return render_template("travel.html", routes=get_all_routes(), foods=get_all_food_recommends())

@app.route("/travel/<int:route_id>")
def travel_detail(route_id: int):
    from services.travel import get_route_by_id
    route = get_route_by_id(route_id)
    if not route: abort(404)
    return render_template("travel_detail.html", route=route)

@app.route("/services")
def services_page():
    from services.quick import get_all_services
    return render_template("services.html", services=get_all_services())

@app.route("/map")
def map_page():
    return render_template("map.html")


# ══════════════════════════════════════════════════════════
#  员工通知看板（要求2：醒目有效的通知方式）
# ══════════════════════════════════════════════════════════
@app.route("/staff")
def staff_dashboard():
    """员工通知看板页面"""
    return render_template("staff.html")

@app.route("/api/staff/dashboard")
def api_staff_dashboard():
    """获取员工看板数据"""
    from services.notify import get_pending_requests, get_all_requests_today, get_notification_stats
    from services.booking import get_review_reminders_due

    stats = get_notification_stats()
    pending = get_pending_requests()
    all_today = get_all_requests_today()
    completed = [r for r in all_today if r["status"] == "completed"]

    # 检查好评推送提醒
    review_reminders = get_review_reminders_due()

    return jsonify({
        "stats": stats,
        "pending": pending,
        "completed": completed[:20],
        "review_reminders_count": len(review_reminders),
    })

@app.route("/api/staff/acknowledge", methods=["POST"])
def api_acknowledge_request():
    """员工确认收到请求"""
    from services.notify import acknowledge_request
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"success": False, "message": "缺少请求ID"}), 400
    acknowledge_request(data["id"], data.get("handler", "前台"))
    return jsonify({"success": True})

@app.route("/api/staff/complete", methods=["POST"])
def api_complete_request():
    """员工完成请求"""
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
def api_confirm_booking():
    """前台确认预订（解锁AI）"""
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
    return jsonify({"success": True, "booking": booking.to_dict()})

@app.route("/api/booking/<int:booking_id>/checkin", methods=["POST"])
def api_check_in(booking_id: int):
    """办理入住"""
    from services.booking import check_in_booking
    data = request.get_json() or {}
    booking = check_in_booking(booking_id, data.get("room_number", ""))
    if not booking:
        return jsonify({"success": False, "message": "预订不存在"}), 404
    return jsonify({"success": True, "booking": booking.to_dict()})

@app.route("/api/booking/<int:booking_id>/checkout", methods=["POST"])
def api_check_out(booking_id: int):
    """办理退房（触发30分钟好评推送倒计时）"""
    from services.booking import check_out_booking
    booking = check_out_booking(booking_id)
    if not booking:
        return jsonify({"success": False, "message": "预订不存在"}), 404
    return jsonify({
        "success": True,
        "message": f"退房成功，将在30分钟后推送好评提醒",
        "booking": booking.to_dict(),
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

    from services.menu import create_order
    order = create_order(openid, items, room_number, remark)

    return jsonify({
        "success": True,
        "message": "下单成功！",
        "order": order.to_dict(),
    })

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
def api_trigger_collection():
    """触发平台信息收集"""
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
#  健康检查
# ══════════════════════════════════════════════════════════
@app.route("/health")
def health():
    return jsonify({"status": "ok", "name": BNB_NAME})


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_app()
    print(f"\n🏔️  {BNB_NAME} 微信公众号客服系统 v2")
    print(f"📍 本地访问: http://127.0.0.1:5000")
    print(f"📍 微信接入: http://你的域名/wechat")
    print(f"📍 员工看板: http://127.0.0.1:5000/staff")
    print(f"📍 平台口碑: http://127.0.0.1:5000/api/monitor/report")
    print()
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
