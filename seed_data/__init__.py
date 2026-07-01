"""
种子数据 — 云上·归墅民宿集群
初始化数据库时自动填充。按 BnB 拆分数据文件。
"""
from services.logger import info, warning, error as log_error
from models import SessionLocal, init_db, Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend, Booking, AggregatedOrder, GuestPoints, PointLog, Bnb

from seed_data.guishu import (
    _seed_guishu_rooms, _seed_guishu_menu, _seed_guishu_services,
    _seed_guishu_travel_routes, _seed_guishu_food_recommends,
)
from seed_data.shanji import (
    _seed_shanji_rooms, _seed_shanji_menu, _seed_shanji_services,
    _seed_common_shanji_routes, _seed_shanji_foods, seed_tea,
)
from seed_data.donglinwai import (
    _seed_donglinwai_rooms, _seed_donglinwai_menu, _seed_donglinwai_services,
    _seed_donglinwai_routes, _seed_donglinwai_foods, seed_healing,
)


# 房型图片辅助 — 图片按 sort_order 编号 room01 ~ room08（归墅专用）
_ROOM_IMAGE_SETS = {
    1: ["/static/img/rooms/room01_00.webp","/static/img/rooms/room01_01.webp","/static/img/rooms/room01_02.webp","/static/img/rooms/room01_03.webp","/static/img/rooms/room01_04.webp"],
    2: ["/static/img/rooms/room02_00.webp","/static/img/rooms/room02_01.webp","/static/img/rooms/room02_02.webp","/static/img/rooms/room02_03.webp","/static/img/rooms/room02_04.webp"],
    3: ["/static/img/rooms/room03_00.webp","/static/img/rooms/room03_01.webp","/static/img/rooms/room03_02.webp","/static/img/rooms/room03_03.webp","/static/img/rooms/room03_04.webp","/static/img/rooms/room03_05.webp","/static/img/rooms/room03_06.webp"],
    4: ["/static/img/rooms/room04_00.webp","/static/img/rooms/room04_01.webp","/static/img/rooms/room04_02.webp","/static/img/rooms/room04_03.webp","/static/img/rooms/room04_04.webp"],
    5: ["/static/img/rooms/room05_00.webp","/static/img/rooms/room05_01.webp","/static/img/rooms/room05_02.webp","/static/img/rooms/room05_03.webp","/static/img/rooms/room05_04.webp","/static/img/rooms/room05_05.webp","/static/img/rooms/room05_06.webp","/static/img/rooms/room05_07.webp","/static/img/rooms/room05_08.webp","/static/img/rooms/room05_09.webp","/static/img/rooms/room05_10.webp"],
    6: ["/static/img/rooms/room06_00.webp","/static/img/rooms/room06_01.webp","/static/img/rooms/room06_02.webp","/static/img/rooms/room06_03.webp","/static/img/rooms/room06_04.webp","/static/img/rooms/room06_05.webp","/static/img/rooms/room06_06.webp","/static/img/rooms/room06_07.webp","/static/img/rooms/room06_08.webp","/static/img/rooms/room06_09.webp","/static/img/rooms/room06_10.webp","/static/img/rooms/room06_11.webp","/static/img/rooms/room06_12.webp"],
    7: ["/static/img/rooms/room07_00.webp","/static/img/rooms/room07_01.webp","/static/img/rooms/room07_02.webp","/static/img/rooms/room07_03.webp","/static/img/rooms/room07_04.webp","/static/img/rooms/room07_05.webp","/static/img/rooms/room07_06.webp","/static/img/rooms/room07_07.webp","/static/img/rooms/room07_08.webp","/static/img/rooms/room07_09.webp","/static/img/rooms/room07_10.webp","/static/img/rooms/room07_11.webp","/static/img/rooms/room07_12.webp","/static/img/rooms/room07_13.webp","/static/img/rooms/room07_14.webp"],
    8: ["/static/img/rooms/room08_00.webp","/static/img/rooms/room08_01.webp","/static/img/rooms/room08_02.webp","/static/img/rooms/room08_03.webp","/static/img/rooms/room08_04.webp"],
}

# 山纪房型图片独立 — 已移至 seed_data/shanji.py
# 东林外房型图片独立 — 已移至 seed_data/donglinwai.py

def _room_imgs(sort_order):
    """按 sort_order 获取房型图片列表（归墅专用）"""
    return _ROOM_IMAGE_SETS.get(sort_order, [])


