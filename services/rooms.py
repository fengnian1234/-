"""
房间服务 - 房型查询、展示、预订咨询
"""
from models import SessionLocal, Room


def get_all_rooms():
    """获取所有可订房间"""
    db = SessionLocal()
    try:
        rooms = db.query(Room).filter(Room.is_available == True)\
                  .order_by(Room.sort_order).all()
        return [r.to_dict() for r in rooms]
    finally:
        db.close()


def get_room_by_id(room_id: int):
    """获取单个房间详情"""
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        return room.to_dict() if room else None
    finally:
        db.close()


def get_rooms_by_type(room_type: str):
    """按房型筛选"""
    db = SessionLocal()
    try:
        rooms = db.query(Room).filter(
            Room.is_available == True,
            Room.room_type == room_type
        ).order_by(Room.sort_order).all()
        return [r.to_dict() for r in rooms]
    finally:
        db.close()


def format_rooms_text():
    """将房间列表格式化为微信文本回复"""
    rooms = get_all_rooms()
    if not rooms:
        return "暂无房间信息，请联系人工客服～"

    lines = ["🛏️ *云上归墅 · 房型展示*\n"]
    for i, room in enumerate(rooms, 1):
        view_icon = {"山景": "🏔️", "云海": "☁️", "竹林": "🎋"}.get(room["view_type"], "🏡")
        lines.append(
            f"{view_icon} *{room['name']}*\n"
            f"  💰 ¥{room['price']}/晚  "
            f"{' (原价 ¥'+str(room['original_price'])+')' if room.get('original_price') else ''}\n"
            f"  👤 {room['capacity']}人  |  {room['bed_type']}  |  {room.get('area', '')}\n"
            f"  📝 {room['description'][:80]}...\n"
            f"  ➡️ 回复「房间{room['id']}」查看图文详情\n"
        )
    lines.append("─" * 30)
    lines.append("💡 回复「预订」获取预订联系方式")
    lines.append("💡 回复「房间图片」查看所有房间图片")
    return "\n".join(lines)


def format_room_detail_text(room_id: int):
    """格式化单个房间详情"""
    room = get_room_by_id(room_id)
    if not room:
        return "该房间信息暂未收录，请回复「房型」查看所有房间～"

    amenities_text = "、".join(room.get("amenities", []))

    lines = [
        f"🏡 *{room['name']}* 详情\n",
        f"💰 价格：¥{room['price']}/晚",
        f"📐 面积：{room.get('area', '详询客服')}",
        f"🛏️ 床型：{room.get('bed_type', '详询客服')}",
        f"👤 可住：{room['capacity']}人",
        f"🌅 景观：{room.get('view_type', '')}",
        f"✨ 设施：{amenities_text}",
        f"\n📝 {room['description']}",
        f"\n📞 预订咨询：请回复「预订」获取联系方式",
        f"🖼️ 查看房间图片：{get_image_url(room)}",
    ]
    return "\n".join(lines)


def get_featured_rooms(limit: int = 4):
    """获取精选房型 — 按价格升序，优先有库存的可订房型"""
    db = SessionLocal()
    try:
        rooms = db.query(Room).filter(
            Room.is_available == True,
            Room.total_count > 0
        ).order_by(Room.price).limit(limit).all()
        return [r.to_dict() for r in rooms]
    finally:
        db.close()


def get_image_url(room: dict) -> str:
    """获取房间图片链接"""
    images = room.get("images", [])
    if images:
        return images[0] if isinstance(images[0], str) else images[0].get("url", "")
    return "暂无图片"


def format_rooms_with_images():
    """生成带图片链接的房间展示文本"""
    rooms = get_all_rooms()
    if not rooms:
        return "暂无房间信息"

    lines = ["🖼️ *云上归墅 · 房间图赏*\n"]
    for room in rooms:
        images = room.get("images", [])
        img_urls = [img if isinstance(img, str) else img.get("url", "") for img in images[:3]]
        img_text = "\n  ".join(img_urls) if img_urls else "  暂无图片"

        lines.append(f"*{room['name']}* ({room.get('view_type', '')})")
        lines.append(f"  {img_text}\n")

    lines.append("💡 回复「房间+编号」如「房间1」查看详细图文")
    return "\n".join(lines)
