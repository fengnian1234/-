"""
云上归墅 - 微信公众号客服系统
Flask 主应用 + 微信消息接入
"""
import os
import hashlib
import time
from flask import Flask, request, jsonify, render_template, abort
from config import (
    DEBUG, SECRET_KEY, WECHAT_TOKEN, WECHAT_APP_ID, WECHAT_APP_SECRET,
    BASE_URL, BNB_NAME,
)
from seed_data import seed_all

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ── 应用初始化 ───────────────────────────────────────────
def init_app():
    """初始化应用：创建数据库并填充种子数据"""
    print("🌄 正在初始化云上归墅客服系统...")
    try:
        seed_all()
    except Exception as e:
        print(f"⚠️ 数据库初始化: {e}")
    print(f"✅ {BNB_NAME} 客服系统已就绪")


# ── 微信服务器验证 ───────────────────────────────────────
@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    """
    微信公众号服务器接入点
    GET: 微信服务器验证（首次接入时）
    POST: 接收用户消息
    """
    if request.method == "GET":
        return _verify_wechat()

    # POST: 处理消息
    return _handle_wechat_post()


def _verify_wechat():
    """微信服务器签名验证"""
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")
    echostr = request.args.get("echostr", "")

    # 验证签名
    tmp_list = sorted([WECHAT_TOKEN, timestamp, nonce])
    tmp_str = "".join(tmp_list)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

    if tmp_str == signature:
        return echostr
    else:
        abort(403)


def _handle_wechat_post():
    """处理微信消息推送"""
    # 使用 wechatpy 解析消息
    from wechatpy import parse_message
    from wechatpy.replies import TextReply, ImageReply
    from wechat import handle_wechat_message, handle_event

    xml_data = request.data
    if not xml_data:
        return "success"

    try:
        msg = parse_message(xml_data)
    except Exception as e:
        return "success"

    # 判断消息类型
    msg_type = getattr(msg, 'type', '')

    try:
        if msg_type == 'text':
            # 文本消息 - 主处理逻辑
            reply_text = handle_wechat_message(msg)

            reply = TextReply(content=reply_text, message=msg)

        elif msg_type == 'event':
            # 事件推送（关注、菜单点击等）
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

    except Exception as e:
        # 任何异常都返回 success，避免微信重复推送
        return "success"


# ── H5 页面路由 ──────────────────────────────────────────
@app.route("/")
def index():
    """首页/欢迎页"""
    return render_template("index.html")


@app.route("/rooms")
def rooms_page():
    """房型展示页"""
    from services.rooms import get_all_rooms
    rooms = get_all_rooms()
    return render_template("rooms.html", rooms=rooms)


@app.route("/rooms/<int:room_id>")
def room_detail(room_id: int):
    """房间详情页"""
    from services.rooms import get_room_by_id
    room = get_room_by_id(room_id)
    if not room:
        abort(404)
    return render_template("room_detail.html", room=room)


@app.route("/menu")
def menu_page():
    """点餐页面"""
    from services.menu import get_menu_categories
    categories = get_menu_categories()
    return render_template("menu.html", categories=categories)


@app.route("/travel")
def travel_page():
    """旅游攻略页"""
    from services.travel import get_all_routes, get_all_food_recommends
    routes = get_all_routes()
    foods = get_all_food_recommends()
    return render_template("travel.html", routes=routes, foods=foods)


@app.route("/travel/<int:route_id>")
def travel_detail(route_id: int):
    """路线详情页"""
    from services.travel import get_route_by_id
    route = get_route_by_id(route_id)
    if not route:
        abort(404)
    return render_template("travel_detail.html", route=route)


@app.route("/services")
def services_page():
    """快捷服务页"""
    from services.quick import get_all_services
    services = get_all_services()
    return render_template("services.html", services=services)


@app.route("/map")
def map_page():
    """地图导航页"""
    return render_template("map.html")


# ── API 接口 ─────────────────────────────────────────────
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


# ── 健康检查 ─────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "name": BNB_NAME})


# ── 启动 ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_app()
    print(f"\n🏔️  {BNB_NAME} 微信公众号客服系统")
    print(f"📍 本地访问: http://127.0.0.1:5000")
    print(f"📍 微信接入: http://{BASE_URL}/wechat")
    print(f"📍 H5页面: http://127.0.0.1:5000/rooms")
    print()
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
