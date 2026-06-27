# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 启动命令

```bash
# 启动开发服务器（从项目根目录执行）
PYTHONUTF8=1 ~/python-embed/python.exe run.py

# 单行快速启动（跳过启动横幅）
PYTHONUTF8=1 ~/python-embed/python.exe -c "from app import app,init_app;init_app();app.run(host='0.0.0.0',port=5000,debug=True)"

# 安装依赖
~/python-embed/python.exe -m pip install <package>

# 停止所有 Python 进程
taskkill //F //IM python.exe
```

Python 是嵌入式发行版，位于 `~/python-embed/`（`~` = 当前用户主目录，跨设备通用）。**必须**设置 `PYTHONUTF8=1` 环境变量。如果 `.exe` 后缀不省略则用 `~/python-embed/python.exe`。

## 工作流规范

**每次修改完成后，必须立即提交并推送到远程仓库。** 不要等用户提醒。

```bash
# 修改完成后的标准收尾流程
git add <修改的文件>
git commit -m "<简要描述>"
git push origin main
```

## 架构概览

```
微信公众号用户消息
       │
       ▼
  POST /wechat  ─── wechat.py ─── 关键词路由表 ─── services/*.py ─── SQLite (models.py)
       │                    │
       ▼                    ▼
  微信XML回复          Jinja2 模板渲染 (templates/*.html)
                      + 独立预览页面 (preview/*.html)
```

### 三层架构

| 层 | 文件 | 职责 |
|----|------|------|
| **路由/控制器** | `app.py` (83条有效路由，14个 `@_bnb_route` 装饰器自动注册 BnB 双路径) | Flask 路由定义、请求分发、H5页面渲染 |
| **微信消息处理** | `wechat.py` (~500行) | 关键词正则匹配 → 服务调用 → 文本回复拼装 |
| **业务服务** | `services/*.py` (10个模块) | 数据库查询、格式化输出、AI对话、订单管理、监控、周报 |

### 服务层 (services/) — 14 个模块

- `rooms.py` — 房型查询、文本/图文格式化
- `booking.py` — 预订确认、AI解锁判断、好评推送、退房倒计时
- `menu.py` — 菜单分类查询、下单、微信支付参数生成
- `travel.py` — 路线/美食/位置查询与格式化
- `quick.py` — 14项快捷服务、服务请求创建
- `ai.py` — Anthropic Claude AI 对话（预订后才解锁）
- `notify.py` — 员工通知、看板数据统计
- `monitor.py` — opencli 精准搜索 + WebSearch 通用兜底，评分解析
- `report.py` — python-docx 周报生成（封面+数据表+评价+趋势）
- `orders.py` — 订单状态管理、看板数据
- `points.py` — 积分获取/兑换、会员等级
- `tea.py` — 山纪专属·茶园体验
- `healing.py` — 东林外专属·疗愈课程
- `logger.py` — 统一日志记录

### 双输出模式

项目有两套并行的页面渲染体系，**修改功能时需要同步更新**：

1. **Flask Jinja2 模板** (`templates/`) — 服务端渲染，通过 `/rooms` 等路由访问，继承 `base.html`
2. **纯 HTML 预览页** (`preview/`) — 独立文件，CSS/JS 内联，数据硬编码在 `<script>` 中，可直接双击打开

预览页是模板的**自包含副本**，不共享 CSS/JS。对页面结构或样式的修改需要分别处理。

### 小程序模拟器与实体页面的同步

`templates/miniapp-simulator.html` 是外壳，内部通过 iframe 加载真实的 Flask 模板页面（带 `?mp=1` 参数触发 mp-mode）。**模拟器的任何 UI/交互改动都可能需要同步修改被加载的实体页面**，必须按以下链路逐一检查：

```
miniapp-simulator.html  (外壳：Tab栏、抽屉、切换弹窗、postMessage监听)
        │
        ├── iframe → templates/index.html     (首页内容 + postMessage发送)
        ├── iframe → templates/rooms.html     (房型列表 + mp-mode卡片)
        ├── iframe → templates/room_detail.html (房型详情弹窗)
        ├── iframe → templates/menu.html
        ├── iframe → templates/travel.html
        ├── iframe → templates/services.html
        ├── iframe → templates/tea.html       (山纪专属)
        ├── iframe → templates/healing.html   (东林外专属)
        └── iframe → templates/miniapp-chat.html (AI管家)
```

**修改规范：**

