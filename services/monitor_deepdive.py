"""
平台深度采集子模块（v3.12: 从 monitor.py 拆出）
- 携程酒店点评二级页面 → 结构化评价+图片
- 小红书笔记详情 → 完整正文+图片下载
- 微博帖子详情 → 完整正文+图片提取
- 大众点评店铺详情 → 结构化评价+图片
"""
import json
import os
import re
import subprocess
import time
import hashlib

from services.logger import debug, info
from services.monitor import _SUBPROCESS_ENV, _analyze_sentiment


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

        # 使用携程酒店点评二级页面（用户说的"二级界面"）
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
                                debug(f"weibo browser scroll 失败", exc_info=True)

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


def _deep_dive_dianping_shop(mentions: list) -> list:
    """
    对大众点评搜索结果，打开店铺详情页提取结构化评价和图片。
    每条评价独立存储，包含文字和图片。
    """
    enriched = []
    for m in mentions[:3]:
        shop_url = m.get("url", "")
        if not shop_url or "dianping.com" not in shop_url:
            enriched.append(m)
            continue

        # 从 URL 提取店铺 ID 用作 session 名
        shop_id = ""
        id_match = re.search(r'/shop/(\w+)', shop_url)
        if id_match:
            shop_id = id_match.group(1)
        else:
            shop_id = hashlib.md5(shop_url.encode()).hexdigest()[:10]
        session = f"dp_shop_{shop_id}"

        try:
            # 1. 打开店铺页面
            subprocess.run(
                ["opencli.cmd", "browser", session, "open", shop_url],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30,
                env=_SUBPROCESS_ENV,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            time.sleep(4)

            # 2. 滚动加载评价（大众点评需要多次滚动触发懒加载）
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
                debug(f"   ⚠️ 大众点评店铺页提取内容不足")
                enriched.append(m)
                continue

            # 4. 提取评价图片（大众点评 CDN 图片）
            dp_images = _extract_dianping_images(content)

            # 5. 解析评价文字（匹配评分+正文）
            parsed_reviews = _parse_dianping_reviews(content)

            if parsed_reviews:
                info(f"   🍽️ 大众点评店铺: {len(parsed_reviews)}条评价 | {m.get('title', '')[:40]}")
                for rev in parsed_reviews:
                    # 每条评价分配部分图片（轮转分配）
                    rev_imgs = rev.get("images", [])
                    if not rev_imgs and dp_images:
                        # 按评价索引分配图片
                        idx = len(enriched) % max(len(dp_images), 1)
                        rev_imgs = dp_images[idx:idx + 3]
                    new_m = {
                        "type": "review",
                        "title": f"[{rev.get('date', '')}] {rev.get('author', '用户')}: {rev.get('text', '')[:80]}",
                        "content": rev.get("text", "")[:600],
                        "rating": rev.get("rating"),
                        "author": rev.get("author", ""),
                        "url": shop_url,
                        "sentiment": rev.get("sentiment", "neutral"),
                        "review_count": 1,
                        "image_urls": rev_imgs,
                    }
                    enriched.append(new_m)
            else:
                # 无结构化评价 → 保留搜索条目，附加图片
                m["content"] = content[:500]
                if dp_images:
                    m["image_urls"] = dp_images[:6]
                    info(f"   🖼️ 大众点评店铺提取 {len(dp_images)} 张图片")
                enriched.append(m)

        except subprocess.TimeoutExpired:
            debug(f"   ⏱️ 大众点评店铺超时: {shop_id}")
            enriched.append(m)
        except Exception as e:
            debug(f"   ⚠️ 大众点评店铺异常: {e}")
            enriched.append(m)

        time.sleep(1.5)

    return enriched


def _extract_dianping_images(content: str) -> list:
    """从大众点评页面内容提取图片 URL"""
    img_urls = []
    patterns = [
        r'https?://[^\s"\'<>]*\.dpfile\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
        r'https?://[^\s"\'<>]*\.dianping\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
        r'https?://[^\s"\'<>]*p\d+\.meituan\.net/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
        # 通用 img 标签
        r'<img[^>]+src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']',
    ]
    for pat in patterns:
        img_urls.extend(re.findall(pat, content, re.IGNORECASE))
    seen = set()
    unique = []
    for u in img_urls:
        if u not in seen and "avatar" not in u.lower() and "icon" not in u.lower():
            seen.add(u)
            unique.append(u)
    return unique[:12]


def _parse_dianping_reviews(content: str) -> list:
    """
    从大众点评店铺页面内容解析结构化评价。
    匹配模式：评分(星级) + 用户 + 日期 + 正文
    """
    reviews = []

    # 大众点评常见评价结构：
    # ★★★★★ 或 5.0分 / 5分
    # 用户名
    # 日期
    # 评价正文
    # 配图 URL

    # 策略1: 按评分标记分割
    star_blocks = re.split(
        r'(?:(?:★★★★★|★★★★☆|★★★☆☆|★★☆☆☆|★☆☆☆☆)|'
        r'(?:[45]\.\d|[12345])分?(?:\s*/\s*5)?)',
        content
    )
    # 同时匹配评分
    rating_matches = re.finditer(
        r'((?:★★★★★|★★★★☆|★★★☆☆|★★☆☆☆|★☆☆☆☆)|'
        r'([45]\.\d|[12345])分?(?:\s*/\s*5)?)',
        content
    )
    star_map = {
        '★★★★★': 5, '★★★★☆': 4, '★★★☆☆': 3,
        '★★☆☆☆': 2, '★☆☆☆☆': 1,
    }

    rating_list = []
    for m_rat in rating_matches:
        star_text = m_rat.group(1)
        if star_text in star_map:
            rating_list.append((m_rat.end(), star_map[star_text]))
        else:
            try:
                num = float(re.match(r'([\d.]+)', star_text).group(1))
                rating_list.append((m_rat.end(), min(5, num)))
            except (ValueError, AttributeError):
                rating_list.append((m_rat.end(), 4))  # 默认

    if len(rating_list) < 1:
        return reviews

    # 策略2: 按用户名行分割（大众点评中用户名常单独一行）
    user_blocks = re.split(r'(?:^|\n)([^\n]{2,12})\s*\n(?=[^\n]{20,})', content)
    # 更稳健的方式：找评分后的文字
    for i, (pos, rating) in enumerate(rating_list):
        # 取评分后的文字作为评价正文
        end_pos = rating_list[i + 1][0] if i + 1 < len(rating_list) else min(pos + 500, len(content))
        snippet = content[pos:end_pos].strip()[:500]

        if len(snippet) < 15:
            continue

        # 尝试提取用户名和日期
        author = "用户"
        date_str = ""
        author_match = re.search(r'(?:^|\n)\s*([^\n]{2,10})\s*$', snippet[:100], re.MULTILINE)
        if author_match:
            author = author_match.group(1).strip()

        date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2})', snippet[:200])
        if date_match:
            date_str = date_match.group(1)

        # 提取图片
        img_urls = []
        for pat in [
            r'https?://[^\s"\'<>]*\.dpfile\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
            r'<img[^>]+src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']',
        ]:
            img_urls.extend(re.findall(pat, snippet, re.IGNORECASE))

        # 情感判断
        sentiment = "neutral"
        if rating >= 4:
            sentiment = "positive"
        elif rating <= 2:
            sentiment = "negative"

        reviews.append({
            "author": author,
            "date": date_str,
            "rating": rating,
            "text": snippet[:400],
            "sentiment": sentiment,
            "images": list(set(img_urls))[:6],
        })

    return reviews
