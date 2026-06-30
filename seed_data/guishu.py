"""
归墅 (guishu) 种子数据 — 客房、菜单、快捷服务、旅游路线、美食推荐
"""
from models import Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend


def _seed_guishu_rooms(db):
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


def _seed_guishu_menu(db):
    # ── 归墅 (guishu) — 三山二水咖啡 真实菜单 ──
    categories = [
        MenuCategory(name="咖啡/茶饮", icon="☕", sort_order=1),
        MenuCategory(name="简餐", icon="🍝", sort_order=2),
        MenuCategory(name="甜品", icon="🍰", sort_order=3),
        MenuCategory(name="特调饮品", icon="🍹", sort_order=4),
    ]
    db.add_all(categories)
    db.flush()

    c0, c1, c2, c3 = categories[0].id, categories[1].id, categories[2].id, categories[3].id
    items = [
        # 咖啡/茶饮
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


def _seed_guishu_services(db):
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
        QuickService(name="特产代购", description="石鱼干/云雾茶等特产，按进价代购不加价", icon="🎁", category="frontdesk", estimated_time="次日可取", sort_order=18),

        # 设施维修 (sort_order 19-21)
        QuickService(name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=19),
        QuickService(name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=20),
        QuickService(name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=21),
    ]
    db.add_all(services)

def _seed_guishu_travel_routes(db):
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
                {"name": "牯岭正街", "description": "逛小店、喝见山茶/庐小仙、买当地特产伴手礼。正街上还有1元公交可以坐"},
                {"name": "街心公园", "description": "牯岭镇中心的小公园，傍晚坐在这里看山景发呆，超惬意"},
                {"name": "小天池看日落（可选）", "description": "从正街步行可达，日落时分金色阳光洒满山峦，手机也能拍出大片"},
            ],
            tips="非常适合到达当天或离开前半天的安排。不用赶景点，走哪算哪。正街上有各种特产店可以买伴手礼。傍晚在街心公园的长椅上坐着看山，是庐山最好的打开方式。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇",
            sort_order=5,
        ),
    ]
    db.add_all(routes)

def _seed_guishu_food_recommends(db):
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
        # ── 茶园雅院 ────────────────────────────────
        FoodRecommend(
            name="人情味茶园雅院",
            category="本地特色",
            description="庐山索道旁藏匿于绿意庭院中的宝藏餐厅，仿佛置身世外桃源。油焖庐山竹笋、茶香鸭、芥末虾球好评如潮",
            address="庐山市牯岭镇慧远路庐山索道东北110米",
            map_link="https://uri.amap.com/marker?position=115.978075,29.572595&name=人情味茶园雅院",
            price_range="人均 ¥69",
            must_try="油焖庐山竹笋、人情味茶香鸭、芥末虾球",
            sort_order=6,
            tags=["#茶园", "#索道旁", "#竹笋", "#茶香鸭", "#庐山美食"],
            images=["/static/img/food/renchawei_01.jpg", "/static/img/food/renchawei_02.jpg"],
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


