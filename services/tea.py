"""
茶园模块服务（云上·山纪专属）
- 茶叶品类展示
- 茶园体验项目
- 茶叶商城
"""
from models import SessionLocal, TeaType, TeaExperience, TeaProduct
from bnb_context import get_service_bnb_id

# 茶园模块专属山纪，覆写默认值
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
    """获取茶园体验项目"""
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
    """获取茶叶商品"""
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
    lines = ["🍵 *云上山纪 · 茶园体验*\n"]

    types = get_tea_types(bnb_id=bnb_id)
    if types:
        lines.append("🌱 *茶叶品类*")
        for t in types:
            lines.append(f"  {t['name']}")
            if t.get('description'):
                lines.append(f"    {t['description'][:60]}")
            if t.get('tasting_notes'):
                lines.append(f"    品鉴：{t['tasting_notes']}")
        lines.append("")

    exps = get_tea_experiences(bnb_id=bnb_id)
    if exps:
        lines.append("🧑‍🌾 *茶园体验*")
        for e in exps:
            lines.append(f"  {e['name']}  ¥{e['price']}")
            lines.append(f"    ⏱️ {e['duration']}  |  👥 {e['capacity']}人")
            if e.get('description'):
                lines.append(f"    {e['description'][:60]}")
        lines.append("")

    lines.append("💡 回复「茶园」查看更多茶文化内容")
    return "\n".join(lines)
