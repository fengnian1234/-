"""
AI智能对话服务 v3.1 — 全链路AI管家
- 预订前：免费旅行顾问（所有人可用）
- 预订后：专属AI管家（已预订客人独享）
- 离店后：复购关怀 + 好评引导
- v3.1: 注入本地数据 + 禁用Markdown星号 + 禁谐音梗
"""
import json
import threading
import time as _time_module
from config import (
    ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, AI_MODEL, AI_ENABLED, AI_REQUIRES_BOOKING,
    AI_REQUEST_INTERVAL, AI_MAX_MESSAGE_LENGTH,
    BNB_NAME, BNB_ADDRESS, BNB_PHONE,
)
from services.logger import debug, warning, log_ai
from services.booking import is_ai_enabled, get_booking_by_openid
from services.logger import info, warning, error as log_error, debug, log_ai


# ══════════════════════════════════════════════════════════
#  并发控制 + 输入校验
# ══════════════════════════════════════════════════════════

# ── 请求间隔控制：每次 AI 请求至少间隔 AI_REQUEST_INTERVAL 秒 ──
_interval_lock = threading.Lock()
_last_request_time = 0.0


def _try_acquire_slot() -> tuple[bool, float]:
    """尝试获取请求槽位。返回 (是否成功, 需等待秒数)"""
    global _last_request_time
    with _interval_lock:
        now = _time_module.time()
        elapsed = now - _last_request_time
        if elapsed >= AI_REQUEST_INTERVAL:
            _last_request_time = now
            return True, 0
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

    _local_data_cache = "\n".join(lines)
    return _local_data_cache


def refresh_local_data():
    """强制刷新本地数据缓存（数据变更后调用）"""
    global _local_data_cache
    _local_data_cache = None
    return _build_local_data()


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
"""


# ══════════════════════════════════════════════════════════
#  系统提示词模板
# ══════════════════════════════════════════════════════════

# 预订前：免费旅行顾问（面向所有微信用户）
TRAVEL_ADVISOR_SYSTEM = f"""你是「{BNB_NAME}」的旅行顾问，位于庐山山上·大林沟路27号。

## 你的身份
- 你是云上·归墅的旅行顾问，热情友好地为每一位咨询者提供帮助
- 你了解庐山的一切：景点、路线、交通、美食、天气、民宿房型
- 你代表云上·归墅民宿的形象，专业但不强行推销

## 民宿基本信息
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 开业：2016年，11间客房，U型三层小楼，带风铃院子
- 评分：携程 4.7分，85条真实住客评价
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」提供精品咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 交通：庐山索道上站步行5分钟，牯岭街步行10分钟，近如琴湖、锦绣谷
- 入住/退房：14:00后入住，12:00前退房，免押金
- 预订：携程/美团/飞猪/大众点评搜索「云上归墅」
- 电话：{BNB_PHONE}

## 回复规则
1. 热情友好，像庐山本地朋友一样提供建议
2. 自然地提到民宿特色，但不要让每句话都像广告
3. 如果用户问及预订，引导至OTA平台搜索「云上归墅」
4. 回复简洁有料，每段不超过300字
5. 适当使用emoji增添亲和力
6. 重要：你只是旅行顾问，不能处理住店服务请求（打扫、叫醒、送餐、维修、续住、退房等）。如果用户提出此类请求，礼貌说明这些服务需预订入住后才能使用，并引导其预订或查看房型

[本地数据 — 以下是云上归墅及庐山周边的准确信息，回答时以此为准]
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
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 开业：2016年，11间客房，U型三层小楼，带风铃院子
- 评分：携程 4.7分，85条真实住客评价
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」仅提供咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 咖啡馆：民宿主理人麦姐亲自打理「三山二水咖啡」
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 交通：庐山索道上站步行5分钟，牯岭街步行10分钟
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 预订：通过携程/美团/飞猪/大众点评等平台
- 前台电话：{BNB_PHONE}

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

## 民宿基本信息
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 开业：2016年，11间客房，U型三层小楼，带风铃院子
- 评分：携程 4.7分，85条真实住客评价
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」仅提供咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 咖啡馆：民宿主理人麦姐亲自打理「三山二水咖啡」
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 交通：庐山索道上站步行5分钟，牯岭街步行10分钟
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 预订：通过携程/美团/飞猪/大众点评等平台
- 前台电话：{BNB_PHONE}

