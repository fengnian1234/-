"""
云上·归墅 - 数据模型
使用 SQLAlchemy + SQLite，轻量且方便迁移
"""
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from config import DATABASE_URL, DB_TYPE, DB_POOL_SIZE, DB_POOL_OVERFLOW, DEBUG, REVIEW_REMINDER_DELAY_MINUTES


class Base(DeclarativeBase):
    pass


# ══════════════════════════════════════════════════════════
#  房间模型
# ══════════════════════════════════════════════════════════
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="房间名称")
    room_type = Column(String(50), nullable=False, comment="房型: 大床房/双床房/套房/亲子房")
    price = Column(Float, nullable=False, comment="价格(元/晚)")
    original_price = Column(Float, comment="原价")
    description = Column(Text, comment="房间描述")
    capacity = Column(Integer, default=2, comment="可住人数")
    bed_type = Column(String(100), comment="床型")
    area = Column(String(50), comment="面积")
    amenities = Column(JSON, comment="设施列表")
    images = Column(JSON, comment="房间图片URL列表")
    view_type = Column(String(100), comment="景观类型: 山景/云海/竹林")
    is_available = Column(Boolean, default=True, comment="是否可订")
    total_count = Column(Integer, default=1, comment="该房型总间数")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "room_type": self.room_type,
            "price": self.price,
            "original_price": self.original_price,
            "description": self.description,
            "capacity": self.capacity,
            "bed_type": self.bed_type,
            "area": self.area,
            "amenities": self.amenities or [],
            "images": self.images or [],
            "view_type": self.view_type,
            "is_available": self.is_available,
            "total_count": self.total_count or 1,
        }


# ══════════════════════════════════════════════════════════
#  预订验证模型（要求1：AI仅在预订确认后解锁）
# ══════════════════════════════════════════════════════════
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    openid = Column(String(100), nullable=False, comment="微信用户openid（预订者）")
    guest_name = Column(String(50), comment="客人姓名")
    phone = Column(String(20), comment="联系电话")
    room_type = Column(String(50), comment="预订房型")
    platform = Column(String(30), comment="预订来源平台: 携程/美团/飞猪/大众点评")
    check_in_date = Column(String(30), comment="入住日期")
    check_out_date = Column(String(30), comment="退房日期")
    room_number = Column(String(20), comment="分配的房号")
    room_code = Column(String(12), unique=True, comment="房间共享码（同住人凭此码绑定AI）")
    status = Column(String(20), default="pending",
                    comment="状态: pending→confirmed→checked_in→checked_out→completed")
    ai_enabled = Column(Boolean, default=False, comment="AI对话是否解锁（确认预订后开启）")
    checked_out_at = Column(DateTime, comment="退房时间（用于计算30分钟后推送好评）")
    review_sent = Column(Boolean, default=False, comment="是否已推送好评提醒")
    review_sent_at = Column(DateTime, comment="好评推送时间")
    review_platform = Column(String(30), comment="推送好评的平台")
    notes = Column(Text, comment="内部备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_pii: bool = True):
        """序列化预订。include_pii=False 时隐藏手机号/openid（客人端使用）"""
        d = {
            "id": self.id,
            "openid": self.openid if include_pii else "***",
            "guest_name": self.guest_name,
            "phone": self.phone if include_pii else "***",
            "room_type": self.room_type,
            "platform": self.platform,
            "check_in_date": self.check_in_date,
            "check_out_date": self.check_out_date,
            "room_number": self.room_number,
            "status": self.status,
            "ai_enabled": self.ai_enabled,
            "room_code": self.room_code,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }

    def is_checked_out_recently(self):
        """是否刚退房且在30分钟提醒窗口内"""
        if not self.checked_out_at or self.review_sent:
            return False
        now = datetime.utcnow()
        trigger_time = self.checked_out_at + timedelta(minutes=REVIEW_REMINDER_DELAY_MINUTES)
        return now >= trigger_time


# ══════════════════════════════════════════════════════════
#  同住人模型（房间码共享机制）
# ══════════════════════════════════════════════════════════
class RoomGuest(Base):
    """同住人 — 通过房间码绑定，共享 AI 管家全部权限"""
    __tablename__ = "room_guests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_code = Column(String(12), nullable=False, index=True, comment="房间共享码")
    openid = Column(String(100), nullable=False, comment="合住人微信openid")
    guest_name = Column(String(50), comment="合住人称呼")
    relation = Column(String(30), default="同住", comment="关系: 家人/朋友/伴侣/同住")
    is_active = Column(Boolean, default=True, comment="是否仍有效")
    bound_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "room_code": self.room_code,
            "openid": self.openid,
            "guest_name": self.guest_name,
            "relation": self.relation,
            "bound_at": self.bound_at.strftime("%Y-%m-%d %H:%M") if self.bound_at else None,
        }


