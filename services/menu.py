"""
点餐服务 - 菜单查询、下单、订单管理
要求5：仅咖啡和简餐，支持微信支付
"""
import time
import hashlib
import random
from datetime import datetime
from models import get_db, MenuCategory, MenuItem, Order
from config import WECHAT_APP_ID, WECHAT_MCH_ID, WECHAT_MCH_KEY
from bnb_context import get_service_bnb_id as _get_bnb_id


def get_menu_categories(bnb_id=None):
    """获取所有菜单分类"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
        categories = db.query(MenuCategory).filter(
            MenuCategory.bnb_id == bnb_id
        ).order_by(MenuCategory.sort_order).all()
        return [c.to_dict() for c in categories]


def get_menu_items_by_category(category_id: int, bnb_id=None):
    """按分类获取菜品"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
        items = db.query(MenuItem).filter(
            MenuItem.bnb_id == bnb_id,
            MenuItem.category_id == category_id,
            MenuItem.is_available == True
        ).order_by(MenuItem.sort_order).all()
        return [i.to_dict() for i in items]


def get_recommended_items(bnb_id=None):
    """获取推荐菜品"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
        items = db.query(MenuItem).filter(
            MenuItem.bnb_id == bnb_id,
            MenuItem.is_available == True,
            MenuItem.is_recommended == True
        ).order_by(MenuItem.sort_order).all()
        return [i.to_dict() for i in items]


def create_order(openid: str, items_data: list, room_number: str = "",
                 remark: str = "", bnb_id=None) -> Order:
    """创建订单
    items_data: [{"id": 1, "name": "庐山云雾茶", "quantity": 2, "price": 68}, ...]
    自动判定通知目标：含体验/疗愈/茶道类 → 主理人，纯餐饮 → 前台点单机
    """
    bnb_id = _get_bnb_id(bnb_id)
    from models import MenuItem, MenuCategory
    with get_db() as db:
        total = sum(item["price"] * item["quantity"] for item in items_data)
        # 判定通知目标
        notify_target = "frontdesk"  # 默认前台点单机
        for item in items_data:
            mi = db.query(MenuItem).filter(MenuItem.id == item["id"]).first()
            if mi:
                cat = db.query(MenuCategory).filter(MenuCategory.id == mi.category_id).first()
                if cat and ("体验" in cat.name or "疗愈" in cat.name or "茶道" in cat.name):
                    notify_target = "manager"
                    break
        order = Order(
            bnb_id=bnb_id,
            openid=openid,
            room_number=room_number,
            items=items_data,
            total_price=total,
            status="pending",
            remark=remark,
            notify_target=notify_target,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order


def get_user_orders(openid: str, limit: int = 10, bnb_id=None):
    """获取用户订单列表"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
        orders = db.query(Order).filter(
            Order.bnb_id == bnb_id,
            Order.openid == openid
        ).order_by(Order.created_at.desc()).limit(limit).all()
        return [o.to_dict() for o in orders]


def get_order_status(order_id: int, bnb_id=None):
    """查询订单状态"""
    bnb_id = _get_bnb_id(bnb_id)
    with get_db() as db:
        order = db.query(Order).filter(Order.id == order_id, Order.bnb_id == bnb_id).first()
        return order.to_dict() if order else None


STATUS_LABELS = {
    "pending": "⏳ 待确认",
    "confirmed": "[✓] 已确认",
    "preparing": "· 制作中",
    "delivered": "🚀 已送达",
    "completed": "✔️ 已完成",
    "cancelled": "· 已取消",
}


def format_menu_text(bnb_id=None):
    """格式化为微信文本菜单（要求5：咖啡简餐）"""
    bnb_id = _get_bnb_id(bnb_id)
    categories = get_menu_categories(bnb_id=bnb_id)
    if not categories:
        return "暂无菜单信息，请咨询前台～"

    from config import BNB_CONFIGS
    name = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])["short_name"]
    lines = [f"· *{name} · 咖啡简餐*\n"]
    lines.append("本民宿不提供正餐，以下为咖啡、茶饮与简餐～\n")

    # 先展示推荐
    recommended = get_recommended_items(bnb_id=bnb_id)
    if recommended:
        lines.append("★ *今日推荐*\n")
        for item in recommended:
            lines.append(f"  {item['name']}  ¥{item['price']}")
            if item.get("description"):
                lines.append(f"    {item['description'][:50]}")
        lines.append("")

    # 分类展示
    for cat in categories:
        items = cat.get("items", [])
        if not items:
            continue
        icon = cat.get("icon", "·")
        lines.append(f"{icon} *{cat['name']}*")
        for item in items[:6]:
            lines.append(f"  {item['name']}  ¥{item['price']}")
        if len(items) > 6:
            lines.append(f"  ... 还有{len(items) - 6}项")
        lines.append("")

    lines.append("─" * 30)
    lines.append("🛒 *如何点餐？*")
    lines.append("  · 回复「点餐」进入点餐页面")
    lines.append("  · 回复「推荐」查看今日推荐")
    lines.append("  · 支持微信支付 💳")
    lines.append("  · 回复「下单+编号」如「下单1,3」")
    lines.append("\n🍜 需要正餐？回复「周边美食」查看推荐餐厅")
    return "\n".join(lines)


