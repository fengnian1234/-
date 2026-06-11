"""
AI智能对话服务 - 使用 Anthropic Claude 进行自然语言问答
要求1：仅在用户有确认预订后解锁AI对话
"""
import json
from config import (
    ANTHROPIC_API_KEY, AI_MODEL, AI_ENABLED, AI_REQUIRES_BOOKING,
    BNB_NAME, BNB_ADDRESS,
)
from services.booking import is_ai_enabled


# 系统提示词 - 定义AI的角色和行为
SYSTEM_PROMPT = f"""你是「{BNB_NAME}」的智能管家，位于庐山山上·庐山风景名胜区大林沟路27号。

## 你的身份
- 你是云上·归墅的专属AI管家，热情、专业、贴心
- 你只对已确认预订的客人开放服务
- 你对庐山的一草一木都很熟悉，对民宿的每个房间都了如指掌

## 民宿基本信息
- 名称：{BNB_NAME}（云上·归墅民宿）
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 特色：坐拥庐山云海景观，静谧典雅的精品民宿
- 房型：大床房、双床房、家庭套房、云景套房、庭院房等
- 设施：地暖、观景阳台、茶室、书吧
- 餐饮：仅提供咖啡和简餐（不提供正餐），可通过服务号点餐
- 预订：通过携程/美团/飞猪/大众点评等平台，不支持微信内直接支付房费

## 你可以帮助用户
- 了解房型和价格，推荐适合的房间
- 介绍庐山景点和游玩路线
- 介绍咖啡简餐菜单
- 解答住宿相关问题（入住时间、退房、设施使用等）
- 提供交通指引
- 处理快捷服务请求

## 回复规则
1. 用亲切温暖的语气，像朋友一样交流
2. 回复简洁但有帮助，每段不超过300字
3. 如果被问到不确定的信息，诚实地建议用户咨询前台人工客服
4. 适当使用emoji让回复更生动
5. 记住：你是已预订客人的专属管家
6. 用中文回复
7. 关于订房：引导至携程/美团/飞猪/大众点评等平台预订
8. 关于正餐：说明本民宿仅提供咖啡简餐，推荐周边餐厅
"""

# 对话上下文缓存
_conversation_cache = {}


def chat(user_openid: str, user_message: str) -> str:
    """
    AI智能对话（要求1：需预订验证）
    返回AI生成的回复文本，未预订用户收到引导提示
    """
    # 要求1：检查预订验证
    if AI_REQUIRES_BOOKING and not is_ai_enabled(user_openid):
        return _booking_required_reply()

    if not AI_ENABLED:
        return _fallback_reply()

    try:
        if user_openid not in _conversation_cache:
            _conversation_cache[user_openid] = []

        history = _conversation_cache[user_openid]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": user_message})

        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=800,
            messages=messages,
            temperature=0.7,
        )

        ai_reply = response.content[0].text

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})

        if len(history) > 20:
            _conversation_cache[user_openid] = history[-20:]

        return ai_reply

    except Exception as e:
        return _fallback_reply()


def _booking_required_reply() -> str:
    """未预订用户尝试使用AI时的回复（要求1）"""
    return (
        "🎐 *AI智能管家需要预订后解锁*\n\n"
        "我是云上·归墅的AI管家，为已确认预订的客人\n"
        "提供专属的智能服务～\n\n"
        "🏨 *预订方式*：\n"
        "在携程/美团/飞猪/大众点评搜索「云上归墅」\n"
        "预订成功后，回复「绑定预订」即可解锁AI管家\n\n"
        "💡 预订前您也可以：\n"
        "  · 回复「1」查看房型展示\n"
        "  · 回复「3」查看游玩攻略\n"
        "  · 回复「4」查看快捷服务\n"
        "  · 回复「人工」转接人工客服"
    )


def _fallback_reply() -> str:
    """AI不可用时的回退回复"""
    return (
        "很抱歉，智能管家暂时休息中～ 😴\n\n"
        "您可以：\n"
        "  · 回复数字 1-5 使用快捷功能\n"
        "  · 回复「人工」转接人工客服\n"
        "  · 拨打前台电话直接咨询\n\n"
        "给您带来不便敬请谅解～"
    )


def reset_conversation(user_openid: str):
    """重置用户对话历史"""
    if user_openid in _conversation_cache:
        del _conversation_cache[user_openid]
