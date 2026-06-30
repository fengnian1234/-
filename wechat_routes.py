"""
微信服务器接入 — 三民宿各一路径，返回 XML
"""
import hashlib
from app import app
from flask import request, abort
from config import WECHAT_TOKEN, BNB_CONFIGS
from bnb_context import set_current_bnb
from services.logger import error as log_error


def _verify_wechat(bnb_id="guishu"):
    """微信服务器签名验证（按民宿取对应 token）"""
    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")
    echostr = request.args.get("echostr", "")

    cfg = BNB_CONFIGS.get(bnb_id, BNB_CONFIGS["guishu"])
    token = cfg.get("wechat_token", WECHAT_TOKEN)
    tmp_list = sorted([token, timestamp, nonce])
    tmp_str = "".join(tmp_list)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

    if tmp_str == signature:
        return echostr
    else:
        abort(403)


def _handle_wechat_post(bnb_id="guishu"):
    """处理微信消息推送（注入 bnb_id 到消息处理）"""
    set_current_bnb(bnb_id)  # 显式设置请求级 BnB 上下文
    from wechatpy import parse_message
    from wechatpy.replies import TextReply
    from wechat import handle_wechat_message, handle_event

    xml_data = request.data
    if not xml_data:
        return "success"

    try:
        msg = parse_message(xml_data)
    except Exception:
        log_error("wechat.parse_xml", "XML解析失败", exc_info=True)
        return "success"

    msg_type = getattr(msg, 'type', '')

    try:
        if msg_type == 'text':
            reply_text = handle_wechat_message(msg, bnb_id=bnb_id)
            reply = TextReply(content=reply_text, message=msg)
        elif msg_type == 'event':
            reply_text = handle_event(msg, bnb_id=bnb_id)
            if not reply_text:
                return "success"
            reply = TextReply(content=reply_text, message=msg)
        elif msg_type == 'image':
            reply = TextReply(
                content="📷 收到您的图片啦～\n如需人工服务，请回复「人工」转接客服～",
                message=msg,
            )
        elif msg_type == 'voice':
            reply = TextReply(
                content="🎤 收到您的语音消息～\n我暂时还不能听懂语音，请用文字告诉我您的需求吧～",
                message=msg,
            )
        else:
            reply = TextReply(
                content="收到您的消息啦～回复「帮助」查看我能为您做什么～",
                message=msg,
            )

        xml_response = reply.render()
        return xml_response

    except Exception:
        log_error("wechat.handle_message", "消息处理异常", exc_info=True)
        return "success"


# 归墅（旧路径兼容）
@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    if request.method == "GET":
        return _verify_wechat("guishu")
    return _handle_wechat_post("guishu")

# 三家民宿独立路径
@app.route("/wechat/gs", methods=["GET", "POST"])
def wechat_gs():
    if request.method == "GET":
        return _verify_wechat("guishu")
    return _handle_wechat_post("guishu")

@app.route("/wechat/sj", methods=["GET", "POST"])
def wechat_sj():
    if request.method == "GET":
        return _verify_wechat("shanji")
    return _handle_wechat_post("shanji")

@app.route("/wechat/dlw", methods=["GET", "POST"])
def wechat_dlw():
    if request.method == "GET":
        return _verify_wechat("donglinwai")
    return _handle_wechat_post("donglinwai")
