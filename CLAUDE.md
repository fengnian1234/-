# 云上·归墅 — Claude Code 项目指引

## 信息获取规则

**数据优先级链**（从高到低）：

```
本地数据 (local_data/)  >  WebSearch  >  其他渠道
     最高优先级              次优先        最低
```

1. **`local_data/` 目录** — 最高优先级。民宿官方提供的图片、价目表、介绍文案等信息文件，其数据压倒一切其他来源。
   - `local_data/images/` — 房型照片、环境图、菜单图等
   - `local_data/documents/` — 房源清单、价目表、官方介绍等
2. **WebSearch** — 次优先级。当 `local_data/` 中没有对应信息时，使用 Claude Code 内置的 `WebSearch` 工具获取，优先于 AnySearch 等第三方渠道。
3. **其他来源** — 最低优先级。AnySearch API、本地缓存、旧数据等仅供补充参考。

- 不同层级数据冲突时，按优先级链采信
- 需要验证事实或获取最新数据时，先查 `local_data/`，再查 WebSearch

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