| 改动类型 | 需检查的文件 |
|----------|-------------|
| Tab 栏配置（名称/数量/图标） | `simulator` 的 `BNB_TABS` + `index.html` 的 `tabMap` postMessage 映射 |
| 侧拉抽屉（我的）内容 | `simulator` 的抽屉 HTML + `base.html` 中 mp-mode 下隐藏的元素 |
| mp-mode 样式（间距/字号/颜色） | `static/css/style-mp.css` — 所有实体模板共用此文件 |
| 页面内导航/链接 | 所有模板中的 `<a href>` 必须使用 `{{ bnb_prefix }}` + `{{ mp }}` 保持模式 |
| BnB 切换逻辑 | `simulator` 的 `switchBnb()` + `base.html` 的 BnB 下拉 + 所有模板的条件渲染 |
| 新增功能入口（茶园/疗愈/积分） | `simulator` Tab 配置 + `index.html` 快捷卡片 + `base.html` 导航 + 对应功能模板 |

**验证方法：** 修改模拟器后，必须用三种 BnB（归墅/山纪/东林外）分别打开模拟器，完整走一遍所有 Tab，确认 iframe 内容与外壳无断裂。

### 数据库

SQLite (`yunshang_bnb.db`)，通过 SQLAlchemy ORM 访问。表：`rooms`、`bookings`、`menu_items`、`menu_categories`、`travel_routes`、`food_recommends`、`service_requests`、`platform_mentions`。

种子数据在 `seed_data.py`，应用启动时自动调用 `seed_all()` 填充。

## 关键设计约定

### 数据来源优先级

```
local_data/  >  opencli  >  WebSearch  >  其他来源
```

`local_data/images/` 和 `local_data/documents/` 中的官方文件权威最高。信息冲突时按此链采信。

**在搜索小红书、携程、大众点评等中文平台时，优先使用 `opencli` 工具**（已安装全局 CLI v1.8.4）。opencli 提供原生站点适配器：

| 平台 | 适配器 | 常用命令 | 浏览器 |
|------|--------|----------|:--:|
| 携程 | `ctrip` | `search`, `hotel-search`, `hotel-suggest` | `search` 不需要 |
| 小红书 | `xiaohongshu` | `search`, `note`, `download`, `feed` | 需要 |
| 大众点评 | `dianping` | `search`, `shop` | 需要 |
| 微博 | `weibo` | `search` | 需要 |
| 知乎 | `zhihu` | `search` | 需要 |

### 浏览器依赖平台的使用前提

小红书、大众点评、微博、知乎等需要登录态的写操作，**必须先完成以下前置步骤**（一次性配置）：

```bash
# 1. 安装 Chrome 扩展（仅需一次）
opencli browser init

# 2. 使用前确保 Chrome 已打开且对应网站已登录
#    - 大众点评：需在 Chrome 中登录 diangping.com
#    - 小红书：需在 Chrome 中登录 xiaohongshu.com
#    - 微博/知乎同理
```

**这些命令无需额外指定 session 或 cookie，opencli 会自动连接已登录的 Chrome 浏览器获取凭证。**

### 命令使用示例

```bash
# ── 无需浏览器的命令（直接可用）──
# 携程搜索（公开，无需浏览器）
opencli ctrip search "庐山 云上归墅" -f json --limit 5

# ── 需要浏览器的命令（需先 opencli browser init + Chrome 已登录）──
# 携程酒店搜索
opencli ctrip hotel-search "庐山" --checkin 2026-06-25 -f json

# 小红书搜索
opencli xiaohongshu search "庐山美食" -f json --limit 5

# 小红书笔记下载（含图片）
opencli xiaohongshu note <note_id> --download

# 大众点评搜索
opencli dianping search "庐山民宿" -f json --limit 5

# 大众点评店铺详情
opencli dianping shop <shop_id> -f json
```

### 图片获取策略

| 来源 | 方法 | 说明 |
|------|------|------|
| 携程点评图片 | 解析 `dimg*.c-ctrip.com/images/` URL | 公开 CDN，无需登录 |
| 小红书笔记图片 | `opencli xiaohongshu note <id> --download` | 需浏览器 |
| 大众点评图片 | `opencli browser extract` 从店铺页提取 | 需浏览器 + 登录 |
| 通用搜索图片 | WebSearch 找到图片 URL → `requests` 下载 | 兜底方案 |

**注意事项：**
- 携程 CDN 图片 URL 的尺寸参数：`_W_640_0.png`（640宽）、`_W_1920_1080.png`（全尺寸），下载时建议 750-1080px 宽度
- opencli download 的图片默认保存在当前工作目录，需移动到 `static/img/` 下对应目录
- 图片格式推荐 WebP（体积小）或 JPG（兼容性好），单张不超过 500KB

### 顾客导向原则

面向客人的页面 (`preview/` 和 `templates/` 中除 `staff.html` 外的所有模板) **只展示对客人有益的功能**。员工看板、好评推送机制等内部运营功能不应出现在顾客页面。

### BnB 色彩架构（CSS 变量一站切换范式）

