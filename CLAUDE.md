# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 启动命令

```bash
# 启动开发服务器
PYTHONUTF8=1 C:/Users/admin/python-embed/python.exe d:/cc/run.py

# 单行快速启动（跳过启动横幅）
PYTHONUTF8=1 C:/Users/admin/python-embed/python.exe -c "from app import app,init_app;init_app();app.run(host='0.0.0.0',port=5000,debug=True)"

# 安装依赖
C:/Users/admin/python-embed/python.exe -m pip install <package>

# 停止所有 Python 进程
taskkill //F //IM python.exe
```

Python 是嵌入式发行版，路径固定为 `C:/Users/admin/python-embed/python.exe`，**必须**设置 `PYTHONUTF8=1` 环境变量。

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
| **路由/控制器** | `app.py` (28条路由) | Flask 路由定义、请求分发、H5页面渲染 |
| **微信消息处理** | `wechat.py` (~500行) | 关键词正则匹配 → 服务调用 → 文本回复拼装 |
| **业务服务** | `services/*.py` (10个模块) | 数据库查询、格式化输出、AI对话、订单管理、监控、周报 |

### 服务层 (services/)

- `rooms.py` — 房型查询、文本/图文格式化
- `booking.py` — 预订确认、AI解锁判断、好评推送、退房倒计时
- `menu.py` — 菜单分类查询、下单、微信支付参数生成
- `travel.py` — 路线/美食/位置查询与格式化
- `quick.py` — 14项快捷服务、服务请求创建
- `ai.py` — Anthropic Claude AI 对话（预订后才解锁）
- `notify.py` — 员工通知、看板数据统计
- `monitor.py` — opencli 精准搜索 + WebSearch 通用兜底，评分解析
- `report.py` — python-docx 周报生成（封面+数据表+评价+趋势）

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

**在搜索小红书、携程、大众点评等中文平台时，优先使用 `opencli` 工具**（已安装全局 CLI）。opencli 提供原生站点适配器：

| 平台 | 适配器 | 常用命令 |
|------|--------|----------|
| 小红书 | `xiaohongshu` | `search`, `note`, `download`, `feed` |
| 携程 | `ctrip` | `search`（public）, `hotel-search`, `hotel-suggest` |
| 大众点评 | `dianping` | `search`, `shop` |

使用示例：
```bash
# 携程搜索（公开，无需 cookie）
opencli ctrip search --keyword "庐山 美食"

# 小红书搜索（需 cookie）
opencli xiaohongshu search --keyword "庐山美食推荐"

# 大众点评搜索（需 cookie）
opencli dianping search --keyword "庐山" --city "九江"
```

注意：小红书和大众点评的写操作需要先配置浏览器 cookie（通过 `opencli browser init`）。

### 顾客导向原则

面向客人的页面 (`preview/` 和 `templates/` 中除 `staff.html` 外的所有模板) **只展示对客人有益的功能**。员工看板、好评推送机制等内部运营功能不应出现在顾客页面。

### 主题系统

使用 `data-theme="dark"` 属性（挂载在 `<html>` 上）+ CSS 自定义属性覆盖实现深浅切换。所有颜色通过 `:root` 变量定义，暗色模式在 `[data-theme="dark"]` 选择器下覆盖。代码位置：
- Flask 模板：`static/css/style.css` 的 `[data-theme="dark"]` 块
- 预览页面：各自内联 `<style>` 中的 `[data-theme="dark"]` 块
- 员工看板：`templates/staff.html` 内联样式中的独立暗色变量

### 硬编码颜色

避免在 HTML `style=""` 属性中使用硬编码颜色值。使用 CSS 类（如 `.notice-card--success`、`.notice-card--warning`、`.room-preview-gradient-sky`），确保暗色模式能正确覆盖。

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
- **MinerU** — 文档提取工具，用于从携程页面等提取结构化信息

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
```
