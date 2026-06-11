"""
点餐服务 - 菜单查询、下单、订单管理
"""
from datetime import datetime
from models import SessionLocal, MenuCategory, MenuItem, Order


def get_menu_categories():
    """获取所有菜单分类"""
    db = SessionLocal()
    try:
        categories = db.query(MenuCategory).order_by(MenuCategory.sort_order).all()
        return [c.to_dict() for c in categories]
    finally:
        db.close()


def get_menu_items_by_category(category_id: int):
    """按分类获取菜品"""
    db = SessionLocal()
    try:
        items = db.query(MenuItem).filter(
            MenuItem.category_id == category_id,
            MenuItem.is_available == True
        ).order_by(MenuItem.sort_order).all()
        return [i.to_dict() for i in items]
    finally:
        db.close()


def get_recommended_items():
    """获取推荐菜品"""
    db = SessionLocal()
    try:
        items = db.query(MenuItem).filter(
            MenuItem.is_available == True,
            MenuItem.is_recommended == True
        ).order_by(MenuItem.sort_order).all()
        return [i.to_dict() for i in items]
    finally:
        db.close()


def create_order(openid: str, items_data: list, room_number: str = "",
                 remark: str = "") -> Order:
    """创建订单
    items_data: [{"id": 1, "name": "庐山云雾茶", "quantity": 2, "price": 68}, ...]
    """
    db = SessionLocal()
    try:
        total = sum(item["price"] * item["quantity"] for item in items_data)
        order = Order(
            openid=openid,
            room_number=room_number,
            items=items_data,
            total_price=total,
            status="pending",
            remark=remark,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    finally:
        db.close()


def get_user_orders(openid: str, limit: int = 10):
    """获取用户订单列表"""
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(
            Order.openid == openid
        ).order_by(Order.created_at.desc()).limit(limit).all()
        return [o.to_dict() for o in orders]
    finally:
        db.close()


def get_order_status(order_id: int):
    """查询订单状态"""
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        return order.to_dict() if order else None
    finally:
        db.close()


STATUS_LABELS = {
    "pending": "⏳ 待确认",
    "confirmed": "✅ 已确认",
    "preparing": "👨‍🍳 制作中",
    "delivered": "🚀 已送达",
    "completed": "✔️ 已完成",
    "cancelled": "❌ 已取消",
}


def format_menu_text():
    """格式化为微信文本菜单"""
    categories = get_menu_categories()
    if not categories:
        return "暂无菜单信息，请咨询前台～"

    lines = ["🍜 *云上归墅 · 山间美餐*\n"]

    # 先展示推荐菜品
    recommended = get_recommended_items()
    if recommended:
        lines.append("⭐ *主厨推荐*\n")
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
        icon = cat.get("icon", "🍽️")
        lines.append(f"{icon} *{cat['name']}*")
        for item in items[:5]:  # 每类最多显示5个
            lines.append(f"  {item['name']}  ¥{item['price']}")
        if len(items) > 5:
            lines.append(f"  ... 还有{len(items) - 5}道")
        lines.append("")

    lines.append("─" * 30)
    lines.append("🛒 *如何点餐？*")
    lines.append("  · 回复「点餐」进入点餐页面")
    lines.append("  · 回复「推荐」查看主厨推荐")
    lines.append("  · 回复「菜单+分类名」如「菜单热菜」")
    lines.append("  · 回复「下单+菜品编号」如「下单1,3,5」")
    return "\n".join(lines)


def format_recommended_text():
    """格式化推荐菜品"""
    items = get_recommended_items()
    if not items:
        return "暂无推荐菜品～"

    lines = ["⭐ *主厨推荐*\n"]
    for item in items:
        lines.append(f"*{item['name']}*  ¥{item['price']}")
        lines.append(f"  {item.get('description', '')}")
        if item.get("image"):
            lines.append(f"  🖼️ {item['image']}")
        lines.append("")

    lines.append("💡 回复「下单+编号」即可点餐")
    return "\n".join(lines)


def format_order_status_text(openid: str):
    """格式化用户订单状态"""
    orders = get_user_orders(openid)
    if not orders:
        return "您还没有订单记录～\n回复「点餐」开始您的山间美食之旅吧！"

    lines = ["📋 *我的订单*\n"]
    for order in orders[:5]:
        status_label = STATUS_LABELS.get(order["status"], order["status"])
        items_text = "、".join(
            f"{item['name']}×{item['quantity']}"
            for item in order.get("items", [])
        )
        lines.append(
            f"🔢 订单#{order['id']}\n"
            f"  📦 {items_text}\n"
            f"  💰 ¥{order['total_price']}\n"
            f"  📮 {status_label}\n"
            f"  🕐 {order['created_at']}\n"
        )
    return "\n".join(lines)
