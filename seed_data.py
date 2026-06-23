"""
种子数据 - 云上·归墅民宿和庐山旅游信息
v2：菜单改为咖啡简餐，地址更新为大林沟路27号
初始化数据库时自动填充
"""
from services.logger import info, warning, error as log_error
from models import SessionLocal, init_db, Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend, Booking, AggregatedOrder, GuestPoints, PointLog


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

# 山纪房型图片独立 — 来自 local_data/images 按房间名校验的文件夹
# sort_order → 图片张数，路径格式: /static/img/rooms/shanji/room{sort_order:02d}_{index:02d}.webp
_SHANJI_ROOM_IMAGE_COUNTS = {
    1:9, 2:7, 3:5, 4:6, 5:9, 6:7, 7:5, 8:6,
    9:7, 10:6, 11:7, 12:11, 13:6, 14:13, 15:8, 16:8,
}

# 东林外房型图片独立 — 来自 local_data/images 按房间名校验的文件夹
# sort_order → 图片张数，路径格式: /static/img/rooms/donglinwai/room{sort_order:02d}_{index:02d}.webp
_DONGLINWAI_ROOM_IMAGE_COUNTS = {
    1:5, 2:5, 3:5, 4:6, 5:7, 6:7,
}

def _room_imgs(sort_order):
    """按 sort_order 获取房型图片列表（归墅专用）"""
    return _ROOM_IMAGE_SETS.get(sort_order, [])


def _shanji_room_imgs(sort_order):
    """按 sort_order 获取山纪房型图片列表（独立图片库）"""
    count = _SHANJI_ROOM_IMAGE_COUNTS.get(sort_order, 0)
    return [f"/static/img/rooms/shanji/room{sort_order:02d}_{i:02d}.webp"
            for i in range(count)]


def _donglinwai_room_imgs(sort_order):
    """按 sort_order 获取东林外房型图片列表（独立图片库）"""
    count = _DONGLINWAI_ROOM_IMAGE_COUNTS.get(sort_order, 0)
    return [f"/static/img/rooms/donglinwai/room{sort_order:02d}_{i:02d}.webp"
            for i in range(count)]


def seed_all():
    """初始化数据库并填充种子数据（支持三民宿独立数据）"""
    init_db()
    db = SessionLocal()

    try:
        # 检查哪些民宿已有客房数据
        existing_bnbs = set()
        if db.query(Room).count() > 0:
            existing_bnbs = set(r[0] for r in db.query(Room.bnb_id).distinct().all())

        # 逐民宿填充数据（各民宿数据独立，互不覆盖）
        for bnb_id in ["guishu", "shanji", "donglinwai"]:
            if bnb_id not in existing_bnbs:
                info(f" 初始化 {bnb_id} 客房/菜单/服务数据...")
                seed_rooms(db, bnb_id)
                seed_menu(db, bnb_id)
                seed_services(db, bnb_id)
                seed_travel_routes(db, bnb_id)
                seed_food_recommends(db, bnb_id)
                info(f"   {bnb_id} 基础数据填充完成")

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


def seed_rooms(db, bnb_id="guishu"):
    """房间数据 — 来自携程官方平台（2026.6）"""
    if bnb_id == "shanji":
        _seed_shanji_rooms(db)
        return
    if bnb_id == "donglinwai":
        _seed_donglinwai_rooms(db)
        return

    # ── 归墅 (guishu) ──
    rooms = [
        Room(
            name="特惠单人间",
            room_type="单人间",
            price=388, original_price=488,
            description="紧凑温馨的单人空间，1.5米双人床，独立卫浴。小而精致，独行旅客的实惠之选。",
            capacity=1, bed_type="1.5m双人床", area="15m²",
            amenities=["观景窗", "地暖", "智能马桶", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room01_00.webp","/static/img/rooms/room01_01.webp",
                "/static/img/rooms/room01_02.webp","/static/img/rooms/room01_03.webp",
                "/static/img/rooms/room01_04.webp",
            ],
            view_type="山景", is_available=True, total_count=1, sort_order=1,
        ),
        Room(
            name="特惠标准间",
            room_type="双床房",
            price=388, original_price=488,
            description="两张1.2米单人床，紧凑实用。适合闺蜜出游或预算有限的结伴旅客。",
            capacity=2, bed_type="2×1.2m单人床", area="15m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi"],
            images=[
                "/static/img/rooms/room02_00.webp","/static/img/rooms/room02_01.webp",
                "/static/img/rooms/room02_02.webp","/static/img/rooms/room02_03.webp",
                "/static/img/rooms/room02_04.webp",
            ],
            view_type="山景", is_available=True, total_count=2, sort_order=2,
        ),
        Room(
            name="知还标准间",
            room_type="双床房",
            price=488, original_price=588,
            description="「云无心以出岫，鸟倦飞而知还」——以民宿命名出处的诗句命名。20m²宽敞双床房，两张1.2米单人床。",
            capacity=2, bed_type="2×1.2m单人床", area="20m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room03_00.webp","/static/img/rooms/room03_01.webp",
                "/static/img/rooms/room03_02.webp","/static/img/rooms/room03_03.webp",
                "/static/img/rooms/room03_04.webp","/static/img/rooms/room03_05.webp",
                "/static/img/rooms/room03_06.webp",
            ],
            view_type="山景", is_available=True, total_count=2, sort_order=3,
        ),
        Room(
            name="山野大床房",
            room_type="大床房",
            price=588, original_price=688,
            description="1.8米大床房，推窗见山。简约自然的原木风格，是情侣和独行旅客的热门之选。",
            capacity=2, bed_type="1.8m大床", area="20m²",
            amenities=["观景窗", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi"],
            images=[
                "/static/img/rooms/room04_00.webp","/static/img/rooms/room04_01.webp",
                "/static/img/rooms/room04_02.webp","/static/img/rooms/room04_03.webp",
                "/static/img/rooms/room04_04.webp",
            ],
            view_type="山景", is_available=True, total_count=1, sort_order=4,
        ),
        Room(
            name="清舍·露台大床房",
            room_type="大床房",
            price=788, original_price=888,
            description="自带独立露台，坐看云起云落。35m²宽敞空间，1.8米大床，是民宿最受欢迎的房型之一。",
            capacity=2, bed_type="1.8m大床", area="35m²",
            amenities=["独立露台", "观景阳台", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room05_00.webp","/static/img/rooms/room05_01.webp",
                "/static/img/rooms/room05_02.webp","/static/img/rooms/room05_03.webp",
                "/static/img/rooms/room05_04.webp","/static/img/rooms/room05_05.webp",
                "/static/img/rooms/room05_06.webp","/static/img/rooms/room05_07.webp",
                "/static/img/rooms/room05_08.webp","/static/img/rooms/room05_09.webp",
                "/static/img/rooms/room05_10.webp",
            ],
            view_type="山景/露台", is_available=True, total_count=2, sort_order=5,
        ),
        Room(
            name="山景·精致大床房",
            room_type="大床房",
            price=688, original_price=788,
            description="30m²精致山景房，1.8米大床配全景窗。精心布置的简约现代风格，推窗即漫山青翠。",
            capacity=2, bed_type="1.8m大床", area="30m²",
            amenities=["全景窗", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room06_00.webp","/static/img/rooms/room06_01.webp",
                "/static/img/rooms/room06_02.webp","/static/img/rooms/room06_03.webp",
                "/static/img/rooms/room06_04.webp","/static/img/rooms/room06_05.webp",
                "/static/img/rooms/room06_06.webp","/static/img/rooms/room06_07.webp",
                "/static/img/rooms/room06_08.webp","/static/img/rooms/room06_09.webp",
                "/static/img/rooms/room06_10.webp","/static/img/rooms/room06_11.webp",
                "/static/img/rooms/room06_12.webp",
            ],
            view_type="山景", is_available=True, total_count=1, sort_order=6,
        ),
        Room(
            name="室雅茶香套房",
            room_type="套房",
            price=988, original_price=1188,
            description="30m²套房格局，1.8米大床+1.5米双人床。独立茶室区域，配高端茶具，品庐山云雾茶，闻茶香入眠。",
            capacity=4, bed_type="1.8m大床 + 1.5m双人床", area="30m²",
            amenities=["独立茶室", "观景阳台", "地暖", "智能马桶", "浴缸", "高端茶具", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room07_00.webp","/static/img/rooms/room07_01.webp",
                "/static/img/rooms/room07_02.webp","/static/img/rooms/room07_03.webp",
                "/static/img/rooms/room07_04.webp","/static/img/rooms/room07_05.webp",
                "/static/img/rooms/room07_06.webp","/static/img/rooms/room07_07.webp",
                "/static/img/rooms/room07_08.webp","/static/img/rooms/room07_09.webp",
                "/static/img/rooms/room07_10.webp","/static/img/rooms/room07_11.webp",
                "/static/img/rooms/room07_12.webp","/static/img/rooms/room07_13.webp",
                "/static/img/rooms/room07_14.webp",
            ],
            view_type="山景", is_available=True, total_count=1, sort_order=7,
        ),
        Room(
            name="田园家庭房",
            room_type="家庭房",
            price=788, original_price=888,
            description="1.8米大床+1.2米单人床，20m²温馨家庭空间。适合三口之家出行，简约舒适的田园风格。",
            capacity=3, bed_type="1.8m大床 + 1.2m单人床", area="20m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "/static/img/rooms/room08_00.webp","/static/img/rooms/room08_01.webp",
                "/static/img/rooms/room08_02.webp","/static/img/rooms/room08_03.webp",
                "/static/img/rooms/room08_04.webp",
            ],
            view_type="山景", is_available=True, total_count=1, sort_order=8,
        ),
    ]
    db.add_all(rooms)


