"""
种子数据 - 云上·归墅民宿和庐山旅游信息
v2：菜单改为咖啡简餐，地址更新为大林沟路27号
初始化数据库时自动填充
"""
from models import SessionLocal, init_db, Room, MenuCategory, MenuItem, QuickService, TravelRoute, FoodRecommend, Booking, AggregatedOrder


def seed_all():
    """初始化数据库并填充种子数据"""
    init_db()
    db = SessionLocal()

    try:
        # 检查是否已初始化（房间数据）
        if db.query(Room).count() > 0:
            print("数据库已有房间数据，仅初始化新增模块")
            seed_orders(db)
            return

        seed_rooms(db)
        seed_menu(db)
        seed_services(db)
        seed_travel_routes(db)
        seed_orders(db)
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
    """房间数据 — 来自携程官方平台（2026.6）"""
    rooms = [
        Room(
            name="特惠单人间",
            room_type="单人间",
            price=388, original_price=488,
            description="紧凑温馨的单人空间，1.5米双人床，独立卫浴。小而精致，独行旅客的实惠之选。",
            capacity=1, bed_type="1.5m双人床", area="15m²",
            amenities=["观景窗", "地暖", "智能马桶", "茶具套装", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang01/800/600"],
            view_type="山景", is_available=True, total_count=1, sort_order=1,
        ),
        Room(
            name="特惠标准间",
            room_type="双床房",
            price=388, original_price=488,
            description="两张1.2米单人床，紧凑实用。适合闺蜜出游或预算有限的结伴旅客。",
            capacity=2, bed_type="2×1.2m单人床", area="15m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi"],
            images=["https://picsum.photos/seed/yunshang02/800/600"],
            view_type="山景", is_available=True, total_count=2, sort_order=2,
        ),
        Room(
            name="知还标准间",
            room_type="双床房",
            price=488, original_price=588,
            description="「云无心以出岫，鸟倦飞而知还」——以民宿命名出处的诗句命名。20m²宽敞双床房，两张1.2米单人床。",
            capacity=2, bed_type="2×1.2m单人床", area="20m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang03/800/600"],
            view_type="山景", is_available=True, total_count=2, sort_order=3,
        ),
        Room(
            name="山野大床房",
            room_type="大床房",
            price=588, original_price=688,
            description="1.8米大床房，推窗见山。简约自然的原木风格，是情侣和独行旅客的热门之选。",
            capacity=2, bed_type="1.8m大床", area="20m²",
            amenities=["观景窗", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi"],
            images=["https://picsum.photos/seed/yunshang04/800/600"],
            view_type="山景", is_available=True, total_count=1, sort_order=4,
        ),
        Room(
            name="清舍·露台大床房",
            room_type="大床房",
            price=788, original_price=888,
            description="自带独立露台，坐看云起云落。35m²宽敞空间，1.8米大床，是民宿最受欢迎的房型之一。",
            capacity=2, bed_type="1.8m大床", area="35m²",
            amenities=["独立露台", "观景阳台", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang05/800/600"],
            view_type="山景/露台", is_available=True, total_count=2, sort_order=5,
        ),
        Room(
            name="山景·精致大床房",
            room_type="大床房",
            price=688, original_price=788,
            description="30m²精致山景房，1.8米大床配全景窗。精心布置的简约现代风格，推窗即漫山青翠。",
            capacity=2, bed_type="1.8m大床", area="30m²",
            amenities=["全景窗", "地暖", "智能马桶", "鹅绒床品", "茶具套装", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang06/800/600"],
            view_type="山景", is_available=True, total_count=1, sort_order=6,
        ),
        Room(
            name="室雅茶香套房",
            room_type="套房",
            price=988, original_price=1188,
            description="30m²套房格局，1.8米大床+1.5米双人床。独立茶室区域，配高端茶具，品庐山云雾茶，闻茶香入眠。",
            capacity=4, bed_type="1.8m大床 + 1.5m双人床", area="30m²",
            amenities=["独立茶室", "观景阳台", "地暖", "智能马桶", "浴缸", "高端茶具", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang07/800/600"],
            view_type="山景", is_available=True, total_count=1, sort_order=7,
        ),
        Room(
            name="田园家庭房",
            room_type="家庭房",
            price=788, original_price=888,
            description="1.8米大床+1.2米单人床，20m²温馨家庭空间。适合三口之家出行，简约舒适的田园风格。",
            capacity=3, bed_type="1.8m大床 + 1.2m单人床", area="20m²",
            amenities=["观景窗", "地暖", "书桌", "茶具套装", "高速WiFi", "迷你吧"],
            images=["https://picsum.photos/seed/yunshang08/800/600"],
            view_type="山景", is_available=True, total_count=1, sort_order=8,
        ),
    ]
    db.add_all(rooms)


def seed_menu(db):
    """咖啡简餐菜单数据（要求5：仅咖啡和简餐，不提供正餐）"""
    categories = [
        MenuCategory(name="精品咖啡", icon="☕", sort_order=1),
        MenuCategory(name="茶饮", icon="🍵", sort_order=2),
        MenuCategory(name="简餐轻食", icon="🥐", sort_order=3),
        MenuCategory(name="甜点", icon="🍰", sort_order=4),
        MenuCategory(name="饮品", icon="🥤", sort_order=5),
    ]
    db.add_all(categories)
    db.flush()

    items = [
        # 精品咖啡
        MenuItem(category_id=1, name="庐山云雾冷萃", price=38, description="高山泉水冷萃12小时，清爽回甘", is_recommended=True, sort_order=1),
        MenuItem(category_id=1, name="手冲单品咖啡", price=42, description="精选埃塞俄比亚耶加雪菲，现场手冲", is_recommended=True, sort_order=2),
        MenuItem(category_id=1, name="意式浓缩", price=22, description="双份浓缩，浓郁醇厚", sort_order=3),
        MenuItem(category_id=1, name="拿铁", price=28, description="经典意式拿铁，可选燕麦奶", sort_order=4),
        MenuItem(category_id=1, name="卡布奇诺", price=28, description="绵密奶泡配浓缩咖啡", sort_order=5),
        MenuItem(category_id=1, name="桂花拿铁", price=32, description="秋季限定，手采桂花入咖", is_recommended=True, sort_order=6),

        # 茶饮
        MenuItem(category_id=2, name="庐山云雾茶（一壶）", price=68, description="明前特级云雾茶，配手工茶点", is_recommended=True, sort_order=1),
        MenuItem(category_id=2, name="桂花红茶", price=38, description="祁门红茶配手采桂花", sort_order=2),
        MenuItem(category_id=2, name="茉莉花茶", price=28, description="福州茉莉花窨制绿茶", sort_order=3),
        MenuItem(category_id=2, name="陈皮普洱", price=35, description="五年陈皮配熟普，暖胃养生", sort_order=4),
        MenuItem(category_id=2, name="蜂蜜柚子茶", price=25, description="自制柚子酱配庐山蜂蜜", sort_order=5),

        # 简餐轻食
        MenuItem(category_id=3, name="牛角包三明治", price=38, description="现烤牛角包夹火腿芝士生菜", is_recommended=True, sort_order=1),
        MenuItem(category_id=3, name="庐山茶香沙拉", price=35, description="高山茶叶入酱，配时蔬坚果", sort_order=2),
        MenuItem(category_id=3, name="意式肉酱面", price=42, description="手工意面配番茄肉酱", sort_order=3),
        MenuItem(category_id=3, name="酸奶水果碗", price=28, description="希腊酸奶配时令山果坚果", sort_order=4),
        MenuItem(category_id=3, name="芝士焗红薯", price=25, description="庐山本地红薯芝士焗烤", sort_order=5),

        # 甜点
        MenuItem(category_id=4, name="手工桂花糕", price=28, description="秋季手采桂花古法蒸制", is_recommended=True, sort_order=1),
        MenuItem(category_id=4, name="提拉米苏", price=35, description="经典意式提拉米苏", sort_order=2),
        MenuItem(category_id=4, name="庐山茶冻", price=22, description="云雾茶汤冷凝，清凉消暑", sort_order=3),
        MenuItem(category_id=4, name="桂花酒酿圆子", price=22, description="甜酒酿配手搓糯米圆子", sort_order=4),

        # 饮品
        MenuItem(category_id=5, name="鲜榨山果汁", price=28, description="时令庐山山果鲜榨", sort_order=1),
        MenuItem(category_id=5, name="山泉柠檬水", price=18, description="庐山泉水配鲜柠檬薄荷", sort_order=2),
        MenuItem(category_id=5, name="手工酸奶", price=22, description="自制发酵酸奶，可选蜂蜜", sort_order=3),
        MenuItem(category_id=5, name="气泡水", price=15, description="巴黎水/圣培露", sort_order=4),
    ]
    db.add_all(items)


def seed_services(db):
    """快捷服务数据"""
    services = [
        # 客房服务
        QuickService(name="续住办理", description="延长入住时间，无需换房", icon="🔑", category="housekeeping", estimated_time="即刻办理", sort_order=1),
        QuickService(name="房间打扫", description="全面清洁房间，更换床品毛巾", icon="🧹", category="housekeeping", estimated_time="约30分钟", sort_order=2),
        QuickService(name="补充用品", description="补充洗漱用品、茶包、矿泉水等", icon="🧴", category="housekeeping", estimated_time="约10分钟", sort_order=3),
        QuickService(name="送餐到房", description="将餐点送至您的房间", icon="🍽️", category="housekeeping", estimated_time="约30分钟", sort_order=5),
        QuickService(name="衣物送洗", description="洗衣、烘干、熨烫服务", icon="👔", category="housekeeping", estimated_time="次日取", sort_order=6),

        # 设施维修
        QuickService(name="设施报修", description="房间设施故障报修处理", icon="🔧", category="maintenance", estimated_time="尽快处理", sort_order=1),
        QuickService(name="空调调节", description="空调温度调节或故障处理", icon="❄️", category="maintenance", estimated_time="约15分钟", sort_order=2),
        QuickService(name="热水问题", description="热水器故障或水温调节", icon="🔥", category="maintenance", estimated_time="尽快处理", sort_order=3),

        # 前台服务
        QuickService(name="叫醒服务", description="设定叫醒时间，准时电话提醒", icon="⏰", category="frontdesk", estimated_time="准时执行", sort_order=1),
        QuickService(name="行李寄存", description="退房后免费寄存行李", icon="🧳", category="frontdesk", estimated_time="即刻办理", sort_order=2),
        QuickService(name="免费路线规划", description="老板根据您的偏好定制游玩路线，不收任何费用", icon="🗺️", category="frontdesk", estimated_time="即刻咨询", sort_order=3),
        QuickService(name="叫车服务", description="预约出租车或包车游览庐山", icon="🚕", category="frontdesk", estimated_time="约15分钟到达", sort_order=4),
        QuickService(name="旅游咨询", description="庐山景点介绍、门票预订、天气查询", icon="🏞️", category="frontdesk", estimated_time="即刻咨询", sort_order=5),
        QuickService(name="搭伙用餐", description="可与老板搭伙用餐，品尝家常庐山味道", icon="🍲", category="frontdesk", estimated_time="需提前联系", sort_order=6),
        QuickService(name="退房办理", description="快速退房，账单结算", icon="🏃", category="frontdesk", estimated_time="约5分钟", sort_order=7),
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


if __name__ == "__main__":
    seed_all()
