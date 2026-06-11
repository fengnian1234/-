"""
AI智能对话服务 - 使用 Anthropic Claude 进行自然语言问答
当关键词匹配无法处理时，交由AI进行智能回复
"""
import json
from config import ANTHROPIC_API_KEY, AI_MODEL, AI_ENABLED, BNB_NAME, BNB_ADDRESS


# 系统提示词 - 定义AI的角色和行为
SYSTEM_PROMPT = f"""你是「{BNB_NAME}」民宿的智能客服助手，位于江西省九江市庐山风景区牯岭镇。

## 你的身份
- 你是云上归墅的专属AI管家，热情、专业、贴心
- 你对庐山的一草一木都很熟悉，对民宿的每个房间都了如指掌

## 民宿基本信息
- 名称：{BNB_NAME}（云上归墅）
- 地址：{BNB_ADDRESS}
- 特色：坐拥庐山云海景观，静谧典雅的精品民宿
- 房型：大床房、双床房、家庭套房、云景套房等
- 设施：地暖、观景阳台、茶室、书吧、餐厅

## 你可以帮助用户
- 了解房型和价格，推荐适合的房间
- 介绍庐山景点和游玩路线
- 推荐周边美食和特色小吃
- 解答住宿相关问题（入住时间、退房、设施使用等）
- 提供交通指引和天气建议

## 回复规则
1. 用亲切温暖的语气，像朋友一样交流
2. 回复简洁但有帮助，每段不超过300字
3. 如果被问到不确定的信息，诚实地建议用户咨询前台人工客服
4. 适当使用emoji让回复更生动
5. 在合适的时候引导用户使用快捷服务（如回复"服务"查看快捷服务）
6. 记住：你是民宿管家，不是通用AI助手，围绕民宿和庐山展开对话
7. 用中文回复
"""

# 对话上下文缓存（简单实现，生产环境可用Redis）
_conversation_cache = {}


def chat(user_openid: str, user_message: str) -> str:
    """
    AI智能对话
    返回AI生成的回复文本
    """
    if not AI_ENABLED:
        return _fallback_reply()

    try:
        # 获取或创建对话历史
        if user_openid not in _conversation_cache:
            _conversation_cache[user_openid] = []

        history = _conversation_cache[user_openid]

        # 构建消息
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 加入最近5轮对话
        for h in history[-10:]:
            messages.append(h)

        # 加入当前用户消息
        messages.append({"role": "user", "content": user_message})

        # 调用 Anthropic API
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=800,
            messages=messages,
            temperature=0.7,
        )

        ai_reply = response.content[0].text

        # 保存对话历史
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_reply})

        # 限制历史长度
        if len(history) > 20:
            _conversation_cache[user_openid] = history[-20:]

        return ai_reply

    except Exception as e:
        # AI调用失败时回退
        return _fallback_reply()


def _fallback_reply() -> str:
    """AI不可用时的回退回复"""
    return (
        "很抱歉，智能客服暂时休息中～ 😴\n\n"
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
