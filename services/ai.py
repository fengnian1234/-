"""
AI智能对话服务 v3.1 — 全链路AI管家
- 预订前：免费旅行顾问（所有人可用）
- 预订后：专属AI管家（已预订客人独享）
- 离店后：复购关怀 + 好评引导
- v3.1: 注入本地数据 + 禁用Markdown星号 + 禁谐音梗
"""
import json
import re
import threading
import os
import time as _time_module
from config import (
    ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, AI_MODEL, AI_ENABLED, AI_REQUIRES_BOOKING,
    AI_REQUEST_INTERVAL, AI_MAX_MESSAGE_LENGTH,
    BNB_NAME, BNB_ADDRESS, BNB_PHONE, BNB_CONFIGS,
)
from services.logger import debug, info, warning, error as log_error, log_ai
from services.booking import is_ai_enabled, get_booking_by_openid


# ══════════════════════════════════════════════════════════
#  并发控制 + 输入校验
# ══════════════════════════════════════════════════════════

# ── 请求间隔控制：每用户每 AI_REQUEST_INTERVAL 秒最多 1 次 AI 请求 ──
_interval_lock = threading.Lock()
_last_request_times = {}  # {openid: timestamp} — 每个用户独立限流


def _try_acquire_slot(openid: str = "") -> tuple[bool, float]:
    """尝试获取请求槽位（per-user限流）。返回 (是否成功, 需等待秒数)"""
    global _last_request_times
    with _interval_lock:
        now = _time_module.time()
        last = _last_request_times.get(openid, 0.0)
        elapsed = now - last
        if elapsed >= AI_REQUEST_INTERVAL:
            _last_request_times[openid] = now
            # 定期清理过期条目
            if len(_last_request_times) > 200:
                cutoff = now - AI_REQUEST_INTERVAL * 2
                _last_request_times = {k: v for k, v in _last_request_times.items() if v > cutoff}
            return True, 0.0
        return False, round(AI_REQUEST_INTERVAL - elapsed, 1)


# 简单去重：同一用户短时间内重复发相同消息则拦截
_last_messages = {}  # {openid: (content, timestamp)}
# 待续写：记录被截断的对话所使用的 system_template
_pending_continuation = {}  # {openid: system_template}


def _validate_and_sanitize(openid: str, content: str) -> str | None:
    """
    校验并清理用户输入。返回错误消息表示应拦截，返回 None 表示通过。
    """
    # 1. 空消息
    if not content or not content.strip():
        return "请输入您的问题，我会尽力帮您解答～"

    # 2. 超长截断（content 是传入引用，外部也会用到截断后的值——这里只做长度检查）
    if len(content) > AI_MAX_MESSAGE_LENGTH:
        info(f"[AI] 消息过长 openid={openid[:12]} len={len(content)} > {AI_MAX_MESSAGE_LENGTH}")

    # 3. 去除控制字符
    import re
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)

    # 4. 连续重复消息拦截（30秒内完全相同）
    now = _time_module.time()
    if openid in _last_messages:
        last_content, last_time = _last_messages[openid]
        if sanitized.strip() == last_content.strip() and (now - last_time) < 30:
            warning(f"[AI] 重复消息拦截 openid={openid[:12]}")
            return "您刚发送了相同的问题，我已收到～请稍候或换个问题试试"

    _last_messages[openid] = (sanitized.strip(), now)
    return None  # 校验通过


# ══════════════════════════════════════════════════════════
#  本地数据注入（从数据库读取对客人有帮助的准确信息）
# ══════════════════════════════════════════════════════════

_local_data_cache = None