# ══════════════════════════════════════════════════════════
#  菜单模型（要求5：仅咖啡和简餐，支持微信支付）
# ══════════════════════════════════════════════════════════
class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(10), comment="图标emoji")
    sort_order = Column(Integer, default=0)
    items = relationship("MenuItem", back_populates="category", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "items": [item.to_dict() for item in self.items if item.is_available],
        }


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="菜品名称")
    price = Column(Float, nullable=False)
    description = Column(Text, comment="描述")
    image = Column(String(500), comment="图片URL")
    is_available = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False, comment="是否推荐")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("MenuCategory", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image": self.image,
            "is_recommended": self.is_recommended,
        }


# ── 订单（增加微信支付字段）────────────────────────────────
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    openid = Column(String(100), nullable=False, comment="微信用户openid")
    room_number = Column(String(50), comment="房间号")
    items = Column(JSON, comment="订单项 [{menu_item_id, name, quantity, price}]")
    total_price = Column(Float, comment="总价（元）")
    status = Column(String(20), default="pending",
                    comment="pending/paid/preparing/delivered/completed/cancelled")
    pay_status = Column(String(20), default="unpaid", comment="支付状态: unpaid/paid/refunded")
    wechat_order_id = Column(String(64), comment="微信支付订单号")
    wechat_transaction_id = Column(String(64), comment="微信支付交易号")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "room_number": self.room_number,
            "items": self.items or [],
            "total_price": self.total_price,
            "status": self.status,
            "pay_status": self.pay_status,
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════
#  服务请求通知模型（要求2：醒目有效的员工通知）
# ══════════════════════════════════════════════════════════
class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    openid = Column(String(100), nullable=False, comment="微信用户openid")
    service_name = Column(String(50), nullable=False, comment="服务名称")
    room_number = Column(String(50), comment="房号")
    urgency = Column(String(20), default="normal", comment="紧急程度: normal/urgent/emergency")
    status = Column(String(20), default="pending",
                    comment="状态: pending→acknowledged→in_progress→completed")
    handler = Column(String(50), comment="处理人")
    notes = Column(Text, comment="处理备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, comment="确认时间")
    completed_at = Column(DateTime, comment="完成时间")

    def to_dict(self, include_pii: bool = True):
        """序列化预订。include_pii=False 时隐藏手机号/openid（客人端使用）"""
        d = {
            "id": self.id,
            "openid": self.openid if include_pii else "***",
            "service_name": self.service_name,
            "room_number": self.room_number,
            "urgency": self.urgency,
            "status": self.status,
            "handler": self.handler,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%H:%M:%S") if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════
#  快捷服务模型
# ══════════════════════════════════════════════════════════
class QuickService(Base):
    __tablename__ = "quick_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    name = Column(String(50), nullable=False, comment="服务名称")
    description = Column(Text, comment="服务描述")
    icon = Column(String(10), comment="图标emoji")
    category = Column(String(30), comment="分类: housekeeping/maintenance/frontdesk/other")
    estimated_time = Column(String(30), comment="预计时间")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "estimated_time": self.estimated_time,
        }


# ══════════════════════════════════════════════════════════
#  旅游推荐模型
# ══════════════════════════════════════════════════════════
class TravelRoute(Base):
    __tablename__ = "travel_routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="路线名称")
    description = Column(Text, comment="路线描述")
    duration = Column(String(50), comment="建议时长")
    difficulty = Column(String(20), comment="难度: easy/medium/hard")
    spots = Column(JSON, comment="景点列表")
    tips = Column(Text, comment="小贴士")
    map_link = Column(String(500), comment="地图链接")
    is_recommended = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "duration": self.duration,
            "difficulty": self.difficulty,
            "spots": self.spots or [],
            "tips": self.tips,
            "map_link": self.map_link,
            "is_recommended": self.is_recommended,
        }


