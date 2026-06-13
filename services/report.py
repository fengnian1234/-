"""
周报生成服务 - 生成 DOCX 格式的口碑监控周报
使用 python-docx 生成中式风格优雅排版
"""
import os
from datetime import datetime, timedelta
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from models import SessionLocal, PlatformMention
from services.monitor import (
    get_mentions_summary, search_platform_mentions,
    get_platform_review_links, MONITOR_PLATFORMS,
)
from config import BNB_NAME, BNB_ADDRESS, BNB_PHONE

# 输出目录
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def generate_weekly_report() -> dict:
    """
    主入口：收集最新数据并生成 DOCX 周报
    返回报告路径和摘要信息
    """
    os.makedirs(REPORT_DIR, exist_ok=True)

    # 1. 收集最新平台数据
    print("📡 正在收集6个平台最新数据...")
    search_results = search_platform_mentions()

    # 2. 获取汇总
    summary = get_mentions_summary()

    # 3. 生成 DOCX
    now = datetime.utcnow()
    week_start = (now - timedelta(days=7)).strftime("%Y.%m.%d")
    week_end = now.strftime("%Y.%m.%d")
    filename = f"云上归墅_口碑周报_{now.strftime('%Y%m%d_%H%M')}.docx"
    filepath = os.path.join(REPORT_DIR, filename)

    doc = _build_docx(summary, search_results, week_start, week_end)
    doc.save(filepath)

    print(f"✅ 周报已生成: {filepath}")

    return {
        "success": True,
        "filename": filename,
        "filepath": filepath,
        "overall_rating": summary.get("overall_rating"),
        "total_mentions": sum(
            p.get("total", 0) for p in summary.get("platforms", {}).values()
        ),
        "platforms_covered": len(MONITOR_PLATFORMS),
        "week_range": f"{week_start} - {week_end}",
    }