## 你可以帮助客人
- 了解房型和设施，解答住宿相关问题
- 介绍庐山景点和定制游玩路线
- 介绍「三山二水咖啡」菜单和在线点餐
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
- 评分：携程 4.7分，85条真实住客评价
- 新消息：主理人麦姐新推出了季节限定冷萃咖啡
- 优惠：老客回归享有专属折扣，详情咨询前台 {BNB_PHONE}
- 预订：携程/美团/飞猪/大众点评搜索「云上归墅」

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
_conversation_cache = {}  # 内存缓存（热数据）
CONVERSATION_MAX_HISTORY = 20

def _save_conversation(openid: str, role: str, content: str):
    """持久化对话记录到数据库"""
    try:
        from models import SessionLocal, MessageLog
        db = SessionLocal()
        log = MessageLog(openid=openid, message_type=role, content=content[:500], reply=content[:500] if role == 'assistant' else '')
        db.add(log); db.commit(); db.close()
    except Exception:
        warning("对话持久化失败")

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
        debug("对话历史加载失败")
        return []


def _call_ai(system_template: str, user_openid: str, user_message: str) -> str:
    """通用的AI调用函数，自动注入本地数据 + 输入校验 + 并发控制"""
    if not AI_ENABLED:
        return _fallback_reply()

    # ── 输入校验 ──
    validation_error = _validate_and_sanitize(user_openid, user_message)
    if validation_error:
        return validation_error

    # ── 消息截断 ──
    if len(user_message) > AI_MAX_MESSAGE_LENGTH:
        user_message = user_message[:AI_MAX_MESSAGE_LENGTH]

    # ── 请求间隔控制 ──
    ok, wait = _try_acquire_slot()
    if not ok:
        warning(f"[AI] 间隔限制 需等待{wait}s openid={user_openid[:12]}")
        return (
            f"⏳ AI 管家正在回复上一条消息，请 {wait} 秒后再试～\n\n"
            f"您也可以：\n"
            "  · 回复数字 1-5 使用快捷功能\n"
            "  · 回复「人工」转接人工客服"
        )

    try:
        # 注入本地数据
        local_data = _get_local_data()
        system_prompt = system_template.replace("{LOCAL_DATA}", local_data)

        if user_openid not in _conversation_cache:
            _conversation_cache[user_openid] = _load_conversation(user_openid)

        history = _conversation_cache[user_openid]

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": user_message})

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
        # 检测截断：兼容 Anthropic(stop_reason) 和 DeepSeek/OpenAI(finish_reason)
        stop = getattr(response, 'stop_reason', None) or getattr(response, 'finish_reason', '')
        truncated = stop in ('max_tokens', 'length', 'stop')

        # 记录截断状态（用于「继续生成」）
        if truncated:
            _pending_continuation[user_openid] = system_template

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})
        _save_conversation(user_openid, "user", user_message)
        _save_conversation(user_openid, "assistant", ai_reply[:500])

        if len(history) > 20:
            _conversation_cache[user_openid] = history[-20:]

        if truncated:
            ai_reply += "\n\n📝 [回复较长，回复「继续」查看完整内容]"

        return ai_reply

    except Exception as e:
        log_error("ai.call", str(e), exc_info=True)
        return _fallback_reply()


# ══════════════════════════════════════════════════════════
#  三个模式的公开接口
# ══════════════════════════════════════════════════════════

def chat_travel_advisor(user_openid: str, user_message: str) -> str:
    """预订前：免费旅行顾问（所有人可用）"""
    return _call_ai(TRAVEL_ADVISOR_SYSTEM, user_openid, user_message)


def chat_pre_arrival(user_openid: str, user_message: str) -> str:
    """已预订但未入住：到店前管家"""
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()
    return _call_ai(PRE_ARRIVAL_SYSTEM, user_openid, user_message)


def chat(user_openid: str, user_message: str) -> str:
    """已入住：专属AI管家（需预订验证）"""
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()
    return _call_ai(GUEST_BUTLER_SYSTEM, user_openid, user_message)