class FoodRecommend(Base):
    __tablename__ = "food_recommends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    description = Column(Text)
    address = Column(String(300))
    map_link = Column(String(500))
    price_range = Column(String(50))
    must_try = Column(String(200))
    image = Column(String(500))
    images = Column(JSON, comment="多图列表（XHS风格图文展示）")
    detail_content = Column(Text, comment="XHS风格长文描述（含emoji、分段）")
    tags = Column(JSON, comment="标签列表如 #庐山美食 #必打卡")
    is_recommended = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "description": self.description, "address": self.address,
            "map_link": self.map_link, "price_range": self.price_range,
            "must_try": self.must_try, "image": self.image,
            "images": self.images or [],
            "detail_content": self.detail_content or "",
            "tags": self.tags or [],
        }


# ══════════════════════════════════════════════════════════
#  平台监控模型（要求6：收集主流平台民宿信息）
# ══════════════════════════════════════════════════════════
class PlatformMention(Base):
    __tablename__ = "platform_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    platform = Column(String(30), nullable=False, comment="来源平台")
    mention_type = Column(String(20), comment="类型: review/note/post/rating")
    title = Column(String(300), comment="标题")
    content = Column(Text, comment="内容摘要")
    rating = Column(Float, comment="评分")
    author = Column(String(100), comment="发布者")
    url = Column(String(500), comment="原始链接")
    sentiment = Column(String(20), comment="情感: positive/neutral/negative")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    collected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, comment="原始发布时间")

    def to_dict(self):
        return {
            "id": self.id, "platform": self.platform,
            "mention_type": self.mention_type, "title": self.title,
            "content": self.content, "rating": self.rating,
            "author": self.author, "url": self.url,
            "sentiment": self.sentiment,
            "collected_at": self.collected_at.strftime("%Y-%m-%d") if self.collected_at else None,
        }


# ══════════════════════════════════════════════════════════
#  消息日志
# ══════════════════════════════════════════════════════════
class MessageLog(Base):
    """消息日志 — 预留：微信消息记录（Phase 3 接入微信客服消息API后启用）"""
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False)
    message_type = Column(String(20))
    content = Column(Text)
    reply = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════════════════
#  数据库初始化（兼容 SQLite 和 PostgreSQL）
# ══════════════════════════════════════════════════════════
_engine_kwargs = {"echo": DEBUG}
if DB_TYPE == "postgresql":
    _engine_kwargs.update({
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_POOL_OVERFLOW,
        "pool_pre_ping": True,       # 连接前检测可用性
        "pool_recycle": 3600,        # 每小时回收连接
    })
elif DB_TYPE == "sqlite":
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine)


