"""
服务层单元测试 — 覆盖全部 services/ 模块
运行: PYTHONUTF8=1 python -m pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRooms:
    """房型服务测试"""

    def test_get_all_rooms(self):
        from services.rooms import get_all_rooms
        rooms = get_all_rooms()
        assert len(rooms) > 0, "至少应有 1 个房型"
        assert "name" in rooms[0]
        assert "price" in rooms[0]

    def test_get_room_by_id(self):
        from services.rooms import get_room_by_id, get_all_rooms
        rooms = get_all_rooms()
        if rooms:
            room = get_room_by_id(rooms[0]["id"])
            assert room is not None
            assert room["name"] == rooms[0]["name"]

    def test_format_rooms_text(self):
        from services.rooms import format_rooms_text
        text = format_rooms_text()
        assert "云上" in text
        assert len(text) > 100

    def test_format_room_detail(self):
        from services.rooms import format_room_detail_text
        text = format_room_detail_text(1)
        assert len(text) > 20


class TestMenu:
    """菜单服务测试"""

    def test_get_menu_categories(self):
        from services.menu import get_menu_categories
        cats = get_menu_categories()
        assert len(cats) > 0, "至少应有 1 个菜单分类"

    def test_format_menu_text(self):
        from services.menu import format_menu_text
        text = format_menu_text()
        assert "三山二水" in text or "咖啡" in text

    def test_get_recommended(self):
        from services.menu import get_recommended_items
        items = get_recommended_items()
        assert isinstance(items, list)


class TestTravel:
    """旅游攻略服务测试"""

    def test_get_all_routes(self):
        from services.travel import get_all_routes
        routes = get_all_routes()
        assert len(routes) > 0, "至少应有 1 条游玩路线"

    def test_get_all_food(self):
        from services.travel import get_all_food_recommends
        foods = get_all_food_recommends()
        assert len(foods) > 0, "至少应有 1 个美食推荐"

    def test_format_routes_text(self):
        from services.travel import format_routes_text
        text = format_routes_text()
        assert len(text) > 50

    def test_format_food_text(self):
        from services.travel import format_food_text
        text = format_food_text()
        assert len(text) > 50

    def test_format_location_text(self):
        from services.travel import format_location_text
        text = format_location_text()
        assert "大林沟路" in text


class TestQuickServices:
    """快捷服务测试"""

    def test_get_all_services(self):
        from services.quick import get_all_services
        svcs = get_all_services()
        assert len(svcs) > 0, "至少应有 1 个快捷服务"

    def test_format_services_text(self):
        from services.quick import format_services_text
        text = format_services_text()
        assert len(text) > 50


class TestBooking:
    """预订管理测试"""

    def test_get_booking_nonexistent(self, test_openid):
        from services.booking import get_booking_by_openid
        b = get_booking_by_openid(test_openid)
        assert b is None, "新用户不应有预订"

    def test_is_ai_disabled(self, test_openid):
        from services.booking import is_ai_enabled
        assert not is_ai_enabled(test_openid)

    def test_is_not_checked_in(self, test_openid):
        from services.booking import is_checked_in
        assert not is_checked_in(test_openid)

    def test_confirm_and_check_flow(self, test_openid):
        from services.booking import confirm_booking, is_ai_enabled, is_checked_in
        from services.booking import check_in_booking, check_out_booking

        # 确认预订
        booking = confirm_booking(
            test_openid, "测试客人", "13800000000",
            "携程", "2026-06-15", "2026-06-17", "山野大床房"
        )
        assert booking is not None
        assert is_ai_enabled(test_openid), "确认预订后 AI 应解锁"
        assert not is_checked_in(test_openid), "确认预订不等于已入住"

        # 入住
        checked_in = check_in_booking(booking.id, "301")
        assert checked_in.status == "checked_in"
        assert is_checked_in(test_openid), "入住后应判定为已入住"

        # 退房
        checked_out = check_out_booking(booking.id)
        assert checked_out.status == "checked_out"

    def test_extend_booking(self, test_openid):
        from services.booking import confirm_booking, check_in_booking, extend_booking

        booking = confirm_booking(
            test_openid, "续住测试", "13900000001",
            "美团", "2026-06-16", "2026-06-18", "云海套房"
        )
        assert booking is not None

        # 入住后延住
        check_in_booking(booking.id, "302")
        result = extend_booking(test_openid, extra_days=2)
        # 注: check_in_booking 的 session 已关闭，extend_booking 开新 session
        # 需要确认 booking 已持久化
        assert result is not None, f"extend_booking 未找到预订 (openid={test_openid}, booking_id={booking.id})"
        assert result["check_out_date"] == "2026-06-20", f"应为06-20，实际{result['check_out_date']}"


class TestPoints:
    """积分体系测试"""

    def test_earn_checkin(self, test_openid):
        from services.points import earn_points, get_guest
        result = earn_points(test_openid, "checkin")
        assert result["success"]

        guest = get_guest(test_openid)
        assert guest["total_points"] >= 1

    def test_get_redeem_items(self):
        from services.points import get_redeem_items
        items = get_redeem_items()
        assert len(items) >= 4

    def test_get_earn_rules(self):
        from services.points import get_earn_rules
        rules = get_earn_rules()
        assert len(rules) > 0


class TestOrders:
    """订单聚合测试"""

    def test_get_platforms(self):
        from services.orders import get_platforms
        plats = get_platforms()
        assert len(plats) >= 5

    def test_add_and_query(self):
        from services.orders import add_order, get_orders
        result = add_order({
            "platform": "ctrip", "guest_name": "测试",
            "check_in": "2026-07-01", "check_out": "2026-07-03",
            "nights": 2, "total_amount": 999.00,
        })
        assert result is not None
        orders = get_orders()
        assert len(orders) > 0


class TestNotify:
    """员工通知测试"""

    def test_create_and_query(self, test_openid):
        from services.notify import create_service_request, get_pending_requests
        result = create_service_request(test_openid, "测试服务", "101")
        assert result is not None

        pending = get_pending_requests()
        assert len(pending) >= 1


class TestAI:
    """AI 服务测试"""

    def test_fallback_when_no_key(self):
        """无 API Key 时返回兜底回复"""
        from services.ai import _fallback_reply
        reply = _fallback_reply()
        assert "智能管家暂时休息" in reply

    def test_get_conversation_mode_unknown(self, test_openid):
        from services.ai import get_conversation_mode
        mode = get_conversation_mode(test_openid)
        assert mode == "travel_advisor", f"未预订用户应为 travel_advisor，实际 {mode}"

    def test_refresh_local_data(self):
        from services.ai import refresh_local_data
        data = refresh_local_data(bnb_id="guishu")
        assert data is not None
        assert len(data) > 0


class TestLogger:
    """日志系统测试"""

    def test_logger_exists(self):
        from services.logger import get_logger, info, warning, error, debug
        logger = get_logger("test")
        assert logger is not None

        # 不应抛异常
        info("测试日志")
        warning("测试警告")
        debug("测试调试")

    def test_log_files_created(self):
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        assert os.path.exists(log_dir), "logs 目录应存在"
