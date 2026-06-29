"""
此山茶场模块服务（云上·山纪专属）
- 茶叶品类展示
- 消费项目（简餐/饮品/甜品/茶道体验）
- 茶叶伴手礼
"""
from models import SessionLocal, TeaType, TeaExperience, TeaProduct
from bnb_context import get_service_bnb_id

# 茶场模块专属山纪，覆写默认值
_get_bnb_id = lambda bnb_id=None: get_service_bnb_id(bnb_id, "shanji")


def get_tea_types(bnb_id=None):
    """获取茶叶品类列表"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        types = db.query(TeaType).filter(
            TeaType.bnb_id == bnb_id
        ).order_by(TeaType.sort_order).all()
        return [t.to_dict() for t in types]
    finally:
        db.close()


def get_tea_experiences(bnb_id=None):
    """获取所有消费项目（含简餐/饮品/甜品/体验）"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        exps = db.query(TeaExperience).filter(
            TeaExperience.bnb_id == bnb_id,
            TeaExperience.is_available == True
        ).order_by(TeaExperience.sort_order).all()
        return [e.to_dict() for e in exps]
    finally:
        db.close()


def get_tea_products(bnb_id=None):
    """获取茶叶伴手礼"""
    bnb_id = _get_bnb_id(bnb_id)
    db = SessionLocal()
    try:
        prods = db.query(TeaProduct).filter(
            TeaProduct.bnb_id == bnb_id,
            TeaProduct.is_available == True
        ).order_by(TeaProduct.sort_order).all()
        return [p.to_dict() for p in prods]
    finally:
        db.close()


def format_tea_text(bnb_id=None):
    """格式化为微信文本输出"""
    bnb_id = _get_bnb_id(bnb_id)
    from bnb_context import get_bnb_config
    cfg = get_bnb_config(bnb_id)
    lines = [f"· *{cfg['short_name']} · 此山茶场*\n"]

    # 营业信息
    lines.append("⏰ 早场 7:00-10:00  晚场 15:00-22:00")
    lines.append("   预约制 · 凭预约码核验入场")
    lines.append("")

    # 消费项目按分类
    exps = get_tea_experiences(bnb_id=bnb_id)
    if exps:
        cat_labels = {"meal": "简餐", "drink": "饮品", "dessert": "甜品", "experience": "茶道体验"}
        by_cat = {}
        for e in exps:
            by_cat.setdefault(e.get("category", "experience"), []).append(e)
        for cat, label in cat_labels.items():
            items = by_cat.get(cat, [])
            if not items:
                continue
            lines.append(f"▸ *{label}*")
            for it in items:
                line = f"  {it['name']}  ¥{it['price']}"
                if it.get("duration"):
                    line += f"  · {it['duration']}"
                lines.append(line)
            lines.append("")

    # 茶叶品类
    types = get_tea_types(bnb_id=bnb_id)
    if types:
        lines.append("▸ *茶叶品类*")
        for t in types:
            lines.append(f"  {t['name']}")
            if t.get('tasting_notes'):
                lines.append(f"    品鉴：{t['tasting_notes']}")
        lines.append("")

    # 伴手礼
    prods = get_tea_products(bnb_id=bnb_id)
    if prods:
        lines.append("▸ *茶叶伴手礼*")
        for p in prods:
            lines.append(f"  {p['name']}  ¥{p['price']}  {p.get('weight', '')}")
            if p.get('description'):
                lines.append(f"    {p['description'][:60]}")
        lines.append("")

    lines.append("▸ 提示： 回复「茶园」查看此山茶场更多内容")
    return "\n".join(lines)