**核心原则：组件样式零硬编码。** 任何 CSS 规则中禁止出现 BnB 专属 hex 值（`#4a7c59`、`#8B6914`、`#7B8DAD` 及其衍生色）。所有 BnB 差异化颜色一律使用 CSS 变量引用（`var(--color-primary)` 等）。hex 值**只允许出现在变量定义块**（`:root`、`[data-bnb]`、`[data-bnb][data-theme]`）中。

**效果：** 新增一个 BnB 只需在各上下文各加 1 个 `[data-bnb]` 变量块，所有组件自动适配，零遗漏。

#### 三套基底色

| BnB | ID | Primary | 中文 | 基调 |
|-----|-----|---------|------|------|
| 归墅 | `guishu` | `#4a7c59` | 竹青 | 山居、清新、自然 |
| 山纪 | `shanji` | `#8B6914` | 茶褐 | 茶馆、沉稳、温暖 |
| 东林外 | `donglinwai` | `#7B8DAD` | 禅灰蓝 | 禅寺、清净、治愈 |

归墅使用 `:root` 默认值，山纪/东林外通过 `[data-bnb]` 选择器覆盖。

#### 色彩上下文地图（新增 BnB 检查清单）

| # | 上下文 | 文件 | 定义方式 | 变量数 |
|---|--------|------|----------|--------|
| 1 | Web 全局样式 | `static/css/style.css` | `[data-bnb="xxx"]` (light+dark 各 1 块) | 20 |
| 2 | 小程序 WebView | `static/css/style-mp.css` | `[data-bnb="xxx"] body.mp-mode` (light+dark) | 10 |
| 3 | AI 管家页 | `templates/miniapp-chat.html` | `<html data-bnb>` + `[data-bnb="xxx"]` CSS | 7 |
| 4 | 模拟器外壳 | `templates/miniapp-simulator.html` | `BNB_COLORS` + `BNB_GRADIENTS` JS 常量 | 2 组 |
| 5 | Python 配置 | `config.py` | `BNB_CONFIGS["xxx"]["theme_color"]` | 1 |
| 6 | 微信原生小程序 | `miniapp/utils/constants.js` | `BNB_CONFIG` 对象 | 1 |

**新增 BnB 操作步骤：** 按上表顺序，在 6 个位置各添加 1 个定义块，颜色值使用新 BnB 的主色及其衍生色（浅/深/背景/文字/边框）。

#### CSS 变量参考（style.css `:root`）

| 变量 | 用途 | 典型组件 |
|------|------|----------|
| `--color-primary` | 主色 | 按钮、链接、激活态、标题 |
| `--color-primary-light` | 浅主色 | hover 态、浅色背景 |
| `--color-primary-dark` | 深主色 | 渐变终点、深色强调 |
| `--color-accent` | 强调色（暖木/茶金/禅木） | 价格、标签、次要按钮 |
| `--color-accent-light` | 浅强调色 | 浅色标签背景 |
| `--color-bg` | 页面背景 | `body` 背景 |
| `--color-bg-light` | 浅背景 | 卡片、面板 |
| `--color-bg-dark` | 深背景 | 暗色区域、表头 |
| `--color-text` | 主文字 | 正文 |
| `--color-text-light` | 次文字 | 描述、meta 信息 |
| `--color-text-lighter` | 弱文字 | 占位符、禁用态 |
| `--color-white` | 表面白 | 卡片背景（各 BnB 微调色温） |
| `--color-border` | 边框 | 分割线、输入框边框 |
| `--color-shadow` | 阴影 | 卡片阴影 |
| `--color-sky` | 天色 | Hero 渐变起点 |
| `--color-mist` | 雾色 | Hero 渐变中间色 |
| `--color-success` / `--color-warning` / `--color-danger` | 语义色 | 各 BnB 可微调 |

#### 主题系统（深色模式）

使用 `data-theme="dark"` 属性（挂载在 `<html>` 上）+ CSS 自定义属性覆盖实现深浅切换。暗色模式变量定义在 `[data-theme="dark"]` 和 `[data-bnb="xxx"][data-theme="dark"]` 选择器下。

CSS 选择器优先级链：`:root` → `[data-bnb]` → `[data-theme]` → `[data-bnb][data-theme]` → `[data-season]` → `[data-season][data-theme]`

#### 组件开发规范

1. **只用变量，不写 hex**：组件 CSS 中所有颜色通过 `var(--color-xxx)` 引用，禁止硬编码
2. **rgba 改用 color-mix**：`rgba(123,141,173,0.12)` → `color-mix(in srgb, var(--color-primary) 12%, transparent)`
3. **渐变可在 `[data-bnb]` 块中覆盖**：Hero、Page-header、Footer 等大面积渐变需要在 BnB 块中单独定义（无法用单一变量表达多色渐变终点）
4. **模板中 Jinja2 动态色用 `{{ bnb.theme_color }}`**：仅在需要设置 `--bnb-color` 或 `--card-color` 等动态 CSS 变量时使用
5. **新增组件时自问**："如果 BnB 从归墅切换到山纪，这个颜色应该跟着变吗？" → 是：用变量；否：用中性色

