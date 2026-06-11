"""
种子数据 - 云上归墅民宿和庐山旅游信息
初始化数据库时自动填充
"""
from models import SessionLocal, init_db, Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend


def seed_all():
    """初始化数据库并填充种子数据"""
    init_db()
    db = SessionLocal()

    try:
        # 检查是否已初始化
        if db.query(Room).count() > 0:
            print("数据库已有数据，跳过初始化")
            return

        seed_rooms(db)
        seed_menu(db)
        seed_services(db)
        seed_travel_routes(db)
        seed_food_recommends(db)

        db.commit()
        print("✅ 种子数据初始化完成！")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


def seed_rooms(db):
    """房间数据"""
    rooms = [
        Room(
            name="云隐·大床房",
            room_type="大床房",
            price=688,
            original_price=888,
            description="推开窗便是云雾缭绕的山景，1.8米大床配鹅绒被，独立卫浴带观景浴缸，是情侣和独行旅客的静谧之选。",
            capacity=2,
            bed_type="1.8m大床",
            area="35㎡",
            amenities=["观景阳台", "地暖", "智能马桶", "观景浴缸", "鹅绒床品", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "https://picsum.photos/seed/yunshang01/800/600",
                "https://picsum.photos/seed/yunshang01b/800/600",
            ],
            view_type="山景",
            is_available=True,
            sort_order=1,
        ),
        Room(
            name="云栖·双床房",
            room_type="双床房",
            price=588,
            original_price=788,
            description="两张1.5米舒适床铺，适合闺蜜出游或亲子同行。房间宽敞明亮，配有儿童用品和亲子设施。",
            capacity=2,
            bed_type="1.5m双床",
            area="40㎡",
            amenities=["观景窗", "地暖", "儿童用品", "书桌", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "https://picsum.photos/seed/yunshang02/800/600",
                "https://picsum.photos/seed/yunshang02b/800/600",
            ],
            view_type="山景",
            is_available=True,
            sort_order=2,
        ),
        Room(
            name="云梦·亲子套房",
            room_type="套房",
            price=988,
            original_price=1288,
            description="独立客厅+卧室的套房格局，儿童主题装饰，配有儿童床、玩具角和小帐篷，全家出行的温馨之选。",
            capacity=4,
            bed_type="1.8m大床 + 1.2m儿童床",
            area="60㎡",
            amenities=["独立客厅", "观景阳台", "地暖", "儿童乐园角", "智能马桶", "浴缸", "茶具套装", "高速WiFi", "迷你吧"],
            images=[
                "https://picsum.photos/seed/yunshang03/800/600",
                "https://picsum.photos/seed/yunshang03b/800/600",
            ],
            view_type="云海",
            is_available=True,
            sort_order=3,
        ),
        Room(
            name="云顶·观景套房",
            room_type="套房",
            price=1288,
            original_price=1688,
            description="位于顶层，270°全景落地窗，躺在床上即可看日出云海。独立起居室+茶室，配高端茶具和香道用品。",
            capacity=2,
            bed_type="2.0m帝王大床",
            area="75㎡",
            amenities=["270°全景窗", "独立茶室", "观景阳台", "地暖", "香道用品", "高端茶具", "智能马桶", "双人浴缸", "高速WiFi", "迷你吧"],
            images=[
                "https://picsum.photos/seed/yunshang04/800/600",
                "https://picsum.photos/seed/yunshang04b/800/600",
            ],
            view_type="云海",
            is_available=True,
            sort_order=4,
        ),
        Room(
            name="竹韵·庭院房",
            room_type="大床房",
            price=788,
            original_price=988,
            description="自带私密竹院，在竹林掩映中品茶读书。日式简约设计，榻榻米茶座，感受庐山的禅意时光。",
            capacity=2,
            bed_type="1.8m大床",
            area="42㎡",
            amenities=["私密竹院", "榻榻米茶座", "地暖", "日式浴缸", "茶具套装", "香薰机", "高速WiFi", "迷你吧"],
            images=[
                "https://picsum.photos/seed/yunshang05/800/600",
                "https://picsum.photos/seed/yunshang05b/800/600",
            ],
            view_type="竹林",
            is_available=True,
            sort_order=5,
        ),
        Room(
            name="归心·豪华家庭套房",
            room_type="套房",
            price=1588,
            original_price=2088,
            description="两室两厅超大空间，主卧配观景阳台，次卧为双床儿童房。客厅有投影影院和壁炉，三代同堂的理想居所。",
            capacity=6,
            bed_type="1.8m大床 + 1.5m双床",
            area="95㎡",
            amenities=["两室两厅", "观景阳台", "投影影院", "壁炉", "地暖", "儿童房", "双卫", "浴缸", "厨房", "高速WiFi"],
            images=[
                "https://picsum.photos/seed/yunshang06/800/600",
            ],
            view_type="山景",
            is_available=True,
            sort_order=6,
        ),
    ]
    db.add_all(rooms)


