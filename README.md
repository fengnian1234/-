# 🏔️ 云上·归墅 · 微信公众号客服系统

庐山之巅，大林沟路27号 — 精品民宿智能客服解决方案。

---

## ✨ 功能总览

### 🤖 微信智能客服
- **关键词自动回复**：回复数字 1-5 或关键词（房型/点餐/攻略/服务/人工）快速获取信息
- **AI 智能管家**：接入 DeepSeek 大模型，自然语言问答，预订后解锁
- **人工客服转接**：支持转接人工（8:00-22:00），非工作时间友好提示

### 🛏️ 房型展示
- 8 种精品房型（来自携程官方数据）
- 支持房间图片、价格、设施介绍
- H5 页面图文详情

### ☕ 咖啡简餐
- 「三山二水咖啡」自营咖啡馆
- 5 大分类 24 款产品（精品咖啡/茶饮/简餐轻食/甜点/饮品）
- 在线下单、购物车、微信支付

### 🗺️ 游玩攻略
- 5 条精选游玩路线
- 6 家周边美食推荐
- 索道通知 + 暑期自驾限行提醒

### 🛎️ 快捷服务
- 14 项快捷服务（客房/维修/前台）
- 一键呼叫，即刻响应

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.10+
- 嵌入式发行版已预装于 `C:\Users\admin\python-embed\`

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件，填入以下配置：

```env
# 微信配置（公众号后台获取）
WECHAT_TOKEN=your_token
WECHAT_APP_ID=wx_your_app_id
WECHAT_APP_SECRET=your_app_secret

# AI 对话（DeepSeek API）
ANTHROPIC_API_KEY=sk-your-deepseek-key
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic

# 微信支付（开通后获取）
WECHAT_MCH_ID=your_mch_id
WECHAT_MCH_KEY=your_mch_key
```

### 4. 启动

```bash
python run.py
```

服务启动后访问：
- 首页：`http://127.0.0.1:5000/`
- 房型展示：`http://127.0.0.1:5000/rooms`
- 咖啡简餐：`http://127.0.0.1:5000/menu`
- 游玩攻略：`http://127.0.0.1:5000/travel`
- 快捷服务：`http://127.0.0.1:5000/services`

### 5. 接入微信公众号

1. 将服务部署到公网服务器（需要 HTTPS 域名）
2. 在公众号后台设置服务器 URL：`https://你的域名/wechat`
3. Token 与 `.env` 中的 `WECHAT_TOKEN` 一致
4. 提交验证，通过后即可接收用户消息

---

## 📋 微信公众号注册指南

### 账号类型选择

| 类型 | 年费 | 微信支付 | 推荐 |
|------|------|---------|------|
| **服务号** | ¥300/年 | ✅ 支持 | **推荐民宿使用** |
| 订阅号 | 免费 | ❌ 不支持 | 媒体/自媒体 |

### 注册流程

1. 访问 https://mp.weixin.qq.com → 注册服务号
2. 准备：营业执照 + 法人身份证 + 对公账户
3. 填写账号名称「云上归墅」
4. 提交审核（1-7 个工作日）
5. 建议申请微信认证（¥300/年）

---

## 📁 项目结构

```
d:/cc/
├── app.py                  # Flask 主应用（28 条路由）
├── config.py               # 配置文件
├── models.py               # 数据库模型（SQLAlchemy + SQLite）
├── wechat.py               # 微信消息处理 + 关键词路由
├── seed_data.py            # 种子数据（携程官方数据）
├── run.py                  # 启动入口
├── requirements.txt        # Python 依赖
├── CLAUDE.md               # Claude Code 项目指引
│
├── services/               # 业务服务层
│   ├── rooms.py            # 房间查询/展示
│   ├── menu.py             # 点餐/订单管理
│   ├── travel.py           # 旅游路线/美食推荐
│   ├── quick.py            # 快捷服务
│   ├── booking.py          # 预订管理/AI解锁
│   ├── ai.py               # AI 智能对话
│   ├── monitor.py          # 平台口碑监控（opencli + WebSearch）
│   ├── report.py           # 周报生成（DOCX）
│   └── notify.py           # 员工通知
│
├── templates/              # Jinja2 模板（Flask 渲染）
│   ├── base.html           # 基础布局
│   ├── index.html          # 首页
│   ├── rooms.html          # 房型列表
│   ├── room_detail.html    # 房间详情
│   ├── menu.html           # 咖啡简餐
│   ├── travel.html         # 游玩攻略
│   ├── travel_detail.html  # 路线详情
│   ├── services.html       # 快捷服务
│   ├── map.html            # 位置导航
│   └── staff.html          # 员工看板
│
├── preview/                # 独立预览 HTML（纯前端）
│   ├── index.html
│   ├── rooms.html
│   ├── menu.html
│   ├── services.html
│   └── travel.html
│
├── local_data/             # 本地数据（最高优先级）
│   ├── images/             # 官方图片（携程 CDN）
│   └── documents/          # 信息文件
│
└── static/css/style.css    # 全局样式表
```

---

## 🛠️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | Flask 3.x | 轻量灵活 |
| 微信 SDK | wechatpy 2.x | 微信公众号开发 |
| 数据库 | SQLite + SQLAlchemy | 11间客房规模完全够用 |
| AI 对话 | DeepSeek V4 Pro | 中文优秀，成本低 |
| 前端 | Jinja2 + 原生 CSS | 无额外依赖 |
| 部署 | Gunicorn + Nginx | 生产环境推荐 |

---

## 📝 关键词回复速查

| 功能 | 关键词 |
|------|--------|
| 房型展示 | `1` `房型` `房间` `客房` |
| 咖啡简餐 | `2` `菜单` `点餐` `咖啡` `简餐` |
| 游玩攻略 | `3` `攻略` `游玩` `路线` `旅游` |
| 快捷服务 | `4` `服务` `快捷` |
| 预订咨询 | `预订` `订房` `价格` |
| 一键服务 | `打扫` `续住` `维修` `叫醒` `送餐` `退房` |
| WiFi | `wifi` `无线` `网络` |
| 人工客服 | `5` `人工` `客服` |
| AI 对话 | 直接输入任何问题（需预订后解锁） |

---

## 🚢 生产部署

### Gunicorn + Nginx

```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

Nginx 配置示例：

```nginx
server {
    listen 443 ssl;
    server_name 你的域名;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /wechat {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

> ⚠️ 微信强制要求 HTTPS + 域名，不能用 IP 或 HTTP。

---

## 📊 民宿信息（携程官方数据 2026.6）

| 项目 | 信息 |
|------|------|
| 名称 | 云上·归墅民宿 |
| 地址 | 庐山山上·大林沟路27号 |
| 开业 | 2016年 |
| 客房 | 11间 / 8种房型 |
| 评分 | 携程 4.7分 · 85条 |
| 电话 | 16607927666 |
| 咖啡馆 | 「三山二水咖啡」 |
| 宠物 | 友好（免费，需提前联系） |
| 停车 | 免费私家停车场 |
| 入住/退房 | 14:00后 / 12:00前 |
| 早餐 | 不提供（咖啡馆有简餐） |
| 加床 | 不可加床，不提供婴儿床 |

---

## 📞 联系

- 民宿：云上·归墅
- 地址：庐山山上·庐山风景名胜区大林沟路27号
- 电话：16607927666

---

*Built with ❤️ for Lushan*