## 微信消息流

```
用户发消息 → POST /wechat → wechatpy.parse_message()
  → handle_wechat_message(msg)
    → build_keyword_routes() 正则匹配
    → 匹配成功 → 调用对应 service 方法 → 拼接回复文本
    → 未匹配 → 检查AI是否解锁 → AI chat() 或 引导提示
  → TextReply(content=reply_text).render()
  → 返回 XML
```

关键词路由在 `wechat.py:build_keyword_routes()` 定义，支持正则捕获组（如 `房间(\d+)` → 房间详情）。

## 外部依赖

- **opencli** — 原生站点适配器（携程/大众点评/小红书/微博/知乎），用于平台口碑精准搜索
- **WebSearch (Bing)** — 免费无限额通用搜索，用于 opencli 未覆盖的平台
- **DeepSeek API** — AI 对话后端（通过 Anthropic 兼容接口 `https://api.deepseek.com/anthropic`）
- **Cron 周报** — 每周一 9:57 自动生成 DOCX → `reports/`（通过 Claude Code 的 CronCreate 调度）
- **matplotlib** — 趋势分析图表生成（评分趋势/提及趋势/情感分布），`pip install matplotlib`
- **MinerU** — 文档提取工具，用于从携程页面等提取结构化信息

## 监控覆盖率

| 平台 | 搜索 | Deep Dive | 图片采集 |
|------|------|-----------|----------|
| 携程 | opencli ctrip search | ✅ `_deep_dive_ctrip_detail` | 点评页 dimg*.c-ctrip.com |
| 小红书 | opencli xiaohongshu search | ✅ `_deep_dive_xhs_notes` | opencli download → 本地 |
| 微博 | opencli weibo search | ✅ `_deep_dive_weibo_posts` | browser extract sinaimg.cn |
| 大众点评 | opencli dianping search | ✅ `_deep_dive_dianping_shop` (v3.6) | browser extract dpfile.com |
| 美团/飞猪/抖音/知乎 | WebSearch 兜底 | — | — |

## 配置

所有配置集中在 `config.py`，敏感信息通过 `.env` 文件注入（参考 `.env.example`）。微信 Token/AppID/Secret、AI API Key、支付商户号等均从环境变量读取。

## 验证方法

```bash
# 检查各页面是否正常渲染
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/rooms
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/menu
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/travel
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/services
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/staff

# 微信接入验证（需要先配置 Token）
# GET /wechat?signature=...&echostr=...&timestamp=...&nonce=...

# BnB 色彩验证 — 每个 BnB 分别检查
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/gs/
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/sj/
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/dlw/
```

## 多 BnB 编码规范（2026-06-27 复盘制定）

### 核心原则

**所有 BnB 差异化信息（名称/电话/地址/颜色）必须从 `BNB_CONFIGS[bnb_id]` 运行时获取，禁止模块级固化。**

### 禁止事项

| # | ❌ 禁止 | ✅ 正确 |
|---|--------|--------|
| 1 | 模块级 f-string 含 BNB_* 常量 | 普通字符串 + `{PLACEHOLDER}` + `.replace()` |
| 2 | `import X as Y` 后 lambda 引用 `X` | 不重命名，或 lambda 用重命名后的 `Y` |
| 3 | `except Exception: pass` | 至少 `debug(f"失败: {e}")` |
| 4 | 硬编码民宿名/电话/地址 | `BNB_CONFIGS[bnb_id]["xxx"]` 或 `cfg["xxx"]` |
| 5 | 新增模型列不更新迁移 | 模型 + `run_migrations()` + 所有 `Model(...)` 调用点同步改 |

### BnB 上下文系统

```python
# 入口处设置（app.py before_request / wechat.py handle_wechat_message 已自动调用）
from bnb_context import set_current_bnb
set_current_bnb(bnb_id)

# 任意位置获取（无需传参）
from bnb_context import get_current_bnb_id
bnb_id = get_current_bnb_id()
cfg = BNB_CONFIGS[bnb_id]

# 服务层兼容用法（优先参数 > Flask g > 线程本地 > 默认值）
from bnb_context import get_service_bnb_id
bnb_id = get_service_bnb_id(bnb_id)
```

### 向后兼容别名（DEPRECATED）

`config.py` 中 `BNB_NAME`、`BNB_PHONE`、`BNB_ADDRESS` 等始终为归墅值，仅允许在以下场景使用：
- 应用启动日志（app.py）
- 归墅专属周报（services/report.py）
- 作为 `BNB_CONFIGS.get()` 的 fallback 默认值

**新增代码禁止引用这些别名。**
