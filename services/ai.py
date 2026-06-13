"""
AI智能对话服务 v3 — 全链路AI管家
- 预订前：免费旅行顾问（所有人可用）
- 预订后：专属AI管家（已预订客人独享）
- 离店后：复购关怀 + 好评引导
"""
import json
from config import (
    ANTHROPIC_API_KEY, AI_MODEL, AI_ENABLED, AI_REQUIRES_BOOKING,
    BNB_NAME, BNB_ADDRESS, BNB_PHONE,
)
from services.booking import is_ai_enabled, get_booking_by_openid


# ══════════════════════════════════════════════════════════
#  系统提示词
# ══════════════════════════════════════════════════════════

# 预订前：免费旅行顾问（面向所有微信用户）
TRAVEL_ADVISOR_PROMPT = f"""你是「{BNB_NAME}」的旅行顾问，位于庐山山上·大林沟路27号。

## 你的身份
- 你是云上·归墅的旅行顾问，热情友好地为每一位咨询者提供帮助
- 你了解庐山的一切：景点、路线、交通、美食、天气、民宿房型
- 你代表云上·归墅民宿的形象，专业但不强行推销

## 民宿基本信息
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 开业：2016年，11间客房，U型三层小楼
- 评分：携程 4.7分 · 85条评价
- 房型（8种）：特惠单人间(¥388)、特惠标准间(¥388)、知还标准间(¥488)、山野大床房(¥588)、山景·精致大床房(¥688)、清舍·露台大床房(¥788)、田园家庭房(¥788)、室雅茶香套房(¥988)
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」提供精品咖啡、茶饮、简餐轻食
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 位置：索道上站步行5分钟，牯岭街步行10分钟，近如琴湖、锦绣谷
- 预订：携程/美团/飞猪/大众点评搜索「云上归墅」
- 电话：{BNB_PHONE}

## 回复规则
1. 热情友好，像庐山本地朋友一样提供建议
2. 自然地提到民宿特色，但不要让每句话都像广告
3. 如果用户问及预订，引导至OTA平台搜索「云上归墅」
4. 回复简洁有料，每段不超过300字
5. 适当使用emoji和庐山元素
6. 用中文回复
"""

# 预订后：专属AI管家（当前功能，已预订客人独享）
GUEST_BUTLER_PROMPT = f"""你是「{BNB_NAME}」的智能管家，位于庐山山上·庐山风景名胜区大林沟路27号。

## 你的身份
- 你是云上·归墅的专属AI管家，服务已确认预订的尊贵客人
- 你对庐山的一草一木都很熟悉，对民宿的每个房间都了如指掌
- 你叫得出客人的名字，记得他们的偏好，像老友一样贴心

## 民宿基本信息
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 开业：2016年，11间客房，U型三层小楼
- 评分：携程 4.7分 · 85条评价
- 房型（8种）：特惠单人间(¥388)、特惠标准间(¥388)、知还标准间(¥488)、山野大床房(¥588)、山景·精致大床房(¥688)、清舍·露台大床房(¥788)、田园家庭房(¥788)、室雅茶香套房(¥988)
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」仅提供精品咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 预订：通过携程/美团/飞猪/大众点评等平台
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 咖啡馆：民宿主理人麦姐亲自打理「三山二水咖啡」
- 位置：索道上站步行5分钟，牯岭街步行10分钟，近如琴湖、锦绣谷

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
3. 如果被问到不确定的信息，建议咨询前台（{BNB_PHONE}）
4. 适当使用emoji让回复更生动
5. 记住：你是已预订客人的专属管家
6. 用中文回复
7. 关于订房：引导至携程/美团/飞猪/大众点评等平台
8. 关于早餐/正餐：说明民宿仅提供咖啡简餐，推荐周边餐厅
9. 关于加床/婴儿床：明确告知不可加床、不提供婴儿床
"""

# 离店后：复购关怀
POST_STAY_PROMPT = f"""你是「{BNB_NAME}」的客户关怀顾问，负责与已退房的客人保持温暖的联系。

## 你的身份
- 你是云上·归墅的客户关怀顾问，感谢客人曾选择入住
- 你像老朋友一样关心客人的近况，自然地邀请他们再次回来
- 你不是推销员——你传递的是山居生活的温暖和想念

## 民宿最新动态（可在对话中自然提及）
- 评分：携程 4.7分 · 85条评价
- 新消息：主理人麦姐新推出了季节限定冷萃咖啡
- 优惠：老客回归享有专属折扣，详情咨询前台 {BNB_PHONE}
- 预订：携程/美团/飞猪/大众点评搜索「云上归墅」

## 回复规则
1. 温暖自然，不催促，像老朋友叙旧
2. 可以聊聊庐山现在的季节风景，勾起美好回忆
3. 自然提及复购优惠，但不是每句话都推销
4. 如果客人对上次入住有反馈，认真倾听并感谢
5. 用中文回复，保持亲切感
"""


# ══════════════════════════════════════════════════════════
#  对话缓存
# ══════════════════════════════════════════════════════════
_conversation_cache = {}


def _call_ai(system_prompt: str, user_openid: str, user_message: str) -> str:
    """通用的AI调用函数"""
    if not AI_ENABLED:
        return _fallback_reply()

    try:
        if user_openid not in _conversation_cache:
            _conversation_cache[user_openid] = []

        history = _conversation_cache[user_openid]

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": user_message})

        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=15.0)

        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=800,
            messages=messages,
            temperature=0.7,
            timeout=15.0,
        )

        ai_reply = response.content[0].text

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})

        if len(history) > 20:
            _conversation_cache[user_openid] = history[-20:]

        return ai_reply

    except Exception as e:
        return _fallback_reply()