def seed_all():
    """初始化数据库并填充种子数据（支持三民宿独立数据）"""
    init_db()
    db = SessionLocal()

    try:
        # 0. 确保 Bnb 基础信息表已填充（从 BNB_CONFIGS 同步）
        seed_bnbs(db)

        # 检查哪些民宿已有客房数据（客房/菜单/服务仅首次填充）
        existing_bnbs = set()
        if db.query(Room).count() > 0:
            existing_bnbs = set(r[0] for r in db.query(Room.bnb_id).distinct().all())

        # 逐民宿填充客房/菜单/服务（仅首次）
        for bnb_id in ["guishu", "shanji", "donglinwai"]:
            if bnb_id not in existing_bnbs:
                info(f" 初始化 {bnb_id} 客房/菜单/服务数据...")
                seed_rooms(db, bnb_id)
                seed_menu(db, bnb_id)
                seed_services(db, bnb_id)
                info(f"   {bnb_id} 基础数据填充完成")

        # 攻略数据（路线+美食）每次启动刷新，确保与种子文件一致
        for bnb_id in ["guishu", "shanji", "donglinwai"]:
            fc = db.query(FoodRecommend).filter(FoodRecommend.bnb_id == bnb_id).count()
            rc = db.query(TravelRoute).filter(TravelRoute.bnb_id == bnb_id).count()
            if fc > 0 or rc > 0:
                db.query(FoodRecommend).filter(FoodRecommend.bnb_id == bnb_id).delete()
                db.query(TravelRoute).filter(TravelRoute.bnb_id == bnb_id).delete()
                db.flush()
            seed_travel_routes(db, bnb_id)
            seed_food_recommends(db, bnb_id)
            info(f" 攻略数据刷新: {bnb_id}" + (f" ({rc}→路线, {fc}→美食)" if fc or rc else ""))

        # 公共数据（仅初始化一次）
        if db.query(AggregatedOrder).count() == 0:
            seed_orders(db)
        if db.query(Booking).count() == 0:
            seed_bookings(db)
        if db.query(PointLog).count() == 0:
            seed_points(db)
        db.commit()

        # 特色模块（按民宿独立初始化）
        if "shanji" not in existing_bnbs:
            seed_tea("shanji")
        if "donglinwai" not in existing_bnbs:
            seed_healing("donglinwai")

        info(" 种子数据初始化完成！")

    except Exception as e:
        db.rollback()
        log_error(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


def seed_bnbs(db):
    """从 BNB_CONFIGS 同步民宿基础信息到 bnbs 表（upsert）"""
    from config import BNB_CONFIGS

    for bnb_id, cfg in BNB_CONFIGS.items():
        existing = db.query(Bnb).filter(Bnb.bnb_id == bnb_id).first()
        if existing:
            existing.name = cfg["name"]
            existing.short_name = cfg["short_name"]
            existing.address = cfg["address"]
            existing.phone = cfg["phone"]
            existing.latitude = cfg.get("latitude")
            existing.longitude = cfg.get("longitude")
            existing.description = cfg.get("description", "")
            existing.theme_color = cfg.get("theme_color", "")
            existing.is_active = True
        else:
            bnb = Bnb(
                bnb_id=bnb_id,
                name=cfg["name"],
                short_name=cfg["short_name"],
                address=cfg["address"],
                phone=cfg["phone"],
                latitude=cfg.get("latitude"),
                longitude=cfg.get("longitude"),
                description=cfg.get("description", ""),
                theme_color=cfg.get("theme_color", ""),
                is_active=True,
                sort_order=list(BNB_CONFIGS.keys()).index(bnb_id),
            )
            db.add(bnb)
    db.commit()
    info(f"✅ BnB 基础信息已同步: {len(BNB_CONFIGS)} 家民宿")


def seed_rooms(db, bnb_id="guishu"):
    """房间数据 — 按民宿分发"""
    if bnb_id == "shanji":
        _seed_shanji_rooms(db)
    elif bnb_id == "donglinwai":
        _seed_donglinwai_rooms(db)
    else:
        _seed_guishu_rooms(db)


def seed_menu(db, bnb_id="guishu"):
    """菜单数据 — 按民宿分发"""
    if bnb_id == "shanji":
        _seed_shanji_menu(db)
    elif bnb_id == "donglinwai":
        _seed_donglinwai_menu(db)
    else:
        _seed_guishu_menu(db)


def seed_services(db, bnb_id="guishu"):
    """快捷服务数据 — 按民宿分发"""
    if bnb_id == "shanji":
        _seed_shanji_services(db)
    elif bnb_id == "donglinwai":
        _seed_donglinwai_services(db)
    else:
        _seed_guishu_services(db)


def seed_travel_routes(db, bnb_id="guishu"):
    """旅游路线数据 — 按民宿分发"""
    if bnb_id == "shanji":
        _seed_common_shanji_routes(db)
    elif bnb_id == "donglinwai":
        _seed_donglinwai_routes(db)
    else:
        _seed_guishu_travel_routes(db)


def seed_food_recommends(db, bnb_id="guishu"):
    """周边美食推荐 — 按民宿分发"""
    if bnb_id == "shanji":
        _seed_shanji_foods(db)
    elif bnb_id == "donglinwai":
        _seed_donglinwai_foods(db)
    else:
        _seed_guishu_food_recommends(db)


def seed_orders(db):
    """示例订单数据"""
    from datetime import datetime, timedelta, UTC
    if db.query(AggregatedOrder).count() > 0:
        return
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    tmr = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")
    d3 = (datetime.now(UTC) + timedelta(days=3)).strftime("%Y-%m-%d")
    d5 = (datetime.now(UTC) + timedelta(days=5)).strftime("%Y-%m-%d")
    PLATFORM_FEES = {"ctrip":0.12,"meituan":0.10,"fliggy":0.10,"dianping":0.08,"direct":0,"xiaohongshu":0,"douyin":0}
    orders = [
        ("ctrip","CT20260601","张伟","山景·精致大床房",today,tmr,1,688,2,"checked_in"),
        ("meituan","MT20260602","李娜","田园家庭房",today,tmr,1,788,3,"checked_in"),
        ("fliggy","FZ20260603","王磊","清舍·露台大床房",today,tmr,1,788,2,"confirmed"),
        ("ctrip","CT20260604","赵雪","室雅茶香套房",tmr,d3,2,1976,4,"confirmed"),
        ("direct","","陈明","知还标准间",tmr,d3,2,976,2,"confirmed"),
        ("meituan","MT20260605","刘洋","特惠标准间",d5,(datetime.now(UTC)+timedelta(days=6)).strftime("%Y-%m-%d"),1,388,2,"confirmed"),
        ("xiaohongshu","","孙雨","山野大床房",d5,(datetime.now(UTC)+timedelta(days=7)).strftime("%Y-%m-%d"),2,1176,2,"confirmed"),
    ]
    for plat, oid, name, room, ci, co, n, amt, gc, st in orders:
        fee = round(amt * PLATFORM_FEES.get(plat, 0), 2)
        db.add(AggregatedOrder(platform=plat,platform_order_id=oid,guest_name=name,room_type=room,check_in=ci,check_out=co,nights=n,total_amount=amt,platform_fee=fee,net_revenue=round(amt-fee,2),guest_count=gc,status=st,source="seed"))
    db.commit()


def seed_bookings(db):
    """预订种子数据 — 演示AI解锁 + 退房好评推送"""
    from datetime import datetime, timedelta, UTC
    if db.query(Booking).count() > 0:
        return
    now = datetime.now(UTC)
    today = now.strftime("%Y-%m-%d")
    tmr = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    yst = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    bookings = [
        Booking(
            openid="demo_user", guest_name="张伟", phone="138****6789",
            platform="携程", room_type="山景·精致大床房",
            check_in_date=today, check_out_date=tmr,
            status="confirmed", ai_enabled=True,
            created_at=now,
        ),
        Booking(
            openid="demo_user2", guest_name="李娜", phone="139****8901",
            platform="美团", room_type="田园家庭房",
            check_in_date=yst, check_out_date=today,
            room_number="301", status="checked_out",
            ai_enabled=True,
            checked_out_at=now - timedelta(minutes=35),
            review_sent=False,
            created_at=now - timedelta(days=2),
        ),
        Booking(
            openid="web_user", guest_name="王磊", phone="136****2345",
            platform="飞猪", room_type="清舍·露台大床房",
            check_in_date=today, check_out_date=tmr,
            room_number="202", status="checked_in",
            ai_enabled=True,
            created_at=now - timedelta(hours=3),
        ),
    ]
    db.add_all(bookings)


def seed_points(db):
    """积分种子数据 — 演示积分中心"""
    from datetime import datetime, timedelta, UTC
    if db.query(GuestPoints).count() > 0:
        return
    now = datetime.now(UTC)

    # 积分账户（银卡会员，85基础分 → 距金卡还差2150分）
    guest = GuestPoints(
        openid="web_user", total_points=530, total_earned=850,
        base_earned=850, total_spent=320, membership="silver",
    )
    db.add(guest)
    db.flush()

    # 积分流水
    logs = [
        PointLog(openid="web_user", points=100, action="earn_checkin",
                 description="每日签到 +100", created_at=now - timedelta(hours=2)),
        PointLog(openid="web_user", points=200, action="earn_booking",
                 description="预订确认 +200", created_at=now - timedelta(days=1)),
        PointLog(openid="web_user", points=300, action="earn_review",
                 description="携程好评 +300", created_at=now - timedelta(days=3)),
        PointLog(openid="web_user", points=50, action="earn_share",
                 description="分享民宿 +50", created_at=now - timedelta(days=4)),
        PointLog(openid="web_user", points=100, action="earn_checkin",
                 description="每日签到 +100", created_at=now - timedelta(days=5)),
        PointLog(openid="web_user", points=100, action="earn_checkin",
                 description="每日签到 +100", created_at=now - timedelta(days=6)),
        PointLog(openid="web_user", points=-120, action="redeem_coffee",
                 description="兑换手冲咖啡 -120", created_at=now - timedelta(days=3)),
        PointLog(openid="web_user", points=-200, action="redeem_gift",
                 description="兑换云雾茶包体验装 -200", created_at=now - timedelta(days=7)),
    ]
    db.add_all(logs)



if __name__ == "__main__":
    seed_all()
