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
from config import DATABASE_URL, DEBUG, REVIEW_REMINDER_DELAY_MINUTES


class Base(DeclarativeBase):
    pass


# ══════════════════════════════════════════════════════════
#  房间模型
# ══════════════════════════════════════════════════════════
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
        }


# ══════════════════════════════════════════════════════════
#  预订验证模型（要求1：AI仅在预订确认后解锁）
# ══════════════════════════════════════════════════════════
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False, comment="微信用户openid")
    guest_name = Column(String(50), comment="客人姓名")
    phone = Column(String(20), comment="联系电话")
    room_type = Column(String(50), comment="预订房型")
    platform = Column(String(30), comment="预订来源平台: 携程/美团/飞猪/大众点评")
    check_in_date = Column(String(30), comment="入住日期")
    check_out_date = Column(String(30), comment="退房日期")
    room_number = Column(String(20), comment="分配的房号")
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

    def to_dict(self):
        return {
            "id": self.id,
            "openid": self.openid,
            "guest_name": self.guest_name,
            "phone": self.phone,
            "room_type": self.room_type,
            "platform": self.platform,
            "check_in_date": self.check_in_date,
            "check_out_date": self.check_out_date,
            "room_number": self.room_number,
            "status": self.status,
            "ai_enabled": self.ai_enabled,
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
#  菜单模型（要求5：仅咖啡和简餐，支持微信支付）
# ══════════════════════════════════════════════════════════
class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    def to_dict(self):
        return {
            "id": self.id,
            "openid": self.openid,
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
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    description = Column(Text)
    address = Column(String(300))
    map_link = Column(String(500))
    price_range = Column(String(50))
    must_try = Column(String(200))
    image = Column(String(500))
    is_recommended = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "description": self.description, "address": self.address,
            "map_link": self.map_link, "price_range": self.price_range,
            "must_try": self.must_try, "image": self.image,
        }


# ══════════════════════════════════════════════════════════
#  平台监控模型（要求6：收集主流平台民宿信息）
# ══════════════════════════════════════════════════════════
class PlatformMention(Base):
    __tablename__ = "platform_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False)
    message_type = Column(String(20))
    content = Column(Text)
    reply = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════════════════
#  数据库初始化
# ══════════════════════════════════════════════════════════
engine = create_engine(DATABASE_URL, echo=DEBUG)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """创建所有表"""
    Base.metadata.create_all(engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