# ══════════════════════════════════════════════════════════
#  积分体系模型
# ══════════════════════════════════════════════════════════
class GuestPoints(Base):
    __tablename__ = "guest_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(200), unique=True, nullable=False, index=True, comment="微信OpenID")
    total_points = Column(Integer, default=0, comment="当前总积分")
    total_earned = Column(Integer, default=0, comment="累计获取积分")
    total_spent = Column(Integer, default=0, comment="累计消费积分")
    membership = Column(String(20), default="silver", comment="会员等级: silver/gold/diamond")
    birthday_month = Column(Integer, comment="生日月份(1-12)，激活当月积分1.5倍")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_pii: bool = True):
        """序列化预订。include_pii=False 时隐藏手机号/openid（客人端使用）"""
        d = {
            "id": self.id,
            "openid": self.openid if include_pii else "***",
            "total_points": self.total_points,
            "total_earned": self.total_earned,
            "total_spent": self.total_spent,
            "membership": self.membership,
            "membership_name": {"silver": "银卡", "gold": "金卡", "diamond": "钻石卡"}.get(self.membership, "银卡"),
            "discount": {"silver": 0.95, "gold": 0.92, "diamond": 0.90}.get(self.membership, 0.95),
            "birthday_month": self.birthday_month,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PointLog(Base):
    __tablename__ = "point_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(200), nullable=False, index=True, comment="微信OpenID")
    points = Column(Integer, nullable=False, comment="积分变动(+入/-出)")
    action = Column(String(50), nullable=False, comment="行为: earn_checkin/earn_booking/earn_review/earn_share/earn_birthday/redeem_coffee/redeem_upgrade/redeem_late/redeem_coupon")
    description = Column(String(200), comment="积分变动说明")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self, include_pii: bool = True):
        """序列化预订。include_pii=False 时隐藏手机号/openid（客人端使用）"""
        d = {
            "id": self.id,
            "openid": self.openid if include_pii else "***",
            "points": self.points,
            "action": self.action,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── 积分兑换商品定义 ──────────────────────────────────────
REDEEM_ITEMS = {
    "coffee":    {"name": "☕ 三山二水精品咖啡1杯", "points": 300, "type": "redeem_coffee"},
    "upgrade":   {"name": "🏠 房型免费升级（视空房）", "points": 500, "type": "redeem_upgrade"},
    "late":      {"name": "⏰ 延迟退房至14:00",       "points": 300, "type": "redeem_late"},
    "coupon50":  {"name": "🎫 房费抵扣券 ¥50",       "points": 500, "type": "redeem_coupon"},
}

# ── 积分获取规则 ──────────────────────────────────────────
EARN_RULES = {
    "booking":     {"name": "入住消费",       "points": 1,   "unit": "每消费¥1得1分"},
    "checkin":     {"name": "每日签到",       "points": 1,   "unit": "每天签到+1分"},
    "review":      {"name": "写订单平台评价", "points": 80,  "unit": "携程/美团/飞猪/大众点评写评价+80分（截图发前台）"},
    "share":       {"name": "邀请好友预订",   "points": 100, "unit": "好友通过分享首次入住+100分"},
    "birthday":    {"name": "生日当月积分×1.5","points": 0,  "unit": "生日当月所有积分获取享1.5倍（联系前台登记生日月份）"},
    "xhs_note":    {"name": "小红书笔记",     "points": 80,  "unit": "带图发笔记+80分"},
    "social_post": {"name": "朋友圈打卡",     "points": 30,  "unit": "定位+民宿图片发朋友圈+30分（截图发前台）"},
}

# ── 会员等级 ──────────────────────────────────────────────
MEMBERSHIP_TIERS = {
    "silver":  {"name": "银卡", "min_points": 0,     "discount": 0.95},
    "gold":    {"name": "金卡", "min_points": 3000,  "discount": 0.92, "perk": "免费延迟退房"},
    "diamond": {"name": "钻石卡","min_points": 8000, "discount": 0.90, "perk": "免费升级+专属管家"},
}


# ══════════════════════════════════════════════════════════
#  多平台订单聚合模型
# ══════════════════════════════════════════════════════════
class AggregatedOrder(Base):
    __tablename__ = "aggregated_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="guishu", index=True, comment="所属民宿")
    platform = Column(String(30), nullable=False, comment="平台: ctrip/meituan/fliggy/dianping/direct/xiaohongshu/douyin")
    platform_order_id = Column(String(100), comment="平台订单号")
    guest_name = Column(String(50), nullable=False, comment="客人姓名")
    guest_phone = Column(String(20), comment="客人电话")
    room_type = Column(String(100), comment="房型")
    room_number = Column(String(20), comment="房间号（入住后分配）")
    check_in = Column(String(20), nullable=False, comment="入住日期")
    check_out = Column(String(20), nullable=False, comment="退房日期")
    nights = Column(Integer, default=1, comment="入住晚数")
    total_amount = Column(Float, comment="订单金额")
    platform_fee = Column(Float, default=0, comment="平台佣金")
    net_revenue = Column(Float, comment="实际收入(金额-佣金)")
    guest_count = Column(Integer, default=1, comment="入住人数")
    status = Column(String(20), default="confirmed", comment="confirmed/checked_in/checked_out/cancelled")
    remark = Column(String(500), comment="备注")
    source = Column(String(20), default="manual", comment="录入方式: manual/api/import")
    synced_at = Column(DateTime, comment="最后同步时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        platform_icons = {"ctrip":"🏨","meituan":"🏠","fliggy":"✈️","dianping":"⭐","direct":"📞","xiaohongshu":"📕","douyin":"🎵"}
        return {
            "id": self.id,
            "platform": self.platform,
            "platform_icon": platform_icons.get(self.platform, "📋"),
            "platform_order_id": self.platform_order_id,
            "guest_name": self.guest_name,
            "guest_phone": self.guest_phone,
            "room_type": self.room_type,
            "room_number": self.room_number,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "nights": self.nights,
            "total_amount": self.total_amount,
            "platform_fee": self.platform_fee,
            "net_revenue": self.net_revenue,
            "guest_count": self.guest_count,
            "status": self.status,
            "status_label": {"confirmed":"已确认","checked_in":"已入住","checked_out":"已退房","cancelled":"已取消"}.get(self.status, self.status),
            "remark": self.remark,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════
#  民宿配置模型
# ══════════════════════════════════════════════════════════
class Bnb(Base):
    __tablename__ = "bnbs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), unique=True, nullable=False, index=True, comment="标识: guishu/shanji/donglinwai")
    name = Column(String(100), nullable=False, comment="民宿全称")
    short_name = Column(String(50), comment="简称")
    address = Column(String(300), comment="地址")
    phone = Column(String(20), comment="联系电话")
    latitude = Column(Float, comment="纬度")
    longitude = Column(Float, comment="经度")
    description = Column(Text, comment="民宿简介")
    theme_color = Column(String(10), comment="主题色")
    wechat_token = Column(String(100), comment="微信Token")
    wechat_app_id = Column(String(50), comment="公众号AppID")
    wechat_app_secret = Column(String(100), comment="公众号AppSecret")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "bnb_id": self.bnb_id,
            "name": self.name,
            "short_name": self.short_name,
            "address": self.address,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "theme_color": self.theme_color,
            "is_active": self.is_active,
        }


# ══════════════════════════════════════════════════════════
#  茶园模块（云上·山纪专属）
# ══════════════════════════════════════════════════════════
class TeaType(Base):
    """茶叶品类"""
    __tablename__ = "tea_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="shanji", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="茶叶名称")
    description = Column(Text, comment="描述")
    origin = Column(String(100), comment="产地")
    brewing_method = Column(Text, comment="冲泡方法")
    tasting_notes = Column(Text, comment="品鉴笔记")
    image = Column(String(500), comment="图片URL")
    images = Column(JSON, comment="多图")
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnbs_id": self.bnb_id,
            "name": self.name,
            "description": self.description,
            "origin": self.origin,
            "brewing_method": self.brewing_method,
            "tasting_notes": self.tasting_notes,
            "image": self.image,
            "images": self.images or [],
        }


class TeaExperience(Base):
    """茶园体验项目"""
    __tablename__ = "tea_experiences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="shanji", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="体验名称")
    description = Column(Text, comment="描述")
    duration = Column(String(50), comment="时长")
    price = Column(Float, comment="价格")
    capacity = Column(Integer, default=10, comment="容量")
    includes = Column(JSON, comment="包含项目")
    images = Column(JSON, comment="图片")
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "name": self.name,
            "description": self.description,
            "duration": self.duration,
            "price": self.price,
            "capacity": self.capacity,
            "includes": self.includes or [],
            "images": self.images or [],
            "is_available": self.is_available,
        }


