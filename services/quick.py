"""
快捷服务 - 续住、卫生打扫、维修、叫醒等
"""
from datetime import datetime
from models import SessionLocal, QuickService


def get_all_services():
    """获取所有快捷服务"""
    db = SessionLocal()
    try:
        services = db.query(QuickService).filter(
            QuickService.is_active == True
        ).order_by(QuickService.sort_order).all()
        return [s.to_dict() for s in services]
    finally:
        db.close()


def get_services_by_category(category: str):
    """按分类获取服务"""
    db = SessionLocal()
    try:
        services = db.query(QuickService).filter(
            QuickService.is_active == True,
            QuickService.category == category
        ).order_by(QuickService.sort_order).all()
        return [s.to_dict() for s in services]
    finally:
        db.close()


def format_services_text():
    """格式化为微信服务菜单"""
    services = get_all_services()
    if not services:
        return "暂无快捷服务信息～"

    lines = ["🛎️ *云上归墅 · 快捷服务*\n"]

    categories = {}
    for svc in services:
        cat = svc.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(svc)

    cat_labels = {
        "housekeeping": "🧹 客房服务",
        "maintenance": "🔧 设施维修",
        "frontdesk": "🏨 前台服务",
        "other": "📦 其他服务",
    }

    for cat, items in categories.items():
        label = cat_labels.get(cat, f"📋 {cat}")
        lines.append(label)
        for item in items:
            icon = item.get("icon", "▪️")
            lines.append(
                f"  {icon} *{item['name']}*\n"
                f"     {item.get('description', '')}\n"
                f"     ⏱️ {item.get('estimated_time', '')}\n"
            )
        lines.append("")

    lines.append("─" * 30)
    lines.append("💡 *如何使用快捷服务？*")
    lines.append("  · 回复「服务+名称」如「服务续住」")
    lines.append("  · 回复「打扫」「续住」「维修」「叫醒」直接呼叫")
    lines.append("  · 也可直接拨打前台电话联系")
    return "\n".join(lines)


def handle_service_request(service_name: str) -> str:
    """处理服务请求，返回确认信息"""
    services = get_all_services()

    # 模糊匹配
    matched = None
    for svc in services:
        if service_name in svc["name"] or svc["name"] in service_name:
            matched = svc
            break

    if not matched:
        return (
            f"未找到「{service_name}」服务～\n"
            f"回复「服务」查看所有快捷服务\n"
            f"或直接拨打前台电话咨询"
        )

    icon = matched.get("icon", "✅")
    return (
        f"{icon} *{matched['name']}* 已收到您的请求！\n\n"
        f"📝 {matched.get('description', '')}\n"
        f"⏱️ 预计处理时间：{matched.get('estimated_time', '尽快处理')}\n\n"
        f"我们的工作人员会尽快为您处理～\n"
        f"如有紧急需求，请拨打前台电话 ☎️"
    )
