"""
数据库迁移脚本：单民宿 → 三民宿平台
添加 bnb_id 列 + 创建新表 + 插入民宿配置
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_URL, DEBUG
from sqlalchemy import create_engine, text
from models import Base, init_db

engine = create_engine(DATABASE_URL, echo=DEBUG)

TABLES_WITH_BNB_ID = [
    "rooms",
    "bookings",
    "menu_categories",
    "menu_items",
    "orders",
    "service_requests",
    "quick_services",
    "travel_routes",
    "food_recommends",
    "platform_mentions",
    "aggregated_orders",
]

def run():
    with engine.connect() as conn:
        # 1. 为已有表添加 bnb_id 列
        for table in TABLES_WITH_BNB_ID:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN bnb_id VARCHAR(20) NOT NULL DEFAULT 'guishu'"
                ))
                conn.commit()
                print(f"  ✅ {table}.bnb_id 添加成功")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  ⏭️  {table}.bnb_id 已存在，跳过")
                else:
                    print(f"  ❌ {table}: {e}")

    # 2. 创建新表（bnbs + 茶园3张 + 疗愈3张）
    print("\n📦 创建新表...")
    Base.metadata.create_all(engine)
    print("  ✅ 新表创建完成")

    # 3. 插入三家民宿配置
    from models import SessionLocal, Bnb
    db = SessionLocal()
    try:
        bnbs_data = [
            {
                "bnb_id": "guishu", "name": "云上·归墅民宿", "short_name": "云上归墅",
                "address": "庐山山上·庐山风景名胜区大林沟路27号", "phone": "16607927666",
                "latitude": 29.5568, "longitude": 115.9797, "theme_color": "#4a7c59",
                "description": "庐山之巅，大林沟路27号，云雾深处的静谧之所。U型三层山居小院，11间精品客房。",
                "is_active": True, "sort_order": 1,
            },
            {
                "bnb_id": "shanji", "name": "云上·山纪民宿", "short_name": "云上山纪",
                "address": "庐山山上·庐山风景名胜区XX路XX号", "phone": "待填写",
                "latitude": 29.5600, "longitude": 115.9850, "theme_color": "#8B6914",
                "description": "茶园环绕，品茗观山。庐山云雾茶香，伴你悠然山居时光。",
                "is_active": True, "sort_order": 2,
            },
            {
                "bnb_id": "donglinwai", "name": "云上·东林外民宿", "short_name": "云上东林外",
                "address": "庐山山上·庐山风景名胜区XX路XX号", "phone": "待填写",
                "latitude": 29.5500, "longitude": 115.9700, "theme_color": "#7B8DAD",
                "description": "东林寺旁，禅意疗愈之所。放下尘嚣，身心归一。",
                "is_active": True, "sort_order": 3,
            },
        ]
        for bnb_data in bnbs_data:
            existing = db.query(Bnb).filter(Bnb.bnb_id == bnb_data["bnb_id"]).first()
            if not existing:
                db.add(Bnb(**bnb_data))
                print(f"  ✅ 插入民宿: {bnb_data['name']}")
            else:
                print(f"  ⏭️  民宿已存在: {bnb_data['name']}")
        db.commit()
    finally:
        db.close()

    print("\n✅ 数据库迁移完成！")


if __name__ == "__main__":
    run()
