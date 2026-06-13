#!/usr/bin/env python
"""
云上归墅 - 启动入口
"""
import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app import app, init_app
    from services.logger import info

    info("🏔️ 云上归墅 · 微信客服系统启动中...")

    # 初始化数据库
    init_app()

    # 启动服务
    info("服务启动中...")
    info("H5页面: http://127.0.0.1:5000")
    info("房型: /rooms")
    info("菜单: /menu")
    info("攻略: /travel")
    info("服务: /services")
    info("导航: /map")
    info("微信接入: /wechat")
    from config import DEBUG
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
