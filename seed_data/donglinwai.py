"""
云上·东林外 种子数据 — 客房、菜单、快捷服务、旅游路线、美食推荐、疗愈模块
"""
from models import Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend
from services.logger import info

# 房型图片计数（sort_order → 图片数量）
_DONGLINWAI_ROOM_IMAGE_COUNTS = {
    1:5, 2:5, 3:5, 4:6, 5:7, 6:7,
}

def _donglinwai_room_imgs(sort_order):
    """按 sort_order 获取东林外房型图片列表（独立图片库）"""
    count = _DONGLINWAI_ROOM_IMAGE_COUNTS.get(sort_order, 0)
    return [f"/static/img/rooms/donglinwai/room{sort_order:02d}_{i:02d}.webp"
            for i in range(count)]


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