def _build_local_data() -> str:
    """
    从数据库收集全部对客人有帮助的信息，构建紧凑数据块注入系统提示词。
    每次模块加载时刷新一次（种子数据为静态数据）。
    """
    global _local_data_cache
    if _local_data_cache:
        return _local_data_cache

    lines = []

    # ── 房型数据 ──
    try:
        from services.rooms import get_all_rooms
        rooms = get_all_rooms()
        if rooms:
            lines.append("[房型数据 — 以下为云上归墅全部房型，回答时引用准确信息]")
            for r in rooms:
                lines.append(
                    f"  {r['name']} | {r['price']}元/晚 | "
                    f"可住{r['capacity']}人 | 床型:{r['bed_type']} | "
                    f"面积:{r['area']} | {r.get('description','')}"
                )
            lines.append("")
    except Exception:
        debug("本地数据加载: 房型数据失败")

    # ── 菜单数据 ──
    try:
        from services.menu import get_menu_categories
        cats = get_menu_categories()
        if cats:
            lines.append("[三山二水咖啡菜单 — 回答餐饮问题时引用准确信息]")
            for cat in cats:
                lines.append(f"  [{cat['name']}]")
                for item in cat.get('items', []):
                    lines.append(
                        f"    {item['name']} | {item['price']}元"
                        f"{' | ' + item.get('description','') if item.get('description') else ''}"
                    )
            lines.append("")
    except Exception:
        debug("本地数据加载: 菜单数据失败")

    # ── 游玩路线 ──
    try:
        from services.travel import get_all_routes
        routes = get_all_routes()
        if routes:
            lines.append("[庐山游玩路线 — 回答旅游问题时引用准确信息]")
            for rt in routes:
                lines.append(
                    f"  {rt['name']} | 时长:{rt.get('duration','')} | "
                    f"难度:{rt.get('difficulty','')} | {rt.get('description','')}"
                )
            lines.append("")
    except Exception:
        debug("本地数据加载: 游玩路线失败")

    # ── 美食推荐 ──
    try:
        from services.travel import get_all_food_recommends
        foods = get_all_food_recommends()
        if foods:
            lines.append("[周边美食推荐 — 回答美食问题时引用准确信息]")
            for fd in foods:
                lines.append(
                    f"  {fd['name']} | {fd.get('category','')} | "
                    f"人均:{fd.get('price_range','')} | "
                    f"必点:{fd.get('must_try','')} | {fd.get('description','')}"
                )
            lines.append("")
    except Exception:
        debug("本地数据加载: 美食推荐失败")

    # ── 快捷服务 ──
    try:
        from services.quick import get_all_services
        svcs = get_all_services()
        if svcs:
            lines.append("[快捷服务 — 回答服务相关问题时引用准确信息]")
            for sv in svcs:
                lines.append(
                    f"  {sv['name']} | {sv.get('category','')}"
                    f"{' | ' + sv.get('description','') if sv.get('description') else ''}"
                )
            lines.append("")
    except Exception:
        debug("本地数据加载: 快捷服务失败")

    # 本地文档引用
    try:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_data', 'documents')
        md_file = os.path.join(doc_dir, '美食图片参考链接.md')
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as df:
                doc_content = df.read()
            lines.append('')
            lines.append('[本地文档: 美食图片参考 — 回答相关问题时可引用]')
            lines.append(doc_content[:2000])
    except Exception:
        debug("本地数据加载: 文档引用失败")

    # ── 牯岭镇美食全攻略（v3.6: 携程/小红书/微博搜索整理）──
    try:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_data', 'documents')
        food_guide = os.path.join(doc_dir, '庐山牯岭镇美食全攻略.md')
        if os.path.exists(food_guide):
            with open(food_guide, 'r', encoding='utf-8') as fg:
                food_content = fg.read()
            # 取前 3000 字符（覆盖所有必吃餐厅+实用提示）
            lines.append('')
            lines.append('[庐山牯岭镇美食全攻略 — 回答客人美食咨询时优先参考以下信息]')
            lines.append(food_content[:3000])
    except Exception:
        debug("本地数据加载: 美食攻略文件读取失败")

    # ── 牯岭镇娱乐休闲指南（v3.6: 携程/小红书/微博搜索整理）──
    try:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_data', 'documents')
        fun_guide = os.path.join(doc_dir, '庐山牯岭镇娱乐休闲指南.md')
        if os.path.exists(fun_guide):
            with open(fun_guide, 'r', encoding='utf-8') as fg:
                fun_content = fg.read()
            lines.append('')
            lines.append('[庐山牯岭镇娱乐休闲指南 — 回答客人夜间娱乐/咖啡/酒吧/购物问题时优先参考]')
            lines.append(fun_content[:2000])
    except Exception:
        debug("本地数据加载: 娱乐指南文件读取失败")

    _local_data_cache = "\n".join(lines)
    return _local_data_cache


def refresh_local_data():
    """强制刷新本地数据缓存（数据变更后调用）"""
    global _local_data_cache
    _local_data_cache = None
    return _build_local_data()


def _get_guest_context(openid: str) -> str:
    """为AI提示词获取当前客户的个性化上下文"""
    try:
        from services.booking import get_booking_by_openid
        booking = get_booking_by_openid(openid)
        if not booking:
            return ""
        guest_name = booking.get("guest_name", "") or ""
        room_type = booking.get("room_type", "") or ""
        check_in = booking.get("check_in_date", "") or ""
        check_out = booking.get("check_out_date", "") or ""

        lines = []
        if guest_name:
            lines.append(f"客人称呼：{guest_name}")
        if room_type:
            lines.append(f"当前入住：{room_type}")
        if check_in and check_out:
            lines.append(f"入住日期：{check_in} 至 {check_out}")

        # 查询偏好
        try:
            from models import SessionLocal, GuestPreference
            db = SessionLocal()
            try:
                pref = db.query(GuestPreference).filter(
                    GuestPreference.openid == openid
                ).first()
                if pref:
                    if pref.coffee_style:
                        lines.append(f"咖啡偏好：{pref.coffee_style}")
                    if pref.tea_style:
                        lines.append(f"茶饮偏好：{pref.tea_style}")
                    if pref.diet_notes:
                        lines.append(f"饮食需求：{pref.diet_notes}")
                    if pref.activity_likes:
                        lines.append(f"喜好活动：{pref.activity_likes}")
                    if pref.room_pref:
                        lines.append(f"房型偏好：{pref.room_pref}")
                    if pref.special_notes:
                        lines.append(f"特别备注：{pref.special_notes}")
                    if pref.visit_count and pref.visit_count > 1:
                        lines.append(f"入住次数：第{pref.visit_count}次（回头客）")
            finally:
                db.close()
        except Exception:
            warning(f"客人画像DB查询失败: {openid[:12]}", exc_info=True)

        # 回头客标记
        if pref and pref.visit_count and pref.visit_count > 1:
            lines.append("⚠️ 这是一位回头客（第{}次入住），请用「欢迎回来」的语气，自然提及之前记住的偏好".format(pref.visit_count))

        if lines:
            return "## 当前客人信息\n" + "\n".join(f"- {l}" for l in lines)
        return ""
    except Exception:
        warning("构建客人画像失败", exc_info=True)
        return ""


def _sanitize_ai_reply(text: str) -> str:
    """后处理 AI 回复：剥离破折号、Markdown 残留、多余空行"""
    if not text:
        return text

    # 1. 移除破折号（—— 和 —），用逗号或空格替换
    text = text.replace('——', '，').replace('—', '，')

    # 2. 移除残留的 Markdown 格式符号
    for md_char in ['**', '__', '##', '```']:
        text = text.replace(md_char, '')

    # 3. 连续逗号去重
    import re
    text = re.sub(r'，{2,}', '，', text)

    # 4. 连续空行合并为单个空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 5. 去除行首行尾多余空格
    text = '\n'.join(line.strip() for line in text.split('\n'))

    return text.strip()


