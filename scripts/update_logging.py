# ⚠️ 安全警告: 此脚本会原地修改项目源文件。仅限开发环境使用，生产环境请删除 scripts/ 目录。
"""批量更新日志系统、异常处理、MessageLog"""
import os

BASE = 'd:/cc'

# ═══════════════════════════════════════════
# 1. app.py
# ═══════════════════════════════════════════
with open(f'{BASE}/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "from flask import Flask, request, jsonify, render_template, abort",
    "from flask import Flask, request, jsonify, render_template, abort\n"
    "from services.logger import info, warning, error as log_error, debug, log_ai, log_keyword, log_booking"
)

content = content.replace('print("✅ 新增模块数据补充完成！")', 'info("新增模块数据补充完成")')
content = content.replace('print("🏔️ 云上归墅 · 微信客服系统已启动")', 'info("云上归墅 · 微信客服系统已启动")')
content = content.replace('print("💡 当前使用 SQLite 数据库")', 'info("当前使用 SQLite 数据库")')

content = content.replace(
    'except Exception:\n            pass  # 关键词失败，降级',
    'except Exception as e:\n            log_error("app.keyword_fallback", str(e))'
)
content = content.replace(
    'except Exception:\n        pass  # AI 失败，走兜底',
    'except Exception as e:\n        log_error("app.ai_fallback", str(e))'
)

with open(f'{BASE}/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok app.py")

# ═══════════════════════════════════════════
# 2. wechat.py — 日志 + MessageLog
# ═══════════════════════════════════════════
with open(f'{BASE}/wechat.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from services.monitor import generate_monitor_report, get_platform_review_links',
    'from services.monitor import generate_monitor_report, get_platform_review_links\n'
    'from services.logger import info, warning, error as log_error, debug, log_keyword, log_booking'
)

# 关键词路由加日志 + MessageLog
old = '            return handler(msg, match)'
new = '''            reply = handler(msg, match)
            try:
                from models import SessionLocal, MessageLog
                db = SessionLocal()
                log_entry = MessageLog(openid=openid, message_type="text", content=content, reply=str(reply)[:500])
                db.add(log_entry); db.commit(); db.close()
            except Exception: pass
            if match:
                log_keyword(openid, str(match.re.pattern), content)
            return reply'''
if old in content:
    content = content.replace(old, new, 1)  # 只替换第一次出现（关键词路由处）

# 关键词异常
content = content.replace(
    'except Exception:\n            pass  # 关键词失败，降级',
    'except Exception as e:\n            log_error("wechat.keyword", str(e))'
)

# AI 异常
content = content.replace(
    'except Exception:\n        pass',
    'except Exception as e:\n        log_error("wechat.ai_fallback", str(e))'
)

# 兜底日志
content = content.replace(
    '# 3. 兜底回复',
    'warning("wechat.fallback", extra={"openid": openid, "content": content[:60]})\n    # 3. 兜底回复'
)

with open(f'{BASE}/wechat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok wechat.py")

# ═══════════════════════════════════════════
# 3. services/ai.py
# ═══════════════════════════════════════════
with open(f'{BASE}/services/ai.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from services.booking import is_ai_enabled, get_booking_by_openid',
    'from services.booking import is_ai_enabled, get_booking_by_openid\n'
    'from services.logger import info, warning, error as log_error, debug, log_ai'
)

# AI 调用异常加日志
content = content.replace(
    '    except Exception:\n        return _fallback_reply()',
    '    except Exception as e:\n        log_error("ai.call", str(e), exc_info=True)\n        return _fallback_reply()'
)

with open(f'{BASE}/services/ai.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok services/ai.py")

# ═══════════════════════════════════════════
# 4. run.py
# ═══════════════════════════════════════════
with open(f'{BASE}/run.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    from app import app, init_app',
    '    from app import app, init_app\n    from services.logger import info'
)

content = content.replace('print("', 'info("')
content = content.replace('print(f"', 'info(f"')
# 修一下嵌套问题
content = content.replace('info("\\n✨ 服务启动中...")', 'info("服务启动中...")')
content = content.replace('info(f"   📱 H5页面: http://127.0.0.1:5000")', 'info("H5页面: http://127.0.0.1:5000")')
content = content.replace('info(f"   🏠 房型展示: http://127.0.0.1:5000/rooms")', 'info("房型: /rooms")')
content = content.replace('info(f"   ☕ 咖啡简餐: http://127.0.0.1:5000/menu")', 'info("菜单: /menu")')
content = content.replace('info(f"   🗺️ 游玩攻略: http://127.0.0.1:5000/travel")', 'info("攻略: /travel")')
content = content.replace('info(f"   🛎️ 快捷服务: http://127.0.0.1:5000/services")', 'info("服务: /services")')
content = content.replace('info(f"   📍 位置导航: http://127.0.0.1:5000/map")', 'info("导航: /map")')
content = content.replace('info(f"   📡 微信接入: http://你的域名/wechat")', 'info("微信接入: /wechat")')
content = content.replace('info("\\n")', '')  # 去掉空行 print
content = content.replace('info()', '')

with open(f'{BASE}/run.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok run.py")

# ═══════════════════════════════════════════
# 5. services/booking.py
# ═══════════════════════════════════════════
with open(f'{BASE}/services/booking.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from models import SessionLocal, Booking',
    'from models import SessionLocal, Booking\n'
    'from services.logger import info, warning, error as log_error, log_booking'
)

with open(f'{BASE}/services/booking.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok services/booking.py")

# ═══════════════════════════════════════════
# 6. seed_data.py
# ═══════════════════════════════════════════
with open(f'{BASE}/seed_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from models import',
    'from services.logger import info, warning, error as log_error\n'
    'from models import'
)
content = content.replace('print("✅', 'info("')
content = content.replace('print("⚠️', 'warning("')

with open(f'{BASE}/seed_data.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ok seed_data.py")

print("\ndone — 日志系统 + 异常处理 + MessageLog 全部更新完成")
