"""
多平台信息收集子Agent（要求6）
收集美团/大众点评/飞猪/携程/小红书/抖音上关于云上·归墅民宿的信息
通过搜索引擎API + 网页抓取来汇总各平台评价和提及
"""
import json
import hashlib
import time
from datetime import datetime
from models import SessionLocal, PlatformMention
from config import MONITOR_PLATFORMS, MONITOR_KEYWORDS, MONITOR_SEARCH_QUERY, BNB_NAME


def search_platform_mentions(query: str = "") -> dict:
    """
    通过搜索收集各平台关于民宿的信息
    实际部署时需要接入搜索API（如 Bing Search API / SerpAPI）
    当前版本提供框架和模拟数据结构
    """
    if not query:
        query = MONITOR_SEARCH_QUERY

    results = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "bnb_name": BNB_NAME,
        "platforms": {},
    }

    # 为每个平台生成搜索结果摘要
    for platform in MONITOR_PLATFORMS:
        platform_query = f"{query} site:{_get_platform_domain(platform)}"
        results["platforms"][platform] = {
            "query": platform_query,
            "mentions_count": 0,
            "avg_rating": None,
            "top_mentions": [],
            "search_url": _get_search_url(platform, query),
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
    """将收集到的提及存储到数据库"""
    db = SessionLocal()
    try:
        count = 0
        for m in mentions:
            # 使用URL哈希去重
            url_hash = hashlib.md5(
                m.get("url", "").encode()
            ).hexdigest()

            existing = db.query(PlatformMention).filter(
                PlatformMention.platform == platform,
                PlatformMention.url == m.get("url", ""),
            ).first()

            if not existing:
                mention = PlatformMention(
                    platform=platform,
                    mention_type=m.get("type", "review"),
                    title=m.get("title", ""),
                    content=m.get("content", ""),
                    rating=m.get("rating"),
                    author=m.get("author", ""),
                    url=m.get("url", ""),
                    sentiment=m.get("sentiment", "neutral"),
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

        # 计算总体评分
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
            "欢迎您在携程/美团/飞猪/大众点评搜索查看最新评价～"
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
                f"*{platform}*：{rating_str}（{data['total']}条评价）\n"
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
    # 1. 执行搜索收集
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
        "note": "实际部署时接入搜索API（Bing/SERP）和平台API以获取实时数据",
    }


def get_platform_review_links() -> dict:
    """获取所有平台评价链接汇总"""
    return {
        "携程": {
            "name": "携程旅行",
            "review_url": "https://hotels.ctrip.com/hotel/dianping/云上归墅",
            "icon": "🏨",
        },
        "美团": {
            "name": "美团民宿",
            "review_url": "https://hotel.meituan.com/dianping/云上归墅",
            "icon": "🏠",
        },
        "飞猪": {
            "name": "飞猪旅行",
            "review_url": "https://www.fliggy.com/review/云上归墅",
            "icon": "✈️",
        },
        "大众点评": {
            "name": "大众点评",
            "review_url": "https://www.dianping.com/shop/云上归墅/review",
            "icon": "⭐",
        },
        "小红书": {
            "name": "小红书",
            "review_url": "https://www.xiaohongshu.com/search_result?keyword=云上归墅",
            "icon": "📕",
        },
        "抖音": {
            "name": "抖音",
            "review_url": "https://www.douyin.com/search/云上归墅",
            "icon": "🎵",
        },
    }