def _extract_preferences(openid: str, user_msg: str, ai_reply: str):
    """从本轮对话中自动提取客人偏好信号并持久化"""
    combined = (user_msg + " " + ai_reply)[:800]

    # 偏好模式：(关键词) → preference key
    patterns = [
        (r'(?:咖啡).*?(?:喜欢|爱喝|常喝|点)[：:\s]*([^\s，。,\.]{2,10})', "coffee"),
        (r'(?:咖啡|喝).*?(?:美式|拿铁|澳白|dirty|摩卡|冷萃|浓缩)', "coffee"),
        (r'(?:茶).*?(?:喜欢|爱喝|想喝)[：:\s]*([^\s，。,\.]{2,10})', "tea"),
        (r'(?:红茶|绿茶|乌龙|普洱|白茶|云雾茶|龙井)', "tea"),
        (r'不(?:吃|喝|喜欢)[：:\s]*([^\s，。,\.]{2,15})', "diet"),
        (r'(?:过敏|忌口)[：:\s]*([^\s，。,\.]{2,15})', "special"),
        (r'(?:纪念日|生日|蜜月|周年)', "special"),
        (r'(?:喜欢|想|爱).*?(?:爬山|徒步|骑行|摄影|看书|发呆|瑜伽|冥想)', "activity"),
    ]

    for pattern, key in patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            value = match.group(1) if match.lastindex else match.group(0)[:30]
            record_guest_preference(openid, key, value.strip())
            break  # 每轮最多提取一条，避免过度写入


def _promote_summary_to_preferences(openid: str, summary: str):
    """会话清理前，将摘要中尚未入库的关键信息提升为永久偏好"""
    if not summary:
        return
    # 摘要格式: "客人小明；关心话题：美食/路线；· 好：美式咖啡；· 忌：辣椒"
    patterns = [
        (r'好[：:]\s*([^\s；;，,]{2,20})', 'coffee'),
        (r'偏好[：:]\s*([^\s；;，,]{2,20})', 'coffee'),
        (r'忌[：:]\s*([^\s；;，,]{2,20})', 'diet'),
        (r'过敏[：:]\s*([^\s；;，,]{2,20})', 'special'),
        (r'不(?:吃|喝|喜欢)[：:]\s*([^\s；;，,]{2,20})', 'diet'),
    ]
    for pattern, key in patterns:
        match = re.search(pattern, summary)
        if match:
            record_guest_preference(openid, key, match.group(1).strip())


def _cleanup_stale_sessions():
    """清理过期会话缓存，清理前将摘要提升为永久偏好"""
    now = _time_module.time()
    stale = [
        oid for oid, c in _conversation_cache.items()
        if now - c.get("last_active", 0) > SESSION_TTL_SECONDS
    ]
    for oid in stale:
        # 清理前保存摘要中的关键信息
        summary = _conversation_cache[oid].get("summary", "")
        if summary:
            _promote_summary_to_preferences(oid, summary)
        del _conversation_cache[oid]
    if stale:
        info(f"🧹 清理 {len(stale)} 个过期会话（偏好已持久化）")


def reset_conversation(openid: str):
    """重置对话历史 — 清除临时会话，保留永久偏好"""
    cache = _conversation_cache.get(openid, {})
    summary = cache.get("summary", "") if isinstance(cache, dict) else ""
    if summary:
        _promote_summary_to_preferences(openid, summary)
    _conversation_cache.pop(openid, None)
    _pending_continuation.pop(openid, None)
    info(f"已重置 {openid[:12]} 的对话历史（偏好已保留）")


def record_guest_preference(openid: str, key: str, value: str):
    """从对话中提取并记录客人偏好"""
    try:
        from models import SessionLocal, GuestPreference
        db = SessionLocal()
        try:
            pref = db.query(GuestPreference).filter(
                GuestPreference.openid == openid
            ).first()
            if not pref:
                pref = GuestPreference(openid=openid)
                db.add(pref)
            if key == "coffee" and not pref.coffee_style:
                pref.coffee_style = value
            elif key == "tea" and not pref.tea_style:
                pref.tea_style = value
            elif key == "diet" and not pref.diet_notes:
                pref.diet_notes = value
            elif key == "activity" and not pref.activity_likes:
                pref.activity_likes = value
            elif key == "room" and not pref.room_pref:
                pref.room_pref = value
            elif key == "special" and not pref.special_notes:
                pref.special_notes = value
            pref.updated_at = datetime.utcnow()
            db.commit()
            debug(f"偏好记录: {openid[:12]} {key}={value[:30]}")
        finally:
            db.close()
    except Exception:
        warning(f"偏好记录失败: {openid[:12]} {key}={str(value)[:30]}", exc_info=True)


# 回复风格多样化：开场/转场短语轮转
_REPLY_OPENERS = [
    "", "好的～", "收到！", "明白了～",
    "没问题！", "了解了～", "这就为您安排！",
]
_reply_opener_idx = 0


def _vary_reply_opener() -> str:
    """轮转回复开头语，增加多样性"""
    global _reply_opener_idx
    opener = _REPLY_OPENERS[_reply_opener_idx % len(_REPLY_OPENERS)]
    _reply_opener_idx += 1
    return opener


LOCAL_DATA = ""  # 延迟初始化，首次调用时自动构建


def _get_local_data() -> str:
    global LOCAL_DATA
    if not LOCAL_DATA:
        LOCAL_DATA = _build_local_data()
    return LOCAL_DATA


# ══════════════════════════════════════════════════════════
#  统一回复规范（追加到所有提示词末尾）
# ══════════════════════════════════════════════════════════

