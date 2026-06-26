"""
旅游推荐服务 - 庐山游玩路线、美食推荐、地图导航
"""
from models import SessionLocal, TravelRoute, FoodRecommend
from bnb_context import get_service_bnb_id as _get_bnb_id


def get_all_routes(bnb_id=None):
    """获取所有游玩路线"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        routes = db.query(TravelRoute).filter(
            TravelRoute.bnb_id == bnb_id
        ).order_by(TravelRoute.sort_order).all()
        return [r.to_dict() for r in routes]
    finally:
        db.close()


def get_route_by_id(route_id: int, bnb_id=None):
    """获取单条路线详情"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        route = db.query(TravelRoute).filter(
            TravelRoute.id == route_id, TravelRoute.bnb_id == bnb_id
        ).first()
        return route.to_dict() if route else None
    finally:
        db.close()


def get_all_food_recommends(bnb_id=None):
    """获取所有美食推荐"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        foods = db.query(FoodRecommend).filter(
            FoodRecommend.bnb_id == bnb_id
        ).order_by(FoodRecommend.sort_order).all()
        return [f.to_dict() for f in foods]
    finally:
        db.close()


def get_food_by_category(category: str, bnb_id=None):
    """按类别获取美食推荐"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        foods = db.query(FoodRecommend).filter(
            FoodRecommend.bnb_id == bnb_id,
            FoodRecommend.category == category
        ).order_by(FoodRecommend.sort_order).all()
        return [f.to_dict() for f in foods]
    finally:
        db.close()