def _seed_shanji_rooms(db):
    """山纪客房 — 官方数据（2026.6），30间16种房型，按民宿主指定排序"""
    rooms = [
        # 1. 山色 — 豪华复式套房（地暖.客厅+麻将室+双卫+双阳台）
        Room(bnb_id="shanji", name="「山色」豪华复式套房", room_type="复式套房",
             price=1188, original_price=1388, capacity=4,
             description="双层复式，两张大床。客厅+麻将室+双卫+双阳台+地暖，山纪最豪华房型。",
             bed_type="2×1.8m大床", area="55m²",
             amenities=["地暖", "客厅", "麻将室", "双卫", "双阳台", "智能马桶", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "迷你吧"],
             view_type="山景", total_count=1, sort_order=1),
        # 2. 云庭 — 景观大床房（KingKoll床垫+品牌卫浴）
        Room(bnb_id="shanji", name="「云庭」景观大床房", room_type="大床房",
             price=528, original_price=628, capacity=2,
             description="1.8米大床，KingKoll床垫，品牌卫浴。推窗见山，雅致舒适。",
             bed_type="1.8m大床", area="25m²",
             amenities=["独立阳台", "地暖", "KingKoll床垫", "品牌卫浴", "高速WiFi", "书桌", "茶具套装"],
             view_type="山景", total_count=3, sort_order=2),
        # 3. 纪云 — 院景双床房（投影.KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「纪云」院景双床房", room_type="双床房",
             price=488, original_price=588, capacity=2,
             description="两张1.2米单人床，投影仪+KingKoll床垫+TOTO卫浴。庭院景观，影音享受。",
             bed_type="2×1.2m单人床", area="22m²",
             amenities=["投影仪", "庭院景观", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi"],
             view_type="庭院", total_count=1, sort_order=3),
        # 4. 纪山 — 雅致大床房（KingKoll床垫.品牌卫浴）
        Room(bnb_id="shanji", name="「纪山」雅致大床房", room_type="大床房",
             price=588, original_price=688, capacity=2,
             description="1.8米大床，KingKoll床垫，品牌卫浴。雅致原木风，静享山居。",
             bed_type="1.8m大床", area="28m²",
             amenities=["独立阳台", "地暖", "KingKoll床垫", "品牌卫浴", "高速WiFi", "茶具套装", "迷你吧"],
             view_type="山景", total_count=2, sort_order=4),
        # 5. 云瑶 — 山景大床房（落地窗.浴缸.沙发床）
        Room(bnb_id="shanji", name="「云瑶」山景大床房", room_type="大床房",
             price=688, original_price=788, capacity=3,
             description="1.8米大床+沙发床。全景落地窗+浴缸，环山云雾尽收眼底。",
             bed_type="1.8m大床 + 沙发床", area="32m²",
             amenities=["全景落地窗", "浴缸", "沙发床", "地暖", "智能马桶", "加热毛巾架", "高速WiFi", "迷你吧"],
             view_type="环山全景", total_count=2, sort_order=5),
        # 6. 云月 — 观景亲子房（地暖.KingKoll床垫.TOTO卫浴.阳台）
        Room(bnb_id="shanji", name="「云月」观景亲子房", room_type="亲子房",
             price=688, original_price=788, capacity=3,
             description="1.8米大床+沙发床。地暖+阳台+KingKoll床垫+TOTO卫浴，亲子家庭的温馨之选。",
             bed_type="1.8m大床 + 沙发床", area="32m²",
             amenities=["地暖", "KingKoll床垫", "TOTO卫浴", "独立阳台", "高速WiFi", "儿童用品"],
             view_type="山景", total_count=1, sort_order=6),
        # 7. 云霏 — 尊享观景阳台大床房（KingKoll床垫.TOTO卫浴）★新增
        Room(bnb_id="shanji", name="「云霏」尊享观景阳台大床房", room_type="大床房",
             price=598, original_price=698, capacity=2,
             description="1.8米大床，独立观景阳台。KingKoll床垫+TOTO卫浴，私享阳台揽尽山色。",
             bed_type="1.8m大床", area="28m²",
             amenities=["独立阳台", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "迷你吧"],
             view_type="山景", total_count=2, sort_order=7),
        # 8. 纪林 — 轻享大床房（KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「纪林」轻享大床房", room_type="大床房",
             price=388, original_price=488, capacity=2,
             description="1.5米双人床，KingKoll床垫+TOTO卫浴。入门优选，简约舒适。",
             bed_type="1.5m双人床", area="18m²",
             amenities=["观景窗", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi"],
             view_type="山景", total_count=2, sort_order=8),
        # 9. 纪泉 — 景观大床房（地暖.阳台.KingKoll床垫.TOTO）★新增
        Room(bnb_id="shanji", name="「纪泉」景观大床房", room_type="大床房",
             price=598, original_price=698, capacity=2,
             description="1.8米大床，地暖+阳台+KingKoll床垫+TOTO卫浴。四重舒适，一房尽享。",
             bed_type="1.8m大床", area="28m²",
             amenities=["地暖", "独立阳台", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "茶具套装"],
             view_type="山景", total_count=2, sort_order=9),
        # 10. 纪庐 — 露台观景大床房（露台+网红浴缸）★新增
        Room(bnb_id="shanji", name="「纪庐」露台观景大床房", room_type="大床房",
             price=728, original_price=828, capacity=2,
             description="1.8米大床，私享露台+网红观景浴缸。泡澡观云，出片率最高的浪漫之选。",
             bed_type="1.8m大床", area="32m²",
             amenities=["私享露台", "网红浴缸", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "迷你吧"],
             view_type="山景", total_count=1, sort_order=10),
        # 11. 纪雅 — 观景双床房（落地窗.KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「纪雅」观景双床房", room_type="双床房",
             price=528, original_price=628, capacity=2,
             description="两张1.2米单人床，全景落地窗+KingKoll床垫+TOTO卫浴。窗边即景。",
             bed_type="2×1.2m单人床", area="25m²",
             amenities=["全景落地窗", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi"],
             view_type="山景", total_count=2, sort_order=11),
        # 12. 云上 — 山景套房（270°全景.景观露台.观景浴缸）
        Room(bnb_id="shanji", name="「云上」山景套房", room_type="套房",
             price=1088, original_price=1288, capacity=2,
             description="1.8米大床，270°全景落地窗+景观露台+观景浴缸。躺床上环视庐山云雾。",
             bed_type="1.8m大床", area="45m²",
             amenities=["270°全景窗", "景观露台", "观景浴缸", "地暖", "智能马桶", "加热毛巾架", "KingKoll床垫", "高速WiFi", "迷你吧"],
             view_type="270°环山全景", total_count=1, sort_order=12),
        # 13. 纪岚 — 景观双床房（阳台.KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「纪岚」景观双床房", room_type="双床房",
             price=488, original_price=588, capacity=2,
             description="两张1.2米单人床，独立阳台+KingKoll床垫+TOTO卫浴。阳台小憩，尽览山景。",
             bed_type="2×1.2m单人床", area="22m²",
             amenities=["独立阳台", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "书桌"],
             view_type="山景", total_count=1, sort_order=13),
        # 14. 纪雪 — 温馨双床房（KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「纪雪」温馨双床房", room_type="双床房",
             price=388, original_price=488, capacity=2,
             description="两张1.2米单人床，KingKoll床垫+TOTO卫浴。温馨实用，结伴首选。",
             bed_type="2×1.2m单人床", area="18m²",
             amenities=["观景窗", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi"],
             view_type="山景", total_count=3, sort_order=14),
        # 15. 安云 — 舒适双床房（KingKoll床垫.品牌卫浴）
        Room(bnb_id="shanji", name="「安云」舒适双床房", room_type="双床房",
             price=428, original_price=528, capacity=2,
             description="两张1.2米单人床，KingKoll床垫+品牌卫浴。宽敞舒适，实用之选。",
             bed_type="2×1.2m单人床", area="20m²",
             amenities=["观景窗", "地暖", "KingKoll床垫", "品牌卫浴", "高速WiFi", "书桌"],
             view_type="山景", total_count=2, sort_order=15),
        # 16. 山隐 — LOFT双床房（阳台.KingKoll床垫.TOTO卫浴）
        Room(bnb_id="shanji", name="「山隐」LOFT双床房", room_type="LOFT",
             price=788, original_price=888, capacity=4,
             description="两张大床，双层LOFT格局+阳台+KingKoll床垫+TOTO卫浴。宽敞复式空间。",
             bed_type="2×1.8m大床", area="40m²",
             amenities=["双层LOFT", "独立阳台", "地暖", "KingKoll床垫", "TOTO卫浴", "高速WiFi", "迷你吧"],
             view_type="山景", total_count=2, sort_order=16),
    ]
    for r in rooms:
        r.images = _shanji_room_imgs(r.sort_order)
    db.add_all(rooms)
    info("   山纪 16种房型 已填充（独立图片库）")


def _seed_donglinwai_rooms(db):
    """东林外客房 — 携程官方数据（2026.6），26间8种房型"""
    rooms = [
        Room(bnb_id="donglinwai", name="知寂·花涧双床房", room_type="双床房",
             price=388, original_price=488, capacity=2,
             description="两张1.2米单人床，庭院景观，零压床垫。推窗见花，静谧禅意。",
             bed_type="2×1.2m单人床", area="20m²",
             amenities=["庭院景观", "零压床垫", "地暖", "高速WiFi", "书桌", "禅修坐垫"],
             view_type="庭院", total_count=4, sort_order=1),
        Room(bnb_id="donglinwai", name="空屿·如愿大床房", room_type="大床房",
             price=428, original_price=528, capacity=2,
             description="1.8米大床，山景氧吧，舒睡床品。面向青山，吐纳自然。",
             bed_type="1.8m大床", area="22m²",
             amenities=["山景窗", "舒睡床品", "地暖", "高速WiFi", "书桌", "禅修坐垫"],
             view_type="山景", total_count=3, sort_order=2),
        Room(bnb_id="donglinwai", name="归宁·愈己大床房", room_type="大床房",
             price=488, original_price=588, capacity=2,
             description="1.8米大床，山景氧吧，舒睡床品。放下尘嚣，归来自在。入住即享疗愈体验。",
             bed_type="1.8m大床", area="25m²",
             amenities=["山景窗", "舒睡床品", "地暖", "高速WiFi", "浴缸", "茶具套装", "疗愈体验"],
             view_type="山景", total_count=4, sort_order=3),
        Room(bnb_id="donglinwai", name="观息·庭院观景套房", room_type="套房",
             price=688, original_price=788, capacity=2,
             description="1.8米大床，全景落地窗+会客空间。独享庭院，观息观心。",
             bed_type="1.8m大床", area="35m²",
             amenities=["全景落地窗", "会客空间", "独立庭院", "地暖", "智能马桶", "浴缸", "高速WiFi", "茶具套装"],
             view_type="庭院山景", total_count=1, sort_order=4),
        Room(bnb_id="donglinwai", name="逐雾·山景Loft复式套房", room_type="LOFT套房",
             price=788, original_price=888, capacity=2,
             description="1.8米大床，独享花园庭院+全景落地窗。双层空间，晨起逐雾，夜观星辰。",
             bed_type="1.8m大床", area="40m²",
             amenities=["双层LOFT", "花园庭院", "全景落地窗", "地暖", "智能马桶", "浴缸", "高速WiFi", "迷你吧"],
             view_type="庭院全景", total_count=3, sort_order=5),
        Room(bnb_id="donglinwai", name="云上·东林下复式楼", room_type="复式楼",
             price=888, original_price=988, capacity=2,
             description="1.8米大床，舒睡床品，全景落地窗。东林寺钟声可闻，独立复式小楼。",
             bed_type="1.8m大床", area="45m²",
             amenities=["独栋复式", "全景落地窗", "舒睡床品", "地暖", "智能马桶", "浴缸", "高速WiFi", "迷你吧", "茶室"],
             view_type="山景/寺景", total_count=2, sort_order=6),
    ]
    for r in rooms:
        r.images = _donglinwai_room_imgs(r.sort_order)
    db.add_all(rooms)
    info("   东林外 6种房型(20间) 已填充（独立图片库）")


def seed_menu(db, bnb_id="guishu"):
    """菜单数据 — 按民宿区分"""
    if bnb_id == "shanji":
        _seed_shanji_menu(db)
        return
    if bnb_id == "donglinwai":
        _seed_donglinwai_menu(db)
        return

    # ── 归墅 (guishu) — 三山二水咖啡 真实菜单 ──
    categories = [
        MenuCategory(name="咖啡+茶饮", icon="☕", sort_order=1),
        MenuCategory(name="简餐", icon="🍝", sort_order=2),
        MenuCategory(name="甜品", icon="🍰", sort_order=3),
        MenuCategory(name="特调饮品", icon="🍹", sort_order=4),
    ]
    db.add_all(categories)
    db.flush()

    c0, c1, c2, c3 = categories[0].id, categories[1].id, categories[2].id, categories[3].id
    items = [
        # 咖啡+茶饮
        MenuItem(category_id=c0, name="美式", price=26, description="经典美式咖啡，纯粹醇香", sort_order=1),
        MenuItem(category_id=c0, name="椰青美式", price=32, description="清甜椰青水配浓缩咖啡，清爽回甘", sort_order=2),
        MenuItem(category_id=c0, name="Dirty", price=38, description="热浓缩碰撞冰牛奶，层次分明", is_recommended=True, sort_order=3),
        MenuItem(category_id=c0, name="拿铁", price=36, description="经典意式拿铁，奶香丝滑", sort_order=4),
        MenuItem(category_id=c0, name="燕麦拿铁", price=38, description="燕麦奶配浓缩咖啡，谷物醇香", sort_order=5),
        MenuItem(category_id=c0, name="生椰拿铁", price=36, description="生椰乳配浓缩咖啡，热带风味", sort_order=6),
        MenuItem(category_id=c0, name="奥利奥拿铁", price=38, description="奥利奥碎融入拿铁，甜蜜酥脆", sort_order=7),
        MenuItem(category_id=c0, name="摩卡", price=38, description="巧克力酱配浓缩咖啡，醇厚甜蜜", sort_order=8),
        MenuItem(category_id=c0, name="抹茶拿铁（无咖啡）", price=28, description="日式抹茶配牛乳，清新无咖啡因", sort_order=9),
        MenuItem(category_id=c0, name="椰子水", price=28, description="天然椰子水，清凉解渴", sort_order=10),
        MenuItem(category_id=c0, name="可可奶", price=20, description="浓郁可可配鲜牛奶，暖胃甜蜜", sort_order=11),
        MenuItem(category_id=c0, name="庐山云雾茶（红/绿）", price=38, description="杯/38元 · 壶/98元。明前高山云雾茶，红绿两色可选", is_recommended=True, sort_order=12),
        # 简餐
        MenuItem(category_id=c1, name="意面", price=42, description="手工意面配番茄肉酱，42元/份", sort_order=1),
        MenuItem(category_id=c1, name="小吃拼盘", price=48, description="多款小食组合拼盘，聚会必备", sort_order=2),
        MenuItem(category_id=c1, name="奥尔良鸡肉披萨", price=88, description="奥尔良风味鸡肉披萨，现烤出炉", is_recommended=True, sort_order=3),
        MenuItem(category_id=c1, name="榴莲美式披萨", price=108, description="猫山王榴莲果肉配美式芝士披萨", is_recommended=True, sort_order=4),
        # 甜品
        MenuItem(category_id=c2, name="提拉米苏", price=26, description="经典意式提拉米苏，层层浓郁", is_recommended=True, sort_order=1),
        MenuItem(category_id=c2, name="豆乳蛋糕", price=26, description="浓郁豆乳酱配松软蛋糕，清甜不腻", sort_order=2),
        # 特调饮品
        MenuItem(category_id=c3, name="没事的", price=32, description="主理人特调，喝一杯，什么事都没有", is_recommended=True, sort_order=1),
    ]
    db.add_all(items)