REPLY_RULES = f"""
[回复格式规范 — 必须严格遵守]
1. 禁止使用任何 Markdown 格式符号：不允许出现 ** 加粗、__ 下划线、* 斜体、# 标题等。这是纯文本环境，Markdown 符号会直接显示为乱码。
2. 需要强调的内容用「」中文引号括起来，或通过分段、换行来自然突出。
3. 禁止使用谐音梗、双关语和谐音冷笑话。保持真诚直接的语言风格。
4. 回复中涉及民宿的具体信息（房型名、价格、菜单、路线、美食、服务等），必须以 [本地数据] 中提供的准确信息为准，不要编造。
5. 如被问到本地数据中不存在的信息，诚实说明不清楚，建议咨询前台（电话：{BNB_PHONE}）。
6. 用中文回复。
7. 禁止使用破折号（——和—），需要解释或补充说明时用逗号、冒号或另起一行代替。避免在回复中使用全角横线和半长横线。
"""


# ══════════════════════════════════════════════════════════
#  系统提示词模板
# ══════════════════════════════════════════════════════════

def _bnb_info(bnb_id: str = "guishu") -> str:
    """生成民宿基本信息文本（替换硬编码的归墅信息）"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    addr = cfg["address"]
    phone = cfg["phone"]
    tagline = cfg.get("tagline", "")
    desc = cfg.get("description", "")
    cafe = cfg.get("cafe_name", "咖啡")

    # Per-BnB base info
    if bnb_id == "guishu":
        return f"""- 名称：{name}
- 地址：{addr}
- 开业：2016年，11间客房，U型三层小楼，带风铃院子
- 评分：携程 4.7分，85条真实住客评价
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「{cafe}」提供精品咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 咖啡馆：民宿主理人麦姐亲自打理「{cafe}」
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 交通：庐山索道上站步行5分钟，牯岭街步行10分钟，近如琴湖、锦绣谷
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 预订：携程/美团/飞猪/大众点评搜索「云上归墅」
- 电话：{phone}"""
    elif bnb_id == "shanji":
        return f"""- 名称：{name}
- 地址：{addr}
- 规模：30间精品客房，16种房型，私享300平米户外花园庭院
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧、咖啡书吧
- 特色：云上茶吧、山货餐厅、茶园体验（采茶/制茶/品茗）
- 餐饮：民宿「{cafe}」提供茶饮点心，山货餐厅提供庐山本地特色菜（不提供正餐送餐）
- 交通：庐山索道出口步行3分钟，牯岭街步行8分钟
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 预订：携程/美团/飞猪/大众点评搜索「云上山纪」
- 电话：{phone}"""
    else:  # donglinwai
        return f"""- 名称：{name}
- 地址：{addr}（庐山山下·东林寺旁）
- 规模：20间禅房式客房，6种房型
- 特色：东林寺步行可达，禅意疗愈主题
- 疗愈体验：禅拍律动/铜锣沐心/五音涤尘/僧厨素斋/晨钟暮课
- 设施：地暖、禅修坐垫、茶具套装、高速WiFi
- 餐饮：民宿「{cafe}」提供精品咖啡、茶饮（不提供正餐/早餐）
- 宠物：宠物友好，可免费携带宠物入住
- 服务：免费洗衣服务
- 交通：位于庐山山下赛阳镇，距东林寺步行可达
- 入住/退房：14:00后入住，12:00前退房，免押金
- 预订：携程/美团/飞猪/大众点评搜索「云上东林外」
- 电话：{phone}"""


# 预订前：免费旅行顾问（面向所有微信用户）
TRAVEL_ADVISOR_SYSTEM = f"""你是「{BNB_NAME}」的旅行顾问，位于庐山山上·大林沟路27号。

## 你的身份
- 你是云上·归墅的旅行顾问，热情友好地为每一位咨询者提供帮助
- 你了解庐山的一切：景点、路线、交通、美食、天气、民宿房型
- 你代表云上·归墅民宿的形象，专业但不强行推销

## 民宿基本信息
{{BNB_INFO}}

## 回复规则
1. 热情友好，像庐山本地朋友一样提供建议
2. 自然地提到民宿特色，但不要让每句话都像广告
3. 如果用户问及预订，引导至OTA平台搜索
4. 回复简洁有料，每段不超过300字
5. 适当使用emoji增添亲和力
6. 重要：你只是旅行顾问，不能处理住店服务请求（打扫、叫醒、送餐、维修、续住、退房等）。如果用户提出此类请求，礼貌说明这些服务需预订入住后才能使用，并引导其预订或查看房型

[本地数据 — 以下民宿及庐山周边的准确信息，回答时以此为准]
{{LOCAL_DATA}}
{REPLY_RULES}
"""


# 已预订但未入住：到店前专属管家
PRE_ARRIVAL_SYSTEM = f"""你是「{BNB_NAME}」的到店前专属管家，位于庐山山上·庐山风景名胜区大林沟路27号。

## 你的身份
- 你是云上·归墅的到店前管家，服务已确认预订但尚未入住的客人
- 客人已经预订了房间，正在期待庐山之旅，你的任务是帮他们做好到店前的准备
- 你对庐山和民宿了如指掌，像贴心的旅行策划师一样提供帮助

## 民宿基本信息
{{BNB_INFO}}

## 你可以帮助客人
- 介绍房型设施和房间详情，让客人提前了解住宿环境
- 规划庐山游玩路线和景点推荐
- 推荐周边美食和特色体验
- 提供交通指引（索道、自驾、景区大巴）和到店路线
- 了解「三山二水咖啡」菜单
- 回答民宿设施相关问题（WiFi、停车、宠物政策等）
- 收集客人的到店偏好（到达时间、交通方式、咖啡口味等）