class TeaProduct(Base):
    """茶叶商城商品"""
    __tablename__ = "tea_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="shanji", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="商品名称")
    tea_type_id = Column(Integer, ForeignKey("tea_types.id"), comment="茶叶品类")
    price = Column(Float, comment="价格")
    weight = Column(String(30), comment="规格")
    description = Column(Text, comment="描述")
    stock = Column(Integer, default=0, comment="库存")
    images = Column(JSON, comment="图片")
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "name": self.name,
            "tea_type_id": self.tea_type_id,
            "price": self.price,
            "weight": self.weight,
            "description": self.description,
            "stock": self.stock,
            "images": self.images or [],
            "is_available": self.is_available,
        }


# ══════════════════════════════════════════════════════════
#  疗愈模块（云上·东林外专属）
# ══════════════════════════════════════════════════════════
class HealingCourse(Base):
    """疗愈项目（一对一个案服务）"""
    __tablename__ = "healing_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="donglinwai", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="项目名称")
    category = Column(String(30), nullable=False, comment="类别: 音疗疗愈/芳香疗愈/情绪疗愈")
    description = Column(Text, comment="项目描述")
    price_tiers = Column(JSON, comment="阶梯价格 [{duration, price, note}]")
    therapist = Column(String(50), default="琼儿老师", comment="疗愈师")
    images = Column(JSON, comment="图片列表")
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price_tiers": self.price_tiers or [],
            "therapist": self.therapist or "琼儿老师",
            "images": self.images or [],
            "is_available": self.is_available,
        }


