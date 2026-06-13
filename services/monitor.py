"""
多平台信息收集子Agent（要求6）
收集美团/大众点评/飞猪/携程/小红书/抖音上关于云上·归墅民宿的信息
通过 AnySearch API 实时搜索各平台评价和提及
"""
import json
import re
import time
from datetime import datetime
import requests

from models import SessionLocal, PlatformMention
from services.logger import info, warning, debug
from config import MONITOR_PLATFORMS, MONITOR_KEYWORDS, MONITOR_SEARCH_QUERY, BNB_NAME

# AnySearch API 配置
ANYSEARCH_ENDPOINT = "https://api.anysearch.com/mcp"
ANYSEARCH_API_KEY = ""  # 留空使用匿名访问（1000次/天免费额度）


def _call_anysearch_api(tool_name: str, arguments: dict) -> str:
    """调用 AnySearch JSON-RPC 2.0 API"""
    headers = {"Content-Type": "application/json"}
    if ANYSEARCH_API_KEY:
        headers["Authorization"] = f"Bearer {ANYSEARCH_API_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    try:
        resp = requests.post(ANYSEARCH_ENDPOINT, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return f"[API Error] {data['error'].get('message', str(data['error']))}"
        result = data.get("result", {})
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                return item.get("text", "")
        return json.dumps(result, indent=2, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        return "[Error] 无法连接 AnySearch API"
    except requests.exceptions.Timeout:
        return "[Error] API 请求超时"
    except Exception as e:
        return f"[Error] {str(e)}"


def _extract_rating(text: str) -> float:
    """从文本中提取评分（如 4.6分、评分4.8、4.6好）"""
    patterns = [
        r'(\d+\.?\d*)\s*分[^钟]',     # 4.6分 (排除"分钟")
        r'评分[：:]?\s*(\d+\.?\d*)',    # 评分4.8
        r'好\s*(\d+\.?\d*)',           # 好4.6
        r'(\d+\.?\d*)\s*好',           # 4.6好
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            val = float(m.group(1))
            if 1.0 <= val <= 5.0:
                return val
    return None


def _extract_review_count(text: str) -> int:
    """从文本中提取评价数量"""
    patterns = [
        r'(\d+)\s*条[评点]',    # 74条评价 / 156条点评
        r'(\d+)\s*条评论',
        r'(\d+)\s*个评价',
        r'(\d+)\s*条好评',
        r'(\d+)\s*review',
        r'(\d+)\s*reviews',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def _parse_search_results(text: str, platform: str) -> list:
    """解析 AnySearch 返回的 Markdown 为结构化数据"""
    mentions = []
    if not text or text.startswith("[Error]") or text.startswith("[API Error]"):
        return mentions

    # 按搜索结果条目拆分（## 开头或 ### 开头）
    blocks = re.split(r'\n(?=#{1,3}\s+\d+\.)', text)

    for block in blocks:
        # 过滤搜索结果表头
        if re.match(r'#{1,3}\s*Search Results', block):
            continue
        if block.strip().startswith("AnySearch") or "powered by" in block.lower():
            continue

        # 提取标题和URL
        title_match = re.search(r'(?:#{1,3}\s+\d+\.\s*)?(.+?)(?:\n|$)', block)
        url_match = re.search(r'\*\*URL\*\*:\s*(https?://[^\s\n]+)', block)
        # 也匹配 Markdown 链接格式 [text](url)
        md_link = re.search(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', block)

        title = title_match.group(1).strip() if title_match else ""
        url = url_match.group(1) if url_match else (md_link.group(2) if md_link else "")
        if not title or len(title) > 200:
            continue
        # 过滤无URL的纯表头块
        if not url:
            continue

        content = block[:500].replace(title, "").strip()

        # 提取评分和评价数
        rating = _extract_rating(block)
        count = _extract_review_count(block)

        # 情感分析
        sentiment = "neutral"
        positive_words = ["很棒", "好评", "推荐", "满意", "惊喜", "不错", "舒服", "干净", "好"]
        negative_words = ["差评", "失望", "糟糕", "脏", "吵", "不值", "坑", "差"]
        pos_score = sum(1 for w in positive_words if w in block)
        neg_score = sum(1 for w in negative_words if w in block)
        if pos_score > neg_score:
            sentiment = "positive"
        elif neg_score > pos_score:
            sentiment = "negative"

        mentions.append({
            "type": "review" if (rating or count) else "mention",
            "title": title[:200],
            "content": content[:500],
            "rating": rating,
            "author": "",
            "url": url,
            "sentiment": sentiment,
            "review_count": count,
        })

    return mentions


def search_platform_mentions(query: str = "") -> dict:
    """
    通过 AnySearch 搜索各平台关于民宿的信息
    每个平台独立搜索，结果存入数据库
    """
    if not query:
        query = MONITOR_SEARCH_QUERY

    results = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "bnb_name": BNB_NAME,
        "platforms": {},
    }

    # 为每个平台执行独立搜索
    for platform in MONITOR_PLATFORMS:
        platform_query = f"{query} {platform}"
        info(f"🔍 正在搜索 {platform}...")

        try:
            raw_text = _call_anysearch_api("search", {
                "query": platform_query,
                "max_results": 5,
            })

            # 解析搜索结果
            mentions = _parse_search_results(raw_text, platform)

            # 保存到数据库
            if mentions:
                stored_count = store_mentions(platform, mentions)
                info(f"    {platform}: 找到 {len(mentions)} 条，存入 {stored_count} 条新记录")
            else:
                info(f"    {platform}: 无有效结果")

            # 计算评分
            ratings = [m["rating"] for m in mentions if m["rating"]]
            review_counts = [m.get("review_count", 0) for m in mentions if m.get("review_count")]

            results["platforms"][platform] = {
                "query": platform_query,
                "mentions_count": len(mentions),
                "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "top_mentions": mentions[:3],
                "search_url": _get_search_url(platform, query),
            }

            # 避免请求过快
            time.sleep(0.5)

        except Exception as e:
            warning(f"    {platform}: 搜索失败 - {e}")
            results["platforms"][platform] = {
                "query": platform_query,
                "mentions_count": 0,
                "avg_rating": None,
                "top_mentions": [],
                "search_url": _get_search_url(platform, query),
                "error": str(e),
            }

    return results


def _get_platform_domain(platform: str) -> str:
    """获取平台域名"""
    domains = {
        "美团": "meituan.com",
        "大众点评": "dianping.com",
        "飞猪": "fliggy.com",
        "携程": "ctrip.com",
        "小红书": "xiaohongshu.com",
        "抖音": "douyin.com",
    }
    return domains.get(platform, "")


def _get_search_url(platform: str, query: str) -> str:
    """生成各平台搜索链接"""
    encoded = query.replace(" ", "+")
    urls = {
        "美团": f"https://www.meituan.com/s/{encoded}",
        "大众点评": f"https://www.dianping.com/search/keyword/{encoded}",
        "飞猪": f"https://www.fliggy.com/search?keyword={encoded}",
        "携程": f"https://www.ctrip.com/search?keyword={encoded}",
        "小红书": f"https://www.xiaohongshu.com/search_result?keyword={encoded}",
        "抖音": f"https://www.douyin.com/search/{encoded}",
    }
    return urls.get(platform, "")


def store_mentions(platform: str, mentions: list):
    """将收集到的提及存储到数据库（URL哈希去重）"""
    db = SessionLocal()
    try:
        count = 0
        for m in mentions:
            url = m.get("url", "")
            if url:
                existing = db.query(PlatformMention).filter(
                    PlatformMention.platform == platform,
                    PlatformMention.url == url,
                ).first()
                if existing:
                    continue

            mention = PlatformMention(
                platform=platform,
                mention_type=m.get("type", "review"),
                title=m.get("title", ""),
                content=m.get("content", ""),
                rating=m.get("rating"),
                author=m.get("author", ""),
                url=url,
                sentiment=m.get("sentiment", "neutral"),
                collected_at=datetime.utcnow(),
            )
            db.add(mention)
            count += 1

        db.commit()
        return count
    finally:
        db.close()


def get_mentions_summary() -> dict:
    """
    获取各平台信息汇总（给主Agent提供信息支持）
    返回结构化的平台声誉数据
    """
    db = SessionLocal()
    try:
        summary = {
            "bnb_name": BNB_NAME,
            "updated_at": datetime.utcnow().isoformat(),
            "platforms": {},
        }

        for platform in MONITOR_PLATFORMS:
            mentions = db.query(PlatformMention).filter(
                PlatformMention.platform == platform
            ).order_by(PlatformMention.collected_at.desc()).limit(20).all()

            if not mentions:
                summary["platforms"][platform] = {
                    "total": 0, "avg_rating": None,
                    "positive": 0, "neutral": 0, "negative": 0,
                    "latest": None,
                    "search_url": _get_search_url(platform, MONITOR_SEARCH_QUERY),
                }
                continue

            ratings = [m.rating for m in mentions if m.rating]
            sentiments = [m.sentiment for m in mentions]

            summary["platforms"][platform] = {
                "total": len(mentions),
                "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "positive": sentiments.count("positive"),
                "neutral": sentiments.count("neutral"),
                "negative": sentiments.count("negative"),
                "latest": mentions[0].to_dict() if mentions else None,
                "search_url": _get_search_url(platform, MONITOR_SEARCH_QUERY),
            }

        # 计算总体评分（加权平均）
        all_ratings = []
        for p in summary["platforms"].values():
            if p["avg_rating"] and p["total"] > 0:
                all_ratings.append((p["avg_rating"], p["total"]))

        if all_ratings:
            total_weight = sum(w for _, w in all_ratings)
            summary["overall_rating"] = round(
                sum(r * w for r, w in all_ratings) / total_weight, 1
            )
        else:
            summary["overall_rating"] = None

        return summary
    finally:
        db.close()


def generate_monitor_report() -> str:
    """
    生成平台监控报告（给主Agent使用）
    用于客服回答"我们家口碑怎么样"之类的问题
    """
    summary = get_mentions_summary()

    if summary["overall_rating"] is None:
        return (
            "目前暂无主流平台的评价数据汇总。\n\n"
            "云上·归墅民宿位于庐山山上·庐山风景名胜区大林沟路27号，"
            "欢迎您在携程/美团/飞猪/大众点评搜索查看最新评价～\n\n"
            "💡 回复「收集口碑」触发平台信息实时收集"
        )

    lines = [
        f"📊 *{BNB_NAME} · 各平台口碑概览*\n",
        f"⭐ 综合评分：{summary['overall_rating']}/5.0\n",
    ]

    for platform, data in summary["platforms"].items():
        if data["total"] > 0:
            rating_str = f"{data['avg_rating']}/5.0" if data['avg_rating'] else "暂无评分"
            sentiment_str = f"👍{data['positive']} 😊{data['neutral']} 👎{data['negative']}"
            lines.append(
                f"*{platform}*：{rating_str}（{data['total']}条）\n"
                f"  {sentiment_str}\n"
            )

    lines.append("\n💡 回复「平台评价」查看各平台详细评价链接")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  子Agent接口（供外部AI Agent调用）
# ══════════════════════════════════════════════════════════
def agent_collect_platform_info() -> dict:
    """
    子Agent入口：收集所有主流平台信息
    返回给主Agent的结构化数据
    """
    # 1. 执行搜索收集（真实AnySearch调用）
    search_results = search_platform_mentions()

    # 2. 获取数据库中的历史汇总
    db_summary = get_mentions_summary()

    # 3. 合并信息
    return {
        "search_results": search_results,
        "historical_summary": db_summary,
        "monitor_platforms": MONITOR_PLATFORMS,
        "bnb_info": {
            "name": BNB_NAME,
            "address": "庐山山上·庐山风景名胜区大林沟路27号",
            "search_keywords": MONITOR_KEYWORDS,
        },
        "collection_timestamp": datetime.utcnow().isoformat(),
        "powered_by": "AnySearch API",
    }


def get_platform_review_links() -> dict:
    """获取所有平台评价链接汇总"""
    from config import REVIEW_PLATFORMS
    return REVIEW_PLATFORMS