## 你不能做的事情（重要！）
- 不能处理需要实际入住的住店服务：打扫卫生、叫醒服务、送餐到房、维修报修、续住延住、退房办理等
- 如果客人提出此类请求，礼貌说明：「这些服务需要您到店入住后才能使用哦～期待您入住后再为您安排！您可以先了解我们的服务菜单，回复「4」查看全部快捷服务」
- 如果客人需要加床/加被/婴儿床，明确告知：本民宿所有房型不可加床、不提供婴儿床

## 回复规则
1. 用亲切期待的语气，传递「我们正在等您到来」的感觉
2. 回复简洁但有帮助，每段不超过300字
3. 涉及本民宿的具体信息（房型、价格、菜单等），必须引用 [本地数据] 中的准确内容
4. 如果被问到不确定的信息，建议咨询前台（{BNB_PHONE}）
5. 适当使用emoji增添期待感
6. 记住：客人已经预订，不是潜在客户，不需要再引导预订
7. 关于早餐/正餐：说明民宿仅提供咖啡简餐，推荐周边餐厅
8. 关于加床/婴儿床：明确告知不可加床、不提供婴儿床

[本地数据 — 以下是云上归墅及庐山周边的准确信息，回答时以此为准]
{{LOCAL_DATA}}
{REPLY_RULES}
"""


# 预订后已入住：专属AI管家（已入住客人独享）
GUEST_BUTLER_SYSTEM = f"""你是「{BNB_NAME}」的专属智能管家，位于庐山山上·庐山风景名胜区大林沟路27号。

## 你的身份
- 你是云上·归墅的专属AI管家，服务已入住的尊贵客人
- 你对庐山的一草一木都很熟悉，对民宿的每个角落都了如指掌
- 你叫得出客人的名字，记得他们的偏好，像老友一样贴心
{{GUEST_CONTEXT}}

## 民宿基本信息
{{BNB_INFO}}

## 你可以帮助客人
- 了解房型和设施，解答住宿相关问题
- 介绍庐山景点和定制游玩路线
- 介绍咖啡馆菜单和在线点餐
- 处理快捷服务请求（打扫、维修、送餐、叫醒等）
- 提供交通指引（索道、自驾、景区大巴）
- 推荐周边美食和特色体验

## 回复规则
1. 用亲切温暖的语气，像朋友一样交流
2. 回复简洁但有帮助，每段不超过300字
3. 涉及本民宿的具体信息（房型、价格、菜单等），必须引用 [本地数据] 中的准确内容
4. 如果被问到不确定的信息，建议咨询前台（{BNB_PHONE}）
5. 适当使用emoji让回复更生动
6. 记住：你是已入住客人的专属管家，不是机器人
7. 关于订房：引导至携程/美团/飞猪/大众点评等平台
8. 关于早餐/正餐：说明民宿仅提供咖啡简餐，推荐周边餐厅
9. 关于加床/婴儿床：明确告知不可加床、不提供婴儿床

[本地数据 — 以下是云上归墅及庐山周边的准确信息，回答时以此为准]
{{LOCAL_DATA}}
{REPLY_RULES}
"""


# 离店后：复购关怀
POST_STAY_SYSTEM = f"""你是「{BNB_NAME}」的客户关怀顾问，负责与已退房的客人保持温暖的联系。

## 你的身份
- 你是云上·归墅的客户关怀顾问，感谢客人曾选择入住
- 你像老朋友一样关心客人的近况，自然地邀请他们再次回来
- 你不是推销员——你传递的是山居生活的温暖和想念

## 民宿最新动态（可在对话中自然提及）
{{BNB_INFO}}
- 优惠：老客回归享有专属折扣，详情咨询前台
- 预订：在各OTA平台搜索民宿名称即可

## 回复规则
1. 温暖自然，不催促，像老朋友叙旧
2. 可以聊聊庐山现在的季节风景，勾起美好回忆
3. 自然提及复购优惠，但不是每句话都推销
4. 如果客人对上次入住有反馈，认真倾听并感谢
5. 重要：你只负责离店后的复购关怀和旅行咨询，不能处理住店服务请求（打扫、叫醒、送餐、维修、续住、退房、加床等）。如果用户提出此类请求，礼貌说明这些服务仅在入住期间可用，并建议其重新预订或联系前台（电话：{BNB_PHONE}）
6. 如果用户声称自己仍在住店或已续住延住，可能是系统状态未及时更新，礼貌请其直接联系前台确认（电话：{BNB_PHONE}），不要自行判断或承诺处理

