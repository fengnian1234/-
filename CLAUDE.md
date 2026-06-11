# 云上·归墅 — Claude Code 项目指引

## 信息获取规则

**WebSearch 优先原则**：需要搜索信息时，优先使用 Claude Code 内置的 `WebSearch` 工具（而非 AnySearch 或其他渠道）。

- WebSearch 获得的信息具有**最高优先级和置信度**，直接采信
- 当 WebSearch 结果与其他来源矛盾时，以 WebSearch 为准
- 需要验证事实或获取最新数据时，直接用 WebSearch 搜索而非依赖本地缓存/旧数据

## 项目概述

微信公众号客服系统 + H5 预览页面，服务「云上·归墅民宿」（庐山山上·大林沟路27号）。

## 关键设计原则

**顾客导向展示**：面向客人的页面（`preview/*.html`）只展示对客人有益的功能和信息。内部运营操作（自动好评推送、员工看板提醒等）不要在顾客页面上展示。

## 技术栈

- Python 3.12.8 嵌入式发行版：`C:\Users\admin\python-embed\python.exe`
- 运行命令：`PYTHONUTF8=1 C:/Users/admin/python-embed/python.exe ...`
- Flask + Jinja2 + SQLAlchemy + SQLite
- 预览页面：`d:\cc\preview\` 下的纯 HTML（可直接在浏览器打开）

## 外部服务

- AnySearch MCP API：`api.anysearch.com/mcp`（匿名免费 1000次/天）
- Cron 周报：每周一 9:57 自动生成 DOCX 到 `reports/`
