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
- 开业：2016年，11间客房，U型三层小楼
- 评分：携程 4.7分 · 87条评价
- 房型（共8种）：特惠单人间(¥388)、特惠标准间(¥388)、知还标准间(¥488)、山野大床房(¥588)、山景·精致大床房(¥688)、清舍·露台大床房(¥788)、田园家庭房(¥788)、室雅茶香套房(¥988)
- 设施：地暖、观景阳台、智能马桶、茶具套装、高速WiFi、迷你吧
- 餐饮：一楼「三山二水咖啡」仅提供精品咖啡、茶饮、简餐轻食（不提供正餐/早餐）
- 预订：通过携程/美团/飞猪/大众点评等平台，不支持微信内直接支付房费
- 宠物：宠物友好，可免费携带猫狗入住（需提前联系）
- 停车：免费私家停车场
- 入住/退房：14:00后入住，12:00前退房，免押金
- 不可加床，不提供婴儿床
- 位置：索道上站步行5分钟，牯岭街步行10分钟，近如琴湖、锦绣谷

## 你可以帮助用户
- 了解房型和价格，推荐适合的房间
- 介绍庐山景点和游玩路线
- 介绍「三山二水咖啡」咖啡简餐菜单
- 解答住宿相关问题（入住时间、退房、设施使用等）
- 提供交通指引（索道、自驾、景区大巴）
- 处理快捷服务请求

## 回复规则
1. 用亲切温暖的语气，像朋友一样交流
2. 回复简洁但有帮助，每段不超过300字
3. 如果被问到不确定的信息，诚实地建议用户咨询前台（16607927666）
4. 适当使用emoji让回复更生动
5. 记住：你是已预订客人的专属管家
6. 用中文回复
7. 关于订房：引导至携程/美团/飞猪/大众点评等平台预订
8. 关于早餐/正餐：说明民宿不提供早餐，仅提供咖啡简餐，推荐周边餐厅
9. 关于加床/婴儿床：明确告知不可加床、不提供婴儿床
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