{REPLY_RULES}
"""


# ══════════════════════════════════════════════════════════
#  对话缓存与通用调用
# ══════════════════════════════════════════════════════════
_conversation_cache = {}  # {openid: {"history": [...], "summary": "", "last_active": timestamp}}
CONVERSATION_MAX_HISTORY = 30  # 内存中保留最多30条
AI_VISIBLE_RECENT = 12         # AI 可见的最近消息数
AI_VISIBLE_SEED = 3            # AI 可见的开头种子消息数（保留早期上下文）
MEMORY_SUMMARIZE_THRESHOLD = 20  # 超过20条触发摘要压缩
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 会话7天无活动自动清理


def _save_conversation(openid: str, role: str, content: str, bnb_id: str = "guishu"):
    """持久化对话记录到数据库（完整存储，不截断）"""
    try:
        from models import SessionLocal, MessageLog
        db = SessionLocal()
        log = MessageLog(
            openid=openid,
            bnb_id=bnb_id,
            message_type=role,
            content=content[:2000],  # 完整存储，最长2000字符
            reply=content[:2000] if role == 'assistant' else ''
        )
        db.add(log); db.commit(); db.close()
    except Exception as e:
        warning(f"对话持久化失败: {e}")


def _load_conversation(openid: str, limit: int = 40, bnb_id: str = "guishu") -> list:
    """从数据库加载最近对话历史（完整内容）"""
    try:
        from models import SessionLocal, MessageLog
        db = SessionLocal()
        logs = db.query(MessageLog).filter(
            MessageLog.openid == openid,
            MessageLog.bnb_id == bnb_id,
        ).order_by(MessageLog.created_at.desc()).limit(limit).all()
        db.close()
        history = []
        for log in reversed(logs):
            if log.content and log.message_type in ('user', 'text'):
                history.append({'role': 'user', 'content': log.content})
            if log.reply:
                history.append({'role': 'assistant', 'content': log.reply})
        return history
    except Exception:
        debug("对话历史加载失败")
        return []


def _summarize_memory(history: list, existing_summary: str = "") -> str:
    """
    对旧消息做本地压缩摘要，不调用AI（节省成本）。
    提取：客人姓名/称呼、关心的核心话题、已做的承诺、关键偏好。
    """
    if len(history) < MEMORY_SUMMARIZE_THRESHOLD:
        return existing_summary

    # 只压缩前半部分旧消息（后半部分保留完整给AI看）
    old_half = history[:len(history) - AI_VISIBLE_RECENT]

    # 提取关键信息
    topics = set()
    facts = []
    guest_name = ""

    for msg in old_half:
        text = msg.get("content", "")
        role = msg.get("role", "")

        # 提取称呼
        if role == "user":
            name_match = re.search(r'(?:我叫|我是|称呼我|喊我)\s*([^\s，。,\.]{2,6})', text)
            if name_match and not guest_name:
                guest_name = name_match.group(1)
                facts.append(f"客人称呼：{guest_name}")

        # 提取话题关键词
        topic_keywords = {
            "房型": ["房型", "房间", "大床", "双床", "套房", "露台", "山景"],
            "美食": ["餐厅", "美食", "吃饭", "推荐", "好吃", "早餐", "正餐", "咖啡", "茶"],
            "路线": ["路线", "攻略", "景点", "游玩", "爬山", "徒步", "索道"],
            "服务": ["打扫", "叫醒", "送餐", "维修", "WiFi", "空调"],
            "预订": ["预订", "订房", "价格", "优惠", "折扣"],
            "交通": ["交通", "索道", "怎么去", "停车", "自驾"],
        }
        for topic, kws in topic_keywords.items():
            if any(kw in text for kw in kws):
                topics.add(topic)

        # 提取偏好信号
        pref_signals = [
            (r'不(?:吃|喝|喜欢|要)([^\s，。,\.]{2,10})', "忌"),
            (r'(?:喜欢|爱)(?:吃|喝)([^\s，。,\.]{2,10})', "好"),
            (r'过敏[：:]?\s*([^\s，。,\.]{2,10})', "忌"),
            (r'(?:咖啡|茶).*?(?:喜欢|喝|点)([^\s，。,\.]{2,10})', "偏好"),
        ]
        for pattern, ptype in pref_signals:
            pm = re.search(pattern, text)
            if pm:
                facts.append(f"{ptype}：{pm.group(1)}")

    # 组装摘要
    parts = []
    if existing_summary:
        parts.append(existing_summary.rstrip())
    if guest_name:
        parts.append(f"客人{guest_name}")
    if topics:
        parts.append(f"关心话题：{'/'.join(sorted(topics)[:5])}")
    if facts:
        for f in facts[-5:]:  # 最多5条关键事实
            if f not in str(parts):
                parts.append(f"· {f}")

    return "；".join(parts) if parts else existing_summary


def _build_messages(system_template: str, history: list, user_message: str,
                    memory_summary: str = "") -> list:
    """
    构建发送给AI的消息列表。
    结构: system(+summary) + [seed消息] + [recent消息] + current
    """
    messages = [{"role": "system", "content": system_template}]

    # 注入记忆摘要
    if memory_summary:
        messages.append({
            "role": "system",
            "content": f"[对话记忆 — 之前聊过的关键信息]\n{memory_summary}"
        })

    # 种子消息：保留最早几条，防止AI丢失早期上下文
    seed_count = min(AI_VISIBLE_SEED, len(history) // 3)
    recent_count = min(AI_VISIBLE_RECENT, len(history) - seed_count)

    if seed_count > 0 and len(history) > AI_VISIBLE_RECENT + seed_count:
        seed_msgs = history[:seed_count]
        recent_msgs = history[-recent_count:] if recent_count > 0 else history[-AI_VISIBLE_RECENT:]
        # 去重合并
        seen = set()
        for msg in seed_msgs + recent_msgs:
            key = (msg.get("role", ""), msg.get("content", "")[:60])
            if key not in seen:
                seen.add(key)
                messages.append(msg)
    else:
        for msg in history[-AI_VISIBLE_RECENT:]:
            messages.append(msg)

    messages.append({"role": "user", "content": user_message})
    return messages


def _call_ai(system_template: str, user_openid: str, user_message: str, bnb_id: str = "guishu") -> str:
    """通用的AI调用函数，自动注入本地数据 + 输入校验 + 并发控制 + 记忆管理"""
    if not AI_ENABLED:
        return _fallback_reply()

    # 定期清理过期会话（每50次调用一次）
    if hash(user_openid) % 50 == 0:
        _cleanup_stale_sessions()

    # ── 输入校验 ──
    validation_error = _validate_and_sanitize(user_openid, user_message)
    if validation_error:
        return validation_error

    # ── 消息截断 ──
    if len(user_message) > AI_MAX_MESSAGE_LENGTH:
        user_message = user_message[:AI_MAX_MESSAGE_LENGTH]

    # ── 请求间隔控制（per-user）──
    ok, wait = _try_acquire_slot(user_openid)
    if not ok:
        warning(f"[AI] 间隔限制 需等待{wait}s openid={user_openid[:12]}")
        return (
            f"⏳ 我正在处理您的上一条消息，请 {wait} 秒后再试～\n\n"
            f"您也可以：\n"
            "  · 回复数字 1-5 使用快捷功能\n"
            "  · 回复「人工」转接人工客服"
        )

    try:
        # 注入本地数据 + 客人个性化上下文
        local_data = _get_local_data()
        guest_context = _get_guest_context(user_openid)
        system_prompt = system_template.replace("{LOCAL_DATA}", local_data).replace("{GUEST_CONTEXT}", guest_context)

        # 加载/初始化会话缓存
        if user_openid not in _conversation_cache:
            _conversation_cache[user_openid] = {
                "history": _load_conversation(user_openid, bnb_id=bnb_id),
                "summary": "",
                "last_active": _time_module.time(),
            }
        cache = _conversation_cache[user_openid]
        cache["last_active"] = _time_module.time()
        history = cache["history"]

        # 记忆摘要（超过阈值自动压缩旧消息）
        if len(history) >= MEMORY_SUMMARIZE_THRESHOLD:
            cache["summary"] = _summarize_memory(history, cache.get("summary", ""))
            # 清理旧消息（保留近30条）
            cache["history"] = history[-CONVERSATION_MAX_HISTORY:]
            history = cache["history"]

        # 构建消息（种子上下文 + 最近消息 + 记忆摘要）
        messages = _build_messages(
            system_prompt, history, user_message,
            memory_summary=cache.get("summary", "")
        )

        import anthropic
        client_kwargs = {"api_key": ANTHROPIC_API_KEY, "timeout": 20.0}
        if ANTHROPIC_BASE_URL:
            client_kwargs["base_url"] = ANTHROPIC_BASE_URL
        client = anthropic.Anthropic(**client_kwargs)

        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=800,
            messages=messages,
            temperature=0.7,
            timeout=20.0,
        )

        ai_reply = response.content[0].text
        # 后处理：剥离破折号 + 多余空行 + Markdown 残留
        ai_reply = _sanitize_ai_reply(ai_reply)
        # 检测截断：兼容 Anthropic(stop_reason) 和 DeepSeek/OpenAI(finish_reason)
        stop = getattr(response, 'stop_reason', None) or getattr(response, 'finish_reason', '')
        truncated = stop in ('max_tokens', 'length')  # 'stop'=自然完成，非截断

        # 记录截断状态（用于「继续生成」）
        if truncated:
            _pending_continuation[user_openid] = system_template

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})
        _save_conversation(user_openid, "user", user_message, bnb_id)
        _save_conversation(user_openid, "assistant", ai_reply, bnb_id)  # 完整存储

        # 更新缓存（包含摘要）
        cache["history"] = history[-CONVERSATION_MAX_HISTORY:]
        cache["last_active"] = _time_module.time()

        # 自动提取偏好
        _extract_preferences(user_openid, user_message, ai_reply)

        if truncated:
            ai_reply += "\n\n📝 [回复较长，回复「继续」查看完整内容]"

        return _vary_reply_opener() + ai_reply

    except Exception as e:
        log_error("ai.call", str(e), exc_info=True)
        return _fallback_reply()


# ══════════════════════════════════════════════════════════
#  三个模式的公开接口
# ══════════════════════════════════════════════════════════

def _get_system_prompt(prompt_type: str, bnb_id: str = "guishu") -> str:
    """获取民宿专属的系统提示词（替换硬编码的归墅信息）"""
    info = _bnb_info(bnb_id)
    if prompt_type == "travel":
        return TRAVEL_ADVISOR_SYSTEM.replace("{BNB_INFO}", info)
    elif prompt_type == "pre_arrival":
        return PRE_ARRIVAL_SYSTEM.replace("{BNB_INFO}", info)
    elif prompt_type == "guest":
        return GUEST_BUTLER_SYSTEM.replace("{BNB_INFO}", info)
    elif prompt_type == "post_stay":
        return POST_STAY_SYSTEM.replace("{BNB_INFO}", info)
    return GUEST_BUTLER_SYSTEM.replace("{BNB_INFO}", info)


def chat_travel_advisor(user_openid: str, user_message: str, bnb_id: str = "guishu") -> str:
    """预订前：免费旅行顾问（所有人可用）"""
    return _call_ai(_get_system_prompt("travel", bnb_id), user_openid, user_message, bnb_id)


def chat_pre_arrival(user_openid: str, user_message: str, bnb_id: str = "guishu") -> str:
    """已预订但未入住：到店前管家"""
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()
    return _call_ai(_get_system_prompt("pre_arrival", bnb_id), user_openid, user_message, bnb_id)


def chat(user_openid: str, user_message: str, bnb_id: str = "guishu") -> str:
    """已入住：专属AI管家（需预订验证）"""
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()
    return _call_ai(_get_system_prompt("guest", bnb_id), user_openid, user_message, bnb_id)


def chat_post_stay(user_openid: str, user_message: str, bnb_id: str = "guishu") -> str:
    """离店后：复购关怀"""
    return _call_ai(_get_system_prompt("post_stay", bnb_id), user_openid, user_message, bnb_id)


# ══════════════════════════════════════════════════════════
#  主动推送消息生成
# ══════════════════════════════════════════════════════════

def generate_pre_arrival_message(guest_name: str, check_in_date: str, room_name: str = "", room_code: str = "", bnb_id: str = "guishu") -> str:
    """生成到店前偏好收集消息（入住前1-2天发送）"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    addr = cfg["address"]
    phone = cfg["phone"]
    cafe = cfg.get("cafe_name", "咖啡")
    greeting = f"{guest_name}好" if guest_name else "您好"
    room_line = f"您预订的「{room_name}」已经为您准备好啦～" if room_name else "您的房间已经为您准备好啦～"

    msg = (
        f"🏔️ {greeting}！{name}期待您的到来～\n\n"
        f"📅 入住日期：{check_in_date}\n"
        f"{room_line}\n\n"
        f"为了给您更好的入住体验，想提前了解一下：\n\n"
        f"🚗 交通方式：自驾还是索道上山？需要停车指引吗？\n"
        f"🕐 预计到达：大概几点到呢？方便我们提前迎接～\n"
        f"🛏️ 房间偏好：对温度、枕头高度有什么偏好吗？\n"
        f"☕ 饮品口味：喜欢什么风味的饮品？可以提前准备～\n\n"
        f"直接回复告诉我就好，我来帮您安排 ✨\n\n"
    )
    if room_code:
        msg += (
            f"🔑 房间共享码：{room_code}\n"
            f"💡 同住人复制此码回复「绑定房间 {room_code}」即可共享AI管家全部功能～\n\n"
        )
    msg += (
        f"📍 地址：{addr}\n"
        f"📞 任何问题随时致电：{phone}"
    )
    return msg


