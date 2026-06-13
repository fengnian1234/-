"""
多平台信息收集子Agent（要求6）
收集美团/大众点评/飞猪/携程/小红书/抖音上关于云上·归墅民宿的信息
v3.3: opencli 平台精准搜索 + WebSearch (Bing) 通用兜底，AnySearch 已移除
"""
import json
import re
import subprocess
import time
from datetime import datetime

import requests

from models import SessionLocal, PlatformMention
from services.logger import info, warning, debug
from config import MONITOR_PLATFORMS, MONITOR_KEYWORDS, MONITOR_SEARCH_QUERY, BNB_NAME

# WebSearch 通用搜索（Bing，国内可直接访问，免费无限额）
WEBSEARCH_ENDPOINT = "https://www.bing.com/search"

# ── 平台 → 搜索策略映射 ──────────────────────────────────────
# 有 opencli 适配器的平台 → 精准搜索（结构化数据）
# 无适配器的平台 → WebSearch 通用搜索
PLATFORM_SEARCH_CONFIG = {
    "携程": {
        "type": "opencli",
        "cmd": ["opencli", "ctrip", "search", "{query}", "-f", "json", "--limit", "5"],
        "needs_browser": False,
    },
    "大众点评": {
        "type": "opencli",
        "cmd": ["opencli", "dianping", "search", "{keyword}", "--city", "九江", "-f", "json", "--limit", "5"],
        "needs_browser": True,
    },
    "小红书": {
        "type": "opencli",
        "cmd": ["opencli", "xiaohongshu", "search", "{query}", "-f", "json", "--limit", "5"],
        "needs_browser": True,
    },
    "微博": {
        "type": "opencli",
        "cmd": ["opencli", "weibo", "search", "{keyword}", "-f", "json", "--limit", "5"],
        "needs_browser": True,
    },
    "知乎": {
        "type": "opencli",
        "cmd": ["opencli", "zhihu", "search", "{keyword}", "-f", "json", "--limit", "5"],
        "needs_browser": True,
    },
    # 暂无 opencli 适配器 → 走 WebSearch
    "美团": {"type": "websearch"},
    "飞猪": {"type": "websearch"},
    "抖音": {"type": "websearch"},
}


# ══════════════════════════════════════════════════════════
#  搜索后端
# ══════════════════════════════════════════════════════════

def _search_via_opencli(platform: str, query: str, max_results: int = 5) -> tuple:
    """
    通过 opencli 原生适配器精准搜索特定平台
    返回 (结构化 mentions 列表, 使用的后端名称)
    """
    config = PLATFORM_SEARCH_CONFIG.get(platform, {})
    if config.get("type") != "opencli":
        return [], "no_adapter"

    cmd_template = config["cmd"]
    cmd = [arg.replace("{query}", query).replace("{keyword}", query) for arg in cmd_template]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            # 判断是否是 cookie 未配置
            if "cookie" in stderr.lower() or "browser" in stderr.lower() or "登录" in stderr:
                return [], "opencli_no_cookie"
            debug(f"opencli {platform} 失败: {stderr[:100]}")
            return [], "opencli_error"

        raw_output = result.stdout.strip()
        if not raw_output:
            return [], "opencli_empty"

        # 清理 opencli 输出中的非 JSON 行（如升级提示）
        lines = raw_output.split('\n')
        json_lines = []
        in_json = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('[') or stripped.startswith('{'):
                in_json = True
            if in_json:
                json_lines.append(stripped)
            if stripped.endswith(']') or stripped.endswith('}'):
                if in_json:
                    # Don't break — there might be multiple JSON blocks
                    pass
        raw_json = '\n'.join(json_lines) if json_lines else raw_output

        mentions = _parse_opencli_results(raw_json, platform)
        if mentions:
            return mentions, f"opencli:{platform}"
        return [], "opencli_empty"

    except FileNotFoundError:
        warning("opencli 未安装或不在 PATH 中")
        return [], "opencli_not_found"
    except subprocess.TimeoutExpired:
        warning(f"opencli {platform} 搜索超时")
        return [], "opencli_timeout"
    except Exception as e:
        warning(f"opencli {platform} 异常: {e}")
        return [], "opencli_error"


