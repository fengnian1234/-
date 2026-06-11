"""
云上归墅 - 数据模型
使用 SQLAlchemy + SQLite，轻量且方便迁移
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from config import DATABASE_URL, DEBUG


class Base(DeclarativeBase):
    pass


# ── 房间模型 ─────────────────────────────────────────────
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


# ── 菜单模型 ─────────────────────────────────────────────
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
    description = Column(Text, comment="菜品描述")
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


# ── 订单模型 ─────────────────────────────────────────────
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False, comment="微信用户openid")
    room_number = Column(String(50), comment="房间号")
    items = Column(JSON, comment="订单项 [{menu_item_id, name, quantity, price}]")
    total_price = Column(Float, comment="总价")
    status = Column(String(20), default="pending",
                    comment="状态: pending/confirmed/preparing/delivered/completed/cancelled")
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
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


# ── 快捷服务模型 ─────────────────────────────────────────
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


# ── 旅游推荐模型 ─────────────────────────────────────────
class TravelRoute(Base):
    __tablename__ = "travel_routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="路线名称")
    description = Column(Text, comment="路线描述")
    duration = Column(String(50), comment="建议时长")
    difficulty = Column(String(20), comment="难度: easy/medium/hard")
    spots = Column(JSON, comment="景点列表 [{name, description, image}]")
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
    name = Column(String(100), nullable=False, comment="餐厅/美食名称")
    category = Column(String(50), comment="类别: 赣菜/小吃/素食/茶馆")
    description = Column(Text)
    address = Column(String(300))
    map_link = Column(String(500))
    price_range = Column(String(50), comment="人均")
    must_try = Column(String(200), comment="必点菜品")
    image = Column(String(500))
    is_recommended = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "address": self.address,
            "map_link": self.map_link,
            "price_range": self.price_range,
            "must_try": self.must_try,
            "image": self.image,
        }


# ── 消息日志 ─────────────────────────────────────────────
class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False)
    message_type = Column(String(20), comment="消息类型: text/image/voice/event")
    content = Column(Text, comment="用户消息内容")
    reply = Column(Text, comment="自动回复内容")
    created_at = Column(DateTime, default=datetime.utcnow)


# ── 数据库初始化 ─────────────────────────────────────────
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