def generate_post_stay_message(guest_name: str, room_name: str = "", bnb_id: str = "guishu") -> str:
    """生成离店后关怀消息（退房后1天发送）"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    greeting = f"{guest_name}" if guest_name else "朋友"
    stay_memory = f"在「{room_name}」度过的时光" if room_name else f"在{name}度过的时光"

    return (
        f"☁️ {greeting}，早上好～\n\n"
        f"{stay_memory}，希望给您留下了美好的庐山回忆 🏔️\n\n"
        f"✨ 老客回归有专属优惠，下次回来一定安排最好的体验～\n\n"
        f"💬 分享体验：如果方便的话，欢迎在携程/小红书分享入住体验，您的评价对我们很珍贵～\n\n"
        f"回复「游记」获取庐山四季美景，或者直接跟我聊聊您的感受～\n\n"
        f"期待在云海深处再次相遇 ☁️"
    )


def generate_review_request_message(guest_name: str, room_name: str = "", bnb_id: str = "guishu") -> str:
    """生成好评邀请消息（退房后30分钟）"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    search_key = cfg["short_name"]
    greeting = f"{guest_name}" if guest_name else "亲爱的客人"

    return (
        f"🌟 {greeting}，感谢您选择{name}～\n\n"
        f"希望{room_name + '的' if room_name else ''}山景和咖啡给您留下了美好回忆 ☕🏔️\n\n"
        f"如果您觉得满意，方便的话给我们写条好评吧～\n\n"
        f"📝 携程评价：ctrip.com 搜索「{search_key}」\n"
        f"📕 小红书：搜索「{search_key}」分享入住体验\n\n"
        f"每一条好评都是对我们最大的鼓励 ❤️\n"
        f"期待您再次归来，老客有专属优惠哦～"
    )