def format_recommended_text(bnb_id=None):
    """格式化推荐菜品"""
    bnb_id = _get_bnb_id(bnb_id)
    items = get_recommended_items(bnb_id=bnb_id)
    if not items:
        return "暂无推荐菜品～"

    lines = ["★ *主厨推荐*\n"]
    for item in items:
        lines.append(f"*{item['name']}*  ¥{item['price']}")
        lines.append(f"  {item.get('description', '')}")
        if item.get("image"):
            lines.append(f"  🖼️ {item['image']}")
        lines.append("")

    lines.append("▸ 提示： 回复「下单+编号」即可点餐")
    return "\n".join(lines)


def format_order_status_text(openid: str, bnb_id=None):
    """格式化用户订单状态"""
    bnb_id = _get_bnb_id(bnb_id)
    orders = get_user_orders(openid, bnb_id=bnb_id)
    if not orders:
        return "您还没有订单记录～\n回复「点餐」开始咖啡简餐之旅吧！"

    lines = ["📋 *我的订单*\n"]
    for order in orders[:5]:
        status_label = STATUS_LABELS.get(order["status"], order["status"])
        pay_label = "[✓] 已支付" if order.get("pay_status") == "paid" else "⏳ 待支付"
        items_text = "、".join(
            f"{item['name']}×{item['quantity']}"
            for item in order.get("items", [])
        )
        lines.append(
            f"🔢 订单#{order['id']}\n"
            f"  📦 {items_text}\n"
            f"  · ¥{order['total_price']}  |  {pay_label}\n"
            f"  📮 {status_label}\n"
            f"  · {order['created_at']}\n"
        )
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  微信支付集成（要求5：服务号内微信支付）
# ══════════════════════════════════════════════════════════
def create_wechat_pay_params(openid: str, order_id: int,
                              total_fee: float, body: str,
                              notify_url: str = "") -> dict:
    """
    生成微信JSAPI支付参数
    实际部署时需要完整的微信支付商户配置
    """
    if not WECHAT_APP_ID or not WECHAT_MCH_ID or not WECHAT_MCH_KEY:
        return {"error": "微信支付未配置", "available": False}

    # 金额：元转分
    total_fee_fen = int(total_fee * 100)

    # 生成支付参数
    params = {
        "appId": WECHAT_APP_ID,
        "timeStamp": str(int(time.time())),
        "nonceStr": _generate_nonce_str(),
        "package": f"prepay_id={_get_prepay_id(openid, order_id, total_fee_fen, body, notify_url)}",
        "signType": "MD5",
    }

    # 生成签名
    params["paySign"] = _generate_pay_sign(params)

    return {"available": True, "params": params, "order_id": order_id}


def _get_prepay_id(openid: str, order_id: int, total_fee: int,
                   body: str, notify_url: str) -> str:
    """
    调用微信统一下单接口获取prepay_id
    实际部署时需通过微信支付API获取
    """
    # 占位 - 实际部署时调用微信支付统一下单API
    return f"wx_prepay_{order_id}_{int(time.time())}"


def _generate_nonce_str(length: int = 32) -> str:
    """生成随机字符串"""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def _generate_pay_sign(params: dict) -> str:
    """生成微信支付签名（MD5）"""
    # 按字典序排序并拼接
    sorted_items = sorted(
        (k, v) for k, v in params.items()
        if k != "paySign" and v is not None
    )
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    sign_str += f"&key={WECHAT_MCH_KEY}"

    return hashlib.md5(sign_str.encode()).hexdigest().upper()


def handle_pay_notify(xml_data: str) -> dict:
    """
    处理微信支付回调通知
    """
    # 实际部署时解析XML并验证签名
    return {"status": "received", "message": "支付回调处理中"}