def _search_via_websearch(query: str, max_results: int = 5) -> str:
    """
    通过 Bing 搜索（免费、无限额、无需 API Key，国内可直接访问）
    返回 Markdown 格式的搜索结果文本
    """
    params = {"q": query, "setlang": "zh-Hans", "count": str(max_results)}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(WEBSEARCH_ENDPOINT, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        results = []
        results.append(f"## Search Results for: {query}")

        # Bing 搜索结果结构: <li class="b_algo"> → <h2><a href="URL">TITLE</a></h2>
        #                                        → <div class="b_attribution"><cite>URL</cite></div>
        #                                        → <div class="b_caption"><p>SNIPPET</p></div>
        algo_pattern = re.compile(
            r'<li[^>]*class="b_algo"[^>]*>(.*?)</li>\s*(?=<li[^>]*class="b_algo"|\s*</ol>)',
            re.DOTALL
        )
        algos = algo_pattern.findall(html)

        for i, algo in enumerate(algos[:max_results]):
            h2_match = re.search(
                r'<h2[^>]*>.*?<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                algo, re.DOTALL
            )
            if not h2_match:
                continue

            url = h2_match.group(1)
            title = re.sub(r'<[^>]+>', '', h2_match.group(2)).strip()

            caption_match = re.search(
                r'<div[^>]*class="b_caption"[^>]*>(.*?)</div>',
                algo, re.DOTALL
            )
            snippet = ""
            if caption_match:
                snippet = re.sub(r'<[^>]+>', '', caption_match.group(1)).strip()
                snippet = re.sub(r'&ensp;|&#0183;|·', ' ', snippet)
                snippet = re.sub(r'\s+', ' ', snippet).strip()

            results.append(f"### {i+1}. {title}")
            results.append(f"**URL**: {url}")
            if snippet:
                results.append(f"{snippet[:300]}")
            results.append("")

        return "\n".join(results) if len(results) > 1 else ""

    except requests.exceptions.ConnectionError:
        return "[Error] 无法连接 WebSearch (Bing)"
    except requests.exceptions.Timeout:
        return "[Error] WebSearch 请求超时"
    except Exception as e:
        return f"[Error] WebSearch: {str(e)}"


def _search_platform(platform: str, query: str, max_results: int = 5) -> tuple:
    """
    为指定平台选择最佳搜索后端
    优先级: opencli 原生适配器 → WebSearch (Bing) 通用搜索
    返回 (mentions列表或Markdown文本, 后端名称)
    """
    config = PLATFORM_SEARCH_CONFIG.get(platform, {"type": "websearch"})

    if config["type"] == "opencli":
        # 尝试 opencli 精准搜索
        mentions, backend = _search_via_opencli(platform, query, max_results)
        if mentions:
            return mentions, backend
        # opencli 失败 → 降级到 WebSearch
        reason = backend.replace("opencli_", "")
        debug(f"{platform}: opencli 不可用({reason})，降级到 WebSearch")

    # WebSearch 通用搜索
    platform_query = f"{query} {platform}"
    raw_text = _search_via_websearch(platform_query, max_results)
    mentions = _parse_websearch_results(raw_text, platform)
    return mentions, "WebSearch"


# ══════════════════════════════════════════════════════════
#  结果解析
# ══════════════════════════════════════════════════════════

def _parse_opencli_results(raw_json: str, platform: str) -> list:
    """
    解析 opencli JSON 输出为统一的 mention 格式
    各平台输出字段不同，需要做字段映射
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        debug(f"opencli {platform} JSON 解析失败")
        return []

    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []

    mentions = []
    for item in data:
        # 字段映射：不同平台 → 统一格式
        title = (
            item.get("title") or item.get("name") or item.get("content") or ""
        )
        url = item.get("url", "")
        author = item.get("author", "") or item.get("user", "") or ""
        rating = None

        # 评分映射
        raw_rating = item.get("rating") or item.get("score") or item.get("avg_rating")
        if raw_rating is not None:
            try:
                rating = float(raw_rating)
                if not (1.0 <= rating <= 5.0):
                    rating = None
            except (ValueError, TypeError):
                pass

        # 评价数映射
        review_count = 0
        raw_count = item.get("reviews") or item.get("review_count") or item.get("likes") or 0
        try:
            review_count = int(raw_count) if raw_count else 0
        except (ValueError, TypeError):
            pass

        # 摘要
        content = item.get("description") or item.get("snippet") or item.get("summary") or ""

        if not title or not url:
            continue

        # 情感分析
        sentiment = _analyze_sentiment(f"{title} {content}")

        mentions.append({
            "type": "review" if (rating or review_count) else "mention",
            "title": str(title)[:200],
            "content": str(content)[:500],
            "rating": rating,
            "author": str(author)[:50],
            "url": str(url)[:500],
            "sentiment": sentiment,
            "review_count": review_count,
        })

    return mentions


def _parse_websearch_results(text: str, platform: str) -> list:
    """解析 Bing 返回的 Markdown 为结构化数据"""
    mentions = []
    if not text or text.startswith("[Error]"):
        return mentions

    blocks = re.split(r'\n(?=#{1,3}\s+\d+\.)', text)

    for block in blocks:
        if re.match(r'#{1,3}\s*Search Results', block):
            continue

        title_match = re.search(r'(?:#{1,3}\s+\d+\.\s*)?(.+?)(?:\n|$)', block)
        url_match = re.search(r'\*\*URL\*\*:\s*(https?://[^\s\n]+)', block)
        md_link = re.search(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', block)

        title = title_match.group(1).strip() if title_match else ""
        url = url_match.group(1) if url_match else (md_link.group(2) if md_link else "")
        if not title or len(title) > 200 or not url:
            continue

        content = block[:500].replace(title, "").strip()
        rating = _extract_rating(block)
        count = _extract_review_count(block)
        sentiment = _analyze_sentiment(block)

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


def _extract_rating(text: str) -> float:
    """从文本中提取评分（如 4.6分、评分4.8）"""
    patterns = [
        r'(\d+\.?\d*)\s*分[^钟]',
        r'评分[：:]?\s*(\d+\.?\d*)',
        r'好\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*好',
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
        r'(\d+)\s*条[评点]',
        r'(\d+)\s*条评论',
        r'(\d+)\s*个评价',
        r'(\d+)\s*review',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def _analyze_sentiment(text: str) -> str:
    """简单情感分析"""
    positive_words = ["很棒", "好评", "推荐", "满意", "惊喜", "不错", "舒服", "干净", "好"]
    negative_words = ["差评", "失望", "糟糕", "脏", "吵", "不值", "坑", "差"]
    pos_score = sum(1 for w in positive_words if w in text)
    neg_score = sum(1 for w in negative_words if w in text)
    if pos_score > neg_score:
        return "positive"
    elif neg_score > pos_score:
        return "negative"
    return "neutral"


# ══════════════════════════════════════════════════════════
#  主搜索入口
# ══════════════════════════════════════════════════════════

def search_platform_mentions(query: str = "") -> dict:
    """
    搜索各平台关于民宿的信息
    策略: opencli 原生适配器优先 → WebSearch (Bing) 通用兜底
    """
    if not query:
        query = MONITOR_SEARCH_QUERY

    results = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "bnb_name": BNB_NAME,
        "search_backend": "opencli + WebSearch",
        "platforms": {},
    }

    for platform in MONITOR_PLATFORMS:
        info(f"🔍 正在搜索 {platform}...")

        try:
            mentions, backend = _search_platform(platform, query, max_results=5)

            if mentions:
                stored_count = store_mentions(platform, mentions)
                info(f"    {platform} [{backend}]: 找到 {len(mentions)} 条，存入 {stored_count} 条新记录")
            else:
                info(f"    {platform} [{backend}]: 无有效结果")

            ratings = [m["rating"] for m in mentions if m["rating"]]
            results["platforms"][platform] = {
                "query": f"{query} {platform}",
                "mentions_count": len(mentions),
                "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "top_mentions": mentions[:3],
                "search_url": _get_search_url(platform, query),
                "backend": backend,
            }

            time.sleep(1.0)

        except Exception as e:
            warning(f"    {platform}: 搜索失败 - {e}")
            results["platforms"][platform] = {
                "query": f"{query} {platform}",
                "mentions_count": 0,
                "avg_rating": None,
                "top_mentions": [],
                "search_url": _get_search_url(platform, query),
                "error": str(e),
            }

    return results


# ══════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════

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
        "微博": f"https://s.weibo.com/weibo?q={encoded}",
        "知乎": f"https://www.zhihu.com/search?type=content&q={encoded}",
    }
    return urls.get(platform, "")


def store_mentions(platform: str, mentions: list):
    """将收集到的提及存储到数据库（URL去重）"""
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
    """获取各平台信息汇总"""
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

        # 总体评分（加权平均）
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
    """生成平台监控报告（给主Agent / 微信客服使用）"""
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


def agent_collect_platform_info() -> dict:
    """
    子Agent入口：收集所有主流平台信息
    返回给主Agent的结构化数据
    """
    search_results = search_platform_mentions()
    db_summary = get_mentions_summary()

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
        "powered_by": "opencli (平台精准搜索) + WebSearch/Bing (通用兜底)",
    }


def get_platform_review_links() -> dict:
    """获取所有平台评价链接汇总"""
    from config import REVIEW_PLATFORMS
    return REVIEW_PLATFORMS