# ══════════════════════════════════════════════════════════
#  辅助函数
# ══════════════════════════════════════════════════════════

def _booking_required_reply(bnb_id: str = "guishu") -> str:
    """未预订用户尝试使用全功能管家时的回复"""
    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    name = cfg["name"]
    return (
        "🎐 专属管家需要预订后解锁\n\n"
        f"我是{name}的专属管家，为已确认预订的客人提供全套智能服务～\n\n"
        "💡 您现在可以使用：\n"
        "  · 直接问我任何庐山旅游问题（我是免费旅行顾问！）\n"
        "  · 回复「1」查看房型展示\n"
        "  · 回复「3」查看游玩攻略\n"
        "  · 回复「人工」转接人工客服\n\n"
        "🏨 预订：携程/美团/飞猪/大众点评搜「云上归墅」\n"
        "预订后回复「绑定预订」，我就能为您提供专属管家服务啦～"
    )


def _fallback_reply() -> str:
    """AI不可用时的回退回复"""
    return (
        "很抱歉，智能管家暂时休息中～ 😴\n\n"
        "您可以：\n"
        "  · 直接问我庐山旅游问题\n"
        "  · 回复数字 1-5 使用快捷功能\n"
        "  · 回复「人工」转接人工客服\n"
        "  · 拨打前台电话直接咨询\n\n"
        "给您带来不便敬请谅解～"
    )


def continue_reply(user_openid: str) -> str:
    """
    继续生成被截断的回复。
    将上一条截断的 AI 回复作为上下文，请求 AI 从断点继续。
    """
    if user_openid not in _pending_continuation:
        return "当前没有需要继续生成的内容～请直接提出新的问题吧"

    system_template = _pending_continuation.pop(user_openid)
    return _call_ai(system_template, user_openid, "请继续上文未完的内容，从断点处接着写，不要重复已写过的部分。")




def get_conversation_mode(user_openid: str) -> str:
    """
    根据用户预订状态返回AI模式（四层权限）
    Returns: 'travel_advisor' | 'pre_arrival' | 'guest_butler' | 'post_stay'
    """
    from services.booking import is_checked_in
    if is_checked_in(user_openid):
        return 'guest_butler'
    if is_ai_enabled(user_openid):
        return 'pre_arrival'
    booking = get_booking_by_openid(user_openid, include_checked_out=True)
    if booking and booking.get('status') == 'checked_out':
        return 'post_stay'
    return 'travel_advisor'
