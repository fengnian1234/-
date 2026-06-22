"""
多平台信息收集子Agent（要求6）
收集美团/大众点评/飞猪/携程/小红书/抖音上关于云上·归墅民宿的信息
v3.3: opencli 平台精准搜索 + WebSearch (Bing) 通用兜底，AnySearch 已移除
"""
import json
import os
import re
import subprocess
import time
import hashlib
from datetime import datetime

import requests

from models import SessionLocal, PlatformMention
from services.logger import info, warning, debug
from config import MONITOR_PLATFORMS, MONITOR_KEYWORDS, MONITOR_SEARCH_QUERY, BNB_NAME

# 确保 subprocess 能找到 opencli（npm 全局安装路径）
_NPM_BIN = os.path.expandvars(r"%APPDATA%\npm")
_SUBPROCESS_ENV = os.environ.copy()
if _NPM_BIN not in _SUBPROCESS_ENV.get("PATH", ""):
    _SUBPROCESS_ENV["PATH"] = _NPM_BIN + os.pathsep + _SUBPROCESS_ENV.get("PATH", "")

# WebSearch 通用搜索（Bing，国内可直接访问，免费无限额）
WEBSEARCH_ENDPOINT = "https://www.bing.com/search"
# 兜底时按平台加 site: 限域搜索 + 排除噪音词
WEBSEARCH_SITE_FILTERS = {
    "美团": "site:meituan.com",
    "飞猪": "site:fliggy.com",
    "抖音": "site:douyin.com",
}

# 无关域名黑名单（云服务/游戏/技术 等与民宿无关的站点）
IRRELEVANT_DOMAINS = {
    "mihoyo.com", "sr.mihoyo.com", "cloud.tencent.com", "cg.163.com",
    "aliyun.com", "aliyun.com", "huaweicloud.com", "qcloud.com",
    "baiduyun.com", "yun.baidu.com", "ksyun.com", "ucloud.cn",
    "qingcloud.com", "qiniu.com", "azure.com", "aws.amazon.com",
    "cloud.google.com", "cloud.baidu.com", "ctyun.cn", "ecloud.cn",
    "volcengine.com", "bytecdn.cn", "myqcloud.com", "dnspod.cn",
    "coding.net", "gitee.com", "csdn.net", "juejin.cn", "segmentfault.com",
    "zhihu.com/question",  # 知乎问题页（非民宿相关）
    "wikipedia.org", "baike.baidu.com",  # 百科页
}

# 无关标题关键词（匹配任一即过滤）
IRRELEVANT_TITLE_PATTERNS = [
    r'云游戏', r'云计算', r'云服务', r'云平台', r'云服务器', r'云存储',
    r'云原生', r'云数据库', r'云安全', r'云网络', r'云桌面', r'云迁移',
    r'腾讯云', r'阿里云', r'华为云', r'百度云', r'京东云', r'金山云',
    r'米哈游', r'miHoYo', r'星穹铁道', r'崩坏', r'原神', r'绝区零',
    r'SaaS', r'IaaS', r'PaaS', r'CDN加速', r'GPU云', r'弹性云',
    r'域名注册', r'备案', r'SSL证书', r'对象存储', r'CDN',
    r'云解决方案', r'上云', r'云原生', r'容器服务', r'微服务',
    r'数据中台', r'业务中台', r'低代码', r'无服务器',
]

# 旅游/酒店/民宿 相关域名白名单 — URL 不含这些时，需标题也包含旅游关键词
TRAVEL_RELEVANT_DOMAINS = {
    "ctrip.com", "trip.com", "meituan.com", "dianping.com",
    "fliggy.com", "alitrip.com", "xiaohongshu.com", "xhslink.com",
    "douyin.com", "weibo.com", "zhihu.com", "qunar.com",
    "booking.com", "agoda.com", "tripadvisor.com", "tripadvisor.cn",
    "mafengwo.cn", "qyer.com", "elong.com", "tuniu.com",
    "airbnb.com", "bnb.com", "xiaozhu.com", "muniao.com",
    "bilibili.com", "kuaishou.com", "ixigua.com",
}

# 旅游相关关键词 — 用于非旅游域名的二次校验
TRAVEL_KEYWORDS = [
    "民宿", "酒店", "旅馆", "客栈", "住宿", "客房", "庐山", "旅游",
    "度假", "旅行", "出游", "攻略", "游记", "景点", "景区", "游玩",
    "探店", "打卡", "推荐", "评价", "体验", "入住", "退房", "预订",
]
WEBSEARCH_EXCLUDE_TERMS = (
    " -腾讯云 -阿里云 -华为云 -百度云 -京东云 -金山云 -UCloud -青云 -七牛云"
    " -云计算 -云服务 -云平台 -云游戏 -云服务器 -云存储 -云原生 -云数据库 -云安全 -云网络"
    " -米哈游 -miHoYo -云产品 -云端 -网易云音乐 -云电脑 -云手机 -云备份"
    " -CDN -SaaS -IaaS -PaaS -企业云 -政务云 -云函数 -云开发 -云解决方案"
    " -星穹铁道 -崩坏 -原神 -云·原神 -绝区零 -云·绝区零"
    " -云渲染 -GPU云 -弹性云 -私有云 -混合云 -云桌面 -云堡垒机"
    " -云磁盘 -云硬盘 -云备份 -云容灾 -云迁移 -云监控 -云日志"
    " -云通信 -云直播 -云点播 -云呼叫 -云会议"
    " -云API -云SDK -云CLI -云IDE"
    " -云加速 -云防护 -云WAF -云防火墙"
)

