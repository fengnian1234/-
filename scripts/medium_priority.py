# ⚠️ 安全警告: 此脚本会原地修改项目源文件。仅限开发环境使用，生产环境请删除 scripts/ 目录。
"""中优先级改进：对话持久化 + Schema文档 + local_data引用"""
import os

# ═══ 1. 对话持久化 ═══
with open('d:/cc/services/ai.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 在 _conversation_cache 后追加持久化函数
old = '_conversation_cache = {}'
new = '''_conversation_cache = {}  # 内存缓存（热数据）
CONVERSATION_MAX_HISTORY = 20

def _save_conversation(openid: str, role: str, content: str):
    """持久化对话记录到数据库"""
    try:
        from models import SessionLocal, MessageLog
        db = SessionLocal()
        log = MessageLog(openid=openid, message_type=role, content=content[:500], reply=content[:500] if role == 'assistant' else '')
        db.add(log); db.commit(); db.close()
    except Exception: pass

def _load_conversation(openid: str, limit: int = 10):
    """从数据库加载最近对话历史"""
    try:
        from models import SessionLocal, MessageLog
        db = SessionLocal()
        logs = db.query(MessageLog).filter(
            MessageLog.openid == openid
        ).order_by(MessageLog.created_at.desc()).limit(limit * 2).all()
        db.close()
        history = []
        for log in reversed(logs):
            if log.content and log.message_type in ('user', 'text'):
                history.append({'role': 'user', 'content': log.content})
            if log.reply:
                history.append({'role': 'assistant', 'content': log.reply})
        return history
    except Exception:
        return []'''

c = c.replace(old, new)

# 从 DB 加载历史
old2 = "if user_openid not in _conversation_cache:\n            _conversation_cache[user_openid] = []"
new2 = "if user_openid not in _conversation_cache:\n            _conversation_cache[user_openid] = _load_conversation(user_openid)"
c = c.replace(old2, new2)

# 持久化保存
old3 = 'history.append({"role": "user", "content": user_message})\n        history.append({"role": "assistant", "content": ai_reply})'
new3 = 'history.append({"role": "user", "content": user_message})\n        history.append({"role": "assistant", "content": ai_reply})\n        _save_conversation(user_openid, "user", user_message)\n        _save_conversation(user_openid, "assistant", ai_reply[:500])'
c = c.replace(old3, new3)

with open('d:/cc/services/ai.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("1. 对话持久化: OK")

# ═══ 2. local_data 文档引用 ═══
with open('d:/cc/services/ai.py', 'r', encoding='utf-8') as f:
    c = f.read()

old4 = '    _local_data_cache = "\\n".join(lines)\n    return _local_data_cache'
new4 = '''    # 本地文档引用
    try:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_data', 'documents')
        md_file = os.path.join(doc_dir, '美食图片参考链接.md')
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as df:
                doc_content = df.read()
            lines.append('')
            lines.append('[本地文档: 美食图片参考 — 回答相关问题时可引用]')
            lines.append(doc_content[:2000])
    except Exception: pass

    _local_data_cache = "\\n".join(lines)
    return _local_data_cache'''

c = c.replace(old4, new4)

with open('d:/cc/services/ai.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("2. local_data 文档引用: OK")

# ═══ 3. Schema 文档追加 ═══
with open('d:/cc/templates/docs.html', 'r', encoding='utf-8') as f:
    html = f.read()

schema = '''
<h2>🗄️ 数据库 Schema (10张表)</h2>

<h3>rooms · 房型表</h3>
<div class="endpoint" style="border-left-color:#4a7c59">
<table style="width:100%;font-size:12px;border-collapse:collapse">
<tr style="background:var(--border)"><td style="padding:4px 8px;font-weight:600">字段</td><td style="padding:4px 8px;font-weight:600">类型</td><td style="padding:4px 8px;font-weight:600">说明</td></tr>
<tr><td>id</td><td>Integer PK</td><td>主键</td></tr>
<tr><td>name</td><td>String(100)</td><td>房间名称</td></tr>
<tr><td>price / original_price</td><td>Float</td><td>价格 / 原价</td></tr>
<tr><td>capacity / bed_type / area</td><td>Integer / String</td><td>人数 / 床型 / 面积</td></tr>
<tr><td>amenities / images</td><td>JSON</td><td>设施列表 / 图片URL列表</td></tr>
<tr><td>view_type</td><td>String(100)</td><td>景观: 山景/云海/竹林</td></tr>
</table></div>

<h3>bookings · 预订表</h3>
<div class="endpoint" style="border-left-color:#c8966a">
<table style="width:100%;font-size:12px;border-collapse:collapse">
<tr style="background:var(--border)"><td style="padding:4px 8px;font-weight:600">字段</td><td style="padding:4px 8px;font-weight:600">说明</td></tr>
<tr><td>status</td><td>confirmed → checked_in → checked_out → completed</td></tr>
<tr><td>ai_enabled</td><td>AI管家是否解锁（确认预订后开启）</td></tr>
<tr><td>check_in_date / check_out_date</td><td>入住/退房日期</td></tr>
<tr><td>checked_out_at</td><td>退房时间（触发30分钟好评推送倒计时）</td></tr>
<tr><td>review_sent</td><td>是否已推送好评提醒</td></tr>
</table></div>

<h3>其余8张表概览</h3>
<div class="endpoint">
<table style="width:100%;font-size:12px;border-collapse:collapse">
<tr style="background:var(--border)"><td style="padding:4px 8px;font-weight:600">表名</td><td style="padding:4px 8px;font-weight:600">用途</td></tr>
<tr><td>menu_categories / menu_items</td><td>咖啡简餐菜单（分类+菜品）</td></tr>
<tr><td>orders</td><td>点餐订单（微信支付）</td></tr>
<tr><td>travel_routes</td><td>庐山游玩路线（景点/时长/难度）</td></tr>
<tr><td>food_recommends</td><td>周边美食推荐（人均/必点/标签）</td></tr>
<tr><td>quick_services</td><td>快捷服务定义（打扫/叫醒/维修等）</td></tr>
<tr><td>service_requests</td><td>服务请求记录（员工通知）</td></tr>
<tr><td>platform_mentions</td><td>多平台评价/口碑采集</td></tr>
<tr><td>guest_points / point_logs</td><td>积分体系（会员等级/积分流水）</td></tr>
<tr><td>aggregated_orders</td><td>多平台订单聚合（含佣金计算）</td></tr>
<tr><td>message_logs</td><td>消息日志（AI对话持久化）</td></tr>
</table></div>
'''

html = html.replace('</div>\n</body>', schema + '\n</div>\n</body>')
with open('d:/cc/templates/docs.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("3. Schema 文档: OK")

print("\n全部中优先级改进完成")