def chat_post_stay(user_openid: str, user_message: str) -> str:
    """离店后：复购关怀"""
    return _call_ai(POST_STAY_SYSTEM, user_openid, user_message)


# ══════════════════════════════════════════════════════════
#  主动推送消息生成
# ══════════════════════════════════════════════════════════

def generate_pre_arrival_message(guest_name: str, check_in_date: str, room_name: str = "", room_code: str = "") -> str:
    """生成到店前偏好收集消息（入住前1-2天发送）"""
    greeting = f"{guest_name}好" if guest_name else "您好"
    room_line = f"您预订的「{room_name}」已经为您准备好啦～" if room_name else "您的房间已经为您准备好啦～"

    msg = (
        f"🏔️ {greeting}！云上·归墅期待您的到来～\n\n"
        f"📅 入住日期：{check_in_date}\n"
        f"{room_line}\n\n"
        f"为了给您更好的入住体验，想提前了解一下：\n\n"
        f"🚗 交通方式：自驾还是索道上山？需要停车指引吗？\n"
        f"🕐 预计到达：大概几点到呢？方便我们提前迎接～\n"
        f"🛏️ 房间偏好：对温度、枕头高度有什么偏好吗？\n"
        f"☕ 咖啡口味：喜欢什么风味的咖啡？麦姐可以提前准备～\n\n"
        f"直接回复告诉我就好，我来帮您安排 ✨\n\n"
    )
    if room_code:
        msg += (
            f"🔑 房间共享码：{room_code}\n"
            f"💡 同住人复制此码回复「绑定房间 {room_code}」即可共享AI管家全部功能～\n\n"
        )
    msg += (
        f"📍 地址：庐山山上·大林沟路27号\n"
        f"📞 任何问题随时致电：{BNB_PHONE}"
    )
    return msg


def generate_post_stay_message(guest_name: str, room_name: str = "") -> str:
    """生成离店后关怀消息（退房后1天发送）"""
    greeting = f"{guest_name}" if guest_name else "朋友"
    stay_memory = f"在「{room_name}」度过的时光" if room_name else "在云上·归墅度过的时光"

    return (
        f"☁️ {greeting}，早上好～\n\n"
        f"{stay_memory}，希望给您留下了美好的庐山回忆 🏔️\n\n"
        f"✨ 麦姐说：下次回来，一定要尝尝新出的季节限定冷萃哦～老客回归有专属优惠～\n\n"
        f"💬 分享体验：如果方便的话，欢迎在携程/小红书分享入住体验，您的评价对我们很珍贵～\n\n"
        f"回复「游记」获取庐山四季美景，或者直接跟我聊聊您的感受～\n\n"
        f"期待在云海深处再次相遇 ☁️"
    )


def generate_review_request_message(guest_name: str, room_name: str = "") -> str:
    """生成好评邀请消息（退房后30分钟）"""
    greeting = f"{guest_name}" if guest_name else "亲爱的客人"

    return (
        f"🌟 {greeting}，感谢您选择云上·归墅～\n\n"
        f"希望{room_name + '的' if room_name else ''}山景和麦姐的咖啡给您留下了美好回忆 ☕🏔️\n\n"
        f"如果您觉得满意，方便的话给我们写条好评吧～\n\n"
        f"📝 携程评价：ctrip.com 搜索「云上归墅」\n"
        f"📕 小红书：搜索「云上归墅」分享入住体验\n\n"
        f"每一条好评都是对我们最大的鼓励 ❤️\n"
        f"期待您再次归来，老客有专属优惠哦～"
    )


# ══════════════════════════════════════════════════════════
#  辅助函数
# ══════════════════════════════════════════════════════════

def _booking_required_reply() -> str:
    """未预订用户尝试使用全功能管家时的回复"""
    return (
        "🎐 专属管家需要预订后解锁\n\n"
        "我是云上·归墅的专属管家，为已确认预订的客人提供全套智能服务～\n\n"
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


def reset_conversation(user_openid: str):
    """重置用户对话历史"""
    if user_openid in _conversation_cache:
        del _conversation_cache[user_openid]
    _pending_continuation.pop(user_openid, None)


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