# ── 平台 → 搜索策略映射 ──────────────────────────────────────
# 所有平台优先 opencli browser (Chrome直接搜索+截图)
# browser 不可用时降级到 opencli 原生适配器 → WebSearch 兜底
PLATFORM_SEARCH_CONFIG = {
    "携程": {
        "type": "opencli",
        "cmd": ["opencli.cmd", "ctrip", "search", "{query}", "-f", "json", "--limit", "5"],
        "query_override": "庐山 云上归墅",
    },
    "大众点评": {
        "type": "opencli",
        "cmd": ["opencli.cmd", "dianping", "search", "{query}", "--city", "九江", "-f", "json", "--limit", "5"],
        "query_override": "云上·归墅",
    },
    "小红书": {
        "type": "opencli",
        "cmd": ["opencli.cmd", "xiaohongshu", "search", "{query}", "-f", "json", "--limit", "5"],
    },
    "微博": {
        "type": "opencli",
        "cmd": ["opencli.cmd", "weibo", "search", "{query}", "-f", "json", "--limit", "5"],
        "query_override": "云上归墅",
    },
    "知乎": {
        "type": "opencli",
        "cmd": ["opencli.cmd", "zhihu", "search", "{keyword}", "-f", "json", "--limit", "5"],
        "query_override": "庐山民宿推荐",
    },
    "飞猪": {"type": "websearch"},
    # 暂无有效搜索方式 → 跳过
    "美团": {"type": "skip"},
    "抖音": {"type": "skip"},
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
            cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
            env=_SUBPROCESS_ENV,
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


def _take_browser_screenshot(platform: str, query: str) -> tuple:
    """仅截取一张浏览器截图，不提取内容。返回 (mentions, screenshots, backend)"""
    from urllib.parse import quote
    search_url = _get_search_url(platform, query)
    hotel_urls = {
        "携程": f"https://hotels.ctrip.com/hotel/search?keyword={quote(query)}",
        "飞猪": f"https://travelsearch.fliggy.com/index.htm?searchType=hotel&keyword={quote(query)}",
    }
    url = hotel_urls.get(platform, search_url)
    if not url:
        return [], [], "no_url"

    session = f"bnb_ss_{platform}"
    try:
        result = subprocess.run(
            ["opencli.cmd", "browser", session, "open", url],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25,
            env=_SUBPROCESS_ENV,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        if result.returncode != 0:
            return [], [], "browser_not_connected"

        time.sleep(3)

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshot_dir = os.path.join(project_root, "local_data", "images", "monitor")
        os.makedirs(screenshot_dir, exist_ok=True)
        filename = f"{platform}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(screenshot_dir, filename)

        subprocess.run(
            ["opencli.cmd", "browser", session, "screenshot", path],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15,
            env=_SUBPROCESS_ENV,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        if os.path.exists(path) and os.path.getsize(path) > 100:
            return [], [os.path.join("local_data", "images", "monitor", filename)], "screenshot_ok"
        return [], [], "screenshot_failed"
    except Exception:
        return [], [], "screenshot_error"


def _search_via_browser(platform: str, query: str, max_results: int = 5) -> tuple:
    """
    通过 opencli browser 直接访问平台搜索页并提取内容（不截图）
    返回 (mentions 列表, [], 使用的后端名称)
    """
    search_url = _get_search_url(platform, query)
    # 对携程/飞猪用酒店搜索URL（需要正确编码）
    from urllib.parse import quote
    encoded_q = quote(query)
    hotel_urls = {
        "携程": f"https://hotels.ctrip.com/hotel/search?keyword={encoded_q}",
        "飞猪": f"https://travelsearch.fliggy.com/index.htm?searchType=hotel&keyword={encoded_q}",
    }
    url = hotel_urls.get(platform, search_url)
    if not url:
        return [], [], "no_url"

    session = f"bnb_{platform}"

    def _run(cmd_args, timeout=30):
        """运行 opencli 命令"""
        result = subprocess.run(
            ["opencli.cmd"] + cmd_args,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout,
            env=_SUBPROCESS_ENV,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        return result

    try:
        # 1. 打开搜索页
        info(f"   🌐 打开 {platform} 搜索页: {url[:80]}...")
        result = _run(["browser", session, "open", url], timeout=25)
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "not connected" in error_msg.lower():
                return [], [], "browser_not_connected"
            debug(f"   browser {platform} open 失败: {error_msg[:100]}")
            return [], [], "browser_open_error"

        # 2. 等待页面渲染 + 滚动加载更多内容
        time.sleep(5)
        for scroll_count in range(3):
            try:
                _run(["browser", session, "scroll", "down"], timeout=8)
                time.sleep(2)
            except Exception:
                pass

        # 3. 提取页面内容
        content = ""
        try:
            extract_result = _run(["browser", session, "extract"], timeout=20)
            if extract_result.returncode == 0 and extract_result.stdout.strip():
                try:
                    wrapper = json.loads(extract_result.stdout.strip())
                    content = wrapper.get("content", extract_result.stdout)
                except json.JSONDecodeError:
                    content = extract_result.stdout.strip()[:5000]
        except Exception as e:
            debug(f"   browser {platform} extract 异常: {e}")

        # 4. 解析内容
        if content and len(content) > 30:
            mentions = _parse_browser_extract(content, platform, query)
        else:
            mentions = []

        backend = f"browser:{platform}"
        info(f"   {platform} [browser]: {len(mentions)} 条提及")
        return mentions, [], backend

    except subprocess.TimeoutExpired:
        warning(f"   browser {platform} 超时")
        return [], [], "browser_timeout"
    except Exception as e:
        warning(f"   browser {platform} 异常: {e}")
        return [], [], "browser_error"


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


# ══════════════════════════════════════════════════════════
#  二级深度采集
#  小红书 → note 详情 | 微博 → post 详情 | 携程 → 酒店详情页
# ══════════════════════════════════════════════════════════

def _deep_dive_ctrip_detail(mentions: list, query: str) -> list:
    """
    对携程搜索结果，打开酒店点评(dianping)二级页面提取结构化评价。
    每条评价独立存储，包含对应的文字和图片。
    """
    new_mentions = []  # 产出多条目：每个酒店拆成多条独立评价
    for m in mentions[:3]:
        hotel_id = m.get("url", "").split("hotelid=")[-1] if "hotelid=" in m.get("url", "") else ""
        if not hotel_id:
            new_mentions.append(m)
            continue

        # 使用携程酒店点评二级页面（用户说的“二级界面”）
        dianping_url = f"https://hotels.ctrip.com/hotel/dianping/{hotel_id}.html"
        session = f"ctrip_dp_{hotel_id}"

        try:
            # 1. 打开点评页
            subprocess.run(
                ["opencli.cmd", "browser", session, "open", dianping_url],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                env=_SUBPROCESS_ENV,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            time.sleep(5)

            # 2. 滚动加载更多评价
            for _ in range(5):
                subprocess.run(
                    ["opencli.cmd", "browser", session, "scroll", "down"],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10,
                    env=_SUBPROCESS_ENV,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                )
                time.sleep(1.5)

            # 3. 提取页面内容
            extract_result = subprocess.run(
                ["opencli.cmd", "browser", session, "extract"],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                env=_SUBPROCESS_ENV,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            content = ""
            if extract_result.returncode == 0:
                try:
                    wrapper = json.loads(extract_result.stdout.strip())
                    content = wrapper.get("content", "")
                except json.JSONDecodeError:
                    content = extract_result.stdout.strip()[:15000]

            if not content or len(content) < 80:
                # 提取失败，保留原始搜索条目
                new_mentions.append(m)
                continue

            # 4. 解析结构化评价：每条评价 = 用户名 + 评分 + 日期 + 正文 + 图片
            parsed_reviews = _parse_ctrip_dianping_reviews(content, hotel_id)

            if parsed_reviews:
                info(f"   🏨 携程点评页: {len(parsed_reviews)}条带图评价 | {m.get('title', '')[:40]}")
                # 每一条评价作为独立的 PlatformMention 存储
                for rev in parsed_reviews:
                    new_m = {
                        "type": "review",
                        "title": f"[{rev.get('date', '')}] {rev.get('author', '住客')}: {rev.get('text', '')[:80]}",
                        "content": rev.get("text", "")[:600],
                        "rating": rev.get("rating"),
                        "author": rev.get("author", ""),
                        "url": dianping_url,
                        "sentiment": rev.get("sentiment", "neutral"),
                        "review_count": 1,
                        "image_urls": rev.get("images", []),
                    }
                    new_mentions.append(new_m)
            else:
                # 解析不出结构化评价 → 用旧逻辑兜底
                m["content"] = content[:500]
                # 仍然尝试提取图片
                img_urls = _extract_ctrip_images(content)
                if img_urls:
                    m["image_urls"] = img_urls
                    info(f"   🖼️ 携程点评页提取 {len(img_urls)} 张图片(非结构化)")
                new_mentions.append(m)

        except subprocess.TimeoutExpired:
            debug(f"   ⏱️ 携程点评页超时: {hotel_id}")
            new_mentions.append(m)
        except Exception as e:
            debug(f"   ⚠️ 携程点评页异常: {e}")
            new_mentions.append(m)

        time.sleep(1.5)

    return new_mentions


def _extract_ctrip_images(content: str) -> list:
    """从携程页面提取图片URL"""
    img_urls = []
    patterns = [
        r'https://dimg\d+\.c-ctrip\.com/[^\s<>"\']+\.(?:jpg|jpeg|png|webp)',
        r'https://ak-d\.ctrip\.com/[^\s<>"\']+\.(?:jpg|jpeg|png|webp)',
        r'<img[^>]+src=["\'](https://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']',
        r'!\[\]\((https://[^\)]+\.(?:jpg|jpeg|png|webp)[^\)]*)\)',
    ]
    for pat in patterns:
        img_urls.extend(re.findall(pat, content, re.IGNORECASE))
    seen = set()
    unique = []
    for u in img_urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique[:10]


def _parse_ctrip_dianping_reviews(content: str, hotel_id: str) -> list:
    """
    从携程点评页(browser extract内容)解析出结构化评价。
    每条评价包含: author, rating, date, text, images, sentiment
    """
    reviews = []

    # 去掉导航/页脚噪音（取中间评价区域）
    # 携程点评页的关键标记
    review_section_start = content.find("住客点评")
    if review_section_start < 0:
        review_section_start = content.find("用户点评")
    if review_section_start < 0:
        review_section_start = content.find("全部点评")
    if review_section_start >= 0:
        content = content[review_section_start:review_section_start + 12000]

    # 策略1: 按"点评关键词"或"入住日期"模式分割
    # 典型携程点评格式: "2026年6月 家庭亲子" → 评分 → 正文 → 图片
    # 先找到日期标记分割
    date_marks = re.findall(r'\d{4}年\d{1,2}月', content)
    if not date_marks:
        date_marks = re.findall(r'\d{4}-\d{2}', content)

    if date_marks:
        # 按日期标记分割
        parts = re.split(r'(\d{4}年\d{1,2}月|\d{4}-\d{2})', content)
        for i in range(1, len(parts) - 1, 2):
            date_str = parts[i].strip()
            block = parts[i+1] if i+1 < len(parts) else ""

            if len(block) < 20:
                continue

            # 提取评分: 如 "5.0分" "4.8 很好"
            rating = None
            rm = re.search(r'(\d+\.?\d*)\s*分|(\d+\.?\d*)\s*很好|(\d+\.?\d*)\s*超棒', block)
            if rm:
                try:
                    rating = float(rm.group(1) or rm.group(2) or rm.group(3))
                    if rating > 5.0:
                        rating = rating / 2 if rating <= 10 else None
                except (ValueError, TypeError):
                    pass

            # 提取用户名
            author = ""
            am = re.search(r'([^\s]{2,10})\s*(?:入住|家庭|情侣|朋友|商务|独自)', block)
            if am:
                author = am.group(1)
            # Try "M49****99" pattern
            am2 = re.search(r'(M\d+\*+\d+|匿名|[A-Z][a-z]+\*+)', block)
            if am2:
                author = am2.group(1)

            # 提取正文（评分之后，图片之前的最长文本段）
            # 去掉评分行
            text_block = re.sub(r'\d+\.?\d*\s*分.*?(?:\n|$)', '', block)
            # 去掉图片URL行
            text_block = re.sub(r'https?://\S+\.(?:jpg|jpeg|png|webp)\S*', '', text_block)
            # 去掉明显的非文本行
            lines = [l.strip() for l in text_block.split('\n') if l.strip()]
            text_lines = [l for l in lines if len(l) > 10 and not l.startswith('http') and not re.match(r'^\d+\.?\d*$', l)]
            text = ' '.join(text_lines)[:500] if text_lines else block[:300]

            if len(text) < 10:
                continue

            # 提取该评价附带的图片URL
            rev_imgs = []
            img_matches = re.findall(
                r'https?://dimg\d+\.c-ctrip\.com/[^\s<>"\']+\.(?:jpg|jpeg|png|webp)',
                block, re.IGNORECASE
            )
            rev_imgs = list(set(img_matches))[:6]

            sentiment = _analyze_sentiment(text)

            reviews.append({
                "date": date_str,
                "author": author,
                "rating": rating,
                "text": text,
                "images": rev_imgs,
                "sentiment": sentiment,
            })
    else:
        # 策略2: 无日期标记 — 按"分"分割评价块
        parts = re.split(r'\n(?=\d+\.?\d*\s*分)', content)
        for block in parts[1:]:  # 跳过第一个空块
            if len(block) < 20:
                continue
            rating = None
            rm = re.search(r'(\d+\.?\d*)\s*分', block)
            if rm:
                try:
                    rating = float(rm.group(1))
                    if rating > 5.0:
                        rating = rating / 2 if rating <= 10 else None
                except (ValueError, TypeError):
                    pass

            text = block[:500].strip()
            rev_imgs = re.findall(
                r'https?://dimg\d+\.c-ctrip\.com/[^\s<>"\']+\.(?:jpg|jpeg|png|webp)',
                block, re.IGNORECASE
            )
            sentiment = _analyze_sentiment(text)
            reviews.append({
                "date": "",
                "author": "",
                "rating": rating,
                "text": text,
                "images": list(set(rev_imgs))[:6],
                "sentiment": sentiment,
            })

    return reviews[:15]  # 最多15条评价


def _parse_ctrip_detail_reviews(content: str) -> list:
    """从携程详情页提取的文本中解析真实住客评价"""
    reviews = []
    # 寻找 "真实住客点评" 之后的评价内容
    review_start = content.find("真实住客点评")
    if review_start < 0:
        review_start = content.find("住客点评")
    if review_start < 0:
        return reviews

    review_section = content[review_start:review_start + 8000]
    # 按日期模式分割评价: "2026年X月X日" 或 "2025年X月X日"
    date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日)'
    parts = re.split(date_pattern, review_section)

    current_date = ""
    for part in parts:
        part = part.strip()
        if re.match(r'\d{4}年\d{1,2}月\d{1,2}日', part):
            current_date = part
        elif len(part) > 30 and current_date:
            # 这是一个评价内容（>30字符，前面有日期）
            # 清理噪音
            clean = re.sub(r'\!\[\]\([^)]+\)', '', part)  # 去掉图片
            clean = re.sub(r'\s+', ' ', clean).strip()
            if len(clean) > 30 and len(clean) < 1000:
                reviews.append(f"[{current_date}] {clean}")

    return reviews[:10]  # 最多10条


# ══════════════════════════════════════════════════════════
#  小红书 note / 微博 post 深度采集
# ══════════════════════════════════════════════════════════

def _deep_dive_xhs_notes(mentions: list) -> list:
    """对小红书搜索结果，逐条进入 note 详情获取完整正文+标签+图片"""
    enriched = []
    for m in mentions[:5]:
        url = m.get("url", "")
        if not url:
            enriched.append(m)
            continue

        # 转换 search_result URL → explore (note detail) URL
        # search_result URL: .../search_result/{note_id}?xsec_token=TOKEN&xsec_source=
        # note URL needed:   .../explore/{note_id}?xsec_token=TOKEN
        note_url = url
        note_id_match = re.search(r'/search_result/([a-f0-9]+)', url)
        if note_id_match:
            note_id = note_id_match.group(1)
            # 提取 xsec_token
            token_match = re.search(r'xsec_token=([^&\s]+)', url)
            token = token_match.group(1) if token_match else ""
            if token:
                note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={token}"
            else:
                note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
            debug(f"   🔗 小红书URL转换: .../search_result/{note_id[:8]}... → .../explore/{note_id[:8]}...")

        try:
            result = subprocess.run(
                ["opencli.cmd", "xiaohongshu", "note", note_url],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                env=_SUBPROCESS_ENV,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            if result.returncode != 0:
                enriched.append(m)
                continue

            # 解析 YAML-style 输出: "- field: xxx\n  value: yyy"
            fields = {}
            current_field = None
            for line in result.stdout.split('\n'):
                if line.startswith('- field:'):
                    current_field = line.split(':', 1)[1].strip()
                    fields[current_field] = ''
                elif line.startswith('  value:') and current_field:
                    val = line.split(':', 1)[1].strip()
                    if val.startswith('>-'):
                        fields[current_field] = ''  # 多行内容继续
                    elif val.startswith("'") and val.endswith("'"):
                        fields[current_field] = val[1:-1]
                    else:
                        fields[current_field] = val
                elif current_field and fields.get(current_field) is not None:
                    # 多行内容的后续行
                    stripped = line.strip()
                    if stripped and not stripped.startswith('- field:'):
                        fields[current_field] += stripped

            # 用详情数据丰富 mention
            full_content = fields.get("content", "")
            if full_content and len(full_content) > 20:
                m["content"] = full_content[:800]
                m["title"] = fields.get("title", m["title"])
                # likes/collects/comments 作为 review_count
                likes = fields.get("likes", "0")
                try:
                    m["review_count"] = int(likes)
                except (ValueError, TypeError):
                    pass
            # 标签
            tags = fields.get("tags", "")
            if tags:
                m["content"] = (m.get("content", "") + f" [标签: {tags}]")[:800]

            # ── 下载笔记图片（opencli download 命令）──
            note_id_short = ""
            img_note_id_match = re.search(r'/explore/([a-f0-9]+)', note_url)
            if img_note_id_match:
                note_id_short = img_note_id_match.group(1)
            if note_id_short:
                # opencli download 会在 --output 目录内再创建 note_id 子目录
                # 所以 --output 指向 小红书/ 父目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                xhs_parent_dir = os.path.join(project_root, "local_data", "images", "monitor", "小红书")
                os.makedirs(xhs_parent_dir, exist_ok=True)

                try:
                    dl_result = subprocess.run(
                        ["opencli.cmd", "xiaohongshu", "download", note_url,
                         "--output", xhs_parent_dir],
                        capture_output=True, text=True, encoding='utf-8', errors='replace',
                        timeout=120, env=_SUBPROCESS_ENV,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    )
                    if dl_result.returncode == 0:
                        note_img_dir = os.path.join(xhs_parent_dir, note_id_short)
                        local_imgs = []
                        if os.path.isdir(note_img_dir):
                            for fname in sorted(os.listdir(note_img_dir)):
                                if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                                    rel_path = os.path.join("local_data", "images", "monitor", "小红书", note_id_short, fname)
                                    local_imgs.append(rel_path)
                        if local_imgs:
                            m["local_images"] = local_imgs
                            m["image_urls"] = []  # 已下载到本地
                            info(f"   🖼️ 小红书 download {len(local_imgs)} 张图片 → {note_id_short[:12]}...")
                except subprocess.TimeoutExpired:
                    debug(f"   ⏱️ 小红书 download 超时: {note_id_short}")
                except Exception as e:
                    debug(f"   ⚠️ 小红书 download 异常: {e}")

            debug(f"   📝 小红书 note: {fields.get('title', '')[:40]} | 赞{likes}")

        except subprocess.TimeoutExpired:
            debug(f"   ⏱️ 小红书 note 超时: {url[:50]}")
        except Exception as e:
            debug(f"   ⚠️ 小红书 note 异常: {e}")

        enriched.append(m)
        time.sleep(1.0)  # 避免请求太快

    return enriched


def _deep_dive_weibo_posts(mentions: list) -> list:
    """对微博搜索结果，逐条进入 post 详情获取完整正文+图片"""
    enriched = []
    for m in mentions[:5]:
        post_id = m.get("url", "").split("weibo.com/")[-1].split("?")[0] if m.get("url") else ""
        # 从 URL 提取: https://weibo.com/2351601945/QDsm3dSos?...
        # post id 是最后一段不含 query 的路径
        parts = post_id.split("/")
        if len(parts) >= 2:
            post_id = parts[-1]
        post_id = post_id.split("?")[0]

        if not post_id or len(post_id) < 5:
            enriched.append(m)
            continue

        try:
            result = subprocess.run(
                ["opencli.cmd", "weibo", "post", post_id],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                env=_SUBPROCESS_ENV,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            if result.returncode != 0:
                enriched.append(m)
                continue

            fields = {}
            current_field = None
            for line in result.stdout.split('\n'):
                if line.startswith('- field:'):
                    current_field = line.split(':', 1)[1].strip()
                    fields[current_field] = ''
                elif line.startswith('  value:') and current_field:
                    val = line.split(':', 1)[1].strip()
                    if val.startswith('>-'):
                        fields[current_field] = ''
                    elif val.startswith("'") and val.endswith("'"):
                        fields[current_field] = val[1:-1]
                    else:
                        fields[current_field] = val
                elif current_field and fields.get(current_field) is not None:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('- field:'):
                        fields[current_field] += stripped

            full_text = fields.get("text", "")
            if full_text and len(full_text) > 20:
                m["content"] = full_text[:800]
                m["title"] = full_text[:100]  # 取前100字作为标题
                m["author"] = fields.get("author", m.get("author", ""))

            likes = fields.get("likes", "0")
            try:
                m["review_count"] = int(likes)
            except (ValueError, TypeError):
                pass

            # ── 提取帖子内嵌图片（browser 打开帖子页面，提取 sinaimg.cn 图片URL）──
            pic_count = int(fields.get("pic_count", "0"))
            post_url = m.get("url", "")
            if pic_count > 0 and post_url:
                # 使用 browser 打开帖子页面，提取实际图片URL
                session = f"wb_post_{post_id[:8]}_img"
                try:
                    br_open = subprocess.run(
                        ["opencli.cmd", "browser", session, "open", post_url],
                        capture_output=True, text=True, encoding='utf-8', errors='replace',
                        timeout=30, env=_SUBPROCESS_ENV,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    )
                    if br_open.returncode == 0:
                        time.sleep(4)  # 等待图片加载

                        # 滚动加载懒加载图片
                        for _ in range(3):
                            try:
                                subprocess.run(
                                    ["opencli.cmd", "browser", session, "scroll", "down"],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace',
                                    timeout=10, env=_SUBPROCESS_ENV,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                                )
                                time.sleep(1.5)
                            except Exception:
                                pass

                        # 提取页面内容
                        br_ext = subprocess.run(
                            ["opencli.cmd", "browser", session, "extract"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=20, env=_SUBPROCESS_ENV,
                            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                        )
                        if br_ext.returncode == 0:
                            try:
                                wrapper = json.loads(br_ext.stdout.strip())
                                page_content = wrapper.get("content", br_ext.stdout)
                            except json.JSONDecodeError:
                                page_content = br_ext.stdout

                            # 提取 sinaimg.cn 图片URL（真实帖子图片，非UI元素）
                            # 微信/微博帖子图片通常来自 wx*.sinaimg.cn, 用 orj360/large/mw690 等尺寸
                            post_images = re.findall(
                                r'https?://(?:wx\d+|ww\d+)\.sinaimg\.cn/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp|gif)',
                                page_content, re.IGNORECASE
                            )
                            if post_images:
                                # 去重、最多9张（微博限制）
                                m["image_urls"] = list(set(post_images))[:9]
                                info(f"   🖼️ 微博 browser 提取 {len(m['image_urls'])} 张图片 (pic_count={pic_count})")
                            else:
                                debug(f"   ⚠️ 微博 pic_count={pic_count} 但 browser 未提取到图片URL")
                except subprocess.TimeoutExpired:
                    debug(f"   ⏱️ 微博 browser 超时: {post_id}")
                except Exception as e:
                    debug(f"   ⚠️ 微博 browser 异常: {e}")

            debug(f"   📝 微博 post: {full_text[:40]}... | 赞{likes} 图{pic_count}")

        except subprocess.TimeoutExpired:
            debug(f"   ⏱️ 微博 post 超时: {post_id}")
        except Exception as e:
            debug(f"   ⚠️ 微博 post 异常: {e}")

        enriched.append(m)
        time.sleep(1.0)

    return enriched


def _search_platform(platform: str, query: str, max_results: int = 5) -> tuple:
    """
    为指定平台选择最佳搜索后端
    【新优先级】opencli 原生适配器(结构化数据) → 二级深度采集(详情图片+正文) → browser搜索 → WebSearch兜底
    返回 (mentions列表, _, 后端名称)
    """
    config = PLATFORM_SEARCH_CONFIG.get(platform, {"type": "websearch"})
    if config.get("query_override"):
        query = config["query_override"]

    if config["type"] == "skip":
        return [], [], "skipped"

    mentions = []
    backend = "none"

    # ── 第一优先级：opencli 原生适配器（返回结构化JSON：评分/评论/图片）──
    if config["type"] == "opencli":
        mentions, backend = _search_via_opencli(platform, query, max_results)
        if mentions:
            info(f"   ✅ {platform} [{backend}]: {len(mentions)} 条结构化数据")

            # 二级深度采集：携程 → 酒店详情页提取真实评价
            if platform == "携程":
                info(f"   🏨 进入携程酒店详情页采集真实评价...")
                mentions = _deep_dive_ctrip_detail(mentions, query)
                backend = f"opencli:ctrip+detail"

            # 二级深度采集：小红书 → note 详情获取完整正文
            if platform == "小红书":
                info(f"   🔍 进入小红书 note 详情采集...")
                mentions = _deep_dive_xhs_notes(mentions)
                backend = f"opencli:xhs+note"

            # 二级深度采集：微博 → post 详情获取完整正文
            if platform == "微博":
                info(f"   🔍 进入微博 post 详情采集...")
                mentions = _deep_dive_weibo_posts(mentions)
                backend = f"opencli:weibo+post"

            # 所有图片已在深度采集阶段提取到各 mention 的 image_urls 字段
            # store_mentions 会统一下载 image_urls → local_images
            return mentions, [], backend
        elif "cookie" in backend or "browser" in backend:
            debug(f"   {platform}: opencli 需浏览器扩展({backend})，尝试 browser 搜索")

    # ── 第二优先级：opencli browser 直接搜索（仅提取内容，不截图）──
    if not mentions:
        b_mentions, _, b_backend = _search_via_browser(platform, query, max_results)
        if b_mentions and len(b_mentions) >= 2:
            info(f"   📸 {platform} [browser]: {len(b_mentions)} 条提及")
            return b_mentions, [], b_backend

    # ── 第三优先级：WebSearch 兜底 ──
    if not mentions:
        site_filter = WEBSEARCH_SITE_FILTERS.get(platform, "")
        platform_query = f'"{query}" {platform} 民宿 评价 {site_filter}{WEBSEARCH_EXCLUDE_TERMS}'
        raw_text = _search_via_websearch(platform_query, max_results)
        mentions = _parse_websearch_results(raw_text, platform)
        return mentions, [], "WebSearch"

    return mentions, [], backend


# ══════════════════════════════════════════════════════════
#  结果解析
# ══════════════════════════════════════════════════════════

def _extract_image_urls(item: dict) -> list:
    """从 opencli 或其他数据源的 item 中提取图片 URL 列表"""
    images = None

    # 多种可能的图片字段名
    for field in ["images", "image_list", "image_urls", "pics", "media", "photos",
                   "cover_images", "covers"]:
        val = item.get(field)
        if val:
            if isinstance(val, list):
                images = [str(v) for v in val if isinstance(v, str) and v.startswith("http")]
            elif isinstance(val, str) and val.startswith("http"):
                images = [val]
            break

    # 单张图片字段
    if not images:
        for field in ["image", "image_url", "cover", "cover_url", "thumbnail",
                       "thumb", "pic", "photo"]:
            val = item.get(field)
            if isinstance(val, str) and val.startswith("http"):
                images = [val]
                break

    return images or []


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

        # 提取图片URL列表
        image_urls = _extract_image_urls(item)

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
            "image_urls": image_urls,
        })

    return mentions


def _is_relevant_result(url: str, title: str, content: str = "") -> bool:
    """检查搜索结果是否与民宿/旅游相关"""
    from urllib.parse import urlparse

    if not url or not title:
        return False

    # 1. 域名黑名单
    try:
        hostname = urlparse(url).hostname or ""
    except Exception:
        hostname = ""
    for blocked in IRRELEVANT_DOMAINS:
        if blocked in hostname:
            return False

    # 2. 标题关键词过滤
    import re as _re
    for pattern in IRRELEVANT_TITLE_PATTERNS:
        if _re.search(pattern, title, _re.IGNORECASE):
            return False

    # 3. 如果 URL 域名不含旅游平台，检查标题是否含旅游关键词
    domain_has_travel = any(td in hostname for td in TRAVEL_RELEVANT_DOMAINS)
    if not domain_has_travel:
        combined = f"{title} {content}"
        has_travel_kw = any(kw in combined for kw in TRAVEL_KEYWORDS)
        if not has_travel_kw:
            return False

    # 4. 过滤纯百科/公司官网类内容
    if not domain_has_travel:
        wiki_indicators = ["百度百科", "维基百科", "wikipedia", "公司简介", "官网首页",
                          "关于我们", "公司介绍", "企业简介", "产品介绍"]
        if any(ind in title for ind in wiki_indicators):
            # 除非同时也提到了民宿/酒店
            if not any(kw in title for kw in ["民宿", "酒店", "旅馆", "庐山"]):
                return False

    return True


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

        # 相关性过滤
        if not _is_relevant_result(url, title):
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
            "image_urls": [],
        })

    return mentions




def _parse_browser_results(content: str, platform: str) -> list:
    """解析 opencli browser extract 返回的 Markdown 内容为结构化数据（用于飞猪等无适配器平台）"""
    mentions = []
    if not content:
        return mentions

    # 飞猪酒店搜索结果格式解析
    # 每个酒店结果由 [酒店酒店 ... ](url) ... ### 酒店名 ... 评分 ... ¥价格 组成
    # 用酒店详情链接作为分隔
    hotel_blocks = re.split(r'\[酒店酒店', content)

    for block in hotel_blocks[1:]:  # 跳过第一个空块
        # 提取酒店详情链接和图片
        detail_match = re.search(r'\]\((https://hotel\.(?:alitrip|fliggy)\.com/hotel_detail2\.htm\?shid=\d+)\)', block)
        if not detail_match:
            continue

        url = detail_match.group(1)

        # 提取酒店名 (### 后的文字)
        name_match = re.search(r'###\s*\n?(.+?)\n', block)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # 提取评分 (如 "4.8分 很好", "5.0分 超棒", "3.2分")
        rating = None
        rating_match = re.search(r'(\d+\.?\d*)\s*分(?:\s*(?:很好|超棒|一般|较差))?', block)
        if rating_match:
            try:
                val = float(rating_match.group(1))
                if 1.0 <= val <= 5.0:
                    rating = val
            except ValueError:
                pass

        # 提取价格
        price = None
        price_match = re.search(r'_¥_(\d+)_起_', block)
        if price_match:
            price = f"¥{price_match.group(1)}起"

        # 提取类型/星级
        category = ""
        cat_match = re.search(r'####\s*(.+?)\n', block)
        if cat_match:
            category = cat_match.group(1).strip()[:60]

        # 情感分析
        sentiment = _analyze_sentiment(f"{name} {category}")

        # 提取图片URL（从 browser extract 的 Markdown 中查找图片链接）
        browser_images = re.findall(r'!\[.*?\]\((https?://[^\s\)]+\.(?:jpg|jpeg|png|webp|gif)[^\s\)]*)\)', block, re.IGNORECASE)
        # 也匹配没有alt的图片语法
        if not browser_images:
            browser_images = re.findall(r'\((https?://[^\s\)]+\.(?:jpg|jpeg|png|webp|gif)[^\s\)]*)\)', block, re.IGNORECASE)
        # 也匹配 <img src="..."> 格式
        if not browser_images:
            browser_images = re.findall(r'<img[^>]+src=["\'](https?://[^\s"\']+\.(?:jpg|jpeg|png|webp|gif)[^\s"\']*)', block, re.IGNORECASE)

        mentions.append({
            "type": "review" if rating else "mention",
            "title": name[:200],
            "content": f"{category} | {price or '暂无报价'}"[:500],
            "rating": rating,
            "author": "",
            "url": url,
            "sentiment": sentiment,
            "review_count": 0,
            "image_urls": browser_images[:5],
        })

    return mentions


def _parse_browser_extract(content: str, platform: str, query: str) -> list:
    """解析 opencli browser extract 返回的通用文本内容"""
    mentions = []
    if not content or len(content) < 30:
        return mentions

    # 清理常见噪音
    content = re.sub(r'http[s]?://\S+', ' ', content)
    content = re.sub(r'\s+', ' ', content).strip()

    # 按行/段落分割，寻找含有关键词的行
    query_keywords = [kw for kw in query.replace('·', ' ').split() if len(kw) >= 2]

    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if len(line) < 8 or len(line) > 500:
            continue

        # 检查是否包含搜索关键词
        has_kw = any(kw in line for kw in query_keywords) if query_keywords else True
        if not has_kw:
            continue

        # 提取评分
        rating = _extract_rating(line)

        # 提取情感
        sentiment = _analyze_sentiment(line)

        mentions.append({
            "type": "review" if rating else "mention",
            "title": line[:200],
            "content": line[:500],
            "rating": rating,
            "author": "",
            "url": _get_search_url(platform, query),
            "sentiment": sentiment,
            "review_count": 0,
            "image_urls": [],
        })

    return mentions[:10]  # 最多10条


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
    """情感分析 — 基于正负面关键词加权"""
    positive_words = [
        "很棒", "好评", "推荐", "满意", "惊喜", "不错", "舒服", "干净",
        "好", "优秀", "超赞", "完美", "温馨", "贴心", "热情", "周到",
        "美丽", "漂亮", "安静", "惬意", "享受", "值得", "喜欢", "赞",
        "强烈推荐", "下次还来", "物超所值", "环境好", "服务好", "风景好",
        "性价比高", "体验好", "舒适", "整洁", "卫生", "便利", "方便",
        "精致", "用心", "感动", "放松", "治愈", "好评如潮",
    ]
    negative_words = [
        "差评", "失望", "糟糕", "脏", "吵", "不值", "坑", "差",
        "不好", "垃圾", "恶心", "后悔", "骗", "不值这个价", "不推荐",
        "服务差", "态度差", "环境差", "卫生差", "设施旧", "破旧",
        "异味", "霉味", "虫子", "噪音", "太吵", "隔音差", "不干净",
        "拥挤", "不便", "失望至极", "不会再住", "体验差",
    ]
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
    策略: opencli browser (Chrome截图) → opencli 适配器 → WebSearch 兜底
    """
    if not query:
        query = MONITOR_SEARCH_QUERY

    results = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "bnb_name": BNB_NAME,
        "search_backend": "opencli browser + opencli + WebSearch",
        "platforms": {},
    }

    for platform in MONITOR_PLATFORMS:
        info(f"🔍 正在搜索 {platform}...")

        try:
            mentions, _, backend = _search_platform(platform, query, max_results=5)

            if mentions:
                stored_count = store_mentions(platform, mentions)
                # 统计已下载图片数
                total_imgs = sum(len(m.get("image_urls", [])) for m in mentions)
                info(f"    {platform} [{backend}]: {len(mentions)}条提及, {total_imgs}张图片URL, 新存{stored_count}条")
            else:
                info(f"    {platform} [{backend}]: 无有效结果")

            ratings = [m["rating"] for m in mentions if m["rating"]]
            total_imgs = sum(len(m.get("image_urls", [])) for m in mentions)
            results["platforms"][platform] = {
                "query": f'"{query}" {platform} 民宿 评价',
                "mentions_count": len(mentions),
                "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "top_mentions": mentions[:3],
                "search_url": _get_search_url(platform, query),
                "backend": backend,
                "image_count": total_imgs,
            }

            time.sleep(1.5)  # 平台间间隔

        except Exception as e:
            warning(f"    {platform}: 搜索失败 - {e}")
            results["platforms"][platform] = {
                "query": f'"{query}" {platform} 民宿 评价',
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
    """生成各平台搜索链接（正确 URL 编码中文）"""
    from urllib.parse import quote
    encoded = quote(query)
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


def download_mention_images(image_urls: list, platform: str) -> list:
    """
    下载提及中的图片到 local_data/images/monitor/{platform}/
    返回本地相对路径列表（相对于项目根目录）
    """
    if not image_urls:
        return []

    # 确保目录存在
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    monitor_img_dir = os.path.join(project_root, "local_data", "images", "monitor", platform)
    os.makedirs(monitor_img_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
    }

    local_paths = []
    for i, img_url in enumerate(image_urls[:5]):  # 最多下载5张
        try:
            # 微博图片需要 weibo Referer
            req_headers = headers.copy()
            if "sinaimg.cn" in img_url:
                req_headers["Referer"] = "https://weibo.com/"
            # 生成文件名
            import hashlib
            url_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
            ext = os.path.splitext(img_url.split("?")[0])[1]
            if not ext or len(ext) > 5:
                ext = ".jpg"
            filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{url_hash}{ext}"
            filepath = os.path.join(monitor_img_dir, filename)

            # 下载
            resp = requests.get(img_url, headers=req_headers, timeout=15)
            resp.raise_for_status()

            # 检查是否为图片（避免下载 HTML 页面）
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type and not img_url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                continue

            with open(filepath, "wb") as f:
                f.write(resp.content)

            # 返回相对于项目根目录的路径
            rel_path = os.path.join("local_data", "images", "monitor", platform, filename)
            local_paths.append(rel_path)
            debug(f"   📷 图片已下载: {rel_path}")

            # 避免请求过快
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            debug(f"   ⚠️ 图片下载超时: {img_url[:60]}")
        except requests.exceptions.ConnectionError:
            debug(f"   ⚠️ 图片下载连接失败: {img_url[:60]}")
        except Exception as e:
            debug(f"   ⚠️ 图片下载失败: {img_url[:60]} - {e}")

    return local_paths


def store_mentions(platform: str, mentions: list):
    """将收集到的提及存储到数据库（URL去重），并下载关联的图片"""
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
                    # 存量记录无图片但新数据有 → 更新补充
                    pre_downloaded = m.get("local_images")
                    new_image_urls = m.get("image_urls", [])
                    has_new_images = pre_downloaded or new_image_urls
                    if has_new_images and not existing.local_images:
                        if pre_downloaded:
                            existing.local_images = pre_downloaded
                            existing.image_urls = new_image_urls
                        else:
                            downloaded = download_mention_images(new_image_urls, platform)
                            if downloaded:
                                existing.local_images = downloaded
                        existing.content = m.get("content", "") or existing.content
                        existing.rating = m.get("rating") or existing.rating
                        existing.sentiment = m.get("sentiment", "neutral")
                        db.commit()
                        debug(f"   🖼️ 更新存量图片: {existing.title[:30]}... → {len(existing.local_images or [])}张")
                    continue

            # 下载/获取图片
            # 优先使用已预下载的 local_images（如 opencli xhs download 直接下载到本地）
            pre_downloaded = m.get("local_images")
            if pre_downloaded:
                local_images = pre_downloaded
                image_urls = m.get("image_urls", [])
            else:
                image_urls = m.get("image_urls", [])
                local_images = download_mention_images(image_urls, platform) if image_urls else []

            mention = PlatformMention(
                platform=platform,
                mention_type=m.get("type", "review"),
                title=m.get("title", ""),
                content=m.get("content", ""),
                rating=m.get("rating"),
                author=m.get("author", ""),
                url=url,
                sentiment=m.get("sentiment", "neutral"),
                image_urls=image_urls,
                local_images=local_images,
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


def _rating_bar(score: float, max_len: int = 10) -> str:
    """生成评分条形图（★☆）"""
    if score is None:
        return "暂无评分"
    full = round(score)
    empty = max_len - full
    return "★" * full + "☆" * empty


def _sentiment_bar(positive: int, neutral: int, negative: int, width: int = 10) -> str:
    """生成情感分布条形图"""
    total = positive + neutral + negative
    if total == 0:
        return "无数据"
    pos_w = round(positive / total * width)
    neg_w = round(negative / total * width)
    neu_w = width - pos_w - neg_w
    if neu_w < 0:
        neu_w = 0
    return f"{'🟢'*pos_w}{'🟡'*neu_w}{'🔴'*neg_w}"


def generate_monitor_report(bnb_id: str = "guishu") -> str:
    """生成平台监控报告（给主Agent / 微信客服使用）"""
    # 按民宿获取对应配置
    if bnb_id and bnb_id != "guishu":
        from bnb_context import get_bnb_config
        cfg = get_bnb_config(bnb_id)
        bnb_name = cfg.get("name", BNB_NAME)
    else:
        bnb_name = BNB_NAME

    summary = get_mentions_summary()

    if summary["overall_rating"] is None:
        return (
            "📊 *口碑简报*\n\n"
            "目前暂无主流平台的评价数据汇总。\n\n"
            f"{bnb_name}位于庐山风景名胜区大林沟路27号，"
            "欢迎在携程/美团/飞猪/大众点评搜索查看最新评价～\n\n"
            "💡 回复「收集口碑」触发平台信息实时收集"
        )

    # 按评分降序排列平台
    sorted_platforms = sorted(
        summary["platforms"].items(),
        key=lambda x: x[1].get("avg_rating") or 0,
        reverse=True,
    )

    overall = summary["overall_rating"]
    bar = _rating_bar(overall)

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"📊  *{bnb_name} · 口碑简报*",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"⭐ 综合评分：{overall}/5.0  {bar}",
        "",
    ]

    for platform, data in sorted_platforms:
        if data["total"] > 0:
            rating_str = f"{data['avg_rating']}/5.0" if data['avg_rating'] else "—"
            rating_bar = _rating_bar(data['avg_rating'], 5) if data['avg_rating'] else ""
            sentiment_bar = _sentiment_bar(data['positive'], data['neutral'], data['negative'])
            lines.append(
                f"▸ *{platform}*  {rating_str} {rating_bar}\n"
                f"   {data['total']}条评价  {sentiment_bar}"
            )

            # 最新评价摘要
            latest = data.get("latest", {})
            if latest and latest.get("title"):
                snippet = (latest.get("content") or latest.get("title", ""))[:60]
                sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(
                    latest.get("sentiment", ""), ""
                )
                lines.append(f"   {sentiment_emoji}「{snippet}...」")
            lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 回复「平台评价」查看各平台评价链接及最新评价")
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