class HealingSpa(Base):
    """SPA/身体疗愈"""
    __tablename__ = "healing_spas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="donglinwai", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="SPA名称")
    category = Column(String(30), comment="类别: massage/aromatherapy/hotstone/facial")
    description = Column(Text, comment="描述")
    duration = Column(String(50), comment="时长")
    price = Column(Float, comment="价格")
    therapist = Column(String(50), comment="理疗师")
    includes = Column(JSON, comment="包含项目")
    images = Column(JSON, comment="图片")
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "duration": self.duration,
            "price": self.price,
            "therapist": self.therapist,
            "includes": self.includes or [],
            "images": self.images or [],
            "is_available": self.is_available,
        }


class MeditationSession(Base):
    """禅修/冥想"""
    __tablename__ = "meditation_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="donglinwai", index=True, comment="所属民宿")
    name = Column(String(100), nullable=False, comment="禅修名称")
    type = Column(String(30), comment="类型: sitting/walking/sound/mantra")
    description = Column(Text, comment="描述")
    duration = Column(String(50), comment="时长")
    schedule = Column(String(100), comment="时间安排")
    price = Column(Float, comment="价格")
    guide = Column(String(50), comment="引导师")
    location = Column(String(100), comment="地点")
    images = Column(JSON, comment="图片")
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "duration": self.duration,
            "schedule": self.schedule,
            "price": self.price,
            "guide": self.guide,
            "location": self.location,
            "images": self.images or [],
            "is_available": self.is_available,
        }


class HealingAppointment(Base):
    """疗愈预约记录"""
    __tablename__ = "healing_appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bnb_id = Column(String(20), nullable=False, default="donglinwai", index=True, comment="所属民宿")
    course_id = Column(Integer, nullable=False, comment="疗愈项目ID")
    course_name = Column(String(100), comment="项目名称（冗余）")
    tier_index = Column(Integer, nullable=False, comment="选择的价格档位索引")
    tier_duration = Column(String(30), comment="档位时长（如 1小时）")
    tier_price = Column(Float, comment="档位价格")
    guest_name = Column(String(50), nullable=False, comment="客人姓名")
    guest_phone = Column(String(20), nullable=False, comment="客人手机号")
    guest_openid = Column(String(100), comment="微信openid（公众号来源）")
    appointment_date = Column(String(20), nullable=False, comment="预约日期 YYYY-MM-DD")
    appointment_time = Column(String(10), nullable=False, comment="开始时间 HH:MM")
    duration_minutes = Column(Integer, nullable=False, comment="服务时长（分钟）")
    status = Column(String(20), default="pending", comment="pending/paid/cancelled/completed")
    pay_status = Column(String(20), default="unpaid", comment="unpaid/paid/refunded")
    note = Column(String(200), comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bnb_id": self.bnb_id,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "tier_index": self.tier_index,
            "tier_duration": self.tier_duration,
            "tier_price": self.tier_price,
            "guest_name": self.guest_name,
            "guest_phone": self.guest_phone,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


def init_db():
    """创建所有表"""
    Base.metadata.create_all(engine)