def get_food_by_id(food_id: int, bnb_id=None):
    """获取单个美食详情"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        food = db.query(FoodRecommend).filter(
            FoodRecommend.id == food_id, FoodRecommend.bnb_id == bnb_id
        ).first()
        return food.to_dict() if food else None
    finally:
        db.close()


def generate_map_link(name: str, lat: float, lng: float,
                      scale: int = 16) -> str:
    """生成腾讯地图链接（微信内置浏览器兼容）"""
    return (
        f"https://apis.map.qq.com/uri/v1/marker?"
        f"marker=coord:{lat},{lng};title:{name}&"
        f"referer=yunshangbnb"
    )


def generate_amap_link(name: str, lat: float, lng: float) -> str:
    """生成高德地图链接"""
    return f"https://uri.amap.com/marker?position={lng},{lat}&name={name}"


def format_routes_text(bnb_id=None):
    """格式化为游玩路线文本"""
    bnb_id = _get_bnb_id(bnb_id)
    routes = get_all_routes(bnb_id=bnb_id)
    if not routes:
        return "暂无游玩路线信息，请咨询前台获取最新攻略～"

    lines = ["🗺️ *庐山游玩攻略*\n"]

    # 民宿位置
    from config import BNB_CONFIGS
    bnb_cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    lines.append(f"📍 *{bnb_cfg['short_name']}* 位于 {bnb_cfg['address']}")
    lines.append(f"  🗺️ 查看地图：{generate_amap_link(bnb_cfg['name'], bnb_cfg['latitude'], bnb_cfg['longitude'])}")
    lines.append("")

    # 推荐路线
    recommended = [r for r in routes if r.get("is_recommended")]
    others = [r for r in routes if not r.get("is_recommended")]

    if recommended:
        lines.append("⭐ *精选推荐路线*\n")
        for route in recommended:
            lines.append(format_route_summary(route))

    if others:
        lines.append("🗺️ *更多路线*\n")
        for route in others:
            lines.append(format_route_summary(route))

    lines.append("─" * 30)
    lines.append("💡 回复「路线+编号」如「路线1」查看详细攻略")
    lines.append("💡 回复「美食」查看周边美食推荐")
    lines.append("💡 回复「地图」查看民宿位置导航")
    return "\n".join(lines)


def format_route_summary(route: dict) -> str:
    """格式化单条路线摘要"""
    difficulty_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
    diff = difficulty_icon.get(route.get("difficulty", "easy"), "🟢")
    return (
        f"*{route['name']}*\n"
        f"  ⏱️ {route.get('duration', '')}  |  {diff} {route.get('difficulty', '')}\n"
        f"  📝 {route.get('description', '')[:80]}\n"
        f"  🗺️ {route.get('map_link', '')}\n\n"
    )


def format_route_detail_text(route_id: int, bnb_id=None):
    """格式化单条路线详情"""
    bnb_id = _get_bnb_id(bnb_id)
    route = get_route_by_id(route_id, bnb_id=bnb_id)
    if not route:
        return "该路线信息暂未收录，回复「攻略」查看所有路线～"

    difficulty_icon = {"easy": "🟢 轻松", "medium": "🟡 适中", "hard": "🔴 挑战"}
    diff = difficulty_icon.get(route.get("difficulty", "easy"), "轻松")

    lines = [
        f"🗺️ *{route['name']}* 详细攻略\n",
        f"⏱️ 建议时长：{route.get('duration', '')}",
        f"💪 难度：{diff}",
        f"\n📝 {route.get('description', '')}\n",
    ]

    spots = route.get("spots", [])
    if spots:
        lines.append("🏞️ *途经景点*")
        for i, spot in enumerate(spots, 1):
            spot_name = spot.get("name", "") if isinstance(spot, dict) else spot
            spot_desc = spot.get("description", "") if isinstance(spot, dict) else ""
            lines.append(f"  {i}. {spot_name}")
            if spot_desc:
                lines.append(f"     {spot_desc[:60]}")

    if route.get("tips"):
        lines.append(f"\n💡 *小贴士*")
        lines.append(f"  {route['tips']}")

    if route.get("map_link"):
        lines.append(f"\n🗺️ *导航路线*")
        lines.append(f"  {route['map_link']}")

    return "\n".join(lines)


def format_food_text(bnb_id=None):
    """格式化美食推荐"""
    bnb_id = _get_bnb_id(bnb_id)
    foods = get_all_food_recommends(bnb_id=bnb_id)
    if not foods:
        return "暂无美食推荐信息～"

    lines = ["🍜 *庐山周边美食推荐*\n"]

    categories = {}
    for food in foods:
        cat = food.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(food)

    for cat, items in categories.items():
        lines.append(f"*{cat}*")
        for item in items:
            lines.append(
                f"  🏠 {item['name']}\n"
                f"  💰 人均：{item.get('price_range', '详询')}\n"
                f"  📝 {item.get('description', '')[:60]}\n"
                f"  🥢 必点：{item.get('must_try', '')}\n"
                f"  📍 {item.get('address', '')}\n"
                f"  🗺️ {item.get('map_link', '')}\n"
            )
        lines.append("")

    lines.append("💡 回复「美食+类别」如「美食赣菜」筛选类别")
    lines.append("💡 回复「美食+编号」如「美食1」查看详细图文攻略")
    return "\n".join(lines)


def format_food_detail_text(food_id: int, bnb_id=None):
    """格式化单条美食详情（XHS风格微信文本）"""
    bnb_id = _get_bnb_id(bnb_id)
    food = get_food_by_id(food_id, bnb_id=bnb_id)
    if not food:
        return "该美食信息暂未收录，回复「美食」查看所有推荐～"

    lines = [
        f"🍜 *{food['name']}* 详细攻略\n",
        f"🏷️ 类别：{food.get('category', '')}",
        f"💰 {food.get('price_range', '')}",
    ]

    tags = food.get("tags", [])
    if tags:
        lines.append(f"{' '.join(tags)}")

    if food.get("detail_content"):
        lines.append(f"\n{food['detail_content']}")

    lines.append(f"\n🥢 *必点*：{food.get('must_try', '')}")
    lines.append(f"📍 {food.get('address', '')}")

    if food.get("map_link"):
        lines.append(f"🗺️ 导航：{food['map_link']}")

    lines.append(f"\n💡 回复「美食」查看全部推荐")
    return "\n".join(lines)


def format_location_text(bnb_id="guishu"):
    """格式化民宿位置和导航信息"""
    from config import BNB_CONFIGS
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    address = cfg["address"]
    lat = cfg["latitude"]
    lng = cfg["longitude"]
    phone = cfg["phone"]

    amap_link = generate_amap_link(name, lat, lng)

    return f"""📍 *{name} · 位置导航*

🏠 地址：{address}
📞 电话：{phone}

🗺️ *点击导航*
  · 高德地图：{amap_link}

🚗 *交通指南*
  · 自驾：导航至「庐山牯岭镇」
  · 高铁：至「九江站」或「庐山站」，转乘上山巴士
  · 飞机：至「南昌昌北机场」或「九江庐山机场」，转乘上山

🚌 *上山方式*
  · 庐山北门换乘中心 → 景区观光车 → 牯岭镇
  · 索道：庐山交通索道（推荐，10分钟上山）

💡 到达牯岭镇后，沿正街前行约500米即到云上归墅～
    """
