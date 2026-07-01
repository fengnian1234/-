"""
云上·山纪 种子数据 — 客房、菜单、快捷服务、旅游路线、美食推荐、此山茶场
"""
from models import Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend
from services.logger import info

# 房型图片计数（sort_order → 图片数量）
_SHANJI_ROOM_IMAGE_COUNTS = {
    1:9, 2:7, 3:5, 4:6, 5:9, 6:7, 7:5, 8:6,
    9:7, 10:6, 11:7, 12:11, 13:6, 14:13, 15:8, 16:8,
}

def _shanji_room_imgs(sort_order):
    """按 sort_order 获取山纪房型图片列表（独立图片库）"""
    count = _SHANJI_ROOM_IMAGE_COUNTS.get(sort_order, 0)
    return [f"/static/img/rooms/shanji/room{sort_order:02d}_{i:02d}.webp"
            for i in range(count)]


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



def _seed_shanji_menu(db):
    """山纪菜单 — 山货餐厅（独立于茶场，山货小炒烧菜为主）"""
    categories = [
        MenuCategory(bnb_id="shanji", name="山货小炒", icon="🔥", sort_order=1),
        MenuCategory(bnb_id="shanji", name="山货烧菜", icon="🍲", sort_order=2),
        MenuCategory(bnb_id="shanji", name="汤煲炖品", icon="🫕", sort_order=3),
        MenuCategory(bnb_id="shanji", name="主食简餐", icon="🍚", sort_order=4),
        MenuCategory(bnb_id="shanji", name="咖啡茶饮", icon="☕", sort_order=5),
    ]
    db.add_all(categories)
    db.flush()

    c0, c1, c2, c3, c4 = categories[0].id, categories[1].id, categories[2].id, categories[3].id, categories[4].id
    items = [
        # ── 山货小炒 ──
        MenuItem(bnb_id="shanji", category_id=c0, name="竹笋炒庐山腊肉", price=48, description="庐山野竹笋+农家土猪腊肉，柴火灶爆炒，镬气十足", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c0, name="野山菌炒土猪肉", price=42, description="庐山松林野菌+散养土猪五花，鲜香滑嫩", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c0, name="蒜苗炒土鸡蛋", price=28, description="后院散养土鸡蛋+庐山紫皮蒜苗，最简单也最下饭", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c0, name="茶香小河虾", price=58, description="庐山云雾茶嫩芽入馔，小河虾酥脆可连壳吃", sort_order=4),
        MenuItem(bnb_id="shanji", category_id=c0, name="青椒炒石鸡", price=68, description="庐山石鸡+本地薄皮青椒，肉质细嫩胜田鸡", is_recommended=True, sort_order=5),
        MenuItem(bnb_id="shanji", category_id=c0, name="蕨菜炒肉丝", price=32, description="春日限定野生蕨菜，过季改用山泉水发制干蕨菜", sort_order=6),
        # ── 山货烧菜 ──
        MenuItem(bnb_id="shanji", category_id=c1, name="庐山三石煲", price=88, description="石鸡+石鱼+石耳文火慢炖两小时，庐山珍味一锅鲜", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c1, name="茶树菇红烧肉", price=68, description="庐山茶树菇+土猪五花，冰糖上色，入口即化", is_recommended=True, sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c1, name="笋干焖土鸡", price=78, description="庐山野笋干+散养土鸡，柴火灶焖烧40分钟", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c1, name="石耳烧排骨", price=58, description="庐山岩壁石耳+土猪肋排，咸鲜入味", sort_order=4),
        MenuItem(bnb_id="shanji", category_id=c1, name="山泉豆腐煲", price=38, description="庐山泉水手工豆腐+菌菇时蔬，素净鲜甜", sort_order=5),
        # ── 汤煲炖品 ──
        MenuItem(bnb_id="shanji", category_id=c2, name="石耳土鸡汤", price=68, description="庐山野生石耳+散养土鸡，隔水炖三小时，汤清味醇", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c2, name="竹荪排骨汤", price=48, description="庐山竹林竹荪+土猪排骨，清润养胃", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c2, name="茶树菇老鸭汤", price=58, description="庐山干茶树菇+两年老鸭，文火慢炖，回味甘香", sort_order=3),
        # ── 主食简餐 ──
        MenuItem(bnb_id="shanji", category_id=c3, name="山货炒饭", price=32, description="腊肉丁+笋干+野菌+土鸡蛋，山货满满一大盘", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c3, name="江西拌粉", price=22, description="地道南昌拌粉做法，花生碎+萝卜干+辣椒油，住客好评率最高", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c3, name="庐山石鱼蒸蛋", price=38, description="庐山石鱼干蒸土鸡蛋，鲜香嫩滑，老少皆宜", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c3, name="农家小炒肉套餐", price=42, description="土猪五花配薄皮青椒+时蔬+米饭+例汤", sort_order=4),
        # ── 咖啡茶饮 ──
        MenuItem(bnb_id="shanji", category_id=c4, name="庐山云雾茶(杯)", price=38, description="中国十大名茶，明前高山云雾，红绿两色可选", is_recommended=True, sort_order=1),
        MenuItem(bnb_id="shanji", category_id=c4, name="庐山云雾茶(壶)", price=98, description="整壶冲泡，2-3人品茗，配茶点", sort_order=2),
        MenuItem(bnb_id="shanji", category_id=c4, name="美式咖啡", price=26, description="经典美式，纯粹醇香", sort_order=3),
        MenuItem(bnb_id="shanji", category_id=c4, name="现磨拿铁", price=36, description="意式浓缩+鲜牛乳，奶香丝滑", sort_order=4),
        MenuItem(bnb_id="shanji", category_id=c4, name="桂花云雾奶盖", price=32, description="云雾茶底+鲜奶奶盖+干桂花，山纪特调", sort_order=5),
    ]
    db.add_all(items)
    info("   山纪 5类27款山货餐厅菜单 已填充")



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
        QuickService(bnb_id="shanji", name="茶道体验预约", description="此山茶场采茶/制茶/茶道品鉴体验预约", icon="🍵", category="frontdesk", estimated_time="即刻预约", sort_order=9),
        QuickService(bnb_id="shanji", name="手工课程预约", description="陶瓷文化体验、手工课程预约", icon="🎨", category="frontdesk", estimated_time="即刻预约", sort_order=10),
        QuickService(bnb_id="shanji", name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟", sort_order=11),
        QuickService(bnb_id="shanji", name="叫醒服务", description="设定叫醒时间，准时电话提醒", icon="⏰", category="frontdesk", estimated_time="准时执行", sort_order=12),
        QuickService(bnb_id="shanji", name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=13),
        QuickService(bnb_id="shanji", name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=14),
        QuickService(bnb_id="shanji", name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=15),
    ]
    db.add_all(services)
    info("   山纪 15项快捷服务 已填充")



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
                {"name": "牯岭正街", "description": "逛小店、喝庐小仙、买当地特产伴手礼"},
                {"name": "街心公园看日落", "description": "傍晚坐在这里看山景发呆"},
            ],
            tips="山纪提供茶道体验+手工课程，不出民宿也能享受充实的一天。正街步行8分钟，吃饭逛街超方便。",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=云上山纪起点",
            sort_order=5,
        ),
    ]
    db.add_all(routes)
    info("   山纪 5条旅游路线 已填充（基于归墅路线+山纪特色优化）")