def _seed_shanji_menu(db):
    """山纪菜单 — 咖啡书吧 + 云上茶吧 + 山货餐厅"""
    categories = [
        MenuCategory(bnb_id="shanji", name="咖啡+茶饮", icon="☕", sort_order=1),
        MenuCategory(bnb_id="shanji", name="山货简餐", icon="🍲", sort_order=2),
        MenuCategory(bnb_id="shanji", name="茶道体验", icon="🍵", sort_order=3),
    ]
    db.add_all(categories)
    db.flush()

    c0, c1, c2 = categories[0].id, categories[1].id, categories[2].id
    items = [
        MenuItem(bnb_id="shanji", category_id=c0, name="美式咖啡", price=26, description="经典美式，纯粹醇香", sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c0, name="拿铁", price=36, description="经典意式拿铁，奶香丝滑", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c0, name="生椰拿铁", price=36, description="生椰乳配浓缩咖啡，热带风味", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c0, name="庐山云雾茶(杯)", price=38, description="中国十大名茶，明前高山云雾，红绿两色可选", is_recommended=True, sort_order=4),
        MenuItem(bnb_id="shanji", category_id=c0, name="庐山云雾茶(壶)", price=98, description="整壶冲泡，2-3人品茗，配茶点", is_recommended=True, sort_order=5),
        MenuItem(bnb_id="shanji", category_id=c0, name="桂花云雾奶盖", price=32, description="云雾茶底+鲜奶奶盖+干桂花，山纪特调", sort_order=6),
        MenuItem(bnb_id="shanji", category_id=c1, name="庐山三石煲", price=88, description="石鸡+石鱼+石耳，庐山珍味一锅鲜", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c1, name="农家小炒肉套餐", price=42, description="本地土猪肉配时蔬，米饭+例汤", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c1, name="庐山石鱼蒸蛋", price=38, description="庐山特有石鱼干蒸土鸡蛋，鲜香嫩滑", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c1, name="山货炒饭", price=32, description="腊肉+笋干+香菇，山货满满", sort_order=4),
        MenuItem(bnb_id="shanji", category_id=c1, name="江西拌粉", price=22, description="地道江西米粉，住客早餐好评率最高", sort_order=5),
        MenuItem(bnb_id="shanji", category_id=c2, name="茶道品鉴体验", price=128, description="茶艺师一对一，品鉴三款云雾茶，60分钟", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c2, name="茶园采茶体验", price=168, description="前往山纪茶园亲手采茶+制茶，90分钟，含茶礼", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c2, name="茶点拼盘", price=48, description="庐山茶饼+桂花糕+核桃酥，配一壶茶", sort_order=3),
    ]
    db.add_all(items)
    info("   山纪 3类14款菜单 已填充")


def _seed_donglinwai_menu(db):
    """东林外菜单 — 仅饮品（精品咖啡 + 奶茶），无餐食"""
    categories = [
        MenuCategory(bnb_id="donglinwai", name="经典咖啡", icon="☕", sort_order=1),
        MenuCategory(bnb_id="donglinwai", name="风味拿铁", icon="🎨", sort_order=2),
        MenuCategory(bnb_id="donglinwai", name="创意特调", icon="✨", sort_order=3),
        MenuCategory(bnb_id="donglinwai", name="云上奶茶", icon="🧋", sort_order=4),
    ]
    db.add_all(categories)
    db.flush()

    c0, c1, c2, c3 = categories[0].id, categories[1].id, categories[2].id, categories[3].id
    items = [
        # ── 经典咖啡 ──
        MenuItem(bnb_id="donglinwai", category_id=c0, name="美式咖啡", price=18, description="热/冰可选，经典醇苦", sort_order=1),
        MenuItem(bnb_id="donglinwai", category_id=c0, name="拿铁咖啡", price=24, description="热/冰可选，奶香丝滑", is_recommended=True, sort_order=2),
        MenuItem(bnb_id="donglinwai", category_id=c0, name="Dirty", price=26, description="冰，浓缩碰撞冰牛奶，层次分明", sort_order=3),
        MenuItem(bnb_id="donglinwai", category_id=c0, name="卡布奇诺", price=26, description="热，绵密奶泡，经典之选", sort_order=4),
        # ── 风味拿铁 ──
        MenuItem(bnb_id="donglinwai", category_id=c1, name="抹茶拿铁", price=26, description="热，日式抹茶融合牛乳", sort_order=1),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="榛果拿铁", price=28, description="热/冰可选，坚果香甜", sort_order=2),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="香草拿铁", price=28, description="热/冰可选，经典香草风味", sort_order=3),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="焦糖拿铁", price=28, description="热/冰可选，焦糖浓郁", sort_order=4),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="燕麦拿铁", price=28, description="热/冰可选，植物基燕麦奶", sort_order=5),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="生椰拿铁", price=28, description="冰，椰乳清甜碰撞浓缩", is_recommended=True, sort_order=6),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="廖卡", price=32, description="热/冰可选，巧克力与咖啡的融合", sort_order=7),
        MenuItem(bnb_id="donglinwai", category_id=c1, name="焦糖玛奇朵", price=32, description="热/冰可选，焦糖奶香层层交织", sort_order=8),
        # ── 创意特调 ──
        MenuItem(bnb_id="donglinwai", category_id=c2, name="椰青冰美式", price=22, description="冰，清甜椰子水+美式，夏日必点", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="杨梅冰美式", price=26, description="冰，杨梅果香+美式，酸甜清爽", sort_order=2),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="荔枝冰咖", price=26, description="冰，荔枝甘甜+冷萃，果香四溢", sort_order=3),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="卡美罗拿铁", price=28, description="热，韩式蜂窝糖饼融入拿铁", sort_order=4),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="焦糖肉桂拿铁", price=28, description="热，肉桂暖香+焦糖，秋冬治愈", sort_order=5),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="黄油啤酒拿铁", price=28, description="热，哈利波特同款灵感，奶盖绵密", sort_order=6),
        MenuItem(bnb_id="donglinwai", category_id=c2, name="苹果肉桂拿铁", price=28, description="热，苹果清甜+肉桂暖意", sort_order=7),
        # ── 云上奶茶 ──
        MenuItem(bnb_id="donglinwai", category_id=c3, name="云上香草奶茶", price=16, description="热，香草慢煮，暖胃暖心", sort_order=1),
        MenuItem(bnb_id="donglinwai", category_id=c3, name="云上焦糖奶茶", price=16, description="热，焦糖慢煮，甜而不腻", sort_order=2),
        MenuItem(bnb_id="donglinwai", category_id=c3, name="云上榛果奶茶", price=16, description="热，榛果慢煮，坚果奶香", sort_order=3),
    ]
    db.add_all(items)
    info("   东林外 4类22款饮品 已填充")


