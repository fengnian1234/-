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

    print("""
    ╔════════════════════════════════════════╗
    ║    🏔️  云上归墅 · 微信客服系统         ║
    ║    YunShang GuiShu · Lushan            ║
    ╚════════════════════════════════════════╝
    """)

    # 初始化数据库
    init_app()

    # 启动服务
    print("\n✨ 服务启动中...")
    print(f"   📱 H5页面: http://127.0.0.1:5000")
    print(f"   🏠 房型展示: http://127.0.0.1:5000/rooms")
    print(f"   ☕ 咖啡简餐: http://127.0.0.1:5000/menu")
    print(f"   🗺️ 游玩攻略: http://127.0.0.1:5000/travel")
    print(f"   🛎️ 快捷服务: http://127.0.0.1:5000/services")
    print(f"   📍 位置导航: http://127.0.0.1:5000/map")
    print(f"   📡 微信接入: http://你的域名/wechat")
    print()

    app.run(host="0.0.0.0", port=5000, debug=True)