# ══════════════════════════════════════════════════════════
#  三个模式的公开接口
# ══════════════════════════════════════════════════════════

def chat_travel_advisor(user_openid: str, user_message: str) -> str:
    """
    预订前：免费旅行顾问（所有人可用）
    回答庐山旅游、房型咨询等问题，自然地引导预订
    """
    return _call_ai(TRAVEL_ADVISOR_PROMPT, user_openid, user_message)


def chat(user_openid: str, user_message: str) -> str:
    """
    预订后：专属AI管家（需预订验证）
    全功能管家，处理住宿相关的一切问题
    """
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()
    return _call_ai(GUEST_BUTLER_PROMPT, user_openid, user_message)


def chat_post_stay(user_openid: str, user_message: str) -> str:
    """
    离店后：复购关怀
    温暖联系，邀请回归，收集反馈
    """
    return _call_ai(POST_STAY_PROMPT, user_openid, user_message)


# ══════════════════════════════════════════════════════════
#  主动推送消息生成
# ══════════════════════════════════════════════════════════

def generate_pre_arrival_message(guest_name: str, check_in_date: str, room_name: str = "") -> str:
    """生成到店前偏好收集消息（入住前1-2天发送）"""
    greeting = f"{guest_name}好" if guest_name else "您好"
    room_line = f"您预订的「{room_name}」已经为您准备好啦～" if room_name else "您的房间已经为您准备好啦～"

    return (
        f"🏔️ {greeting}！云上·归墅期待您的到来～\n\n"
        f"📅 入住日期：{check_in_date}\n"
        f"{room_line}\n\n"
        f"为了给您更好的入住体验，想提前了解一下：\n\n"
        f"🚗 *交通方式*：自驾还是索道上山？需要停车指引吗？\n"
        f"🕐 *预计到达*：大概几点到呢？方便我们提前迎接～\n"
        f"🛏️ *房间偏好*：对温度、枕头高度有什么偏好吗？\n"
        f"☕ *咖啡口味*：喜欢什么风味的咖啡？麦姐可以提前准备～\n\n"
        f"直接回复告诉我就好，我来帮您安排 ✨\n\n"
        f"📍 地址：庐山山上·大林沟路27号\n"
        f"📞 任何问题随时致电：{BNB_PHONE}"
    )


def generate_post_stay_message(guest_name: str, room_name: str = "") -> str:
    """生成离店后关怀消息（退房后1天发送）"""
    greeting = f"{guest_name}" if guest_name else "朋友"
    stay_memory = f"在「{room_name}」度过的时光" if room_name else "在云上·归墅度过的时光"

    return (
        f"☁️ {greeting}，早上好～\n\n"
        f"{stay_memory}，希望给您留下了美好的庐山回忆 🏔️\n\n"
        f"✨ *麦姐说*：下次回来，一定要尝尝新出的季节限定冷萃哦～老客回归有专属优惠～\n\n"
        f"💬 *分享体验*：如果方便的话，欢迎在携程/小红书分享入住体验，您的评价对我们很珍贵～\n\n"
        f"回复「游记」获取庐山四季美景，或者直接跟我聊聊您的感受～\n\n"
        f"期待在云海深处再次相遇 ☁️"
    )


def generate_review_request_message(guest_name: str, room_name: str = "") -> str:
    """生成好评邀请消息（退房后30分钟，原有功能增强）"""
    greeting = f"{guest_name}" if guest_name else "亲爱的客人"

    return (
        f"🌟 {greeting}，感谢您选择云上·归墅～\n\n"
        f"希望{room_name + '的' if room_name else ''}山景和麦姐的咖啡给您留下了美好回忆 ☕🏔️\n\n"
        f"如果您觉得满意，方便的话给我们写条好评吧～\n\n"
        f"📝 *携程评价*：ctrip.com 搜索「云上归墅」\n"
        f"📕 *小红书*：搜索「云上归墅」分享入住体验\n\n"
        f"每一条好评都是对我们最大的鼓励 ❤️\n"
        f"期待您再次归来，老客有专属优惠哦～"
    )


# ══════════════════════════════════════════════════════════
#  辅助函数
# ══════════════════════════════════════════════════════════

def _booking_required_reply() -> str:
    """未预订用户尝试使用全功能管家时的回复"""
    return (
        "🎐 *专属管家需要预订后解锁*\n\n"
        "我是云上·归墅的专属管家，为已确认预订的客人提供全套智能服务～\n\n"
        "💡 *您现在可以使用*：\n"
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


def reset_conversation(user_openid: str):
    """重置用户对话历史"""
    if user_openid in _conversation_cache:
        del _conversation_cache[user_openid]


def get_conversation_mode(user_openid: str) -> str:
    """
    根据用户预订状态返回AI模式
    Returns: 'travel_advisor' | 'guest_butler' | 'post_stay'
    """
    if not is_ai_enabled(user_openid):
        # 检查是否曾入住过（离店状态）
        booking = get_booking_by_openid(user_openid, include_checked_out=True)
        if booking and booking.get('status') == 'checked_out':
            return 'post_stay'
        return 'travel_advisor'
    return 'guest_butler'