def seed_services(db, bnb_id="guishu"):
    """快捷服务数据 — 按民宿区分"""
    if bnb_id == "shanji":
        _seed_shanji_services(db)
        return
    if bnb_id == "donglinwai":
        _seed_donglinwai_services(db)
        return

    # ── 归墅 (guishu) ──
    services = [
        QuickService(name="续住办理", description="延长入住时间，无需换房", icon="🔑", category="housekeeping", estimated_time="即刻办理", sort_order=1),
        QuickService(name="房间打扫", description="全面清洁房间，更换床品毛巾", icon="🧹", category="housekeeping", estimated_time="约30分钟", sort_order=2),
        QuickService(name="补充用品", description="补充洗漱用品、茶包、矿泉水等", icon="🧴", category="housekeeping", estimated_time="约10分钟", sort_order=3),
        QuickService(name="送餐到房", description="将餐点送至您的房间", icon="🍽️", category="housekeeping", estimated_time="约30分钟", sort_order=4),
        QuickService(name="衣物送洗", description="洗衣、烘干、熨烫服务", icon="👔", category="housekeeping", estimated_time="次日取", sort_order=5),

        # 前台服务 (sort_order 6-13) — 按用户指定顺序
        QuickService(name="行李寄存", description="退房后免费寄存行李", icon="🧳", category="frontdesk", estimated_time="即刻办理", sort_order=6),
        QuickService(name="旅游咨询", description="庐山景点介绍、门票预订、天气查询", icon="🏞️", category="frontdesk", estimated_time="即刻咨询", sort_order=7),
        QuickService(name="旅拍服务", description="专业摄影师跟拍，记录庐山美好时光。含服装造型指导、精修底片全送", icon="📸", category="frontdesk", estimated_time="约2-3小时", sort_order=8),
        QuickService(name="免费路线规划", description="老板根据您的偏好定制游玩路线，不收任何费用", icon="🗺️", category="frontdesk", estimated_time="即刻咨询", sort_order=9),
        QuickService(name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟到达", sort_order=10),
        QuickService(name="叫醒服务", description="设定叫醒时间，准时电话提醒", icon="⏰", category="frontdesk", estimated_time="准时执行", sort_order=11),
        QuickService(name="搭伙用餐", description="可与老板搭伙用餐，品尝家常庐山味道", icon="🍲", category="frontdesk", estimated_time="需提前联系", sort_order=12),
        QuickService(name="退房办理", description="快速退房，账单结算", icon="🏃", category="frontdesk", estimated_time="约5分钟", sort_order=13),

        # 前台服务 - 新增 (sort_order 14-18)
        QuickService(name="登山杖免费租借", description="押金¥50，归还退押金。住客点赞率最高的贴心服务", icon="🥾", category="frontdesk", estimated_time="即刻领取", sort_order=14),
        QuickService(name="雨伞/雨衣租借", description="庐山多雨，免费借用雨伞或一次性雨衣，退房归还即可", icon="🌂", category="frontdesk", estimated_time="即刻领取", sort_order=15),
        QuickService(name="充电宝租借", description="前台扫码借取，全山通用归还点，支持主流品牌", icon="🔋", category="frontdesk", estimated_time="即刻领取", sort_order=16),
        QuickService(name="医药箱/急救包", description="创可贴/晕车药/退烧药/藿香正气水/碘伏棉签等常用药品", icon="💊", category="frontdesk", estimated_time="即刻取用", sort_order=17),
        QuickService(name="特产代购", description="庐山茶饼/石鱼干/云雾茶等特产，按进价代购不加价", icon="🎁", category="frontdesk", estimated_time="次日可取", sort_order=18),

        # 设施维修 (sort_order 19-21)
        QuickService(name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=19),
        QuickService(name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=20),
        QuickService(name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=21),
    ]
    db.add_all(services)


def _seed_shanji_services(db):
    """山纪快捷服务 — 管家式服务为主"""
    services = [
        QuickService(bnb_id="shanji", name="续住办理", description="延长入住时间，无需换房", icon="🔑", category="frontdesk", estimated_time="即刻办理", sort_order=1),
        QuickService(bnb_id="shanji", name="房间打扫", description="全面清洁房间，更换床品毛巾", icon="🧹", category="housekeeping", estimated_time="约30分钟", sort_order=2),
        QuickService(bnb_id="shanji", name="补充用品", description="补充洗漱用品、茶包、矿泉水等", icon="🧴", category="housekeeping", estimated_time="约10分钟", sort_order=3),
        QuickService(bnb_id="shanji", name="接送服务", description="庐山索道站/观光车站免费接送（步行3分钟即达也可选择接送）", icon="🚗", category="frontdesk", estimated_time="即刻出发", sort_order=4),
        QuickService(bnb_id="shanji", name="行李寄存", description="退房后免费寄存行李", icon="🧳", category="frontdesk", estimated_time="即刻办理", sort_order=5),
        QuickService(bnb_id="shanji", name="旅游咨询", description="庐山景点介绍、门票预订、天气查询", icon="🏞️", category="frontdesk", estimated_time="即刻咨询", sort_order=6),
        QuickService(bnb_id="shanji", name="免费路线规划", description="管家根据您的偏好定制游玩路线，不收任何费用", icon="🗺️", category="frontdesk", estimated_time="即刻咨询", sort_order=7),
        QuickService(bnb_id="shanji", name="旅拍服务", description="云端光影·山纪臻享艺术旅拍体验，含45分钟专属拍摄", icon="📸", category="frontdesk", estimated_time="约45分钟", sort_order=8),
        QuickService(bnb_id="shanji", name="茶道体验预约", description="茶园采茶/制茶/茶道品鉴体验预约", icon="🍵", category="frontdesk", estimated_time="即刻预约", sort_order=9),
        QuickService(bnb_id="shanji", name="手工课程预约", description="陶瓷文化体验、手工课程预约", icon="🎨", category="frontdesk", estimated_time="即刻预约", sort_order=10),
        QuickService(bnb_id="shanji", name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟", sort_order=11),
        QuickService(bnb_id="shanji", name="叫醒服务", description="设定叫醒时间，准时电话提醒", icon="⏰", category="frontdesk", estimated_time="准时执行", sort_order=12),
        QuickService(bnb_id="shanji", name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=13),
        QuickService(bnb_id="shanji", name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=14),
        QuickService(bnb_id="shanji", name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=15),
    ]
    db.add_all(services)
    info("   山纪 15项快捷服务 已填充")


def _seed_donglinwai_services(db):
    """东林外快捷服务 — 疗愈+禅修特色"""
    services = [
        QuickService(bnb_id="donglinwai", name="续住办理", description="延长入住时间，无需换房", icon="🔑", category="frontdesk", estimated_time="即刻办理", sort_order=1),
        QuickService(bnb_id="donglinwai", name="房间打扫", description="全面清洁房间，更换床品毛巾", icon="🧹", category="housekeeping", estimated_time="约30分钟", sort_order=2),
        QuickService(bnb_id="donglinwai", name="补充用品", description="补充洗漱用品、茶包、矿泉水等", icon="🧴", category="housekeeping", estimated_time="约10分钟", sort_order=3),
        QuickService(bnb_id="donglinwai", name="免费洗衣服务", description="免费洗衣、烘干，住客专享", icon="👔", category="housekeeping", estimated_time="次日取", sort_order=4),
        QuickService(bnb_id="donglinwai", name="接送服务", description="东林寺/庐山索道接送", icon="🚗", category="frontdesk", estimated_time="即刻出发", sort_order=5),
        QuickService(bnb_id="donglinwai", name="行李寄存", description="退房后免费寄存行李", icon="🧳", category="frontdesk", estimated_time="即刻办理", sort_order=6),
        QuickService(bnb_id="donglinwai", name="疗愈体验预约", description="铜锣沐心/禅拍律动/五音涤尘/观山饮露桩 预约", icon="🧘", category="frontdesk", estimated_time="即刻预约", sort_order=7),
        QuickService(bnb_id="donglinwai", name="精力管理营咨询", description="专属疗愈师定制3日精力管理营", icon="📋", category="frontdesk", estimated_time="即刻咨询", sort_order=8),
        QuickService(bnb_id="donglinwai", name="晨钟暮课引导", description="指引参与东林寺早晚课（步行3分钟），可选随喜", icon="🛎️", category="frontdesk", estimated_time="即刻指引", sort_order=9),
        QuickService(bnb_id="donglinwai", name="宠物托管", description="外出期间可协助照看宠物（民宿可携宠入住）", icon="🐱", category="frontdesk", estimated_time="即刻安排", sort_order=10),
        QuickService(bnb_id="donglinwai", name="旅游咨询", description="东林寺/西林寺/庐山索道周边景点介绍", icon="🏞️", category="frontdesk", estimated_time="即刻咨询", sort_order=11),
        QuickService(bnb_id="donglinwai", name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟", sort_order=12),
        QuickService(bnb_id="donglinwai", name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=13),
        QuickService(bnb_id="donglinwai", name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=14),
        QuickService(bnb_id="donglinwai", name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=15),
    ]
    db.add_all(services)
    info("   东林外 15项快捷服务 已填充")


def seed_travel_routes(db, bnb_id="guishu"):
    """旅游路线数据 — 按民宿区分"""
    if bnb_id == "shanji":
        _seed_common_shanji_routes(db)
        return
    if bnb_id == "donglinwai":
        _seed_donglinwai_routes(db)
        return

    # ── 归墅 (guishu) ──
    routes = [
        TravelRoute(
            name="一日游：庐山精华线（西线+中线）",
            description="适合一日游的特种兵路线。上午走西线自然风光（如琴湖/花径/锦绣谷/仙人洞），下午走中线人文景观（美庐/会议旧址/芦林湖），节奏紧凑但不会太累。",
            duration="1天（约6-7小时）",
            difficulty="easy",
            spots=[
                {"name": "如琴湖", "description": "湖形如小提琴，清晨湖面倒映山峦，出片圣地"},
                {"name": "花径", "description": "白居易「人间四月芳菲尽，山寺桃花始盛开」出处，花木扶疏"},
                {"name": "锦绣谷", "description": "庐山最精华的徒步路段！悬崖栈道、云雾缭绕，运气好能看到野生猕猴（勿投喂）"},
                {"name": "仙人洞", "description": "天然石洞，传说吕洞宾修炼之地"},
                {"name": "美庐别墅", "description": "宋美龄庐山避暑官邸，见证近代历史风云"},
                {"name": "庐山会议旧址+博物馆", "description": "了解庐山地质、文化、近代历史"},
                {"name": "芦林湖", "description": "蓝调湖景，傍晚光线最佳，拍照绝美"},
            ],
            tips="① 索道上山（10分钟）代替大巴（40分钟盘山路），防晕车！② 锦绣谷步道约3小时/15000步，穿运动鞋 ③ 观光车末班18:00，别错过 ④ 牯岭镇有1元公交覆盖主要景点 ⑤ 中午在牯岭街吃饭（推荐石牛酒家或847别墅）",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇起点",
            is_recommended=True,
            sort_order=1,
        ),
        TravelRoute(
            name="两日游：庐山全景深度（最推荐✨）",
            description="小红书上最受推荐的节奏！Day1西线+中线人文轻松游，Day2东线硬核自然景观。不赶不累，精华全涵盖。",
            duration="2天",
            difficulty="medium",
            spots=[
                {"name": "DAY1上午：如琴湖→花径→锦绣谷→仙人洞", "description": "西线经典徒步，全程约3小时。锦绣谷是云雾最佳观赏点，运气好能拍到云海"},
                {"name": "DAY1下午：美庐别墅→会议旧址→庐山博物馆→芦林湖", "description": "中线人文路线，轻松漫步。芦林湖傍晚蓝调时刻拍照绝美"},
                {"name": "DAY1晚上：牯岭街正街", "description": "逛正街、吃石牛酒家、喝见山茶/庐小仙。可选看《庐山恋》电影（30元）"},
                {"name": "DAY2清晨：含鄱口看日出", "description": "远眺鄱阳湖，雨后初晴云海几率最高。需早起，但值得！"},
                {"name": "DAY2上午：五老峰", "description": "一峰到五峰依次攀登（约2.5h），第四峰风景最美。体力有限者可爬到四峰折返"},
                {"name": "DAY2下午：三叠泉", "description": "「不到三叠泉，不算庐山客」2600+级台阶！三级瀑布飞流直下，震撼到说不出话。可乘小火车省一半体力"},
            ],
            tips="⚠️ 真实博主血泪经验：不要把五老峰和三叠泉连在一起一天走完！强度极大，很多人直接走崩溃。体力有限就二选一。必备登山杖！建议带防晒+薄外套（山上温差大）+雨衣。牯岭镇住一晚，推开窗可能就是云海～",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇起点",
            is_recommended=True,
            sort_order=2,
        ),
        TravelRoute(
            name="文化之旅：庐山人文寻踪",
            description="探访庐山深厚的文化底蕴。从千年书院到净土宗祖庭，从蒋宋官邸到近代会议旧址，感受庐山千年文脉。",
            duration="1天（可拆为两个半天）",
            difficulty="easy",
            spots=[
                {"name": "白鹿洞书院", "description": "中国四大书院之首，朱熹讲学之地。千年学府，古木参天"},
                {"name": "东林寺", "description": "净土宗祖庭，千年古刹。免费参观，寺内有素斋"},
                {"name": "东林大佛", "description": "世界最高阿弥陀佛铜像，需爬台阶约30分钟登顶。免费！"},
                {"name": "美庐别墅", "description": "蒋宋庐山避暑官邸，「美庐」二字为蒋介石亲笔题写"},
                {"name": "庐山会议旧址", "description": "近代中国重要历史见证地，内部陈列丰富"},
                {"name": "庐山博物馆", "description": "毛泽东庐山旧居，芦林湖畔。了解庐山地质变迁和文化脉络"},
            ],
            tips="白鹿洞书院和东林寺在山下，建议单独安排一天或包车串联。东林寺+东林大佛均免费。白鹿洞书院门票40元。庐山站打车到东林寺约25分钟。山上美庐、会议旧址、博物馆都在牯岭镇附近，步行可达，可安排半天轻松逛完。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇",
            sort_order=3,
        ),
        TravelRoute(
            name="徒步挑战：好汉坡穿越线",
            description="从好汉坡徒步登顶庐山，适合户外爱好者和徒步玩家。全程约15公里，是对体力和意志的双重考验。",
            duration="1天（约5-6小时徒步）",
            difficulty="hard",
            spots=[
                {"name": "好汉坡起点（莲花洞）", "description": "从莲花洞出发，开始登顶之旅。好汉坡以陡峭著称，名不虚传"},
                {"name": "半山亭", "description": "中途唯一休息点，可补水。到这里就完成了一半"},
                {"name": "牯岭镇终点", "description": "登顶后在牯岭镇庆祝！来一碗利民煨汤馆的瓦罐汤，配南昌拌粉，是对自己最好的奖励"},
            ],
            tips="① 需较好体能，新手慎选 ② 穿专业登山鞋，带足水（至少2L）和干粮 ③ 建议7:00前出发，避开正午烈日 ④ 雨天切勿尝试！石阶湿滑危险 ⑤ 登山杖必备 ⑥ 可选莲花洞→好汉坡→牯岭镇路线（经典方向），也可以反过来下山（对膝盖压力大）",
            map_link="https://uri.amap.com/marker?position=115.9500,29.5300&name=好汉坡起点莲花洞",
            sort_order=4,
        ),
        TravelRoute(
            name="休闲漫步：牯岭镇半日闲",
            description="不想太累？这个半日闲路线最适合你。在牯岭镇周边悠闲漫步，逛正街、品茶饮、看日落，感受山居慢生活。",
            duration="半天（约3-4小时）",
            difficulty="easy",
            spots=[
                {"name": "如琴湖环湖", "description": "绕湖一周约1小时，湖光山色尽收眼底。清晨或傍晚光线最佳"},
                {"name": "花径公园", "description": "白居易诗碑所在地，四季花木扶疏。免费开放"},
                {"name": "牯岭正街", "description": "逛小店、喝见山茶/庐小仙、买庐山茶饼伴手礼。正街上还有1元公交可以坐"},
                {"name": "街心公园", "description": "牯岭镇中心的小公园，傍晚坐在这里看山景发呆，超惬意"},
                {"name": "小天池看日落（可选）", "description": "从正街步行可达，日落时分金色阳光洒满山峦，手机也能拍出大片"},
            ],
            tips="非常适合到达当天或离开前半天的安排。不用赶景点，走哪算哪。正街上的庐山茶饼10元一盒（桂花味推荐），买回去送人很好。傍晚在街心公园的长椅上坐着看山，是庐山最好的打开方式。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇",
            sort_order=5,
        ),
    ]
    db.add_all(routes)


def _seed_common_shanji_routes(db):
    """山纪路线 — 与归墅共用牯岭街核心路线（山纪距索道仅3分钟步行）"""
    routes = [
        TravelRoute(
            bnb_id="shanji",
            name="一日游：庐山精华线（西线+中线）",
            description="从山纪出发步行3分钟即到索道和观光车站。上午走西线自然风光（如琴湖/花径/锦绣谷/仙人洞），下午走中线人文景观（美庐/会议旧址/芦林湖），节奏紧凑但不会太累。",
            duration="1天（约6-7小时）",
            difficulty="easy",
            spots=[
                {"name": "如琴湖", "description": "湖形如小提琴，清晨湖面倒映山峦，出片圣地"},
                {"name": "花径", "description": "白居易「人间四月芳菲尽，山寺桃花始盛开」出处"},
                {"name": "锦绣谷", "description": "庐山最精华的徒步路段！悬崖栈道、云雾缭绕"},
                {"name": "仙人洞", "description": "天然石洞，传说吕洞宾修炼之地"},
                {"name": "美庐别墅", "description": "宋美龄庐山避暑官邸，见证近代历史"},
                {"name": "庐山会议旧址+博物馆", "description": "了解庐山地质、文化、近代历史"},
                {"name": "芦林湖", "description": "蓝调湖景，傍晚光线最佳，拍照绝美"},
            ],
            tips="① 索道上山（10分钟）代替大巴（40分钟盘山路），山纪距索道仅步行3分钟！② 锦绣谷步道约3小时，穿运动鞋 ③ 观光车末班18:00 ④ 中午在牯岭街吃饭（步行8分钟即到）",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=云上山纪起点",
            is_recommended=True,
            sort_order=1,
        ),
        TravelRoute(
            bnb_id="shanji",
            name="两日游：庐山全景深度（最推荐✨）",
            description="Day1西线+中线人文轻松游，Day2东线硬核自然景观。不赶不累，精华全涵盖。回民宿后还能在山纪咖啡书吧喝茶看书。",
            duration="2天",
            difficulty="medium",
            spots=[
                {"name": "DAY1上午：如琴湖→花径→锦绣谷→仙人洞", "description": "西线经典徒步，全程约3小时"},
                {"name": "DAY1下午：美庐别墅→会议旧址→庐山博物馆→芦林湖", "description": "中线人文路线，轻松漫步"},
                {"name": "DAY1晚上：山纪庭院+咖啡书吧", "description": "回民宿享受300平花园庭院，在书吧点一杯拿铁看山景"},
                {"name": "DAY2清晨：含鄱口看日出", "description": "远眺鄱阳湖，雨后初晴云海几率最高"},
                {"name": "DAY2上午：五老峰", "description": "一峰到五峰依次攀登（约2.5h），第四峰风景最美"},
                {"name": "DAY2下午：三叠泉", "description": "2600+级台阶！三级瀑布飞流直下"},
            ],
            tips="⚠️ 不要把五老峰和三叠泉连在一起一天走完！体力有限就二选一。必备登山杖！山纪有登山杖可借～",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=云上山纪起点",
            is_recommended=True,
            sort_order=2,
        ),
        TravelRoute(
            bnb_id="shanji",
            name="文化之旅：庐山人文寻踪",
            description="探访庐山深厚的文化底蕴。从千年书院到净土宗祖庭，从蒋宋官邸到近代会议旧址。",
            duration="1天（可拆为两个半天）",
            difficulty="easy",
            spots=[
                {"name": "白鹿洞书院", "description": "中国四大书院之首，朱熹讲学之地"},
                {"name": "东林寺", "description": "净土宗祖庭，千年古刹。免费参观"},
                {"name": "东林大佛", "description": "世界最高阿弥陀佛铜像，免费！"},
                {"name": "美庐别墅", "description": "蒋宋庐山避暑官邸"},
                {"name": "庐山会议旧址", "description": "近代中国重要历史见证地"},
                {"name": "庐山博物馆", "description": "毛泽东庐山旧居，芦林湖畔"},
            ],
            tips="白鹿洞书院和东林寺在山下，建议单独安排一天。从山纪坐索道下山转车可达。山上美庐、会议旧址、博物馆都在牯岭镇附近，步行可达。",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=云上山纪起点",
            sort_order=3,
        ),
        TravelRoute(
            bnb_id="shanji",
            name="徒步挑战：好汉坡穿越线",
            description="从好汉坡徒步登顶庐山，适合户外爱好者。全程约15公里，对体力和意志的双重考验。",
            duration="1天（约5-6小时徒步）",
            difficulty="hard",
            spots=[
                {"name": "好汉坡起点（莲花洞）", "description": "开始登顶之旅。好汉坡以陡峭著称"},
                {"name": "半山亭", "description": "中途唯一休息点，可补水"},
                {"name": "牯岭镇终点", "description": "登顶后步行8分钟回山纪，泡一壶云雾茶犒劳自己"},
            ],
            tips="① 需较好体能，新手慎选 ② 穿专业登山鞋，带足水（至少2L）③ 雨天切勿尝试！④ 登山杖必备（山纪前台可借）",
            map_link="https://uri.amap.com/marker?position=115.9500,29.5300&name=好汉坡起点莲花洞",
            sort_order=4,
        ),
        TravelRoute(
            bnb_id="shanji",
            name="休闲漫步：山纪庭院+牯岭镇半日闲",
            description="不想太累？上午在山纪300平花园庭院喝茶发呆，下午去牯岭镇闲逛。咖啡书吧、正街小吃、街心公园看日落，感受山居慢生活。",
            duration="半天（约3-4小时）",
            difficulty="easy",
            spots=[
                {"name": "山纪花园庭院", "description": "300平户外庭院，喝咖啡看书，享受无人打扰的清晨"},
                {"name": "云上茶吧", "description": "品鉴庐山云雾茶，体验茶道文化"},
                {"name": "如琴湖环湖", "description": "绕湖一周约1小时，湖光山色尽收眼底"},
                {"name": "牯岭正街", "description": "逛小店、喝庐小仙、买庐山茶饼伴手礼"},
                {"name": "街心公园看日落", "description": "傍晚坐在这里看山景发呆"},
            ],
            tips="山纪提供茶道体验+手工课程，不出民宿也能享受充实的一天。正街步行8分钟，吃饭逛街超方便。",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=云上山纪起点",
            sort_order=5,
        ),
    ]
    db.add_all(routes)
    info("   山纪 5条旅游路线 已填充（基于归墅路线+山纪特色优化）")


def _seed_donglinwai_routes(db):
    """东林外路线 — 基于小红书真实攻略，以东林寺/西林寺/赛阳镇为核心"""
    routes = [
        TravelRoute(
            bnb_id="donglinwai",
            name="禅修半日：东林寺+西林寺深度游",
            description="从东林外步行3分钟到东林寺，再走5分钟到西林寺。千年古刹、银杏古树、晨钟暮鼓，不用赶路，慢慢感受。苏轼「横看成岭侧成峰」就题在西林寺壁上。",
            duration="半天（约3-4小时）",
            difficulty="easy",
            spots=[
                {"name": "东林寺", "description": "净土宗祖庭，免费参观。千年古刹，飞檐翘角在竹林中若隐若现。晨钟暮课可随喜参与"},
                {"name": "东林寺银杏（秋季）", "description": "寺内古银杏，秋季满树金黄，住客好评「东林寺正是银杏黄了，很漂亮」"},
                {"name": "西林寺", "description": "步行5分钟即到。苏轼《题西林壁》出处——「横看成岭侧成峰，远近高低各不同」"},
                {"name": "西林塔", "description": "唐代古塔，千年屹立。比东林寺更清静，适合静坐冥想"},
                {"name": "回到东林外", "description": "回来喝一杯手冲咖啡，或体验铜锣沐心/禅拍律动疗愈"},
            ],
            tips="① 东林寺+西林寺均免费 ② 建议清晨去，钟声+晨雾最有禅意 ③ 寺内有素斋可随喜 ④ 着宽松衣物，方便打坐 ⑤ 东林外提供晨钟暮课引导，管家会告诉你怎么走",
            map_link="https://uri.amap.com/marker?position=115.940758,29.595012&name=云上东林外起点",
            is_recommended=True,
            sort_order=1,
        ),
        TravelRoute(
            bnb_id="donglinwai",
            name="一日游：东林大佛朝圣+庐山索道上山",
            description="小红书1075赞攻略推荐！上午朝拜世界最高阿弥陀佛铜像（免费），下午乘索道上庐山游览。从信仰到山水，一日双境。",
            duration="1天",
            difficulty="medium",
            spots=[
                {"name": "上午：东林大佛", "description": "世界最高阿弥陀佛铜像，免费参观。需爬台阶约30分钟登顶，沿途有免费饮水站"},
                {"name": "中午：悦莲素食自助或大路王山庄", "description": "东林寺周边的素食/农家菜，补充体力"},
                {"name": "下午：庐山索道上山", "description": "从东林外驱车约15分钟到索道站，10分钟索道上山"},
                {"name": "下午：如琴湖+花径+锦绣谷", "description": "西线精华自然风光，锦绣谷云雾缭绕"},
                {"name": "傍晚：索道下山回东林外", "description": "回到民宿，享受疗愈体验（铜锣浴/禅拍）放松一天的疲惫"},
            ],
            tips="① 东林大佛免门票！自带水杯沿途有免费饮水 ② 大佛台阶较多，穿舒适鞋子 ③ 索道末班约18:00，注意时间 ④ 体力有限者大佛登顶后可乘观光车下山",
            map_link="https://uri.amap.com/marker?position=115.940758,29.595012&name=云上东林外起点",
            is_recommended=True,
            sort_order=2,
        ),
        TravelRoute(
            bnb_id="donglinwai",
            name="疗愈三日：东林外精力管理营",
            description="专属疗愈师定制三日行程。禅拍律动+铜锣沐心+五音涤尘+观山饮露桩+晨钟暮课，配合僧厨素斋，给身心做一次深度SPA。东林外住客专享。",
            duration="3天2晚",
            difficulty="easy",
            spots=[
                {"name": "DAY1：抵达·放下", "description": "下午入住→庭院茶席（欢迎茶）→傍晚东林寺漫步→晚间铜锣沐心（45分钟）→禅房安眠"},
                {"name": "DAY2：疗愈·归心", "description": "晨间观山饮露桩（30分钟）→僧厨素斋早餐→上午禅拍律动（60分钟）→午后五音涤尘（30分钟）→傍晚溪边茶席→晚间自由发呆/看书"},
                {"name": "DAY3：告别·带走", "description": "晨钟暮课随喜（东林寺早课）→素斋早餐→西林寺/赛阳镇田园漫步→退房→「离店时带不走的山水可打包成记忆」"},
            ],
            tips="① 需提前联系民宿预约疗愈师 ② 建议携带少量行李，多带些放空的勇气 ③ 允许发呆、赤脚走路、忘记手机密码 ④ 禅房内备有禅修坐垫和焚香器具",
            map_link="https://uri.amap.com/marker?position=115.940758,29.595012&name=云上东林外起点",
            is_recommended=True,
            sort_order=3,
        ),
    ]
    db.add_all(routes)
    info("   东林外 3条专属路线 已填充（小红书真实攻略）")


def seed_food_recommends(db, bnb_id="guishu"):
    """周边美食推荐 — 按民宿区分"""
    if bnb_id == "shanji":
        _seed_shanji_foods(db)
        return
    if bnb_id == "donglinwai":
        _seed_donglinwai_foods(db)
        return

    # ── 归墅 (guishu) ──
    foods = [
        # ── 餐厅 ────────────────────────────────────────
        FoodRecommend(
            name="石牛酒家",
            category="赣菜",
            description="牯岭街老牌苍蝇馆子，现炒现做有锅气。小红书1283赞攻略推荐，1450赞合集收录。环境一般但味道实在",
            address="牯岭镇庐山正街15-1号（街心花园马路对面）",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5570&name=石牛酒家",
            price_range="人均 ¥55-75",
            must_try="三杯鸡、土豆烧牛肉、黄豆烧皖鱼、野芹菜、石耳烧鸡",
            is_recommended=True,
            sort_order=1,
            tags=["#现炒有锅气", "#本地人推荐", "#高性价比", "#苍蝇馆子"],
            images=["/static/img/food/shiniu_01.jpg"],
            detail_content=(
                "\U0001f9a4 1283赞XHS博主“蒸龙虾”推荐：“现炒现做的，比较有锅气”！\n\n"
                "\U0001f4cd 就在正街街心花园对面，吃完下楼就是牯岭街。饭点会排队，不能网上取号。\n\n"
                "\U0001f357 **三杯鸡**（博主推荐）— 一点点辣很嫩很好吃，和香菇一起焖超下饭。\n\n"
                "\U0001f354 **土豆烧牛肉**— 软烂入味，土豆绵密。博主原话：“我浙江人，挺喜欢吃的”。\n\n"
                "\U0001f41f **黄豆烧皖鱼**— 鱼很嫩很新鲜，黄豆软糯入味，1450赞合集收录推荐。\n\n"
                "\U0001f33f **野芹菜** + **石耳烧鸡**— 庐山本地食材，山野鲜味。\n\n"
                "⚠️ **石鱼爆蛋慎点**— XHS多人反映太油太咸。\n\n"
                "\U0001f4dd 真实评价：“现炒的，有锅气，不像有些店用预制菜”；但也有避雷帖说“别来”。\n\n"
                "\U0001f4a1 两人吃150+。饭点人多要排队，建议错峰。介意环境的慎选——是烟火气小店不是精致餐厅。"
            ),
        ),
        FoodRecommend(
            name="847别墅餐厅",
            category="赣菜",
            description="百年别墅改造的江西菜馆。小红书1450赞合集列为“褒贬不一”——有人吃了三次还想吃，有人说一般般。服务公认好",
            address="牯岭镇窑洼路与慧远路交叉口东120米",
            map_link="https://uri.amap.com/marker?position=115.9795,29.5580&name=847别墅餐厅",
            price_range="人均 ¥60-70",
            must_try="土豆烧肉、红烧白鱼、菌菇汤、香煎豆腐、鸭/烧鸡（1450赞合集推荐）",
            is_recommended=True,
            sort_order=2,
            tags=["#百年别墅", "#服务满分", "#褒贬不一", "#真实推荐"],
            images=["/static/img/food/847_01.jpg"],
            detail_content=(
                "\U0001f3db️ 三天庐山行吃得最舒心的一餐！百年老别墅改造，复古氛围感拉满。\n\n"
                "\U0001f44d XHS博主“辣椒小姐”原话：“来庐山两次了，一共吃了三次这家餐厅，菜超级下饭！”\n\n"
                "\U0001f4cd 前台小姐姐和奶奶都特别和善，结账时提醒可以买券省钱，走的时候还送了茶饼！\n\n"
                "\U0001f969 **土豆烧肉**（招牌）— 现炖的，端上来还咕嘟咕嘟冒热气，肉酥烂土豆绵密。\n\n"
                "\U0001f41f **红烧白鱼**— 庐山本地白鱼，嫩、鲜、没土腥味。\n\n"
                "\U0001f344 **菌菇汤**— 味正鲜美，真材实料熬的。\n\n"
                "\U0001f4dd 1450赞XHS合集将其列为“褒贬不一”：价格偏贵，推荐鸭和烧鸡。也有4赞笔记说“一般般”。\n\n"
                "\U0001f4a1 综合评价：比网红营销店强太多，但不要期待“零差评”。服务是真的好。"
            ),
        ),
        FoodRecommend(
            name="望庐说·本地菜馆",
            category="赣菜",
            description="牯岭街网红餐厅，环境古色古香。口碑两极分化严重——338赞笔记说“一年了还在想念”，98赞笔记说“避雷”。服务态度公认好",
            address="牯岭镇合面街10号（建设银行对面）",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5568&name=望庐说",
            price_range="人均 ¥80-100",
            must_try="板栗烧鸡、外婆家粉皮、炝鸭血、干锅笋",
            is_recommended=True,
            sort_order=3,
            tags=["#网红餐厅", "#环境好", "#争议大", "#服务好"],
            images=["/static/img/food/wanglu_01.jpg"],
            detail_content=(
                "⚠️ 先说结论：这是一家评价两极分化的店，放在这里是让你自行判断的。\n\n"
                "\U0001f44d **好评方**（338赞XHS笔记“是谁一年了还在想念庐山的望庐说”）：\n"
                "  · “最最最不负众望的一顿！没有雷点！”\n"
                "  · 环境蓝白风格很清新，进门古色古香\n"
                "  · 板栗烧鸡超级下饭，鸡肉很嫩很香\n"
                "  · 1283赞博主：“服务态度非常好，快吃完会过来问有没有不满意”\n"
                "  · 份量大，可以在大众点评扫码排队\n\n"
                "\U0001f44e **差评方**（XHS多人反映）：\n"
                "  · 1450赞合集将其标注为“预制菜”\n"
                "  · 有食客吐槽“狠狠踩雷了”，凉皮粘在一起、栗子硬\n"
                "  · 多人反映“很咸很咸”，营销过度\n\n"
                "\U0001f4a1 建议：如果你追求环境好+拍照好看，可以一试。追求锅气和性价比→隔壁石牛酒家或847别墅。"
            ),
        ),
        FoodRecommend(
            name="庐人村·牯岭美食集",
            category="赣菜",
            description="二楼靠窗位可看山景拍照。1450赞XHS合集列为“褒贬不一”。云雾鸡用稻草荷叶裹烤是特色，一楼有特产和奶茶店",
            address="牯岭镇合面街1号（正街上）",
            map_link="https://uri.amap.com/marker?position=115.9803,29.5569&name=庐人村",
            price_range="人均 ¥80-100",
            must_try="云雾鸡（稻草荷叶裹烤）、老村长扣肉夹馍、炝鸭血",
            sort_order=4,
            tags=["#山景餐厅", "#拍照好看", "#褒贬不一", "#云雾鸡"],
            images=["/static/img/food/lurencun_01.jpg"],
            detail_content=(
                "\U0001f357 二楼靠窗位能看到山景，吃着饭拍张照，朋友圈赞爆！\n\n"
                "\U0001f425 **云雾鸡**（必点）— 用稻草和荷叶裹着烤，鸡肉嫩到脱骨。荷叶的清香渗进鸡肉里，跟普通烤鸡完全两个档次。\n\n"
                "\U0001f969 **老村长扣肉夹馍**— 扣肉肥而不腻，夹进热馍里，油香混着肉香，一口下去超满足。\n\n"
                "\U0001f986 **炝鸭血**— 嫩滑入味，辣度刚刚好。\n\n"
                "\U0001f4dd 真实评价：\n"
                "  · “最爱的是油麦菜，特别清甜”（没想到吧，素菜是亮点）\n"
                "  · “整体口味偏咸，腊肉烧笋的腊肉又干又硬”\n"
                "  · “笋还可以，挺下饭的”\n\n"
                "\U0001f4a1 一楼有当地特产和奶茶店，吃完可以顺便逛逛买伴手礼。属于“褒贬不一”梯队。"
            ),
        ),
        FoodRecommend(
            name="利民煨汤馆",
            category="小吃/煨汤",
            description="大众点评4.0星、9186条评论的苍蝇馆子！1450赞XHS合集收录。瓦罐炭火慢煨，价格亲民环境一般，是最暖胃的存在",
            address="牯岭镇正街中段",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5572&name=利民煨汤馆",
            price_range="人均 ¥26-45",
            must_try="茶树菇排骨汤、山药土鸡汤、石鱼炒蛋、南昌拌粉",
            is_recommended=True,
            sort_order=5,
            tags=["#大众点评9186评", "#瓦罐煨汤", "#性价比之王", "#苍蝇馆子"],
            images=["/static/img/food/limin_01.jpg"],
            detail_content=(
                "\U0001f372 庐山爬山累了，来一碗瓦罐煨汤简直续命！大众点评9186条评论、4.0星。\n\n"
                "\U0001f525 瓦罐埋在炭火里慢煨，从早煨到晚，汤色浓白，鲜到掉眉毛。\n\n"
                "\U0001f356 **茶树菇排骨汤**（招牌）— 茶树菇的清香和排骨的肉香完美融合，汤面浮着薄薄一层油花，喝完整个人都暖了。\n\n"
                "\U0001f425 **山药土鸡汤**— 土鸡+铁棍山药，煨到山药化在汤里，浓稠鲜甜。爬山下来来一碗，瞬间回血。\n\n"
                "\U0001f373 **石鱼炒蛋**— 庐山石鱼+土鸡蛋，石鱼鲜香酥脆，比普通炒蛋好吃十倍！\n\n"
                "\U0001f35c **南昌拌粉**— 江西招牌！粉Q弹，拌上萝卜干花生辣椒油，一碗才十块出头。\n\n"
                "\U0001f4a1 人均三四十，是牯岭街最暖胃的存在。1450赞合集将其与“璐姑娘”并列推荐（石鸡、土豆好吃）。建议爬山前来一碗补充体力～"
            ),
        ),
        FoodRecommend(
            name="庐山茶饼·伴手礼",
            category="伴手礼/小吃",
            description="庐山特产茶饼，桂花味最受欢迎。363赞XHS笔记“好吃的嘞”，2518赞合集收录。酥脆香甜10元一盒，送人自吃两相宜",
            address="牯岭镇正街多家店铺有售",
            map_link="",
            price_range="约 ¥10/盒",
            must_try="桂花茶饼、云雾茶饼、九江糍粑",
            sort_order=6,
            tags=["#伴手礼", "#桂花味", "#10元一盒", "#XHS爆款"],
            images=["/static/img/food/chabing_01.jpg"],
            detail_content=(
                "\U0001f36a 来庐山必带的伴手礼！正街上很多店都有卖，363赞XHS博主说“好吃的嘞”。\n\n"
                "\U0001f338 **桂花茶饼**— 用云雾茶汁和面，撒上桂花，酥脆中带着淡淡茶香和桂花甜。掰开层次分明，配茶一绝。\n\n"
                "\U0001f375 **云雾茶饼**— 茶味更浓，喜欢茶香的首选这个。\n\n"
                "\U0001f361 **九江糍粑**— 软糯拉丝，裹上芝麻花生粉，香甜不腻。\n\n"
                "\U0001f4b0 10元一盒，买5送1，买10送3。建议多买几盒回去送同事朋友。\n\n"
                "\U0001f4a1 正街上的价格都差不多，没必要特意比价。别在景区门口买，比镇上贵一倍。"
            ),
        ),
        # ── 特色饮品店 ────────────────────────────────
        FoodRecommend(
            name="庐小仙",
            category="茶饮",
            description="庐山高山上的鲜果茶饮！120赞XHS笔记推荐“必喝这家”。桃香云雾茶是招牌，史努比联名杯超可爱，小红书热门打卡店",
            address="牯岭镇合面街（二楼可用餐）",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5570&name=庐小仙",
            price_range="人均 ¥18-28",
            must_try="桃香云雾茶、庐小仙奶茶（史努比杯）、草莓云雾鲜果茶",
            is_recommended=True,
            sort_order=7,
            tags=["#庐山限定", "#鲜果茶", "#史努比联名", "#XHS爆款", "#必打卡"],
            images=["/static/img/food/luxiaoxian_01.jpg"],
            detail_content=(
                "\U0001f351 “赏庐山烟云美景，喝庐小仙茶饮”——120赞XHS博主“严蝎蝎”推荐：“好多朋友推荐必喝这家奶茶！”\n\n"
                "开在合面街，楼下买茶、楼上可以用餐。\n\n"
                "\U0001f351 **桃香云雾茶**（招牌必喝）— 用庐山云雾茶做茶底，加鲜桃果肉。茶香清高、桃香甜美，喝完嘴里还有淡淡回甘。\n\n"
                "\U0001f9cb **庐小仙奶茶**— 史努比联名杯子超可爱！配料有红豆+仙草，料多到像在喝粥。杯子拿到手上拍照，朋友圈都在问在哪买的。\n\n"
                "\U0001f353 **草莓云雾鲜果茶**— 季节限定！新鲜草莓+云雾绿茶，酸酸甜甜超解暑。\n\n"
                "⚠️ **注意区分**：庐小鲜≠庐小仙！XHS多人避雷的是“庐小鲜”（贵且难吃），庐小仙是合面街上的鲜果茶店，别搞混了。\n\n"
                "\U0001f4f8 拿着史努比杯子站在合面街拍照，背景是庐山街景，氛围感拉满～\n\n"
                "\U0001f4a1 旺季排队15-20分钟，建议错峰来。价格小贵但值得，毕竟“庐山限定”～"
            ),
        ),
        FoodRecommend(
            name="见山茶",
            category="茶饮",
            description="庐山本土新式茶饮品牌。1283赞XHS博主说“和霸王茶姬差不多”，274赞笔记说“很普通建议喝雪盖顶”。门头是网红打卡地标，适合拍照发圈",
            address="牯岭镇牯岭正街88号（正街中段）",
            map_link="https://uri.amap.com/marker?position=115.9802,29.5570&name=见山茶",
            price_range="人均 ¥18-32",
            must_try="云雾茉莉鲜奶茶、雪顶云雾奶茶、见山柠檬茶、桂花云雾奶盖",
            is_recommended=True,
            sort_order=8,
            tags=["#庐山限定", "#拍照打卡", "#争议口味", "#中式美学"],
            images=["/static/img/food/jianshan_01.webp"],
            detail_content=(
                "\U0001f343 庐山本土最火的新式茶饮品牌！门头是石质纹理墙面+大写的“见山”二字，已经成了牯岭街新地标。\n\n"
                "\U0001f4ca 真实口碑（来自多篇XHS笔记交叉验证）：\n"
                "  · 1283赞博主“蒸龙虾”：“和霸王茶姬差不多，拍照打卡可以买来拍拍照”\n"
                "  · 274赞笔记“庐山那些风很大的店”：“很普通的味道…建议喝有雪盖顶的”\n"
                "  · 142赞测评笔记认为书院龙井系列不错\n"
                "  · 也有大量避雷帖说“太难喝了”、“遍地都是广告”\n\n"
                "\U0001f375 **云雾茉莉鲜奶茶**（销量冠军）— 庐山云雾绿茶底+鲜牛乳+茉莉花瓣。喝到杯底能看到真正的茶叶。\n\n"
                "\U0001f3d4️ **雪顶云雾奶茶**— 奶盖绵密得像云朵，撒上抹茶粉做出庐山山峦造型。\n\n"
                "\U0001f34b **见山柠檬茶**— 暴打香水柠檬+云雾茶汤，酸爽解暑。\n\n"
                "\U0001f4f8 店内“见山”二字背景墙+庐山诗句灯箱，随手拍都出片。\n\n"
                "\U0001f4a1 旺季排队30分钟起。客观说：拍照好看，口味普通——调节期望再去，反而有惊喜。"
            ),
        ),
    ]
    db.add_all(foods)


def _seed_shanji_foods(db):
    """山纪美食 — 与归墅共享牯岭街全部8家推荐（步行8分钟即到）"""
    foods = [
        FoodRecommend(bnb_id="shanji", name="石牛酒家", category="赣菜",
            description="牯岭街老牌苍蝇馆子，现炒现做有锅气。从山纪步行8分钟即到", address="牯岭镇庐山正街15-1号",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5570&name=石牛酒家",
            price_range="人均 ¥55-75", must_try="三杯鸡、土豆烧牛肉、黄豆烧皖鱼、石耳烧鸡",
            images=["/static/img/food/shiniu_01.jpg"], is_recommended=True, sort_order=1),
        FoodRecommend(bnb_id="shanji", name="847别墅餐厅", category="赣菜",
            description="百年别墅改造的江西菜馆。土豆烧肉端上来还咕嘟冒热气，服务公认好",
            address="牯岭镇窑洼路与慧远路交叉口东120米",
            map_link="https://uri.amap.com/marker?position=115.9795,29.5580&name=847别墅餐厅",
            price_range="人均 ¥60-70", must_try="土豆烧肉、红烧白鱼、菌菇汤",
            images=["/static/img/food/847_01.jpg"], is_recommended=True, sort_order=2),
        FoodRecommend(bnb_id="shanji", name="望庐说·本地菜馆", category="赣菜",
            description="网红餐厅，环境古色古香。板栗烧鸡是招牌，服务态度公认好",
            address="牯岭镇合面街10号", map_link="https://uri.amap.com/marker?position=115.9800,29.5568&name=望庐说",
            price_range="人均 ¥80-100", must_try="板栗烧鸡、外婆家粉皮、炝鸭血",
            images=["/static/img/food/wanglu_01.jpg"], sort_order=3),
        FoodRecommend(bnb_id="shanji", name="庐人村·牯岭美食集", category="赣菜",
            description="二楼靠窗位看山景。云雾鸡稻草荷叶裹烤，一楼有特产奶茶",
            address="牯岭镇合面街1号", map_link="https://uri.amap.com/marker?position=115.9803,29.5569&name=庐人村",
            price_range="人均 ¥80-100", must_try="云雾鸡、老村长扣肉夹馍",
            images=["/static/img/food/lurencun_01.jpg"], sort_order=4),
        FoodRecommend(bnb_id="shanji", name="利民煨汤馆", category="小吃/煨汤",
            description="瓦罐炭火慢煨，价格亲民。爬山回来喝一碗续命", address="牯岭镇正街中段",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5572&name=利民煨汤馆",
            price_range="人均 ¥26-45", must_try="茶树菇排骨汤、山药土鸡汤、南昌拌粉",
            images=["/static/img/food/limin_01.jpg"], is_recommended=True, sort_order=5),
        FoodRecommend(bnb_id="shanji", name="庐山茶饼·伴手礼", category="伴手礼/小吃",
            description="桂花茶饼10元一盒，送人自吃两相宜", address="牯岭镇正街多家店铺有售",
            price_range="约 ¥10/盒", must_try="桂花茶饼、云雾茶饼、九江糍粑",
            images=["/static/img/food/chabing_01.jpg"], sort_order=6),
        FoodRecommend(bnb_id="shanji", name="庐小仙", category="茶饮",
            description="庐山鲜果茶饮！桃香云雾茶+史努比联名杯，必打卡", address="牯岭镇合面街",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5570&name=庐小仙",
            price_range="人均 ¥18-28", must_try="桃香云雾茶、庐小仙奶茶（史努比杯）",
            images=["/static/img/food/luxiaoxian_01.jpg"], is_recommended=True, sort_order=7),
        FoodRecommend(bnb_id="shanji", name="见山茶", category="茶饮",
            description="庐山本土新式茶饮。云雾茉莉鲜奶茶最受欢迎，门头是网红打卡地标",
            address="牯岭镇牯岭正街88号", map_link="https://uri.amap.com/marker?position=115.9802,29.5570&name=见山茶",
            price_range="人均 ¥18-32", must_try="云雾茉莉鲜奶茶、雪顶云雾奶茶",
            images=["/static/img/food/jianshan_01.webp"], sort_order=8),
    ]
    db.add_all(foods)
    info("   山纪 8家美食推荐 已填充（与归墅共享牯岭街美食圈）")


def _seed_donglinwai_foods(db):
    """东林外美食 — 2本地（大路王山庄+悦莲素食）+ 4山上餐馆 + 2茶饮"""
    foods = [
        FoodRecommend(bnb_id="donglinwai", name="大路王山庄", category="农家菜",
            description="步行2分钟即到！花筑品牌农家菜馆，住客好评「菜烧的很好，像家一样亲切」",
            address="赛阳镇赛阳路（东林外旁140米）",
            map_link="https://uri.amap.com/marker?position=115.940758,29.595012&name=大路王山庄",
            price_range="人均 ¥45-65", must_try="庐山三石煲、农家小炒肉、土鸡汤",
            images=["/static/img/food/daluwang_01.webp"],
            is_recommended=True, sort_order=1, tags=["#步行可达", "#农家菜", "#住客好评"]),
        FoodRecommend(bnb_id="donglinwai", name="悦莲素食自助", category="素食",
            description="东林寺周边口碑最好的素食馆！20+种素食自助，清淡健康。朝拜前后吃一顿，身心都清净",
            address="东林寺周边（步行约10分钟）", price_range="人均 ¥28-38",
            must_try="素斋自助、菌菇汤面、手工豆腐",
            images=["/static/img/food/yuelian_01.jpg"], is_recommended=True, sort_order=2,
            tags=["#素食", "#自助", "#东林寺周边"]),
        FoodRecommend(bnb_id="donglinwai", name="石牛酒家", category="赣菜(山上)",
            description="牯岭街最火苍蝇馆子，现炒有锅气。索道上山后可达", address="牯岭镇庐山正街15-1号",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5570&name=石牛酒家",
            price_range="人均 ¥55-75", must_try="三杯鸡、土豆烧牛肉、黄豆烧皖鱼",
            images=["/static/img/food/shiniu_01.jpg"], sort_order=3),
        FoodRecommend(bnb_id="donglinwai", name="847别墅餐厅", category="赣菜(山上)",
            description="百年别墅里的江西菜，服务出了名的好", address="牯岭镇窑洼路与慧远路交叉口东120米",
            map_link="https://uri.amap.com/marker?position=115.9795,29.5580&name=847别墅餐厅",
            price_range="人均 ¥60-70", must_try="土豆烧肉、红烧白鱼、菌菇汤",
            images=["/static/img/food/847_01.jpg"], sort_order=4),
        FoodRecommend(bnb_id="donglinwai", name="利民煨汤馆", category="小吃/煨汤(山上)",
            description="瓦罐炭火慢煨，爬山后的续命汤", address="牯岭镇正街中段",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5572&name=利民煨汤馆",
            price_range="人均 ¥26-45", must_try="茶树菇排骨汤、山药土鸡汤、南昌拌粉",
            images=["/static/img/food/limin_01.jpg"], sort_order=5),
        FoodRecommend(bnb_id="donglinwai", name="庐人村·牯岭美食集", category="赣菜(山上)",
            description="二楼靠窗位可观山景。云雾鸡稻草荷叶裹烤，一楼有特产", address="牯岭镇合面街1号",
            map_link="https://uri.amap.com/marker?position=115.9803,29.5569&name=庐人村",
            price_range="人均 ¥80-100", must_try="云雾鸡、老村长扣肉夹馍",
            images=["/static/img/food/lurencun_01.jpg"], sort_order=6),
        FoodRecommend(bnb_id="donglinwai", name="庐小仙", category="茶饮(山上)",
            description="庐山鲜果茶饮！桃香云雾茶+史努比联名杯", address="牯岭镇合面街",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5570&name=庐小仙",
            price_range="人均 ¥18-28", must_try="桃香云雾茶、庐小仙奶茶（史努比杯）",
            images=["/static/img/food/luxiaoxian_01.jpg"], is_recommended=True, sort_order=7),
        FoodRecommend(bnb_id="donglinwai", name="见山茶", category="茶饮(山上)",
            description="庐山本土新式茶饮。云雾茉莉鲜奶茶最受欢迎，门头是网红打卡地标",
            address="牯岭镇牯岭正街88号", map_link="https://uri.amap.com/marker?position=115.9802,29.5570&name=见山茶",
            price_range="人均 ¥18-32", must_try="云雾茉莉鲜奶茶、雪顶云雾奶茶",
            images=["/static/img/food/jianshan_01.webp"], sort_order=8),
    ]
    db.add_all(foods)
    info("   东林外 8家美食推荐 已填充（2本地+4山上+2茶饮）")


def seed_orders(db):
    """示例订单数据"""
    from datetime import datetime, timedelta
    if db.query(AggregatedOrder).count() > 0:
        return
    today = datetime.utcnow().strftime("%Y-%m-%d")
    tmr = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    d3 = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
    d5 = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")
    PLATFORM_FEES = {"ctrip":0.12,"meituan":0.10,"fliggy":0.10,"dianping":0.08,"direct":0,"xiaohongshu":0,"douyin":0}
    orders = [
        ("ctrip","CT20260601","张伟","山景·精致大床房",today,tmr,1,688,2,"checked_in"),
        ("meituan","MT20260602","李娜","田园家庭房",today,tmr,1,788,3,"checked_in"),
        ("fliggy","FZ20260603","王磊","清舍·露台大床房",today,tmr,1,788,2,"confirmed"),
        ("ctrip","CT20260604","赵雪","室雅茶香套房",tmr,d3,2,1976,4,"confirmed"),
        ("direct","","陈明","知还标准间",tmr,d3,2,976,2,"confirmed"),
        ("meituan","MT20260605","刘洋","特惠标准间",d5,(datetime.utcnow()+timedelta(days=6)).strftime("%Y-%m-%d"),1,388,2,"confirmed"),
        ("xiaohongshu","","孙雨","山野大床房",d5,(datetime.utcnow()+timedelta(days=7)).strftime("%Y-%m-%d"),2,1176,2,"confirmed"),
    ]
    for plat, oid, name, room, ci, co, n, amt, gc, st in orders:
        fee = round(amt * PLATFORM_FEES.get(plat, 0), 2)
        db.add(AggregatedOrder(platform=plat,platform_order_id=oid,guest_name=name,room_type=room,check_in=ci,check_out=co,nights=n,total_amount=amt,platform_fee=fee,net_revenue=round(amt-fee,2),guest_count=gc,status=st,source="seed"))
    db.commit()


def seed_bookings(db):
    """预订种子数据 — 演示AI解锁 + 退房好评推送"""
    from datetime import datetime, timedelta
    if db.query(Booking).count() > 0:
        return
    now = datetime.utcnow()
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
    from datetime import datetime, timedelta
    if db.query(GuestPoints).count() > 0:
        return
    now = datetime.utcnow()

    # 积分账户
    guest = GuestPoints(
        openid="web_user", total_points=580, total_earned=850,
        total_spent=270, membership="silver",
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
        PointLog(openid="web_user", points=-150, action="redeem_coupon",
                 description="兑换50元优惠券 -150", created_at=now - timedelta(days=7)),
    ]
    db.add_all(logs)


def seed_tea(bnb_id="shanji"):
    """茶园模块种子数据（云上·山纪）"""
    from models import SessionLocal, TeaType, TeaExperience, TeaProduct
    db = SessionLocal()
    try:
        if db.query(TeaType).count() > 0:
            return
        # 茶叶品类
        types = [
            TeaType(bnb_id=bnb_id, name="庐山云雾茶", description="中国十大名茶之一，生长于庐山海拔800米以上的云雾带，芽叶肥壮、白毫显露、香高味醇",
                    origin="庐山汉阳峰云雾带", brewing_method="85°C山泉水，玻璃杯上投法，3分钟",
                    tasting_notes="清香持久，滋味鲜醇回甘，汤色清澈明亮", sort_order=1),
            TeaType(bnb_id=bnb_id, name="庐山红茶", description="采用庐山本地茶青发酵制成，汤色红艳明亮，带有蜜糖甜香",
                    origin="庐山牯岭镇茶园", brewing_method="90°C沸水，紫砂壶，冲泡30秒",
                    tasting_notes="蜜糖甜香，滋味醇厚顺滑，回甘明显", sort_order=2),
            TeaType(bnb_id=bnb_id, name="庐山白茶", description="轻发酵工艺，保留茶叶天然风味，清甜淡雅适合四季饮用",
                    origin="庐山五老峰下", brewing_method="80°C水，玻璃杯，2分钟",
                    tasting_notes="清甜淡雅，花香隐约，入口绵柔", sort_order=3),
        ]
        db.add_all(types)
        db.flush()

        # 茶园体验
        exps = [
            TeaExperience(bnb_id=bnb_id, name="晨雾采茶体验", description="清晨跟随茶农上山，在晨雾中亲手采摘嫩芽，感受茶山清晨的宁静",
                          duration="2小时", price=128, capacity=10,
                          includes=["采茶竹篓", "茶农指导", "鲜制云雾茶一杯"], sort_order=1),
            TeaExperience(bnb_id=bnb_id, name="手工制茶工坊", description="在制茶师傅指导下，亲手完成杀青、揉捻、干燥等工序，制作属于自己的茶",
                          duration="3小时", price=268, capacity=6,
                          includes=["茶叶原料", "制茶工具", "自制茶叶50g带回家"], sort_order=2),
            TeaExperience(bnb_id=bnb_id, name="茶道品鉴课", description="学习盖碗、紫砂壶冲泡技法，品鉴三款不同年份的庐山茶",
                          duration="1.5小时", price=168, capacity=8,
                          includes=["三款茶品", "茶点", "茶道器具使用"], sort_order=3),
        ]
        db.add_all(exps)

        # 茶叶商品
        prods = [
            TeaProduct(bnb_id=bnb_id, name="庐山云雾茶·特级", tea_type_id=types[0].id,
                       price=288, weight="100g", description="明前手工采摘，一芽一叶，鲜醇回甘", stock=20, sort_order=1),
            TeaProduct(bnb_id=bnb_id, name="庐山云雾茶·一级", tea_type_id=types[0].id,
                       price=168, weight="100g", description="谷雨前采摘，香气浓郁，口感醇厚", stock=50, sort_order=2),
            TeaProduct(bnb_id=bnb_id, name="庐山红茶·蜜韵", tea_type_id=types[1].id,
                       price=138, weight="100g", description="蜜糖甜香，暖胃养心，冬日首选", stock=30, sort_order=3),
        ]
        db.add_all(prods)
        db.commit()
        print("  ✅ 茶园模块种子数据填充完成")
    finally:
        db.close()


def seed_healing(bnb_id="donglinwai"):
    """疗愈模块种子数据（云上·东林外）—— 一对一个案服务"""
    from models import SessionLocal, HealingCourse
    db = SessionLocal()
    try:
        existing = db.query(HealingCourse).filter(HealingCourse.bnb_id == bnb_id).count()
        if existing >= 8:
            return
        elif existing > 0:
            # 清除旧数据后重新填充
            db.query(HealingCourse).filter(HealingCourse.bnb_id == bnb_id).delete()
            db.flush()

        courses = [
            # ═══ 音疗疗愈系列 ═══
            HealingCourse(bnb_id=bnb_id, name="五音涤尘", category="音疗疗愈",
                          description="以宫商角徵羽五音对应五脏，通过古法音疗振动涤荡内在尘垢。精选天然乐器（水晶钵、铜锣、雨棍等），层层递进释放深层压力，恢复身心和谐韵律。",
                          price_tiers=[
                              {"duration": "1小时", "price": 298},
                              {"duration": "2小时", "price": 528},
                              {"duration": "3小时", "price": 728},
                          ], therapist="琼儿老师",
                          tags=[{"text": "五脏调理", "color": "green"}, {"text": "压力释放", "color": "blue"}],
                          sort_order=1),
            HealingCourse(bnb_id=bnb_id, name="铜钵沐心", category="音疗疗愈",
                          description="喜马拉雅铜钵置于身体七大脉轮之上，以槌击钵缘产生的泛音波动层层包裹全身。钵音如暖泉沐心，融化紧绷筋膜，引领进入深度冥想态。",
                          price_tiers=[
                              {"duration": "1小时", "price": 398},
                              {"duration": "2小时", "price": 718},
                              {"duration": "3小时", "price": 968},
                          ], therapist="琼儿老师",
                          tags=[{"text": "脉轮平衡", "color": "purple"}, {"text": "深度冥想", "color": "purple"}],
                          sort_order=2),
            HealingCourse(bnb_id=bnb_id, name="全息振动疗愈", category="音疗疗愈",
                          description="融合颂钵、音叉、人声泛音三大振动体系，从细胞层面启动自愈力。以精密频率序列作用于神经系统，适合长期失眠、慢性疲劳及能量低落者。",
                          price_tiers=[
                              {"duration": "1小时", "price": 800},
                              {"duration": "2小时", "price": 1480},
                              {"duration": "3小时", "price": 1980},
                          ], therapist="琼儿老师",
                          tags=[{"text": "失眠修复", "color": "teal"}, {"text": "细胞自愈", "color": "teal"}],
                          sort_order=3),

            # ═══ 芳香疗愈系列 ═══
            HealingCourse(bnb_id=bnb_id, name="炁贯沐顶", category="芳香疗愈",
                          description="以道家导引术结合头部经络穴位按摩，配合定制复方精油沿督脉推贯。清阳上升，浊气下沉，对头痛、失眠、用脑过度的客人尤有奇效。",
                          price_tiers=[
                              {"duration": "45分钟", "price": 298},
                              {"duration": "90分钟", "price": 528},
                              {"duration": "135分钟", "price": 728},
                          ], therapist="琼儿老师",
                          tags=[{"text": "头痛舒缓", "color": "blue"}, {"text": "清脑提神", "color": "green"}],
                          sort_order=4),
            HealingCourse(bnb_id=bnb_id, name="气旋回春", category="芳香疗愈",
                          description="以太极推揉手法沿经络走向疏导气机，配合回春配方精油渗透肌理。从丹田出发，螺旋式推展至四肢末梢，唤醒沉睡的生命活力。",
                          price_tiers=[
                              {"duration": "45分钟", "price": 298},
                              {"duration": "90分钟", "price": 528},
                              {"duration": "135分钟", "price": 728},
                          ], therapist="琼儿老师",
                          tags=[{"text": "经络疏导", "color": "orange"}, {"text": "活力唤醒", "color": "orange"}],
                          sort_order=5),
            HealingCourse(bnb_id=bnb_id, name="轻脊引香", category="芳香疗愈",
                          description="专注脊柱两侧膀胱经的芳香拨筋手法，逐节松解椎骨间的紧张与错位感。配合温灸与定制脊柱精油，改善体态、释放背部长期积压的疲劳。",
                          price_tiers=[
                              {"duration": "45分钟", "price": 368},
                              {"duration": "90分钟", "price": 668},
                              {"duration": "135分钟", "price": 888},
                          ], therapist="琼儿老师",
                          tags=[{"text": "脊柱护理", "color": "teal"}, {"text": "体态矫正", "color": "green"}],
                          sort_order=6),
            HealingCourse(bnb_id=bnb_id, name="芳香裹肤", category="芳香疗愈",
                          description="东林外最具仪式感的奢华身体护理。以温热的草本泥膜包裹全身，配合精油引流按摩，深层排毒、紧致肌肤。裹肤后以玫瑰花瓣浴收尾，由内而外焕发柔光。",
                          price_tiers=[
                              {"duration": "1小时", "price": 2980},
                              {"duration": "2小时", "price": 5280},
                              {"duration": "3小时", "price": 7280},
                          ], therapist="琼儿老师",
                          tags=[{"text": "深层排毒", "color": "pink"}, {"text": "紧致焕肤", "color": "pink"}],
                          sort_order=7),

            # ═══ 情绪疗愈系列 ═══
            HealingCourse(bnb_id=bnb_id, name="情绪疏压释放", category="情绪疗愈",
                          description="融合EFT情绪释放敲击、引导式意象对话与呼吸疏导三大技术，在安全抱持的空间中探访情绪淤堵的源头。不评判、不说教，只让情绪自然流过、被看见、被释放。适合长期高压、情绪内耗、或正经历人生转折期的你。",
                          price_tiers=[
                              {"duration": "3小时", "price": 1680},
                          ], therapist="琼儿老师",
                          tags=[{"text": "情绪释放", "color": "gold"}, {"text": "内在疗愈", "color": "gold"}],
                          sort_order=8),
        ]
        db.add_all(courses)
        db.commit()
        print("  ✅ 疗愈模块种子数据填充完成（8项一对一个案服务）")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