def seed_menu(db):
    """菜单数据"""
    # 分类
    categories = [
        MenuCategory(name="庐山本味", icon="🏔️", sort_order=1),
        MenuCategory(name="清爽小菜", icon="🥒", sort_order=2),
        MenuCategory(name="暖心汤羹", icon="🍲", sort_order=3),
        MenuCategory(name="主食面点", icon="🍚", sort_order=4),
        MenuCategory(name="茶饮甜品", icon="🍵", sort_order=5),
        MenuCategory(name="酒水饮料", icon="🍶", sort_order=6),
    ]
    db.add_all(categories)
    db.flush()

    # 菜品
    items = [
        # 庐山本味
        MenuItem(category_id=1, name="庐山石鸡", price=128, description="庐山特产石鸡，红烧烹制，肉质鲜嫩", is_recommended=True, sort_order=1),
        MenuItem(category_id=1, name="庐山云雾笋", price=68, description="高山云雾笋尖，清炒保留原味", is_recommended=True, sort_order=2),
        MenuItem(category_id=1, name="九江茶饼蒸肉", price=88, description="九江传统茶饼配五花肉，茶香肉嫩", sort_order=3),
        MenuItem(category_id=1, name="庐山豆腐煲", price=58, description="庐山山泉水豆腐，文火慢炖", sort_order=4),
        MenuItem(category_id=1, name="鄱阳湖银鱼煎蛋", price=48, description="鄱阳湖鲜银鱼配土鸡蛋", sort_order=5),
        MenuItem(category_id=1, name="庐山石耳炖鸡", price=168, description="庐山特产石耳与土鸡同炖，滋补养颜", is_recommended=True, sort_order=6),
        MenuItem(category_id=1, name="山珍野菌煲", price=98, description="庐山野生菌菇，砂锅慢煲", sort_order=7),

        # 清爽小菜
        MenuItem(category_id=2, name="庐山泉水泡菜", price=28, description="山泉水腌制时蔬，清脆爽口", sort_order=1),
        MenuItem(category_id=2, name="蒜泥白肉", price=38, description="薄切五花配蒜泥酱汁", sort_order=2),
        MenuItem(category_id=2, name="凉拌云耳", price=32, description="庐山野生木耳凉拌", sort_order=3),
        MenuItem(category_id=2, name="糖渍桂花藕", price=28, description="桂花时节采摘，蜜渍脆藕", sort_order=4),
        MenuItem(category_id=2, name="山椒拌笋尖", price=35, description="嫩笋尖配自制山椒酱", sort_order=5),

        # 暖心汤羹
        MenuItem(category_id=3, name="庐山云雾茶羹", price=38, description="高山云雾茶入羹，清雅回甘", is_recommended=True, sort_order=1),
        MenuItem(category_id=3, name="瓦罐土鸡汤", price=88, description="庐山走地鸡，瓦罐慢煨4小时", sort_order=2),
        MenuItem(category_id=3, name="野菌豆腐汤", price=42, description="山菌与泉水豆腐同煮", sort_order=3),

        # 主食面点
        MenuItem(category_id=4, name="九江炒粉", price=32, description="九江地道炒粉，镬气十足", sort_order=1),
        MenuItem(category_id=4, name="庐山笋干肉丝面", price=38, description="自制面条配笋干肉丝汤底", sort_order=2),
        MenuItem(category_id=4, name="农家柴火饭", price=22, description="土灶柴火煮饭，配时蔬", sort_order=3),
        MenuItem(category_id=4, name="桂花米糕", price=28, description="手打米浆蒸制，桂花点缀", sort_order=4),
        MenuItem(category_id=4, name="山泉煮粥", price=18, description="庐山泉水配新米慢熬", sort_order=5),

        # 茶饮甜品
        MenuItem(category_id=5, name="庐山云雾茶（一壶）", price=88, description="明前特级云雾茶，配茶点", is_recommended=True, sort_order=1),
        MenuItem(category_id=5, name="手工桂花糕", price=32, description="秋季手采桂花，古法蒸制", sort_order=2),
        MenuItem(category_id=5, name="庐山茶冻", price=28, description="云雾茶汤冷凝，清凉消暑", sort_order=3),
        MenuItem(category_id=5, name="桂花酒酿圆子", price=26, description="甜酒酿配手搓糯米圆子", sort_order=4),
        MenuItem(category_id=5, name="山泉冰粉", price=22, description="庐山泉水手搓冰粉，红糖配", sort_order=5),

        # 酒水饮料
        MenuItem(category_id=6, name="庐山啤酒", price=15, description="九江本地精酿", sort_order=1),
        MenuItem(category_id=6, name="九江陈年封缸酒", price=68, description="九江传统黄酒，醇厚甘甜", sort_order=2),
        MenuItem(category_id=6, name="鲜榨山果汁", price=28, description="时令山果鲜榨", sort_order=3),
        MenuItem(category_id=6, name="山泉柠檬水", price=18, description="庐山泉水配鲜柠檬", sort_order=4),
    ]
    db.add_all(items)