def _build_docx(summary: dict, search_results: dict,
                week_start: str, week_end: str) -> Document:
    """构建 DOCX 文档"""
    doc = Document()

    # ── 页面设置 ──
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ── 样式预设 ──
    style = doc.styles['Normal']
    style.font.name = 'Microsoft YaHei'
    style.font.size = Pt(10.5)
    style.paragraph_format.line_spacing = 1.5
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    # ══════════════════════════════════════════
    #  封面
    # ══════════════════════════════════════════
    for _ in range(6):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(f"{BNB_NAME}")
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x2a, 0x3d, 0x33)
    run.font.name = 'Microsoft YaHei'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    doc.add_paragraph()

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("口碑监控周报")
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x5b, 0x7b, 0x6f)
    run.font.name = 'Microsoft YaHei'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(f"报告周期：{week_start} — {week_end}\n{BNB_ADDRESS}\n{BNB_PHONE}")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x6b, 0x6b, 0x66)
    run.font.name = 'Microsoft YaHei'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    doc.add_page_break()

    # ══════════════════════════════════════════
    #  一、执行摘要
    # ══════════════════════════════════════════
    _add_heading(doc, "一、执行摘要", level=1)

    overall = summary.get("overall_rating")
    total_mentions = sum(p.get("total", 0) for p in summary.get("platforms", {}).values())

    overview_text = (
        f"本周（{week_start} — {week_end}）共监控 {len(MONITOR_PLATFORMS)} 个主流平台，"
        f"累计获取 {total_mentions} 条评价与提及。"
    )
    if overall:
        overview_text += f"各平台加权综合评分为 ⭐{overall}/5.0。"
    else:
        overview_text += "当前暂无足够评分数据进行综合计算。"

    p = doc.add_paragraph(overview_text)
    p.paragraph_format.first_line_indent = Cm(0.74)

    # 综合评分卡片
    if overall:
        doc.add_paragraph()
        card = doc.add_paragraph()
        card.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = card.add_run(f"⭐ 综合评分  {overall} / 5.0")
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x8b, 0x73, 0x55)
        run.font.name = 'Microsoft YaHei'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    # ══════════════════════════════════════════
    #  二、各平台数据明细
    # ══════════════════════════════════════════
    doc.add_paragraph()
    _add_heading(doc, "二、各平台数据明细", level=1)

    # 汇总表格
    table = doc.add_table(rows=1, cols=6)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # 表头
    headers = ["平台", "评价数", "均分", "好评👍", "中评😊", "差评👎"]
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(9)

    # 数据行
    for platform in MONITOR_PLATFORMS:
        data = summary.get("platforms", {}).get(platform, {})
        row = table.add_row()
        row.cells[0].text = platform
        row.cells[1].text = str(data.get("total", 0))
        row.cells[2].text = f"{data.get('avg_rating')}/5.0" if data.get("avg_rating") else "—"
        row.cells[3].text = str(data.get("positive", 0))
        row.cells[4].text = str(data.get("neutral", 0))
        row.cells[5].text = str(data.get("negative", 0))

    doc.add_paragraph()

    # 各平台详情
    for platform in MONITOR_PLATFORMS:
        data = summary.get("platforms", {}).get(platform, {})
        mentions_data = data.get("latest", {})

        _add_heading(doc, f"{platform}", level=2)

        if data.get("total", 0) == 0:
            doc.add_paragraph(f"  本周暂无 {platform} 平台的新数据。")
            continue

        # 关键指标
        indicators = doc.add_paragraph()
        indicators.paragraph_format.left_indent = Cm(0.5)
        run = indicators.add_run(
            f"总提及：{data.get('total', 0)} 条  |  "
            f"均分：{data.get('avg_rating', '—')}  |  "
            f"情感：👍{data.get('positive', 0)} 😊{data.get('neutral', 0)} 👎{data.get('negative', 0)}"
        )
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x6b, 0x6b, 0x66)

        # 最新评价摘要
        if mentions_data and isinstance(mentions_data, dict):
            title = mentions_data.get("title", "")
            content = mentions_data.get("content", "")
            rating = mentions_data.get("rating", "")
            url = mentions_data.get("url", "")

            if title or content:
                quote = doc.add_paragraph()
                quote.paragraph_format.left_indent = Cm(1.0)
                quote.paragraph_format.space_before = Pt(4)

                if rating:
                    run = quote.add_run(f"【{rating}分】")
                    run.font.bold = True
                    run.font.size = Pt(9)

                snippet = content[:200] if content else title[:200]
                run = quote.add_run(f' "{snippet}..."')
                run.font.size = Pt(9)
                run.font.italic = True

            if url:
                link = doc.add_paragraph()
                link.paragraph_format.left_indent = Cm(1.0)
                run = link.add_run(f"🔗 {url}")
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(0x3d, 0x53, 0x47)

    # ══════════════════════════════════════════
    #  三、评价截图区
    # ══════════════════════════════════════════
    doc.add_page_break()
    _add_heading(doc, "三、平台评价截图", level=1)

    doc.add_paragraph(
        "以下为各平台评价入口链接，可手动截图添加至本区域。"
        "建议每周截取评分页面和最新3条评价作为附件归档。"
    )

    platforms_links = get_platform_review_links()
    for key, info in platforms_links.items():
        p = doc.add_paragraph()
        run = p.add_run(f"{info['icon']} {info['name']}")
        run.font.bold = True
        run.font.size = Pt(10)

        p2 = doc.add_paragraph()
        p2.paragraph_format.left_indent = Cm(1.0)
        run = p2.add_run(info['review_url'])
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x3d, 0x53, 0x47)

        # 截图占位框
        placeholder = doc.add_paragraph()
        placeholder.alignment = WD_ALIGN_PARAGRAPH.CENTER
        placeholder.paragraph_format.space_before = Pt(6)
        placeholder.paragraph_format.space_after = Pt(6)
        run = placeholder.add_run(f"┌{'─'*40}┐\n│  [{info['name']} 评价截图]  │\n└{'─'*40}┘")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x90)

        doc.add_paragraph()

    # ══════════════════════════════════════════
    #  四、趋势分析建议
    # ══════════════════════════════════════════
    doc.add_paragraph()
    _add_heading(doc, "四、趋势分析与建议", level=1)

    # 情感分布统计
    total_pos = sum(p.get("positive", 0) for p in summary.get("platforms", {}).values())
    total_neu = sum(p.get("neutral", 0) for p in summary.get("platforms", {}).values())
    total_neg = sum(p.get("negative", 0) for p in summary.get("platforms", {}).values())
    total_all = total_pos + total_neu + total_neg

    if total_all > 0:
        pos_pct = round(total_pos / total_all * 100)
        neg_pct = round(total_neg / total_all * 100)

        analysis = doc.add_paragraph()
        analysis.paragraph_format.first_line_indent = Cm(0.74)
        analysis.add_run(
            f"本周正面评价占比 {pos_pct}%，负面评价占比 {neg_pct}%。"
        )

        if pos_pct >= 80:
            analysis.add_run("整体口碑表现优秀，建议保持现有服务质量，持续关注新评价动态。")
        elif pos_pct >= 60:
            analysis.add_run("口碑良好，建议关注差评原因并及时改进。")
        else:
            analysis.add_run("口碑有待改善，建议重点排查差评原因，制定改进计划。")
    else:
        doc.add_paragraph("本周暂无足够数据进行分析。建议增加平台信息收集频率。")

    doc.add_paragraph()

    # 建议列表
    suggestions = [
        "每日检查携程/美团最新评价，对差评48小时内回复",
        "鼓励满意客人离店时在平台写评价（退房好评推送已自动执行）",
        "小红书和抖音端增加民宿日常内容发布，提高曝光度",
        "关注竞品民宿评价动态，了解差异化服务方向",
    ]
    for s in suggestions:
        p = doc.add_paragraph(f"• {s}", style='List Bullet')
        for run in p.runs:
            run.font.size = Pt(9)

    # ══════════════════════════════════════════
    #  页脚
    # ══════════════════════════════════════════
    doc.add_paragraph()
    doc.add_paragraph()
    footer_text = doc.add_paragraph()
    footer_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_text.add_run(
        f"— {BNB_NAME} · 智能客服系统自动生成 —\n"
        f"报告时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x90)

    return doc


def _add_heading(doc: Document, text: str, level: int = 1):
    """添加带样式的标题"""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.name = 'Microsoft YaHei'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        if level == 1:
            run.font.color.rgb = RGBColor(0x2a, 0x3d, 0x33)
            run.font.size = Pt(16)
        elif level == 2:
            run.font.color.rgb = RGBColor(0x3d, 0x53, 0x47)
            run.font.size = Pt(13)
    return heading
