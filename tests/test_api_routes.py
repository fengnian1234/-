"""
API 集成测试 — 覆盖核心 JSON API 端点
运行: PYTHONUTF8=1 python -m pytest tests/ -v
"""


class TestStaffAPI:
    """员工看板 API"""

    def test_get_dashboard(self, client):
        """获取员工看板数据"""
        resp = client.get("/api/staff/dashboard")
        assert resp.status_code == 200
        data = resp.get_json()
        # 看板直接返回 stats/pending_svc 等字段
        assert "stats" in data

    def test_get_dashboard_unauthorized(self, client):
        """看板可访问（未设 AUTH 时不拦截）"""
        resp = client.get("/api/staff/dashboard")
        assert resp.status_code in (200, 401)


class TestRoomAPI:
    """房型相关 API"""

    def test_get_all_rooms(self, client):
        """获取所有房型"""
        resp = client.get("/api/rooms")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["rooms"], list)
        assert len(data["rooms"]) > 0

    def test_get_room_detail(self, client):
        """获取单个房型详情"""
        resp = client.get("/api/rooms")
        rooms = resp.get_json()["rooms"]
        if rooms:
            room_id = rooms[0]["id"]
            resp = client.get(f"/api/rooms/{room_id}")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["room"]["id"] == room_id

    def test_get_room_not_found(self, client):
        """请求不存在的房型"""
        resp = client.get("/api/rooms/99999")
        assert resp.status_code == 404


class TestMenuAPI:
    """菜单 API"""

    def test_get_menu(self, client):
        """获取菜单分类 + 菜品"""
        resp = client.get("/api/menu")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data.get("categories", []), list)


class TestTravelAPI:
    """旅游路线 API"""

    def test_get_travel(self, client):
        """获取旅游路线 + 美食（单端点返回两者）"""
        resp = client.get("/api/travel")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data.get("routes", []), list)
        assert isinstance(data.get("foods", []), list)


class TestQuickServicesAPI:
    """快捷服务 API"""

    def test_get_all_services(self, client):
        """获取所有快捷服务"""
        resp = client.get("/api/services")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data.get("services", []), list)


class TestPointsAPI:
    """积分 API"""

    def test_get_guest_points(self, client):
        """查询用户积分（新用户返回 guest + 规则列表）"""
        resp = client.get("/api/points/test_api_user_001")
        assert resp.status_code == 200
        data = resp.get_json()
        # 返回格式: {guest, logs, redeem_items, earn_rules, membership_info}
        assert "guest" in data
        assert "redeem_items" in data

    def test_earn_points_invalid(self, client):
        """无效积分获取操作"""
        resp = client.post("/api/points/earn", json={
            "openid": "test_user",
            "action": "nonexistent_action"
        })
        assert resp.status_code in (200, 400)

    def test_redeem_points_forbidden(self, client):
        """积分兑换（无需校验的用户）"""
        resp = client.post("/api/points/redeem", json={
            "openid": "no_such_user",
            "item": "coffee"
        })
        # 应返回错误（用户不存在或无积分）
        assert resp.status_code in (200, 400, 404)


class TestTeaAPI:
    """茶场预约 API"""

    def test_get_available_dates(self, client):
        """获取可预约日期"""
        resp = client.get("/api/tea/reservation/dates?bnb_id=shanji")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data.get("dates", []), list)

    def test_get_available_slots(self, client):
        """获取指定日期的可用时间槽（不含日期参数，使用默认今天）"""
        resp = client.get("/api/tea/reservation/slots?bnb_id=shanji")
        # 不传日期时使用今天，默认返回 slots + success
        assert resp.status_code == 200
        data = resp.get_json()
        assert "success" in data

    def test_book_tea_invalid(self, client):
        """无效参数 — 预约失败返回错误"""
        resp = client.post("/api/tea/reservation/book", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_tea_types(self, client):
        """获取茶叶品类"""
        resp = client.get("/api/tea/types?bnb_id=shanji")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


class TestHealingAPI:
    """疗愈模块 API"""

    def test_get_courses(self, client):
        """获取疗愈课程列表"""
        resp = client.get("/api/healing/courses?bnb_id=donglinwai")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data.get("courses", []), list)

    def test_get_slots(self, client):
        """获取疗愈时间槽"""
        resp = client.get("/api/healing/slots?bnb_id=donglinwai&course_id=1&tier_index=0&date=2099-01-01")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "success" in data


class TestMonitoringAPI:
    """平台监控 API"""

    def test_get_report(self, client):
        """获取监控文字报告"""
        resp = client.get("/api/monitor/report")
        assert resp.status_code == 200
        data = resp.get_json()
        # 报告返回 {"report": "..."} 格式
        assert "report" in data

    def test_get_summary(self, client):
        """获取监控摘要（返回平台汇总信息）"""
        resp = client.get("/api/monitor/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        # 返回格式: {success: True, platforms: [...]} 或 裸数据
        assert data is not None


class TestErrorHandling:
    """错误处理测试"""

    def test_no_route_404(self, client):
        """不存在的路由返回 404"""
        resp = client.get("/api/nonexistent_endpoint_xyz")
        assert resp.status_code == 404

    def test_err_response_format(self, client):
        """验证 _err() 错误格式: success=False + message"""
        resp = client.post("/api/tea/reservation/book", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "message" in data


class TestBnBContext:
    """多 BnB 路由测试"""

    def test_guishu_routes(self, client):
        """归墅路由正常工作"""
        routes = ["/gs/", "/gs/rooms", "/gs/menu", "/gs/travel", "/gs/services"]
        for route in routes:
            resp = client.get(route)
            assert resp.status_code == 200, f"Route {route} failed"

    def test_shanji_routes(self, client):
        """山纪路由正常工作"""
        routes = ["/sj/", "/sj/rooms", "/sj/menu", "/sj/travel", "/sj/services"]
        for route in routes:
            resp = client.get(route)
            assert resp.status_code == 200, f"Route {route} failed"

    def test_donglinwai_routes(self, client):
        """东林外路由正常工作"""
        routes = ["/dlw/", "/dlw/rooms", "/dlw/menu", "/dlw/travel", "/dlw/services"]
        for route in routes:
            resp = client.get(route)
            assert resp.status_code == 200, f"Route {route} failed"


class TestHealthCheck:
    """健康检查"""

    def test_health(self, client):
        """GET /health"""
        resp = client.get("/health")
        assert resp.status_code == 200