def seed_services(db):
    """快捷服务数据"""
    services = [
        # 客房服务
        QuickService(name="续住办理", description="延长入住时间，无需换房", icon="🔑", category="housekeeping", estimated_time="即刻办理", sort_order=1),
        QuickService(name="房间打扫", description="全面清洁房间，更换床品毛巾", icon="🧹", category="housekeeping", estimated_time="约30分钟", sort_order=2),
        QuickService(name="补充用品", description="补充洗漱用品、茶包、矿泉水等", icon="🧴", category="housekeeping", estimated_time="约10分钟", sort_order=3),
        QuickService(name="加床服务", description="增加一张单人床及配套床品", icon="🛏️", category="housekeeping", estimated_time="约20分钟", sort_order=4),
        QuickService(name="送餐到房", description="将餐点送至您的房间", icon="🍽️", category="housekeeping", estimated_time="约30分钟", sort_order=5),
        QuickService(name="衣物送洗", description="洗衣、烘干、熨烫服务", icon="👔", category="housekeeping", estimated_time="次日取", sort_order=6),

        # 设施维修
        QuickService(name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=1),
        QuickService(name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=2),
        QuickService(name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=3),

        # 前台服务
        QuickService(name="叫醒服务", description="设定叫醒时间，准时电话提醒", icon="⏰", category="frontdesk", estimated_time="准时执行", sort_order=1),
        QuickService(name="行李寄存", description="退房后免费寄存行李", icon="🧳", category="frontdesk", estimated_time="即刻办理", sort_order=2),
        QuickService(name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟到达", sort_order=3),
        QuickService(name="旅游咨询", description="庐山景点介绍、路线规划、门票预订", icon="🗺️", category="frontdesk", estimated_time="即刻咨询", sort_order=4),
        QuickService(name="退房办理", description="快速退房，账单结算", icon="🏃", category="frontdesk", estimated_time="约5分钟", sort_order=5),
    ]
    db.add_all(services)


def seed_travel_routes(db):
    """旅游路线数据"""
    routes = [
        TravelRoute(
            name="经典一日游：庐山精华线",
            description="适合首次来庐山的游客，打卡最具代表性的景点，感受庐山的雄奇秀险。",
            duration="1天（约6-8小时）",
            difficulty="easy",
            spots=[
                {"name": "含鄱口", "description": "庐山最佳日出观景点，远眺鄱阳湖，云海壮观"},
                {"name": "五老峰", "description": "庐山标志性山峰，五峰并列如五位老人"},
                {"name": "三叠泉", "description": "庐山第一瀑布，三级跌落，气势磅礴"},
                {"name": "花径", "description": "白居易笔下'大林寺桃花'所在地"},
                {"name": "如琴湖", "description": "状如提琴的秀美湖泊"},
            ],
            tips="建议7:00出发看日出，穿舒适运动鞋，带防晒和雨具（山上天气多变）",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇起点",
            is_recommended=True,
            sort_order=1,
        ),
        TravelRoute(
            name="深度两日游：庐山全景探秘",
            description="慢节奏深度体验，涵盖自然风光、人文历史和山居生活。适合住1-2晚的旅客。",
            duration="2天",
            difficulty="medium",
            spots=[
                {"name": "DAY1: 牯岭镇-花径-仙人洞-大天池-龙首崖", "description": "上午漫步牯岭镇，下午探索西线自然奇观"},
                {"name": "DAY1夜: 牯岭镇正街", "description": "品尝庐山特色美食，逛文创小店"},
                {"name": "DAY2: 含鄱口日出-五老峰-三叠泉-白鹿洞书院", "description": "早起看日出，打卡东线经典，下午感受千年书院文化"},
            ],
            tips="建议住1晚，第二天早起看日出。山上早晚温差大，带外套。三叠泉需一定体力，可乘缆车。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇起点",
            is_recommended=True,
            sort_order=2,
        ),
        TravelRoute(
            name="文化之旅：庐山人文寻踪",
            description="探访庐山深厚的文化底蕴，白鹿洞书院、东林寺、美庐别墅……感受千年文脉。",
            duration="1天",
            difficulty="easy",
            spots=[
                {"name": "白鹿洞书院", "description": "中国四大书院之首，朱熹讲学之地"},
                {"name": "东林寺", "description": "净土宗祖庭，千年古刹"},
                {"name": "美庐别墅", "description": "蒋宋庐山避暑官邸，见证近代历史"},
                {"name": "庐山会议旧址", "description": "近代中国重要历史见证地"},
                {"name": "庐山博物馆", "description": "了解庐山地质、文化、历史"},
            ],
            tips="白鹿洞书院和东林寺在山下，建议单独安排一天。美庐别墅和会议旧址在牯岭镇附近，步行可达。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇",
            sort_order=3,
        ),
        TravelRoute(
            name="徒步挑战：庐山穿越线",
            description="从好汉坡徒步登顶，适合户外爱好者和徒步玩家，全程约15公里。",
            duration="1天（约6-8小时徒步）",
            difficulty="hard",
            spots=[
                {"name": "好汉坡起点", "description": "从莲花洞出发，开始登顶之旅"},
                {"name": "半山亭", "description": "中途休息点，可补水"},
                {"name": "牯岭镇", "description": "登顶终点，在镇上庆祝"},
            ],
            tips="需较好体能，穿专业登山鞋，带足水和干粮。建议7:00前出发，避开正午烈日。雨天切勿尝试！",
            map_link="https://uri.amap.com/marker?position=115.9500,29.5300&name=好汉坡起点",
            sort_order=4,
        ),
        TravelRoute(
            name="休闲漫步：牯岭镇半日闲",
            description="适合不想太累的旅客，在牯岭镇周边悠闲漫步，品茶看书，感受山居慢生活。",
            duration="半天（约3-4小时）",
            difficulty="easy",
            spots=[
                {"name": "如琴湖环湖", "description": "绕湖一周约1小时，湖光山色尽收眼底"},
                {"name": "花径公园", "description": "白居易诗碑，四季花木扶疏"},
                {"name": "牯岭正街", "description": "逛小店、品小吃、买特产"},
                {"name": "云上归墅茶室", "description": "回到民宿，泡一壶云雾茶，看云卷云舒"},
            ],
            tips="非常适合到达当天或离开前半天的安排，轻松惬意。",
            map_link="https://uri.amap.com/marker?position=115.9797,29.5568&name=牯岭镇",
            sort_order=5,
        ),
    ]
    db.add_all(routes)


def seed_food_recommends(db):
    """周边美食推荐"""
    foods = [
        FoodRecommend(
            name="庐山老灶人家",
            category="赣菜",
            description="地道九江菜，柴火灶烹饪，门口对联写着'庐山真面目，老灶好味道'",
            address="牯岭镇正街68号",
            map_link="https://uri.amap.com/marker?position=115.9800,29.5570&name=庐山老灶人家",
            price_range="人均 ¥60-100",
            must_try="庐山石鸡、石耳炖鸡、鄱阳湖鱼头",
            is_recommended=True,
            sort_order=1,
        ),
        FoodRecommend(
            name="云雾山房素食",
            category="素食",
            description="东林寺附近的山间素食馆，食材取自自家菜园，禅意十足",
            address="东林寺旁200米",
            map_link="https://uri.amap.com/marker?position=115.9600,29.5400&name=云雾山房素食",
            price_range="人均 ¥40-70",
            must_try="罗汉斋、茶香豆腐、桂花藕粉",
            sort_order=2,
        ),
        FoodRecommend(
            name="牯岭小吃街",
            category="小吃",
            description="牯岭镇正街上的小吃聚集地，各种庐山特色小吃一网打尽",
            address="牯岭镇正街中段",
            map_link="https://uri.amap.com/marker?position=115.9805,29.5572&name=牯岭小吃街",
            price_range="人均 ¥20-50",
            must_try="九江炒粉、庐山茶饼、桂花糕、山泉水豆腐脑",
            is_recommended=True,
            sort_order=3,
        ),
        FoodRecommend(
            name="山居茶寮",
            category="茶馆",
            description="隐藏在竹林中的茶室，可品鉴庐山云雾茶，学习茶道，看云起云落",
            address="牯岭镇环山路12号",
            map_link="https://uri.amap.com/marker?position=115.9780,29.5580&name=山居茶寮",
            price_range="人均 ¥50-100",
            must_try="明前云雾茶、桂花红茶、手工茶点",
            sort_order=4,
        ),
        FoodRecommend(
            name="庐山味道",
            category="赣菜",
            description="牯岭镇上的网红餐厅，装修新中式风格，菜品精致，拍照好看",
            address="牯岭镇正街102号",
            map_link="https://uri.amap.com/marker?position=115.9810,29.5565&name=庐山味道",
            price_range="人均 ¥80-130",
            must_try="云雾茶香虾、石锅豆腐、桂花酒酿",
            sort_order=5,
        ),
        FoodRecommend(
            name="山野人家农家乐",
            category="赣菜",
            description="庐山脚下的农家菜馆，土鸡土鸭现杀现做，野菜新鲜采摘",
            address="庐山北门附近2公里",
            map_link="https://uri.amap.com/marker?position=115.9400,29.5200&name=山野人家",
            price_range="人均 ¥50-80",
            must_try="土鸡汤、腊肉炒笋、清炒野菜",
            sort_order=6,
        ),
    ]
    db.add_all(foods)


if __name__ == "__main__":
    seed_all()
