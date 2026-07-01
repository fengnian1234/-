"""刷新归墅攻略数据 — 删除旧数据触发seed_all重填"""
from models import SessionLocal, FoodRecommend, TravelRoute
from seed_data.guishu import _seed_guishu_travel_routes, _seed_guishu_food_recommends

db = SessionLocal()
fc = db.query(FoodRecommend).filter(FoodRecommend.bnb_id == 'guishu').delete()
rc = db.query(TravelRoute).filter(TravelRoute.bnb_id == 'guishu').delete()
db.commit()
print(f"已删除归墅 {fc} 条美食 + {rc} 条路线旧数据")

# 立即重新填充
_seed_guishu_travel_routes(db)
_seed_guishu_food_recommends(db)
db.commit()

# 验证
fc2 = db.query(FoodRecommend).filter(FoodRecommend.bnb_id == 'guishu').count()
rc2 = db.query(TravelRoute).filter(TravelRoute.bnb_id == 'guishu').count()
# 检查见山茶
jsc = db.query(FoodRecommend).filter(FoodRecommend.name.like('%见山%')).first()
print(f"重seed完成: {rc2} 条路线 + {fc2} 条美食")
if jsc:
    print(f"见山茶 desc: {jsc.description}")
    print(f"见山茶 detail长度: {len(jsc.detail_content or '')} 字符")
db.close()
