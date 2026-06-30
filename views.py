"""
H5 页面渲染路由 — 支持 /path 和 /<bnb_prefix>/path 双模式
"""
from app import app
from flask import request, render_template, abort


# ── 三民宿 BnB 前缀 H5 路由装饰器 ─────────────────────────
def _bnb_route(rule, **kwargs):
    """注册同时支持 /path 和 /<bnb_prefix>/path 的路由"""
    def decorator(f):
        app.add_url_rule(rule, f.__name__ + "_default", f, **kwargs)
        app.add_url_rule("/<bnb_prefix>" + rule, f.__name__ + "_prefixed", f, **kwargs)
        return f
    return decorator


@app.route("/docs")
def docs_page():
    """API 文档"""
    return render_template("docs.html")


@_bnb_route("/")
def bnb_index(bnb_prefix=None):
    from services.rooms import get_featured_rooms
    from bnb_context import get_current_bnb_id
    return render_template("index.html", featured_rooms=get_featured_rooms(4, bnb_id=get_current_bnb_id()))

@_bnb_route("/rooms")
def bnb_rooms(bnb_prefix=None):
    from services.rooms import get_all_rooms
    from bnb_context import get_current_bnb_id
    return render_template("rooms.html", rooms=get_all_rooms(bnb_id=get_current_bnb_id()))

@_bnb_route("/rooms/<int:room_id>")
def bnb_room_detail(room_id: int, bnb_prefix=None):
    from services.rooms import get_room_by_id
    room = get_room_by_id(room_id)
    if not room: abort(404)
    return render_template("room_detail.html", room=room)

@_bnb_route("/menu")
def bnb_menu(bnb_prefix=None):
    from services.menu import get_menu_categories
    from bnb_context import get_current_bnb_id
    return render_template("menu.html", categories=get_menu_categories(bnb_id=get_current_bnb_id()))

@_bnb_route("/travel")
def bnb_travel(bnb_prefix=None):
    from services.travel import get_all_routes, get_all_food_recommends
    from bnb_context import get_current_bnb_id
    bid = get_current_bnb_id()
    return render_template("travel.html", routes=get_all_routes(bnb_id=bid), foods=get_all_food_recommends(bnb_id=bid))

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
    from bnb_context import get_current_bnb_id
    return render_template("services.html", services=get_all_services(bnb_id=get_current_bnb_id()))

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

@app.route("/staff")
def staff_dashboard():
    """员工通知看板页面"""
    return render_template("staff.html")
