#!/usr/bin/env python
"""云上·归墅 — 面向客户的精美演示文稿（按截图文件名对应页面布局）"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

INK  = RGBColor(0x2A,0x3D,0x33); INK_LT = RGBColor(0x5B,0x7B,0x6F)
GOLD = RGBColor(0x8B,0x73,0x55); WHITE = RGBColor(0xFF,0xFF,0xFF)
DARK = RGBColor(0x1A,0x18,0x15); PAPER = RGBColor(0xF7,0xF4,0xED)
LT   = RGBColor(0x9E,0x9A,0x90); BD = RGBColor(0xD8,0xD3,0xC8)

def bg(s, c): s.background.fill.solid(); s.background.fill.fore_color.rgb = c

def tb(s, l, t, w, h, text, sz=14, c=DARK, bold=False, fn='PingFang SC', al=PP_ALIGN.LEFT):
    box = s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text
    p.font.size = Pt(sz); p.font.color.rgb = c; p.font.bold = bold
    p.font.name = fn; p.alignment = al
    return box

def card(s, l, t, w, h, fill=WHITE):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(l),Inches(t),Inches(w),Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = fill; c.line.color.rgb = BD; c.line.width = Pt(1)
    return c

def img(s, path, l, t, w, h=None):
    if not os.path.exists(path): return tb(s,l,t,w,1,f'[img:{os.path.basename(path)}]',10,LT)
    s.shapes.add_picture(path,Inches(l),Inches(t),Inches(w),Inches(h) if h else None)

def line(s, l, t):
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(l),Inches(t),Inches(1.5),Pt(3))
    ln.fill.solid(); ln.fill.fore_color.rgb = GOLD; ln.line.fill.background()

IMG = 'd:/cc/reports/ppt_screenshots'

# ═══════════════ S1 — 封面 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, INK)
tb(s, 1.5, 1.8, 10, 1.2, '云上·归墅', 60, WHITE, True, 'Noto Serif SC', PP_ALIGN.CENTER)
tb(s, 1.5, 3.0, 10, 0.7, '微信公众号智能服务系统', 24, RGBColor(0xCC,0xC8,0xBE), al=PP_ALIGN.CENTER)
tb(s, 3, 3.8, 7, 0.5, '云无心以出岫，鸟倦飞而知还', 16, GOLD, fn='KaiTi', al=PP_ALIGN.CENTER)
tb(s, 1.5, 5.2, 10, 0.4, '庐山山上 · 大林沟路27号  |  携程4.7分  |  2016年开业', 12, LT, al=PP_ALIGN.CENTER)

# ═══════════════ S2 — 民宿介绍 (左图右文) ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
img(s, f'{IMG}/第二面左半边.png', 0.3, 0.2, 5.2, 7.1)
tb(s, 6.0, 0.8, 6.8, 0.7, '一座藏在庐山云雾里的民宿', 30, INK, True, 'Noto Serif SC')
line(s, 6.0, 1.6)
tb(s, 6.0, 2.1, 6.5, 4.8,
   '🏔️  海拔千米的U型三层小楼\n      推窗即漫山云海\n\n'
   '☕  一楼「三山二水咖啡」自营精品咖啡馆\n      主理人麦姐亲自打理\n      自种庐山云雾茶，自酿美酒\n\n'
   '🛏️  11间客房 · 8种精品房型\n      ¥388起 · 山景/露台/云海/竹林\n\n'
   '🐾  宠物友好 · 免费携带猫狗入住\n\n'
   '🅿️  免费私家停车场\n\n'
   '🚡  索道上站步行5分钟\n\n'
   '⭐  携程 4.7分 · 85条真实评价', 14, DARK)

# ═══════════════ S3 — AI智能管家 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
tb(s, 1.0, 0.5, 11, 0.7, 'AI 智能管家 · 全程陪伴', 32, INK, True, 'Noto Serif SC'); line(s, 1, 1.3)
phases = [
    ('🗺️ 预订前', '免费旅行顾问', '所有人可用\n庐山攻略咨询\n房型推荐\n自然引导预订', INK),
    ('🛎️ 预订后', '专属AI管家', '已预订客人独享\n全功能智能服务\n房间/路线/点餐\n私人旅行规划', INK_LT),
    ('☁️ 离店后', '复购关怀', '温暖叙旧\n收集入住反馈\n老客专属优惠\n邀请再次归来', GOLD),
]
for i, (icon, title, desc, clr) in enumerate(phases):
    x = 1.5 + i*3.7
    card(s, x, 1.8, 3.2, 4.0, clr)
    tb(s, x+0.3, 2.0, 2.6, 0.4, icon, 20, WHITE, True)
    tb(s, x+0.3, 2.5, 2.6, 0.5, title, 20, WHITE, True)
    tb(s, x+0.3, 3.2, 2.6, 2.2, desc, 13, RGBColor(0xE0,0xDC,0xD4))
tb(s, 1.0, 6.3, 11, 0.5, '微信公众号内回复任意消息即可体验 · 预订后自动解锁完整AI管家功能', 12, LT, al=PP_ALIGN.CENTER)

# ═══════════════ S4 — 首页全貌 (两张图上下排列) ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
tb(s, 1.0, 0.3, 11, 0.6, '首页全貌 · 移动端', 28, INK, True, 'Noto Serif SC')
img(s, f'{IMG}/第四面右半边.png', 4.0, 1.1, 5.5, 3.0)
img(s, f'{IMG}/第四面右半边2.png', 4.0, 4.2, 5.5, 3.0)
tb(s, 0.5, 1.5, 3.2, 5.5,
   '✨ 水墨晕染视觉\n    多层径向渐变Hero\n    山形剪影底部\n\n'
   '📱 5大快捷入口\n    房型 · 点餐 · 攻略\n    服务 · 积分中心\n\n'
   '⭐ 住客好评轮播\n    12条真实好评\n    4条一组自动切换\n\n'
   '🤖 智能客服功能介绍\n\n'
   '❓ 常见问题FAQ', 12, DARK)

# ═══════════════ S5 — 房型展示 (两张图上下排列) ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
img(s, f'{IMG}/第五面右半边.png', 5.5, 0.3, 4.5, 3.4)
img(s, f'{IMG}/第五面右半边2.png', 5.5, 3.8, 4.5, 3.4)
tb(s, 0.5, 1.0, 4.5, 0.6, '房型展示', 30, INK, True, 'Noto Serif SC'); line(s, 0.5, 1.7)
tb(s, 0.5, 2.2, 4.5, 4.8,
   '🛏️  8种精品房型 · 11间客房\n\n'
   '📷  携程官方高清图片展示\n\n'
   '💰  实时价格对比（原价 vs 现价）\n\n'
   '🏷️  景观标签：山景 / 云海 / 竹林\n\n'
   '📐  面积 · 床型 · 可住人数\n\n'
   '🔥  实时库存余量徽章\n    仅剩1间红色预警\n\n'
   '✨  房间设施标签展示', 13, DARK)

# ═══════════════ S6 — 咖啡简餐 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
img(s, f'{IMG}/第六面右边.png', 5.5, 0.5, 4.5, 6.5)
tb(s, 0.5, 1.0, 4.5, 0.6, '「三山二水咖啡」点单', 30, INK, True, 'Noto Serif SC'); line(s, 0.5, 1.7)
tb(s, 0.5, 2.2, 4.5, 4.8,
   '☕  5大分类 · 24款产品\n\n'
   '    精品咖啡 · 茶饮\n    简餐轻食 · 甜点 · 饮品\n\n'
   '🛒  在线购物车\n    添加/删除/修改数量\n    实时计算总价\n\n'
   '💳  微信支付集成\n\n'
   '🏠  送餐到房服务\n    输入房间号即可\n\n'
   '⭐  推荐标签\n    热门单品标注', 13, DARK)

# ═══════════════ S7 — 游玩攻略 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
img(s, f'{IMG}/第七面右边.png', 5.5, 0.5, 4.5, 6.5)
tb(s, 0.5, 1.0, 4.5, 0.6, '游玩攻略', 30, INK, True, 'Noto Serif SC'); line(s, 0.5, 1.7)
tb(s, 0.5, 2.2, 4.5, 4.8,
   '🗺️  5条精选游玩路线\n\n'
   '    轻松 · 适中 · 挑战\n    每条含多景点+时间估算\n\n'
   '🍜  6家周边美食推荐\n    人均价格 · 必点菜品\n    地图导航一键跳转\n\n'
   '🚡  实时索道通知\n\n'
   '🚗  暑期自驾限行提醒', 13, DARK)

# ═══════════════ S8 — 快捷服务 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
img(s, f'{IMG}/第八面右边.png', 5.5, 0.5, 4.5, 6.5)
tb(s, 0.5, 1.0, 4.5, 0.6, '快捷服务', 30, INK, True, 'Noto Serif SC'); line(s, 0.5, 1.7)
tb(s, 0.5, 2.2, 4.5, 4.8,
   '🛎️  14项贴心服务\n\n'
   '🧹  客房服务\n    续住 · 打扫 · 送餐 · 洗衣\n\n'
   '🔧  设施维修\n    报修 · 空调 · 热水\n\n'
   '🏨  前台服务\n    叫醒 · 行李寄存 · 叫车\n    路线规划 · 旅游咨询\n    搭伙用餐 · 退房办理\n\n'
   '📞  一键拨打前台', 13, DARK)

# ═══════════════ S9 — 积分 + 订单 (左右并排) ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
tb(s, 1.0, 0.3, 11, 0.6, '会员积分 & 订单管理', 28, INK, True, 'Noto Serif SC'); line(s, 5.5, 1.0)
img(s, f'{IMG}/第九面.png', 0.5, 1.5, 5.8, 5.5)
img(s, f'{IMG}/第九面右半边.png', 7.0, 1.5, 5.8, 5.5)
tb(s, 0.5, 1.0, 5.8, 0.5, '⭐ 会员积分中心', 16, INK, True, al=PP_ALIGN.CENTER)
tb(s, 7.0, 1.0, 5.8, 0.5, '📊 多平台订单聚合', 16, INK, True, al=PP_ALIGN.CENTER)

# ═══════════════ S10 — 桌面端全貌 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, PAPER)
tb(s, 1.0, 0.3, 11, 0.6, '桌面端适配 · 1200px 宽屏体验', 28, INK, True, 'Noto Serif SC')
img(s, f'{IMG}/第十面.png', 0.5, 1.2, 12.3, 5.8)
tb(s, 1.0, 7.0, 11, 0.3, '4列介绍 · 3列房型 · 2列功能 · 响应式自动切换  |  移动端 & 桌面端独立优化', 10, LT, al=PP_ALIGN.CENTER)

# ═══════════════ S11 — 感谢 ═══════════════
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s, INK)
tb(s, 1.5, 2.3, 10, 1.0, '感谢观看', 56, WHITE, True, 'Noto Serif SC', PP_ALIGN.CENTER)
tb(s, 1.5, 3.5, 10, 0.5, '云上·归墅 · 微信公众号智能服务系统', 20, GOLD, al=PP_ALIGN.CENTER)
tb(s, 1.5, 4.3, 10, 0.4, '庐山山上 · 大林沟路27号  |  16607927666', 13, LT, al=PP_ALIGN.CENTER)
tb(s, 1.5, 4.8, 10, 0.4, '携程 / 美团 / 飞猪 / 大众点评  搜索「云上归墅」', 12, RGBColor(0x88,0x85,0x7E), al=PP_ALIGN.CENTER)

output = 'd:/cc/reports/云上归墅_项目演示_20260612.pptx'
prs.save(output)
print(f'PPT: {output}')
print(f'Slides: {len(prs.slides)}')

# 验证图片使用情况
for fn in ['第二面左半边.png','第四面右半边.png','第四面右半边2.png','第五面右半边.png','第五面右半边2.png','第六面右边.png','第七面右边.png','第八面右边.png','第九面.png','第九面右半边.png','第十面.png']:
    p = f'{IMG}/{fn}'
    print(f'  {"✅" if os.path.exists(p) else "❌"} {fn} ({os.path.getsize(p)//1024}KB)' if os.path.exists(p) else f'  ❌ {fn}')