def _seed_shanji_foods(db):
    """山纪美食 — 与归墅共享牯岭街全部8家推荐（步行8分钟即到）"""
    foods = [
        FoodRecommend(bnb_id="shanji", name="石牛酒家", category="赣菜",
            description="牯岭街老牌苍蝇馆子，现炒现做有锅气。小红书1283赞攻略推荐，1450赞合集收录。环境一般但味道实在，从山纪步行8分钟即到",
            address="牯岭镇庐山正街15-1号（街心花园马路对面）",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5570&name=石牛酒家",
            price_range="人均 ¥55-75", must_try="三杯鸡、土豆烧牛肉、黄豆烧皖鱼、野芹菜、石耳烧鸡",
            tags=["#现炒有锅气", "#本地人推荐", "#高性价比", "#苍蝇馆子"],
            images=["/static/img/food/shiniu_01.jpg"], is_recommended=True, sort_order=1,
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
        FoodRecommend(bnb_id="shanji", name="847别墅餐厅", category="赣菜",
            description="百年别墅改造的江西菜馆。小红书1450赞合集列为“褒贬不一”——有人吃了三次还想吃，有人说一般般。服务公认好",
            address="牯岭镇窑洼路与慧远路交叉口东120米",
            map_link="https://uri.amap.com/marker?position=115.9795,29.5580&name=847别墅餐厅",
            price_range="人均 ¥60-70", must_try="土豆烧肉、红烧白鱼、菌菇汤、香煎豆腐、鸭/烧鸡（1450赞合集推荐）",
            tags=["#百年别墅", "#服务满分", "#褒贬不一", "#真实推荐"],
            images=["/static/img/food/847_01.jpg"], is_recommended=True, sort_order=2,
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
        FoodRecommend(bnb_id="shanji", name="望庐说·本地菜馆", category="赣菜",
            description="牯岭街网红餐厅，环境古色古香。口碑两极分化严重——338赞笔记说“一年了还在想念”，98赞笔记说“避雷”。服务态度公认好",
            address="牯岭镇合面街10号（建设银行对面）",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5568&name=望庐说",
            price_range="人均 ¥80-100", must_try="板栗烧鸡、外婆家粉皮、炝鸭血、干锅笋",
            tags=["#网红餐厅", "#环境好", "#争议大", "#服务好"],
            images=["/static/img/food/wanglu_01.jpg"], sort_order=3,
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
        FoodRecommend(bnb_id="shanji", name="庐人村·牯岭美食集", category="赣菜",
            description="二楼靠窗位可看山景拍照。1450赞XHS合集列为“褒贬不一”。云雾鸡用稻草荷叶裹烤是特色，一楼有特产和奶茶店",
            address="牯岭镇合面街1号（正街上）",
            map_link="https://uri.amap.com/marker?position=115.9803,29.5569&name=庐人村",
            price_range="人均 ¥80-100", must_try="云雾鸡（稻草荷叶裹烤）、老村长扣肉夹馍、炝鸭血",
            tags=["#山景餐厅", "#拍照好看", "#褒贬不一", "#云雾鸡"],
            images=["/static/img/food/lurencun_01.jpg"], sort_order=4,
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
        FoodRecommend(bnb_id="shanji", name="利民煨汤馆", category="小吃/煨汤",
            description="大众点评4.0星、9186条评论的苍蝇馆子！1450赞XHS合集收录。瓦罐炭火慢煨，价格亲民环境一般，是最暖胃的存在",
            address="牯岭镇正街中段",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5572&name=利民煨汤馆",
            price_range="人均 ¥26-45", must_try="茶树菇排骨汤、山药土鸡汤、石鱼炒蛋、南昌拌粉",
            tags=["#大众点评9186评", "#瓦罐煨汤", "#性价比之王", "#苍蝇馆子"],
            images=["/static/img/food/limin_01.jpg"], is_recommended=True, sort_order=5,
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
        FoodRecommend(bnb_id="shanji", name="人情味茶园雅院", category="本地特色",
            description="庐山索道旁藏匿于绿意庭院中的宝藏餐厅，仿佛置身世外桃源。油焖庐山竹笋、茶香鸭、芥末虾球好评如潮",
            address="庐山市牯岭镇慧远路庐山索道东北110米",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=人情味茶园雅院",
            price_range="人均 ¥69", must_try="油焖庐山竹笋、人情味茶香鸭、芥末虾球",
            tags=["#茶园", "#索道旁", "#竹笋", "#茶香鸭", "#庐山美食"],
            images=["/static/img/food/renchawei_01.jpg", "/static/img/food/renchawei_02.jpg"], sort_order=6,
            detail_content=(
                "\U0001f31f **入仙境\U0001f33f在庐山茶园深处吃了顿饭…**\n\n"
                "✨【人情味•茶园雅院】探店记✨\n\n"
                "你是否厌倦了城市的喧嚣，渴望在忙碌中找到一处静谧之地？来吧！这里有一处藏匿于庐山上的小院餐厅，绝对能让你流连忘返！\n\n"
                "\U0001f4cd **位置**：位于庐山牯岭镇索道北面110米。从索道下来步行只需几分钟，就能看到一个充满绿意的庭院，仿佛置身世外桃源。\n\n"
                "⏰ **营业时间**：每天11:00-21:00。无论你是想来一顿悠闲的午餐还是温馨的晚餐，这里都能满足你的需求。\n\n"
                "\U0001f37d️ **推荐菜品**：\n"
                "• 油焖庐山竹笋：新鲜采摘的竹笋，经过大厨的精心烹饪，每一口都是大自然的味道。\n"
                "• 人情味茶香鸭：这道菜将茶叶的清香与鸭肉完美融合，让人回味无穷。\n"
                "• 芥末虾球：虾肉鲜嫩，搭配微微刺激的芥末酱，口感层次丰富。"
            ),
        ),
        FoodRecommend(bnb_id="shanji", name="庐小仙", category="茶饮",
            description="庐山高山上的鲜果茶饮！120赞XHS笔记推荐“必喝这家”。桃香云雾茶是招牌，史努比联名杯超可爱，小红书热门打卡店",
            address="牯岭镇合面街（二楼可用餐）",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5570&name=庐小仙",
            price_range="人均 ¥18-28", must_try="桃香云雾茶、庐小仙奶茶（史努比杯）、草莓云雾鲜果茶",
            tags=["#庐山限定", "#鲜果茶", "#史努比联名", "#XHS爆款", "#必打卡"],
            images=["/static/img/food/luxiaoxian_01.jpg"], is_recommended=True, sort_order=7,
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
        FoodRecommend(bnb_id="shanji", name="见山茶", category="茶饮",
            description="庐山本土新式茶饮品牌。1283赞XHS博主说“和霸王茶姬差不多”，274赞笔记说“很普通建议喝雪盖顶”。门头是网红打卡地标，适合拍照发圈",
            address="牯岭镇牯岭正街88号（正街中段）",
            map_link="https://uri.amap.com/marker?position=115.9802,29.5570&name=见山茶",
            price_range="人均 ¥18-32", must_try="云雾茉莉鲜奶茶、雪顶云雾奶茶、见山柠檬茶、桂花云雾奶盖",
            tags=["#庐山限定", "#拍照打卡", "#争议口味", "#中式美学"],
            images=["/static/img/food/jianshan_01.webp"], sort_order=8,
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
    info("   山纪 8家美食推荐 已填充（与归墅共享牯岭街美食圈）")



def seed_tea(bnb_id="shanji"):
    """此山茶场种子数据（云上·山纪）— 幂等：先清旧数据再插入"""
    from models import SessionLocal, TeaType, TeaExperience, TeaProduct
    db = SessionLocal()
    try:
        # 幂等：先清此山纪的旧茶场数据
        db.query(TeaProduct).filter(TeaProduct.bnb_id == bnb_id).delete()
        db.query(TeaExperience).filter(TeaExperience.bnb_id == bnb_id).delete()
        db.query(TeaType).filter(TeaType.bnb_id == bnb_id).delete()
        db.flush()

        # ── 茶叶品类 ──
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

        # ── 消费项目（按分类）──
        exps = [
            # 简餐 (meal)
            TeaExperience(bnb_id=bnb_id, category="meal", name="素面", description="庐山山泉煮面，配时令山野菜，清淡养胃",
                          duration="约15分钟出品", price=28, capacity=0,
                          includes=["时令山野菜", "手工面条"], sort_order=1),
            TeaExperience(bnb_id=bnb_id, category="meal", name="茶香炒饭", description="庐山云雾茶入饭，配松仁火腿炒制，茶香四溢",
                          duration="约15分钟出品", price=38, capacity=0,
                          includes=["云雾茶粉", "松仁", "火腿丁"], sort_order=2),
            TeaExperience(bnb_id=bnb_id, category="meal", name="庐山石鸡煲", description="庐山特产石鸡，配以茶树菇文火慢炖，鲜香浓郁",
                          duration="约30分钟出品", price=88, capacity=0,
                          includes=["庐山石鸡", "茶树菇", "时蔬"], sort_order=3),
            # 饮品 (drink)
            TeaExperience(bnb_id=bnb_id, category="drink", name="云雾冷萃", description="庐山云雾茶低温冷萃8小时，清冽甘甜，夏日首选",
                          duration="即刻出杯", price=32, capacity=0,
                          includes=["冷萃云雾茶", "冰块"], sort_order=4),
            TeaExperience(bnb_id=bnb_id, category="drink", name="古树红茶拿铁", description="云南古树红茶+鲜牛乳，茶香奶滑，温热舒心",
                          duration="即刻出杯", price=36, capacity=0,
                          includes=["古树红茶", "鲜牛乳"], sort_order=5),
            TeaExperience(bnb_id=bnb_id, category="drink", name="桂花云雾奶盖", description="云雾茶底+鲜奶奶盖+干桂花，此山招牌特调",
                          duration="即刻出杯", price=32, capacity=0,
                          includes=["云雾茶底", "鲜奶奶盖", "干桂花"], sort_order=6),
            TeaExperience(bnb_id=bnb_id, category="drink", name="手冲单品·庐山云雾", description="茶艺师手冲一壶云雾茶，配两只茶杯，适合二人对饮",
                          duration="约10分钟", price=68, capacity=0,
                          includes=["一壶云雾茶", "两只茶杯", "茶点"], sort_order=7),
            # 甜品 (dessert)
            TeaExperience(bnb_id=bnb_id, category="dessert", name="茶冻", description="云雾茶汤+石花菜凝冻，Q弹清甜，入口即化",
                          duration="即刻出品", price=22, capacity=0,
                          includes=["云雾茶汤", "石花菜", "桂花蜜"], sort_order=8),
            TeaExperience(bnb_id=bnb_id, category="dessert", name="抹茶芝士蛋糕", description="日式抹茶+奶油奶酪，绵密细腻，茶香回甘",
                          duration="即刻出品", price=38, capacity=0,
                          includes=["日式抹茶粉", "奶油奶酪"], sort_order=9),
            TeaExperience(bnb_id=bnb_id, category="dessert", name="桂花酒酿圆子", description="庐山桂花+手工糯米圆子，甜糯温暖，经典江西甜品",
                          duration="约10分钟", price=26, capacity=0,
                          includes=["庐山桂花", "手工糯米圆子", "酒酿"], sort_order=10),
            # 晚场酒水 (alcohol) — 18:00后才可购买
            TeaExperience(bnb_id=bnb_id, category="alcohol", name="庐山云雾精酿", description="此山茶场联名精酿啤酒，云雾茶花入酿，清爽回甘",
                          duration="即刻出杯", price=38, capacity=0,
                          includes=["云雾茶花", "精酿啤酒"], sort_order=11),
            TeaExperience(bnb_id=bnb_id, category="alcohol", name="青梅煮酒", description="庐山青梅+米酒温煮，酸甜暖胃，配茶更佳",
                          duration="约10分钟", price=48, capacity=0,
                          includes=["庐山青梅", "手工米酒"], sort_order=12),
            TeaExperience(bnb_id=bnb_id, category="alcohol", name="桂花米酿", description="庐山桂花酿制米酒，清甜不腻，冰镇更佳",
                          duration="即刻出杯", price=32, capacity=0,
                          includes=["庐山桂花", "糯米酒"], sort_order=13),
            TeaExperience(bnb_id=bnb_id, category="alcohol", name="特调茶酒", description="云雾茶+金酒+柠檬，茶香鸡尾酒，晚场限定",
                          duration="即刻出杯", price=58, capacity=0,
                          includes=["云雾茶", "金酒", "柠檬"], sort_order=14),
            # 晚场演出 (performance)
            TeaExperience(bnb_id=bnb_id, category="performance", name="山间音乐会", description="晚场民谣弹唱+手碟即兴，庭院Live，山风伴奏",
                          duration="约45分钟/场", price=68, capacity=30,
                          includes=["民谣弹唱", "手碟即兴", "庭院坐席"], sort_order=15),
            TeaExperience(bnb_id=bnb_id, category="performance", name="茶山露天电影", description="星空下的露天电影放映，配茶饮一杯+小食，山夜独好",
                          duration="约2小时", price=38, capacity=50,
                          includes=["露天放映", "茶饮一杯", "小食拼盘"], sort_order=16),
        ]
        db.add_all(exps)

        # ── 茶叶伴手礼 ──
        prods = [
            TeaProduct(bnb_id=bnb_id, name="庐山云雾茶·特级", tea_type_id=types[0].id,
                       price=288, weight="100g/盒", description="明前手工采摘，一芽一叶，鲜醇回甘，礼品木盒装", stock=20, sort_order=1),
            TeaProduct(bnb_id=bnb_id, name="庐山云雾茶·一级", tea_type_id=types[0].id,
                       price=168, weight="100g/盒", description="谷雨前采摘，香气浓郁，口感醇厚，纸盒精装", stock=50, sort_order=2),
            TeaProduct(bnb_id=bnb_id, name="庐山红茶·蜜韵", tea_type_id=types[1].id,
                       price=138, weight="100g/盒", description="蜜糖甜香，暖胃养心，冬日首选", stock=30, sort_order=3),
            TeaProduct(bnb_id=bnb_id, name="此山茶饼", tea_type_id=None,
                       price=68, weight="200g/饼", description="庐山云雾茶粉+糯米手工压制，茶香扑鼻，配茶佳点", stock=40, sort_order=4),
            TeaProduct(bnb_id=bnb_id, name="自采茶叶·礼品装", tea_type_id=None,
                       price=388, weight="150g/木盒", description="茶场自采自制，精选一芽一叶，手工木盒精装，送礼体面", stock=15, sort_order=5),
            TeaProduct(bnb_id=bnb_id, name="自采茶叶·袋装", tea_type_id=None,
                       price=128, weight="80g/袋", description="茶场自采自制，日常饮用实惠装，自留首选", stock=30, sort_order=6),
        ]
        db.add_all(prods)
        db.commit()
        print("  ✅ 此山茶场种子数据填充完成")
    finally:
        db.close()



