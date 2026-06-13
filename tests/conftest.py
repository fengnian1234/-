"""
测试配置 + 共享 fixtures
"""
import pytest
import sys
import os

# 确保项目根在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, init_app


@pytest.fixture(scope="session")
def flask_app():
    """创建 Flask 测试应用"""
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "test.local"
    with app.app_context():
        init_app()
    return app


@pytest.fixture
def client(flask_app):
    """Flask 测试客户端"""
    return flask_app.test_client()


@pytest.fixture
def test_openid():
    """测试用 openid"""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}"
